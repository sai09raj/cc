#!/usr/bin/env python3
"""TENURE-11 generational collector simulator.

Dependency free (Python 3 standard library only). Implements the collector
rules of tenure11_v1.pdf sections 2-13 and Figures 1-6.

Usage:
  python3 gcsim.py sweep      OUTDIR      # 96-config sweep, selections, baseline log
  python3 gcsim.py log        [--strict-promote] [--dfs] OUTFILE
                                          # baseline (or adversarial) event log
  python3 gcsim.py run EDEN SURV T PT     # one configuration, prints metrics
"""
import sys, os, json, hashlib
from collections import deque

# ---------------------------------------------------------------------------
# Constants measured from the figures (see measure_figures.py / MEMO.md)
# ---------------------------------------------------------------------------
HEADER = 16            # Figure 2: header box spans byte offsets 0..16
ALIGN = 8              # section 2
OLD_SIZE = 128 * 1024  # Figure 1: old-generation bar spans 0..128 KiB

# Figure 3: base payload (bytes) and number of reference slots
KINDS = {
    'TEMP':    (24, 0),
    'SESSION': (96, 1),
    'BLOB':    (96, 0),
    'ENTRY':   (56, 1),
    'NODE':    (40, 1),
    'REG':     (112, 4),
}

# Figure 4: phases [left, right) and mixes indexed by (i mod 10)
PHASES = [
    (0, 4000, ['TEMP', 'TEMP', 'SESSION', 'NODE', 'TEMP', 'ENTRY', 'TEMP', 'NODE', 'TEMP', 'SESSION']),
    (4000, 16000, ['TEMP', 'SESSION', 'TEMP', 'ENTRY', 'NODE', 'TEMP', 'ENTRY', 'TEMP', 'NODE', 'TEMP']),
    (16000, 22000, ['SESSION', 'TEMP', 'SESSION', 'ENTRY', 'SESSION', 'NODE', 'SESSION', 'TEMP', 'ENTRY', 'NODE']),
    (22000, 26000, ['TEMP', 'TEMP', 'ENTRY', 'TEMP', 'NODE', 'TEMP', 'TEMP', 'TEMP', 'ENTRY', 'TEMP']),
]
END_MARK = 26000

EDENS = [16384, 24576, 32768, 49152]
SURVS = [8192, 24576]
TS = [1, 2, 3, 5]
PTS = [None, 768, 1024]   # None = off
BASELINE = (24576, 8192, 2, None)

LOG_HEADER = 'TENURE11-GCLOG-V1'


def obj_size(kind, i):
    base, _ = KINDS[kind]
    if kind == 'BLOB':
        base += 96 * (i % 13)
    elif kind == 'ENTRY':
        base += 24 * (i % 3)
    elif kind == 'NODE':
        base += 8 * (i % 5)
    total = HEADER + base
    return (total + ALIGN - 1) // ALIGN * ALIGN


def kind_for(i):
    for lo, hi, mix in PHASES:
        if lo <= i < hi:
            return mix[i % 10]
    raise ValueError(i)


class OOM(Exception):
    def __init__(self, op):
        self.op = op


class Obj:
    __slots__ = ('kind', 'size', 'slots', 'space', 'addr', 'age', 'occ',
                 'moved', 'mark', 'sid')

    def __init__(self, kind, size, nslots, sid):
        self.kind = kind
        self.size = size
        self.slots = [None] * nslots
        self.space = 'E'     # 'E' eden, 'S' survivor, 'O' old
        self.addr = 0
        self.age = 0
        self.occ = 0
        self.moved = -1      # minor-collection epoch in which it was moved
        self.mark = -1       # major-collection epoch in which it was marked
        self.sid = sid       # survivor-space epoch: valid survivor iff == heap.surv_epoch


