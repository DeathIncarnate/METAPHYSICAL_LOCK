#!/usr/bin/env python3
"""
Optimized Mersenne pipeline with checkpointing.

Usage:
  python mersenne_fast_checkpoint.py            # start fresh
  python mersenne_fast_checkpoint.py --resume   # resume from checkpoint (default name)
  python mersenne_fast_checkpoint.py --resume --checkpoint-file my.chkpt.json
"""

import math
import os
import sys
import time
import json
import tempfile
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import mmap
import hashlib
import argparse

# Optional dependencies
try:
    import psutil
except Exception:
    psutil = None

try:
    import gmpy2
    GMPY2_AVAILABLE = True
except Exception:
    gmpy2 = None
    GMPY2_AVAILABLE = False

# -------------------------
# CONFIG (tune these)
# -------------------------
TARGET_DECIMAL_DIGITS = 1_000_000_000
CHUNK_DECIMAL_DIGITS = 50_000
TEMP_CHUNKS = "decimal_chunks.tmp"
DECIMAL_FINAL = "mersenne_decimal.txt"
CHECKPOINT_FILE_DEFAULT = "mersenne_checkpoint.json"
MAX_RAM_PERCENT = 90
PROGRESS_INTERVAL_SECONDS = 2.0
FORMAT_WORKERS = min(8, (os.cpu_count() or 4))
CHECKPOINT_EVERY_CHUNKS = 128        # save checkpoint every N chunks
CHECKPOINT_EVERY_SECONDS = 30.0      # or every N seconds (whichever comes first)

# -------------------------
# Utilities
# -------------------------
def now():
    return datetime.now().strftime("%H:%M:%S")

def info(msg):
    print(f"[{now()}] [INFO] {msg}", flush=True)

def warn(msg):
    print(f"[{now()}] [WARN] {msg}", flush=True)

def error(msg):
    print(f"[{now()}] [ERROR] {msg}", flush=True)

def mem_percent():
    if psutil:
        return psutil.virtual_memory().percent
    return None

def throttle_if_needed():
    if psutil:
        while psutil.virtual_memory().percent >= MAX_RAM_PERCENT:
            info(f"Memory at {psutil.virtual_memory().percent}%, throttling...")
            time.sleep(0.5)

def bits_for_decimal_digits(digits: int) -> int:
    log10_2 = math.log10(2.0)
    return math.floor((digits - 1) / log10_2) + 1

def atomic_write_json(path: str, obj: dict):
    # write to temp file then replace
    dirn = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(dir=dirn, prefix=".tmp_chkpt_", text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except Exception:
                pass

def sha256_of_file(path: str):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

# -------------------------
# Checkpoint helpers
# -------------------------
def save_checkpoint(checkpoint_file: str, tmp_filename: str, p: int, chunk_digits: int,
                    N_str: str, write_pos: int, written_chunks: int):
    """
    Save checkpoint JSON atomically. N_str is decimal string of remaining N.
    Also store a quick checksum of the temp file (if it exists).
    """
    info(f"Saving checkpoint to '{checkpoint_file}' (chunks={written_chunks}, write_pos={write_pos})")
    chk = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "p": p,
        "chunk_digits": chunk_digits,
        "N_str": N_str,
        "write_pos": write_pos,
        "written_chunks": written_chunks,
        "tmp_filename": os.path.abspath(tmp_filename),
    }
    try:
        if os.path.exists(tmp_filename):
            chk["tmp_sha256"] = sha256_of_file(tmp_filename)
            chk["tmp_size"] = os.path.getsize(tmp_filename)
    except Exception as e:
        warn(f"Could not compute temp file checksum: {e}")
    atomic_write_json(checkpoint_file, chk)
    info("Checkpoint saved")

def load_checkpoint(checkpoint_file: str):
    if not os.path.exists(checkpoint_file):
        raise FileNotFoundError(f"Checkpoint file '{checkpoint_file}' not found")
    with open(checkpoint_file, "r", encoding="utf-8") as f:
        chk = json.load(f)
    return chk

# -------------------------
# Fast path: gmpy2 native conversion
# -------------------------
def fast_gmpy2_full_decimal(N):
    info("Attempting gmpy2 native decimal conversion (fast path)")
    start = time.time()
    s = gmpy2.digits(N, 10)
    elapsed = time.time() - start
    info(f"gmpy2 conversion done in {elapsed:.2f}s; length={len(s)}")
    return s

