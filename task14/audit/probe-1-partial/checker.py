#!/usr/bin/env python3
"""GRID-14 trace checker (Python 3 standard library only), coded separately from sim.js.

It does not import or reuse any simulator code. From the trace it uses only: the header's
configuration (C, plan, order, offsets), the LINK table (names and lengths), and the per-step
records. Signal state is recomputed here from Figures 3/4 of the packet, and movements are
derived from link geometry (which side the vehicle arrives from and which side it leaves by),
not taken from the simulator's own movement field.

Invariants
  I1 no cell ever holds two vehicles            (every P snapshot: (link, cell) pairs unique)
  I2 every stop-line crossing happens during a green for that vehicle's movement
     crossings are detected from consecutive P snapshots (vehicle in the last cell of a link ending
     at an intersection at step t-1, in cell 0 of another link at step t); the simulator's own
     X records are additionally checked and cross-matched
  I3 at every step: created = waiting + in network + departed
     created: G records so far; in network: vehicles in the P snapshot; departed: O records so far;
     waiting: replayed terminal queues (a created vehicle waits until it first appears in the network)

usage: python3 checker.py trace.txt
exit status 0 if all three invariants hold, 1 otherwise.
"""
import re
import sys

GREENS = {60: ['18/8/18/8', '22/6/18/6', '16/7/22/7', '20/9/16/7', '16/7/20/9', '21/5/21/5'],
          72: ['22/10/22/10', '27/8/22/7', '20/9/27/8', '25/11/20/8', '20/8/25/11', '26/6/26/6'],
          84: ['26/12/26/12', '32/9/26/9', '23/11/32/10', '29/14/23/10', '23/11/29/13', '31/7/31/7'],
          96: ['30/14/30/14', '37/11/30/10', '27/12/37/12', '34/15/27/12', '27/12/34/15', '36/8/36/8'],
          108: ['34/16/34/16', '42/12/34/12', '30/14/42/14', '38/18/30/14', '30/14/38/18', '40/10/40/10'],
          120: ['39/17/39/17', '48/13/38/13', '34/15/48/15', '43/20/34/15', '34/15/43/20', '45/11/45/11']}
SEQ = {'lead': 'ABCD', 'lag': 'BADC'}
ALL_RED = 2


