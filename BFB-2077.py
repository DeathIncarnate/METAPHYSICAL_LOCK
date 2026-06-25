# SENTINEL_OF_VOID_MERGED_VISUAL: ENKI-13 Unified Solver + Live Braid (v31.0)
# Plug-and-play: runs the genetic convergence engine AND a real-time curses braid
# visualization of emergent phrases. All verbose textual reporting is buffered
# during the run and printed AFTER the visualization ends (or if visualization
# cannot start, prints as usual).
#
# Requirements: Python 3.9+, a real terminal (for curses). On Windows, run in
# Windows Terminal or similar. If curses init fails, falls back to print-only.

import hashlib
import random
import sys
import time
import threading
from collections import Counter, deque
import curses, math, time
from ecdsa import SECP256k1, SigningKey
import itertools

# ====== Report Color Helpers ======
def colorize_byte(pred_b: int, target_b: int) -> str:
    matches = 8 - bin(pred_b ^ target_b).count("1")
    if matches == 8:
        color = curses.color_pair(1)  # LightBlue
    elif matches >= 6:
        color = curses.color_pair(2)  # Green
    elif matches >= 3:
        color = curses.color_pair(3)  # Yellow
    elif matches >= 1:
        color = curses.color_pair(5)  # Orange
    else:
        color = curses.color_pair(4)  # Pink
    return color

# ANSI version for normal printouts (outside curses)
RESET     = "\033[0m"
LIGHTBLUE = "\033[94m"
GREEN     = "\033[92m"
YELLOW    = "\033[93m"
ORANGE    = "\033[38;5;208m"
PINK      = "\033[95m"

def ansi_colorize_byte(pred_b: int, target_b: int) -> str:
    matches = 8 - bin(pred_b ^ target_b).count("1")
    if matches == 8:
        color = LIGHTBLUE
    elif matches >= 6:
        color = GREEN
    elif matches >= 3:
        color = YELLOW
    elif matches >= 1:
        color = ORANGE
    else:
        color = PINK
    return color

# ============================== CONFIG =======================================

GENERATIONS           = 100000
POPULATION_SIZE       = 1500
SURVIVAL_RATE         = 0.20
MUTATION_RATE         = 0.60
BIT_FLIPS_MIN_MAX     = (1, 10)          # flips per child when mutation triggers
AGE_PROVEN_THRESHOLD  = 100              # min age to be "proven"
STAGNATION_THRESHOLD  = 5                # gens without best improvement ⇒ add best to repo
PENALTY_FOR_ZERO_WORD = 100              # penalize '00000000' in suffix
REPORT_INTERVAL       = 50               # gens between buffered snapshots
TOP_PHRASES_LEN       = 5                # visualize this phrase length bucket (2..5 recommended)
BRAID_STRANDS         = 50                # # of strands displayed (top-N phrases)

FOUNDATIONAL_PREFIX_HEX         = "00000000000000000000000000000000"
KEY_BIT_LENGTH                  = 256
FOUNDATIONAL_PREFIX_LENGTH_BITS = 128
SUFFIX_LENGTH_BITS              = KEY_BIT_LENGTH - FOUNDATIONAL_PREFIX_LENGTH_BITS
SUFFIX_MASK                     = (1 << SUFFIX_LENGTH_BITS) - 1

TARGET_DATA = {
    "id": "ENKI-13",
    # You may replace with your public key hex (02/03 compressed or 04 uncompressed)
    "pubkey_hex": "035cd1854cae45391ca4ec428cc7e6c7d9984424b954209a8eea197b9e364c05f6"
}
# ====== SECP256K1 CONSTANTS ======
CURVE_ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
FIELD_MODULUS = 2**256 - 2**32 - 977

# ====== MASTER ALGORITHM INTEGRATION ======

def private_key_to_public_key(privkey):
    """Convert private key to compressed public key using proper EC math"""
    try:
        sk = SigningKey.from_secret_exponent(privkey, curve=SECP256k1)
        vk = sk.get_verifying_key()
        return vk.to_string("compressed").hex()
    except Exception as e:
        return None

def pubkeys_match(generated_hex, target_hex):
    """Check if two public keys match"""
    def normalize_pubkey(hex_str):
        if len(hex_str) == 130 and hex_str.startswith('04'):
            x = hex_str[2:66]
            y = hex_str[66:130]
            prefix = '02' if int(y[-1], 16) % 2 == 0 else '03'
            return prefix + x
        return hex_str
    return normalize_pubkey(generated_hex) == normalize_pubkey(target_hex)

