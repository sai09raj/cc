#!/usr/bin/env python3
"""Aggregate GRID-14 exploration output (standard library only).

Usage: grid14_analyze.py BASELINE_TOTAL sample_csv_glob all_csv_glob > analysis.json
  sample files: the stratified uniform sample (used for whole-space estimates);
  all files:    every simulated configuration (sample + exhaustive stratum + descent), used for the
                count of distinct configurations simulated and for the best configuration found.
"""
import csv, glob, json, math, sys
from collections import defaultdict

CYCLES = [60, 72, 84, 96, 108, 120]
NOFF = 4 ** 9
SPACE = 6 * 6 * 2 * NOFF


def read(globpat):
    rows = []
    for fn in sorted(glob.glob(globpat)):
        with open(fn) as f:
            for r in csv.reader(f):
                if len(r) != 10:
                    continue
                rows.append({'idx': int(r[0]), 'C': int(r[1]), 'plan': int(r[2]), 'order': r[3],
                             'offsets': [int(float(x)) for x in r[4].split(';')], 'AM': int(r[5]), 'PM': int(r[6]),
                             'EVENT': int(r[7]), 'total': int(r[8]), 'grid': int(r[9])})
    return rows


def main():
    base = int(sys.argv[1])
    sample = read(sys.argv[2])
    allrows = read(sys.argv[3])
    out = {}
    # ---------------- stratified estimates (72 equal-size strata)
    strata = defaultdict(list)
    for r in sample:
        strata[(r['C'], r['plan'], r['order'])].append(r)
    assert len(strata) == 72, len(strata)
    Ns = NOFF

    # strata that were enumerated completely (all 4^9 offset vectors simulated) are used exactly
    uniq_all = {}
    for r in allrows: uniq_all[r['idx']] = r
    full = defaultdict(list)
    for r in uniq_all.values(): full[(r['C'], r['plan'], r['order'])].append(r)
    exact_strata = {k: v for k, v in full.items() if len(v) == NOFF}
    out['exhaustively_enumerated_strata'] = [list(k) for k in sorted(exact_strata)]

    def strat_est(fn, groups=None, count=False):
        """estimate sum over the space of fn(row) restricted to strata in `groups` (None = all).
        Completely enumerated strata contribute their exact sum (zero variance)."""
        est = 0.0; var = 0.0; nsamp = 0; nstrata = 0
        for key, rs in strata.items():
            if groups is not None and not groups(key):
                continue
            nstrata += 1
            if key in exact_strata:
                est += sum(fn(r) for r in exact_strata[key]); continue
            n = len(rs); vals = [fn(r) for r in rs]; nsamp += n
            m = sum(vals) / n
            v = sum((x - m) ** 2 for x in vals) / (n - 1) if n > 1 else 0.0
            est += Ns * m; var += Ns * Ns * v / n
        se = math.sqrt(var)
        lo, hi = est - 1.96 * se, est + 1.96 * se
        if count:  # a count lies in [0, size of the group]
            lo, hi = max(lo, 0.0), min(hi, float(nstrata * Ns))
        return {'estimate': est, 'se': se, 'ci95': [lo, hi],
                # rule of three: if no sampled configuration qualifies, 95% upper bound on the count
                'zero_in_sample_upper95': (3.0 / nsamp * nstrata * Ns) if (est == 0 and nsamp) else None}

    out['sample_size'] = len(sample)
    out['sample_per_stratum'] = sorted(set(len(v) for v in strata.values()))
    out['sum_total_tts'] = strat_est(lambda r: r['total'])
    out['count_below_baseline'] = strat_est(lambda r: 1 if r['total'] < base else 0, count=True)
    out['count_gridlock'] = strat_est(lambda r: r['grid'], count=True)
    out['below_baseline_by_cycle'] = {C: strat_est(lambda r: 1 if r['total'] < base else 0, lambda k, C=C: k[0] == C, count=True) for C in CYCLES}
    out['below_baseline_by_plan'] = {p: strat_est(lambda r: 1 if r['total'] < base else 0, lambda k, p=p: k[1] == p, count=True) for p in range(1, 7)}
    out['gridlock_by_cycle'] = {C: strat_est(lambda r: r['grid'], lambda k, C=C: k[0] == C, count=True) for C in CYCLES}
    # mean total TTS by knob (sample means; equal-size strata so plain means are unbiased)
    def mean_by(keyf):
        d = defaultdict(list)
        for r in sample: d[keyf(r)].append(r['total'])
        return {str(k): {'mean': sum(v) / len(v), 'n': len(v), 'min': min(v)} for k, v in sorted(d.items())}
    out['mean_total_by_cycle'] = mean_by(lambda r: r['C'])
    out['mean_total_by_plan'] = mean_by(lambda r: r['plan'])
    out['mean_total_by_order'] = mean_by(lambda r: r['order'])
    out['mean_total_by_cycle_order'] = mean_by(lambda r: f"{r['C']}-{r['order']}")
    out['mean_by_scenario_and_cycle'] = {str(C): {s: sum(r[s] for r in sample if r['C'] == C) / sum(1 for r in sample if r['C'] == C) for s in ('AM', 'PM', 'EVENT')} for C in CYCLES}
    out['gridlock_rate_by_cycle_order'] = {f'{C}-{o}': sum(r['grid'] for r in sample if r['C'] == C and r['order'] == o) / sum(1 for r in sample if r['C'] == C and r['order'] == o) for C in CYCLES for o in ('lead', 'lag')}
    # variance decomposition of total TTS in the sample (main effects + within-stratum = offsets)
    allv = [r['total'] for r in sample]; gm = sum(allv) / len(allv)
    sst = sum((x - gm) ** 2 for x in allv)
    def ss_between(keyf):
        d = defaultdict(list)
        for r in sample: d[keyf(r)].append(r['total'])
        return sum(len(v) * (sum(v) / len(v) - gm) ** 2 for v in d.values())
    ss_c = ss_between(lambda r: r['C']); ss_p = ss_between(lambda r: r['plan']); ss_o = ss_between(lambda r: r['order'])
    ss_strat = ss_between(lambda r: (r['C'], r['plan'], r['order']))
    out['variance_share'] = {'cycle_main': ss_c / sst, 'plan_main': ss_p / sst, 'order_main': ss_o / sst,
                             'cycle_plan_order_joint': ss_strat / sst, 'offsets_within_stratum': 1 - ss_strat / sst}
    # within-stratum spread caused by offsets
    spread = []
    for key, rs in strata.items():
        v = [r['total'] for r in rs]
        spread.append((key, min(v), sum(v) / len(v), max(v)))
    spread.sort(key=lambda x: x[2])
    out['strata_by_mean'] = [{'C': k[0], 'plan': k[1], 'order': k[2], 'min': a, 'mean': b, 'max': c} for k, a, b, c in spread]
    # ---------------- everything simulated
    uniq = {}
    for r in allrows: uniq[r['idx']] = r
    out['distinct_configurations_simulated'] = len(uniq)
    out['simulated_below_baseline_exact'] = sum(1 for r in uniq.values() if r['total'] < base)
    out['simulated_gridlock_exact'] = sum(1 for r in uniq.values() if r['grid'])
    out['simulated_sum_total_exact'] = sum(r['total'] for r in uniq.values())
    out['exhausted_strata_detail'] = {f'{k[0]}-{k[1]}-{k[2]}': {
        'n': len(v), 'sum_total': sum(r['total'] for r in v), 'below_baseline': sum(1 for r in v if r['total'] < base),
        'gridlock': sum(r['grid'] for r in v), 'min': min(r['total'] for r in v), 'mean': sum(r['total'] for r in v) / len(v),
        'max': max(r['total'] for r in v),
        'best': min(v, key=lambda r: (r['total'], r['idx']))} for k, v in exact_strata.items()}
    best = min(uniq.values(), key=lambda r: (r['total'], r['idx']))
    out['best_found'] = best
    top = sorted(uniq.values(), key=lambda r: (r['total'], r['idx']))[:15]
    out['top15_found'] = top
    json.dump(out, sys.stdout, indent=1)


if __name__ == '__main__':
    main()
