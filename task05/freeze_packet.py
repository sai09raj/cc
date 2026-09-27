from pathlib import Path
import hashlib,json,datetime,shutil
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'platform'
files=['artifact/KILNWORKS-T05-R2-20260926.pdf','platform/prompt.md','platform/ideal-flow.json','platform/ideal-flow.md','platform/rubric.json','platform/rubric.md']
manifest=P/'frozen-packet-manifest.json'
if manifest.exists():raise SystemExit('Freeze already exists; verify it, never overwrite it.')
rows=json.loads((P/'rubric.json').read_text(encoding='utf-8'));flows=json.loads((P/'ideal-flow.json').read_text(encoding='utf-8'))
assert 12<=len(rows)<=50 and all(-10<=r['weight']<=10 for r in rows)
assert sum(max(0,r['weight']) for r in rows)==77
assert len((P/'prompt.md').read_text(encoding='utf-8').split())<=500
assert all(5<=len(s)<=3000 for s in flows.values())
result=dict(version='R2-F1',frozen_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),purpose='one local blind calibration; no target-model acceptance claims',criteria=len(rows),positive_weight=77,negative_weight=-8,files=[dict(path=p,bytes=(ROOT/p).stat().st_size,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in files])
manifest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
dest=ROOT/'blind/r2-run01/input';dest.mkdir(parents=True,exist_ok=False)
for p in files[:2]:shutil.copyfile(ROOT/p,dest/Path(p).name)
(ROOT/'blind/r2-run01/output').mkdir()
print(json.dumps(result))
