#!/usr/bin/env python3
"""Write results.md from executed-program outputs (standard library only).

Usage: grid14_report.py analysis.json variants.jsonl checker_output.txt network.txt > results.md
"""
import json, sys

an = json.load(open(sys.argv[1]))
var = [json.loads(l) for l in open(sys.argv[2]) if l.strip()]
chk = open(sys.argv[3]).read()
net = [l.split() for l in open(sys.argv[4]) if l.strip()]
SPACE = 18874368
out = []
P = out.append


def f(x):
    return f'{int(round(x)):,}'


def est(e, unit=''):
    s = f"≈ {f(e['estimate'])}{unit} (95 % CI {f(e['ci95'][0])} – {f(e['ci95'][1])})"
    if e.get('zero_in_sample_upper95') is not None:
        s = f"0 in the sample (95 % upper bound ≈ {f(e['zero_in_sample_upper95'])})"
    return s


P('# GRID-14 results')
P('')
P('All numbers come from programs I ran: `grid14_sim.js` / `grid14_explore.js` (Node.js v22.22.2), and `grid14_checker.py` / `grid14_analyze.py` / `grid14_report.py` (Python 3.11.15). Reproduction commands are in `README.md`.')
P('')
P('## 1. Values read from the figures')
P('')
P('Cell length 7.5 m. Cells = metres / 7.5; every length gives a whole number of cells.')
P('')
P('**Street blocks (Figure 1; each block is two links, one per direction, of equal length)**')
P('')
P('| Block | Length (m) | Cells |')
P('|---|---:|---:|')
blocks = [('I0–I1', 240), ('I1–I2', 195), ('I3–I4', 165), ('I4–I5', 270), ('I6–I7', 210), ('I7–I8', 180),
          ('I0–I3', 225), ('I3–I6', 150), ('I1–I4', 180), ('I4–I7', 255), ('I2–I5', 202.5), ('I5–I8', 157.5)]
for n, m in blocks:
    P(f'| {n} | {m:g} | {int(m / 7.5)} |')
P('')
P('**Inbound boundary links (Figure 1, labelled "in")**')
P('')
P('| Terminal | Feeds | Approach side | Length (m) | Cells |')
P('|---|---|---|---:|---:|')
inb = [(0, 'I0', 'N', 285), (1, 'I1', 'N', 330), (2, 'I2', 'N', 270), (3, 'I2', 'E', 307.5), (4, 'I5', 'E', 262.5),
       (5, 'I8', 'E', 322.5), (6, 'I6', 'S', 292.5), (7, 'I7', 'S', 277.5), (8, 'I8', 'S', 337.5), (9, 'I0', 'W', 315),
       (10, 'I3', 'W', 300), (11, 'I6', 'W', 270)]
for k, j, s, m in inb:
    P(f'| T{k} | {j} | {s} | {m:g} | {int(m / 7.5)} |')
P('')
P('Outbound boundary links: 10 cells each (Section 2). The simulator built exactly these lengths; `node grid14_sim.js network` prints them:')
P('')
P('```')
for l in net:
    P(' '.join(l))
P('```')
P('')
P('**Demand (Figure 2, veh/h)**')
P('')
P('| Scenario | T0 | T1 | T2 | T3 | T4 | T5 | T6 | T7 | T8 | T9 | T10 | T11 |')
P('|---|' + '---:|' * 12)
D = {'AM': [208, 266, 182, 234, 195, 254, 221, 176, 273, 247, 202, 228],
     'PM': [221, 176, 273, 247, 202, 228, 208, 266, 182, 234, 195, 254],
     'EVENT': [208, 266, 182, 234, 312, 254, 221, 176, 273, 395, 202, 228]}
for s, v in D.items():
    P(f'| {s} | ' + ' | '.join(map(str, v)) + ' |')