class Heap:
    def __init__(self, eden, surv, T, PT, strict_promote=False, dfs=False):
        self.EDEN, self.SURV, self.T, self.PT = eden, surv, T, PT
        self.strict = strict_promote
        self.dfs = dfs
        self.roots = {}                    # slot -> Obj (non-null only)
        self.eden_used = 0
        self.from_used = 0
        self.surv_epoch = 0                # objects in from-space have sid == surv_epoch
        self.free = [[0, OLD_SIZE]]        # free list (address, length)
        self.old = set()                   # live-or-not-yet-freed old objects
        self.old_occ = 0
        self.remset = set()
        self.minor_epoch = 0
        self.major_epoch = 0
        self.op = -1
        # metrics
        self.n_minor = 0
        self.n_major = 0
        self.copied = 0
        self.promoted = 0
        self.pretenured = 0
        self.total_pause = 0
        self.max_pause = 0
        self.peak_occ = 0
        self.log = []

    # -- helpers -----------------------------------------------------------
    def is_young(self, o):
        if o.space == 'E':
            return True
        return o.space == 'S' and o.sid == self.surv_epoch

    def free_bytes(self):
        return sum(b[1] for b in self.free)

    def old_place(self, o):
        """Section 8. Returns True on success."""
        s = o.size
        best = None
        for idx, b in enumerate(self.free):
            if b[1] >= s and (best is None or b[0] < self.free[best][0]):
                best = idx
        if best is None:
            return False
        a, ln = self.free[best]
        if ln - s >= 32:
            occ = s
            self.free[best] = [a + s, ln - s]
        else:
            occ = ln
            del self.free[best]
        o.space = 'O'
        o.addr = a
        o.occ = occ
        self.old.add(o)
        self.old_occ += occ
        return True

    def _pause(self, p):
        self.total_pause += p
        if p > self.max_pause:
            self.max_pause = p

    # -- section 9 -----------------------------------------------------------
    def major(self):
        self.major_epoch += 1
        ep = self.major_epoch
        stack = []
        for k in sorted(self.roots):
            o = self.roots[k]
            if o.mark != ep:
                o.mark = ep
                stack.append(o)
        while stack:
            o = stack.pop()
            for r in o.slots:
                if r is not None and r.mark != ep:
                    r.mark = ep
                    stack.append(r)
        marked_occ = 0
        freed = []
        for o in self.old:
            if o.mark == ep:
                marked_occ += o.occ
            else:
                freed.append(o)
        for o in freed:
            self.old.discard(o)
            self.remset.discard(o)
            self.old_occ -= o.occ
            self.free.append([o.addr, o.occ])
            o.space = 'X'   # freed
        self.free.sort()
        merged = []
        for a, ln in self.free:
            if merged and merged[-1][0] + merged[-1][1] == a:
                merged[-1][1] += ln
            else:
                merged.append([a, ln])
        self.free = merged
        pause = 150 + marked_occ // 32 + len(freed) // 2
        self.n_major += 1
        self._pause(pause)
        self.log.append(('M', self.op, 0, 0, 0, marked_occ, len(freed), self.old_occ, pause))

    # -- section 7 -----------------------------------------------------------
    def minor(self):
        if self.free_bytes() < self.eden_used + self.from_used:
            self.major()
        R = len(self.remset)
        self.minor_epoch += 1
        ep = self.minor_epoch
        new_sid = self.surv_epoch + 1
        st = {'to': 0, 'copied': 0, 'promoted': 0}
        promoted_objs = []
        T, SURV, strict = self.T, self.SURV, self.strict

        def move(o):
            new_age = o.age + 1
            tenure = (new_age > T) if strict else (new_age >= T)
            o.moved = ep
            if not tenure and st['to'] + o.size <= SURV:
                o.addr = st['to']
                st['to'] += o.size
                o.age = new_age
                o.space = 'S'
                o.sid = new_sid
                st['copied'] += o.size
            else:
                if not self.old_place(o):
                    raise OOM(self.op)
                st['promoted'] += o.size
                promoted_objs.append(o)

        def needs_move(r):
            return r is not None and r.moved != ep and self.is_young(r)

        if not self.dfs:
            queue = deque()

            def visit(r):
                if needs_move(r):
                    move(r)
                    queue.append(r)

            for k in sorted(self.roots):
                visit(self.roots[k])
            for o in sorted(self.remset, key=lambda x: x.addr):
                for r in o.slots:
                    visit(r)
            while queue:
                o = queue.popleft()
                for r in o.slots:
                    visit(r)
        else:
            # ADVERSARIAL ONLY: depth-first (pre-order, recursive) evacuation
            def visit(r):
                if not needs_move(r):
                    return
                move(r)
                stack = [(r, 0)]
                while stack:
                    o, j = stack[-1]
                    if j >= len(o.slots):
                        stack.pop()
                        continue
                    stack[-1] = (o, j + 1)
                    c = o.slots[j]
                    if needs_move(c):
                        move(c)
                        stack.append((c, 0))

            for k in sorted(self.roots):
                visit(self.roots[k])
            for o in sorted(self.remset, key=lambda x: x.addr):
                for r in o.slots:
                    visit(r)

        # flip: eden and from-space emptied, to-space becomes from-space
        self.eden_used = 0
        self.from_used = st['to']
        self.surv_epoch = new_sid
        # rebuild remembered set over every old object
        newrs = set()
        for o in self.old:
            for r in o.slots:
                if r is not None and r.space == 'S' and r.sid == new_sid:
                    newrs.add(o)
                    break
        self.remset = newrs
        copied, promoted = st['copied'], st['promoted']
        pause = 40 + copied // 64 + promoted // 32 + 2 * R
        self.n_minor += 1
        self.copied += copied
        self.promoted += promoted
        self._pause(pause)
        self.peak_occ = max(self.peak_occ, self.old_occ)
        self.log.append(('m', self.op, copied, promoted, R, 0, 0, self.old_occ, pause))

    # -- section 6 -----------------------------------------------------------
    def alloc(self, kind, i):
        size = obj_size(kind, i)
        o = Obj(kind, size, KINDS[kind][1], 0)
        if self.PT is not None and size >= self.PT:
            if not self.old_place(o):
                self.major()
                if not self.old_place(o):
                    raise OOM(self.op)
            self.pretenured += size
            self.peak_occ = max(self.peak_occ, self.old_occ)
            return o
        if self.eden_used + size > self.EDEN:
            self.minor()
        o.addr = self.eden_used
        self.eden_used += size
        o.space = 'E'
        o.age = 0
        return o

    # -- section 10 ----------------------------------------------------------
    def store(self, holder, slot, ref):
        holder.slots[slot] = ref
        if ref is not None and holder.space == 'O' and self.is_young(ref):
            self.remset.add(holder)

    def set_root(self, k, o):
        if o is None:
            self.roots.pop(k, None)
        else:
            self.roots[k] = o


