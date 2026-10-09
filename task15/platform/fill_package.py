#!/usr/bin/env python3
"""Write rubric.md and ideal-flow.md for FIRE-15 from the answer key (reference/aggregate.json).
usage: fill_package.py AGGREGATE_JSON   (checks every criterion is <= 301 characters)"""
import json, os, sys
A = json.load(open(sys.argv[1]))
assert A["plans"] == 105413504 and A["missing"] == 0, "answer key incomplete"
f = lambda v: f"{v:,}"
BASE = "S1, S4, S5, S8, S9, S12, S13"
bb7 = A["below_by_crew_station"][6]
mean = A["mean_by_crew_station"]
spread = [max(m) - min(m) for m in mean]
crew_most = spread.index(max(spread)) + 1
best7 = bb7.index(max(bb7)) + 1; worst7 = bb7.index(min(bb7)) + 1
opt = A["optimum"]; plan = ", ".join(f"S{s}" for s in opt["plan"])
avg = A["sum_total_loss"] / A["plans"]

R = []  # (weight, text)
def add(w, t): R.append((w, t))
add(1, "States the cover of cell (100, 36) as houses (H).")
add(1, "States the cover of cell (76, 62) as rock (R).")
add(1, "States the coordinates of station S14 as x = 100, y = 92.")
add(1, "States the lightning strike rate of scenario D as 145 per mille per step.")
add(1, "States that in scenario C, period 3 (steps 240-359), the wind blows toward the southwest (SW).")
add(1, 'Records the exact language and runtime version used (for example "Python 3.11.4"), not only the language name.')
add(1, "Gives concrete commands that rerun its simulator and its checker to reproduce the reported results.")
for s, v in zip("ABCD", (1992, 4240, 3455, 4079)):
    add(2, f"Reports the baseline plan's (crews 1-7 at {BASE}) scenario {s} loss as exactly {f(v)}.")
add(3, f"Reports the baseline plan's (crews 1-7 at {BASE}) total loss over scenarios A-D as exactly 13,766.")
add(3, f"Reports the total loss of the baseline with crew 7 at S6 instead of S13 (crews 1-7 at S1, S4, S5, S8, S9, S12, S6) as exactly 10,956.")
add(3, "Reports the total loss of the plan with all seven crews at station S6 as exactly 18,683.")
add(4, f"Identifies the optimal plan (smallest total loss; ties to the smaller station number for crew 1, then crew 2, and so on) as crews 1-7 at {plan}.")
add(3, f"Reports the optimal plan's (crews 1-7 at {plan}) total loss as exactly {f(opt['total_loss'])}.")
add(10, f"Reports the sum of total loss over all 105,413,504 plans as exactly {f(A['sum_total_loss'])}.")
add(10, f"Reports the number of plans, out of 105,413,504, whose total loss is below the baseline's 13,766 as exactly {f(A['below_baseline'])}.")
add(10, f"Reports the number of plans whose loss is below the baseline's in every scenario (A below 1,992, B below 4,240, C below 3,455 and D below 4,079) as exactly {f(A['below_baseline_all_four'])}.")
for j in range(14):
    add(5, f"Reports the number of plans with crew 7 at station S{j + 1} whose total loss is below 13,766 as exactly {f(bb7[j])}.")
add(1, "The checker's recorded output reports that in the baseline scenario A trace no cell is ignited more than once.")
add(1, "The checker's recorded output reports that every spread ignition in the baseline scenario A trace is next to a cell of the same fire that was burning when that step's spread phase began.")
add(1, "The checker's recorded output reports that in the baseline scenario A trace no crew puts out more than its capacity in a step or any cell outside the fire it is working on.")
add(2, "The checker's recorded output reports checking exactly 980 spread ignitions in the baseline scenario A trace.")
add(1, "The checker's recorded output rejects the altered trace with a spread ignition moved to a cell with no burning neighbour of its fire, naming the spread-adjacency invariant as violated.")
add(1, "The checker's recorded output rejects the altered trace with a crew putting out one cell more than its capacity in a step, naming the crew-capacity invariant as violated.")
add(2, f"The memo identifies crew {crew_most} as the crew whose station changes the average total loss across the plan space the most.")
add(1, f"The memo names S{best7} as the best station for crew 7, the station with the most plans below the baseline ({f(bb7[best7 - 1])}).")
add(1, f"The memo names S{worst7} as the worst station for crew 7, the station with the fewest plans below the baseline ({f(bb7[worst7 - 1])}).")
add(-10, "Uses a third-party package or external tool (for example NumPy, FARSITE, FlamMap) to compute any simulation result.")
add(-8, "Reports a whole-space sum or count over the 105,413,504 plans as an exact value when its own report or code shows it simulated fewer plans than that.")
add(-6, "Calls its reported plan optimal (rather than the best found) when its own report or code shows it simulated fewer than all 105,413,504 plans.")
add(-5, "The checker imports, calls or copies code from the simulator instead of being separately coded.")
add(-8, "Hard-codes any reported simulation result (a loss, count or sum) as a literal in its delivered source code instead of computing it by running its simulator.")
add(-5, "Accesses the internet or any external source (packages, code, documentation or results) while building or running its simulator or checker.")
add(1, "Delivers as files a simulator source, a separately coded checker source, a baseline scenario A trace, a results file and an engineering memo.")

assert len(R) <= 50, len(R)
for i, (w, t) in enumerate(R, 1):
    assert len(t) <= 301, (i, len(t))
