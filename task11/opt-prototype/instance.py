"""Prototype instance generator for the array-cable layout task (scratch)."""
import json
import math
import random

TYPES = [  # (name, capacity in turbines, cost per metre)
    ("C1", 3, 100),
    ("C2", 5, 145),
    ("C3", 8, 210),
]


def make(seed, n=30, sub=(0, 0)):
    rng = random.Random(seed)
    pts = set()
    while len(pts) < n:
        x = rng.randrange(-7, 8) * 600 + rng.randrange(-120, 121, 40)
        y = rng.randrange(1, 10) * 600 + rng.randrange(-120, 121, 40)
        if all((x - a) ** 2 + (y - b) ** 2 >= 450 ** 2 for a, b in pts) and (x, y) != sub:
            pts.add((x, y))
    turbines = sorted(pts, key=lambda p: (p[1], p[0]))
    return {"substation": list(sub), "turbines": [list(p) for p in turbines], "types": TYPES}


def length(p, q):
    # metres, rounded half up to the nearest metre, integer arithmetic
    d2 = (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2
    r = math.isqrt(d2)
    # round half up: compare (r + 0.5)^2 with d2  ->  4 d2 >= (2r+1)^2
    return r + 1 if 4 * d2 >= (2 * r + 1) ** 2 else r


def orient(a, b, c):
    v = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    return (v > 0) - (v < 0)


def on_seg(a, b, c):
    return min(a[0], b[0]) <= c[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= c[1] <= max(a[1], b[1])


def cross(p1, p2, q1, q2):
    """True if closed segments share any point other than a common endpoint."""
    shared = {tuple(p1), tuple(p2)} & {tuple(q1), tuple(q2)}
    o1, o2, o3, o4 = orient(p1, p2, q1), orient(p1, p2, q2), orient(q1, q2, p1), orient(q1, q2, p2)
    if shared:
        # sharing an endpoint: only a problem if collinear and overlapping beyond the shared point
        if o1 == 0 and o2 == 0:
            s = shared.pop()
            others = [t for t in (tuple(p1), tuple(p2), tuple(q1), tuple(q2)) if t != s]
            if len(others) == 2:
                a, b = others
                # overlap iff a and b on the same side of s along the line
                return (a[0] - s[0]) * (b[0] - s[0]) + (a[1] - s[1]) * (b[1] - s[1]) > 0
        return False
    if o1 != o2 and o3 != o4:
        return True
    if o1 == 0 and on_seg(p1, p2, q1): return True
    if o2 == 0 and on_seg(p1, p2, q2): return True
    if o3 == 0 and on_seg(q1, q2, p1): return True
    if o4 == 0 and on_seg(q1, q2, p2): return True
    return False


if __name__ == "__main__":
    inst = make(11)
    json.dump(inst, open("inst.json", "w"), indent=1)
    print(len(inst["turbines"]), "turbines")


def make_grid(seed, rows=5, cols=6, spacing=800, jitter=160, sub=None):
    """Compact jittered row layout, substation at the field centre (integer metres)."""
    rng = random.Random(seed)
    turbines = []
    for r in range(rows):
        for c in range(cols):
            x = c * spacing + rng.randrange(-jitter, jitter + 1, 20)
            y = r * spacing + rng.randrange(-jitter, jitter + 1, 20) + (spacing // 2 if c % 2 else 0)
            turbines.append((x, y))
    if sub is None:
        sub = ((cols - 1) * spacing // 2 + 400, (rows - 1) * spacing // 2 + 200)
    turbines = sorted(turbines, key=lambda p: (p[1], p[0]))
    return {"substation": list(sub), "turbines": [list(p) for p in turbines], "types": TYPES}
