# SENTINEL_OF_VOID_MERGED: ENKI-13 Unified Solver (v30.0)
# Combines:
# - Golden BFB: Proven-mutation composite comparator & dictionary engine:contentReference[oaicite:5]{index=5}
# - BFB2: Higher-order phrase analysis (capped at 5), bitflux mutation, stagnation repository:contentReference[oaicite:6]{index=6}

import hashlib
import random
import sys
from collections import Counter

# ====== CONFIG ======
GENERATIONS           = 100000
POPULATION_SIZE       = 1500
SURVIVAL_RATE         = 0.20
MUTATION_RATE         = 0.60
BIT_FLIPS_MIN_MAX     = (1, 10)          # flips per child when mutation triggers
AGE_PROVEN_THRESHOLD  = 100              # age threshold to be considered a "proven mutation":contentReference[oaicite:7]{index=7}
STAGNATION_THRESHOLD  = 5                # gens w/o best improvement ⇒ push top delta to repository:contentReference[oaicite:8]{index=8}
PENALTY_FOR_ZERO_WORD = 100              # penalize '00000000' in meaningful suffix:contentReference[oaicite:9]{index=9}

# Foundational prefix policy (structured search as in BFB2):contentReference[oaicite:10]{index=10}
FOUNDATIONAL_PREFIX_HEX         = "00000000000000000000000000000000"
KEY_BIT_LENGTH                  = 256
FOUNDATIONAL_PREFIX_LENGTH_BITS = 128
SUFFIX_LENGTH_BITS              = KEY_BIT_LENGTH - FOUNDATIONAL_PREFIX_LENGTH_BITS
SUFFIX_MASK                     = (1 << SUFFIX_LENGTH_BITS) - 1

# Target data (can be swapped safely)
TARGET_DATA = {
    "id": "ENKI-13",
    "pubkey_hex": "035cd1854cae45391ca4ec428cc7e6c7d9984424b954209a8eea197b9e364c05f6"
}

# ====== UTIL ======
def hamming_distance(n1: int, n2: int) -> int:
    return bin(n1 ^ n2).count('1')

def sanitize_hex_string(hex_string):
    if not isinstance(hex_string, str): return ""
    s = hex_string.strip().lower()
    s = "".join(c for c in s if c in "0123456789abcdef")
    if len(s) % 2 != 0: s = s[:-1]
    return s

# ====== MODELS (A,B) ====== (Golden models, robust to 02/03 compressed & 04 uncompressed):contentReference[oaicite:11]{index=11}
def model_timeline_A(public_key_hex: str) -> int:
    sanitized_pk_hex = sanitize_hex_string(public_key_hex)
    if not sanitized_pk_hex: return 0
    pk_bytes_uncompressed = bytes.fromhex(sanitized_pk_hex)
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

