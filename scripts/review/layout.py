"""Applique la relecture de Laurent (oct. 2026) aux récits.

Part de articles.base.json (sortie de convert.py) et des consignes de specs.py ; écrit src/data/articles.json.
Chaque récit est vu comme une suite de jetons : blocs de texte (paragraphes, titres, listes…) et groupes de photos.
"""
import json, re, sys, unicodedata, os, copy
from bs4 import BeautifulSoup
from PIL import Image, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.abspath(os.path.join(HERE, '../..'))
sys.path.insert(0, HERE)
from specs import SPECS

arts = json.load(open(os.path.join(HERE, 'articles.base.json')))
album = json.load(open(os.path.join(SITE, 'src/data/album-final.json')))
by_stem = {}
for r, groups in album.items():
    for g in groups:
        for p in g['photos']:
            if p.get('stem'):
                by_stem.setdefault(p['stem'].lower(), p)


def norm(s):
    s = re.sub(r'<[^>]+>', ' ', s)
    s = s.replace('’', "'").replace('‘', "'").replace('«', '"').replace('»', '"').replace('\xa0', ' ')
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    s = re.sub(r'[^a-z0-9]+', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


class Doc:
    def __init__(self, a):
        self.a = a
        self.toks = []
        for part in a['body']:
            if part['type'] == 'html':
                s = BeautifulSoup(part['html'], 'html.parser')
                for c in s.children:
                    if str(c).strip():
                        self.toks.append({'t': 'b', 'html': str(c)})
            elif part['type'] == 'photos':
                self.toks.append({'t': 'P', **{k: v for k, v in part.items() if k != 'type'}})
            else:
                self.toks.append({'t': 'F', 'file': part['file']})

    # --- repérage
    def block(self, start, nth=0):
        key = norm(start)
        hits = [i for i, t in enumerate(self.toks) if t['t'] == 'b' and norm(t['html']).startswith(key)]
        if not hits:
            hits = [i for i, t in enumerate(self.toks) if t['t'] == 'b' and key in norm(t['html'])]
        if len(hits) != 1 and not (hits and nth):
            raise SystemExit(f"[{self.a['slug']}] bloc « {start} » : {len(hits)} correspondance(s)")
        return hits[nth]

    def photo(self, ref):
        if isinstance(ref, int):
            return ref
        st = ref.lower()
        for i, p in enumerate(self.a['photos']):
            if p.get('stem', '').lower() == st:
                return i
        raise SystemExit(f"[{self.a['slug']}] photo {ref} inconnue (ajouter d'abord)")

    def group_of(self, i):
        for k, t in enumerate(self.toks):
            if t['t'] == 'P' and i in t['items']:
                return k
        return None

    def take(self, idx):
        """retire des photos de leurs groupes ; renvoie la légende si une photo seule est retirée"""
        cap = None
        for i in idx:
            k = self.group_of(i)
            if k is None:
                continue
            g = self.toks[k]
            g['items'].remove(i)
            if not g['items']:
                cap = cap or g.get('caption')
                del self.toks[k]
        return cap

    def insert(self, pos, tok):
        self.toks.insert(pos, tok)

    # --- opérations
    def op(self, o):
        kind = o['op']
        if kind == 'add':
            p = by_stem.get(o['stem'].lower())
            if not p:
                raise SystemExit(f"[{self.a['slug']}] photo à ajouter introuvable dans l'album : {o['stem']}")
            self.a['photos'].append({'src': p.get('m') or p['src'], 'w': p.get('mw') or p['w'], 'h': p.get('mh') or p['h'],
                                     'full': p['full'], 'fw': p['fw'], 'fh': p['fh'], 'alt': o.get('alt', ''), 'stem': o['stem'],
                                     'album': True})
            return
        if kind == 'beside':        # photo(s) flottante(s) à côté du paragraphe
            idx = [self.photo(x) for x in (o['photo'] if isinstance(o['photo'], list) else [o['photo']])]
            cap = self.take(idx)
            k = self.block(o['para'], o.get('nth', 0))
            self.insert(k, {'t': 'P', 'items': idx, 'float': o.get('side', True), **({'caption': o.get('caption', cap)} if o.get('caption', cap) else {})})
            # seul le paragraphe concerné (ou les n suivants) habille la photo ; la suite reprend sous la photo
            if o.get('paras', 1):
                self.insert(k + 1 + o.get('paras', 1), {'t': 'brk'})
            return
        if kind in ('before', 'after'):  # groupe de photos (pleine largeur) avant / après un paragraphe
            idx = [self.photo(x) for x in o['photos']]
            cap = self.take(idx)
            k = self.block(o['para'], o.get('nth', 0)) + (1 if kind == 'after' else 0)
            tok = {'t': 'P', 'items': idx}
            if o.get('caption', cap):
                tok['caption'] = o.get('caption', cap)
            for key in ('wide', 'layout'):
                if key in o:
                    tok[key] = o[key]
            self.insert(k, tok)
            return
        if kind == 'para_before_photo':   # déplace un paragraphe juste avant le groupe d'une photo
            k = self.block(o['para'], o.get('nth', 0))
            tok = self.toks.pop(k)
            self.toks.insert(self.group_of(self.photo(o['photo'])), tok)
            return
        if kind == 'para_after_photo':
            k = self.block(o['para'], o.get('nth', 0))
            tok = self.toks.pop(k)
            self.toks.insert(self.group_of(self.photo(o['photo'])) + 1, tok)
            return
        if kind == 'group':   # modifie le groupe qui contient une photo
            g = self.toks[self.group_of(self.photo(o['photo']))]
            for key in ('wide', 'layout', 'float', 'caption'):
                if key in o:
                    if o[key] is None:
                        g.pop(key, None)
                    else:
                        g[key] = o[key]
            if 'order' in o:
                g['items'] = [self.photo(x) for x in o['order']]
            return
        if kind == 'merge':   # fusionne le bloc avec le précédent (même paragraphe)
            k = self.block(o['para'], o.get('nth', 0))
            prev = self.toks[k - 1]
            assert prev['t'] == 'b', (self.a['slug'], o)
            inner = lambda h: re.sub(r'^<p[^>]*>|</p>$', '', h.strip())
            sep = '<br/>' if o.get('br') else ' '
            prev['html'] = '<p>' + inner(prev['html']) + sep + inner(self.toks[k]['html']) + '</p>'
            del self.toks[k]
            return
        if kind == 'replace':
            n = 0
            for t in self.toks:
                if t['t'] == 'b' and o['old'] in t['html']:
                    t['html'] = t['html'].replace(o['old'], o['new']); n += 1
            if not n:
                raise SystemExit(f"[{self.a['slug']}] texte introuvable : {o['old']}")
            return
        if kind == 'delete':
            del self.toks[self.block(o['para'], o.get('nth', 0))]
            return
        if kind == 'insert':  # nouveau bloc après un paragraphe, ou en fin de récit
            k = len(self.toks) if o.get('para') is None else self.block(o['para']) + 1
            self.toks.insert(k, {'t': 'b', 'html': o['html']})
            return
        if kind == 'set_html':
            self.toks[self.block(o['para'])]['html'] = o['html']
            return
        if kind == 'photo_caption':  # légende propre à une photo (sous la photo, petite et en italique)
            self.a['photos'][self.photo(o['photo'])]['cap'] = o['text']
            return
        raise SystemExit('opération inconnue : ' + kind)

    def body(self):
        out = []
        brk = False
        for t in self.toks:
            if t['t'] == 'brk':
                brk = True; continue
            if t['t'] == 'b':
                if out and out[-1]['type'] == 'html' and not brk:
                    out[-1]['html'] += '\n' + t['html']
                else:
                    out.append({'type': 'html', 'html': t['html']})
                brk = False
                continue
            brk = False
            if False:
                pass
            elif t['t'] == 'P':
                out.append({'type': 'photos', **{k: v for k, v in t.items() if k != 't'}})
            else:
                out.append({'type': 'film', 'file': t['file']})
        return out


CHECK = sys.argv[2:] if len(sys.argv) > 1 and sys.argv[1] == '--check' else None
errors = []
COMMENT_LINE = re.compile(r'commentaires?\s*\(\s*\d+\s*\)\s*::', re.I)
for a in arts:
    for i, p in enumerate(a['photos']):
        p.setdefault('stem', os.path.splitext(os.path.basename(p['src']))[0])
    d = Doc(a)
    # ligne héritée de l'ancienne plateforme : « commentaires (1) :: Ajouter un commentaire :: Lien permanent »
    d.toks = [t for t in d.toks if not (t['t'] == 'b' and COMMENT_LINE.search(re.sub(r'<[^>]+>', '', t['html'])))]
    saved = copy.deepcopy((a['photos'], d.toks))
    try:
        for o in SPECS.get(a['slug'], []):
            d.op(o)
    except SystemExit as e:
        errors.append(str(e)); a['photos'], d.toks = saved
    for t in d.toks:   # orthographe : plateau des Bolovens
        if t['t'] == 'b':
            t['html'] = re.sub(r'Boloven(?!s)', 'Bolovens', t['html'])
    if CHECK and a['slug'] in CHECK:
        print('=====', a['slug'])
        n = 0
        for t in d.toks:
            if t['t'] == 'b':
                print(f"  b{n:<3}", re.sub(r'<[^>]+>', '', t['html']).strip().replace('\n', ' ')[:100]); n += 1
            elif t['t'] == 'brk':
                print('  ----')
            elif t['t'] == 'P':
                extra = {k: v for k, v in t.items() if k not in ('t', 'items')}
                print('  [P]', [a['photos'][i].get('stem') if a['photos'][i].get('album') else i for i in t['items']], extra or '')
            else:
                print('  [F]', t['file'])
    a['body'] = d.body()
    used = sorted({i for part in a['body'] if part['type'] == 'photos' for i in part['items']})
    a['photoCount'] = len(used)

for e in errors:
    print('ERREUR', e)
if CHECK is None:
    json.dump(arts, open(os.path.join(SITE, 'src/data/articles.json'), 'w'), ensure_ascii=False, indent=1)
print('ok', sum(len(SPECS.get(a['slug'], [])) for a in arts), 'opérations')
