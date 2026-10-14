# TR-21 rubric (v1)

38 criteria; positive weight 111; longest 151 characters.

| # | Weight | Criterion |
|---|---|---|
| 1 | +1 | States that substation TSS-B is out of service at the 07:30 peak. |
| 2 | +1 | States that the TSS-D no-load voltage in force at the 07:30 peak is 850 V (tap +1). |
| 3 | +1 | States that the TSS-C no-load voltage in force at the 07:30 peak is 835 V (tap 0). |
| 4 | +1 | States that route X1 (N9 to N1) is in service at the 07:30 peak. |
| 5 | +4 | Reports the output current of substation TSS-A at the 07:30 peak as 2866 A (accept 2862.6 to 2868.4 A). |
| 6 | +4 | Reports the output current of substation TSS-C at the 07:30 peak as 3747 A (accept 3742.8 to 3750.4 A). |
| 7 | +4 | Reports the output current of substation TSS-D at the 07:30 peak as 3185 A (accept 3181.5 to 3188.0 A). |
| 8 | +4 | Reports the current in route L2 at the 07:30 peak as 176.4 A (accept 175.8 to 176.9 A) flowing from N1 to N2. |
| 9 | +4 | Reports the current in route L3 at the 07:30 peak as 151.1 A (accept 150.5 to 151.6 A) flowing from N3 to N2. |
| 10 | +4 | Reports the current in route M1 at the 07:30 peak as 298.4 A (accept 297.9 to 299.0 A) flowing from N4 to N2. |
| 11 | +4 | Reports the current in route M2 at the 07:30 peak as 1910 A (accept 1907.7 to 1911.6 A) flowing from C to N4. |
| 12 | +4 | Reports the current in route M3 at the 07:30 peak as 1837 A (accept 1835.1 to 1838.8 A) flowing from C to N3. |
| 13 | +4 | Reports the current in route N9R at the 07:30 peak as 729.9 A (accept 729.1 to 730.7 A) flowing from N4 to N9. |
| 14 | +4 | Reports the current in route S1 at the 07:30 peak as 994.0 A (accept 992.9 to 995.0 A) flowing from N1 to N5. |
| 15 | +4 | Reports the current in route S2 at the 07:30 peak as 281.2 A (accept 280.6 to 281.7 A) flowing from N6 to N5. |
| 16 | +4 | Reports the current in route S3 at the 07:30 peak as 625.9 A (accept 625.2 to 626.5 A) flowing from N2 to N6. |
| 17 | +4 | Reports the current in route S4 at the 07:30 peak as 1042 A (accept 1040.7 to 1042.9 A) flowing from N7 to N6. |
| 18 | +4 | Reports the current in route S6 at the 07:30 peak as 537.3 A (accept 536.8 to 537.9 A) flowing from N7 to N3. |
| 19 | +4 | Reports the current in route X1 at the 07:30 peak as 608.4 A (accept 607.7 to 609.0 A) flowing from N1 to N9. |
| 20 | +4 | Reports the pantograph voltage of tram T104 at N1 at the 07:30 peak as 699.3 V (accept 699.18 to 699.39 V). |
| 21 | +4 | Reports the pantograph voltage of tram T109 at N5 at the 07:30 peak as 658.7 V (accept 658.63 to 658.84 V). |
| 22 | +4 | Reports the pantograph voltage of tram T113 at N9 at the 07:30 peak as 665.0 V (accept 664.93 to 665.14 V). |
| 23 | +4 | Reports the pantograph voltage of tram T117 at N3 at the 07:30 peak as 698.5 V (accept 698.44 to 698.65 V). |
| 24 | +4 | Reports the pantograph voltage of tram T122 at N4 at the 07:30 peak as 703.5 V (accept 703.36 to 703.57 V). |
| 25 | +4 | Reports the pantograph voltage of tram T126 at N8 at the 07:30 peak as 591.4 V (accept 591.33 to 591.54 V). |
| 26 | +4 | Reports the pantograph voltage of tram T131 at N7 at the 07:30 peak as 716.2 V (accept 716.14 to 716.35 V). |
| 27 | +4 | Reports the pantograph voltage of tram T140 at B at the 07:30 peak as 682.7 V (accept 682.55 to 682.76 V). |
| 28 | +4 | Reports the total conductor loss at the 07:30 peak as 945.9 kW (accept 944.9 to 946.9 kW). |
| 29 | +3 | Identifies tram T126 at N8 as the only tram below the 600 V minimum pantograph voltage at the 07:30 peak. |
| 30 | +1 | States that no in-service substation rectifier is blocked at the 07:30 peak. |
| 31 | +1 | In the handover memo, the entry for substation TSS-B cites the 05:40 log entry or the 07:10 log entry as the entry that sets its state at 07:30. |
| 32 | +1 | In the handover memo, the entry for the TSS-D tap cites the 06:15 log entry as the entry that sets it at 07:30. |
| 33 | +1 | In the handover memo, the entry for the TSS-C tap cites the 06:55 log entry as the entry that sets it at 07:30. |
| 34 | +1 | In the handover memo, the entry for route X1 cites the 05:20 log entry as the entry that sets its state at 07:30. |
| 35 | +1 | Delivers the source code of the load-flow solver as a file. |
| 36 | +1 | Delivers a results file that lists the reported substation currents, route currents, tram voltages and conductor loss. |
| 37 | +1 | Delivers the handover memo as a file. |
| 38 | -5 | Reports in its results a current, voltage or loss value that its own delivered solver does not output when run (a value typed in or estimated by hand). |
