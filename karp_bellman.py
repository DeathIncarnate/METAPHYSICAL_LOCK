
from fractions import Fraction

def karp_max_cycle_mean(n, edges, weight_lookup):
    neg_inf = Fraction(-10**12,1)
    dp = [[neg_inf]*n for _ in range(n+1)]
    for v in range(n):
        dp[0][v] = Fraction(0,1)
    for k in range(1,n+1):
        rowk = dp[k]; rowkm1 = dp[k-1]
        for (u,v,kk,t) in edges:
            w = weight_lookup(kk,t)
            pv = rowkm1[u]
            if pv > neg_inf/2:
                val = pv + w
                if val > rowk[v]: rowk[v] = val
    best = neg_inf
    for v in range(n):
        if dp[n][v] <= neg_inf/2: continue
        cur = Fraction(10**12,1)
        for k in range(n):
            if dp[k][v] <= neg_inf/2: continue
            val = (dp[n][v] - dp[k][v]) / (n - k)
            if val < cur: cur = val
        if cur > best: best = cur
    return best

def bellman_ford_potential(n, edges, weight_lookup, eta):
    costs = []
    for (u,v,kk,t) in edges:
        w = weight_lookup(kk,t)
        costs.append((v,u, -(w+eta)))
    dist = [Fraction(0,1)]*n
    for _ in range(n-1):
        updated=False
        for (u,v,c) in costs:
            nd = dist[u] + c
            if nd < dist[v]:
                dist[v]=nd; updated=True
        if not updated: break
    for (u,v,c) in costs:
        if dist[u] + c < dist[v]:
            return False, []
    return True, dist