def run_workload(h):
    # registry setup (operation -1)
    h.op = -1
    for j in range(16):
        r = h.alloc('REG', -1)
        h.set_root(100 + j, r)
    sessions = 0
    entries = 0
    for i in range(END_MARK):
        h.op = i
        kind = kind_for(i)
        o = h.alloc(kind, i)
        if kind == 'TEMP':
            h.set_root(0, o)
        elif kind == 'SESSION':
            ring = 1 + (sessions % 64)
            sessions += 1
            h.set_root(ring, o)
            b = h.alloc('BLOB', i)
            s = h.roots[ring]
            h.store(s, 0, b)
        elif kind == 'ENTRY':
            if sessions > 0:
                h.store(o, 0, h.roots.get(1 + ((sessions - 1) % 64)))
            reg = h.roots[100 + (entries % 16)]
            h.store(reg, (entries // 16) % 4, o)
            entries += 1
        elif kind == 'NODE':
            h.store(o, 0, h.roots.get(120))
            h.set_root(120, o)
        if i % 1500 == 1499:
            h.set_root(120, None)


def simulate(eden, surv, T, PT, strict_promote=False, dfs=False):
    h = Heap(eden, surv, T, PT, strict_promote, dfs)
    oom = None
    try:
        run_workload(h)
    except OOM as e:
        oom = e.op
    return h, oom


def log_text(h):
    lines = [LOG_HEADER]
    for n, (ty, op, cp, pr, rs, mk, fr, oc, pa) in enumerate(h.log, 1):
        lines.append(f'{n};{ty};{op};{cp};{pr};{rs};{mk};{fr};{oc};{pa}')
    return '\n'.join(lines) + '\n'


def log_hash(text):
    return hashlib.sha256(text.encode('ascii')).hexdigest()[:16]


def pt_name(pt):
    return 'off' if pt is None else str(pt)


COLS = ['idx', 'eden', 'surv', 'T', 'pt', 'oom', 'oom_op', 'minor', 'major',
        'copied', 'promoted', 'pretenured', 'total_pause', 'max_pause', 'peak_old']


def row_for(idx, cfg):
    eden, surv, T, PT = cfg
    h, oom = simulate(eden, surv, T, PT)
    if oom is not None:
        return dict(idx=idx, eden=eden, surv=surv, T=T, pt=pt_name(PT), oom='yes', oom_op=oom,
                    minor='', major='', copied='', promoted='', pretenured='',
                    total_pause='', max_pause='', peak_old='')
    return dict(idx=idx, eden=eden, surv=surv, T=T, pt=pt_name(PT), oom='no', oom_op='',
                minor=h.n_minor, major=h.n_major, copied=h.copied, promoted=h.promoted,
                pretenured=h.pretenured, total_pause=h.total_pause, max_pause=h.max_pause,
                peak_old=h.peak_occ)


def configs():
    out = []
    for e in EDENS:
        for s in SURVS:
            for t in TS:
                for p in PTS:
                    out.append((e, s, t, p))
    return out


def select(rows):
    feas = [r for r in rows if r['oom'] == 'no']
    cost = min(feas, key=lambda r: (r['total_pause'], r['max_pause'], r['idx']))
    lat_c = [r for r in feas if r['total_pause'] <= 220000]
    lat = min(lat_c, key=lambda r: (r['max_pause'], r['total_pause'], r['idx'])) if lat_c else None
    fp_c = [r for r in feas if r['max_pause'] <= 2400]
    fp = min(fp_c, key=lambda r: (r['eden'] + 2 * r['surv'], r['total_pause'], r['idx'])) if fp_c else None
    return {'cost_optimal': cost, 'latency_optimal_under_budget': lat,
            'footprint_optimal_under_ceiling': fp,
            'n_latency_candidates': len(lat_c), 'n_footprint_candidates': len(fp_c)}


def cmd_sweep(outdir):
    os.makedirs(outdir, exist_ok=True)
    rows = [row_for(i, c) for i, c in enumerate(configs())]
    with open(os.path.join(outdir, 'sweep.csv'), 'w') as f:
        f.write(','.join(COLS) + '\n')
        for r in rows:
            f.write(','.join(str(r[c]) for c in COLS) + '\n')
    sel = select(rows)
    feas = [r for r in rows if r['oom'] == 'no']
    summary = {
        'n_configs': len(rows),
        'n_feasible': len(feas),
        'oom_configs': [{k: r[k] for k in ('idx', 'eden', 'surv', 'T', 'pt', 'oom_op')}
                        for r in rows if r['oom'] == 'yes'],
        'sum_total_pause_feasible': sum(r['total_pause'] for r in feas),
        'sum_major_feasible': sum(r['major'] for r in feas),
        'sum_minor_feasible': sum(r['minor'] for r in feas),
        'sum_copied_feasible': sum(r['copied'] for r in feas),
        'sum_promoted_feasible': sum(r['promoted'] for r in feas),
        'sum_pretenured_feasible': sum(r['pretenured'] for r in feas),
    }
    with open(os.path.join(outdir, 'selections.json'), 'w') as f:
        json.dump({'selections': sel, 'summary': summary}, f, indent=2)
    with open(os.path.join(outdir, 'selections.txt'), 'w') as f:
        for k in ('cost_optimal', 'latency_optimal_under_budget', 'footprint_optimal_under_ceiling'):
            r = sel[k]
            if r is None:
                f.write(f'{k}: none\n')
            else:
                f.write(f"{k}: idx={r['idx']} EDEN={r['eden']} SURV={r['surv']} T={r['T']} PT={r['pt']} "
                        f"total_pause={r['total_pause']} max_pause={r['max_pause']} "
                        f"footprint={r['eden'] + 2 * r['surv']}\n")
        f.write(f"latency candidates (total<=220000): {sel['n_latency_candidates']}\n")
        f.write(f"footprint candidates (max<=2400): {sel['n_footprint_candidates']}\n")
        for k, v in summary.items():
            f.write(f'{k}: {v}\n')
    # baseline log
    cmd_log(os.path.join(outdir, 'baseline_log.txt'))
    print(open(os.path.join(outdir, 'selections.txt')).read())


def cmd_log(path, strict=False, dfs=False):
    h, oom = simulate(*BASELINE, strict_promote=strict, dfs=dfs)
    text = log_text(h)
    with open(path, 'w', newline='\n') as f:
        f.write(text)
    hx = log_hash(text)
    with open(path + '.hash', 'w') as f:
        f.write(hx + '\n')
    print(f'{path}: events={len(h.log)} oom={oom} hash={hx}')


def main(argv):
    if len(argv) >= 2 and argv[1] == 'sweep':
        cmd_sweep(argv[2] if len(argv) > 2 else '.')
    elif len(argv) >= 2 and argv[1] == 'log':
        args = argv[2:]
        strict = '--strict-promote' in args
        dfs = '--dfs' in args
        paths = [a for a in args if not a.startswith('--')]
        cmd_log(paths[0] if paths else 'baseline_log.txt', strict, dfs)
    elif len(argv) == 6 and argv[1] == 'run':
        e, s, t = int(argv[2]), int(argv[3]), int(argv[4])
        p = None if argv[5] == 'off' else int(argv[5])
        print(row_for(-1, (e, s, t, p)))
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == '__main__':
    main(sys.argv)
