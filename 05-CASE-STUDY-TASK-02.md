# Task 02 Case Study: From 80–88% to 100/99% to 36/38/41%

## Why this case study matters

The sequence demonstrates both sides of task authoring:

- how a materially stronger architecture can reduce frontier-model scores; and
- how one hidden semantic can turn apparent score success into a fairness risk.

The correct conclusion is not “we found a guaranteed way to fail the model.” It is “we found a stronger task architecture and also discovered the exact validation step needed to keep that architecture honest.”

## Iteration 1 — packet arbiter repair

### Design

The first Task 02 asked the model to repair a compact packet round-robin arbiter, run simulation, produce a waveform/report, and reproduce deterministic values.

### Outcome

Observed scores were approximately 80–88%.

### Why Opus succeeded

- The DUT was small.
- The interface and intended protocol were complete.
- A clean state-machine rewrite was easier than diagnosing each original defect.
- The model could build its own testbench and oracle.
- The deterministic trace made validation straightforward.

### Lesson

Adding report fields or more directed cases does not change a small rewrite task into a frontier task.

## Iteration 2 — Revision B tagged reorder buffer

### Design

Revision B increased the apparent complexity:

- four-entry tagged ROB;
- modulo-8 full tags and low-bit indexing;
- issue, completion, retirement, flush, turnover, and backpressure cases;
- visual protocol card;
- deterministic and randomized testing;
- JSON metrics, waveform, SHA, and verification report.

### Outcome

Two Opus 4.8 runs scored 100% and 99%.

### What the trajectories showed

Both runs:

1. inventoried and enlarged the visual inputs;
2. installed/used an RTL simulator;
3. built an independent Python transaction model;
4. checked all worked-trace points;
5. rewrote the small RTL cleanly;
6. added directed and randomized verification;
7. ran the buggy original as a control;
8. computed outputs and hash;
9. produced all five files.

The single 99% miss was not a technical design failure. The report discussed Panel C and cycle 38 but did not explicitly attribute `head/tail/occupancy = 3/4/1` to Panel C in the exact requested way.

### Lesson

The task remained a small reconstruct-and-rewrite problem. More edge cases, exact tuples, and reporting detail created typing burden, not robust frontier difficulty. The correct response was architectural replacement, not another wording pass.

## Iteration 3 — Revision C DRAM controller characterization and tuning

### Design improvement

Revision C removed the supplied implementation and asked the model to reconstruct a controller from a single visual packet, generate a workload, implement a simulator, sweep a design space, choose a target-qualified configuration, and produce five files.

The packet encoded:

- address mapping;
- bank/row timing;
- read/write mode selection;
- age override;
- refresh;
- same-cycle order;
- bus reservation;
- waveform-derived constants;
- legal knobs and tie-break;
- a 624-request workload.

### The three trajectories

| Trajectory | Score label | Events | Turns | Runtime | Cost | Tool uses |
|---|---:|---:|---:|---:|---:|---:|
| `36.json` | 36% | 379 | 130 | 33.8 min | $9.98 | 123 |
| `38.json` | 38% | 325 | 102 | 55.8 min | $10.32 | 99 |
| `41.json` | 41% | 256 | 83 | 46.1 min | $9.14 | 80 |

All identify the model as `claude-opus-4-8` using Claude Code 2.1.177.

Tool-use counts:

| Trajectory | Bash | Read | Edit | Write | TaskCreate | TaskUpdate |
|---|---:|---:|---:|---:|---:|---:|
| `36.json` | 62 | 38 | 2 | 3 | 7 | 11 |
| `38.json` | 52 | 24 | 3 | 2 | 7 | 11 |
| `41.json` | 40 | 22 | 6 | 2 | 4 | 6 |

These were not shallow failures. Each model conducted a substantial agentic workflow.

## What all three runs got right

They independently agreed on:

- 64-byte line addressing;
- `bank = (line XOR (line >> 2)) & 3`;
- `row = line >> 4`;
- `tRCD/tCL/tRP/tWR = 9/11/10/12`;
- R→W guard 6;
- authoritative W→R guard 11 rather than stale 8;
- refresh interval 384;
- measured `tBURST = 4` from the waveform;
- measured `tRFC = 42`;
- the ordered stages completion → refresh → admission → age → mode → dispatch;
- no fallback to the other operation when the selected operation has no bank-free candidate;
- the full 624-request workload;
- all 272 legal configurations;
- all five requested deliverables.

They also produced the same non-reference outputs:

| Item | Three-run consensus |
|---|---|
| Baseline total cycles | `14008` |
| Baseline read p99 | `253` |
| Recommended configuration | `{Q:8,H:4,B:2,L:96}` |
| Recommended total cycles | `8425` |
| Recommended read p99 | `337` |
| Qualifying configurations | exactly `1` |
| Baseline dispatch SHA-256 | `6207d72875ea31ae7d2bae62bb10de212ef7fc82b03b7e85142dd3f4a5747966` |
| Recommended dispatch SHA-256 | `a6da4ef9ae98d20e750768df05f2db38bea5ad34f10c0c88b98b0ac8060a98d5` |

