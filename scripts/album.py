"""Construit l'album photo à partir des dossiers envoyés (un dossier par lieu).

Entrée : album_src/<Archive_Lieu_N>/*.jpg
Sortie :
  public/album/<rubrique>/<id>.jpg      (grande taille, 1600 px max)
  public/album/<rubrique>/t/<id>.jpg    (vignette, 640 px max)
  src/data/album.json                   (sections par lieu, photos triées par date de prise de vue)
  src/data/hd.json                      (photos des récits pour lesquelles une meilleure définition existe)
Les doublons (même photo envoyée deux fois) sont éliminés en gardant la meilleure définition.
"""
import glob, json, os, re, sys, unicodedata, shutil
from PIL import Image, ImageOps
import imagehash

SRC, SITE = sys.argv[1], sys.argv[2]

# dossier (sans Archive_ ni numéro) -> (rubrique, libellé)
PLACES = {
    "d_part": ("le-projet", "Le départ"), "depart": ("le-projet", "Le départ"),
    "Tanzanie": ("tanzanie", "Safari"), "Zanzibar": ("tanzanie", "Zanzibar"),
    "Hong_Kong": ("chine", "Hong Kong"), "Beijing": ("chine", "Pékin"), "Shanghai": ("chine", "Shanghai"),
    "Guilin": ("chine", "Guilin"), "Yangshuo": ("chine", "Yangshuo"),
    "Vientiane": ("laos", "Vientiane"), "Luang_Prabang": ("laos", "Luang Prabang"), "Hin_Boun": ("laos", "Hin Boun et la grotte de Kong Lo"),
    "Boloven": ("laos", "Plateau des Bolavens"), "Bolaven": ("laos", "Plateau des Bolavens"), "Done_Khon": ("laos", "Don Khon"), "Don_Khon": ("laos", "Don Khon"),
}

def place_of(folder):
    key = re.sub(r"^Archive_?", "", folder)
    key = re.sub(r"[_ ]?\d+$", "", key)
    return key, PLACES.get(key)

def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

def taken(im, path):
    try:
        d = im.getexif().get(306) or im.getexif().get(36867)
        if d and re.match(r"\d{4}:\d\d:\d\d", d):
            return d[:10].replace(":", "-") + "T" + d[11:19]
    except Exception:
        pass
    m = re.search(r"(20\d\d)_(\d\d)(\d\d)", os.path.basename(path))
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}T00:00:00" if m else None

def save(im, path, maxside, q):
    im = im.copy()
    im.thumbnail((maxside, maxside), Image.LANCZOS)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path, "JPEG", quality=q, optimize=True, progressive=True)
    return im.size

# ---- 1. inventaire et dédoublonnage -------------------------------------------
items, unknown = [], set()
for f in sorted(glob.glob(os.path.join(SRC, "*", "**", "*"), recursive=True)):
    if "__MACOSX" in f or not f.lower().endswith((".jpg", ".jpeg", ".png")):
        continue
    folder = os.path.relpath(f, SRC).split(os.sep)[0]
    key, pl = place_of(folder)
    if not pl:
        unknown.add(key); continue
    im = ImageOps.exif_transpose(Image.open(f))
    items.append({"path": f, "rubrique": pl[0], "place": pl[1], "w": im.size[0], "h": im.size[1],
                  "hash": imagehash.phash(im), "date": taken(Image.open(f), f), "name": os.path.basename(f)})
if unknown:
    print("DOSSIERS NON RECONNUS :", sorted(unknown))

kept, dupes = [], 0
for it in sorted(items, key=lambda x: -x["w"] * x["h"]):
    twin = next((k for k in kept if k["hash"] - it["hash"] <= 4), None)
    if twin:
        dupes += 1
        if not twin["date"] and it["date"]:
            twin["date"] = it["date"]
        continue
    kept.append(it)

# ---- 2. correspondance avec les photos des récits ---------------------------
articles = json.load(open(os.path.join(SITE, "src/data/articles.json")))
art_photos = []
for a in articles:
    for p in a["photos"]:
        art_photos.append((a["slug"], p, imagehash.phash(Image.open(os.path.join(SITE, "public", p["src"].lstrip("/"))))))

out_root = os.path.join(SITE, "public", "album")
shutil.rmtree(out_root, ignore_errors=True)
hd, album, matched_src = {}, {}, set()
used_ids = set()
for it in kept:
    im = ImageOps.exif_transpose(Image.open(it["path"])).convert("RGB")
    base = slug(f"{it['place']}-{os.path.splitext(it['name'])[0]}")
    pid = base
    n = 2
    while pid in used_ids:
        pid = f"{base}-{n}"; n += 1
    used_ids.add(pid)
    full = f"/album/{it['rubrique']}/{pid}.jpg"
    fw, fh = save(im, os.path.join(SITE, "public", full.lstrip("/")), 1600, 84)
    if max(fw, fh) > 700:
        thumb = f"/album/{it['rubrique']}/t/{pid}.jpg"
        save(im, os.path.join(SITE, "public", thumb.lstrip("/")), 640, 80)
    else:
        thumb = full
    match = next(((s, p) for s, p, h in art_photos if h - it["hash"] <= 6), None)
    if match:
        matched_src.add(match[1]["src"])
    rec = {"id": pid, "src": thumb, "full": full, "w": fw, "h": fh, "date": it["date"],
           "article": match[0] if match else None}
    if match and fw > match[1]["w"] * 1.3:
        # une meilleure définition existe pour une photo de récit
        med = f"/album/{it['rubrique']}/m/{pid}.jpg"
        mw, mh = save(im, os.path.join(SITE, "public", med.lstrip("/")), 1200, 82)
        hd[match[1]["src"]] = {"src": med, "w": mw, "h": mh, "full": full, "fw": fw, "fh": fh}
    album.setdefault(it["rubrique"], {}).setdefault(it["place"], []).append(rec)

result = {}
for r, places in album.items():
    secs = []
    for place, photos in places.items():
        photos.sort(key=lambda p: (p["date"] or "9999", p["id"]))
        dates = [p["date"] for p in photos if p["date"]]
        secs.append({"place": place, "from": min(dates)[:10] if dates else None, "to": max(dates)[:10] if dates else None, "photos": photos})
    secs.sort(key=lambda s: s["from"] or "9999")
    result[r] = secs

json.dump(result, open(os.path.join(SITE, "src/data/album.json"), "w"), ensure_ascii=False, indent=1)
json.dump(hd, open(os.path.join(SITE, "src/data/hd.json"), "w"), ensure_ascii=False, indent=1)
json.dump(sorted(matched_src), open(os.path.join(SITE, "src/data/album-index.json"), "w"), indent=1)
total = sum(len(s["photos"]) for v in result.values() for s in v)
print(f"{len(items)} fichiers reçus, {dupes} doublons retirés, {total} photos dans l'album, "
      f"{sum(1 for v in result.values() for s in v for p in s['photos'] if p['article'])} déjà dans les récits, "
      f"{len(hd)} photos de récits passées en meilleure définition")
for r, secs in result.items():
    print(" ", r, [(s["place"], len(s["photos"]), s["from"], s["to"]) for s in secs])
