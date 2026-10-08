"""TASK 13: write the text/data files of the incident bundle (COMTRADE records, event reports, settings, logs)."""
import datetime as dt, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import case2 as cs  # noqa: E402

OUT = os.path.join(HERE, "..", "artifact", "bundle2")
T0 = dt.datetime(2026, 9, 14, 14, 22, 7, 345000)   # time of sample 0 (both relays GPS-synchronized)


def ts(k):
    return T0 + dt.timedelta(microseconds=round(k * 1e6 / cs.FS))


def fmt_cfg_time(t):
    return t.strftime("%d/%m/%Y,%H:%M:%S.") + f"{t.microsecond:06d}"


def fmt_ser(t):
    return t.strftime("%H:%M:%S.") + f"{t.microsecond // 1000:03d}" + f"{(t.microsecond % 1000) // 100:01d}"


def write_comtrade(name, station, dev, q, dig_names, digs, ct_primary):
    n = len(q["V"][0])
    an = [("VA", "A", "V", q["V"][0], cs.QV, 2000, 1), ("VB", "B", "V", q["V"][1], cs.QV, 2000, 1),
          ("VC", "C", "V", q["V"][2], cs.QV, 2000, 1), ("IA", "A", "A", q["I"][0], cs.QI, ct_primary, 5),
          ("IB", "B", "A", q["I"][1], cs.QI, ct_primary, 5), ("IC", "C", "A", q["I"][2], cs.QI, ct_primary, 5)]
    lines = [f"{station},{dev},1999", f"{len(an) + len(dig_names)},{len(an)}A,{len(dig_names)}D"]
    for i, (cid, ph, uu, data, mult, pri, sec) in enumerate(an, 1):
        lines.append(f"{i},{cid},{ph},,{uu},{mult},0,0,{min(data)},{max(data)},{pri},{sec},S")
    for j, d in enumerate(dig_names, 1):
        lines.append(f"{j},{d},,,0")
    lines += ["60", "1", f"{int(cs.FS)},{n}", fmt_cfg_time(ts(0)), fmt_cfg_time(ts(cs.K_FAULT)), "ASCII", "1"]
    open(os.path.join(OUT, name + ".cfg"), "w", newline="\r\n").write("\n".join(lines) + "\n")
    rows = []
    for k in range(n):
        vals = [str(ch[k]) for ch in q["V"]] + [str(ch[k]) for ch in q["I"]]
        dv = [str(digs[k][d]) for d in dig_names]
        rows.append(",".join([str(k + 1), str(round(k * 1e6 / cs.FS))] + vals + dv))
    open(os.path.join(OUT, name + ".dat"), "w", newline="\r\n").write("\n".join(rows) + "\n")


def transitions(d, names):
    ev = []
    prev = {x: 0 for x in names}
    for k, row in enumerate(d):
        for x in names:
            if row[x] != prev[x]:
                ev.append((k, x, row[x]))
                prev[x] = row[x]
    return ev



