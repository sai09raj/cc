You are the network operations engineer for the Fenwick Hill water supply zone. The attached wd22_v1.pdf is the complete specification: a data sheet, a drawn pipe plan (the network topology and every pipe section's type and length are given only on this drawing), and a demand pattern bar chart (the hourly demand multipliers are given only on this chart). Write and run your own extended-period simulation of the 24 h day, following the data sheet's hydraulic model, time stepping and control rules exactly.

1. List every pump start and stop event of the day with its time.

2. Report the tank level at every full hour from 01:00 to 24:00, and the minimum tank level of the day with the time it occurs.

3. Report the total pump energy and the total energy cost for the day.

4. Report the lowest junction pressure head of the day with its junction and step start time, and list every junction and step below the minimum pressure head.

5. For each candidate P-1 start level in the operations review, report the daily energy cost and the minimum tank level, state which candidates let the tank fall below the reserve, and recommend a start level using the data sheet's rule.

6. Write an operations note for the operations manager giving your recommendation and the low pressure finding.

Report tank levels in m to 3 decimal places, pressure heads to 0.01 m, energy to 4 significant figures and costs to 0.01 GBP. Deliver as files: the simulation source, a results file with every value above, and the operations note. Base every number on your own executed program.
