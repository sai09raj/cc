#!/usr/bin/env python3
"""Independent invariant checker for GRID-14 simulator traces (Python 3, standard library only).

It shares no code with the simulator. From the trace it uses only: the CONFIG line (cycle, plan,
order, offsets), the LINK lines (id, length in cells, kind, upstream/downstream intersection,
terminal), and per step the NEW / EXIT / POS / WAIT records. Signal timing, approach sides,
exit sides, movements and the phase that serves each movement are re-derived here from the
packet (Sections 1-3, Figures 1, 3 and 4).

Invariants:
  I1 no cell ever holds two vehicles (checked on every POS record);
  I2 every stop-line crossing (a vehicle that was in the stop-line cell of a link ending at an
     intersection at the end of step t-1 and is in cell 0 of another link at the end of step t)
     happens at a step t at which the phase serving that movement is green at that intersection;
  I3 at every step: vehicles created so far == vehicles waiting + vehicles in the network +
     vehicles departed so far.
Exit status 0 if all three hold, 1 otherwise.
"""
import sys

# Figure 4 green times (A, B, C, D) by cycle and plan
GREEN = {
    60: [(18, 8, 18, 8), (22, 6, 18, 6), (16, 7, 22, 7), (20, 9, 16, 7), (16, 7, 20, 9), (21, 5, 21, 5)],
    72: [(22, 10, 22, 10), (27, 8, 22, 7), (20, 9, 27, 8), (25, 11, 20, 8), (20, 8, 25, 11), (26, 6, 26, 6)],
    84: [(26, 12, 26, 12), (32, 9, 26, 9), (23, 11, 32, 10), (29, 14, 23, 10), (23, 11, 29, 13), (31, 7, 31, 7)],
    96: [(30, 14, 30, 14), (37, 11, 30, 10), (27, 12, 37, 12), (34, 15, 27, 12), (27, 12, 34, 15), (36, 8, 36, 8)],
    108: [(34, 16, 34, 16), (42, 12, 34, 12), (30, 14, 42, 14), (38, 18, 30, 14), (30, 14, 38, 18), (40, 10, 40, 10)],
    120: [(39, 17, 39, 17), (48, 13, 38, 13), (34, 15, 48, 15), (43, 20, 34, 15), (34, 15, 43, 20), (45, 11, 45, 11)],
}
SEQ = {'lead': 'ABCD', 'lag': 'BADC'}


def green_phase(C, plan, order, offset, t):
    """Phase letter green at step t for an intersection with this offset, or None (all-red)."""
    g = dict(zip('ABCD', GREEN[C][plan - 1]))
    tau = (t - offset) % C
    start = 0
    for p in SEQ[order]:
        if start <= tau < start + g[p]:
            return p
        start += g[p] + 2
    return None


def node_xy(j):
    return (j % 3, j // 3)  # (x east, y south)


def terminal_side(k):
    return 'N' if k < 3 else 'E' if k < 6 else 'S' if k < 9 else 'W'


def side_of(frm, to):
    """Side of intersection `frm` on which neighbouring intersection `to` lies."""
    (x0, y0), (x1, y1) = node_xy(frm), node_xy(to)
    if x1 == x0 + 1 and y1 == y0: return 'E'
    if x1 == x0 - 1 and y1 == y0: return 'W'
    if y1 == y0 + 1 and x1 == x0: return 'S'
    if y1 == y0 - 1 and x1 == x0: return 'N'
    raise ValueError('not adjacent')


OPP = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}
# driver arriving from side s: left exit, right exit
LEFT_EXIT = {'N': 'E', 'E': 'S', 'S': 'W', 'W': 'N'}
RIGHT_EXIT = {'N': 'W', 'W': 'S', 'S': 'E', 'E': 'N'}


def movement(arr_side, exit_side):
    if exit_side == OPP[arr_side]: return 'T'
    if exit_side == LEFT_EXIT[arr_side]: return 'L'
    if exit_side == RIGHT_EXIT[arr_side]: return 'R'
    raise ValueError('U-turn')


def serving_phase(arr_side, mv):
    if arr_side in 'NS':
        return 'B' if mv == 'L' else 'A'
    return 'D' if mv == 'L' else 'C'


