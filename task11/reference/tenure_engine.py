"""TENURE-11 reference engine: generational GC under a fixed mutator.

Implements design/semantic-contract.md (section ids in comments).
Objects move in place: an evacuated object's region/address change and every
Python reference to it sees the new location, which is equivalent to updating
every scanned slot. MUTANT flags exist only for the score-topology audit.
"""
import hashlib
import itertools
import sys

# S01
ALIGN = 8
HEADER = 16
OLD_SIZE = 131072
MIN_SPLIT = 32
N_OPS = 26000
RING = 64
REG_COUNT = 16
LIST_DROP = 1500

# S02: kind -> (base payload, step, modulus, ref slots)
KINDS = {
    "TEMP": (24, 0, 1, 0),
    "SESSION": (96, 0, 1, 1),
    "BLOB": (96, 96, 13, 0),
    "ENTRY": (56, 24, 3, 1),
    "NODE": (40, 8, 5, 1),
    "REG": (112, 0, 1, 4),
}

# S04
PHASES = [(0, "warm"), (4000, "steady"), (16000, "burst"), (22000, "drain")]
MIXES = {
    "warm": "TEMP TEMP SESSION NODE TEMP ENTRY TEMP NODE TEMP SESSION".split(),
    "steady": "TEMP SESSION TEMP ENTRY NODE TEMP ENTRY TEMP NODE TEMP".split(),
    "burst": "SESSION TEMP SESSION ENTRY SESSION NODE SESSION TEMP ENTRY NODE".split(),
    "drain": "TEMP TEMP ENTRY TEMP NODE TEMP TEMP TEMP ENTRY TEMP".split(),
}

ROOT_SCRATCH, ROOT_RING0, ROOT_REG0, ROOT_LIST = 0, 1, 100, 120

# S12
EDENS = [16384, 24576, 32768, 49152]
SURVS = [8192, 24576]
TENURES = [1, 2, 3, 5]
PRETENURES = [0, 768, 1024]  # 0 = off
CONFIGS = list(itertools.product(EDENS, SURVS, TENURES, PRETENURES))

MUTANT = {}


class OOM(Exception):
    pass


def obj_size(kind, i):
    base, step, mod, _ = KINDS[kind]
    payload = base + step * (i % mod)
    return (HEADER + payload + ALIGN - 1) // ALIGN * ALIGN


class Obj:
    __slots__ = ("kind", "size", "slots", "region", "addr", "age", "occ", "gc_epoch")

    def __init__(self, kind, size):
        self.kind = kind
        self.size = size
        self.slots = [None] * KINDS[kind][3]
        self.region = None   # 'eden' | 'surv' | 'old'
        self.addr = 0
        self.age = 0
        self.occ = 0         # occupied block length when old
        self.gc_epoch = -1   # minor-GC number in which it was evacuated


