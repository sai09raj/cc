# R3 production witnesses

Extracted mechanically from `reference/kilnworks_sim.py`'s own uninterrupted
per-design trace (the same execution that produces the graded makespan/bill). All
indices are **zero-based** minutes. A record at minute `t` reflects the state/actions
decided for `[t, t+1)`; `robot_pos`/`robot_cargo` shown are the values **at the start**
of that minute (before that minute's chosen actions take effect at `t+1`), matching
`design/semantic-contract.md` S09. Any physically valid, equally-conforming schedule
passes; these are witnesses of mechanism, not a hidden route tie-break.

## W1 — node-4 fault engagement (design D0)

| t | Robot 0 action | Robot 0 pos | Robot 1 action | Robot 1 pos | power |
|---:|---|---:|---|---:|---:|
| 6 | move->4 | 3 | wait(home) | 5 | 4 |
| 7 | wait(offline) | 4 | pickup(1) | 5 | 1 |
| 12 | wait(offline) | 4 | wait(blocked) | 7 | 0 |
| 13 | move->1 | 4 | move->4 | 7 | 2 |

Robot 0 first reaches node 4 during minute 6 (arriving at the start of minute 7) and
is frozen there through minute 12 (6 minutes total, S07). Robot 1 is blocked from
using node 4 (capacity 1) while Robot 0 occupies it, then legally follows into node 4
the same minute (13) Robot 0 finally vacates it toward node 1 — the same-minute
vacate-and-enter case in S05.

## W2 — cross-campaign interleaving (design D0)

At `t=35` (the minute campaign 1's first lots release, S02), campaign 0's lots
`{2, 3, 4}` are still open (cure-completion times `36, 55, 42` respectively) —
production evidence that campaigns 0 and 1 share the plant's resources
simultaneously, not four independent resets.

## W3 — persistent machine setup memory across a campaign boundary (design D4)

| Machine | Lot | start_t | release_abs | duration | Interpretation |
|---|---:|---:|---:|---:|---|
| Q | gidx 1 (s=0,j=1, family 1) | 0 | 0 | 7 | campaign-0 job, sets Q's family memory to 1 |
| Q | gidx 6 (s=1,j=1, family 0) | 36 | 35 | 10 | campaign-1's first Q job |

`Qbase(1,1) = 4 + (3*1+1) mod 5 = 8`. The delivered duration is `10 = 8 + 2`, i.e.
setup `2` was charged because Q's remembered family (`1`, from campaign 0's lot 1)
differs from this job's family (`0`) — proof the memory was **not** reset at the
campaign boundary. A per-campaign-reset implementation would treat this as Q's first
job ever for campaign 1 and charge setup `0` (duration `8`), which is mechanically
distinguishable and is exactly what `reference/mutant_per_campaign_reset.py` produces.

## W4 — cross-campaign oven batch (design D1)

Batch at `t=50`: members `{gidx 3 (s=0,j=3), gidx 7 (s=1,j=2)}`, campaigns `{0, 1}`.
Both share `family = 1` (`family(3,0) = (3+0) mod 2 = 1`; `family(2,1) = (2+1) mod 2
= 1`); membership is fixed the instant the batch starts (S06) and both cure together
for `4 + 1 = 5` minutes — a same-family pairing that only exists because a
campaign-0 and a campaign-1 lot were simultaneously waiting at the oven.

## Cross-file reconciliation

- Each design's full trace has exactly `makespan` records; its last cumulative bill
  equals the design's reported bill; all 20 lots reach `done` and `fixture_held`
  reaches `0` at the final boundary.
- `reference/kilnworks_verify.py` independently checks structural feasibility
  (fixture ceiling, node/edge capacity, non-negative/post-release starts) on every
  design's delivered trace and rejects both required adversarial mutations
  (negative preparation start; forced route/node collision) while accepting the
  unmodified original.
- A second, independently-built implementation (`audit/independent-reconstruction.md`)
  reproduces every one of these witnesses' underlying numbers exactly, including W3's
  duration-`10` boundary-crossing job and W4's mixed-campaign batch.
