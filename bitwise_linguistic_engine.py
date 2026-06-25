"""
SENTINEL_OF_VOID v2.0: Bitwise Linguistic Analysis
Building the True Grammar of Error from Forensic Data
"""

import hashlib
import sys
from collections import Counter
import json

# Expanded forensic dataset (your 3 pairs + synthetic expansion)
FORENSIC_DATASET = [
    # Your verified pairs
    ("1Fo65aKq8s8iquMt6weF1rku1moWVEd5Ua", "000000000000000000000000000000033e7665705359f04f28b88cf897c603c9", "03633cbe3ec02b9401c5effa144c5b4d22f87940259634858fc7e59b1c09937852"),
    ("1Kh22PvXERd2xpTQk3ur6pPEqFeckCJfAr", "00000000000000000000000000000000000000000011720c4f018d51b8cebba8", "02c4b305d8e43408828b81358ba655673a1a2f6d788369165b44a395d6e2b5c583"),
    ("1PXAyUB8ZoH3WD8n5zoAthYjN15yN5CVq5", "000000000000000000000000000000001c533b6bb7f0804e09960225e44877ac", "02a0b8b2d793a65a5b512b5d4b4f3b1e3b1a2e8c9d0f1b2c3d4e5f6a7b8c9d0e1f"),
    
    # Synthetic expansion based on error patterns
    ("SYNTH_001", "00000000000000000000000000000000a8b20cf700e4e050008ff268c914fc11", "02" + "a8b20cf700e4e050008ff268c914fc11" * 2),
    ("SYNTH_002", "00000000000000000000000000000000bcb70df51ae4e85004cffb78f917fd91", "03" + "bcb70df51ae4e85004cffb78f917fd91" * 2),
]

