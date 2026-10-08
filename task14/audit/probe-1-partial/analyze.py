#!/usr/bin/env python3
"""Aggregate the exploration CSVs written by explore.js into whole-space estimates and the best
configuration found (Python 3 standard library only).

usage: python3 analyze.py <baseline_total> <sample_csv>... --search <search_csv>...

The stratified random sample (explore.js sample) is the only input used for whole-space estimates;
search CSVs are biased towards good configurations and are used only for the best configuration and
for the count of distinct configurations simulated.
"""
import json
import math
import sys
from collections import defaultdict

CYC = [60, 72, 84, 96, 108, 120]
N_H = 4 ** 9          # configurations per (C, plan, order) stratum
N_ALL = 72 * N_H


def read(paths):
    rows = []
    for p in paths:
        with open(p) as f:
            for line in f:
                q = line.strip().split(',')
                if len(q) != 17:
                    continue  # tolerate a partially written last line
                C, plan, order = int(q[0]), int(q[1]), q[2]
                ks = tuple(int(x) for x in q[3:12])
                AM, PM, EV, tot, g = (int(x) for x in q[12:17])
                assert AM + PM + EV == tot
                rows.append((C, plan, order, ks, AM, PM, EV, tot, g))
    return rows


def key_order(r):
    C, plan, order, ks = r[0], r[1], r[2], r[3]
    return (r[7], C, plan, 0 if order == 'lead' else 1, ks)


