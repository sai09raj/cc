#!/usr/bin/env python3
"""Make two deliberately corrupted copies of a GRID-14 trace (standard library only).

  altered_red_crossing: one stop-line crossing is moved one step earlier, into a step at which the
      vehicle had been held at the stop line although its target cell was empty (i.e. a red step);
  altered_double_cell:  one vehicle is placed in the cell of the vehicle directly ahead of it
      (same link, so no other record changes meaning).
Usage: make_altered_traces.py trace.txt out_red.txt out_double.txt
"""
import sys


def load(path):
    header, steps = [], []
    cur = None
    with open(path) as f:
        for line in f:
            line = line.rstrip('\n')
            if line.startswith('STEP '):
                cur = [line]
                steps.append(cur)
            elif cur is None:
                header.append(line)
            else:
                cur.append(line)
    return header, steps


def pos_map(step_lines):
    for ln in step_lines:
        if ln.startswith('POS'):
            items = ln.split()[1:]
            return {int(a): (int(b), int(c)) for a, b, c in (x.split(':') for x in items)}
    return {}


def set_pos(step_lines, newpos):
    for i, ln in enumerate(step_lines):
        if ln.startswith('POS'):
            step_lines[i] = 'POS ' + ' '.join(f'{v}:{l}:{c}' for v, (l, c) in newpos.items())


def main(src, out_red, out_double):
    header, steps = load(src)
    nlen = {}
    for ln in header:
        if ln.startswith('LINK '):
            p = ln.split()
            nlen[int(p[1])] = (int(p[2]), p[3])
    P = [pos_map(s) for s in steps]

    # ---- 1. move a crossing into a red interval
    K = 3  # move the crossing K steps earlier, deep enough into the red that another phase is green
    target = None
    for t in range(K + 2, len(steps)):
        for v, (l, c) in P[t].items():
            if c != 0 or v not in P[t - 1]:
                continue
            pl, pc = P[t - 1][v]
            if pl == l or nlen[pl][1] == 'out' or pc != nlen[pl][0] - 1:
                continue
            # crossing at step t from (pl, last) into (l, 0). Require the vehicle to have been held at the
            # stop line for steps t-K-1 .. t-1 while cell 0 of link l stayed empty: it was therefore held
            # by a red signal at steps t-K .. t-1.
            ok = all(P[t - d].get(v) == (pl, pc) for d in range(1, K + 2))
            ok = ok and all((l, 0) not in set(P[t - d].values()) for d in range(1, K + 2))
            if ok:
                target = (t, v, pl, l)
                break
        if target:
            break
    t, v, pl, l = target
    red_steps = [list(s) for s in steps]
    for d in range(1, K + 1):
        newpos = dict(P[t - d]); newpos[v] = (l, 0)
        set_pos(red_steps[t - d], newpos)
    with open(out_red, 'w') as f:
        f.write('\n'.join(header) + '\n')
        for s in red_steps:
            f.write('\n'.join(s) + '\n')
    print(f'red-crossing alteration: vehicle {v} crossing from link {pl} into link {l} moved from step {t} to step {t - K} '
          f'(it is shown in cell 0 of link {l} at steps {t - K}..{t - 1})')

    # ---- 2. two vehicles in one cell
    target2 = None
    for t2 in range(1000, len(steps)):
        byl = {}
        for vv, (ll, cc) in P[t2].items():
            byl.setdefault(ll, []).append((cc, vv))
        for ll, lst in byl.items():
            lst.sort()
            for (c1, v1), (c2, v2) in zip(lst, lst[1:]):
                if c2 == c1 + 1 and P[t2 - 1].get(v1, (None,))[0] == ll:
                    target2 = (t2, v1, v2, ll, c2)
                    break
            if target2: break
        if target2: break
    t2, v1, v2, ll, c2 = target2
    dbl_steps = [list(s) for s in steps]
    newpos = dict(P[t2]); newpos[v1] = (ll, c2)
    set_pos(dbl_steps[t2], newpos)
    with open(out_double, 'w') as f:
        f.write('\n'.join(header) + '\n')
        for s in dbl_steps:
            f.write('\n'.join(s) + '\n')
    print(f'double-cell alteration: at step {t2} vehicle {v1} placed in link {ll} cell {c2}, already holding vehicle {v2}')


if __name__ == '__main__':
    main(*sys.argv[1:4])