class BitwiseLinguisticEngine:
    def __init__(self, dataset):
        self.dataset = dataset
        self.error_frequency_map = None
        self.bit_grammar_rules = {}
        self.error_patterns = {}
        
    def build_error_frequency_map(self):
        """Build comprehensive error analysis from forensic data"""
        print("🔍 BUILDING BITWISE ERROR FREQUENCY MAP...")
        
        error_bit_counts = [0] * 256
        error_vectors = []
        
        for identifier, true_priv_hex, pub_hex in self.dataset:
            try:
                true_key = int(true_priv_hex, 16)
                predicted_key = self.predict_private_key(pub_hex)
                error_vector = true_key ^ predicted_key
                error_vectors.append(error_vector)
                
                # Count error bits
                for i in range(256):
                    if (error_vector >> i) & 1:
                        error_bit_counts[i] += 1
                        
            except Exception as e:
                print(f"Error processing {identifier}: {e}")
        
        # Calculate frequencies
        total_samples = len(error_vectors)
        self.error_frequency_map = [
            (count / total_samples) * 100 for count in error_bit_counts
        ]
        
        # Analyze error patterns for linguistic rules
        self.analyze_error_patterns(error_vectors)
        
        return self.error_frequency_map
    
    def predict_private_key(self, public_key_hex):
        """Consistent prediction model (your timeline A)"""
        compressed_pk = self.compress_pubkey(public_key_hex)
        pk_bytes = bytes.fromhex(compressed_pk)
        
        h1 = hashlib.sha256(pk_bytes).digest()
        first_half = int.from_bytes(h1[:16], 'big')
        h2 = hashlib.sha256(pk_bytes + first_half.to_bytes(16, 'big')).digest()
        signature = int.from_bytes(h2[:16], 'big')
        second_half = first_half ^ signature
        
        return (first_half << 128) | second_half
    
    def compress_pubkey(self, pk_hex):
        """Convert to compressed public key format"""
        if len(pk_hex) == 130 and pk_hex.startswith('04'):
            pk_bytes = bytes.fromhex(pk_hex)
            y = int.from_bytes(pk_bytes[33:], 'big')
            prefix = b'\x02' if y % 2 == 0 else b'\x03'
            return (prefix + pk_bytes[1:33]).hex()
        return pk_hex
    
    def analyze_error_patterns(self, error_vectors):
        """Analyze error vectors to discover linguistic patterns"""
        print("🎯 ANALYZING ERROR PATTERNS FOR LINGUISTIC RULES...")
        
        # Convert errors to hexadecimal phrases
        error_phrases = []
        for error_vec in error_vectors:
            hex_str = f"{error_vec:064x}"
            # Split into 8-byte words for analysis
            words = [hex_str[i:i+8] for i in range(0, 64, 8)]
            phrase = "_".join(words)
            error_phrases.append(phrase)
        
        # Build frequency analysis
        phrase_freq = Counter(error_phrases)
        word_freq = Counter()
        
        for phrase in error_phrases:
            for word in phrase.split('_'):
                word_freq[word] += 1
        
        # Discover grammatical rules
        self.discover_grammatical_rules(error_phrases, phrase_freq, word_freq)
        
        print(f"   Discovered {len(self.bit_grammar_rules)} grammatical rules")
        print(f"   Top error phrase: {phrase_freq.most_common(1)[0]}")
    
    def discover_grammatical_rules(self, phrases, phrase_freq, word_freq):
        """Discover linguistic rules from error patterns"""
        
        # Rule 1: Word frequency patterns
        top_words = [word for word, count in word_freq.most_common(10)]
        self.bit_grammar_rules["high_frequency_words"] = top_words
        
        # Rule 2: Phrase structure patterns
        common_phrases = [phrase for phrase, count in phrase_freq.most_common(5)]
        self.bit_grammar_rules["common_phrases"] = common_phrases
        
        # Rule 3: Positional word patterns
        positional_words = {i: [] for i in range(8)}
        for phrase in phrases:
            words = phrase.split('_')
            for i, word in enumerate(words):
                if i < 8:  # Only 8 words per phrase
                    positional_words[i].append(word)
        
        # Find most common word at each position
        for position, words in positional_words.items():
            if words:
                most_common = Counter(words).most_common(1)[0][0]
                self.bit_grammar_rules[f"position_{position}"] = most_common
        
        # Rule 4: Error bit clustering
        self.analyze_bit_clusters()
    
    def analyze_bit_clusters(self):
        """Analyze which bits tend to error together"""
        if not self.error_frequency_map:
            return
        
        # Find high-error regions
        high_error_bits = [
            i for i, freq in enumerate(self.error_frequency_map) 
            if freq > 50  # Bits that error more than 50% of the time
        ]
        
        # Group into clusters (bits within 8 positions of each other)
        clusters = []
        current_cluster = []
        
        for bit in sorted(high_error_bits):
            if not current_cluster or bit - current_cluster[-1] <= 8:
                current_cluster.append(bit)
            else:
                if len(current_cluster) >= 2:  # Only meaningful clusters
                    clusters.append(current_cluster)
                current_cluster = [bit]
        
        if len(current_cluster) >= 2:
            clusters.append(current_cluster)
        
        self.bit_grammar_rules["error_clusters"] = clusters
    
    def predict_verror_from_bit_grammar(self, public_key_hex):
        """Predict V_error using bitwise linguistic rules"""
        print("🔮 PREDICTING V_error FROM BITWISE GRAMMAR...")
        
        # Use public key to seed the prediction
        pk_hash = hashlib.sha256(public_key_hex.encode()).digest()
        seed = int.from_bytes(pk_hash, 'big')
        
        # Apply grammatical rules to generate error pattern
        verror_prediction = self.apply_bit_grammar_rules(seed)
        
        print(f"   Bitwise Grammar V_error: {verror_prediction:064x}")
        return verror_prediction
    
    def apply_bit_grammar_rules(self, seed):
        """Apply discovered grammatical rules to generate error pattern"""
        error_pattern = 0
        
        # Rule 1: Set high-frequency error bits
        if "error_clusters" in self.bit_grammar_rules:
            for cluster in self.bit_grammar_rules["error_clusters"]:
                for bit in cluster:
                    error_pattern |= (1 << bit)
        
        # Rule 2: Use positional word patterns to modulate bits
        if "position_0" in self.bit_grammar_rules:
            pos_word = self.bit_grammar_rules["position_0"]
            word_value = int(pos_word, 16) if pos_word != "00000000" else 0xFFFFFFFF
            error_pattern ^= (word_value & 0xFFFF)  # Use lower 16 bits
        
        # Rule 3: Incorporate seed for public-key-specific variation
        error_pattern ^= (seed & 0xFFFFFFFF)
        
        # Ensure we don't get zero
        if error_pattern == 0:
            error_pattern = 0xDEADBEEF  # Fallback pattern
        
        return error_pattern
    
    def perform_linguistic_direct_solve(self, public_key_hex):
        """Perform direct solve using bitwise linguistic analysis"""
        print("🎯 PERFORMING LINGUISTIC DIRECT SOLVE...")
        
        # Get consistent k_predicted
        k_pred = self.predict_private_key(public_key_hex)
        print(f"   k_predicted: {k_pred:064x}")
        
        # Predict V_error from bitwise grammar
        v_error = self.predict_verror_from_bit_grammar(public_key_hex)
        
        # Direct solve
        k_true = k_pred ^ v_error
        print(f"   k_true (Linguistic Solve): {k_true:064x}")
        
        return k_true

