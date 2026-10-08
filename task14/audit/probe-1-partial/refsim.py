#!/usr/bin/env python3
"""Independent, deliberately naive reference implementation of the GRID-14 model (Python 3 stdlib).

Coded separately from sim.js: it keeps a full cell array per link, takes an explicit copy of the
occupancy at the start of every step, generates vehicles and turning choices on the fly (no
precomputed routes), and evaluates signals from a list of (start, end, phase) intervals.
Used only to cross-check sim.js on chosen configurations.

usage: python3 refsim.py C plan lead|lag o0 o1 ... o8   (offsets in seconds)
       python3 refsim.py            (baseline and the three variants)
"""
import sys

MOD = 2 ** 31
def nxt(x):
    return (1103515245 * x + 12345) % MOD

IN_M = {0: 285, 1: 330, 2: 270, 3: 307.5, 4: 262.5, 5: 322.5, 6: 292.5, 7: 277.5, 8: 337.5,
        9: 315, 10: 300, 11: 270}
# street blocks (metres): unordered intersection pair -> length
BLOCK_M = {(0, 1): 240, (1, 2): 195, (3, 4): 165, (4, 5): 270, (6, 7): 210, (7, 8): 180,
           (0, 3): 225, (3, 6): 150, (1, 4): 180, (4, 7): 255, (2, 5): 202.5, (5, 8): 157.5}
DEM = {'AM':    [208, 266, 182, 234, 195, 254, 221, 176, 273, 247, 202, 228],
       'PM':    [221, 176, 273, 247, 202, 228, 208, 266, 182, 234, 195, 254],
       'EVENT': [208, 266, 182, 234, 312, 254, 221, 176, 273, 395, 202, 228]}
GREEN = {60: ['18/8/18/8', '22/6/18/6', '16/7/22/7', '20/9/16/7', '16/7/20/9', '21/5/21/5'],
         72: ['22/10/22/10', '27/8/22/7', '20/9/27/8', '25/11/20/8', '20/8/25/11', '26/6/26/6'],
         84: ['26/12/26/12', '32/9/26/9', '23/11/32/10', '29/14/23/10', '23/11/29/13', '31/7/31/7'],
         96: ['30/14/30/14', '37/11/30/10', '27/12/37/12', '34/15/27/12', '27/12/34/15', '36/8/36/8'],
         108: ['34/16/34/16', '42/12/34/12', '30/14/42/14', '38/18/30/14', '30/14/38/18', '40/10/40/10'],
         120: ['39/17/39/17', '48/13/38/13', '34/15/48/15', '43/20/34/15', '34/15/43/20', '45/11/45/11']}

# geometry: intersection j at (row, col); terminal positions
def rc(j):
    return divmod(j, 3)
# compass headings of travel: 'S' means travelling southwards (arrived from the north)
DELTA = {'N': (-1, 0), 'S': (1, 0), 'E': (0, 1), 'W': (0, -1)}
LEFT_OF = {'S': 'E', 'N': 'W', 'E': 'N', 'W': 'S'}    # left turn heading for a given heading
RIGHT_OF = {'S': 'W', 'N': 'E', 'E': 'S', 'W': 'N'}

def terminal_for_exit(j, heading):
    r, c = rc(j)
    if heading == 'N' and r == 0: return c
    if heading == 'E' and c == 2: return 3 + r
    if heading == 'S' and r == 2: return 6 + c
    if heading == 'W' and c == 0: return 9 + r
    return None

def terminal_entry(k):
    """intersection and heading of a vehicle entering at terminal k"""
    if k <= 2: return k, 'S'
    if k <= 5: return 3 * (k - 3) + 2, 'W'
    if k <= 8: return 6 + (k - 6), 'N'
    return 3 * (k - 9), 'E'

def ncells(m):
    n = m / 7.5
    assert abs(n - round(n)) < 1e-9
    return int(round(n))

class Link:
    def __init__(self, key, n, dest, heading):
        self.key, self.n, self.dest, self.heading = key, n, dest, heading
        self.cells = [None] * n

def build():
    links = {}
    for k in range(12):
        j, h = terminal_entry(k)
        links[('in', k)] = Link(('in', k), ncells(IN_M[k]), j, h)
        links[('out', k)] = Link(('out', k), 10, None, None)
    for (a, b), m in BLOCK_M.items():
        n = ncells(m)
        ra, ca = rc(a); rb, cb = rc(b)
        hab = 'E' if rb == ra else 'S'
        hba = 'W' if rb == ra else 'N'
        links[('blk', a, b)] = Link(('blk', a, b), n, b, hab)
        links[('blk', b, a)] = Link(('blk', b, a), n, a, hba)
    return links

def next_link_key(j, heading):
    k = terminal_for_exit(j, heading)
    if k is not None:
        return ('out', k)
    r, c = rc(j)
    dr, dc = DELTA[heading]
    return ('blk', j, 3 * (r + dr) + (c + dc))

