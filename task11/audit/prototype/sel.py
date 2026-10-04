import gcp
gcp.P["OLD_SIZE"]=128*1024; gcp.VAR["BLOB"]=(13,96)
r=gcp.sweep(dims="PT")
feas={k:v for k,v in r.items() if not v[0]}
# row: (oom, minor, major, copied, promoted, ptot, pmax, peak_old)
s1=min(feas, key=lambda k:(feas[k][5], feas[k][6], k))
pm=sorted(v[6] for v in feas.values()); pt=sorted(v[5] for v in feas.values())
print("pmax quartiles", pm[len(pm)//4], pm[len(pm)//2], pm[3*len(pm)//4], "ptot quartiles", pt[len(pt)//4], pt[len(pt)//2], pt[3*len(pt)//4])
budget=pt[len(pt)//3]
s2=min((k for k in feas if feas[k][5]<=budget), key=lambda k:(feas[k][6], feas[k][5], k))
ceil=pm[len(pm)//3]
s3=min((k for k in feas if feas[k][6]<=ceil), key=lambda k:(k[0]+2*k[1], feas[k][5], k))
for name,k in [("min total pause",s1),("min max pause | ptot<=%d"%budget,s2),("min young footprint | pmax<=%d"%ceil,s3)]:
    print(name, k, feas[k])
print("rows with pmax<=ceil:", sum(1 for v in feas.values() if v[6]<=ceil), " rows with ptot<=budget:", sum(1 for v in feas.values() if v[5]<=budget))
