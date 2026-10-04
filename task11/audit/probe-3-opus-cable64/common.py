"""Shared problem data / geometry for the optimizer (the checker does NOT import this)."""
import json, os
from math import isqrt
HERE = os.path.dirname(os.path.abspath(__file__))
FIELD = os.path.join(HERE, '..', 'field.json')
MAXLEN = 1300
TYPES_ALL = [('C1', 4, 100), ('C2', 8, 160), ('C3', 14, 245)]
SCEN = {
    'S1': ('substation_primary', ['C1', 'C2', 'C3'], 6),
    'S2': ('substation_primary', ['C1', 'C2', 'C3'], 5),
    'S3': ('substation_primary', ['C2', 'C3'], 6),
    'S4': ('substation_alternative', ['C1', 'C2', 'C3'], 6),
}

def rlen(a, b):
    d2 = (a[0]-b[0])**2 + (a[1]-b[1])**2
    n = isqrt(d2)
    if 4*d2 >= (2*n+1)**2:
        n += 1
    return n

def orient(a, b, c):
    v = (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])
    return (v > 0) - (v < 0)

def onseg(a, b, c):  # c collinear with a-b: is c within bbox
    return min(a[0], b[0]) <= c[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= c[1] <= max(a[1], b[1])

def seg_conflict(p1, p2, p3, p4):
    """True iff the two segments share a point other than a common endpoint
    (collinear overlap counts even with a shared endpoint)."""
    shared = [p for p in (p1, p2) if p in (p3, p4)]
    if len(shared) == 2:
        return True
    if len(shared) == 1:
        s = shared[0]
        q = p2 if p1 == s else p1
        r = p4 if p3 == s else p3
        if orient(s, q, r) != 0:
            return False
        return (q[0]-s[0])*(r[0]-s[0]) + (q[1]-s[1])*(r[1]-s[1]) > 0
    o1, o2, o3, o4 = orient(p1, p2, p3), orient(p1, p2, p4), orient(p3, p4, p1), orient(p3, p4, p2)
    if o1 != o2 and o3 != o4:
        return True
    if o1 == 0 and onseg(p1, p2, p3): return True
    if o2 == 0 and onseg(p1, p2, p4): return True
    if o3 == 0 and onseg(p3, p4, p1): return True
    if o4 == 0 and onseg(p3, p4, p2): return True
    return False

class Instance:
    def __init__(self, scen):
        F = json.load(open(FIELD))
        sub_key, tnames, K = SCEN[scen]
        self.scen = scen
        self.names = sorted(F['turbines'])
        self.n = len(self.names)
        self.P = [tuple(F['turbines'][k]) for k in self.names] + [tuple(F[sub_key])]
        self.root = self.n
        self.K = K
        self.types = [t for t in TYPES_ALL if t[0] in tnames]
        self.Q = max(t[1] for t in self.types)
        n = self.n
        self.L = [[rlen(self.P[i], self.P[j]) for j in range(n+1)] for i in range(n+1)]
        # undirected edges: turbine-turbine (<=MAXLEN) and turbine-root
        E = []
        for i in range(n):
            for j in range(i+1, n):
                if self.L[i][j] <= MAXLEN:
                    E.append((i, j))
        for i in range(n):
            E.append((i, n))
        self.E = E
        self.eid = {}
        for k, (i, j) in enumerate(E):
            self.eid[(i, j)] = k; self.eid[(j, i)] = k
        self.cross = [set() for _ in E]
        for a in range(len(E)):
            i, j = E[a]
            for b in range(a+1, len(E)):
                k, l = E[b]
                if seg_conflict(self.P[i], self.P[j], self.P[k], self.P[l]):
                    self.cross[a].add(b); self.cross[b].add(a)
        self.nbr = [[] for _ in range(n+1)]
        for (i, j) in E:
            self.nbr[i].append(j); self.nbr[j].append(i)

    def price(self, load):
        for name, cap, pr in self.types:
            if load <= cap:
                return pr
        return None

    def tname(self, load):
        for name, cap, pr in self.types:
            if load <= cap:
                return name
        return None

    def evaluate(self, parent):
        """parent[i] in 0..n (n=root). returns (cost, loads) or (None, reason)"""
        n = self.n
        load = [1]*n
        order = []
        depth = [-1]*(n+1); depth[n] = 0
        for i in range(n):
            path = []
            v = i
            while depth[v] < 0:
                path.append(v); v = parent[v]
                if len(path) > n: return None, 'cycle'
            for u in reversed(path):
                depth[u] = depth[parent[u]] + 1
        for i in sorted(range(n), key=lambda v: -depth[v]):
            p = parent[i]
            if p != n: load[p] += load[i]
        cost = 0
        for i in range(n):
            pr = self.price(load[i])
            if pr is None: return None, 'cap'
            cost += pr * self.L[i][parent[i]]
        return cost, load