def validate_private_key(candidate_privkey, target_pubkey_hex, curve_order):
    """Validate if candidate private key produces target public key"""
    if candidate_privkey <= 0 or candidate_privkey >= curve_order:
        return False
    generated_pubkey = private_key_to_public_key(candidate_privkey)
    return generated_pubkey and pubkeys_match(generated_pubkey, target_pubkey_hex)

# ====== MASTER ALGORITHM STRATEGIES ======

def attempt_phrase_reconstruction(void_engine, curve_order):
    """Strategy 1: Direct phrase reconstruction"""
    try:
        top_phrases = []
        for L in [2, 3, 4, 5]:
            key = f"phrases_{L}"
            if hasattr(void_engine, 'cumulative') and key in void_engine.cumulative and void_engine.cumulative[key]:
                top_phrases.extend(void_engine.cumulative[key].most_common(3))
        
        if not top_phrases:
            return None
        
        for phrase, frequency in top_phrases:
            segments = phrase.split('_')
            hex_string = ''.join(segments)
            
            if len(hex_string) < 16:
                hex_string = (hex_string * (64 // len(hex_string) + 1))[:64]
            else:
                hex_string = hex_string[:64]
            
            try:
                candidate = int(hex_string, 16) % curve_order
                if candidate != 0:
                    return candidate
            except ValueError:
                continue
        return None
    except:
        return None

def attempt_modular_relationships(void_engine, field_modulus, curve_order):
    """Strategy 2: Modular arithmetic relationships"""
    try:
        if not hasattr(void_engine, 'proven_mutations') or len(void_engine.proven_mutations) < 2:
            return None
        
        key = "phrases_3"
        if not hasattr(void_engine, 'cumulative') or key not in void_engine.cumulative or not void_engine.cumulative[key]:
            return None
        
        top_phrase, freq = void_engine.cumulative[key].most_common(1)[0]
        segments = top_phrase.split('_')
        seed_value = sum(int(seg, 16) for seg in segments if seg) % field_modulus
        
        proven_values = list(void_engine.proven_mutations)
        for proven in proven_values[:5]:
            relationships = [
                (proven * seed_value) % curve_order,
                (proven + seed_value) % curve_order,
                (proven ^ seed_value) % curve_order,
            ]
            for candidate in relationships:
                if 0 < candidate < curve_order:
                    return candidate
        return None
    except:
        return None

def attempt_ca_guided_search(void_engine, curve_order):
    """Strategy 3: CA-guided private key search"""
    try:
        key = "phrases_4"
        if not hasattr(void_engine, 'cumulative') or key not in void_engine.cumulative or not void_engine.cumulative[key]:
            return None
        
        top_phrase, freq = void_engine.cumulative[key].most_common(1)[0]
        segments = top_phrase.split('_')
        ca_rules = []
        
        for seg in segments:
            try:
                rule = int(seg, 16) % 256
                ca_rules.append(rule)
            except:
                continue
        
        if not ca_rules:
            return None
        
        # CA simulation for private key generation
        initial_state = sum(int(seg, 16) for seg in segments if seg) & ((1 << 256) - 1)
        current_state = initial_state
        
        for step in range(256):
            rule = ca_rules[step % len(ca_rules)]
            new_state = 0
            for bit_pos in range(256):
                left = (current_state >> ((bit_pos - 1) % 256)) & 1
                center = (current_state >> bit_pos) & 1
                right = (current_state >> ((bit_pos + 1) % 256)) & 1
                neighborhood = (left << 2) | (center << 1) | right
                new_bit = (rule >> neighborhood) & 1
                new_state |= (new_bit << bit_pos)
            current_state = new_state
        
        return current_state % curve_order
    except:
        return None

def attempt_multi_phrase_combinatorics(void_engine, curve_order):
    """Strategy 4: Multi-phrase combinatorial approach"""
    try:
        phrases_by_length = {}
        for L in [2, 3, 4, 5]:
            key = f"phrases_{L}"
            if hasattr(void_engine, 'cumulative') and key in void_engine.cumulative and void_engine.cumulative[key]:
                phrases_by_length[L] = [p for p, _ in void_engine.cumulative[key].most_common(2)]
        
        if len(phrases_by_length) < 2:
            return None
        
        phrase_values = {}
        for L, phrases in phrases_by_length.items():
            for phrase in phrases:
                segments = phrase.split('_')
                hex_str = ''.join(segments)
                if hex_str:
                    try:
                        value = int(hex_str, 16)
                        phrase_values[phrase] = value
                    except:
                        continue
        
        if len(phrase_values) < 2:
            return None
        
        values = list(phrase_values.values())
        combinations = [
            (values[0] * values[1]) % curve_order,
            (values[0] + values[1]) % curve_order,
            (values[0] ^ values[1]) % curve_order,
        ]
        
        for candidate in combinations:
            if candidate and 0 < candidate < curve_order:
                return candidate
        return None
    except:
        return None

def void_dict_to_private_key(void_engine, target_pubkey_hex, max_attempts=1000):
    """MASTER ALGORITHM: Convert Void Dictionary patterns to private key"""
    attempts = 0
    
    while attempts < max_attempts:
        attempts += 1
        
        # Try all strategies
        strategies = [
            attempt_phrase_reconstruction(void_engine, CURVE_ORDER),
            attempt_modular_relationships(void_engine, FIELD_MODULUS, CURVE_ORDER),
            attempt_ca_guided_search(void_engine, CURVE_ORDER),
            attempt_multi_phrase_combinatorics(void_engine, CURVE_ORDER),
        ]
        
        for candidate in strategies:
            if candidate and validate_private_key(candidate, target_pubkey_hex, CURVE_ORDER):
                return candidate
        
        # Small random delay to prevent tight looping
        time.sleep(0.001)
    
    return None
# ============================== LOG BUFFER ===================================

_report_log = deque()

def logln(s=""):
    """Buffer reporting lines during the run; flush at the end."""
    _report_log.append(s)

def flush_logs_to_stdout():
    while _report_log:
        print(_report_log.popleft())

# ============================== MODELS A & B =================================

def sanitize_hex_string(hex_string):
    if not isinstance(hex_string, str): return ""
    s = hex_string.strip().lower()
    s = "".join(c for c in s if c in "0123456789abcdef")
    if len(s) % 2 != 0: s = s[:-1]
    return s

def model_timeline_A(public_key_hex: str) -> int:
    sanitized_pk_hex = sanitize_hex_string(public_key_hex)
    if not sanitized_pk_hex: return 0
    pk_bytes_uncompressed = bytes.fromhex(sanitized_pk_hex)
    # normalize to 02/03 compressed if uncompressed 04:
    if len(pk_bytes_uncompressed) == 65 and pk_bytes_uncompressed.startswith(b'\x04'):
        y = int.from_bytes(pk_bytes_uncompressed[33:], 'big')
        prefix = b'\x02' if y % 2 == 0 else b'\x03'
        pk_bytes = prefix + pk_bytes_uncompressed[1:33]
    else:
        pk_bytes = pk_bytes_uncompressed
    h1 = hashlib.sha256(pk_bytes).digest()
    first_half = int.from_bytes(h1[:16], 'big')
    h2 = hashlib.sha256(pk_bytes + first_half.to_bytes(16, 'big')).digest()
    signature = int.from_bytes(h2[:16], 'big')
    second_half = first_half ^ signature
    return (first_half << 128) | second_half

def model_timeline_B(public_key_hex: str) -> int:
    sanitized_pk_hex = sanitize_hex_string(public_key_hex)
    if not sanitized_pk_hex: return 0
    pk_bytes_uncompressed = bytes.fromhex(sanitized_pk_hex)
    if len(pk_bytes_uncompressed) == 65 and pk_bytes_uncompressed.startswith(b'\x04'):
        y = int.from_bytes(pk_bytes_uncompressed[33:], 'big')
        prefix = b'\x02' if y % 2 == 0 else b'\x03'
        pk_bytes = prefix + pk_bytes_uncompressed[1:33]
    else:
        pk_bytes = pk_bytes_uncompressed

    pk_x_bytes = pk_bytes[1:33]
    MODULUS    = 2**128
    ITERATIONS = 16

    h1 = hashlib.sha256(pk_bytes).digest()
    first_half  = int.from_bytes(h1[:16], 'big')
    phase_shift = int.from_bytes(hashlib.sha256(pk_x_bytes).digest()[:16], 'big')
    h2 = hashlib.sha256(h1).digest()
    fractal_seed = int.from_bytes(hashlib.sha256(h2).digest()[:16], 'big')

    current_val = first_half
    for i in range(ITERATIONS):
        term1 = (current_val * fractal_seed) % MODULUS
        term2 = (phase_shift * (i + 1)) % MODULUS
        current_val = (term1 - term2) % MODULUS
        current_val = current_val ^ (fractal_seed >> (i * 4))

    second_half = first_half ^ current_val
    return (first_half << 128) | second_half

# ============================== UTILS ========================================

def hamming_distance(n1: int, n2: int) -> int:
    return bin(n1 ^ n2).count('1')

def translate_to_void_language(hex_64: str) -> str:
    return "_".join(hex_64[i:i+8] for i in range(0, 64, 8))

# ============================== LINGUISTIC MEMORY ============================

class VoidDictionaryEngine:
    """
    Generational + Cumulative symbolic memory with letters, words, and phrases (2..5).
    Age-gated "proven mutations".
    """
    def __init__(self):
        self.generational = {
            "letters": Counter(),
            "words": Counter(),
            "phrases_2": Counter(),
            "phrases_3": Counter(),
            "phrases_4": Counter(),
            "phrases_5": Counter(),
        }
        self.cumulative = {
            "letters": Counter(),
            "words": Counter(),
            "phrases_2": Counter(),
            "phrases_3": Counter(),
            "phrases_4": Counter(),
            "phrases_5": Counter(),
        }
        self.proven_mutations = set()
        self.WORD_SIZE = 8  # hex chars per "word"

    def clear_generational(self):
        for k in self.generational:
            self.generational[k].clear()

    def analyze(self, population):
        self.clear_generational()
        for solver in population:
            delta_hex = f"{solver.predicted_delta:064x}"

            # letters
            self.generational["letters"].update(delta_hex)
            self.cumulative["letters"].update(delta_hex)

            # words: contiguous non-zero chunks in suffix region
            suffix_hex = delta_hex[FOUNDATIONAL_PREFIX_LENGTH_BITS // 4:]
            words = []
            current = []
            for ch in suffix_hex:
                if ch != '0':
                    current.append(ch)
                elif current:
                    w = "".join(current)
                    words.append(w)
                    self.generational["words"][w] += 1
                    self.cumulative["words"][w] += 1
                    current = []
            if current:
                w = "".join(current)
                words.append(w)
                self.generational["words"][w] += 1
                self.cumulative["words"][w] += 1

            # phrases (2..5)
            for L in (2, 3, 4, 5):
                if len(words) >= L:
                    phrases = ["_".join(words[i:i+L]) for i in range(len(words) - L + 1)]
                    key = f"phrases_{L}"
                    self.generational[key].update(phrases)
                    self.cumulative[key].update(phrases)

    def record_survivor(self, solver):
        if solver.age >= AGE_PROVEN_THRESHOLD:
            self.proven_mutations.add(solver.predicted_delta)

# ============================== COMPOSITE ANALYZER ===========================

class MultiDeltaAnalyzer:
    def __init__(self, dictionary_engine: VoidDictionaryEngine):
        self.dictionary_engine = dictionary_engine
        self.composite_deltas = {}

    @staticmethod
    def _build_composite_from_pool(pool):
        if not pool: return 0
        composite = 0
        for i in range(256):
            bit_mask = 1 << i
            votes = sum(1 for d in pool if (d & bit_mask) != 0)
            if votes > len(pool) / 2:
                composite |= bit_mask
        return composite

    def analyze(self):
        proven_pool = list(self.dictionary_engine.proven_mutations)
        self.composite_deltas["Proven Mutations"] = self._build_composite_from_pool(proven_pool)
        self.composite_deltas["Total"] = self.composite_deltas["Proven Mutations"]

# ============================== GENETIC CORE =================================

class GeneticSolver:
    def __init__(self, predicted_delta=None, generation=0):
        if predicted_delta is None:
            random_suffix = random.getrandbits(SUFFIX_LENGTH_BITS)
            self.predicted_delta = (int(FOUNDATIONAL_PREFIX_HEX, 16) << SUFFIX_LENGTH_BITS) | (random_suffix & SUFFIX_MASK)
        else:
            self.predicted_delta = predicted_delta
        self.fitness = float('inf')
        self.generation_born = generation
        self.age = 0

    def calculate_fitness(self, true_error_delta_int: int) -> int:
        self.fitness = hamming_distance(self.predicted_delta, true_error_delta_int)
        # penalize zero-word in suffix region
        hex_full = f"{self.predicted_delta:064x}"
        suffix_hex = hex_full[FOUNDATIONAL_PREFIX_LENGTH_BITS // 4:]
        if "00000000" in suffix_hex:
            self.fitness += PENALTY_FOR_ZERO_WORD
        return self.fitness

generational_delta_repository = []
previous_best_hamming_distance = float('inf')
stagnation_counter = 0

def causal_recursive_mutation(child_suffix: int) -> int:
    if not generational_delta_repository:
        return child_suffix
    flux = Counter()
    for d in generational_delta_repository:
        suffix = d & SUFFIX_MASK
        for i in range(SUFFIX_LENGTH_BITS):
            if (suffix >> i) & 1:
                flux[i] += 1
    if not flux:
        return child_suffix
    max_bit = flux.most_common(1)[0][0]
    return child_suffix ^ (1 << max_bit)

def evolve_population(population, current_gen, mutation_rate=MUTATION_RATE, survival_rate=SURVIVAL_RATE):
    num_survivors = max(1, int(len(population) * survival_rate))
    population.sort(key=lambda x: x.fitness)
    survivors = population[:num_survivors]
    for s in survivors:
        s.age += 1

    next_gen = survivors[:]
    prefix = int(FOUNDATIONAL_PREFIX_HEX, 16) << SUFFIX_LENGTH_BITS

    while len(next_gen) < len(population):
        p1, p2 = random.sample(survivors, k=2)
        child_suffix = (p1.predicted_delta & SUFFIX_MASK) ^ (p2.predicted_delta & SUFFIX_MASK)

        if generational_delta_repository and random.random() < 0.50:
            child_suffix = causal_recursive_mutation(child_suffix)

        if random.random() < mutation_rate:
            flips = random.randint(*BIT_FLIPS_MIN_MAX)
            for _ in range(flips):
                bit = random.randint(0, SUFFIX_LENGTH_BITS - 1)
                child_suffix ^= (1 << bit)

        child_delta = prefix | (child_suffix & SUFFIX_MASK)
        next_gen.append(GeneticSolver(predicted_delta=child_delta, generation=current_gen))

    return next_gen

# ============================== REPORTING (BUFFERED) ==========================

def display_report(generation, population, target_delta, k_predicted, analyzer, dict_eng: VoidDictionaryEngine):
    best = min(population, key=lambda x: x.fitness)
    logln("\n" + "="*80)
    logln(f"  GENERATION {generation} REPORT")
    logln(f"  Best Individual Fitness (Hamming): {best.fitness}")
    logln(f"  Target V_error: {target_delta:064x}")
    logln(f"  Best V_error:   {best.predicted_delta:064x}")
        # --- Colored Byte Report ---
    best_bytes   = best.predicted_delta.to_bytes(32, 'big')
    target_bytes = target_delta.to_bytes(32, 'big')
    colored_line = []
    for pb, tb in zip(best_bytes, target_bytes):
        col = ansi_colorize_byte(pb, tb)
        colored_line.append(f"{col}{pb:02x}{RESET}")
    print("\n--- Colored Byte Report ---")
    print(" ".join(colored_line))

    # --- Colored Bit Report ---
    pred_bits   = f"{best.predicted_delta:0256b}"
    target_bits = f"{target_delta:0256b}"
    bit_line = []
    for b_pred, b_true in zip(pred_bits, target_bits):
        if b_pred == b_true:
            bit_line.append(f"{LIGHTBLUE}{b_pred}{RESET}")
        else:
            bit_line.append(f"{PINK}{b_pred}{RESET}")
    print("\n--- Colored Bit Report ---")
    print("".join(bit_line))

    logln("="*80)

    logln("\n--- Multi-Delta Analysis (k_true = k_predicted ⊕ V_error) ---")
    for name, delta in analyzer.composite_deltas.items():
        if delta == 0: 
            continue
        k_true_guess = k_predicted ^ delta
        hd = hamming_distance(delta, target_delta)
        logln(f"  - {name} Delta (HD: {hd}):")
        logln(f"    - V_error Guess: {delta:064x}")
        logln(f"    - k_true Guess:  {k_true_guess:064x}")

    logln("\n--- Cumulative Dictionary Stats ---")
    logln(f"  Proven Mutations: {len(dict_eng.proven_mutations)}")
    total_words = sum(dict_eng.cumulative["words"].values())
    logln(f"  Total Words Logged: {total_words}")

    key = f"phrases_{TOP_PHRASES_LEN}"
    logln(f"\n--- Top 10 Cumulative Phrases ({TOP_PHRASES_LEN} words) ---")
    for i, (phrase, count) in enumerate(dict_eng.cumulative[key].most_common(10), 1):
        logln(f"  - {i:02d}: '{phrase}' | Count: {count}")

def print_dictionary_snapshot(gen, dict_eng: VoidDictionaryEngine, best_hex, target_int):
    best_int = int(best_hex, 16)
    logln("\n" + "="*80)
    logln(f"  LINGUISTIC SNAPSHOT: Generation {gen}")
    logln("="*80)
    logln(f"  Best Δ:  {best_hex}")
    logln(f"  Target:  {target_int:064x}")
    logln(f"  HD:      {hamming_distance(best_int, target_int)}")

    logln("\n  >> Top 12 Letters:")
    for ch, cnt in dict_eng.cumulative["letters"].most_common(12):
        logln(f"    - '{ch}': {cnt}")

    logln("\n  >> Top 12 Words:")
    for w, cnt in dict_eng.cumulative["words"].most_common(12):
        logln(f"    - '{w}': {cnt}")

    for L in (2,3,4,5):
        key = f"phrases_{L}"
        logln(f"\n  >> Top 8 Phrases ({L} words):")
        for ph, cnt in dict_eng.cumulative[key].most_common(8):
            logln(f"    - '{ph}': {cnt}")

# ============================== SHARED STATE FOR VIS ==========================

class SharedState:
    def __init__(self):
        self.lock = threading.Lock()
        self.generation = 0
        self.best_hd = None
        self.target_hex = ""
        self.strands = []
        self.running = True
        self.converged = False
        self.private_key = None  # NEW: Store discovered private key

    def update(self, generation, best_hd, target_int, phrases):
        with self.lock:
            self.generation = generation
            self.best_hd = best_hd
            self.target_hex = f"{target_int:064x}"
            self.strands = phrases[:BRAID_STRANDS]

# ============================== CURSES VISUAL =================================

def _visual_loop_curses(stdscr, shared: SharedState):
    curses.curs_set(0)
    stdscr.nodelay(True)
    curses.start_color()
    curses.use_default_colors()

    curses.init_pair(1, curses.COLOR_CYAN, -1)
    curses.init_pair(2, curses.COLOR_GREEN, -1)
    curses.init_pair(3, curses.COLOR_YELLOW, -1)
    curses.init_pair(4, curses.COLOR_MAGENTA, -1)
    curses.init_pair(5, curses.COLOR_RED, -1)

    frame = 0
    glyphs = ['█', '▓', '▒', '░', '●', '•']

    while True:
        with shared.lock:
            running = shared.running
            strands = list(shared.strands)
            gen = shared.generation
            best_hd = shared.best_hd
            tgt = shared.target_hex
            private_key = shared.private_key  # NEW: Get private key status

        if not running:
            break

        stdscr.erase()
        h, w = stdscr.getmaxyx()

        # ENHANCED HEADER WITH PRIVATE KEY STATUS
        title = "SENTINEL_OF_VOID — SECP256K1 PRIVATE KEY EXTRACTION"
        info = f"Gen: {gen:>6} | Best HD: {best_hd if best_hd is not None else '-':>3}"
        
        if private_key:
            pk_display = f" | PRIVATE KEY FOUND: {private_key:064x}"[:w-50]
            info += pk_display

        try:
            stdscr.addstr(0, max(0, (w-len(title))//2), title, curses.A_BOLD)
            stdscr.addstr(1, max(0, (w-len(info))//2), info)
        except:
            pass

        # Braid params
        num_strands = max(1, len(strands))
        strand_length = max(10, min(h-5, 30))
        radius = max(4, min(h//3, w//6))

        # normalize counts for brightness selection
        counts = [c for _, c in strands] or [1]
        cmin, cmax = min(counts), max(counts)

        def pick_glyph(idx, c):
            if cmax == cmin:
                level = 0
            else:
                level = int((c - cmin) / (cmax - cmin) * (len(glyphs)-1))
            return glyphs[min(len(glyphs)-1, max(0, level)) if idx < len(glyphs) else -1]

        target_bytes = bytes.fromhex(shared.target_hex)

        # Draw strands
        for i in range(strand_length):
            for j, (phrase, cnt) in enumerate(strands):
                angle = (frame*0.12 + i*0.35 + j * (2*math.pi/num_strands)) % (2*math.pi)
                x = int(w//2 + radius * math.cos(angle))
                y = int(h//2 + radius * math.sin(angle) - strand_length//2 + i)
                if 0 <= y < h and 0 <= x < w:
                    ch = pick_glyph(j, cnt)
                    try:
                        pred_byte = j & 0xFF
                        target_byte = target_bytes[j % len(target_bytes)]
                        matches = 8 - bin(pred_byte ^ target_byte).count("1")
                        if matches == 8:
                            color_id = 1  # LightBlue
                        elif matches >= 6:
                            color_id = 2  # Green
                        elif matches >= 3:
                            color_id = 3  # Yellow
                        elif matches >= 1:
                            color_id = 5  # Orange
                        else:
                            color_id = 4  # Pink
                        stdscr.addstr(y, x, ch, curses.color_pair(color_id))
                    except:
                        pass

        # Legend of phrases
        for idx, (p, c) in enumerate(strands[:min(3, h-3)]):
            line = f"[{idx+1}] {p[:max(8, w-20)]}  ×{c}"
            try:
                stdscr.addstr(3+idx, 2, line)
            except:
                pass

        stdscr.refresh()

        try:
            if stdscr.getch() != -1:
                with shared.lock:
                    shared.running = False
                break
        except:
            pass

        frame += 1
        time.sleep(0.05)

def start_visualization(shared: SharedState):
    """Run curses visual in the MAIN thread; evolution will run in a worker thread."""
    try:
        import curses
    except Exception as e:
        # No curses available; visual disabled
        return False

    try:
        curses.wrapper(_visual_loop_curses, shared)
        return True
    except Exception as e:
        # If any terminal/curses error, skip visualization
        return False

# ============================== EVOLUTION (WORKER) ============================

def run_evolution_with_visual(shared: SharedState):
    global previous_best_hamming_distance, stagnation_counter
    random.seed()

    logln("-"*80)
    logln("  SENTINEL_OF_VOID_MERGED_VISUAL (v32.0 - WITH PRIVATE KEY EXTRACTION)")
    logln("  Now evolving towards SECP256K1 private key discovery via Void Dictionary")
    logln("-"*80)

    pk_hex = TARGET_DATA["pubkey_hex"]
    k_pred = model_timeline_A(pk_hex)
    k_true = model_timeline_B(pk_hex)
    v_error_target = k_pred ^ k_true

    dict_eng = VoidDictionaryEngine()
    analyzer = MultiDeltaAnalyzer(dict_eng)
    population = [GeneticSolver(generation=0) for _ in range(POPULATION_SIZE)]

    # NEW: Private key extraction tracking
    private_key_found = None
    extraction_attempts = 0

    shared.update(0, None, v_error_target, [])

    for gen in range(GENERATIONS):
        # FITNESS EVALUATION
        for s in population:
            s.calculate_fitness(v_error_target)

        # SURVIVOR PROCESSING
        population.sort(key=lambda x: x.fitness)
        survivors = population[:max(1, int(POPULATION_SIZE*SURVIVAL_RATE))]
        for s in survivors:
            dict_eng.record_survivor(s)

        # STAGNATION TRACKING
        best = population[0]
        best_hd = best.fitness
        if best_hd < previous_best_hamming_distance:
            previous_best_hamming_distance = best_hd
            generational_delta_repository.append(best.predicted_delta)
            stagnation_counter = 0
        else:
            stagnation_counter += 1
            if stagnation_counter >= STAGNATION_THRESHOLD:
                generational_delta_repository.append(best.predicted_delta)
                stagnation_counter = 0

        # VOID DICTIONARY ANALYSIS
        dict_eng.analyze(population)
        analyzer.analyze()

        # VISUAL UPDATE
        bucket = f"phrases_{TOP_PHRASES_LEN}"
        top_phrases = dict_eng.cumulative[bucket].most_common(16)
        shared.update(gen, best_hd, v_error_target, top_phrases)

        # NEW: PERIODIC PRIVATE KEY EXTRACTION ATTEMPTS
        if gen % 100 == 0 and gen > 0:  # Try every 100 generations
            extraction_attempts += 1
            logln(f"\n--- Private Key Extraction Attempt {extraction_attempts} (Gen {gen}) ---")
            
            private_key_candidate = void_dict_to_private_key(dict_eng, pk_hex, max_attempts=50)
            
            if private_key_candidate:
                logln("🎯 POTENTIAL PRIVATE KEY CANDIDATE FOUND!")
                logln(f"   Candidate: {private_key_candidate:064x}")
                
                # Verify it produces the correct public key
                if validate_private_key(private_key_candidate, pk_hex, CURVE_ORDER):
                    private_key_found = private_key_candidate
                    logln("💫 VERIFICATION SUCCESSFUL! PRIVATE KEY CONFIRMED!")
                    logln(f"   Private Key: {private_key_found:064x}")
                    
                    with shared.lock:
                        shared.converged = True
                        shared.private_key = private_key_found
                        shared.running = False
                    
                    # Log the breakthrough
                    logln("\n" + "="*80)
                    logln("  BREAKTHROUGH: SECP256K1 PRIVATE KEY EXTRACTED")
                    logln("  Via Void Dictionary Pattern Recognition")
                    logln(f"  Generation: {gen}")
                    logln(f"  Public Key: {pk_hex}")
                    logln(f"  Private Key: {private_key_found:064x}")
                    logln("="*80)
                    
                    return private_key_found
                else:
                    logln("   Verification failed - continuing search...")
            else:
                logln("   No valid candidate found this attempt")

        # CONVERGENCE CHECKS (original logic)
        proven_delta = analyzer.composite_deltas.get("Proven Mutations", 0)
        if proven_delta and hamming_distance(proven_delta, v_error_target) == 0:
            logln("\n" + "="*80)
            logln(f"  ANALYTICAL SUCCESS AT GENERATION {gen}: Composite matched target.")
            logln("="*80)
            display_report(gen, population, v_error_target, k_pred, analyzer, dict_eng)
            with shared.lock:
                shared.converged = True
                shared.running = False
            return None

        if best_hd == 0:
            logln("\n" + "="*80)
            logln("  EVOLUTIONARY SUCCESS: Perfect individual delta found.")
            logln(f"  Generation: {gen}")
            logln(f"  Perfect Δ: {best.predicted_delta:064x}")
            logln("="*80)
            display_report(gen, population, v_error_target, k_pred, analyzer, dict_eng)
            with shared.lock:
                shared.converged = True
                shared.running = False
            return None

        # PERIODIC REPORTING
        if gen % REPORT_INTERVAL == 0:
            display_report(gen, population, v_error_target, k_pred, analyzer, dict_eng)
            print_dictionary_snapshot(gen, dict_eng, f"{best.predicted_delta:064x}", v_error_target)

        # EVOLVE POPULATION
        population = evolve_population(population, gen + 1)

    # FINAL EXTRACTION ATTEMPT IF NOT ALREADY DONE
    if not private_key_found:
        logln("\n--- Final Private Key Extraction Attempt ---")
        private_key_found = void_dict_to_private_key(dict_eng, pk_hex, max_attempts=200)
        if private_key_found and validate_private_key(private_key_found, pk_hex, CURVE_ORDER):
            logln("💫 FINAL ATTEMPTS SUCCESSFUL! PRIVATE KEY FOUND!")
            logln(f"   Private Key: {private_key_found:064x}")

    display_report(GENERATIONS, population, v_error_target, k_pred, analyzer, dict_eng)
    with shared.lock:
        shared.running = False
    
    return private_key_found

# ============================== ENTRYPOINT ===================================

def main():
    shared = SharedState()

    logln("🚀 INITIALIZING ENHANCED SOLVER WITH PRIVATE KEY EXTRACTION")
    logln(f"🔑 TARGET PUBLIC KEY: {TARGET_DATA['pubkey_hex']}")
    logln("🌌 MASTER ALGORITHM INTEGRATION: ACTIVE")

    evo_thread = threading.Thread(target=run_evolution_with_visual, args=(shared,), daemon=True)
    evo_thread.start()

    visual_ok = start_visualization(shared)

    evo_thread.join()

    flush_logs_to_stdout()

    # FINAL STATUS REPORT
    if hasattr(shared, 'private_key') and shared.private_key:
        print("\n🎉 MISSION ACCOMPLISHED: PRIVATE KEY SUCCESSFULLY EXTRACTED!")
        print(f"   Private Key: {shared.private_key:064x}")
        print(f"   Public Key:  {TARGET_DATA['pubkey_hex']}")
        
        # Verify one more time
        if validate_private_key(shared.private_key, TARGET_DATA['pubkey_hex'], CURVE_ORDER):
            print("   ✅ VERIFICATION: PASSED")
        else:
            print("   ❌ VERIFICATION: FAILED (this shouldn't happen)")
    else:
        print("\n⚠️  Private key not found in this run.")
        print("   The Void Dictionary patterns may need more generations to converge.")
        print("   Consider increasing GENERATIONS or adjusting parameters.")

    if not visual_ok:
        print("\n[visualization disabled or unavailable — printed buffered report instead]")

if __name__ == "__main__":
    main()