"""Convertit les 36 fichiers Word en contenus pour le site Astro.

Sortie :
  tdma4/src/data/articles.json   (métadonnées + HTML nettoyé de chaque récit)
  tdma4/public/photos/<pays>/<recit>-NN.jpg
"""
import hashlib, json, os, re, subprocess, sys, unicodedata, glob, shutil, io
from bs4 import BeautifulSoup, NavigableString, Tag
from PIL import Image, ImageOps

SRC = sys.argv[1]          # dossier des .docx
OUT = sys.argv[2]          # racine du projet Astro
TMP = sys.argv[3]          # dossier de travail

MONTHS = {m: i + 1 for i, m in enumerate(
    "janvier février mars avril mai juin juillet août septembre octobre novembre décembre".split())}
WEEKDAYS = "lundi mardi mercredi jeudi vendredi samedi dimanche".split()

RUBRIQUES = {
    "01": ("le-projet", "On part faire un tour du monde", None),
    "02": ("itineraire", "Itinéraire", None),
    "03": ("tanzanie", "Tanzanie", "Afrique"),
    "04": ("chine", "Chine", "Asie"),
    "05": ("laos", "Laos", "Asie"),
    "06": ("cambodge", "Cambodge", "Asie"),
    "07": ("bali", "Bali", "Asie"),
    "08": ("australie", "Australie", "Océanie"),
    "09": ("nouvelle-zelande", "Nouvelle-Zélande", "Océanie"),
    "10": ("polynesie", "Polynésie française", "Océanie"),
    "11": ("ile-de-paques", "Île de Pâques", "Amérique du Sud"),
    "12": ("patagonie", "Patagonie", "Amérique du Sud"),
    "13": ("chili", "Chili", "Amérique du Sud"),
    "14": ("bolivie", "Bolivie", "Amérique du Sud"),
    "15": ("perou", "Pérou", "Amérique du Sud"),
    "16": ("etats-unis", "États-Unis", "Amérique du Nord"),
    "17": ("conclusion", "Conclusion", None),
}


DUPES = []


def nfc(s):
    return unicodedata.normalize("NFC", s)


def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s.lower()).strip("-")
    return re.sub(r"-+", "-", s)


def year_for(month):
    return 2007 if month >= 8 else 2008


DATELINE_PLACE_FIRST = re.compile(
    r"^(?P<place>.{2,60}?),\s*le\s+(?P<d>\d{1,2}|1er)\s+(?P<m>[a-zéû]+)(?:\s+(?P<y>\d{4}))?\s*\.?$", re.I)
DATELINE_DAY_FIRST = re.compile(
    r"^(?:(?:%s)\s+)?(?P<d>\d{1,2}|1er)\s+(?P<m>[a-zéû]+)(?:\s+(?P<y>\d{4}))?\s*,\s*(?P<place>.{2,80}?)\s*\.?$" % "|".join(WEEKDAYS), re.I)
HEADER_DATE = re.compile(r"^(?:le\s+)?(?P<d>\d{1,2})[/ ](?P<m>\d{1,2}|[a-zéû]+)[/ ](?P<y>\d{4})\s*-\s*(?P<title>.+)$", re.I)


def parse_dateline(text):
    t = text.strip()
    for rx in (DATELINE_PLACE_FIRST, DATELINE_DAY_FIRST):
        m = rx.match(t)
        if m and m.group("m").lower() in MONTHS:
            d = 1 if m.group("d") == "1er" else int(m.group("d"))
            mo = MONTHS[m.group("m").lower()]
            y = int(m.group("y")) if m.group("y") else year_for(mo)
            return {"place": m.group("place").strip(" ,."), "date": f"{y:04d}-{mo:02d}-{d:02d}"}
    return None


AI_ALT = re.compile(r"(Une image contenant|contenu généré|Description générée|^image\d*$|\.(jpe?g|gif|png)$)", re.I)


def clean_alt(alt):
    if not alt or AI_ALT.search(alt):
        return ""
    return alt.strip()


