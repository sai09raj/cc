# COHERE-12 deliverables

Language/runtime: CPython 3.11.15 (GCC 13.3.0), Linux. Only the standard library is used (`sys`, `json`, `re`).

| file | content |
|---|---|
| `sim.py` | cycle-accurate simulator |
| `checker.py` | independent trace checker (it does not import sim.py) |
| `sweep.csv` | 64 configurations: placement,Q,B,makespan,p95_load_miss_latency,messages,nacks |
| `baseline_trace.txt` | trace of P1, Q=2, B=2 |
| `memo.md` | design memo |

## Reproduce

```
cd outputs
python3 -I sim.py baseline --trace baseline_trace.txt   # baseline summary (JSON) + trace
python3 -I sim.py sweep sweep.csv                       # 64-row CSV, Fastest/Leanest, sums
python3 -I sim.py run P2 4 1                            # any single configuration
python3 -I checker.py baseline_trace.txt --selftest     # invariants (+ fault-injection self test)
```

## Trace format

The trace has one event per line: `<cycle> <event>`, in execution order. The events are:

* `ST Ci Lx old->new`: a cache line state change (`->I` means the way was freed).
* `LD Ci Lx val=v hit|miss`: a load completion, with the value it returned.
* `STORE Ci Lx val=v`: a store write.
* `MSG serial type src->dst ...`: a message was created.
* `REFUSE`, `NACK`, `DIRREQ`, `DIR`, `FINISH`: refusals, Nack handling, directory events and core finish.
* `END`: the last line.

## Interpretation choices

1. Load-miss latency is measured from the cycle the load's GetS was first sent (way allocation) to the load completion. Resends do not reset it.
2. Eviction is implemented literally. While the set is full and has an S/M way, each retry of the miss sends another PutS/PutM, even when the other way of the set is already waiting for its PutAck.
3. A line is "present" when any way holds it in any state, including transient states.
4. The checker tests the M invariant after every state change, which is stricter than once per cycle. "Most recent store" means the latest STORE in trace order (by cycle, then by the packet's controller order within a cycle). Hits are checked as well as misses.