def node_pos(name):
    """grid coordinates (row, col) of an intersection 'Ij' or a terminal 'Tk' (terminals lie outside)."""
    if name[0] == 'I':
        j = int(name[1:])
        return (j // 3, j % 3)
    k = int(name[1:])
    if k <= 2: return (-1, k)
    if k <= 5: return (k - 3, 3)
    if k <= 8: return (3, k - 6)
    return (k - 9, -1)


def heading(a, b):
    (ra, ca), (rb, cb) = node_pos(a), node_pos(b)
    if ra == rb: return 'E' if cb > ca else 'W'
    if ca == cb: return 'S' if rb > ra else 'N'
    raise ValueError((a, b))


def movement(h_in, h_out):
    """movement for a vehicle travelling with heading h_in that leaves with heading h_out."""
    order = 'NESW'  # clockwise
    d = (order.index(h_out) - order.index(h_in)) % 4
    return {0: 'T', 1: 'R', 3: 'L'}.get(d, 'U')  # U = U-turn (never allowed)


def green_phase(C, plan, order, offset, t):
    g = dict(zip('ABCD', (int(x) for x in GREENS[C][plan - 1].split('/'))))
    tau = (t - offset) % C
    start = 0
    for ph in SEQ[order]:
        if start <= tau < start + g[ph]:
            return ph
        start += g[ph] + ALL_RED
    return None  # all-red


def phase_serves(ph, h_in, mv):
    # approach N/S = vehicles travelling S/N
    ns = h_in in ('N', 'S')
    return {'A': ns and mv in 'TR', 'B': ns and mv == 'L',
            'C': (not ns) and mv in 'TR', 'D': (not ns) and mv == 'L'}.get(ph, False)


def check(path, max_report=5):
    cfg = None
    links = {}
    viol = {'I1': [], 'I2': [], 'I3': []}
    counts = {'I1': 0, 'I2': 0, 'I3': 0}
    created = {}          # v -> (t, terminal)
    created_n = 0
    departed_n = 0
    o_records = {}        # t -> set of vehicles
    queue_waiting = set() # created and not yet seen in network
    seen = set()
    prev = {}             # vehicle -> (link, cell) at previous step
    crossings = 0
    x_records = []        # (t, v, from, to)
    derived = set()
    steps = 0
    n_records = {}
    pending_P = None

    def add(kind, msg):
        counts[kind] += 1
        if len(viol[kind]) < max_report:
            viol[kind].append(msg)

    def finish_step(t, snap):
        nonlocal crossings, departed_n
        # I1: unique cells
        occ = {}
        for v, (l, c) in snap.items():
            if not (0 <= c < links[l]['len']):
                add('I1', f't={t}: vehicle {v} at invalid cell {l}:{c}')
            key = (l, c)
            if key in occ:
                add('I1', f't={t}: vehicles {occ[key]} and {v} both in link {l} ({links[l]["name"]}) cell {c}')
            else:
                occ[key] = v
        # departures recorded at this step
        gone = o_records.get(t, set())
        departed_n += len(gone)
        # I2: crossings derived from position changes
        for v, (l, c) in snap.items():
            if v in prev:
                pl, pc = prev[v]
                if pl != l:
                    L = links[pl]
                    if L['end'][0] != 'I' or pc != L['len'] - 1 or c != 0:
                        add('I2', f't={t}: vehicle {v} jumped {L["name"]}:{pc} -> {links[l]["name"]}:{c} (not a stop-line crossing)')
                        continue
                    crossings += 1
                    derived.add((t, v, pl, l))
                    h_in = heading(L['start'], L['end'])
                    h_out = heading(links[l]['start'], links[l]['end'])
                    if links[l]['start'] != L['end']:
                        add('I2', f't={t}: vehicle {v} crossed into a link not leaving {L["end"]}')
                        continue
                    mv = movement(h_in, h_out)
                    j = int(L['end'][1:])
                    ph = green_phase(cfg['C'], cfg['plan'], cfg['order'], cfg['offsets'][j], t)
                    if not phase_serves(ph, h_in, mv):
                        add('I2', f't={t}: vehicle {v} crossed {L["end"]} from {L["name"]} to {links[l]["name"]} '
                                  f'(heading {h_in}, movement {mv}) while signal shows {ph or "all-red"}')
        # I3: conservation
        for v in snap:
            if v in queue_waiting:
                queue_waiting.discard(v); seen.add(v)
            elif v not in seen:
                add('I3', f't={t}: vehicle {v} in network but never created / already departed')
        innet = len(snap)
        waiting = len(queue_waiting)
        if created_n != waiting + innet + departed_n:
            add('I3', f't={t}: created {created_n} != waiting {waiting} + in network {innet} + departed {departed_n}')
        rep = n_records.get(t)
        if rep is not None and rep != (created_n, waiting, innet, departed_n):
            add('I3', f't={t}: simulator reported (created, waiting, innet, departed)={rep}, checker derived '
                      f'{(created_n, waiting, innet, departed_n)}')
        # departed vehicles must have been in the last cell of an outbound link and now be absent
        for v in gone:
            if v in snap:
                add('I3', f't={t}: vehicle {v} recorded as departed but still in network')
            elif v not in prev or links[prev[v][0]]['end'][0] != 'T' or prev[v][1] != links[prev[v][0]]['len'] - 1:
                add('I3', f't={t}: vehicle {v} departed from a position that is not the last cell of an outbound link')
            seen.discard(v)
        for v in prev:
            if v not in snap and v not in gone:
                add('I3', f't={t}: vehicle {v} vanished from the network without a departure record')

    with open(path) as f:
        cur_t = None
        snaps = {}
        for line in f:
            if line.startswith('# GRID-14'):
                m = re.search(r'C=(\d+) plan=(\d+) order=(\w+) offsets=([\d,]+)', line)
                cfg = {'C': int(m.group(1)), 'plan': int(m.group(2)), 'order': m.group(3),
                       'offsets': [int(x) for x in m.group(4).split(',')]}
                continue
            if line.startswith('#') or not line.strip():
                continue
            parts = line.split()
            tag = parts[0]
            if tag == 'LINK':
                lid, name, ln = int(parts[1]), parts[2], int(parts[3])
                a, b = name.split('->')
                links[lid] = {'name': name, 'len': ln, 'start': a, 'end': b}
            elif tag == 'G':
                t, v, k = int(parts[1]), int(parts[2]), int(parts[3])
                created[v] = (t, k); created_n += 1; queue_waiting.add(v)
            elif tag == 'O':
                o_records.setdefault(int(parts[1]), set()).add(int(parts[2]))
            elif tag == 'X':
                x_records.append((int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4])))
            elif tag == 'N':
                n_records[int(parts[1])] = tuple(int(x) for x in parts[2:6])
                # the N record closes the step: run the step checks now
                t = int(parts[1])
                finish_step(t, pending_P)
                prev = pending_P
                steps += 1
            elif tag == 'P':
                t = int(parts[1])
                snap = {}
                for tok in parts[2:]:
                    v, l, c = (int(x) for x in tok.split(':'))
                    if v in snap:
                        add('I1', f't={t}: vehicle {v} listed twice')
                    snap[v] = (l, c)
                pending_P = snap
            elif tag == 'E':
                pass
    # X records (simulator's own crossing log) checked too and cross-matched with derived crossings
    xs = set(x_records)
    for (t, v, fl, tl) in x_records:
        L = links[fl]
        h_in = heading(L['start'], L['end'])
        h_out = heading(links[tl]['start'], links[tl]['end'])
        mv = movement(h_in, h_out)
        j = int(L['end'][1:])
        ph = green_phase(cfg['C'], cfg['plan'], cfg['order'], cfg['offsets'][j], t)
        if not phase_serves(ph, h_in, mv):
            add('I2', f'X record t={t}: vehicle {v} {L["name"]} -> {links[tl]["name"]} movement {mv} during {ph or "all-red"}')
    unmatched = len(xs ^ derived)
    if unmatched:
        add('I2', f'{unmatched} crossings differ between X records and position-derived crossings')
    return cfg, steps, crossings, len(x_records), counts, viol


def main():
    path = sys.argv[1]
    cfg, steps, crossings, nx, counts, viol = check(path)
    print(f'trace: {path}')
    print(f'configuration: C={cfg["C"]} plan={cfg["plan"]} order={cfg["order"]} offsets={cfg["offsets"]}')
    print(f'steps checked: {steps}; stop-line crossings checked: {crossings} (position-derived), {nx} (X records)')
    names = {'I1': 'no cell ever holds two vehicles',
             'I2': 'every stop-line crossing happens during a green for its movement',
             'I3': 'created = waiting + in network + departed at every step'}
    ok = True
    for k in ('I1', 'I2', 'I3'):
        status = 'PASS' if counts[k] == 0 else f'FAIL ({counts[k]} violations)'
        ok &= counts[k] == 0
        print(f'{k} {names[k]}: {status}')
        for m in viol[k]:
            print(f'    {m}')
    print('RESULT:', 'ALL INVARIANTS HOLD' if ok else 'TRACE REJECTED')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
