"""TENURE-11 prototype v2 (scratch). Parametrised for tuning."""
import itertools, time

P = dict(
    ALIGN=8, HEADER=16, OLD_SIZE=160 * 1024, MIN_SPLIT=32,
    RING=64, REG_COUNT=16, N_OPS=26000, LISTDROP=1500,
    EDENS=[16384, 24576, 32768, 49152], SURVS=[8192, 24576], TENS=[1, 2, 3, 5],
    POLICIES=["FIRST", "BEST", "NEXT"], PTS=[0, 768, 1024], FIXED_POLICY="FIRST",
)
KINDS = {"TEMP": (24, 0), "SESSION": (96, 2), "BLOB": (96, 0), "ENTRY": (56, 1), "NODE": (40, 1), "REG": (112, 4)}
VAR = {"BLOB": (13, 32), "NODE": (5, 8), "ENTRY": (3, 24)}
MIXES = {
    "warm":   ["TEMP", "TEMP", "SESSION", "NODE", "TEMP", "ENTRY", "TEMP", "NODE", "TEMP", "SESSION"],
    "steady": ["TEMP", "SESSION", "TEMP", "ENTRY", "NODE", "TEMP", "ENTRY", "TEMP", "NODE", "TEMP"],
    "burst":  ["SESSION", "TEMP", "SESSION", "ENTRY", "SESSION", "NODE", "SESSION", "TEMP", "ENTRY", "NODE"],
    "drain":  ["TEMP", "TEMP", "ENTRY", "TEMP", "NODE", "TEMP", "TEMP", "TEMP", "ENTRY", "TEMP"],
}
PHASES = [(0, "warm"), (4000, "steady"), (16000, "burst"), (22000, "drain")]


def osize(kind, i):
    p, _ = KINDS[kind]
    if kind in VAR:
        m, step = VAR[kind]
        p += step * (i % m)
    a = P["ALIGN"]
    return (P["HEADER"] + p + a - 1) // a * a


class Obj:
    __slots__ = ("id", "kind", "size", "refs", "region", "addr", "age", "fwd")

    def __init__(s, i, kind, size, nrefs):
        s.id = i; s.kind = kind; s.size = size; s.refs = [None] * nrefs
        s.region = None; s.addr = 0; s.age = 0; s.fwd = None


