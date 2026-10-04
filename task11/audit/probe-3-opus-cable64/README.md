# Offshore inter-array cable layout - deliverables

Language/runtime: Python 3.11.15 (standard library only), C compiled with gcc 13.3.0 (`-O2`, libc/libm only).
Platform: Linux x86_64, 4 vCPU.

| File | Purpose |
|---|---|
| `common.py` | optimizer-side data loading, rounding, geometry (crossing test), cost evaluation |
| `heur.py` | Esau-Williams greedy + simulated annealing (subtree re-hang / re-root moves) |
| `greedy_sweep.py` | sweep + Prim greedy baselines |
| `sa_from.py` | SA restarts from a given start layout |
| `export_model.py` | writes the B&B model (edges, crossing cliques, prices, UB) |
| `bnb.c` | exact attempt: own dual simplex LP + cuts + branch-and-bound (DFS or best-first) |
| `checker.py` | independent checker (separately coded geometry with exact rationals) |
| `finalize.py` | picks best layout per scenario, writes `layouts/S*.json`, runs checker, exports `models/S*.txt` |
| `greedy_report.py` | greedy baselines -> `evidence/greedy.json`, `layouts/greedy/` |
| `layouts/S*.json` | best layouts found (cable endpoint, type, load, length, cost) |
| `evidence/bnb_S*.log/.out` | lower-bound runs (root LP bound and best-first global bound) |
| `MEMO.md` | engineering memo |

Reproduction (from `work/`):
```
gcc -O2 -march=native -o bnb bnb.c -lm
python3 heur.py S1 6 600000            # EW greedy + SA (repeat for S2..S4); writes ub_S*.json
python3 sa_from.py S2 sweep 5 600000 0 # SA from sweep greedy; S4 was seeded from a B&B dive:
python3 export_model.py S4 9000000 m_S4_open.txt && ./bnb m_S4_open.txt out_S4_open.txt 60
python3 sa_from.py S4 out_S4_open.txt 5 600000 0
python3 finalize.py                    # best layouts + independent check + models
for s in S1 S2 S3 S4; do BEST=1 ./bnb models/$s.txt evidence/bnb_$s.out 720 > evidence/bnb_$s.log; done
python3 greedy_report.py
python3 checker.py layouts/S1.json     # validate any layout
```
SA is randomized (seeded), so reruns with other seeds may give different upper bounds.
