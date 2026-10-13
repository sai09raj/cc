"""Build artifact/holloway_v1.pdf: data sheet, site log, elevation, loading diagram; metadata stripped, leak check."""
import os, sys, json, fitz
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "..", "artifact"); os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, HERE); os.chdir(HERE)
import render
NAME = "holloway_v1.pdf"
tmp = os.path.join(OUT, ".sheet"); render.elevation(tmp + "_s3.png"); render.loading(tmp + "_s4.png")
doc = fitz.open()
for f, fs in (("../packet/datasheet.txt", 8.4), ("../packet/sitelog.txt", 9.0)):
    p = doc.new_page(width=612, height=792)
    rc = p.insert_textbox(fitz.Rect(36, 36, 576, 756), open(f).read(), fontsize=fs, fontname="cour" if "datasheet" in f else "helv")
    assert rc >= 0, (f, rc)
for s in ("_s3.png", "_s4.png"):
    data = open(tmp + s, "rb").read(); img = fitz.open("png", data); iw, ih = img[0].rect.width, img[0].rect.height
    q = doc.new_page(width=792, height=612); sc = min(762 / iw, 582 / ih); q.insert_image(fitz.Rect(15, 15, 15 + iw * sc, 15 + ih * sc), stream=data); os.remove(tmp + s)
doc.set_metadata({})
try: doc.del_xml_metadata()
except Exception: pass
t = os.path.join(OUT, ".tmp.pdf"); doc.save(t, garbage=4, deflate=True, clean=True); doc.close()
d = fitz.open(t); d.xref_set_key(-1, "Info", "null"); d.xref_set_key(-1, "ID", "null")
for x in range(1, d.xref_length()):          # drop embedded ICC profiles: images use plain DeviceRGB
    if d.xref_get_key(x, "Subtype")[1] == "/Image" and d.xref_get_key(x, "ColorSpace")[0] != "null":
        d.xref_set_key(x, "ColorSpace", "/DeviceRGB")
cat = d.pdf_catalog(); pages = d.xref_get_key(cat, "Pages")[1]; d.update_object(cat, "<< /Type /Catalog /Pages %s >>" % pages)
out = os.path.join(OUT, NAME); d.save(out, garbage=4, deflate=True, clean=True, no_new_id=True); d.close(); os.remove(t)
raw = open(out, "rb").read(); i = raw.find(b"% Written by")
if i != -1:
    j = raw.find(b"\n", i); raw = raw[:i] + b"%" + b" " * (j - i - 1) + raw[j:]; open(out, "wb").write(raw)
raw = open(out, "rb").read()
for bad in (b"Producer", b"Creator", b"Author", b"CreationDate", b"ModDate", b"XMP", b"matplotlib", b"tEXt", b"ICCBased"):
    assert bad not in raw, bad
d = fitz.open(out); print(out, d.page_count, d.metadata, d.xref_get_key(-1, "Info"))
for pg in d: assert not pg.get_drawings(), "vector drawings present"
txt = "".join(pg.get_text() for pg in d); k = json.load(open("key.json"))
vals = [f"{abs(v):.4g}" for v in k.values()] + [f"{abs(v):.2f}" for v in k.values()]
leaks = [v for v in vals if v in txt and len(v) >= 4]; assert not leaks, leaks
print("no metadata, no vectors, no answer values in text")
