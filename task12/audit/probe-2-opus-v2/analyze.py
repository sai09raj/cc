#!/usr/bin/env python3
"""Combine census and stratified-sample results into whole-space numbers (Python 3 stdlib only).

Usage: python3 analyze.py <baseline_makespan> <out.json> --census c1.csv c2.csv ... --sweep s1.csv s2.csv ...

The 29,360,128 configurations are split into 448 cells (28 placements x 4 Q x 4 B), 65,536 line maps each.
 * census cells: all 65,536 maps were simulated (census.js) -> exact cell totals.
 * other cells: stratified sample from sweep.js. Only complete sweep rounds are used, so each
   non-census cell has the same number n of maps, drawn without replacement.
Estimate for a non-census cell = 65,536 x sample mean; standard error with finite-population correction.
Whole-space estimate = exact census part + estimated sampled part; reported SE covers the sampled part only.
"""
import sys, json, math
from collections import defaultdict

base = int(sys.argv[1]); outp = sys.argv[2]
args = sys.argv[3:]
census_files, sweep_files, mode = [], [], None
for a in args:
    if a == '--census': mode = 'c'; continue
    if a == '--sweep': mode = 's'; continue
    (census_files if mode == 'c' else sweep_files).append(a)

N_CELL = 65536
cells_census = defaultdict(dict)   # cell -> {map: (ms, msg, nk)}
for fn in census_files:
    with open(fn) as f:
        for line in f:
            p = line.strip().split(',')
            if len(p) != 8: continue
            d0, d1, mp, Q, B, ms, msg, nk = map(int, p)
            cells_census[(d0, d1, Q, B)][mp] = (ms, msg, nk)
census = {k: v for k, v in cells_census.items() if len(v) == N_CELL}
partial_census = {k: len(v) for k, v in cells_census.items() if len(v) != N_CELL}

rows_by_round = defaultdict(list)
for fn in sweep_files:
    with open(fn) as f:
        for line in f:
            p = line.strip().split(',')
            if len(p) != 9: continue
            d0, d1, mp, Q, B, rnd, ms, msg, nk = map(int, p)
            rows_by_round[rnd].append((d0, d1, mp, Q, B, ms, msg, nk))
rounds = sorted(r for r, v in rows_by_round.items() if len(v) == 448)
sample = defaultdict(list)
for r in rounds:
    for x in rows_by_round[r]:
        sample[(x[0], x[1], x[3], x[4])].append(x)
n = len(rounds)
fpc = 1 - n / N_CELL
all_cells = [(a, b, q, bb) for a in range(8) for b in range(a + 1, 8) for q in (1, 2, 3, 4) for bb in (1, 2, 4, 8)]
assert len(all_cells) == 448


def cell_values(k):
    """list of makespans for the cell (all maps if census, else the sample) and whether exact"""
    if k in census:
        return [v[0] for v in census[k].values()], True
    return [x[5] for x in sample[k]], False


def estimate(fn, cell_pred=lambda k: True):
    tot = 0.0; var = 0.0; exact_part = 0
    for k in all_cells:
        if not cell_pred(k): continue
        vals, exact = cell_values(k)
        t = [fn(v) for v in vals]
        if exact:
            tot += sum(t); exact_part += sum(t)
        else:
            m = sum(t) / n
            s2 = sum((a - m) ** 2 for a in t) / (n - 1)
            tot += N_CELL * m; var += N_CELL ** 2 * s2 / n * fpc
    return {'estimate': tot, 'se': math.sqrt(var), 'exact_part_from_census': exact_part}


res = {'baseline_makespan': base, 'census_cells': sorted([list(k) for k in census]), 'partial_census_cells_ignored': {str(k): v for k, v in partial_census.items()},
       'sweep_rounds_used': n, 'sample_maps_per_noncensus_cell': n}
census_runs = len(census) * N_CELL
sample_runs_outside = sum(len(sample[k]) for k in all_cells if k not in census)
sample_runs_inside = sum(len(sample[k]) for k in all_cells if k in census)
res['distinct_configs_used'] = census_runs + sample_runs_outside
res['census_runs'] = census_runs; res['sample_runs_outside_census'] = sample_runs_outside; res['sample_runs_inside_census_cells(duplicates)'] = sample_runs_inside
res['sum_makespan'] = estimate(lambda v: v)
res['count_below_baseline'] = estimate(lambda v: 1 if v < base else 0)
res['count_le_6000'] = estimate(lambda v: 1 if v <= 6000 else 0)
res['below_baseline_by_Q'] = {q: estimate(lambda v: 1 if v < base else 0, lambda k, q=q: k[2] == q) for q in (1, 2, 3, 4)}
res['below_baseline_by_B'] = {b: estimate(lambda v: 1 if v < base else 0, lambda k, b=b: k[3] == b) for b in (1, 2, 4, 8)}
res['mean_makespan_by_Q'] = {q: estimate(lambda v: v, lambda k, q=q: k[2] == q)['estimate'] / (N_CELL * 112) for q in (1, 2, 3, 4)}
res['mean_makespan_by_B'] = {b: estimate(lambda v: v, lambda k, b=b: k[3] == b)['estimate'] / (N_CELL * 112) for b in (1, 2, 4, 8)}
res['mean_makespan_by_placement'] = {f'N{a}-N{b}': estimate(lambda v: v, lambda k, a=a, b=b: k[0] == a and k[1] == b)['estimate'] / (N_CELL * 16)
                                     for a in range(8) for b in range(a + 1, 8)}
