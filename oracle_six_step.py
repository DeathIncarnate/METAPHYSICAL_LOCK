
from fractions import Fraction

def v2(x:int)->int:
    v=0
    while x%2==0:
        x//=2; v+=1
    return v

def floor_log2(n:int)->int:
    return n.bit_length()-1

def mantissa_power16(n:int):
    s = floor_log2(n)
    m = Fraction(n, 1<<s)
    return m**16

def bin_membership_power16(n:int, t:int, L:int=16):
    m16 = mantissa_power16(n)
    return (m16 >= (1<<t)) and (m16 < (1<<(t+1)))

def six_step_realizable_mod2_24(r:int, t:int, m:int, L:int, alpha1:int, alpha2:int):
    """Finite, exact 6-step alternating (1,2,1,2,1,2) realizability for (m=6,L=16).
    Decision modulo 2^{m+2+4r} = 2^{24} using bin windows (top 16 bits) + lift (low 8 bits).
    Returns True iff there exists odd n in the class with required valuations and bins.
    Pattern phases: t, t+alpha1, t+alpha1+alpha2, t+2*alpha1+alpha2, t+2*alpha1+2*alpha2, t+3*alpha1+2*alpha2 (mod L).
    """
    assert L==16
    MOD_LIFT = 1<<(m+2)  # 2^8
    MOD = 1<<24
    # Precompute target phase bins for the six legs
    t0 = t % L
    t1 = (t + alpha1) % L
    t2 = (t + alpha1 + alpha2) % L
    t3 = (t + 2*alpha1 + alpha2) % L
    t4 = (t + 2*alpha1 + 2*alpha2) % L
    t5 = (t + 3*alpha1 + 2*alpha2) % L

    # Necessary valuation filter: for (1,2,1,2,1,2) we must have n ≡ 11 (mod 16)
    # (first 1,2 pair enforces it; the rest preserve it in practice—still check explicitly).
    start = r % MOD
    step = MOD_LIFT
    c = start
    while c < MOD:
        if (c & 1)==1 and (c & 0xF)==0xB:  # odd and 11 mod 16
            n = c
            # leg 0: k=1 at t0
            if v2(3*n + 1) != 1 or not bin_membership_power16(n, t0, L):
                c += step; continue
            T1 = (3*n + 1)//2
            # leg 1: k=2 at t1
            if v2(3*T1 + 1) != 2 or not bin_membership_power16(T1, t1, L):
                c += step; continue
            T2 = (3*T1 + 1)//4
            # leg 2: k=1 at t2
            if v2(3*T2 + 1) != 1 or not bin_membership_power16(T2, t2, L):
                c += step; continue
            T3 = (3*T2 + 1)//2
            # leg 3: k=2 at t3
            if v2(3*T3 + 1) != 2 or not bin_membership_power16(T3, t3, L):
                c += step; continue
            T4 = (3*T3 + 1)//4
            # leg 4: k=1 at t4
            if v2(3*T4 + 1) != 1 or not bin_membership_power16(T4, t4, L):
                c += step; continue
            T5 = (3*T4 + 1)//2
            # leg 5: k=2 at t5
            if v2(3*T5 + 1) != 2 or not bin_membership_power16(T5, t5, L):
                c += step; continue
            return True
        c += step
    return False
