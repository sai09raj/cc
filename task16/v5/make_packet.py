"""Build artifact/cw200_v1.pdf: data sheet, operating log, three isometric sheets; metadata stripped."""
import os, sys, fitz
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "..", "artifact"); os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, HERE); os.chdir(HERE)
import render
tmpimg = os.path.join(OUT, ".sheet"); render.render("1", tmpimg + "_s1.png"); render.render("2", tmpimg + "_s2.png"); render.render_details(tmpimg + "_s3.png")
doc = fitz.open()
for f, fs in (("datasheet.txt", 8.3), ("oplog.txt", 9.3)):
    p = doc.new_page(width=612, height=792); rc = p.insert_textbox(fitz.Rect(36, 36, 576, 756), open(f).read(), fontsize=fs, fontname="helv"); assert rc >= 0
for s in ("_s1.png", "_s2.png", "_s3.png"):
    data = open(tmpimg + s, "rb").read(); img = fitz.open("png", data); iw, ih = img[0].rect.width, img[0].rect.height
    q = doc.new_page(width=792, height=612); sc = min(762 / iw, 582 / ih); q.insert_image(fitz.Rect(15, 15, 15 + iw * sc, 15 + ih * sc), stream=data)
    os.remove(tmpimg + s)
doc.set_metadata({})
try: doc.del_xml_metadata()
except Exception: pass
tmp = os.path.join(OUT, ".tmp.pdf"); doc.save(tmp, garbage=4, deflate=True, clean=True); doc.close()
d = fitz.open(tmp); d.xref_set_key(-1, "Info", "null"); d.xref_set_key(-1, "ID", "null")
cat = d.pdf_catalog(); pages = d.xref_get_key(cat, "Pages")[1]; d.update_object(cat, "<< /Type /Catalog /Pages %s >>" % pages)
out = os.path.join(OUT, "cw200_v1.pdf"); d.save(out, garbage=4, deflate=True, clean=True, no_new_id=True); d.close(); os.remove(tmp)
raw = open(out, "rb").read(); i = raw.find(b"% Written by")
if i != -1:
    j = raw.find(b"\n", i); raw = raw[:i] + b"%" + b" " * (j - i - 1) + raw[j:]; open(out, "wb").write(raw)
d = fitz.open(out); print(out, d.page_count, d.metadata, d.xref_get_key(-1, "Info"), d.xref_get_key(-1, "ID"))
txt = "".join(pg.get_text() for pg in d)
for val in ("78.64", "75.67", "25.27", "52.31", "29.04", "11.82", "3.06"):
    assert val not in txt, val
print("no answer values in text")