def check(path, max_report=5):
    cfg = None
    links = {}
    viol = {'I1': [], 'I2': [], 'I3': []}
    crossings = 0
    steps = 0
    created = departed = 0
    prev_pos = {}
    t = None
    cur_new = cur_exit = 0
    pos = None
    waiting = None

    def link_geom(lid):
        L = links[lid]
        return L

    def finish_step():
        nonlocal created, departed, prev_pos, crossings
        # I1: no two vehicles in one cell
        seen = {}
        for v, (l, c) in pos.items():
            key = (l, c)
            if key in seen:
                if len(viol['I1']) < 1000:
                    viol['I1'].append(f'step {t}: vehicles {seen[key]} and {v} both in link {l} cell {c}')
            else:
                seen[key] = v
        # I2: stop-line crossings
        for v, (l, c) in pos.items():
            if v in prev_pos:
                pl, pc = prev_pos[v]
                if pl != l:
                    A = links[pl]
                    if A['kind'] == 'out':
                        viol['I2'].append(f'step {t}: vehicle {v} moved off an outbound link into link {l}')
                        continue
                    if pc != A['n'] - 1 or c != 0:
                        viol['I2'].append(f'step {t}: vehicle {v} changed link from cell {pc} to cell {c}')
                        continue
                    crossings += 1
                    j = A['to']
                    B = links[l]
                    if B['from'] != j:
                        viol['I2'].append(f'step {t}: vehicle {v} jumped from link {pl} to link {l} not leaving I{j}')
                        continue
                    arr = A['arr']
                    ex = terminal_side(B['term']) if B['kind'] == 'out' else side_of(j, B['to'])
                    mv = movement(arr, ex)
                    need = serving_phase(arr, mv)
                    have = green_phase(cfg['C'], cfg['plan'], cfg['order'], cfg['offsets'][j], t)
                    if have != need:
                        viol['I2'].append(f'step {t}: vehicle {v} crossed at I{j} ({arr}-approach {mv}, needs phase {need}) while signal shows {have or "all-red"}')
        # I3: conservation
        created += cur_new
        departed += cur_exit
        if created != waiting + len(pos) + departed:
            viol['I3'].append(f'step {t}: created {created} != waiting {waiting} + network {len(pos)} + departed {departed}')
        prev_pos = pos

    with open(path) as f:
        for line in f:
            line = line.rstrip('\n')
            if not line or line.startswith('#'):
                continue
            tag, _, rest = line.partition(' ')
            if tag == 'CONFIG':
                kv = dict(x.split('=') for x in rest.split())
                cfg = {'C': int(kv['C']), 'plan': int(kv['plan']), 'order': kv['order'],
                       'offsets': [int(float(x)) for x in kv['offsets'].split(',')]}
            elif tag == 'LINK':
                p = rest.split()
                kv = dict(x.split('=') for x in p[3:])
                links[int(p[0])] = {'n': int(p[1]), 'kind': p[2], 'from': int(kv['from']), 'to': int(kv['to']),
                                    'arr': kv['arrside'], 'term': int(kv['term'])}
            elif tag == 'STEP':
                if t is not None:
                    finish_step()
                t = int(rest)
                steps += 1
                cur_new = cur_exit = 0
                pos = {}
                waiting = 0
            elif tag == 'NEW':
                cur_new += 1
            elif tag == 'EXIT':
                cur_exit += 1
            elif tag == 'POS':
                for item in rest.split():
                    v, l, c = item.split(':')
                    v, l, c = int(v), int(l), int(c)
                    if not (0 <= c < links[l]['n']):
                        viol['I1'].append(f'step {t}: vehicle {v} in nonexistent cell {c} of link {l}')
                    if v in pos:
                        viol['I1'].append(f'step {t}: vehicle {v} listed twice')
                    pos[v] = (l, c)
            elif tag == 'WAIT':
                waiting = len(rest.split())
            elif tag == 'END':
                pass
    if t is not None:
        finish_step()
    ok = True
    names = {'I1': 'no cell ever holds two vehicles',
             'I2': 'every stop-line crossing happens during a green for its movement',
             'I3': 'created == waiting + in network + departed at every step'}
    print(f'trace: {path}')
    print(f'config: {cfg}; steps read: {steps}; stop-line crossings checked: {crossings}; vehicles created: {created}; departed: {departed}')
    for k in ('I1', 'I2', 'I3'):
        n = len(viol[k])
        status = 'PASS' if n == 0 else f'FAIL ({n} violation(s))'
        print(f'{k} [{names[k]}]: {status}')
        for m in viol[k][:max_report]:
            print('    ' + m)
        ok = ok and n == 0
    print('OVERALL:', 'PASS' if ok else 'REJECTED')
    return ok


if __name__ == '__main__':
    sys.exit(0 if check(sys.argv[1]) else 1)