P('')
P('**Turning shares (Figure 3)**: arrivals from north or south: left 20 %, through 65 %, right 15 %. Arrivals from west or east: left 10 %, through 75 %, right 15 %. Left and right are taken from the driver\'s point of view; the figure shows a southbound arrival with left going east and right going west, and an eastbound arrival with left going north and right going south.')
P('')
P('**Phases (Figure 3)**: A = N and S approaches, through and right; B = N and S approaches, left; C = E and W approaches, through and right; D = E and W approaches, left. Each phase is protected, and each green is followed by a 2 s all-red. Sequence from local time 0: **lead A, B, C, D**; **lag B, A, D, C**.')
P('')
P('**Green times (Figure 4, A/B/C/D in seconds)**; in every row, greens + 4 × 2 s all-red = C:')
P('')
P('| C | Plan 1 | Plan 2 | Plan 3 | Plan 4 | Plan 5 | Plan 6 |')
P('|---|---|---|---|---|---|---|')
G = {60: ['18/8/18/8', '22/6/18/6', '16/7/22/7', '20/9/16/7', '16/7/20/9', '21/5/21/5'],
     72: ['22/10/22/10', '27/8/22/7', '20/9/27/8', '25/11/20/8', '20/8/25/11', '26/6/26/6'],
     84: ['26/12/26/12', '32/9/26/9', '23/11/32/10', '29/14/23/10', '23/11/29/13', '31/7/31/7'],
     96: ['30/14/30/14', '37/11/30/10', '27/12/37/12', '34/15/27/12', '27/12/34/15', '36/8/36/8'],
     108: ['34/16/34/16', '42/12/34/12', '30/14/42/14', '38/18/30/14', '30/14/38/18', '40/10/40/10'],
     120: ['39/17/39/17', '48/13/38/13', '34/15/48/15', '43/20/34/15', '34/15/43/20', '45/11/45/11']}
for C, row in G.items():
    P(f'| {C} | ' + ' | '.join(row) + ' |')
P('')
base = var[0]
P('## 2. Baseline (C = 84 s, plan 1, lead, all offsets 0)')
P('')
P('| Scenario | TTS (veh·s) | Vehicles | Run ended at step |')
P('|---|---:|---:|---:|')
nveh = {'AM': 2728, 'PM': 2740, 'EVENT': 2978}
for i, s in enumerate(['AM', 'PM', 'EVENT']):
    P(f"| {s} | {base[s]:,} | {nveh[s]:,} | {base['end'][i]} |")
P(f"| **Total** | **{base['total']:,}** | | |")
P('')
P(f"The baseline does not gridlock.")
P('')
P('## 3. Variants of the baseline (only the named knob changed)')
P('')
P('| Variant | AM | PM | EVENT | Total TTS | Change from baseline |')
P('|---|---:|---:|---:|---:|---:|')
names = ['Baseline', 'Offsets 0, 21, 42 s from west to east in each row (I0, I3, I6 = 0; I1, I4, I7 = 21; I2, I5, I8 = 42)',
         'Lag instead of lead', 'Cycle 60 s instead of 84 s (plan 1, lead, offsets 0)']
for n, v in zip(names, var):
    P(f"| {n} | {v['AM']:,} | {v['PM']:,} | {v['EVENT']:,} | **{v['total']:,}** | {100 * (v['total'] - base['total']) / base['total']:+.1f} % |")
P('')
P('None of the variants gridlocks.')
P('')
P('## 4. Whole configuration space (18,874,368 configurations)')
P('')
nsim = an['distinct_configurations_simulated']
P(f"**Configurations actually simulated: {nsim:,} distinct configurations ({100 * nsim / SPACE:.2f} % of the space), each on all three scenarios.** "
  'Not all 18,874,368 were simulated. At about 25 ms per configuration on the 4 available cores, a full census needs about 33 hours, against a 2.5-hour limit. '
  'The whole-space figures below are therefore **estimates, not exact counts**. They come from a stratified uniform random sample: '
  f"{an['sample_size']:,} configurations, {an['sample_per_stratum'][0]:,} drawn uniformly (with replacement) from the 4^9 offset vectors of each of the 72 equal-sized (cycle, plan, order) groups. "
  'The groups enumerated completely, ' + ', '.join(f'({a} s, plan {b}, {c})' for a, b, c in an['exhaustively_enumerated_strata']) +
  ', enter the estimates with their exact values. Intervals are 95 % normal-approximation confidence intervals for the stratified estimator; counts are clipped to the size of their group.')
