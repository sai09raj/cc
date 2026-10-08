import json
P = json.load(open("params.json"))
out = ["/* generated from params.json */"]
out.append("static const int L_EW[3][2] = {%s};" % ",".join("{%d,%d}" % tuple(r) for r in P["L_EW"]))
out.append("static const int L_NS[2][3] = {%s};" % ",".join("{%d,%d,%d}" % tuple(r) for r in P["L_NS"]))
out.append("static const int L_ENTRY[12] = {%s};" % ",".join(map(str, P["L_ENTRY"])))
out.append("#define L_EXIT %d" % P["L_EXIT"])
out.append("static const int DEMAND[3][12] = {%s};" % ",".join("{%s}" % ",".join(map(str, P["DEMANDS"][s])) for s in ("AM", "PM", "EVENT")))
out.append("static const int TURN_NS[3] = {%s}; static const int TURN_EW[3] = {%s};" % (",".join(map(str, P["TURN_NS"])), ",".join(map(str, P["TURN_EW"]))))
out.append("#define ALL_RED %d\n#define T_GEN %d\n#define CAP %d" % (P["ALL_RED"], P["T_GEN"], P["CAP"]))
cyc = sorted(int(c) for c in P["GREEN"])
out.append("#define NCYC %d\nstatic const int CYCLES[NCYC] = {%s};" % (len(cyc), ",".join(map(str, cyc))))
out.append("static const int GREEN[NCYC][6][4] = {%s};" % ",".join("{" + ",".join("{%s}" % ",".join(map(str, g)) for g in P["GREEN"][str(c)]) + "}" for c in cyc))
open("params.h", "w").write("\n".join(out) + "\n")
