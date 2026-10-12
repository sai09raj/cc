"""Build artifact/kingsmead_v2.pdf: data sheet, control log, SLD, cable route plan; metadata stripped."""
import os, sys, json, fitz
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "..", "artifact"); os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, HERE); os.chdir(HERE)
import render
tmp = os.path.join(OUT, ".sheet"); render.sld(tmp + "_sld.png"); render.plan(tmp + "_plan.png")
doc = fitz.open()
for f, fs in (("../packet/datasheet.txt", 8.6), ("../packet/oplog.txt", 9.0)):
    p = doc.new_page(width=612, height=792); rc = p.insert_textbox(fitz.Rect(36, 36, 576, 756), open(f).read(), fontsize=fs, fontname="helv"); assert rc >= 0, f
for s in ("_sld.png", "_plan.png"):
    data = open(tmp + s, "rb").read(); img = fitz.open("png", data); iw, ih = img[0].rect.width, img[0].rect.height
    q = doc.new_page(width=792, height=612); sc = min(762 / iw, 582 / ih); q.insert_image(fitz.Rect(15, 15, 15 + iw * sc, 15 + ih * sc), stream=data); os.remove(tmp + s)
doc.set_metadata({})
try: doc.del_xml_metadata()
except Exception: pass
t = os.path.join(OUT, ".tmp.pdf"); doc.save(t, garbage=4, deflate=True, clean=True); doc.close()
d = fitz.open(t); d.xref_set_key(-1, "Info", "null"); d.xref_set_key(-1, "ID", "null")
cat = d.pdf_catalog(); pages = d.xref_get_key(cat, "Pages")[1]; d.update_object(cat, "<< /Type /Catalog /Pages %s >>" % pages)
out = os.path.join(OUT, "kingsmead_v2.pdf"); d.save(out, garbage=4, deflate=True, clean=True, no_new_id=True); d.close(); os.remove(t)
raw = open(out, "rb").read(); i = raw.find(b"% Written by")
if i != -1:
    j = raw.find(b"\n", i); raw = raw[:i] + b"%" + b" " * (j - i - 1) + raw[j:]; open(out, "wb").write(raw)
d = fitz.open(out); print(out, d.page_count, d.metadata, d.xref_get_key(-1, "Info"))
txt = "".join(pg.get_text() for pg in d); k = json.load(open("key.json"))
vals = [f"{k['kV'][b]:.3f}" for b in k["kV"]] + [f"{v['I_A']:.1f}" for v in k["routes"].values()] + [f"{k['losses_kW']:.1f}", f"{k['T1']['MVA']:.3f}", f"{k['T2']['MVA']:.3f}"]
leaks = [v for v in vals if v in txt]; assert not leaks, leaks; print("no answer values in text")
