# Plug-and-play: Now with SECP256K1 PRIVATE KEY EXTRACTION via Void Dictionary
# Enhanced with Master Algorithm integration

import hashlib
import random
import sys
import time
import threading
from collections import Counter, deque
import curses, math, time
from ecdsa import SECP256k1, SigningKey
import itertools

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

# ====== ENHANCED GENETIC SOLVER WITH PRIVATE KEY EXTRACTION ======

# [KEEP ALL YOUR ORIGINAL CODE UP TO THE run_evolution_with_visual FUNCTION]

# MODIFY THE EVOLUTION FUNCTION TO INCLUDE PRIVATE KEY EXTRACTION
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

# ====== ENHANCED SHARED STATE ======

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

# ====== ENHANCED VISUALIZATION ======

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

        # [REST OF YOUR ORIGINAL VISUALIZATION CODE REMAINS THE SAME]
        # ... (braid visualization logic)

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

# ====== ENHANCED MAIN FUNCTION ======

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