def main():
    os.makedirs(OUT, exist_ok=True)
    c = cs.build()
    q, dA, dB, d2b, d2c, opens = c["q"], c["dA"], c["dB"], c["d2b"], c["d2c"], c["opens"]
    st = lambda k, br: 0 if (opens[br] is not None and k >= opens[br]) else 1
    digA = [dict(Z1=r["Z1"], Z2=r["Z2"], KEY=r["KEY"], RX=r["RX"], TRIP=r["TRIP"], **{"52A": st(k, "L1")}) for k, r in enumerate(dA)]
    digB = [dict(Z1=r["Z1"], Z2=r["Z2"], Z3R=r["Z3R"], RX=r["RX"], ECHO=r["ECHO"], KEY=r["KEY"], TRIP=r["TRIP"], **{"52A": 1}) for k, r in enumerate(dB)]
    dig2b = [dict(Z1=r["Z1"], Z2=r["Z2"], KEY=r["KEY"], RX=r["RX"], TRIP=r["TRIP"], **{"52A": st(k, "L2B")}) for k, r in enumerate(d2b)]
    dig2c = [dict(Z1=r["Z1"], Z2=r["Z2"], KEY=r["KEY"], RX=r["RX"], TRIP=r["TRIP"], **{"52A": st(k, "L2C")}) for k, r in enumerate(d2c)]
    names = ["Z1", "Z2", "KEY", "RX", "TRIP", "52A"]
    write_comtrade("SUBA_L1-21_20260914_142207", "SUBSTATION A", "L1-21 LINE RELAY", q["A"], names, digA, 1200)
    write_comtrade("SUBB_L2-21_20260914_142207", "SUBSTATION B", "L2-21 LINE RELAY", q["L2B"], names, dig2b, 1200)
    write_comtrade("SUBC_L2-21_20260914_142207", "SUBSTATION C", "L2-21 LINE RELAY", q["L2C"], names, dig2c, 1200)
    lab = {1: "asserted", 0: "deasserted"}

    def ser_lines(dig, keys):
        out = []
        for k, x, v in transitions(dig, keys):
            if x == "52A":
                out.append(f"{fmt_ser(ts(k))}  52A        {'closed' if v else 'open'}")
            else:
                out.append(f"{fmt_ser(ts(k))}  {x:<10} {lab[v]}")
        return out
    trip = cs.first(dA, "TRIP")
    floc = (dA[trip]["Z"]["BC"] * 2000 / 240).imag / 0.48
    hdr = lambda sub, rel, line, other: [f"SUBSTATION {sub}  -  {rel} LINE RELAY (230 kV line {line} to Substation {other})", "EVENT SUMMARY"]
    reps = {
        "SUBA_L1-21_event_report.txt": hdr("A", "L1-21", "L1", "B") + [
            f"Date: 2026-09-14   Trigger: {fmt_ser(ts(cs.K_FAULT))}   Oscillography: SUBA_L1-21_20260914_142207",
            "Event: TRIP", "Trip logic: POTT (Z2 and RX)", "Faulted loop: BC",
            f"Fault location (reactance method, line data of settings): {floc:.1f} km", "",
            "SEQUENTIAL EVENTS RECORDER (relay time, GPS synchronized)"] + ser_lines(digA, names) + [""],
        "SUBB_L1-21_event_report.txt": hdr("B", "L1-21", "L1", "A") + [
            f"Date: 2026-09-14   Trigger: {fmt_ser(ts(cs.K_FAULT + 43))}",
            "Event: KEY (no trip)",
            "Oscillography: not available. The relay's event storage (4 records) was overwritten by later events",
            "during the L1 and L2 restoration switching on 2026-09-14; only the SER below was retrieved.", "",
            "SEQUENTIAL EVENTS RECORDER (relay time, GPS synchronized)"] + ser_lines(digB, ["Z1", "Z2", "Z3R", "RX", "ECHO", "KEY", "TRIP"]) + [""],
        "SUBB_L2-21_event_report.txt": hdr("B", "L2-21", "L2", "C") + [
            f"Date: 2026-09-14   Trigger: {fmt_ser(ts(cs.K_FAULT))}   Oscillography: SUBB_L2-21_20260914_142207",
            "Event: TRIP", "Trip logic: Z1", "Faulted loop: BC", "",
            "SEQUENTIAL EVENTS RECORDER (relay time, GPS synchronized)"] + ser_lines(dig2b, names) + [""],
        "SUBC_L2-21_event_report.txt": hdr("C", "L2-21", "L2", "B") + [
            f"Date: 2026-09-14   Trigger: {fmt_ser(ts(cs.K_FAULT))}   Oscillography: SUBC_L2-21_20260914_142207",
            "Event: TRIP", "Trip logic: POTT (Z2 and RX)", "Faulted loop: BC", "",
            "SEQUENTIAL EVENTS RECORDER (relay time, GPS synchronized)"] + ser_lines(dig2c, names) + [""],
    }
    for fn, lines in reps.items():
        open(os.path.join(OUT, fn), "w").write("\n".join(lines))

    def settings(sub, rid, tid, z1, z2, z3, echo, rev):
        return "\n".join([f"SUBSTATION {sub}  -  {rid} LINE RELAY  -  SETTINGS EXPORT (GROUP 1, ACTIVE)", f"Settings revision: {rev}",
             f"RID      = SUB{sub}-{rid}", f"TID      = {tid}",
             "CTR      = 240          ; CT ratio 1200/5", "PTR      = 2000         ; VT ratio 230000/115",
             "Z1ANG    = 84.0         ; deg, maximum torque angle of all mho elements",
             f"Z1P      = {z1:<12} ; ohm sec, zone 1 forward phase mho reach",
             f"Z2P      = {z2:<12} ; ohm sec, zone 2 forward phase mho reach",
             f"Z3P      = {z3:<12} ; ohm sec, zone 3 reverse phase mho reach",
             "50PP     = 0.50         ; A sec, minimum loop current for phase mho elements",
             "SCHEME   = POTT", f"ECHO     = {echo}",
             "EDPU     = 32           ; samples, echo pickup", "EDUR     = 64           ; samples, echo duration",
             "EBLK     = 64           ; samples, echo block after Z3R",
             "TR       = Z1 + Z2*RX   ; trip equation", "KEY      = Z2 + ECHO    ; transmit equation", ""])
    open(os.path.join(OUT, "SUBA_L1-21_settings.txt"), "w").write(settings("A", "L1-21", "230KV LINE L1 TO SUB B", "3.71", "5.79", "OFF", "N", "R4 2025-11-20"))
    open(os.path.join(OUT, "SUBB_L1-21_settings.txt"), "w").write(settings("B", "L1-21", "230KV LINE L1 TO SUB A", "3.71", "5.79", "1.74", "Y", "R5 2026-05-26"))
    open(os.path.join(OUT, "SUBB_L2-21_settings.txt"), "w").write(settings("B", "L2-21", "230KV LINE L2 TO SUB C", "2.32", "3.62", "OFF", "N", "R2 2023-04-18"))
    open(os.path.join(OUT, "SUBC_L2-21_settings.txt"), "w").write(settings("C", "L2-21", "230KV LINE L2 TO SUB B", "2.32", "3.62", "OFF", "N", "R2 2023-04-18"))

    ops = ["SYSTEM OPERATIONS LOG  -  2026-09-14", "",
           "14:22:07  Disturbance, 230 kV system.",
           "          Line L2 (Substation B - Substation C) tripped at both ends (B: zone 1, C: POTT), as expected for an L2 fault.",
           "          Breaker L1 at Substation A tripped (relay L1-21, POTT). Breaker L1 at Substation B did not trip.",
           "14:31:40  L2 patrol dispatched.", "14:40-15:55  Restoration switching at Substations A and B (several close/open operations).",
           "15:58:12  L1 restored from Substation A, no fault found on L1.",
           "17:05:00  Patrol report received for L2 (see patrol report). L2 restored 18:40.",
           "          L1 trip at Substation A classified as a probable misoperation; protection engineering to investigate.", ""]
    open(os.path.join(OUT, "operations_log.txt"), "w").write("\n".join(ops))
    print("opens", opens, "floc", round(floc, 1))


if __name__ == "__main__":
    main()