res['mean_makespan_by_QB'] = {f'Q{q}B{b}': estimate(lambda v: v, lambda k, q=q, b=b: k[2] == q and k[3] == b)['estimate'] / (N_CELL * 28)
                              for q in (1, 2, 3, 4) for b in (1, 2, 4, 8)}
res['mean_makespan_overall'] = res['sum_makespan']['estimate'] / 29360128
# knob importance: spread of the mean makespan when one knob changes, others averaged
pm = res['mean_makespan_by_placement'].values()
res['knob_spread_of_means'] = {
    'placement (best..worst mean)': [min(pm), max(pm)],
    'Q (min..max mean)': [min(res['mean_makespan_by_Q'].values()), max(res['mean_makespan_by_Q'].values())],
    'B (min..max mean)': [min(res['mean_makespan_by_B'].values()), max(res['mean_makespan_by_B'].values())],
}
# within-cell spread over line maps (sample sd averaged over cells)
sds = []
for k in all_cells:
    vals, _ = cell_values(k)
    m = sum(vals) / len(vals); sds.append(math.sqrt(sum((a - m) ** 2 for a in vals) / (len(vals) - 1)))
res['mean_within_cell_sd_over_line_maps'] = sum(sds) / len(sds)
# variance decomposition on the uniform stratified sweep sample (all 448 cells, equal n each)
srows = [x for r in rounds for x in rows_by_round[r]]
mu = sum(x[5] for x in srows) / len(srows); tv = sum((x[5] - mu) ** 2 for x in srows) / len(srows)


def share(keyf):
    g = defaultdict(list)
    for x in srows:
        g[keyf(x)].append(x[5])
    return sum(len(v) * (sum(v) / len(v) - mu) ** 2 for v in g.values()) / len(srows) / tv


res['variance_share_of_makespan_from_sweep_sample'] = {
    'placement_main_effect': share(lambda x: (x[0], x[1])), 'Q_main_effect': share(lambda x: x[3]), 'B_main_effect': share(lambda x: x[4]),
    'placement_Q_B_cells_together': share(lambda x: (x[0], x[1], x[3], x[4])),
    'line_map_within_cell(remainder)': 1 - share(lambda x: (x[0], x[1], x[3], x[4])), 'total_variance': tv}
# hot-line analysis on census cells: mean makespan by home bank of L0,L1,L2
hot = {}
for k in census:
    g = defaultdict(list)
    for mp, v in census[k].items():
        g[''.join('D1' if (mp >> L) & 1 else 'D0' for L in (0, 1, 2))].append(v[0])
    hot[str(k)] = {h: round(sum(v) / len(v), 1) for h, v in sorted(g.items())}
res['census_mean_by_home_of_L0_L1_L2'] = hot
# census per-cell stats
res['census_cell_stats'] = {str(k): {'min': min(v[0] for v in census[k].values()), 'mean': sum(v[0] for v in census[k].values()) / N_CELL,
                                     'max': max(v[0] for v in census[k].values()),
                                     'below_baseline': sum(1 for v in census[k].values() if v[0] < base),
                                     'le_6000': sum(1 for v in census[k].values() if v[0] <= 6000)} for k in sorted(census)}
# best configuration found (spec tie-break: makespan, messages, D0, D1, Q, B, map)
cands = []
for k, d in census.items():
    for mp, v in d.items():
        cands.append((v[0], v[1], k[0], k[1], k[2], k[3], mp, v[2]))
for k in all_cells:
    if k in census: continue
    for x in sample[k]:
        cands.append((x[5], x[6], x[0], x[1], x[3], x[4], x[2], x[7]))
cands.sort()
res['best_found'] = [dict(makespan=c[0], messages=c[1], D0=c[2], D1=c[3], Q=c[4], B=c[5], map=c[6], nacks=c[7]) for c in cands[:15]]
# best per placement among what was simulated
bp = {}
for c in cands:
    key = f'N{c[2]}-N{c[3]}'
    if key not in bp: bp[key] = dict(makespan=c[0], messages=c[1], Q=c[4], B=c[5], map=c[6])
res['best_found_per_placement'] = bp
json.dump(res, open(outp, 'w'), indent=1)
print(json.dumps({k: res[k] for k in ('distinct_configs_used', 'census_runs', 'sample_runs_outside_census', 'sweep_rounds_used', 'sum_makespan', 'count_below_baseline',
                                      'count_le_6000', 'below_baseline_by_Q', 'below_baseline_by_B', 'mean_makespan_by_Q', 'mean_makespan_by_B', 'knob_spread_of_means',
                                      'mean_within_cell_sd_over_line_maps', 'variance_share_of_makespan_from_sweep_sample')}, indent=1))
print('best', res['best_found'][:3])
