
from fractions import Fraction
from karp_bellman import karp_max_cycle_mean, bellman_ford_potential

def verify_graph(states, edges, W, eta_goal=Fraction(0,1)):
    n = len(states)
    def weight_lookup(kk,t): return W(kk,t)
    overline = karp_max_cycle_mean(n, edges, weight_lookup)
    eta = eta_goal
    ok, h = bellman_ford_potential(n, edges, weight_lookup, eta)
    delta_h = (max(h)-min(h)) if ok else None
    return overline, eta, ok, delta_h, h