def run(C, plan, order, offs, scen):
    g = [int(s) for s in GREEN[C][plan - 1].split('/')]
    seq = 'ABCD' if order == 'lead' else 'BADC'
    intervals = []
    t0 = 0
    for ph in seq:
        gl = g['ABCD'.index(ph)]
        intervals.append((t0, t0 + gl, ph))
        t0 += gl + 2
    assert t0 == C
    def phase_at(j, t):
        tau = (t - offs[j]) % C
        for s, e, ph in intervals:
            if s <= tau < e:
                return ph
        return None
    def allowed(ph, heading, mv):
        if ph is None: return False
        ns = heading in ('N', 'S')
        if ph == 'A': return ns and mv in ('T', 'R')
        if ph == 'B': return ns and mv == 'L'
        if ph == 'C': return (not ns) and mv in ('T', 'R')
        if ph == 'D': return (not ns) and mv == 'L'

    links = build()
    dem = DEM[scen]
    xs = [1000 + 17 * k for k in range(12)]
    queues = [[] for _ in range(12)]
    born = []
    vy = []        # vehicle generator state
    mov = []       # chosen movement at the current link's end
    nveh = 0
    gone = 0
    tts = 0
    def choose(v, heading):
        vy[v] = nxt(vy[v])
        r = (vy[v] // 65536) % 100
        L, T, R = (20, 65, 15) if heading in ('N', 'S') else (10, 75, 15)
        mov[v] = 'L' if r < L else ('T' if r < L + T else 'R')
    end = 7199
    for t in range(7200):
        if t < 3600:
            for k in range(12):
                xs[k] = nxt(xs[k])
                if (xs[k] // 256) % 3600 < dem[k]:
                    v = nveh; nveh += 1
                    born.append(t); vy.append((2654435761 * v + 12345) % MOD); mov.append(None)
                    queues[k].append(v)
        snap = {key: [c is not None for c in L.cells] for key, L in links.items()}
        moves = []   # (vehicle, from_key, from_idx, to_key or None)
        for key, L in links.items():
            n = L.n
            for i in range(n):
                v = L.cells[i]
                if v is None: continue
                if i < n - 1:
                    if not snap[key][i + 1]:
                        moves.append((v, key, i, key, i + 1))
                elif L.dest is None:
                    moves.append((v, key, i, None, None))
                else:
                    if allowed(phase_at(L.dest, t), L.heading, mov[v]):
                        h = {'T': L.heading, 'L': LEFT_OF[L.heading], 'R': RIGHT_OF[L.heading]}[mov[v]]
                        nk = next_link_key(L.dest, h)
                        if not snap[nk][0]:
                            moves.append((v, key, i, nk, 0))
        entries = []
        for k in range(12):
            if queues[k] and not snap[('in', k)][0]:
                entries.append((k, queues[k].pop(0)))
        for v, fk, fi, tk, ti in moves:
            assert links[fk].cells[fi] == v
            links[fk].cells[fi] = None
        for v, fk, fi, tk, ti in moves:
            if tk is None:
                gone += 1
                tts += t - born[v] + 1
            else:
                assert links[tk].cells[ti] is None
                links[tk].cells[ti] = v
                if ti == 0 and links[tk].dest is not None:
                    choose(v, links[tk].heading)
        for k, v in entries:
            L = links[('in', k)]
            assert L.cells[0] is None
            L.cells[0] = v
            choose(v, L.heading)
        if t + 1 >= 3600 and gone == nveh:
            end = t
            break
    grid = gone < nveh
    if grid:
        alive = set(range(nveh))
        # vehicles that left are not tracked individually here; recompute from what remains
        rem = [v for q in queues for v in q] + [v for L in links.values() for v in L.cells if v is not None]
        tts += sum(7200 - born[v] for v in rem)
    return tts, end, grid

if __name__ == '__main__':
    if len(sys.argv) > 1:
        C, plan, order = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
        offs = [int(a) for a in sys.argv[4:13]]
        cfgs = [('given', C, plan, order, offs)]
    else:
        cfgs = [('baseline', 84, 1, 'lead', [0] * 9),
                ('offsets 0/21/42', 84, 1, 'lead', [0, 21, 42] * 3),
                ('lag', 84, 1, 'lag', [0] * 9),
                ('C60', 60, 1, 'lead', [0] * 9)]
    for name, C, plan, order, offs in cfgs:
        res = {s: run(C, plan, order, offs, s) for s in ('AM', 'PM', 'EVENT')}
        tot = sum(r[0] for r in res.values())
        print(f"{name}: " + ' '.join(f"{s}={r[0]}(end {r[1]}{', GRIDLOCK' if r[2] else ''})" for s, r in res.items()) + f" total={tot}")
