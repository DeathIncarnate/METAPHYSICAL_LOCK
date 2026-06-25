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
BRAID_STRANDS         = 20                # # of strands displayed (top-N phrases)

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
        self.strands = []  # list of (phrase, count)
        self.running = True
        self.converged = False

    def update(self, generation, best_hd, target_int, phrases):
        with self.lock:
            self.generation = generation
            self.best_hd = best_hd
            self.target_hex = f"{target_int:064x}"
            self.strands = phrases[:BRAID_STRANDS]

# ============================== CURSES VISUAL =================================

def _visual_loop_curses(stdscr, shared: SharedState):
    import curses, math
    curses.curs_set(0)
    stdscr.nodelay(True)
    frame = 0

    glyphs = ['█', '▓', '▒', '░', '●', '•']
    while True:
        with shared.lock:
            running = shared.running
            strands = list(shared.strands)
            gen = shared.generation
            best_hd = shared.best_hd
            tgt = shared.target_hex

        if not running:
            break

        stdscr.erase()
        h, w = stdscr.getmaxyx()

        # Header
        title = "SENTINEL_OF_VOID — Live Convergence Braid"
        info  = f"Gen: {gen:>6}   Best HD: {best_hd if best_hd is not None else '-':>3}   Target: {tgt[-16:]}"
        try:
            stdscr.addstr(0, max(0, (w-len(title))//2), title)
            stdscr.addstr(1, max(0, (w-len(info))//2),  info)
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

        # Draw strands
        for i in range(strand_length):
            for j, (phrase, cnt) in enumerate(strands):
                # angular phase is derived from frame, row offset, and strand index
                angle = (frame*0.12 + i*0.35 + j * (2*math.pi/num_strands)) % (2*math.pi)
                x = int(w//2 + radius * math.cos(angle))
                y = int(h//2 + radius * math.sin(angle) - strand_length//2 + i)
                if 0 <= y < h and 0 <= x < w:
                    ch = pick_glyph(j, cnt)
                    try:
                        stdscr.addch(y, x, ch)
                    except:
                        pass

        # Legend of phrases:
        for idx, (p, c) in enumerate(strands[:min(3, h-3)]):
            line = f"[{idx+1}] {p[:max(8, w-20)]}  ×{c}"
            try:
                stdscr.addstr(3+idx, 2, line)
            except:
                pass

        stdscr.refresh()

        # Exit on key press
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
    logln("  SENTINEL_OF_VOID_MERGED_VISUAL (v31.0)")
    logln("  Evolving via GA + composite consensus + bitflux guidance + live braid")
    logln("-"*80)

    pk_hex = TARGET_DATA["pubkey_hex"]
    k_pred = model_timeline_A(pk_hex)
    k_true = model_timeline_B(pk_hex)
    v_error_target = k_pred ^ k_true

    dict_eng = VoidDictionaryEngine()
    analyzer = MultiDeltaAnalyzer(dict_eng)
    population = [GeneticSolver(generation=0) for _ in range(POPULATION_SIZE)]

    # initial update to shared
    shared.update(0, None, v_error_target, [])

    for gen in range(GENERATIONS):
        # fitness
        for s in population:
            s.calculate_fitness(v_error_target)

        # survivor aging & proven record
        population.sort(key=lambda x: x.fitness)
        survivors = population[:max(1, int(POPULATION_SIZE*SURVIVAL_RATE))]
        for s in survivors:
            dict_eng.record_survivor(s)

        # stagnation tracking
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

        # analyze language & composites
        dict_eng.analyze(population)
        analyzer.analyze()

        # live visual feed: top phrases for TOP_PHRASES_LEN
        bucket = f"phrases_{TOP_PHRASES_LEN}"
        top_phrases = dict_eng.cumulative[bucket].most_common(8)  # take more; visual will slice to BRAID_STRANDS
        shared.update(gen, best_hd, v_error_target, top_phrases)

        # comparator halt (consensus match)
        proven_delta = analyzer.composite_deltas.get("Proven Mutations", 0)
        if proven_delta and hamming_distance(proven_delta, v_error_target) == 0:
            logln("\n" + "="*80)
            logln(f"  ANALYTICAL SUCCESS AT GENERATION {gen}: Composite matched target.")
            logln("="*80)
            display_report(gen, population, v_error_target, k_pred, analyzer, dict_eng)
            with shared.lock:
                shared.converged = True
                shared.running = False
            return

        # individual perfect found
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
            return

        # periodic buffered reporting
        if gen % REPORT_INTERVAL == 0:
            display_report(gen, population, v_error_target, k_pred, analyzer, dict_eng)
            print_dictionary_snapshot(gen, dict_eng, f"{best.predicted_delta:064x}", v_error_target)

        # evolve
        population = evolve_population(population, gen + 1)

    # if loop ends
    display_report(GENERATIONS, population, v_error_target, k_pred, analyzer, dict_eng)
    with shared.lock:
        shared.running = False

# ============================== ENTRYPOINT ===================================

def main():
    shared = SharedState()

    # Start evolution in a worker thread
    evo_thread = threading.Thread(target=run_evolution_with_visual, args=(shared,), daemon=True)
    evo_thread.start()

    # Run visualization in main thread; if curses fails, we just wait for evo to complete
    visual_ok = start_visualization(shared)

    # Ensure evolution completes
    evo_thread.join()

    # If visualization was running, it's now stopped; flush buffered logs
    flush_logs_to_stdout()

    # If visualization never showed (or user pressed a key to exit early), print a note
    if not visual_ok:
        print("\n[visualization disabled or unavailable — printed buffered report instead]")

if __name__ == "__main__":
    main()
