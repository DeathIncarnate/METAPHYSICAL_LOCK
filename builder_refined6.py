
from itertools import product
from fractions import Fraction
from oracle_six_step import six_step_realizable_mod2_24

def v2(x:int)->int:
    v=0
    while x%2==0:
        x//=2; v+=1
    return v

def build_states6(m:int, L:int, w:int):
    residues = [r for r in range(1, 1<<(m+2), 2)]
    phases = list(range(L))
    histories = [tuple()] if w==0 else list(product((1,2), repeat=w))
    flags = [0,1,2,3,4,5,6]  # commit depth for 6-step
    states = [(r,t,h,phi) for r in residues for t in phases for h in histories for phi in flags]
    index = {s:i for i,s in enumerate(states)}
    return states, index

def shift_hist(sig, k, w):
    if w==0: return tuple()
    return (sig + (k,))[-w:]

def build_edges_refined6(m:int, L:int, w:int, alpha1:int, alpha2:int,
                         forbid_k1_after_k1:bool=True,
                         prune_committed_by_oracle:bool=True):
    states, idx = build_states6(m,L,w)
    MOD = 1<<(m+2)
    edges = []  # (u,v,kk,t_at_source)
    low_bins = set([0,1,2,3,4,5])
    def W(kk,t):
        if kk==1:
            return Fraction(0,1) if t in low_bins else Fraction(1,1)
        else:
            return Fraction(-1,1) if t in low_bins else Fraction(0,1)

    def add(u,v,kk,t):
        edges.append((u,v,kk,t))

    oracle_cache = {}

    for (r,t,h,phi), u in idx.items():
        kval = v2(3*r + 1)
        if kval not in (1,2):
            continue
        lastk = h[-1] if len(h)>0 else None
        if forbid_k1_after_k1 and lastk==1 and kval==1:
            continue

        y = ((3*r + 1) >> kval) % MOD
        tprime = (t + (alpha1 if kval==1 else alpha2)) % L
        hprime = shift_hist(h, kval, w)

        if phi==0:
            if kval==1:
                # free k1
                v = idx[(y,tprime,hprime,0)]
                add(u,v,1,t)
                # committed 6-step branch only from high bins
                if t not in low_bins:
                    keep_committed = True
                    if prune_committed_by_oracle:
                        key = (r,t)
                        if key not in oracle_cache:
                            keep = six_step_realizable_mod2_24(r, t, m, L, alpha1, alpha2)
                            oracle_cache[key] = keep
                        keep_committed = oracle_cache[key]
                    if keep_committed:
                        v1 = idx[(y,tprime,hprime,1)]
                        add(u,v1,1,t)
            else:
                # free k2
                v = idx[(y,tprime,hprime,0)]
                add(u,v,2,t)

        elif phi==1:
            # must take k2 to phase t+alpha1
            if kval==2 and tprime == (t + alpha1) % L:
                v2n = idx[(y,tprime,hprime,2)]
                add(u,v2n,2,t)
        elif phi==2:
            # must take k1 to phase t+alpha1+alpha2
            if kval==1 and tprime == (t + alpha1 + alpha2) % L:
                v3n = idx[(y,tprime,hprime,3)]
                add(u,v3n,1,t)
        elif phi==3:
            # must take k2 to phase t+2*alpha1+alpha2
            if kval==2 and tprime == (t + 2*alpha1 + alpha2) % L:
                v4n = idx[(y,tprime,hprime,4)]
                add(u,v4n,2,t)
        elif phi==4:
            # must take k1 to phase t+2*alpha1+2*alpha2
            if kval==1 and tprime == (t + 2*alpha1 + 2*alpha2) % L:
                v5n = idx[(y,tprime,hprime,5)]
                add(u,v5n,1,t)
        elif phi==5:
            # must take k2 to phase t+3*alpha1+2*alpha2, then finish
            if kval==2 and tprime == (t + 3*alpha1 + 2*alpha2) % L:
                v6n = idx[(y,tprime,hprime,6)]
                add(u,v6n,2,t)
        else:
            # phi==6: drop back to free with any valid kval
            v = idx[(y,tprime,hprime,0)]
            add(u,v,kval,t)

    return states, edges, W