def main():
    args = sys.argv[1:]
    base = int(args[0])
    i = args.index('--search') if '--search' in args else len(args)
    sample = read(args[1:i])
    search = read(args[i + 1:])
    # ---- stratified estimates (each stratum has N_H configurations)
    strata = defaultdict(list)
    for r in sample:
        strata[(r[0], r[1], r[2])].append(r)
    assert len(strata) == 72, len(strata)
    est = {}
    for h, rs in strata.items():
        n = len(rs)
        tot = [r[7] for r in rs]
        below = [1 if r[7] < base else 0 for r in rs]
        grid = [r[8] for r in rs]
        def mv(x):
            m = sum(x) / n
            v = sum((a - m) ** 2 for a in x) / (n - 1) if n > 1 else 0.0
            return m, v
        est[h] = {'n': n, 'tot': mv(tot), 'below': mv(below), 'grid': mv(grid),
                  'nbelow': sum(below), 'ngrid': sum(grid),
                  'AM': sum(r[4] for r in rs) / n, 'PM': sum(r[5] for r in rs) / n, 'EVENT': sum(r[6] for r in rs) / n,
                  'min': min(tot), 'max': max(tot)}

    def agg(sel, field):
        """population total over the selected strata and its standard error"""
        s, var = 0.0, 0.0
        for h in sel:
            m, v = est[h][field]
            s += N_H * m
            var += N_H ** 2 * v / est[h]['n']
        return s, math.sqrt(var)

    def zero_one_note(sel, field, cnt):
        # strata where every sampled configuration had the same 0/1 outcome: the plug-in SE is 0; give
        # the 95% one-sided bound on the unseen fraction (1 - 0.05**(1/n)) times stratum size
        extra = 0.0
        for h in sel:
            n = est[h]['n']
            k = est[h][cnt]
            if k == 0 or k == n:
                extra += N_H * (1 - 0.05 ** (1 / n))
        return extra

    allh = list(est)
    out = {'n_sample': len(sample), 'per_stratum_n_min': min(e['n'] for e in est.values()),
           'per_stratum_n_max': max(e['n'] for e in est.values())}
    s, se = agg(allh, 'tot')
    out['sum_total_TTS'] = (s, se)
    for field, cnt in (('below', 'nbelow'), ('grid', 'ngrid')):
        s, se = agg(allh, field)
        out[f'count_{field}'] = (s, se, zero_one_note(allh, field, cnt))
    out['by_cycle'] = {}
    for C in CYC:
        sel = [h for h in allh if h[0] == C]
        s, se = agg(sel, 'below')
        sm, sem = agg(sel, 'tot')
        g, gse = agg(sel, 'grid')
        out['by_cycle'][C] = {'below': (s, se, zero_one_note(sel, 'below', 'nbelow')), 'mean_total': sm / (12 * N_H),
                              'mean_total_se': sem / (12 * N_H), 'grid': (g, gse),
                              'nsample': sum(est[h]['n'] for h in sel),
                              'nbelow_sample': sum(est[h]['nbelow'] for h in sel)}
    out['by_plan'] = {}
    for p in range(1, 7):
        sel = [h for h in allh if h[1] == p]
        s, se = agg(sel, 'below')
        sm, sem = agg(sel, 'tot')
        out['by_plan'][p] = {'below': (s, se, zero_one_note(sel, 'below', 'nbelow')), 'mean_total': sm / (12 * N_H),
                             'mean_total_se': sem / (12 * N_H), 'nsample': sum(est[h]['n'] for h in sel),
                             'nbelow_sample': sum(est[h]['nbelow'] for h in sel)}
    out['by_order'] = {}
    for o in ('lead', 'lag'):
        sel = [h for h in allh if h[2] == o]
        sm, sem = agg(sel, 'tot')
        s, se = agg(sel, 'below')
        g, gse = agg(sel, 'grid')
        out['by_order'][o] = {'mean_total': sm / (36 * N_H), 'mean_total_se': sem / (36 * N_H), 'below': (s, se), 'grid': (g, gse)}
    out['by_cycle_order'] = {}
    for C in CYC:
        for o in ('lead', 'lag'):
            sel = [h for h in allh if h[0] == C and h[2] == o]
            sm, _ = agg(sel, 'tot')
            g, _ = agg(sel, 'grid')
            out['by_cycle_order'][f'{C}/{o}'] = {'mean_total': sm / (6 * N_H), 'grid_frac': g / (6 * N_H)}
    # ---- variance decomposition of total TTS over the whole space (from stratum means/variances)
    grand = sum(est[h]['tot'][0] for h in allh) / 72
    total_var = sum(est[h]['tot'][1] + (est[h]['tot'][0] - grand) ** 2 for h in allh) / 72
    within = sum(est[h]['tot'][1] for h in allh) / 72
    def main_effect(idx, levels):
        v = 0.0
        for lv in levels:
            sel = [h for h in allh if h[idx] == lv]
            m = sum(est[h]['tot'][0] for h in sel) / len(sel)
            v += (m - grand) ** 2 / len(levels)
        return v
    vc, vp, vo = main_effect(0, CYC), main_effect(1, range(1, 7)), main_effect(2, ('lead', 'lag'))
    between = total_var - within
    out['variance_shares'] = {'cycle': vc / total_var, 'plan': vp / total_var, 'order': vo / total_var,
                              'interactions_C_plan_order': (between - vc - vp - vo) / total_var,
                              'offsets_within_stratum': within / total_var}
    # within-C=60 decomposition (where the optimum lives)
    sel60 = [h for h in allh if h[0] == 60]
    g60 = sum(est[h]['tot'][0] for h in sel60) / 12
    tv60 = sum(est[h]['tot'][1] + (est[h]['tot'][0] - g60) ** 2 for h in sel60) / 12
    w60 = sum(est[h]['tot'][1] for h in sel60) / 12
    out['variance_shares_C60'] = {'between_plan_order': (tv60 - w60) / tv60, 'offsets_within': w60 / tv60}
    out['strata'] = {f'{h[0]}/{h[1]}/{h[2]}': {'n': e['n'], 'mean_total': e['tot'][0], 'sd_total': math.sqrt(e['tot'][1]),
                     'frac_below': e['below'][0], 'frac_grid': e['grid'][0], 'min': e['min'], 'max': e['max'],
                     'mean_AM': e['AM'], 'mean_PM': e['PM'], 'mean_EVENT': e['EVENT']}
                     for h, e in sorted(est.items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][2] != 'lead'))}
    # ---- best configuration found and distinct configurations simulated
    allrows = sample + search
    uniq = {}
    for r in allrows:
        uniq.setdefault((r[0], r[1], r[2], r[3]), r)
    best = min(uniq.values(), key=key_order)
    out['distinct_configs_simulated'] = len(uniq)
    out['rows_total'] = len(allrows)
    out['best'] = {'C': best[0], 'plan': best[1], 'order': best[2], 'k': list(best[3]),
                   'offsets_s': [k * best[0] // 4 for k in best[3]], 'AM': best[4], 'PM': best[5], 'EVENT': best[6],
                   'total': best[7], 'gridlock': best[8]}
    top = sorted(uniq.values(), key=key_order)[:10]
    out['top10'] = [{'C': r[0], 'plan': r[1], 'order': r[2], 'offsets_s': [k * r[0] // 4 for k in r[3]], 'total': r[7]} for r in top]
    best_by_stratum = {}
    for r in uniq.values():
        h = f'{r[0]}/{r[1]}/{r[2]}'
        if h not in best_by_stratum or key_order(r) < key_order(best_by_stratum[h]):
            best_by_stratum[h] = r
    out['best_by_stratum'] = {h: {'offsets_s': [k * r[0] // 4 for k in r[3]], 'total': r[7]}
                              for h, r in sorted(best_by_stratum.items(), key=lambda kv: kv[1][7])}
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