# -------------------------
# Chunked streaming with checkpointing
# -------------------------
def stream_decimal_chunks_with_checkpoint(p: int, chunk_digits: int, tmp_filename: str,
                                          checkpoint_file: str, resume: bool):
    """
    Stream decimal chunks LSB-first into a temp file with checkpointing support.
    If resume=True and checkpoint exists, resume from saved N and write_pos.
    Returns total written_chunks.
    """
    info(f"Streaming decimal chunks with checkpointing to '{tmp_filename}' (chunk_digits={chunk_digits})")
    start = time.time()

    # Prepare N and pow10, possibly from checkpoint
    if resume and os.path.exists(checkpoint_file):
        chk = load_checkpoint(checkpoint_file)
        # validate config
        if chk.get("p") != p or chk.get("chunk_digits") != chunk_digits:
            raise RuntimeError("Checkpoint configuration mismatch (p or chunk_digits). Aborting resume.")
        N_str = chk["N_str"]
        write_pos = chk.get("write_pos", 0)
        written_chunks = chk.get("written_chunks", 0)
        info(f"Resuming from checkpoint: written_chunks={written_chunks}, write_pos={write_pos}")
        if GMPY2_AVAILABLE:
            N = gmpy2.mpz(N_str)
            pow10 = gmpy2.mpz(10) ** chunk_digits
        else:
            N = int(N_str)
            pow10 = 10 ** chunk_digits
    else:
        # fresh start
        if GMPY2_AVAILABLE:
            mp_one = gmpy2.mpz(1)
            N = (mp_one << p) - 1
            pow10 = gmpy2.mpz(10) ** chunk_digits
        else:
            N = (1 << p) - 1
            pow10 = 10 ** chunk_digits
        write_pos = 0
        written_chunks = 0

    info(f"Constructed N bit_length={N.bit_length()}")

    # Prepare temp file (open for read/write, create if missing)
    # If resuming and file exists, we will mmap and append at write_pos
    with open(tmp_filename, "a+b") as tf:
        tf.flush()
        tf.seek(0, os.SEEK_END)
        current_size = tf.tell()
        # ensure file is at least write_pos bytes
        if write_pos > current_size:
            tf.write(b"\x00" * (write_pos - current_size))
            tf.flush()
        # We'll use mmap only for writes; simpler to write directly at offsets
        last_print = time.time()
        last_checkpoint_time = time.time()
        chunks_since_checkpoint = 0

        # Thread pool for formatting
        with ThreadPoolExecutor(max_workers=FORMAT_WORKERS) as ex:
            futures = []
            while N:
                throttle_if_needed()
                if GMPY2_AVAILABLE:
                    N, rem = divmod(N, pow10)
                    rem_int = int(rem)
                else:
                    N, rem_int = divmod(N, pow10)

                # format chunk in thread
                fut = ex.submit(lambda r: f"{r:0{chunk_digits}d}\n".encode("ascii"), rem_int)
                futures.append(fut)

                # flush completed futures in FIFO order to keep LSB-first order
                while futures and futures[0].done():
                    chunk_bytes = futures.pop(0).result()
                    tf.seek(write_pos)
                    tf.write(chunk_bytes)
                    tf.flush()
                    write_pos += len(chunk_bytes)
                    written_chunks += 1
                    chunks_since_checkpoint += 1

                # progress print
                if time.time() - last_print >= PROGRESS_INTERVAL_SECONDS:
                    info(f"  chunks written: {written_chunks}, remaining bits ~ {N.bit_length() if N else 0}")
                    last_print = time.time()

                # checkpoint by chunk count or time
                if (chunks_since_checkpoint >= CHECKPOINT_EVERY_CHUNKS) or (time.time() - last_checkpoint_time >= CHECKPOINT_EVERY_SECONDS):
                    # save N as decimal string
                    N_str = str(N) if not GMPY2_AVAILABLE else gmpy2.digits(N, 10)
                    save_checkpoint(checkpoint_file, tmp_filename, p, chunk_digits, N_str, write_pos, written_chunks)
                    last_checkpoint_time = time.time()
                    chunks_since_checkpoint = 0

            # flush any remaining futures
            for fut in futures:
                chunk_bytes = fut.result()
                tf.seek(write_pos)
                tf.write(chunk_bytes)
                tf.flush()
                write_pos += len(chunk_bytes)
                written_chunks += 1

        # final checkpoint (N == 0)
        N_str = "0"
        save_checkpoint(checkpoint_file, tmp_filename, p, chunk_digits, N_str, write_pos, written_chunks)

    elapsed = time.time() - start
    info(f"Finished streaming chunks in {elapsed:.1f}s; temp file size={os.path.getsize(tmp_filename)} bytes; chunks={written_chunks}")
    return written_chunks

