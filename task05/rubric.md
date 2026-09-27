# R2-F1 rubric — frozen before local blind calibration

Positive total77; negative trap-8. Criteria are binary. Local normalization is earned positive points minus triggered penalty, divided by77, clamped at zero. This is an explicitly labelled local measure; official source material does not specify a complete platform normalization formula. Accept equivalent correct work. Report a supplemental generous proportional score for incomplete objective profiles/proof coverage; a low binary score alone cannot establish difficulty if substantial correct work is hidden by an incomplete profile. No hidden file/schema/route requirements.

1. **+1** — Executes the delivered offline optimizer with a documented command to generate the submitted case results; equivalent languages and source organization pass.

2. **+1** — Provides the six logical products as accessible files: optimizer, independent verifier, schedules, case matrix/selections, certification/traces/adversarial results, and memo. No particular filenames, schema or physical file count is required.

3. **+1** — Identifies all24 distinct design/campaign cases: D0..D5 crossed with campaign0..3. Extra explanatory records pass when these cases are unambiguous.

4. **+2** — Recovers solid undirected edges {0-3,3-6,3-4,4-7,6-7,7-8,5-8,2-5,1-4}, adding only4-5 for open designs D3/D5. Node=3y+x, P=3,Q=5,K=1; equivalent labels pass with an explicit mapping.

5. **+2** — Generates lots j=0..4 for campaigns s=0..3 with family=(j+s)%2, release=2floor(j/2), Pbase=5+(j*j+2s)%4 and Qbase=4+(3j+s)%5. Equivalent formula notation passes.

6. **+1** — Uses design inputs (F,G,aisle,capital): D0=(2,5,closed,0),D1=(3,5,closed,7),D2=(2,6,closed,9),D3=(2,5,open,6),D4=(3,6,closed,16),D5=(3,6,open,22).

7. **+2** — Reports D0 four-campaign optimum makespan profile as [41, 46, 39, 47] minutes, campaign order0,1,2,3. This is one design profile; separate rows, an equivalent table or another explicit ordering pass. Any attaining schedule passes.

8. **+2** — Reports D1 four-campaign optimum makespan profile as [34, 37, 33, 37] minutes, campaign order0,1,2,3. This is one design profile; separate rows, an equivalent table or another explicit ordering pass. Any attaining schedule passes.

9. **+2** — Reports D2 four-campaign optimum makespan profile as [41, 46, 39, 46] minutes, campaign order0,1,2,3. This is one design profile; separate rows, an equivalent table or another explicit ordering pass. Any attaining schedule passes.

10. **+2** — Reports D3 four-campaign optimum makespan profile as [40, 44, 39, 43] minutes, campaign order0,1,2,3. This is one design profile; separate rows, an equivalent table or another explicit ordering pass. Any attaining schedule passes.

11. **+2** — Reports D4 four-campaign optimum makespan profile as [33, 35, 31, 35] minutes, campaign order0,1,2,3. This is one design profile; separate rows, an equivalent table or another explicit ordering pass. Any attaining schedule passes.

12. **+2** — Reports D5 four-campaign optimum makespan profile as [30, 33, 31, 33] minutes, campaign order0,1,2,3. This is one design profile; separate rows, an equivalent table or another explicit ordering pass. Any attaining schedule passes.

13. **+2** — Reports D0 four-campaign minimum bill at optimum makespan profile as [267, 307, 300, 286] benchmark cost units, campaign order0,1,2,3. This is one design profile; separate rows, an equivalent table or another explicit ordering pass. Any attaining schedule passes.

14. **+2** — Reports D1 four-campaign minimum bill at optimum makespan profile as [255, 289, 251, 294] benchmark cost units, campaign order0,1,2,3. This is one design profile; separate rows, an equivalent table or another explicit ordering pass. Any attaining schedule passes.

15. **+2** — Reports D2 four-campaign minimum bill at optimum makespan profile as [266, 289, 290, 318] benchmark cost units, campaign order0,1,2,3. This is one design profile; separate rows, an equivalent table or another explicit ordering pass. Any attaining schedule passes.

16. **+2** — Reports D3 four-campaign minimum bill at optimum makespan profile as [254, 301, 260, 288] benchmark cost units, campaign order0,1,2,3. This is one design profile; separate rows, an equivalent table or another explicit ordering pass. Any attaining schedule passes.

17. **+2** — Reports D4 four-campaign minimum bill at optimum makespan profile as [264, 284, 249, 289] benchmark cost units, campaign order0,1,2,3. This is one design profile; separate rows, an equivalent table or another explicit ordering pass. Any attaining schedule passes.

18. **+2** — Reports D5 four-campaign minimum bill at optimum makespan profile as [267, 274, 230, 279] benchmark cost units, campaign order0,1,2,3. This is one design profile; separate rows, an equivalent table or another explicit ordering pass. Any attaining schedule passes.

