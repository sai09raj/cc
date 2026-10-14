You are the traction control engineer on the Hartsdown Tramway at the 07:30 morning peak. The attached tr21_v1.pdf (data sheet, control log, and a drawn route plan; the network topology and every section's conductor type and length are given only on the drawing) is the complete specification. Determine the supply state the log leaves at 07:30 and compute the steady state DC load flow for the 07:30 snapshot by writing and running your own network solver, following the data sheet's model and conventions. Report every value to 4 significant figures.

1. State which substations are in service at 07:30, the no load voltages of TSS-C and TSS-D in force, and whether route X1 is in service.

2. Report the output current of substations TSS-A, TSS-C, TSS-D, and the current and its direction (from which node to which node) in routes L2, L3, M1, M2, M3, N9R, S1, S2, S3, S4, S6, X1.

3. Report the pantograph voltage of trams T104, T109, T113, T117, T122, T126, T131, T140, and the total conductor loss.

4. Identify every tram below the minimum pantograph voltage, and state whether any in-service substation rectifier is blocked.

5. Write a handover memo listing the state of TSS-B, the TSS-C and TSS-D taps and route X1 that your solution uses, each with the log entry that sets it.

Deliver as files: the solver source, a results file with every value above, and the memo. Base every number on your own executed program.