class Heap:
    def __init__(s, eden, surv, tenure, policy, mut):
        s.E = eden; s.S = surv; s.T = tenure; s.pol = policy; s.mut = mut
        s.eden_top = 0; s.from_top = 0
        s.old = {}; s.free = [(0, P["OLD_SIZE"])]; s.rover = 0
        s.roots = {}; s.remset = {}; s.nid = 0
        s.minor = s.major = s.copied = s.promoted = 0
        s.ptot = s.pmax = s.peak_old = 0; s.oom = False
        s.trace = []

    def old_place(s, size):
        fl = s.free; idx = None
        if s.pol == "FIRST":
            for j, (a, z) in enumerate(fl):
                if z >= size:
                    idx = j; break
        elif s.pol == "BEST":
            best = None
            for j, (a, z) in enumerate(fl):
                if z >= size:
                    key = (z, -a) if s.mut.get("best_tie_high") else (z, a)
                    if best is None or key < best:
                        best = key; idx = j
        else:  # NEXT: first block whose start >= rover, wrapping
            n = len(fl)
            start = next((j for j, (a, z) in enumerate(fl) if a >= s.rover), 0)
            for k in range(n):
                j = (start + k) % n
                if fl[j][1] >= size:
                    idx = j; break
        if idx is None:
            return None
        a, z = fl[idx]
        if z - size >= P["MIN_SPLIT"]:
            fl[idx] = (a + size, z - size); taken = size
        else:
            fl.pop(idx); taken = z
        s.rover = a + taken
        return a, taken

    def old_used(s):
        return P["OLD_SIZE"] - sum(z for _, z in s.free)

    def store(s, obj, slot, tgt):
        obj.refs[slot] = tgt
        if obj.region == "old" and tgt is not None and tgt.region != "old":
            s.remset[obj.id] = obj

    def alloc(s, kind, i):
        size = osize(kind, i)
        pt = s.mut.get("PT", 0)
        if pt and size >= pt:
            pl = s.old_place(size)
            if pl is None:
                s.major_gc(); pl = s.old_place(size)
                if pl is None:
                    s.oom = True; return None
            o = Obj(s.nid, kind, pl[1], KINDS[kind][1]); s.nid += 1
            o.region = "old"; o.addr = pl[0]; s.old[pl[0]] = o
            s.peak_old = max(s.peak_old, s.old_used())
            return o
        if s.eden_top + size > s.E:
            s.minor_gc()
            if s.oom:
                return None
        o = Obj(s.nid, kind, size, KINDS[kind][1]); s.nid += 1
        o.region = "eden"; o.addr = s.eden_top; s.eden_top += size
        return o

    def minor_gc(s):
        young = s.eden_top + s.from_top
        freeb = sum(z for _, z in s.free)
        if s.mut.get("guard_largest"):
            freeb = max([z for _, z in s.free] + [0])
        largest = max([z for _, z in s.free] + [0])
        if freeb < young or largest < P.get("LARGEST_GUARD", 0):
            s.major_gc()
        s.minor += 1
        to_top = 0; q = []; copied = promoted = 0

        def evac(o):
            nonlocal to_top, copied, promoted
            if o is None or o.region == "old":
                return o
            if o.fwd is not None:
                return o.fwd
            na = o.age + 1
            ten = (na > s.T) if s.mut.get("tenure_gt") else (na >= s.T)
            n = Obj(o.id, o.kind, o.size, 0); n.refs = list(o.refs); n.age = na
            if not ten and to_top + o.size <= s.S:
                n.region = "surv"; n.addr = to_top; to_top += o.size; copied += o.size
            elif ten or not s.mut.get("overflow_oom"):
                pl = s.old_place(o.size)
                if pl is None:
                    s.oom = True; return o
                n.region = "old"; n.addr = pl[0]; n.size = pl[1]; s.old[pl[0]] = n
                promoted += o.size
            o.fwd = n
            if s.mut.get("dfs"):
                scan(n)
            else:
                q.append(n)
            return n

        def scan(n):
            for k, r in enumerate(n.refs):
                if r is not None and r.region != "old":
                    n.refs[k] = evac(r)

        for k in sorted(s.roots):
            s.roots[k] = evac(s.roots[k])
            if s.oom: return
        rs = list(s.remset.values())
        if not s.mut.get("remset_insertion"):
            rs.sort(key=lambda o: o.addr)
        for o in rs:
            scan(o)
            if s.oom: return
        qi = 0
        while qi < len(q):
            scan(q[qi]); qi += 1
            if s.oom: return
        s.remset = {o.id: o for o in sorted(s.old.values(), key=lambda x: x.addr)
                    if any(r is not None and r.region != "old" for r in o.refs)}
        s.eden_top = 0; s.from_top = to_top
        s.copied += copied; s.promoted += promoted
        pause = 40 + copied // 64 + promoted // 32 + 2 * len(rs)
        s.ptot += pause; s.pmax = max(s.pmax, pause)
        s.peak_old = max(s.peak_old, s.old_used())
        s.trace.append(("m", copied, promoted, pause))

    def major_gc(s):
        s.major += 1
        stack = [r for _, r in sorted(s.roots.items()) if r is not None]
        seen = set(); mb = 0
        while stack:
            o = stack.pop()
            if id(o) in seen: continue
            seen.add(id(o))
            if o.region == "old": mb += o.size
            for r in o.refs:
                if r is not None and id(r) not in seen:
                    stack.append(r)
        dead = [a for a, o in s.old.items() if id(o) not in seen]
        for a in dead:
            o = s.old.pop(a); s.remset.pop(o.id, None); s.free.append((a, o.size))
        s.free.sort()
        if not s.mut.get("no_coalesce"):
            m = []
            for a, z in s.free:
                if m and m[-1][0] + m[-1][1] == a:
                    m[-1] = (m[-1][0], m[-1][1] + z)
                else:
                    m.append((a, z))
            s.free = m
        if not s.mut.get("rover_keep"):
            s.rover = 0
        pause = 150 + mb // 32 + len(dead) // 2
        s.ptot += pause; s.pmax = max(s.pmax, pause)
        s.trace.append(("M", mb, len(dead), pause))


def run(e, sv, t, pol, mut=None):
    h = Heap(e, sv, t, pol, mut or {})
    R = h.roots
    for j in range(P["REG_COUNT"]):
        R[100 + j] = h.alloc("REG", j)
    sess = cache = 0
    for i in range(P["N_OPS"]):
        ph = [p for st, p in PHASES if i >= st][-1]
        kind = MIXES[ph][i % 10]
        o = h.alloc(kind, i)
        if o is None: break
        if kind == "TEMP":
            R[0] = o
        elif kind == "SESSION":
            slot = 1 + sess % P["RING"]; sess += 1
            R[slot] = o
            b = h.alloc("BLOB", i)
            if b is None: break
            h.store(R[slot], 0, b)
        elif kind == "ENTRY":
            reg = R[100 + cache % P["REG_COUNT"]]
            h.store(reg, (cache // P["REG_COUNT"]) % 4, o); cache += 1
        elif kind == "NODE":
            h.store(o, 0, R.get(120)); R[120] = o
        if i % P["LISTDROP"] == P["LISTDROP"] - 1:
            R[120] = None
        if h.oom: break
    return h


def row(h):
    return (h.oom, h.minor, h.major, h.copied, h.promoted, h.ptot, h.pmax, h.peak_old)


def sweep(mut=None, dims=None):
    out = {}
    if dims == "PT":
        for e, sv, t, pt in itertools.product(P["EDENS"], P["SURVS"], P["TENS"], P["PTS"]):
            m = dict(mut or {}); m["PT"] = pt
            out[(e, sv, t, pt)] = row(run(e, sv, t, P["FIXED_POLICY"], m))
        return out
    for c in itertools.product(P["EDENS"], P["SURVS"], P["TENS"], P["POLICIES"]):
        out[c] = row(run(*c, mut))
    return out


if __name__ == "__main__":
    t0 = time.time()
    base = sweep()
    print(f"time {time.time() - t0:.1f}s rows {len(base)} oom {sum(v[0] for v in base.values())}")
    for k, v in sorted(base.items()):
        print(k, v)
