# FIRE-15: what is left

Written so the task can be finished even if this session stops.

1. Answer key: 56 cloud workers (branches `claude/fire15-gt-s{1..14}q{0..3}`) each push their part files
   to `task15/gt/` on their branch, about 45-60 minutes after 13:00 UTC on 2026-10-09.
2. Run `bash task15/finish.sh` from the repo root. It fetches every branch, copies the 196 part files,
   aggregates them into `task15/reference/aggregate.json`, and writes `task15/platform/rubric.md` and
   `task15/platform/ideal-flow.md` (49 criteria, all <= 301 characters, whole-space items ~70% of weight).
   If it reports missing parts, rerun that worker: `bash task15/proto/gt_run.sh S1 Q` (about 45 min on 4 cores).
3. Check: the optimum in aggregate.json must reproduce with `gcc -O3 -o /tmp/ffast task15/proto/ffast.c &&
   /tmp/ffast one <its seven stations>`; and `python3 task15/proto/fire_ref.py <stations>` must give the same total.
4. Blind probe (opus, 2.5 h, Python/Node only) was launched at 13:05 UTC with the earlier prompt wording;
   grade it against the rubric once it reports (expected: exact baseline/variants/checker, whole-space as
   estimates, so roughly 25-35%).
5. Platform entry: copy-paste prompt.md, rubric.md rows and ideal-flow.md boxes; attach `artifact/fire15_v1.pdf`.
   Domain: Earth & Environmental Sciences; subdomain: wildfire management - initial-attack crew stationing.

## Done (as of 2026-10-09 13:20 UTC)
- Design and model frozen: `design/spec.md` (packet text), `proto/params.py` -> `params.json`/`params.h` (all constants).
- Engines: `proto/fire_ref.py` (literal Python reference, written from the spec) and `proto/ffast.c` (fast C engine,
  also has the `chunk` mode used for the answer key); they agree exactly on 17 plans. `proto/cfire.c` is an old prototype (ignore).
- Packet `artifact/fire15_v1.pdf` (built by `artifact/make_packet.py`): 2 text pages + 4 raster figures, metadata stripped
  (no Info, XMP or ID; no answer values anywhere in it).
- Prompt `platform/prompt.md`: final wording (489 words); asks only for what the rubric grades.
- Rubric and Ideal Flow: `platform/rubric_TEMPLATE.md`, `platform/ideal-flow_TEMPLATE.md` (placeholders for answer-key values);
  `platform/fill_package.py` writes the filled `rubric.md` / `ideal-flow.md` and asserts 49 criteria, each <= 301 characters.
- Answer key launched: 56 cloud workers, script `proto/gt_run.sh`, aggregator `proto/aggregate.py`.
- Design notes and the compute estimate: `STATUS.md`.

## Not done yet
- Collect the answer key and fill the rubric/Ideal Flow (step 2 above).
- Verify the optimum (step 3).
- Grade the blind probe (step 4). If its report never arrives (session ended), skip it: the real platform runs are the test.
  Note the probe saw an earlier prompt that also asked for S9, timber burn time, a wind factor, crew 6 data,
  and a third variant (crews 1 and 7 swapped: 14,354) and a "why the optimal plan wins" memo question.
- Platform entry and screenshot check of every entered field against the files (playbook mistake #81).
- After the real runs: grade the trajectories, record the outcome in `STATUS.md` and the playbook.

## Standing checks from the user (apply before giving anything to the platform)
- The prompt must require tool use and at least one output file (it does: five files).
- No metadata in any artifact (recheck the PDF if it is rebuilt).
- Every rubric criterion <= 301 characters, atomic and self-contained (fill_package.py asserts the length; the table in
  the rubric records atomicity).
- Re-check against the reviewer feedback in playbook 07 (#75, #76): no value outside the legal set, no unstated rule,
  every asked explanation graded, nothing bundled, no undefined metric, no validity-only criteria, a penalty for each
  "only if" rule in the prompt.

Fixed values (already in the rubric): baseline A 1,992 / B 4,240 / C 3,455 / D 4,079, total 13,766;
crew 7 at S6 10,956; all at S6 18,683; 980 spread ignitions in baseline scenario A.