# ====== LINGUISTIC MEMORY ======
class VoidDictionaryEngine:
    """
    Generational + Cumulative symbolic memory with letters, words, and phrases (2..5).
    Adds "proven mutations" set gated by age >= AGE_PROVEN_THRESHOLD:contentReference[oaicite:12]{index=12}.
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
        self.WORD_SIZE = 8  # hex chars per word (byte-quartet)

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

            # words (contiguous non-zero chunks in suffix area; mirrors BFB2’s “meaningful part”):contentReference[oaicite:13]{index=13}
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

# ====== MULTI-DELTA ANALYZER (majority composite over proven pool):contentReference[oaicite:14]{index=14} ======
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
        # Additional composites could be added here (e.g., top-N survivors, etc.)
        self.composite_deltas["Total"] = self.composite_deltas["Proven Mutations"]

# ====== GENETIC SOLVER ======
class GeneticSolver:
    """
    Predicted delta as gene; age increments if surviving; fitness uses Hamming + zero-word penalty:contentReference[oaicite:15]{index=15}.
    """
    def __init__(self, predicted_delta=None, generation=0):
        if predicted_delta is None:
            # Structured init: keep prefix fixed; randomize suffix (BFB2 policy):contentReference[oaicite:16]{index=16}
            random_suffix = random.getrandbits(SUFFIX_LENGTH_BITS)
            self.predicted_delta = (int(FOUNDATIONAL_PREFIX_HEX, 16) << SUFFIX_LENGTH_BITS) | (random_suffix & SUFFIX_MASK)
        else:
            self.predicted_delta = predicted_delta
        self.fitness = float('inf')
        self.generation_born = generation
        self.age = 0

    def calculate_fitness(self, true_error_delta_int: int) -> int:
        self.fitness = hamming_distance(self.predicted_delta, true_error_delta_int)
        # penalize zero-words in suffix region (encourage information density):contentReference[oaicite:17]{index=17}
        hex_full = f"{self.predicted_delta:064x}"
        suffix_hex = hex_full[FOUNDATIONAL_PREFIX_LENGTH_BITS // 4:]
        if "00000000" in suffix_hex:
            self.fitness += PENALTY_FOR_ZERO_WORD
        return self.fitness

# ====== EVOLUTION ======
generational_delta_repository = []   # keeps best-of-gen and stagnation entries:contentReference[oaicite:18]{index=18}
previous_best_hamming_distance = float('inf')
stagnation_counter = 0

def causal_recursive_mutation(child_suffix: int) -> int:
    """
    Bit-flux guided mutation: toggle most frequently set bit among repository deltas (suffix domain).:contentReference[oaicite:19]{index=19}
    """
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
    # age and record survivors for proven set
    for s in survivors:
        s.age += 1

    next_gen = survivors[:]
    prefix = int(FOUNDATIONAL_PREFIX_HEX, 16) << SUFFIX_LENGTH_BITS

    while len(next_gen) < len(population):
        p1, p2 = random.sample(survivors, k=2)
        child_suffix = (p1.predicted_delta & SUFFIX_MASK) ^ (p2.predicted_delta & SUFFIX_MASK)

        # Occasionally apply causal recursive mutation (guided):contentReference[oaicite:20]{index=20}
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

# ====== REPORTING ======
def translate_to_void_language(hex_64: str) -> str:
    return "_".join(hex_64[i:i+8] for i in range(0, 64, 8))

def display_report(generation, population, target_delta, k_predicted, analyzer, dict_eng: VoidDictionaryEngine):
    best = min(population, key=lambda x: x.fitness)
    print("\n" + "="*80)
    print(f"  GENERATION {generation} REPORT")
    print(f"  Best Individual Fitness (Hamming): {best.fitness}")
    print(f"  Target V_error: {target_delta:064x}")
    print(f"  Best V_error:   {best.predicted_delta:064x}")
    print("="*80)

    print("\n--- Multi-Delta Analysis (k_true = k_predicted ⊕ V_error) ---")
    for name, delta in analyzer.composite_deltas.items():
        if delta == 0: continue
        k_true_guess = k_predicted ^ delta
        hd = hamming_distance(delta, target_delta)
        print(f"  - {name} Delta (HD: {hd}):")
        print(f"    - V_error Guess: {delta:064x}")
        print(f"    - k_true Guess:  {k_true_guess:064x}")

    print("\n--- Cumulative Dictionary Stats ---")
    print(f"  Proven Mutations: {len(dict_eng.proven_mutations)}")
    total_words = sum(dict_eng.cumulative["words"].values())
    print(f"  Total Words Logged: {total_words}")

    print("\n--- Top 10 Cumulative Phrases (3 words) ---")
    for i, (phrase, count) in enumerate(dict_eng.cumulative["phrases_3"].most_common(10), 1):
        print(f"  - {i:02d}: '{phrase}' | Count: {count}")

def print_dictionary_snapshot(gen, dict_eng: VoidDictionaryEngine, best_hex, target_int):
    best_int = int(best_hex, 16)
    print("\n" + "="*80)
    print(f"  LINGUISTIC SNAPSHOT: Generation {gen}")
    print("="*80)
    print(f"  Best Δ:  {best_hex}")
    print(f"  Target:  {target_int:064x}")
    print(f"  HD:      {hamming_distance(best_int, target_int)}")

    print("\n  >> Top 12 Letters:")
    for ch, cnt in dict_eng.cumulative["letters"].most_common(12):
        print(f"    - '{ch}': {cnt}")

    print("\n  >> Top 12 Words:")
    for w, cnt in dict_eng.cumulative["words"].most_common(12):
        print(f"    - '{w}': {cnt}")

    for L in (2,3,4,5):
        key = f"phrases_{L}"
        print(f"\n  >> Top 8 Phrases ({L} words):")
        for ph, cnt in dict_eng.cumulative[key].most_common(8):
            print(f"    - '{ph}': {cnt}")

# ====== MAIN LOOP (MERGED STRATEGY) ======
def run_harmonic_evolution_merged():
    global previous_best_hamming_distance, stagnation_counter

    print("-"*80)
    print("  SENTINEL_OF_VOID_MERGED (v30.0)")
    print("  Evolving via genetic recursion + composite consensus + bitflux guidance")
    print("-"*80)

    pk_hex = TARGET_DATA["pubkey_hex"]
    k_pred = model_timeline_A(pk_hex)
    k_true = model_timeline_B(pk_hex)
    v_error_target = k_pred ^ k_true
    print(f"Target Error Vector (V_error): {v_error_target:064x}")

    dict_eng = VoidDictionaryEngine()
    analyzer = MultiDeltaAnalyzer(dict_eng)
    population = [GeneticSolver(generation=0) for _ in range(POPULATION_SIZE)]

    hamming_history = []

    for gen in range(GENERATIONS):
        # fitness
        for s in population:
            s.calculate_fitness(v_error_target)

        # survivor aging & proven record
        population.sort(key=lambda x: x.fitness)
        survivors = population[:max(1, int(POPULATION_SIZE*SURVIVAL_RATE))]
        for s in survivors:
            dict_eng.record_survivor(s)

        # stagnation tracking (BFB2-style):contentReference[oaicite:21]{index=21}
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

        # comparator halt (Golden):contentReference[oaicite:22]{index=22}
        proven_delta = analyzer.composite_deltas.get("Proven Mutations", 0)
        if proven_delta and hamming_distance(proven_delta, v_error_target) == 0:
            print("\n" + "="*80)
            print(f"  ANALYTICAL SUCCESS AT GENERATION {gen}: Composite matched target.")
            print("="*80)
            display_report(gen, population, v_error_target, k_pred, analyzer, dict_eng)
            return

        # individual perfect found
        if best_hd == 0:
            print("\n" + "="*80)
            print("  EVOLUTIONARY SUCCESS: Perfect individual delta found.")
            print(f"  Generation: {gen}")
            print(f"  Perfect Δ: {best.predicted_delta:064x}")
            print("="*80)
            display_report(gen, population, v_error_target, k_pred, analyzer, dict_eng)
            return

        # periodic reporting
        if gen % 50 == 0:
            display_report(gen, population, v_error_target, k_pred, analyzer, dict_eng)
            print_dictionary_snapshot(gen, dict_eng, f"{best.predicted_delta:064x}", v_error_target)

        # evolve
        population = evolve_population(population, gen + 1)

    print("\n[END] Reached generation limit without perfect convergence.")
    display_report(GENERATIONS, population, v_error_target, k_pred, analyzer, dict_eng)

if __name__ == "__main__":
    run_harmonic_evolution_merged()