def is_image_block(el):
    if not isinstance(el, Tag) or el.name != "p":
        return False
    imgs = el.find_all("img")
    return bool(imgs) and el.get_text(strip=True) == ""


def unwrap_layout_tables(soup):
    for table in soup.find_all("table"):
        cols = table.find_all("col")
        first_row = table.find("tr")
        ncells = len(first_row.find_all(["td", "th"], recursive=False)) if first_row else 0
        if len(cols) <= 1 and ncells <= 1:
            frag = []
            for cell in table.find_all(["td", "th"]):
                frag.extend(list(cell.children))
            for node in frag:
                table.insert_before(node.extract() if isinstance(node, Tag) else NavigableString(str(node)))
            table.decompose()


def split_mixed_paragraphs(soup):
    """Paragraphe contenant image + texte : on sépare l'image dans son propre bloc."""
    for p in list(soup.find_all("p")):
        imgs = p.find_all("img")
        if imgs and p.get_text(strip=True):
            for img in imgs:
                newp = soup.new_tag("p")
                newp.append(img.extract())
                p.insert_before(newp)


def process_image(src_path, dest_dir, dest_name):
    os.makedirs(dest_dir, exist_ok=True)
    im = Image.open(src_path)
    im = ImageOps.exif_transpose(im)
    ext = ".jpg"
    if im.mode in ("P", "RGBA", "LA"):
        im = im.convert("RGB")
    elif im.mode != "RGB":
        im = im.convert("RGB")
    w, h = im.size
    if w > 1600:
        im = im.resize((1600, round(h * 1600 / w)), Image.LANCZOS)
        w, h = im.size
    out = os.path.join(dest_dir, dest_name + ext)
    im.save(out, "JPEG", quality=84, optimize=True, progressive=True)
    return dest_name + ext, w, h