19. **+1** — Resets production state separately for every case and completes operations at boundary t before simultaneous starts/actions occupying [t,t+1); a duration-d operation occupies [t,t+d). Starts use resources released at t, and execution ends at the final cure boundary.

20. **+1** — Assigns each lot in executed preparation once to P or Q after release, with at most one uninterrupted setup-plus-processing operation per machine; the machine frees on completion and prepared output waits in an unlimited buffer.

21. **+1** — Initializes executed machine family memory unset, updates it at preparation start, retains it through idle, and applies setup0 initially/on unchanged family or2 on a change; processing duration is the generated duration for the selected machine.

22. **+1** — Keeps executed fixture holdings at most F; each lot holds one continuously from preparation start through waits, transport and curing, releasing only at cure completion.

23. **+1** — Starts executed robots empty at nodes3 and5 with fixed identities and executes exactly one one-minute wait, adjacent drawn-edge move, pickup or unload action per minute. Pickup/unload/wait remain at the node; empty repositioning is allowed and locations persist.

24. **+1** — Executes pickups taking one prepared untransported lot at its source using an empty robot; cargo capacity is one and duplicate pickup is forbidden. Pickup becomes cargo at t+1; unloading occurs only at K and makes the lot available for curing at t+1. Every lot is conserved through its stages.

25. **+1** — Uses each undirected edge in executed routes at most once per minute, forbidding both swaps and same-direction sharing; boundary node capacity is1 except P/Q/K capacity2. Following into a vacated node is legal.

26. **+1** — Selects at executed oven starts one or two arrived uncured same-family lots while the oven is idle; membership stays fixed for4+family minutes, then all members finish together. Waiting arrivals do not automatically start curing.

27. **+1** — Respects aggregate G in every executed minute including ongoing operations and all new starts/actions: P=2,Q=3,oven=3,robot move/pick/unload=1 each, wait=0; setup draws full machine power and other idle resources draw zero.

28. **+1** — Computes makespan as final cure boundary and bill as sum over t=0..M-1 of total minute power times 1+(floor(t/7)%3). This checks arithmetic on delivered schedules independently of whether they are optimal.

29. **+2** — Delivers and executes a separately runnable verifier that independently reconstructs constraints and checks; shared material with the optimizer is limited to immutable instance data. Equivalent complete-certificate checkers pass; a wrapper importing optimizer transitions, feasibility or pruning does not establish independence.

30. **+10** — Independently establishes the minimum makespan for all24 cases through executed complete search excluding earlier completion or a checked complete mathematical certificate, with justified state merging/pruning. Feasible schedules, labels or hashes alone do not prove optimality; equivalent complete proof methods pass.

31. **+10** — Independently establishes the minimum bill at the minimum makespan for all24 cases through executed complete cost search or a checked complete mathematical certificate. This grades complete independent evidence, not another copy of the numerical result; equivalent complete proof methods pass.

32. **+2** — Produces chronological traces from the delivered uninterrupted schedules with starts/completions, both robot positions/cargo, active preparation/oven work, fixtures, minute power and cumulative bill; final time/bill reconcile with case records. Equivalent nesting, compression and simultaneous-event ordering pass.

33. **+2** — Applies the lexicographic key (max of four makespans,sum of four bills+3capital,capital,ID) to all six designs and selects its minimum. Grade selection arithmetic/population on delivered metrics without charging an upstream metric error again; with correct metrics the result is D5,(33,1116,22,D5).

34. **+2** — Minimizes the lexicographic key (max of four makespans,sum of four bills+3capital,capital,ID) within capital<=9, including equality and hence D0,D1,D2,D3. Grade population/selection on delivered metrics without recharging upstream metric errors; with correct metrics the result is D1,(37,1110,7,D1).

35. **+1** — Compares D0 with both selected designs using the delivered executed objectives. Accept a comparison that is correct relative to delivered results despite an upstream optimization error; do not require additional design pairs.

36. **+2** — Explains at least one actual routing, batching or resource interaction using identifiable event times from delivered production schedules, connecting it to the engineering recommendation. Accept any accurate supported interaction; no particular reference route or unrequested comparison is mandatory.

37. **+1** — Explains that distance-only travel omits shared undirected-edge and interior-node occupancy interactions, so its bound alone cannot certify a feasible joint robot schedule or achieved completion time.

38. **+1** — Executes a copied-production-schedule test changing its earliest preparation start to-1; verifier rejects the copy and accepts the preserved original. Equivalent test harnesses pass.

39. **+1** — Executes a copied-production-route mutation causing an edge or interior-node conflict; verifier rejects it, identifies the first invalid action minute or clearly mapped boundary, and preserves the accepted original. Either collision type suffices.

40. **+1** — Records optimizer/verifier reproduction commands and actual tool versions, sufficient to regenerate the delivered files in the declared offline environment.

41. **-8** — Embeds precomputed case-result values or schedule tables as substitutes for executing the optimizer that produces reported results. Immutable input constants and computed search caches do not trigger this active-behavior trap; omission alone does not trigger it.
