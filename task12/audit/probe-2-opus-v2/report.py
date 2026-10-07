#!/usr/bin/env python3
"""Render results.md from the executed programs' outputs (Python 3 stdlib only).
Usage: python3 report.py analysis.json runs.json checker.txt > results.md
runs.json holds the JSON lines printed by `node sim.js` for the baseline and the variants.
"""
import sys, json

an = json.load(open(sys.argv[1])); runs = json.load(open(sys.argv[2])); chk = open(sys.argv[3]).read().strip()
b = runs['baseline']
f = lambda x: f'{x:,.0f}'


def est(e):
    if e['se'] == 0:
        return f"{f(e['estimate'])} (exact)"
    return f"≈ {f(e['estimate'])} ± {f(1.96 * e['se'])} (95% CI; SE {f(e['se'])}; exact census part {f(e['exact_part_from_census'])})"


out = []
P = out.append
P('# COHERE-12 results\n')
P('All numbers below come from the programs in this directory, executed offline: simulator `sim.js` '
  f'(Node.js {runs["node"]}), checker `checker.py` and analysis scripts (Python {runs["python"]}).\n')
P('## Values read from the figures\n')
P('* Figure 1 (floorplan): node Nn is at row n div 4, column n mod 4 (N0..N3 = row 0, columns 0..3; N4..N7 = row 1, columns 0..3); core Cn sits on node Nn.')
P('* Figure 2 (link latency, cycles, both directions): N0-N1 = 1, N1-N2 = 2, N2-N3 = 1, N4-N5 = 2, N5-N6 = 1, N6-N7 = 3, '
  'N0-N4 = 1, N1-N5 = 3, N2-N6 = 1, N3-N7 = 2. (Measured from the embedded image: bars end exactly on the 1st/2nd/3rd major gridline; '
  'pixel ends 802/1291/1779 vs gridlines at 803/1292/1780, axis origin 317.)')
P('* Figure 5 (baseline line map): L0 D1, L1 D0, L2 D1, L3 D1, L4 D0, L5 D1, L6 D0, L7 D0, L8 D1, L9 D1, L10 D0, L11 D1, L12 D0, L13 D0, L14 D1, L15 D0 '
  '-> bits 0,2,3,5,8,9,11,14 set -> **line map number 19245** (0x4B2D).\n')
P('## Baseline and variants (each a single executed run)\n')
P('| run | D0 | D1 | line map | Q | B | makespan | p95 load-miss latency | messages | Nacks |')
P('|---|---|---|---|---|---|---|---|---|---|')
for name, key, cfg in [('Baseline', 'baseline', (0, 7, 19245, 2, 2)), ('Variant 1: line map 43690', 'v1', (0, 7, 43690, 2, 2)),
                       ('Variant 2: D0 N1, D1 N6', 'v2', (1, 6, 19245, 2, 2)), ('Variant 3: D0 N1, D1 N6, Q=4, B=1', 'v3', (1, 6, 19245, 4, 1))]:
    r = runs[key]
    P(f'| {name} | N{cfg[0]} | N{cfg[1]} | {cfg[2]} | {cfg[3]} | {cfg[4]} | **{r["makespan"]}** | {r["p95"]} | {r["messages"]} | {r["nacks"]} |')
P(f'\nBaseline: makespan **{b["makespan"]}** cycles, p95 load-miss latency **{b["p95"]}** cycles '
  f'(over {b["loadMisses"]} loads that sent GetS; issue cycle = cycle the GetS was first sent; if the issue cycle is instead taken as the first cycle the core attempted the load, including eviction retries, p95 = {b["p95first"]}), '
  f'messages **{b["messages"]}**, Nacks **{b["nacks"]}**. Run end cycle {b["endCycle"]}.\n')
P('## Whole configuration space (29,360,128 configurations)\n')
P('**Not every configuration was simulated.** At ~5 ms per simulation per CPU core (4 cores), the full space needs ~41 core-hours (~10 h wall-clock), '
  'far beyond the 2.5 h budget. Method actually used:\n')
P(f'* **Census (exact)**: every one of the 65,536 line maps was simulated for {len(an["census_cells"])} of the 448 (placement, Q, B) cells: '
  'D0=N2/D1=N6 with all 16 (Q,B); D0=N2/D1=N5 with Q=4 (all B); D0=N1/D1=N6 with Q=4 (all B). '
  f'That is {f(an["census_runs"])} configurations.')
P(f'* **Stratified sample**: in each of the other {448 - len(an["census_cells"])} cells, {an["sample_maps_per_noncensus_cell"]:,} line maps drawn without replacement '
  f'(keyed pseudo-random permutation, identical sample size in every cell): {f(an["sample_runs_outside_census"])} configurations.')
P(f'* **Distinct configurations simulated and used: {f(an["distinct_configs_used"])}** ({100 * an["distinct_configs_used"] / 29360128:.2f}% of the space). '
  f'(Sweep samples that fell in census cells, {f(an["sample_runs_inside_census_cells(duplicates)"])} runs, duplicate census runs and are not counted; '
  'plus the handful of baseline/variant/validation runs.)')
P('* Whole-space figures = exact census totals + (65,536 x sample mean) for every sampled cell. Intervals are 95% (1.96 SE, stratified, finite-population corrected) and cover sampling error only. '
  '**These are estimates, not exact counts.**\n')
