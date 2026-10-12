# KINGSMEAD-11 v1 pre-entry audit

- Tool use + 3 output files required by the prompt. PASS
- PDF metadata: no Info/ID/XMP; no answer values in text (make_packet asserts). PASS
- Criteria <= 301 chars (longest 173); atomic; self-contained; explicit accept ranges on every numeric criterion. PASS
- Blind solve (no key access) matched every value to 6+ s.f. (taps 9/4, A 11.041476, B 11.186921, all bus voltages, all route currents and directions, T1 4.559959 MVA / -1.539505 Mvar, T2 9.519662 MVA, C1 1207.48 kvar, PV 821.71 kvar, max section F4-1 185 after J4 at 66.651 %).
- Fixed from the blind solve: infeed metering point (now stated: at P33; key 11.43 MW, 5.523 Mvar, losses 188.2 kW = probe's P33 values); transformer impedance stated independent of tap; sheet numbering 1-4; 06:30 log wording (no "split the busbar" claim).
- Simulated single errors (rest right): NOP-1 open 20, T1 AUTO 14, C1 out 20, PV 4000 22, F2-3 opened 40, repair added in series 50, F4-2 type 45, IC-1 length 53, repair ignored 64.
