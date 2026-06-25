
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
    # Check u(n) in I_t using exact comparison via 16th powers (since L=16)
    # condition: 2^t <= (n/2^s)^16 < 2^{t+1}
    m16 = mantissa_power16(n)
    return (m16 >= (1<<t)) and (m16 < (1<<(t+1)))

def two_step_realizable_mod2_16(r:int, t:int, m:int, L:int, alpha1:int):
    """Finite, exact two-step realizability test for (m=6,L=16).

    Decide existence of n modulo 2^{m+2+2r} with:
      (R1) n ≡ r (mod 2^{m+2})
      (R2) v2(3n+1) = 1
      (R3) u(n) in I_t
      (R4) v2(3T(n)+1) = 2
      (R5) u(T(n)) in I_{t+alpha1}
    For L=16, reduce to search modulo 2^{16}.
    """
    MOD_LIFT = 1<<(m+2)
    MOD = 1<<16  # m+2+2r = 6+2+8 = 16 for (m=6,L=16)
    assert L==16 and MOD_LIFT <= MOD

    targets = []
    # enumerate residues c in [0,2^16) with c ≡ r (mod 2^{m+2}), odd, and c ≡ 11 (mod 16)
    start = r % MOD
    step = MOD_LIFT
    c = start
    while c < MOD:
        if (c & 1)==1 and (c & 0xF)==0xB:  # odd and 11 mod 16
            targets.append(c)
        c += step

    if not targets:
        return False  # no representative even satisfies necessary congruence

    for c in targets:
        n = c
        if v2(3*n + 1) != 1:
            continue
        if not bin_membership_power16(n, t, L):
            continue
        Tn = (3*n + 1)//2
        if v2(3*Tn + 1) != 2:
            continue
        if not bin_membership_power16(Tn, (t+alpha1)%L, L):
            continue
        return True

    return False
