from typing import List
import numpy as np
import matplotlib.pyplot as plt
import os

def token_to_rules(token: str) -> List[int]:
    """Convert underscore-delimited hex token into a list of Wolfram rules (0–255)."""
    segments = [seg.strip().lower() for seg in token.split("_") if seg.strip()]
    rules = []
    for seg in segments:
        val = int(seg, 16)           # interpret as hex
        rule = val % 256             # reduce mod 256
        rules.append(rule)
    return rules

def rule_lookup(rule: int) -> np.ndarray:
    """Build lookup table for one Wolfram rule."""
    bits = [(rule >> i) & 1 for i in reversed(range(8))]  # order 111..000
    lookup = np.zeros(8, dtype=np.uint8)
    for idx in range(8):
        lookup[idx] = bits[7 - idx]
    return lookup

def simulate_rule_sequence(rules: List[int], width: int = 201, steps: int = 150) -> np.ndarray:
    """Simulate a CA using a sequence of rules (cycling row by row)."""
    grid = np.zeros((steps, width), dtype=np.uint8)
    grid[0, width // 2] = 1  # single seed in center

    for r in range(1, steps):
        active_rule = rules[(r - 1) % len(rules)]
        lookup = rule_lookup(active_rule)
        prev = grid[r - 1]
        new = np.zeros(width, dtype=np.uint8)

        for i in range(width):
            idx = (prev[(i - 1) % width] << 2) | (prev[i] << 1) | (prev[(i + 1) % width])
            new[i] = lookup[idx]

        grid[r] = new

    return grid

def batch_process_tokens(tokens: List[str], outdir: str = "ca_outputs", width: int = 201, steps: int = 150):
    """Process a list of tokens: extract rules, simulate, save images."""
    os.makedirs(outdir, exist_ok=True)
    manifest = []

    for token in tokens:
        rules = token_to_rules(token)
        grid = simulate_rule_sequence(rules, width=width, steps=steps)

        # save image
        safe_name = token.replace("_", "-")
        filename = f"{safe_name}_rules{'-'.join(map(str,rules))}.png"
        filepath = os.path.join(outdir, filename)

        plt.figure(figsize=(8, 8))
        plt.imshow(grid, cmap="gray_r", interpolation="nearest")
        plt.title(f"Token: {token}\nRules: {rules}")
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(filepath, dpi=200)
        plt.close()

        manifest.append({"token": token, "rules": rules, "file": filepath})

    return manifest

# --- Example usage ---
if __name__ == "__main__":
    tokens = [
        "98bb_cb11a6_e81_c4ad14_f9",
        "cb11a6_e81_c4ad14_f9_3ed18",
        "b487_dc518848_1_8456b7_7",
        "dc518848_1_8456b7_7_36dd91",
        "d8fb_d91186_e856_dcab1_8f9",
        "d91186_e856_dcab1_8f9_3fd14",
        "bc87_cd41ea48_4_4458b78b8_4cc12",
        "b48f_dc41a848_5_8c5ab78f_14d599",
        "3c36_575_ae44814_5effa7c_837398a",
        "bc8f_5c41a848_5_8dab38f_14dc99",
    ]

    manifest = batch_process_tokens(tokens, outdir="ca_outputs_batch")

    # print summary
    for entry in manifest:
        print(f"Token: {entry['token']}")
        print(f"  Rules: {entry['rules']}")
        print(f"  Image: {entry['file']}")
        print()