P('')
P('| Item | Result |')
P('|---|---|')
P(f"| Sum of total TTS over all configurations | {est(an['sum_total_tts'])} veh·s, i.e. ≈ {an['sum_total_tts']['estimate']:.4e} |")
P(f"| Mean total TTS per configuration | ≈ {f(an['sum_total_tts']['estimate'] / SPACE)} veh·s |")
P(f"| Number with total TTS below the baseline (< {base['total']:,}) | {est(an['count_below_baseline'])} |")
P(f"| Number that gridlock | {est(an['count_gridlock'])} |")
P('')
P('**Configurations below the baseline, by cycle length** (3,145,728 configurations per cycle)')
P('')
P('| Cycle (s) | Configurations below baseline | Gridlocking configurations |')
P('|---|---|---|')
for C in ['60', '72', '84', '96', '108', '120']:
    P(f"| {C} | {est(an['below_baseline_by_cycle'][C])} | {est(an['gridlock_by_cycle'][C])} |")
P('')
P('**Configurations below the baseline, by timing plan** (3,145,728 configurations per plan)')
P('')
P('| Plan | Configurations below baseline |')
P('|---|---|')
for p in ['1', '2', '3', '4', '5', '6']:
    P(f"| {p} | {est(an['below_baseline_by_plan'][p])} |")
P('')
P('Exact counts among the configurations actually simulated (this is not a whole-space figure): '
  f"{an['simulated_below_baseline_exact']:,} below the baseline, {an['simulated_gridlock_exact']:,} gridlock, and total TTS summed over them = {an['simulated_sum_total_exact']:,} veh·s.")
P('')
if an.get('exhausted_strata_detail'):
    P('**Groups enumerated completely (exact over all 262,144 offset vectors)**')
    P('')
    P('| Group | Sum of total TTS | Below baseline | Gridlock | Min | Mean | Max |')
    P('|---|---:|---:|---:|---:|---:|---:|')
    for k, d in sorted(an['exhausted_strata_detail'].items()):
        P(f"| {k} | {d['sum_total']:,} | {d['below_baseline']:,} | {d['gridlock']:,} | {d['min']:,} | {f(d['mean'])} | {d['max']:,} |")
    P('')
P('## 5. Optimum')
P('')
b = an['best_found']
P(f"**Best configuration found (not proven optimal, because only {nsim:,} of 18,874,368 configurations were simulated):**")
P('')
P(f"* C = {b['C']} s, plan {b['plan']}, {b['order']}, offsets I0..I8 = {', '.join(str(o) for o in b['offsets'])} s")
P(f"* AM {b['AM']:,} + PM {b['PM']:,} + EVENT {b['EVENT']:,} = **total TTS {b['total']:,} veh·s** (no gridlock), {100 * (b['total'] - base['total']) / base['total']:+.1f} % against the baseline")
P('')
P('Search used: (i) the stratified sample of all 72 groups; (ii) complete enumeration of all 4^9 offset vectors in the groups listed above, the three groups with the lowest sampled mean total TTS; (iii) coordinate descent over the offsets (one intersection at a time, all 4 values, repeated until no change), started from the 4 best sampled configurations of each of the other 22 groups with C = 60 or 72 s. Within the completely enumerated groups, the configuration above is exact under the packet\'s tie-break. No search in any other group found a better total.')
P('')
P('Fifteen best configurations simulated (ties broken as in the packet):')
P('')
P('| # | C | Plan | Order | Offsets I0..I8 | AM | PM | EVENT | Total |')
P('|---|---|---|---|---|---:|---:|---:|---:|')
for i, r in enumerate(an['top15_found']):
    P(f"| {i + 1} | {r['C']} | {r['plan']} | {r['order']} | {','.join(map(str, r['offsets']))} | {r['AM']:,} | {r['PM']:,} | {r['EVENT']:,} | {r['total']:,} |")