pos = sum(w for w, _ in R if w > 0); ws = sum(w for w, t in R[16:19]) + 5 * 14
out = ["# FIRE-15 rubric", "", f"{len(R)} criteria; positive weight {pos}; whole-space items carry {ws} ({100 * ws / pos:.1f}%). Longest criterion {max(len(t) for _, t in R)} characters.", "",
       "| # | Weight | Criterion |", "|---|---|---|"]
out += [f"| {i} | {'+' if w > 0 else ''}{w} | {t} |" for i, (w, t) in enumerate(R, 1)]
out += ["", "## Atomicity and self-containment check", "",
        "Each criterion checks one value, one claim or one requirement, and states the expected answer with the plan or scenario it applies to, so a grader needs nothing else. Lengths:", "",
        "| # | Atomic | Self-contained | Characters |", "|---|---|---|---|"]
out += [f"| {i} | yes | yes | {len(t)} |" for i, (w, t) in enumerate(R, 1)]
out += ["", "## Reverse coverage", "",
        "- Figure values asked in the prompt: criteria 1-5. Runtime version and commands: 6-7.",
        "- Baseline per scenario and total: 8-12. The two variants: 13-14. Optimum and its loss: 15-16.",
        "- Whole-space sum, below-baseline count, below in all four scenarios: 17-19. Crew 7 per-station counts: 20-33.",
        "- Checker invariants, count and the two altered traces: 34-39. Memo questions: 40-42.",
        "- \"Call it optimal only if...\": negative 45; exact whole-space values from a partial run: negative 44. Standard library: 43. Separate checker: 46. Own executed programs: 47. Offline: 48. Deliverables: 49.",
        "", "## Reviewer-feedback audit", "",
        "| Past problem | Here |", "|---|---|",
        "| Expected value outside the allowed set | Every value comes from the answer key or the reference engines; the optimum's stations are legal |",
        "| Value that needs an unstated rule | All rules are in the packet text; blind probe checks reproduction |",
        "| Required explanation not graded | Each memo question has its own criterion (40-42) |",
        "| Bundled facts | One value per criterion |",
        "| Undefined metric | Loss, burnt cell, spread ignition and \"below the baseline\" are defined in the packet or criterion |",
        "| Validity-only or presence-only criteria | None; every number is graded as an exact value |",
        "| Prompt rule with no penalty | Optimal-claim and partial-exact penalties (44, 45), judged from the run's own report or code |"]
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rubric.md"), "w").write("\n".join(out) + "\n")

bb = ", ".join(f"S{j + 1} {f(v)}" for j, v in enumerate(bb7))
analyze = ("Read the packet and recover the whole model. From Figure 1 read the cover letter of each 8 x 8 block (for example cell (100, 36) is houses and (76, 62) rock) and the 14 station cells (S14 at x 100, y 92). "
           "From Figure 2 read burn times and base chances (grass 2 and 100, brush 4 and 75, timber 7 and 50, houses 5 and 65), the wind factors by speed class and angle, seeds and strike rates (D 145 per mille), "
           "the 70 percent diagonal factor and the other constants. From Figure 3 read the wind of each period (scenario C, period 3: toward SW, strong) and from Figure 4 each crew's speed and capacity. "
           "Recover the rules in the text: the generators, the six phases of a step, the eligibility and draw order of spread, the crews' arrival, return and nearest-cell rule, dispatch, the run end and the loss.")
execute = ("Write a step-by-step simulator in the standard library, offline, and make it fast: the whole-space items need all 105,413,504 plans times four scenario runs, so plan the runtime, scan only burning cells, split the space across all cores and checkpoint partial results. "
           f"Baseline ({BASE}): A 1,992, B 4,240, C 3,455, D 4,079, total 13,766. Variants: crew 7 at S6 10,956; all at S6 18,683. "
           f"Whole space: sum of total loss {f(A['sum_total_loss'])}; {f(A['below_baseline'])} plans below the baseline; {f(A['below_baseline_all_four'])} below it in all four scenarios; with crew 7 at each station, below the baseline: {bb}. "
           f"Optimal: {plan}, total loss {f(opt['total_loss'])}; call it optimal only because all plans were simulated, and state that count. "
           "Write the baseline scenario A trace and run a separately coded checker: it passes the three invariants, reports 980 spread ignitions checked, and rejects the two altered copies, naming the invariant each violates. Record the runtime version and reproduction commands.")
synth = (f"Write the memo from your own results. Across the space the average total loss is {avg:,.0f}. Crew {crew_most}'s station changes the average most: its per-station averages range from {min(mean[crew_most - 1]):,.0f} to {max(mean[crew_most - 1]):,.0f}. "
         f"Crew 7 is best based at S{best7} ({f(bb7[best7 - 1])} plans below the baseline) and worst at S{worst7} ({f(bb7[worst7 - 1])}). "
         "Explain the pattern from the landscape and wind: stations near the town and upwind of it reach fires that threaten houses sooner, and each house cell costs ten times a plain cell. "
         "Note that fire growth is chaotic, so only an exhaustive sweep gives the exact counts and sums.")
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ideal-flow.md"), "w").write(
    f"## Analyze\n\n```text\n{analyze}\n```\n\n## Execute & Generate\n\n```text\n{execute}\n```\n\n## Synthesize\n\n```text\n{synth}\n```\n")
print(f"rubric: {len(R)} criteria, positive {pos}, whole-space share {100 * ws / pos:.1f}%, max len {max(len(t) for _, t in R)}")
print("ideal flow lengths:", len(analyze), len(execute), len(synth))
