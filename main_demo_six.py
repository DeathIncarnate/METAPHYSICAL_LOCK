
from fractions import Fraction
from builder_refined6 import build_edges_refined6
from verifier_refined import verify_graph

def run(m=6,L=16,w=1, alpha1=9, alpha2=-7, prune_committed=True):
    states, edges, W = build_edges_refined6(m,L,w,alpha1,alpha2,
                                            forbid_k1_after_k1=True,
                                            prune_committed_by_oracle=prune_committed)
    overline, eta, ok, delta_h, h = verify_graph(states, edges, W, eta_goal=Fraction(0,1))
    print("=== Refined-6 (committed prune = {}) ===".format(prune_committed))
    print(f"Params: m={m}, L={L}, w={w}, alpha1={alpha1}, alpha2={alpha2}")
    print(f"|X'|={len(states)}, |E'|={len(edges)}")
    print(f"Max cycle mean overline = {overline} (~{float(overline)})")
    print(f"Potential feasible at eta=0? {ok}")
    print(f"Δh(eta=0) = {delta_h} (~{float(delta_h) if delta_h is not None else None})")

if __name__=='__main__':
    run(prune_committed=True)
