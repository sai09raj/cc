"""Every leader end point lies on its own section (between its joints) and on no other pipe."""
import render, net as N
render.plan("/tmp/claude-0/-home-user-cc/d4dced91-29da-5e32-939d-2f48108a4558/scratchpad/wd/plan.png")
def pos_on(path, p):
    s = 0.0
    for (xa, ya), (xb, yb) in zip(path, path[1:]):
        seg = abs(xb - xa) + abs(yb - ya)
        if min(xa, xb) - 1e-9 <= p[0] <= max(xa, xb) + 1e-9 and min(ya, yb) - 1e-9 <= p[1] <= max(ya, yb) + 1e-9:
            return s + abs(p[0] - xa) + abs(p[1] - ya)
        s += seg
    return None
bad = []
secs = {p[0]: p[3] for p in N.PIPES}
for pid, k, pt in render.LEADERS:
    path = render.pts(pid); D = render.plen(path); L = sum(l for _, l in secs[pid])
    s = pos_on(path, pt); lo = sum(l for _, l in secs[pid][:k]) / L * D; hi = sum(l for _, l in secs[pid][:k + 1]) / L * D
    if s is None or not (lo + 0.05 < s < hi - 0.05): bad.append((pid, k, pt, s, lo, hi))
    others = [q for q in render.PATHS if q != pid and pos_on(render.pts(q), pt) is not None]
    if others: bad.append((pid, k, "also on", others))
print(len(render.LEADERS), "leaders; bad:", bad)
assert len(render.LEADERS) == sum(len(p[3]) for p in N.PIPES) and not bad
