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

def four_step_realizable_mod2_24(r:int, t:int, m:int, L:int, alpha1:int, alpha2:int):
    assert L==16
    MOD_LIFT = 1<<(m+2)    # 2^8 for m=6
    MOD = 1<<24
    t1 = (t + alpha1) % L
    t2 = (t + alpha1 + alpha2) % L
    t3 = (t + 2*alpha1 + alpha2) % L

    # enumerate representatives c in [0,2^24) with c ≡ r (mod 2^{m+2}), odd
    start = r % MOD
    step = MOD_LIFT
    c = start
    while c < MOD:
        if (c & 1)==1:
            n = c
            # step 1: k=1
            if v2(3*n + 1) == 1 and bin_membership_power16(n, t, L):
                T1 = (3*n + 1)//2
                # step 2: k=2
                if v2(3*T1 + 1) == 2 and bin_membership_power16(T1, t1, L):
                    # step 3: k=1
                    T2 = (3*T1 + 1)//4
                    if v2(3*T2 + 1) == 1 and bin_membership_power16(T2, t2, L):
                        # step 4: k=2
                        T3 = (3*T2 + 1)//2
                        if v2(3*T3 + 1) == 2 and bin_membership_power16(T3, t3, L):
                            return True
        c += step
    return False