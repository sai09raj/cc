"""Write canonical TENURE-11 outputs to reference/goldens/ (sweep, selections, baseline log)."""
import csv
import hashlib
import json
import os
import tenure_engine as E

BUDGET = 220000
CEILING = 2400
BASELINE = (24576, 8192, 2, 0)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "goldens")


def selections(rows):
    feas = {c: r for c, r in rows.items() if not r["oom"]}
    cost = min(feas, key=lambda c: (feas[c]["pause_total"], feas[c]["pause_max"], c))
    under = [c for c in feas if feas[c]["pause_total"] <= BUDGET]
    lat = min(under, key=lambda c: (feas[c]["pause_max"], feas[c]["pause_total"], c))
    fit = [c for c in feas if feas[c]["pause_max"] <= CEILING]
    foot = min(fit, key=lambda c: (c[0] + 2 * c[1], feas[c]["pause_total"], c))
    return {"cost_optimal": cost, "latency_optimal_under_budget": lat,
            "footprint_optimal_under_ceiling": foot,
            "n_feasible": len(feas), "n_under_budget": len(under), "n_under_ceiling": len(fit)}


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = E.sweep()
    fields = ["eden", "surv", "tenure", "pretenure", "oom", "oom_op", "minor", "major", "copied",
              "promoted", "pretenured", "pause_total", "pause_max", "old_peak"]
    with open(os.path.join(OUT, "sweep.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(fields)
        for c in E.CONFIGS:
            r = rows[c]
            w.writerow(list(c) + [r[k] for k in fields[4:]])
    sel = selections(rows)
    h, oom_op = E.run(*BASELINE)
    text = E.gclog_text(h)
    with open(os.path.join(OUT, "baseline_gclog.txt"), "w", newline="\n") as f:
        f.write(text)
    feas = [r for r in rows.values() if not r["oom"]]
    summary = {
        "budget": BUDGET, "ceiling": CEILING, "baseline": BASELINE,
        "selections": {k: (list(v) if isinstance(v, tuple) else v) for k, v in sel.items()},
        "selected_rows": {k: rows[sel[k]] for k in ("cost_optimal", "latency_optimal_under_budget",
                                                       "footprint_optimal_under_ceiling")},
        "baseline_metrics": E.metrics(h, oom_op),
        "baseline_events": len(h.log),
        "baseline_hash16": hashlib.sha256(text.encode()).hexdigest()[:16],
        "aggregates": {
            "oom_configs": sum(r["oom"] for r in rows.values()),
            "sum_pause_total_feasible": sum(r["pause_total"] for r in feas),
            "sum_major_feasible": sum(r["major"] for r in feas),
            "sum_copied_feasible": sum(r["copied"] for r in feas),
            "sum_promoted_feasible": sum(r["promoted"] for r in feas),
        },
    }
    with open(os.path.join(OUT, "summary.json"), "w") as f:
        json.dump(summary, f, indent=1, default=list)
    print(json.dumps(summary, indent=1, default=list))


if __name__ == "__main__":
    main()