def main():
    files = sorted(glob.glob(os.path.join(SRC, "*.docx")), key=lambda f: nfc(os.path.basename(f)))
    photos_root = os.path.join(OUT, "public", "photos")
    if os.path.isdir(photos_root):
        shutil.rmtree(photos_root)
    articles = []
    for path in files:
        base = nfc(os.path.basename(path)[:-5])
        num = base[:2]
        rslug, rname, continent = RUBRIQUES[num]
        rest = base[3:].strip()
        m = re.match(r"^(.*?)\s+-\s+(?:(\d+)\s+)?(.*)$", rest)
        if m:
            sub_order = int(m.group(2)) if m.group(2) else 1
            file_title = m.group(3).strip()
        else:
            sub_order, file_title = 1, rest

        work = os.path.join(TMP, f"{num}-{sub_order}")
        shutil.rmtree(work, ignore_errors=True)
        os.makedirs(work)
        html = subprocess.run(["pandoc", path, "-t", "html", "--wrap=none", f"--extract-media={work}"],
                              capture_output=True, text=True, check=True).stdout
        soup = BeautifulSoup(html, "html.parser")
        unwrap_layout_tables(soup)
        split_mixed_paragraphs(soup)

        # ---- en-tête : titre, date, lieu --------------------------------
        title, date, place = None, None, None
        blocks = [b for b in soup.contents if isinstance(b, Tag)]
        consumed = 0
        for b in blocks[:5]:
            text = b.get_text(" ", strip=True)
            if is_image_block(b):
                break
            hm = HEADER_DATE.match(text)
            if hm:
                title = title or hm.group("title").strip()
                mo = hm.group("m")
                mo = int(mo) if mo.isdigit() else MONTHS.get(mo.lower(), 1)
                date = date or f"{int(hm.group('y')):04d}-{mo:02d}-{int(hm.group('d')):02d}"
                b.decompose(); consumed += 1; continue
            if text.startswith("Publié dans"):
                b.decompose(); consumed += 1; continue
            dl = parse_dateline(text)
            if dl and len(text) < 90:
                place = dl["place"]
                date = dl["date"]
                b.decompose(); consumed += 1
                break
            if title is None and len(text) < 90 and not text.endswith((".", ":", "!", "?")) or (title is None and text.endswith("…")):
                title = text
                b.decompose(); consumed += 1; continue
            break
        if not title:
            title = file_title
        title = title.replace("CHINE", "Chine")
        title = re.sub(r"\s+", " ", title).strip()

        slug = slugify(title)
        if any(a["slug"] == slug for a in articles):
            slug = f"{slug}-{rslug}"

        # ---- nettoyage du corps ----------------------------------------
        for a in soup.find_all("a"):
            href = a.get("href", "")
            if "web.archive.org" in href or "uniterre" in href or not href:
                a.unwrap()
            else:
                a["rel"] = "noopener"
                a["target"] = "_blank"
        for u in soup.find_all("u"):
            u.unwrap()
        for tag in soup.find_all(["span", "colgroup"]):
            if tag.name == "colgroup":
                tag.decompose()
            else:
                tag.unwrap()
        for tag in soup.find_all(True):
            if tag.name not in ("img", "a", "ol"):
                tag.attrs = {k: v for k, v in tag.attrs.items() if k in ("class",) and tag.name in ("tr",)}
        # adresses e-mail : on les retire du texte
        for s in soup.find_all(string=re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")):
            s.replace_with(re.sub(r"[\w.+-]+@[\w-]+\.[\w.]+", "[adresse retirée]", s))

        # lignes de séparation (_____ ou -----) -> filet
        for p in soup.find_all("p"):
            if re.fullmatch(r"[\s_\-=*.]{8,}", p.get_text()) and not p.find("img"):
                p.replace_with(soup.new_tag("hr"))

        # films à insérer (repères laissés dans les fichiers Word)
        FILM = re.compile(r"(?:à\s+)?ins[ée]rer\s*(?:le\s+)?(?:film)?\s*:?\s*(.+?\.(?:mp4|mov|avi|wmv|m4v))", re.I)
        for p in soup.find_all("p"):
            fm = FILM.search(p.get_text(" ", strip=True))
            if fm:
                v = soup.new_tag("p")
                v["data-film"] = fm.group(1).strip()
                p.replace_with(v)

        # paragraphes courts entièrement en gras/italique : intertitres ou légendes
        for p in soup.find_all("p"):
            txt = p.get_text(" ", strip=True)
            kids = [c for c in p.contents if not (isinstance(c, NavigableString) and not c.strip())]
            if 0 < len(txt) < 90 and len(kids) == 1 and isinstance(kids[0], Tag) and kids[0].name in ("strong", "em") \
                    and not txt.endswith((".", ",")):
                if kids[0].name == "em":
                    p["data-cap"] = "1"   # légende possible si des photos suivent
                else:
                    h = soup.new_tag("h3")
                    h.string = txt
                    p.replace_with(h)

        # ---- images -----------------------------------------------------
        photos = []
        dest_dir = os.path.join(photos_root, rslug)
        idx = 0
        prev_hash = None
        for img in soup.find_all("img"):
            src = img.get("src")
            alt = clean_alt(img.get("alt"))
            # même photo insérée deux fois de suite dans le fichier Word : on n'en garde qu'une
            h = hashlib.md5(open(src, "rb").read()).hexdigest()
            if h == prev_hash:
                DUPES.append(f"{title} : photo {idx} répétée")
                par = img.find_parent("p")
                img.decompose()
                if par is not None and not par.find("img") and not par.get_text(strip=True):
                    par.decompose()
                continue
            prev_hash = h
            if src.lower().endswith(".gif") and rslug == "itineraire":
                img.find_parent("p").decompose()
                continue
            idx += 1
            name, w, h = process_image(src, dest_dir, f"{slug}-{idx:02d}")
            url = f"/photos/{rslug}/{name}"
            photos.append({"src": url, "w": w, "h": h, "alt": alt})
            img.attrs = {"data-photo": str(len(photos) - 1)}

        # regroupement des images consécutives en galeries
        out_parts = []
        group = []

        def flush():
            if group:
                out_parts.append({"type": "photos", "items": [int(i) for i in group]})
                group.clear()

        blocks = list(soup.contents)
        pending_caption = None
        for i, b in enumerate(blocks):
            if isinstance(b, NavigableString):
                if b.strip():
                    flush(); out_parts.append({"type": "html", "html": str(b)})
                continue
            if is_image_block(b):
                for img in b.find_all("img"):
                    group.append(img["data-photo"])
                continue
            flush()
            if b.name == "p" and b.get("data-film"):
                out_parts.append({"type": "film", "file": re.sub(r"^film\s*:?\s*", "", b["data-film"], flags=re.I)})
                continue
            if b.name == "p" and b.get("data-cap"):
                nxt = next((x for x in blocks[i + 1:] if isinstance(x, Tag)), None)
                txt = b.get_text(" ", strip=True)
                if nxt is not None and is_image_block(nxt):
                    out_parts.append({"type": "caption", "text": txt.rstrip(" :\u00a0")})
                    continue
                if not txt.endswith((":", "?", "!")):
                    del b["data-cap"]
                    b.name = "h3"
                    b.string = txt
                else:
                    del b["data-cap"]
            out_parts.append({"type": "html", "html": str(b)})
        flush()
        # une légende précède son groupe de photos : on l'attache au groupe
        merged = []
        for part in out_parts:
            if part["type"] == "photos" and merged and merged[-1]["type"] == "caption":
                part["caption"] = merged.pop()["text"]
            merged.append(part)
        out_parts = [p for p in merged if p["type"] != "caption"] if False else [
            ({"type": "html", "html": f"<p><em>{p['text']}</em></p>"} if p["type"] == "caption" else p) for p in merged]
        # fusion des blocs html consécutifs
        body = []
        for part in out_parts:
            if part["type"] == "html" and body and body[-1]["type"] == "html":
                body[-1]["html"] += "\n" + part["html"]
            else:
                body.append(part)

        text_paras = [p.get_text(" ", strip=True) for p in soup.find_all("p") if p.get_text(strip=True)]
        excerpt = ""
        for t in text_paras:
            if len(t) > 60:
                excerpt = t
                break
        if len(excerpt) > 220:
            excerpt = excerpt[:220].rsplit(" ", 1)[0] + "…"
        words = sum(len(t.split()) for t in text_paras)

        articles.append({
            "slug": slug, "title": title, "rubrique": rslug, "rubriqueName": rname,
            "continent": continent, "order": int(num) * 10 + sub_order,
            "date": date, "place": place, "excerpt": excerpt, "words": words,
            "readingMinutes": max(1, round(words / 220)),
            "photos": photos, "body": body, "sourceFile": base,
        })
        print(f"{base[:55]:55} | {title[:40]:40} | {date} | {place} | {len(photos)} photos")

    # dates manquantes : on hérite du précédent
    articles.sort(key=lambda a: a["order"])
    last = None
    for a in articles:
        if not a["date"]:
            a["date"] = last
            a["dateApprox"] = True
        last = a["date"]
    rubriques = []
    for num, (rslug, rname, cont) in RUBRIQUES.items():
        arts = [a for a in articles if a["rubrique"] == rslug]
        if arts:
            cover = next((a["photos"][0] for a in arts if a["photos"]), None)
            rubriques.append({"slug": rslug, "name": rname, "continent": cont, "num": int(num),
                              "cover": cover, "articles": [a["slug"] for a in arts],
                              "photoCount": sum(len(a["photos"]) for a in arts)})
    os.makedirs(os.path.join(OUT, "src", "data"), exist_ok=True)
    with open(os.path.join(OUT, "src", "data", "articles.json"), "w") as f:
        json.dump(articles, f, ensure_ascii=False, indent=1)
    with open(os.path.join(OUT, "src", "data", "rubriques.json"), "w") as f:
        json.dump(rubriques, f, ensure_ascii=False, indent=1)
    print("doublons retirés :", len(DUPES), DUPES)
    print(len(articles), "articles,", sum(len(a["photos"]) for a in articles), "photos")


if __name__ == "__main__":
    main()
