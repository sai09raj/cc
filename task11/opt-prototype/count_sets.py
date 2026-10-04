import instance, time, sys
inst = instance.make_grid(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))
P = [tuple(p) for p in inst["turbines"]]; n = len(P)
adj = [[j for j in range(n) if j != i and instance.length(P[i], P[j]) <= 1300] for i in range(n)]
print("n", n, "avg degree", sum(map(len, adj)) / n)
maxk = int(sys.argv[4]); counts = [0] * (maxk + 1); t0 = time.time()
# ESU-style enumeration of connected induced subgraphs, each counted once (min vertex = v)
def extend(sub, ext, v):
    counts[len(sub)] += 1
    if len(sub) == maxk: return
    ext = list(ext)
    while ext:
        w = ext.pop()
        new_ext = ext + [u for u in adj[w] if u > v and u not in sub and all(u not in adj[s] and u != s for s in sub)]
        extend(sub | {w}, new_ext, v)
for v in range(n):
    extend({v}, [u for u in adj[v] if u > v], v)
print("counts by size", counts[1:], "time", round(time.time() - t0, 1))