P('')
P('## 6. Sensitivity summaries (from the stratified sample)')
P('')
vs = an['variance_share']
P(f"Share of the variance of total TTS: cycle {100 * vs['cycle_main']:.1f} %, order {100 * vs['order_main']:.1f} %, plan {100 * vs['plan_main']:.2f} %, cycle × plan × order jointly {100 * vs['cycle_plan_order_joint']:.1f} %, offsets (within group) {100 * vs['offsets_within_stratum']:.1f} %.")
P('')
P('| Cycle | Mean total TTS | Mean lead | Mean lag | Gridlock rate lead | Gridlock rate lag | Lowest total in sample |')
P('|---|---:|---:|---:|---:|---:|---:|')
for C in ['60', '72', '84', '96', '108', '120']:
    m = an['mean_total_by_cycle'][C]
    P(f"| {C} | {f(m['mean'])} | {f(an['mean_total_by_cycle_order'][C + '-lead']['mean'])} | {f(an['mean_total_by_cycle_order'][C + '-lag']['mean'])} | {100 * an['gridlock_rate_by_cycle_order'][C + '-lead']:.2f} % | {100 * an['gridlock_rate_by_cycle_order'][C + '-lag']:.2f} % | {m['min']:,} |")
P('')
P('| Plan | Mean total TTS | Order | Mean total TTS |')
P('|---|---:|---|---:|')
for i, p in enumerate(['1', '2', '3', '4', '5', '6']):
    o = ['lead', 'lag'][i] if i < 2 else ''
    P(f"| {p} | {f(an['mean_total_by_plan'][p]['mean'])} | {o} | {f(an['mean_total_by_order'][o]['mean']) if o else ''} |")
P('')
P('## 7. Interpretations where the specification left room')
P('')
for t in [
    'Each of the four greens, including the last one in the sequence, is followed by its own 2 s all-red. Figure 4 confirms this: greens + 8 s = C in every row.',
    'Lag is read from Figure 3 as B, A, D, C, so each street gets its left phase before its through/right phase.',
    'Right turns are served only in the through/right phase of their approach (A or C). There is no right turn on red and no permissive left.',
    'A vehicle advances its own generator once on entering its inbound boundary link (cell 0, after leaving the terminal queue) and once on entering each street block. Creation does not draw, and entering an outbound boundary link does not draw. Routes are therefore independent of the signal configuration.',
    'Departure step e is the step in which the vehicle moves out of the last cell of its outbound link. A vehicle created at step g can enter cell 0 during the same step g.',
    '"Empty at the start of the step" is taken literally: a vehicle cannot move into a cell vacated in the same step, so standing queues discharge at one vehicle every 2 s.',
    'The run-end test is applied at the end of each step t >= 3599. Gridlock means a run reached the end of step 7199 with vehicles still waiting or in the network. Every such vehicle (including any still in a terminal queue) contributes 7200 - g.',
    'Simulator shortcut: if, with vehicles in the network, nothing moves for C consecutive steps and no vehicle can enter (t >= 3600, or every inbound cell 0 is occupied), the state is frozen forever. The run is then closed as if continued to step 7199, which gives identical TTS. I confirmed this against the reference model, which has no shortcut.',
    'Variant "offsets 0, 21 and 42 s for the intersections of each row from west to east": I0, I3, I6 = 0; I1, I4, I7 = 21; I2, I5, I8 = 42. All other settings stay at the baseline.',
    'The whole-space items cannot be reported exactly without simulating all 18,874,368 configurations, which did not fit in the time available. They are reported as estimates with confidence intervals.',
]:
    P('* ' + t)
P('')
P('## 8. Checker results')
P('')
P('`grid14_checker.py` is a separate Python program that shares no code with the simulator. It reads `baseline_AM_trace.txt`, which has a POS record of every vehicle\'s link and cell at the end of every step, plus NEW, EXIT and WAIT records. It re-derives signal states, approach sides and movements from the packet itself. A stop-line crossing is any vehicle that is in the last cell of a link ending at an intersection at the end of step t−1 and in cell 0 of a different link at the end of step t.')
P('')
P('```')
P(chk.strip())
P('```')
print('\n'.join(out))
