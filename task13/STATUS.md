# Task 13 — L1 POTT misoperation investigation (Electrical Engineering, power-system protection)

Design per the community tips (Playbook 08, section 5): a diagnosis task. Line L1 tripped at
Substation A by POTT for a B-C fault on line L2 6.5 km past Substation B. Relay A behaved
correctly (Z2 + received permissive). Relay B echoed the permissive because its zone 3
reverse did not assert. B's settings are coordinated on paper. The root cause is one step
upstream: B's L1 protection CT core is landed on X1-X5 (2000:5, per the commissioning record
and the nameplate tap chart) instead of the design X2-X4 (1200:5), while relay B's settings
assume 1200:5. B therefore measures impedances 1.667x too large, and its zone 3 reverse
(designed with a 1.5 margin) misses the fault. With the design ratio, the replay shows Z3R
asserting at sample 350, no echo and no trip at A.

Evidence needs files combined: B's recorded currents are 0.6x A's for the same through
current (prefault and fault), and the commissioning record (background) plus CT drawing B
give the landed tap and its ratio.

- Reference: `reference/` (net.py network, waves.py synthesis, relay.py replay,
  build_case.py, gen_data.py, make_docs.py). Bundle: `artifact/L1_event_2026-09-14.zip`.
- Draft prompt: `platform/prompt.md` (291 words).
- Next: early opus-alias blind probe; read its trajectory and harden the shortcuts it used.
