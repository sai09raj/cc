#!/usr/bin/env python3
"""Compose results.txt from the executed programs' outputs (no numbers are typed in by hand).

usage: python3 make_results.py named.csv analysis.json checker_logs_dir inputs.txt > results.txt
"""
import json
import os
import sys

named_csv, an_json, logdir, inputs_txt = sys.argv[1:5]
named = {}
for line in open(named_csv):
    q = line.strip().split(',')
    if len(q) == 17:
        named[f'{q[0]}/{q[1]}/{q[2]}/{"".join(q[3:12])}'] = [int(x) for x in q[12:17]]
A = json.load(open(an_json))
base = named['84/1/lead/000000000']
B = base[3]


def f(x):
    return f'{x:,.0f}'


def ci(est, se):
    return f'{f(est)}  (standard error {f(se)}; 95% interval {f(est - 1.96 * se)} .. {f(est + 1.96 * se)})'


P = print
P('GRID-14 RESULTS  (every number below was produced by the delivered programs; see memo.md for commands)')
P('=' * 100)
P('Runtime: ' + open(os.path.join(logdir, 'runtime.txt')).read().strip())
P()
P('1. VALUES READ FROM THE FIGURES')
P(open(inputs_txt).read().rstrip())
P()
P('2. BASELINE  (C = 84 s, plan 1, lead, all offsets 0)')
P(f'   AM TTS    = {base[0]}')
P(f'   PM TTS    = {base[1]}')
P(f'   EVENT TTS = {base[2]}')
P(f'   total TTS = {base[3]}   gridlock: {"yes" if base[4] else "no"}')
P()
P('3. VARIANTS OF THE BASELINE  (total TTS; AM / PM / EVENT in brackets)')
for label, k in (('offsets 0, 21, 42 s west->east in every row', '84/1/lead/012012012'),
                 ('lag instead of lead', '84/1/lag/000000000'),
                 ('cycle 60 s instead of 84 s', '60/1/lead/000000000')):
    r = named[k]
    P(f'   {label:45s} total = {r[3]}  ({r[0]} / {r[1]} / {r[2]}), change vs baseline {r[3] - B:+d} '
      f'({100 * (r[3] - B) / B:+.2f}%), gridlock: {"yes" if r[4] else "no"}')
P()
P('4. WHOLE CONFIGURATION SPACE (18,874,368 configurations)')
P(f'   Configurations actually simulated (distinct): {A["distinct_configs_simulated"]:,} '
  f'= {100 * A["distinct_configs_simulated"] / 18874368:.3f}% of the space.')
P('   The space was NOT simulated exhaustively, so every whole-space quantity below is a STATISTICAL ESTIMATE')
P(f'   from a stratified uniform random sample of {A["n_sample"]:,} configurations '
  f'({A["per_stratum_n_min"]}..{A["per_stratum_n_max"]} per (cycle, plan, order) stratum, offsets uniform over 4^9),')
P('   expanded by the stratum size 262,144. They are not exact counts/sums.')
P(f'   Sum of total TTS over all configurations: {ci(*A["sum_total_TTS"])}')
c = A['count_below']
P(f'   Number with total TTS below the baseline ({B}): {ci(c[0], c[1])}')
P(f'       (strata in which every sampled configuration fell on the same side of the baseline contribute no')
P(f'        sampling variance; their combined 95% bound on misclassified configurations is {f(c[2])})')
g = A['count_grid']
P(f'   Number that gridlock: {ci(g[0], g[1])}  (same caveat; bound {f(g[2])})')
P('   Below-baseline count by cycle length:')
for C, v in A['by_cycle'].items():
    b = v['below']
    P(f'      C = {C:>3} s: {ci(b[0], b[1])}   [sample: {v["nbelow_sample"]} of {v["nsample"]} below; '
      f'95% bound for unanimous strata {f(b[2])}]')
P('   Below-baseline count by timing plan:')
for p, v in A['by_plan'].items():
    b = v['below']
    P(f'      plan {p}: {ci(b[0], b[1])}   [sample: {v["nbelow_sample"]} of {v["nsample"]} below; '
      f'95% bound for unanimous strata {f(b[2])}]')
P()
P('5. BEST CONFIGURATION FOUND  (not proven optimal: only part of the space was simulated)')
b = A['best']
P(f'   C = {b["C"]} s, plan {b["plan"]}, {b["order"]}, offsets I0..I8 = {b["offsets_s"]} s '
  f'(multiples of C/4: {"".join(str(k) for k in b["k"])})')
P(f'   AM = {b["AM"]}, PM = {b["PM"]}, EVENT = {b["EVENT"]}, total TTS = {b["total"]} '
  f'({100 * (b["total"] - B) / B:+.2f}% vs baseline), gridlock: {"yes" if b["gridlock"] else "no"}')
P('   Ten best distinct configurations found:')
for r in A['top10']:
    P(f'      {r["total"]}  C={r["C"]} plan {r["plan"]} {r["order"]} offsets {r["offsets_s"]}')
P('   Best found in each of the 12 C = 60 strata (search effort was concentrated there):')
for h, r in A['best_by_stratum'].items():
    if h.startswith('60/'):
        P(f'      {h:12s} {r["total"]}  offsets {r["offsets_s"]}')
P()
P('6. AVERAGE TOTAL TTS BY KNOB (stratified-sample estimates, standard error in brackets)')
for C, v in A['by_cycle'].items():
    P(f'   C = {C:>3} s: mean total TTS {f(v["mean_total"])} ({f(v["mean_total_se"])}), estimated gridlocking configs {f(v["grid"][0])}')
for o, v in A['by_order'].items():
    P(f'   {o:4s}: mean total TTS {f(v["mean_total"])} ({f(v["mean_total_se"])}), estimated gridlocking configs {f(v["grid"][0])}')
for p, v in A['by_plan'].items():
    P(f'   plan {p}: mean total TTS {f(v["mean_total"])} ({f(v["mean_total_se"])})')
P('   cycle x order mean total TTS (gridlock fraction):')
for k, v in A['by_cycle_order'].items():
    P(f'      {k:9s} {f(v["mean_total"])}  ({v["grid_frac"]:.3f})')
vs = A['variance_shares']
P('   Share of the variance of total TTS over the whole space explained by:')
P(f'      cycle {100 * vs["cycle"]:.1f}%, order {100 * vs["order"]:.1f}%, plan {100 * vs["plan"]:.2f}%, '
  f'C x plan x order interactions {100 * vs["interactions_C_plan_order"]:.1f}%, offsets (within stratum) {100 * vs["offsets_within_stratum"]:.1f}%')
v6 = A['variance_shares_C60']
P(f'   Within C = 60 only: plan/order {100 * v6["between_plan_order"]:.1f}%, offsets {100 * v6["offsets_within"]:.1f}%')
P()
P('7. TRACE CHECKER (checker.py, separately coded) ON THE BASELINE AM TRACE AND TWO ALTERED COPIES')
for name in ('check_baseline.txt', 'alter.txt', 'check_red.txt', 'check_double.txt'):
    P(f'   --- {name}')
    for line in open(os.path.join(logdir, name)).read().rstrip().split('\n'):
        P('   ' + line)
