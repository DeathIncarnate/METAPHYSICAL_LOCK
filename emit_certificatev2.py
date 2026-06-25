import json
from fractions import Fraction
from builder_refined6 import build_edges_refined6
from verifier_refined import verify_graph

def frac_to_str(x: Fraction)->str:
    return f"{x.numerator}/{x.denominator}"

def main(m=6,L=16,w=1, alpha1=9, alpha2=-7):
    states, edges, W = build_edges_refined6(m,L,w,alpha1,alpha2,
                                            forbid_k1_after_k1=True,
                                            prune_committed_by_oracle=True)
    overline, eta, ok, delta_h, h = verify_graph(states, edges, W)
    out = {
        "m": m, "L": L, "w": w, "alpha1": alpha1, "alpha2": alpha2,
        "overline": frac_to_str(overline),
        "eta": frac_to_str(eta),
        "feasible": ok,
        "Delta_h": None if delta_h is None else frac_to_str(delta_h),
        "edges": edges,
        "weights": {
            "rule": "bin-tight",
            "k1_low": "0/1", "k1_high": "1/1",
            "k2_low": "-1/1", "k2_high": "0/1"
        },
        "h": [frac_to_str(x) for x in h] if ok else None
    }
    with open("certificate_six.json","w") as f:
        json.dump(out, f, indent=2)
    print("Wrote certificate_six.json")

if __name__=="__main__":
    main()
