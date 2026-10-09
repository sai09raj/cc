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

Fixed values (already in the rubric): baseline A 1,992 / B 4,240 / C 3,455 / D 4,079, total 13,766;
crew 7 at S6 10,956; all at S6 18,683; 980 spread ignitions in baseline scenario A.
