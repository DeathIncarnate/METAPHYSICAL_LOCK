from builder_refined6 import build_edges_refined6

def dump_committed(m=6,L=16,w=1, alpha1=9, alpha2=-7):
    states, edges, W = build_edges_refined6(m,L,w,alpha1,alpha2,
                                            forbid_k1_after_k1=True,
                                            prune_committed_by_oracle=True)
    # committed edges are those with phi=1 in source state
    committed_pairs = set()
    for (r,t,h,phi), idx in states:
        if phi==1:
            committed_pairs.add((r,t))
    print("Committed bricks (r,t):")
    for pair in sorted(committed_pairs):
        print(pair)

if __name__=='__main__':
    dump_committed()