All three explained the same causal mechanism: with baseline `H=2` and `B=4`, the controller can remain in WRITE mode when fewer than four writes remain, issuing reads mainly through age override. Their recommended design changed all four knobs and found a narrow throughput/tail-latency compromise.

## What the private oracle expected

The author’s Revision C oracle and rubric expected:

- baseline total `9026`;
- recommendation `{Q:10,H:4,B:4,L:128}`;
- recommended total `8429`;
- baseline hash `21f9f02358a121aecaef87c2c3815bf423be1bb842ca7521da2db772e5face52`;
- recommended hash `3e4cd882a3d0eb48c3dad9bcf546fd5b93cefbfba89924c40b7d20c48566d739`.

Those values were internally reproducible between `reference_model.py` and `independent_oracle.py`.

## Root cause of the disagreement

Both private implementations included:

```python
if write_mode and writes_waiting == 0:
    write_mode = False
    writes_in_batch = 0
```

The generated visible packet stated:

- READ→WRITE when writes waiting ≥ H or no reads;
- WRITE→READ when B writes have dispatched and a read waits;
- if the selected operation has no bank-free request, issue nothing and do not fall back;
- mode persists across idle cycles;
- aged dispatch changes neither mode nor B counter.

It did not state a third transition out of WRITE when zero writes are waiting. The three models therefore implemented the two visible transitions and state persistence. Their shared result followed coherently from the packet.

## Why the “independent oracle” did not protect us

It was independently coded but not independently specified. Both author implementations inherited the same intended behavior. They verified code-to-code agreement, not artifact-to-code completeness.

The missing control was a code-to-source reverse audit:

> For every material branch in the oracle, point to the exact prompt or artifact statement that authorizes it.

That one audit would have identified the extra transition before model runs.

## Fairness assessment

The Revision C architecture is legitimately stronger than the ROB repair. The trajectories prove that it demanded sustained multimodal and tool-based work. Nevertheless, the current score outcome is contaminated by an incomplete visible specification. It should not be treated as a clean submission-ready stump solely because the platform shows 36%, 38%, and 41%.

This is exactly the kind of fake-stump risk warned about by the project’s preflight and generous-reading rules: a competent rival answer may be correct under the supplied materials even though it differs from the author’s hidden reference.

## Two honest repair choices

### Choice A — keep the intended private semantics

Add an explicit visible rule such as:

> At the mode-selection stage, if the controller is in WRITE mode and no writes are waiting, it transitions to READ and clears the write-batch counter before selecting the operation.

Then:

1. regenerate the packet;
2. rerun the source-to-code audit;
3. regenerate goldens, sweeps, Ideal Flow, rubric, and entry guide;
4. verify all displayed results;
5. rerun both required models.

The old 36/38/41 trajectories cannot be reused as proof because their input specification changed.

### Choice B — keep the current visible packet semantics

Remove the hidden transition from the reference and update all goldens/rubrics to the three-run consensus. This is semantically fair, but the three models have already solved the core task accurately; their scores would rise sharply. A new difficulty architecture or additional legitimate constraints would likely be needed.

## Lessons to carry forward

1. Below-50 scores are a gate, not a certificate.
2. Three detailed matching rival outputs are diagnostic evidence.
3. Source-to-code reverse tracing is mandatory.
4. Independent code must originate from an independently reconstructed specification.
5. The best architecture from this attempt was reconstruction + simulation + exhaustive search + causal synthesis.
6. Small rewriteable state machines are not recoverable through prompt expansion.
7. Report omissions should not be mistaken for core technical stumps.
8. All numbers, hashes, and checkpoints should be generated into platform-entry text, not manually retyped.
9. Runtime/toolchain validation belongs before platform entry.
10. Never hide a discovered fairness flaw simply because the score target was achieved.

## Evidence paths

- `C:\Users\SAI\Downloads\Telegram Desktop\36.json`
- `C:\Users\SAI\Downloads\Telegram Desktop\38.json`
- `C:\Users\SAI\Downloads\Telegram Desktop\41.json`
- `C:\Users\SAI\Documents\ChatGPT\MR\task 02\revision-b\trajectory-analysis-100-99.md`
- `C:\Users\SAI\Documents\ChatGPT\MR\task 02\revision-c\reference_model.py`
- `C:\Users\SAI\Documents\ChatGPT\MR\task 02\revision-c\independent_oracle.py`
- `C:\Users\SAI\Documents\ChatGPT\MR\task 02\revision-c\make_packet.py`
- `C:\Users\SAI\Documents\ChatGPT\MR\task 02\revision-c\ideal-flow.md`
- `C:\Users\SAI\Documents\ChatGPT\MR\task 02\revision-c\rubric-draft.md`

This case study is intentionally candid. Its value is not just that the scores fell; it is that the trajectories taught us how to distinguish genuine difficulty from a hidden-contract failure.
