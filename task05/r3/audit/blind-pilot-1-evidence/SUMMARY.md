# SUMMARY — KILNWORKS Retrofit Evaluation

Full detail and evidence: `MEMO.md` (engineering memo), `EXTRACTION_NOTES.md`
(PDF vector-graphics proof), and everything under `certification/`,
`traces/`, `traces_v2/`. One command reproduces all of it: `bash reproduce.sh`.

## Graph / rule interpretation

Aisle graph recovered by parsing the packet's vector PDF paths (not
eyeballing): 9 shared edges `0-3,3-6,3-4,4-7,6-7,7-8,5-8,2-5,1-4`, plus
`4-5` only in the open-aisle layout (dash array proves it: `[1.2 2.4]`
ghost/non-edge in closed, `[6.4 4.8]` real edge in open). K (node 1) has
degree 1 in both layouts — every delivery passes through junction node 4
(capacity 1). Docking bays P(3)/Q(5)/K(1) hold 2 robots each. The one
graphically-only datum — Robot 0's forced-offline duration at its first
node-4 arrival — was read off the shaded rectangle's coordinates against the
axis gridlines: spans data-units [3,9] exactly = **6 minutes**
(`EXTRACTION_NOTES.md` §2). All other rules (campaign/lot formulas, setup
memory, assignment policy, robot priority cascade, oven pairing timer, power
admission order, tariff formula) were transcribed directly from the printed
text in Sections C-F.

## Six designs' results (primary simulator, verifier-confirmed identical)

| Design | F | G | Aisle | Capital | Makespan | Bill |
|---|---|---|---|---|---|---|
| D0 | 2 | 5 | closed | 0  | 187 | 1331 |
| D1 | 3 | 5 | closed | 7  | 165 | 1336 |
| D2 | 2 | 6 | closed | 9  | 187 | 1447 |
| D3 | 2 | 5 | open   | 6  | 185 | 1401 |
| D4 | 3 | 6 | closed | 16 | 152 | 1362 |
| D5 | 3 | 6 | open   | 22 | 142 | 1290 |

## Investment selections (key = (makespan asc, bill asc))

- **Unrestricted: D5**, key **(142, 1290)** — dominates all six designs on
  both metrics simultaneously, no tie-break needed.
- **Capital <= 9: D1**, key **(165, 1336)**, from eligible pool
  {D0, D1, D2, D3} — strictly lowest makespan in the pool, no tie-break
  needed.

## Verifier agreement

Independently-coded verifier (`sim/verifier_sim.py`: flat dict world state,
Floyd-Warshall shortest paths, generic power-budget walk, robot rules
re-transcribed from the packet text — not derived from the primary's code)
reproduces **byte-identical** minute-by-minute traces to the primary
simulator for all six designs (1,018 total simulated minutes, every logged
field, 0 mismatches — `certification/trace_diff_report.txt`) and identical
per-lot timing for all 120 lot-records (20 lots x 6 designs, 0 mismatches).
A third, standalone feasibility-certificate checker
(`sim/certificate_checker.py`), which reads only the emitted trace files and
independently re-checks every hard constraint (release timing, fixture
ceiling — cross-validated two ways, power budget, edge/node capacity,
tariff/bill arithmetic, cure duration, completeness), certifies **0
violations** on both implementations' traces for all six designs.

## Adversarial experiments

Both run against D0's and D5's genuine certified traces
(`sim/adversarial_experiments.py`; full output in
`certification/adversarial_results_D0.json` / `..._D5.json`):

- **Negative-start**: (a) a machine start moved earlier than its lot's
  release — caught (`NEGATIVE-START/EARLY-START: lot5 machine_start at
  t=32 < release 35`); (b) a machine start moved to a literally negative
  minute (t=-5) — caught by two independent checks at once.
- **Route-collision**: (a) both robots forced onto junction node 4
  (capacity 1) in the same minute — caught (`ROUTE-COLLISION/NODE-CAPACITY
  at t=93: node 4 holds 2 robots (cap 1)`); (b) both robots forced onto the
  same edge (3,4) in the same minute — caught by both the node- and
  edge-capacity rules simultaneously.

All 4 injected corruptions, on both designs tested: **caught** (`"ALL
ADVERSARIAL INJECTIONS CAUGHT": true`).

## Causal explanation (grounded in the delivered traces)

D0's bottleneck is the fixture ceiling F, not the power ceiling G:
`fixture_held` sits at the F=2 cap for 94.1% of D0's run, and D0 shows
**zero** robot actions ever refused for lack of power. Proof by
construction: D2 (F=2, G=6, otherwise = D0) reproduces D0's exact 187-minute
makespan with 0 power refusals — the extra power headroom is simply never
spent — while its bill is *higher* (1447 vs 1331) because the freed-up power
lets starts land in costlier tariff windows without buying any schedule
length. Relaxing F to 3 (D1) is what actually matters: fixture-binding drops
to 84.8%, power refusals jump from 0 to 31 (G finally starts to bind), and
oven pairing goes from 0/20 to 5/15 batches paired. Opening the aisle alone
(D3) shortens Q's path to K (distance 4->2) but only trims 2 minutes off
makespan and *raises* the bill by 70, because F=2 still caps concurrency at
97.3% binding — the shorter path mainly makes Robot 1 cycle through the
single-capacity node-4 junction *more often* (node-capacity contention
triples, 3->9), not less. D5 (F=3 **and** open aisle) is where the shorter
path finally pays off, because F is no longer the strangling constraint —
hence D5, not D3 or D4 alone, is the pointwise-best design. Full numeric
backing: `certification/design_diagnostics.json`, MEMO.md section 6.

**Why independent per-campaign resets would be wrong**
(`certification/campaign_reset_experiment.json`): resetting machine memory /
fixtures / robot positions / oven state and rebasing each campaign's clock
to 0 *overstates* makespan by 29-36 minutes per design (it throws away the
cross-campaign pipeline overlap and machine-memory carryover the continuous
run actually exploits) while *understating* the bill by 63-166 (each reset
campaign illegitimately re-enters the cheapest tariff window at its own
fresh t=0, which a single real plant clock can never do four times). The two
errors run in opposite directions on the two reported metrics, so no
correction factor fixes it — the campaigns must share one clock and one
resource pool because that is what the plant actually has.

**What a distance-only relaxation loses**
(`certification/distance_only_relaxation.json`): keeping only graph
distance and discarding F, G, node/edge capacity, the forced-offline
disruption, and the oven pairing wait produces a lower bound that is nearly
flat across all six designs (121-122 minutes) — it is almost blind to F, G,
and the aisle retrofit, the exact three levers the packet asks to evaluate —
while the real makespans range 142-187. The 15-35% gap to reality is
capacity-driven (it shrinks exactly where F=3 relieves the real bottleneck),
confirming that distance alone cannot even rank the six designs correctly,
let alone size the schedule.

## Work directory

`/tmp/kilnworks-blind-test/work/` — see `MEMO.md` section 10 for the full
deliverables index (simulator/verifier source, full traces, case matrix,
certification evidence, extraction proof, this summary, and the memo).
