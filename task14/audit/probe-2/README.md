# GRID-14 deliverables

Runtime used for every number: **Node.js v22.22.2** (simulator, batch driver) and **Python 3.11.15**
(checker, trace alteration, aggregation). Standard libraries only, offline. Linux x86-64, 4 cores.

| File | What it is |
|---|---|
| `grid14_sim.js` | The step-by-step simulator (network, signals, demand, vehicles, metrics). CLI: `run`, `trace`, `network`. |
| `grid14_explore.js` | Batch driver over the configuration space (stratified sample, exhaustive offset enumeration of one (C, plan, order) stratum, coordinate descent). Uses `grid14_sim.js`. |
| `grid14_checker.py` | Separately coded invariant checker (shares no code with the simulator; re-derives signal timing and movements from the packet). |
| `make_altered_traces.py` | Produces the two corrupted copies of the trace. |
| `grid14_analyze.py` | Aggregates the CSV output of the explorer into `analysis.json`. |
| `grid14_report.py` | Writes `results.md` from `analysis.json`, the baseline/variant runs and the checker output. |
| `reference_check_sim.py` | A second, deliberately simple cell-array implementation of the model in Python, used only to cross-check the JS simulator (identical TTS and end step on every run compared). |
| `progression_analysis.py` | Diagnostic for the memo: green-wave "progression" score versus total TTS over an enumerated group. |
| `variants.jsonl` | Raw simulator output for the baseline and the three variants. |
| `baseline_AM_trace.txt` | Step-by-step trace of the baseline AM run (C 84, plan 1, lead, offsets 0). |
| `altered_trace_red_crossing.txt`, `altered_trace_double_cell.txt` | The two altered copies. |
| `checker_output.txt` | Checker output on the trace and on both altered copies. |
| `analysis.json` | Aggregated exploration statistics. |
| `sim_runs.csv.gz` | Every configuration simulated (index, C, plan, order, offsets, AM, PM, EVENT, total, gridlock). |
| `results.md` | Every requested number. |
| `memo.md` | Engineering memo. |

## Reproduction

```sh
node --version            # v22.22.2
python3 --version         # Python 3.11.15

# baseline and the three variants
node grid14_sim.js run                                           # baseline C=84 plan 1 lead offsets 0
node grid14_sim.js run --offsets 0,21,42,0,21,42,0,21,42         # row offsets 0/21/42 west->east
node grid14_sim.js run --order lag                               # lag
node grid14_sim.js run --C 60                                    # cycle 60
# any configuration: --C <60..120> --plan <1..6> --order lead|lag --offsets o0,...,o8

# trace + checker
node grid14_sim.js trace --scenario AM --out baseline_AM_trace.txt
python3 grid14_checker.py baseline_AM_trace.txt
python3 make_altered_traces.py baseline_AM_trace.txt altered_trace_red_crossing.txt altered_trace_double_cell.txt
python3 grid14_checker.py altered_trace_red_crossing.txt         # exit 1, I2 violated
python3 grid14_checker.py altered_trace_double_cell.txt          # exit 1, I1 violated

# exploration (each line = one of 4 parallel workers, w = 0..3)
mkdir -p runs
node grid14_explore.js sample  --per 1500 --seed 1 --worker w --nworkers 4 --out runs/sample_w.csv
node grid14_explore.js exhaust --C 60 --plan 6 --order lag  --worker w --nworkers 4 --out runs/exhaust_60_6_lag_w.csv
node grid14_explore.js exhaust --C 60 --plan 6 --order lead --worker w --nworkers 4 --out runs/exhaust_60_6_lead_w.csv
node grid14_explore.js descent --starts <comma-separated config indices> --worker w --nworkers 4 --out runs/descent_w.csv
node grid14_explore.js exhaust --C 60 --plan 2 --order lag  --worker w --nworkers 4 --out runs/exhaust_60_2_lag_w.csv
python3 grid14_analyze.py 4052648 'runs/sample_*.csv' 'runs/*.csv' > analysis.json
node grid14_sim.js network > network.txt
python3 grid14_report.py analysis.json variants.jsonl checker_output.txt network.txt > results.md

# independent cross-check of any scenario run with the Python reference model
python3 reference_check_sim.py AM 84 1 lead 0,0,0,0,0,0,0,0,0     # -> (1138089, 4966, 2728) = (TTS, last step, vehicles)
```

Configuration index (used in the CSVs): `index = ((cycleIdx*6 + plan-1)*2 + (lag?1:0)) * 4^9 + sum_j q_j * 4^(8-j)`,
with cycleIdx the position of C in (60, 72, 84, 96, 108, 120) and q_j in {0,1,2,3} the offset of I_j in
units of C/4. Ascending index order is exactly the packet's tie-break order, so "smallest (total, index)"
is the packet's optimum rule.
