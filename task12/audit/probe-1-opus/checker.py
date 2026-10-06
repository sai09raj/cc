#!/usr/bin/env python3
"""Independent invariant checker for a COHERE-12 simulator trace (stdlib only).

It does not import the simulator. It replays the trace and verifies:
  (1) SWMR-M: at no point (and hence at no cycle) do two caches hold the
      same line in state M;
  (2) every load (hit or miss) returns the value of the most recent store
      to that line in the trace's global order (initial value 0).
It also cross-checks that every state-change record starts from the state the
checker believes the cache is in, and that cycles never go backwards.

Usage: python3 checker.py TRACE_FILE [--selftest]
Exit code 0 if all invariants hold, 1 otherwise.
"""
import sys
import re

ST_RE = re.compile(r"^ST C(\d+) L(\d+) (\S+)->(\S+)$")
LD_RE = re.compile(r"^LD C(\d+) L(\d+) val=(\S+) (hit|miss)")
STORE_RE = re.compile(r"^STORE C(\d+) L(\d+) val=(-?\d+)$")


def check(lines):
    state = {}              # (cache, line) -> state  (absent == I)
    holders_m = {}          # line -> set of caches in M
    last_store = {}         # line -> value
    errors = []
    n_loads = n_stores = n_trans = 0
    max_m = 0
    last_cycle = 0
    cycles_checked = set()
    for lineno, raw in enumerate(lines, 1):
        raw = raw.rstrip("\n")
        if not raw or raw.startswith("#"):
            continue
        cyc_s, _, ev = raw.partition(" ")
        cyc = int(cyc_s)
        if cyc < last_cycle:
            errors.append("line %d: cycle went backwards" % lineno)
        last_cycle = cyc
        cycles_checked.add(cyc)
        m = ST_RE.match(ev)
        if m:
            c, L, old, new = int(m.group(1)), int(m.group(2)), m.group(3), m.group(4)
            n_trans += 1
            cur = state.get((c, L), "I")
            if cur != old:
                errors.append("line %d: C%d L%d trace says %s but replay has %s"
                              % (lineno, c, L, old, cur))
            if new == "I":
                state.pop((c, L), None)
            else:
                state[(c, L)] = new
            s = holders_m.setdefault(L, set())
            s.discard(c)
            if new == "M":
                s.add(c)
            max_m = max(max_m, len(s))
            if len(s) > 1:
                errors.append("cycle %d: line %d in M at caches %s"
                              % (cyc, L, sorted(s)))
            continue
        m = STORE_RE.match(ev)
        if m:
            c, L, v = int(m.group(1)), int(m.group(2)), int(m.group(3))
            n_stores += 1
            if state.get((c, L)) != "M":
                errors.append("line %d: store by C%d to L%d not in M (%s)"
                              % (lineno, c, L, state.get((c, L), "I")))
            last_store[L] = v
            continue
        m = LD_RE.match(ev)
        if m:
            c, L, v = int(m.group(1)), int(m.group(2)), m.group(3)
            n_loads += 1
            exp = last_store.get(L, 0)
            if v == "None" or int(v) != exp:
                errors.append("cycle %d: C%d load L%d returned %s, most recent store %d"
                              % (cyc, c, L, v, exp))
            continue
    return {"errors": errors, "loads": n_loads, "stores": n_stores,
            "transitions": n_trans, "max_M_holders": max_m,
            "cycles": len(cycles_checked), "last_cycle": last_cycle}


def report(name, r):
    print("%s: %d loads, %d stores, %d state transitions over %d event cycles (last %d); "
          "max simultaneous M holders of one line = %d"
          % (name, r["loads"], r["stores"], r["transitions"], r["cycles"],
             r["last_cycle"], r["max_M_holders"]))
    if r["errors"]:
        print("FAIL: %d violation(s)" % len(r["errors"]))
        for e in r["errors"][:20]:
            print("  " + e)
    else:
        print("PASS: single-writer (M) invariant and load-value invariant hold")


def selftest(lines):
    """Inject faults to show the checker detects them."""
    ok = True
    # fault 1: corrupt the value of the first miss load that read a nonzero value
    mut = list(lines)
    for i, l in enumerate(mut):
        mm = re.match(r"^(\d+) LD (C\d+ L\d+) val=(\d+) (.*)$", l.rstrip("\n"))
        if mm and int(mm.group(3)) != 0:
            mut[i] = "%s LD %s val=%d %s\n" % (mm.group(1), mm.group(2),
                                               int(mm.group(3)) + 1, mm.group(4))
            break
    r = check(mut)
    print("selftest stale-load fault detected:", bool(r["errors"]))
    ok &= bool(r["errors"])
    # fault 2: insert a second M holder right after the first ->M transition
    mut = list(lines)
    for i, l in enumerate(mut):
        mm = re.match(r"^(\d+) ST C(\d+) L(\d+) \S+->M$", l.rstrip("\n"))
        if mm:
            other = (int(mm.group(2)) + 1) % 8
            mut.insert(i + 1, "%s ST C%d L%s I->M\n" % (mm.group(1), other, mm.group(3)))
            break
    r = check(mut)
    print("selftest double-M fault detected:", bool(r["errors"]))
    ok &= bool(r["errors"])
    return ok


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    with open(argv[1]) as f:
        lines = f.readlines()
    r = check(lines)
    report(argv[1], r)
    rc = 1 if r["errors"] else 0
    if "--selftest" in argv:
        if not selftest(lines):
            rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))
