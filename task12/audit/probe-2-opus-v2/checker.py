#!/usr/bin/env python3
"""COHERE-12 trace checker (Python 3 standard library only; coded separately from sim.js).

Reads a trace written by `node sim.js baseline trace.txt` and checks:
  Invariant 1 (single writer): at no cycle do two caches hold the same line in state M.
  Invariant 2 (value): every load returns the value of the most recent store to that line
                       (memory starts at 0 for every line).
Trace lines are in execution order. Relevant records:
  STATE <cycle> C<c> L<l> <old> <new>
  LOAD  <cycle> C<c> L<l> <value> hit|miss
  STORE <cycle> C<c> L<l> <value> hit|miss
Extra consistency checks: cycles never decrease; each STATE record's <old> matches the
checker's own reconstruction of that cache line; load hits only in S/SM_AD/SM_A/M; store hits
only in M; store-miss completions only on a line that just entered M; store values follow
1000*core + (stores completed by that core).
Exit status 0 when both invariants hold, 1 otherwise.
"""
import sys
from collections import defaultdict


def check(path, verbose=True):
    state = defaultdict(lambda: 'I')        # (core, line) -> state reconstructed from STATE records
    m_holders = defaultdict(set)            # line -> set of cores holding it in M
    last_store = defaultdict(int)           # line -> value of most recent store (0 = initial memory)
    store_count = defaultdict(int)          # core -> stores completed
    v1, v2, other = [], [], []
    loads = stores = transitions = 0
    max_m_holders = 0
    last_cycle = 0
    with open(path) as f:
        for ln, raw in enumerate(f, 1):
            p = raw.split()
            if not p:
                continue
            kind = p[0]
            if kind in ('CONFIG', 'END'):
                continue
            cyc = int(p[1])
            if cyc < last_cycle:
                other.append(f'line {ln}: cycle went backwards ({cyc} < {last_cycle})')
            last_cycle = cyc
            if kind == 'STATE':
                core, line, old, new = int(p[2][1:]), int(p[3][1:]), p[4], p[5]
                transitions += 1
                if state[(core, line)] != old:
                    other.append(f'line {ln}: C{core} L{line} recorded old state {old} but reconstructed {state[(core, line)]}')
                state[(core, line)] = new
                if old == 'M':
                    m_holders[line].discard(core)
                if new == 'M':
                    if m_holders[line] - {core}:
                        v1.append(f'cycle {cyc}: C{core} enters M on L{line} while {sorted(m_holders[line])} hold M')
                    m_holders[line].add(core)
                    max_m_holders = max(max_m_holders, len(m_holders[line]))
            elif kind == 'LOAD':
                core, line, val, how = int(p[2][1:]), int(p[3][1:]), int(p[4]), p[5]
                loads += 1
                if how == 'hit' and state[(core, line)] not in ('S', 'SM_AD', 'SM_A', 'M'):
                    other.append(f'line {ln}: load hit in state {state[(core, line)]}')
                if how == 'miss' and state[(core, line)] != 'S':
                    other.append(f'line {ln}: load miss completed in state {state[(core, line)]}')
                if val != last_store[line]:
                    v2.append(f'cycle {cyc}: C{core} load L{line} returned {val}, most recent store wrote {last_store[line]}')
            elif kind == 'STORE':
                core, line, val, how = int(p[2][1:]), int(p[3][1:]), int(p[4]), p[5]
                stores += 1
                if state[(core, line)] != 'M':
                    other.append(f'line {ln}: store completed in state {state[(core, line)]}')
                store_count[core] += 1
                if val != 1000 * core + store_count[core]:
                    other.append(f'line {ln}: store value {val} != {1000 * core + store_count[core]}')
                last_store[line] = val
    ok1, ok2 = not v1, not v2
    if verbose:
        print(f'trace: {path}')
        print(f'records: {transitions} state transitions, {loads} loads, {stores} stores, last cycle {last_cycle}')
        print(f'Invariant 1 (at most one M holder per line at every cycle): {"PASS" if ok1 else "FAIL"}'
              f' ({len(v1)} violations; max simultaneous M holders of a line = {max_m_holders})')
        for v in v1[:10]:
            print('   ', v)
        print(f'Invariant 2 (every load returns the most recent store): {"PASS" if ok2 else "FAIL"}'
              f' ({len(v2)} violations over {loads} loads)')
        for v in v2[:10]:
            print('   ', v)
        print(f'Trace consistency checks: {"PASS" if not other else "FAIL"} ({len(other)} problems)')
        for v in other[:10]:
            print('   ', v)
    return ok1, ok2, other


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('usage: python3 checker.py <trace file>')
        sys.exit(2)
    a, b, o = check(sys.argv[1])
    sys.exit(0 if (a and b) else 1)
