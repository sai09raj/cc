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

## W5 — machine-Q maintenance freeze, now recurring (design D1)

S13 is a **recurring** interval (hardened in R3c): `Q_cumulative` resets to 0 on
every trigger, and the mechanism can fire any number of times in one design's run
-- not just once. Design D1 fires it twice:

- **Trigger 1** at `t=44` (lot global index 1's 7 minutes + lot global index 7's 6
  minutes: `7+6=13 >= 10`, crossing on the second job). Freeze `[45,57]`, resumes
  `58`, cumulative tracking restarts from 0.
- **Trigger 2** at `t=118` (three more completed jobs -- global indices 8, 11, 19 --
  accumulate `4+4+4=12 >= 10`, crossing on the third). Freeze `[119,131]`, resumes
  `132`.

Without the mechanism (`mutant_disable_maintenance`), Q's schedule after `t=114`
assigns global index **16** to its last slot (`start=133`); with the mechanism
active, the second freeze pushes that same slot to global index **18** instead
(`start=136`) -- the freeze doesn't just delay a job, it changes *which* lot Q
ends up processing, because the delay lets a different lot become the cheaper
choice by the time Q reopens:

| | Q's final job |
|---|---|
| Mechanism active (reference) | global index 18, start `t=136` |
| Mechanism disabled (mutant) | global index 16, start `t=133` |

A model that implements only a single, non-recurring freeze (matching R3b's old
behavior) reproduces trigger 1 correctly but silently drops trigger 2 -- passing
half of criteria 14-16's intent while failing D1's golden value, full-trace hash,
and this witness.

## Trace-integrity hashes (criteria 38-43)

Each design's complete minute-by-minute trace, canonically serialized as
`DESIGN:<name>` followed by one `t,power,cum_bill` line per minute, hashed with
SHA-256 (`kilnworks_sim.canonical_trace_serialization` +
`hashlib.sha256(...).hexdigest()`). The full 64-hex-character digest is the
canonical/grading-material record below; **the rubric criteria (38-43) use only
the first 16 hex characters**, truncated deliberately to keep manual platform
entry safe from transcription errors while remaining overwhelmingly sensitive
to any single divergent minute (64 bits of entropy — an accidental match
between two genuinely different traces is astronomically unlikely across this
six-design, non-adversarial setting). Enter only the bolded 16-character
prefix into the rubric field, not the full hash.

| Design | Full SHA-256 | Rubric value (first 16 chars) |
|---|---|---|
| D0 | `955957f0e6a9788d034f615b29341368fae4d42a5fa575a788379d3a6f1e3212` | **`955957f0e6a9788d`** |
| D1 | `9eafc0820bda70a94009a8f3dacc0d119bad748a64518b681880cc2764b7afbe` | **`9eafc0820bda70a9`** |
| D2 | `7d104044363f36b297277d2a09d0a419c8c634dae3a11d2566046f790d600f66` | **`7d104044363f36b2`** |
| D3 | `b1086cb4f38396f41d51ab74450d46f982a205dd1bd981f48bfd27e5f1fc97e8` | **`b1086cb4f38396f4`** |
| D4 | `c9e705daef1ddcf7d204c5c720152cba158c6f233176ab1954c645cbffe4bdac` | **`c9e705daef1ddcf7`** |
| D5 | `6a1d99ca7302e560d10088487821a15129f006d3379117b686acca636f93248a` | **`6a1d99ca7302e560`** |

D0's hash is unchanged from R3b -- its Q workload (two jobs, `7+5=12`) crosses the
new threshold (10) exactly once, on its very last Q job, so there is no remaining
work left for a freeze to ever block; the trigger fires but has zero causal effect
on D0's trace (confirmed: `mutant_disable_maintenance` and
`mutant_maintenance_inclusive` both still reproduce D0 exactly). This is now
correctly described as structural: D0 *does* trigger the mechanism once, it just
never has a second job available to delay. All five other hashes changed.

Every one of these values was copied directly from executed Python output,
never hand-typed.

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
