"""Place substations on the route plan so every route can be drawn to scale (Manhattan path, length = route length)."""
import random, json, net as N
random.seed(7)
NODES = ["PS"] + [f"S{i}" for i in range(1, 13)]
def ends(r): return ("PS" if r[1] in ("A", "B") else r[1]), r[2]
ROUTES = [(r[0], *ends(r), sum(L for _, L in r[3])) for r in N.ROUTES]
def cost(P):
    c = 0.0
    for rid, a, b, L in ROUTES:
        d = abs(P[a][0] - P[b][0]) + abs(P[a][1] - P[b][1])
        if d > 0.88 * L: c += (d - 0.88 * L) ** 2
        if d < 0.55 * L: c += (0.55 * L - d) ** 2
    for i, a in enumerate(NODES):
        for b in NODES[i + 1:]:
            d = abs(P[a][0] - P[b][0]) + abs(P[a][1] - P[b][1])
            if d < 450: c += (450 - d) ** 2
    return c
P = {n: (random.randint(-2000, 2000) // 10 * 10, random.randint(-2000, 2000) // 10 * 10) for n in NODES}; P["PS"] = (0, 0)
best = cost(P); T = 1e5
for it in range(200000):
    n = random.choice(NODES[1:]); old = P[n]
    P[n] = (old[0] + random.randint(-150, 150) // 10 * 10, old[1] + random.randint(-150, 150) // 10 * 10)
    c = cost(P)
    if c < best or random.random() < pow(2.718, -(c - best) / T): best = c
    else: P[n] = old
    T *= 0.99995
print("cost", best); json.dump(P, open("layout.json", "w"))
for rid, a, b, L in ROUTES:
    d = abs(P[a][0] - P[b][0]) + abs(P[a][1] - P[b][1]); print(rid, a, b, L, d, round(d / L, 2))