class Heap:
    def __init__(self, eden, surv, tenure, pretenure):
        self.EDEN, self.SURV, self.T, self.PT = eden, surv, tenure, pretenure
        self.eden_used = 0
        self.from_used = 0
        self.eden_objs = []
        self.from_objs = []
        self.free = [(0, OLD_SIZE)]          # S08 free list, address ordered
        self.old = {}                        # addr -> Obj
        self.roots = {}                      # slot -> Obj or None
        self.remset = set()                  # ids of old objects (S10)
        self.remobj = {}
        self.op = -1
        self.minor = self.major = 0
        self.copied = self.promoted = self.pretenured = 0
        self.pause_total = self.pause_max = 0
        self.old_peak = 0
        self.log = []

    # ---- S08 ----
    def place_old(self, obj):
        for idx, (a, length) in enumerate(self.free):
            if length >= obj.size:
                if length - obj.size >= MIN_SPLIT:
                    self.free[idx] = (a + obj.size, length - obj.size)
                    occ = obj.size
                else:
                    self.free.pop(idx)
                    occ = length
                obj.region, obj.addr, obj.occ = "old", a, occ
                self.old[a] = obj
                return True
        return False

    def old_occupancy(self):
        return sum(o.occ for o in self.old.values())

    def free_total(self):
        return sum(length for _, length in self.free)

    def sample_peak(self):
        self.old_peak = max(self.old_peak, self.old_occupancy())

    def add_pause(self, p):
        self.pause_total += p
        self.pause_max = max(self.pause_max, p)

    # ---- S10 write barrier ----
    def store(self, obj, slot, target):
        obj.slots[slot] = target
        if target is not None and obj.region == "old" and target.region != "old":
            self.remset.add(id(obj))
            self.remobj[id(obj)] = obj

    # ---- S06 ----
    def alloc(self, kind, i):
        size = obj_size(kind, i)
        o = Obj(kind, size)
        if self.PT and size >= self.PT:
            if not self.place_old(o):
                self.major_gc()
                if not self.place_old(o):
                    raise OOM()
            self.pretenured += size
            self.sample_peak()
            return o
        if self.eden_used + size > self.EDEN:
            self.minor_gc()
        o.region, o.addr, o.age = "eden", self.eden_used, 0
        self.eden_used += size
        self.eden_objs.append(o)
        return o

    # ---- S07 ----
    def minor_gc(self):
        guard_free = self.free_total()
        if MUTANT.get("guard_largest"):
            guard_free = max([l for _, l in self.free] + [0])
        if guard_free < self.eden_used + self.from_used:
            self.major_gc()
        self.minor += 1
        epoch = self.minor
        R = len(self.remset)
        to_used = 0
        to_objs = []
        queue = []
        copied = promoted = 0

        def evac(o):
            nonlocal to_used, copied, promoted
            if o is None or o.region == "old" or o.gc_epoch == epoch:
                return
            o.gc_epoch = epoch
            a = o.age + 1
            tenure = (a > self.T) if MUTANT.get("tenure_gt") else (a >= self.T)
            if not tenure and to_used + o.size <= self.SURV:
                o.region, o.addr, o.age = "surv", to_used, a
                to_used += o.size
                copied += o.size
                to_objs.append(o)
            else:
                if not self.place_old(o):
                    raise OOM()
                promoted += o.size
            if MUTANT.get("dfs"):
                scan(o)
            else:
                queue.append(o)

        def scan(o):
            for s in o.slots:
                evac(s)

        for slot in sorted(self.roots):
            evac(self.roots[slot])
        rs = [self.remobj[k] for k in self.remset]
        if MUTANT.get("remset_insertion"):
            rs = list(self.remobj[k] for k in self.remset)  # set order
        else:
            rs.sort(key=lambda o: o.addr)
        for o in rs:
            scan(o)
        qi = 0
        while qi < len(queue):
            scan(queue[qi])
            qi += 1

        self.eden_used, self.eden_objs = 0, []
        self.from_used, self.from_objs = to_used, to_objs
        # rebuild remembered set
        self.remset, self.remobj = set(), {}
        for o in self.old.values():
            if any(s is not None and s.region == "surv" for s in o.slots):
                self.remset.add(id(o))
                self.remobj[id(o)] = o
        self.copied += copied
        self.promoted += promoted
        pause = 40 + copied // 64 + promoted // 32 + 2 * R
        self.add_pause(pause)
        self.sample_peak()
        self.log.append(("m", self.op, copied, promoted, R, 0, 0, self.old_occupancy(), pause))

    # ---- S09 ----
    def major_gc(self):
        self.major += 1
        marked = set()
        stack = [self.roots[s] for s in sorted(self.roots) if self.roots[s] is not None]
        while stack:
            o = stack.pop()
            if id(o) in marked:
                continue
            marked.add(id(o))
            for s in o.slots:
                if s is not None and id(s) not in marked:
                    stack.append(s)
        marked_bytes = 0
        freed = 0
        for a in sorted(self.old):
            o = self.old[a]
            if id(o) in marked:
                marked_bytes += o.occ
            else:
                del self.old[a]
                self.free.append((a, o.occ))
                self.remset.discard(id(o))
                self.remobj.pop(id(o), None)
                o.region = None
                freed += 1
        self.free.sort()
        if not MUTANT.get("no_coalesce"):
            merged = []
            for a, length in self.free:
                if merged and merged[-1][0] + merged[-1][1] == a:
                    merged[-1] = (merged[-1][0], merged[-1][1] + length)
                else:
                    merged.append((a, length))
            self.free = merged
        pause = 150 + marked_bytes // 32 + freed // 2
        self.add_pause(pause)
        self.log.append(("M", self.op, 0, 0, 0, marked_bytes, freed, self.old_occupancy(), pause))


def run(eden, surv, tenure, pretenure):
    h = Heap(eden, surv, tenure, pretenure)
    R = h.roots
    oom_op = None
    try:
        h.op = -1
        for j in range(REG_COUNT):
            o = h.alloc("REG", j)
            R[ROOT_REG0 + j] = o
        sessions = entries = 0
        for i in range(N_OPS):
            h.op = i
            phase = [p for start, p in PHASES if i >= start][-1]
            kind = MIXES[phase][i % 10]
            o = h.alloc(kind, i)
            if kind == "TEMP":
                R[ROOT_SCRATCH] = o
            elif kind == "SESSION":
                slot = ROOT_RING0 + sessions % RING
                sessions += 1
                R[slot] = o
                b = h.alloc("BLOB", i)
                h.store(R[slot], 0, b)
            elif kind == "ENTRY":
                if sessions:
                    h.store(o, 0, R[ROOT_RING0 + (sessions - 1) % RING])
                reg = R[ROOT_REG0 + entries % REG_COUNT]
                h.store(reg, (entries // REG_COUNT) % 4, o)
                entries += 1
            elif kind == "NODE":
                h.store(o, 0, R.get(ROOT_LIST))
                R[ROOT_LIST] = o
            if i % LIST_DROP == LIST_DROP - 1:
                R[ROOT_LIST] = None
    except OOM:
        oom_op = h.op
    return h, oom_op


def metrics(h, oom_op):
    return {
        "oom": oom_op is not None, "oom_op": oom_op,
        "minor": h.minor, "major": h.major,
        "copied": h.copied, "promoted": h.promoted, "pretenured": h.pretenured,
        "pause_total": h.pause_total, "pause_max": h.pause_max, "old_peak": h.old_peak,
    }


def gclog_text(h):
    lines = ["TENURE11-GCLOG-V1"]
    for n, (t, op, cp, pr, rs, mk, fr, occ, pz) in enumerate(h.log, 1):
        lines.append(f"{n};{t};{op};{cp};{pr};{rs};{mk};{fr};{occ};{pz}")
    return "\n".join(lines) + "\n"


def cfg_key(c):
    return c  # (EDEN, SURV, T, PT) ascending, PT 0 < 768 < 1024


def sweep():
    return {c: metrics(*run(*c)) for c in CONFIGS}


if __name__ == "__main__":
    import time
    t0 = time.time()
    rows = sweep()
    print(f"sweep {len(rows)} configs in {time.time() - t0:.1f}s; OOM {sum(r['oom'] for r in rows.values())}")
    for c, r in rows.items():
        print(c, r)
