import gcp
gcp.P["OLD_SIZE"]=128*1024; gcp.VAR["BLOB"]=(13,96)
base=gcp.sweep(dims="PT")
for m in ["dfs","remset_insertion","tenure_gt","no_coalesce","guard_largest","best_tie_high"]:
    r=gcp.sweep({m:True},dims="PT")
    print(f"{m:18s} rows_changed={sum(1 for k in base if base[k]!=r[k]):3d}/96 ptot_changed={sum(1 for k in base if base[k][5]!=r[k][5]):3d}")