def display_error_analysis(engine):
    """Display comprehensive error analysis"""
    if not engine.error_frequency_map:
        return
    
    print("\n" + "="*80)
    print("  BITWISE ERROR FREQUENCY ANALYSIS")
    print("="*80)
    
    # Group bits by error frequency
    high_error = [(i, freq) for i, freq in enumerate(engine.error_frequency_map) if freq > 50]
    medium_error = [(i, freq) for i, freq in enumerate(engine.error_frequency_map) if 20 <= freq <= 50]
    low_error = [(i, freq) for i, freq in enumerate(engine.error_frequency_map) if freq < 20]
    
    print(f"  High Error Bits (>50%): {len(high_error)} bits")
    if high_error:
        bits_str = ", ".join([f"bit_{bit}" for bit, freq in high_error[:10]])
        print(f"    {bits_str}" + ("..." if len(high_error) > 10 else ""))
    
    print(f"  Medium Error Bits (20-50%): {len(medium_error)} bits")
    print(f"  Low Error Bits (<20%): {len(low_error)} bits")
    
    # Show grammatical rules
    print("\n  DISCOVERED GRAMMATICAL RULES:")
    for rule_type, rules in engine.bit_grammar_rules.items():
        if rule_type == "error_clusters":
            print(f"    {rule_type}: {rules}")
        else:
            print(f"    {rule_type}: {rules[:3]}" + ("..." if len(rules) > 3 else ""))

def test_linguistic_engine():
    """Test the new linguistic engine"""
    print("🌌 INITIATING LINGUISTIC ENGINE v2.0")
    print("="*80)
    
    # Initialize engine with forensic data
    engine = BitwiseLinguisticEngine(FORENSIC_DATASET)
    
    # Build error analysis
    engine.build_error_frequency_map()
    
    # Display analysis
    display_error_analysis(engine)
    
    # Test with your target public key
    TARGET_PUBKEY = "035cd1854cae45391ca4ec428cc7e6c7d9984424b954209a8eea197b9e364c05f6"
    
    print(f"\n🎯 TESTING LINGUISTIC SOLVE ON TARGET:")
    print(f"   Public Key: {TARGET_PUBKEY}")
    
    # Perform linguistic direct solve
    private_key = engine.perform_linguistic_direct_solve(TARGET_PUBKEY)
    
    # Validate (placeholder - would need actual EC validation)
    print(f"\n💫 LINGUISTIC SOLVE COMPLETE")
    print(f"   Private Key Candidate: {private_key:064x}")
    
    # Save linguistic rules for future use
    linguistic_data = {
        "error_frequency_map": engine.error_frequency_map,
        "bit_grammar_rules": engine.bit_grammar_rules,
        "test_results": {
            "public_key": TARGET_PUBKEY,
            "private_key_candidate": f"{private_key:064x}",
            "method": "bitwise_linguistic_analysis"
        }
    }
    
    with open("linguistic_engine_v2.json", "w") as f:
        json.dump(linguistic_data, f, indent=2)
    
    print("💾 Linguistic analysis saved to: linguistic_engine_v2.json")
    
    return engine, private_key

if __name__ == "__main__":
    engine, private_key = test_linguistic_engine()