P('| quantity | value |')
P('|---|---|')
P(f'| Sum of makespan over all configurations | {est(an["sum_makespan"])} |')
P(f'| Mean makespan | ≈ {an["mean_makespan_overall"]:.1f} cycles |')
P(f'| Configurations with makespan < baseline ({b["makespan"]}) | {est(an["count_below_baseline"])} |')
P(f'| Configurations with makespan ≤ 6,000 | {est(an["count_le_6000"])} |')
for q in ('1', '2', '3', '4'):
    P(f'| Q = {q}: makespan < baseline | {est(an["below_baseline_by_Q"][q])} |')
for bb in ('1', '2', '4', '8'):
    P(f'| B = {bb}: makespan < baseline | {est(an["below_baseline_by_B"][bb])} |')
P('')
bf = an['best_found'][0]
pm = sorted(an['mean_makespan_by_placement'].values()); gap_mean = pm[1] - pm[0]
bpk = f'N{bf["D0"]}-N{bf["D1"]}'
gap_best = min(v['makespan'] for k, v in an['best_found_per_placement'].items() if k != bpk) - bf['makespan']
P('## Optimal configuration\n')
P(f'**Best configuration found: D0 on N{bf["D0"]}, D1 on N{bf["D1"]}, line map {bf["map"]}, Q = {bf["Q"]}, B = {bf["B"]}, makespan {bf["makespan"]} cycles** '
  f'({bf["messages"]} messages, {bf["nacks"]} Nacks).\n')
P('Status: this is the exact optimum of the D0=N2/D1=N6 placement (all 1,048,576 of its configurations were simulated) and it beats every one of the other '
  f'{f(an["distinct_configs_used"] - 1048576)} simulated configurations (best of the exhaustively simulated N2-N5 and N1-N6 Q=4 cells: '
  f'{an["best_found_per_placement"]["N2-N5"]["makespan"]} and {an["best_found_per_placement"]["N1-N6"]["makespan"]}). It is **not certified** as the global optimum: '
  f'{100 - 100 * an["distinct_configs_used"] / 29360128:.1f}% of the space was not simulated. The evidence that it is global: N2-N6 has the lowest mean makespan of all 28 placements, '
  f'{gap_mean:.0f} cycles below the next placement, and the best simulated configuration of any other placement is {gap_best} cycles slower.\n')
P('Top configurations found (spec order: makespan, messages, D0, D1, Q, B, map):\n')
P('| rank | D0 | D1 | map | Q | B | makespan | messages |')
P('|---|---|---|---|---|---|---|---|')
for i, c in enumerate(an['best_found'][:10]):
    P(f'| {i + 1} | N{c["D0"]} | N{c["D1"]} | {c["map"]} | {c["Q"]} | {c["B"]} | {c["makespan"]} | {c["messages"]} |')
P('\nBest found per placement:\n')
P('| placement | estimated mean makespan | best found | config of best (Q, B, map) |')
P('|---|---|---|---|')
for k, v in an['mean_makespan_by_placement'].items():
    bp = an['best_found_per_placement'][k]
    P(f'| {k} | {v:.0f} | {bp["makespan"]} | Q={bp["Q"]}, B={bp["B"]}, map={bp["map"]} |')
P('\nMean makespan by Q (over the whole space, estimated): ' + ', '.join(f'Q={q}: {v:.0f}' for q, v in an['mean_makespan_by_Q'].items()))
P('\nMean makespan by B (estimated): ' + ', '.join(f'B={q}: {v:.0f}' for q, v in an['mean_makespan_by_B'].items()))
P('\nMean makespan by (Q,B) (estimated): ' + ', '.join(f'{k}: {v:.0f}' for k, v in an['mean_makespan_by_QB'].items()))
P(f'\nAverage within-cell standard deviation of makespan across line maps: {an["mean_within_cell_sd_over_line_maps"]:.0f} cycles.\n')
vs = an['variance_share_of_makespan_from_sweep_sample']
P(f'Share of makespan variance over the space (uniform stratified sample): placement {100*vs["placement_main_effect"]:.1f}%, Q {100*vs["Q_main_effect"]:.1f}%, '
  f'B {100*vs["B_main_effect"]:.1f}%, all (placement,Q,B) cells together {100*vs["placement_Q_B_cells_together"]:.1f}%, line map within a cell {100*vs["line_map_within_cell(remainder)"]:.1f}%.\n')
P('## Checker (baseline trace)\n')
P('```\n' + chk + '\n```\n')
P('Mutation tests (to show the checker can fail): changing one load value in the trace -> Invariant 2 FAIL; injecting a second cache entering M on a line -> Invariant 1 FAIL. '
  'The checker also passed on traces of 6 other configurations (incl. the best one and Q=1 high-Nack runs).\n')
P('## Reproduction\n')
P('```\ncd outputs\nnode sim.js baseline baseline_trace.txt      # baseline metrics + trace (prints JSON metrics)\n'
  'node sim.js run 0 7 43690 2 2                # variant 1\nnode sim.js run 1 6 19245 2 2                # variant 2\nnode sim.js run 1 6 19245 4 1                # variant 3\n'
  'node sim.js run 2 6 55860 4 1                # best configuration found\npython3 checker.py baseline_trace.txt\n'
  '# census of a placement (worker w of 4):  node census.js 2 6 4:1,4:2,...,1:8 w 4 c26_w$w.csv\n'
  '# stratified sweep (worker w of 4):       node sweep.js w 4 sweep_w$w.csv <stop-epoch-seconds>\n'
  '# combine:  python3 analyze.py 6725 analysis.json --census c*.csv --sweep sweep_w*.csv\n'
  '# render:   python3 report.py analysis.json runs.json checker_output.txt > results.md\n```\n')
P('Raw per-configuration CSVs (census and sample) are in `outputs/data/` (gzipped).\n')
print('\n'.join(out))