# -------------------------
# Assemble final decimal (simple)
# -------------------------
def assemble_final_decimal(tmp_filename: str, final_filename: str):
    info(f"Assembling final decimal file '{final_filename}' from temp '{tmp_filename}'")
    start = time.time()
    with open(tmp_filename, "rb") as tf:
        chunks = tf.read().splitlines()
    if not chunks:
        raise RuntimeError("Temp chunk file empty")

    with open(final_filename, "w", encoding="ascii") as out:
        msb = chunks[-1].decode("ascii")
        out.write(msb.lstrip("0") or "0")
        for c in reversed(chunks[:-1]):
            out.write(c.decode("ascii"))

    elapsed = time.time() - start
    info(f"Final decimal file written in {elapsed:.1f}s; size={os.path.getsize(final_filename)} bytes")
    # remove temp and checkpoint
    try:
        os.remove(tmp_filename)
        info(f"Removed temp file '{tmp_filename}'")
    except Exception as e:
        warn(f"Could not remove temp file: {e}")

# -------------------------
# Main
# -------------------------
def main():
    parser = argparse.ArgumentParser(description="Mersenne pipeline with checkpointing")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint if available")
    parser.add_argument("--checkpoint-file", default=CHECKPOINT_FILE_DEFAULT, help="Checkpoint JSON filename")
    args = parser.parse_args()

    info("Starting Mersenne pipeline (checkpointing enabled)")
    info(f"Python {sys.version.splitlines()[0]}")
    if psutil:
        info(f"psutil available; total RAM={psutil.virtual_memory().total // (1024**3)} GB")
    else:
        warn("psutil not installed; memory throttling disabled")

    if GMPY2_AVAILABLE:
        info("gmpy2 available; will try native conversion first")
    else:
        warn("gmpy2 not available; using Python int fallback")

    if TARGET_DECIMAL_DIGITS <= 0:
        error("TARGET_DECIMAL_DIGITS must be > 0")
        return

    p = bits_for_decimal_digits(TARGET_DECIMAL_DIGITS)
    approx_digits = int(p * math.log10(2)) + 1
    info(f"Target decimal digits: {TARGET_DECIMAL_DIGITS}")
    info(f"Computed exponent p: {p}")
    info(f"Approx decimal digits for 2^p - 1: {approx_digits}")

    try:
        # Build N and try fast path
        if GMPY2_AVAILABLE:
            N = (gmpy2.mpz(2) << p) - 1
            try:
                s = fast_gmpy2_full_decimal(N)
                with open(DECIMAL_FINAL, "w", encoding="ascii") as f:
                    f.write(s)
                info(f"Wrote final decimal via gmpy2 fast path; size={os.path.getsize(DECIMAL_FINAL)}")
                # remove any stale checkpoint
                if os.path.exists(args.checkpoint_file):
                    try:
                        os.remove(args.checkpoint_file)
                        info("Removed stale checkpoint file")
                    except Exception:
                        pass
                return
            except Exception as e:
                warn(f"gmpy2 fast path failed: {e}; falling back to streaming")

        # Fallback: streaming with checkpointing
        stream_decimal_chunks_with_checkpoint(p, CHUNK_DECIMAL_DIGITS, TEMP_CHUNKS, args.checkpoint_file, args.resume)
        assemble_final_decimal(TEMP_CHUNKS, DECIMAL_FINAL)
        # remove checkpoint after success
        if os.path.exists(args.checkpoint_file):
            try:
                os.remove(args.checkpoint_file)
                info("Removed checkpoint file after successful assembly")
            except Exception:
                pass

        info("Pipeline completed successfully (streaming path)")

    except Exception as exc:
        error(f"Unhandled exception: {exc}")
        import traceback
        traceback.print_exc()
        return

if __name__ == "__main__":
    main()
