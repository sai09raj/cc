"""TASK 13: write the text/data files of the incident bundle (COMTRADE records, event reports, settings, logs)."""
import datetime as dt, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import waves, build_case as bc  # noqa: E402

OUT = os.path.join(HERE, "..", "artifact", "bundle")
T0 = dt.datetime(2026, 9, 14, 14, 22, 7, 345000)   # time of sample 0 (both relays GPS-synchronized)


def ts(k):
    return T0 + dt.timedelta(microseconds=round(k * 1e6 / waves.FS))


def fmt_cfg_time(t):
    return t.strftime("%d/%m/%Y,%H:%M:%S.") + f"{t.microsecond:06d}"


def fmt_ser(t):
    return t.strftime("%H:%M:%S.") + f"{t.microsecond // 1000:03d}" + f"{(t.microsecond % 1000) // 100:01d}"


def write_comtrade(name, station, dev, q, dig_names, digs, ct_primary):
    n = len(q["V"][0])
    an = [("VA", "A", "V", q["V"][0], bc.QV, 2000, 1), ("VB", "B", "V", q["V"][1], bc.QV, 2000, 1),
          ("VC", "C", "V", q["V"][2], bc.QV, 2000, 1), ("IA", "A", "A", q["I"][0], bc.QI, ct_primary, 5),
          ("IB", "B", "A", q["I"][1], bc.QI, ct_primary, 5), ("IC", "C", "A", q["I"][2], bc.QI, ct_primary, 5)]
    lines = [f"{station},{dev},1999", f"{len(an) + len(dig_names)},{len(an)}A,{len(dig_names)}D"]
    for i, (cid, ph, uu, data, mult, pri, sec) in enumerate(an, 1):
        lines.append(f"{i},{cid},{ph},,{uu},{mult},0,0,{min(data)},{max(data)},{pri},{sec},S")
    for j, d in enumerate(dig_names, 1):
        lines.append(f"{j},{d},,,0")
    lines += ["60", "1", f"{int(waves.FS)},{n}", fmt_cfg_time(ts(0)), fmt_cfg_time(ts(waves.K_FAULT)), "ASCII", "1"]
    open(os.path.join(OUT, name + ".cfg"), "w", newline="\r\n").write("\n".join(lines) + "\n")
    rows = []
    for k in range(n):
        vals = [str(ch[k]) for ch in q["V"]] + [str(ch[k]) for ch in q["I"]]
        dv = [str(digs[k][d]) for d in dig_names]
        rows.append(",".join([str(k + 1), str(round(k * 1e6 / waves.FS))] + vals + dv))
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
    q, rec, dA, dB, PA, PB, trip = bc.build()
    k_open = trip + waves.BKR_A
    k_l2 = waves.K_FAULT + waves.K_L2_CLEAR_DELAY
    digA = [dict(Z1=r["Z1"], Z2=r["Z2"], KEY=r["KEY"], RX=r["RX"], TRIP=r["TRIP"], **{"52A": 0 if k >= k_open else 1})
            for k, r in enumerate(dA)]
    digB = [dict(Z1=r["Z1"], Z2=r["Z2"], Z3R=r["Z3R"], RX=r["RX"], ECHO=r["ECHO"], KEY=r["KEY"], **{"52A": 1})
            for k, r in enumerate(dB)]
    write_comtrade("SUBA_L1_RLY_20260914_142207", "SUBSTATION A", "L1-21 LINE RELAY", q["A"],
                   ["Z1", "Z2", "KEY", "RX", "TRIP", "52A"], digA, 1200)
    write_comtrade("SUBB_L1_RLY_20260914_142207", "SUBSTATION B", "L1-21 LINE RELAY", q["B"],
                   ["Z1", "Z2", "Z3R", "RX", "ECHO", "KEY", "52A"], digB, 1200)

    # event reports
    za = dA[trip]["Z"]["BC"] * 2000 / 240     # relay A's own primary conversion (its settings CTR)
    floc = za.imag / 0.48
    serA = transitions(digA, ["Z1", "Z2", "KEY", "RX", "TRIP", "52A"])
    serB = transitions(digB, ["Z1", "Z2", "Z3R", "RX", "ECHO", "KEY"])
    lab = {1: "asserted", 0: "deasserted"}

    def ser_lines(ser, open_label):
        out = []
        for k, x, v in ser:
            if x == "52A":
                out.append(f"{fmt_ser(ts(k))}  52A        {'closed' if v else 'open'}")
            else:
                out.append(f"{fmt_ser(ts(k))}  {x:<10} {lab[v]}")
        return out
    A_txt = ["SUBSTATION A  -  L1-21 LINE RELAY (230 kV line L1 to Substation B)", "EVENT SUMMARY",
             f"Date: 2026-09-14   Trigger: {fmt_ser(ts(waves.K_FAULT))}   Record: SUBA_L1_RLY_20260914_142207",
             "Event: TRIP", "Trip logic: POTT (Z2 and RX)", "Faulted loop: BC",
             f"Fault location (reactance method, line data of settings): {floc:.1f} km", "",
             "SEQUENTIAL EVENTS RECORDER (relay time, GPS synchronized)"] + ser_lines(serA, "") + [""]
    B_txt = ["SUBSTATION B  -  L1-21 LINE RELAY (230 kV line L1 to Substation A)", "EVENT SUMMARY",
             f"Date: 2026-09-14   Trigger: {fmt_ser(ts(waves.K_FAULT))}   Record: SUBB_L1_RLY_20260914_142207",
             "Event: KEY (no trip)", "", "SEQUENTIAL EVENTS RECORDER (relay time, GPS synchronized)"] + ser_lines(serB, "") + [""]
    open(os.path.join(OUT, "SUBA_L1_RLY_event_report.txt"), "w").write("\n".join(A_txt))
    open(os.path.join(OUT, "SUBB_L1_RLY_event_report.txt"), "w").write("\n".join(B_txt))

    def settings(sub, other, z3, echo):
        s = [f"SUBSTATION {sub}  -  L1-21 LINE RELAY  -  SETTINGS EXPORT (GROUP 1, ACTIVE)",
             f"RID      = SUB{sub}-L1-21", f"TID      = 230KV LINE L1 TO SUB {other}",
             "CTR      = 240          ; CT ratio (primary A / 5 A)", "PTR      = 2000         ; VT ratio (primary V / secondary V)",
             "Z1ANG    = 84.0         ; deg, maximum torque angle of all mho elements",
             "Z1P      = 3.71         ; ohm sec, zone 1 forward phase mho reach",
             "Z2P      = 5.79         ; ohm sec, zone 2 forward phase mho reach",
             f"Z3P      = {z3:<12} ; ohm sec, zone 3 reverse phase mho reach",
             "50PP     = 0.50         ; A sec, minimum loop current for phase mho elements",
             "SCHEME   = POTT", f"ECHO     = {echo}",
             "EDPU     = 32           ; samples, echo pickup", "EDUR     = 64           ; samples, echo duration",
             "EBLK     = 64           ; samples, echo block after Z3R",
             "TR       = Z1 + Z2*RX   ; trip equation", "KEY      = Z2 + ECHO    ; transmit equation", ""]
        return "\n".join(s)
    open(os.path.join(OUT, "SUBA_L1_RLY_settings.txt"), "w").write(settings("A", "B", "OFF", "N"))
    open(os.path.join(OUT, "SUBB_L1_RLY_settings.txt"), "w").write(settings("B", "A", "1.74", "Y"))

    ops = ["SYSTEM OPERATIONS LOG  -  2026-09-14", "",
           f"{fmt_ser(ts(waves.K_FAULT))[:8]}  Disturbance, 230 kV system. Breaker L1 at Substation A tripped (relay L1-21, POTT).",
           f"{fmt_ser(ts(waves.K_FAULT))[:8]}  Line L2 (Substation B - Substation C) tripped at both ends, zone 1, correct.",
           "            Breaker L1 at Substation B did not trip.",
           "14:31:40  L2 patrol dispatched.", "15:58:12  L1 restored from Substation A, no fault found on L1.",
           "17:05:00  Patrol report received for L2 (see patrol report). L2 restored 18:40.",
           "            L1 trip at Substation A classified as a probable misoperation; protection engineering to investigate.", ""]
    open(os.path.join(OUT, "operations_log.txt"), "w").write("\n".join(ops))

    key = dict(trip_sample=trip, open_sample=k_open, l2_clear_sample=k_l2, floc_km=round(floc, 1),
               serA=[(k, x, v) for k, x, v in serA], serB=[(k, x, v) for k, x, v in serB])
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    json.dump(key, open(os.path.join(HERE, "out", "case_key.json"), "w"), indent=1)
    print(json.dumps(key)[:600])


if __name__ == "__main__":
    main()
