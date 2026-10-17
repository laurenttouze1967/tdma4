"""Album photos : état figé tel que relu par Laurent (album_frozen.json), puis ses déplacements (#42–#51).

Les numéros de photos des consignes se réfèrent à l'album relu (avant tout déplacement).
Écrit src/data/album-final.json et crée les images des photos nouvelles.
"""
import json, os, re, sys, glob
from PIL import Image, ImageOps

FROZEN, SRC, UP = sys.argv[1], sys.argv[2], sys.argv[3]   # album figé, photos d'origine, photos envoyées à part
SITE = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
album = json.load(open(FROZEN))

def slug(s):
    import unicodedata
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')

# nom de fichier d'origine de chaque photo (pour les retrouver par leur nom)
stems = {}
for f in glob.glob(os.path.join(SRC, '*', '**', '*'), recursive=True):
    if f.lower().endswith(('.jpg', '.jpeg', '.png')) and '__MACOSX' not in f:
        st = os.path.splitext(os.path.basename(f))[0]
        stems.setdefault(slug(st), st)
for r, groups in album.items():
    for g in groups:
        for p in g['photos']:
            if not p.get('full', '').startswith('/album/'):
                continue
            pid = os.path.splitext(os.path.basename(p['full']))[0]
            cands = [s for s in stems if pid.endswith('-' + s) or pid.endswith('-' + s + '-2') or pid.endswith('-' + s + '-3')]
            if cands:
                p['stem'] = stems[max(cands, key=len)]

def save(im, path, maxside, q):
    im = im.copy(); im.thumbnail((maxside, maxside), Image.LANCZOS)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path, 'JPEG', quality=q, optimize=True, progressive=True)
    return im.size

def make(rub, place, stem, path):
    """crée les fichiers d'une photo (grande, vignette, moyenne pour les récits)"""
    im = ImageOps.exif_transpose(Image.open(path)).convert('RGB')
    pid = slug(f'{place}-{stem}')
    full = f'/album/{rub}/{pid}.jpg'
    fw, fh = save(im, os.path.join(SITE, 'public', full[1:]), 1600, 84)
    thumb = f'/album/{rub}/t/{pid}.jpg'
    w, h = save(im, os.path.join(SITE, 'public', thumb[1:]), 640, 80)
    return {'src': thumb, 'w': w, 'h': h, 'full': full, 'fw': fw, 'fh': fh, 'alt': place, 'date': None, 'stem': stem}

def medium(p):
    """version 1200 px pour une photo reprise dans un récit"""
    if p.get('m'):
        return
    pid = os.path.splitext(os.path.basename(p['full']))[0]
    rub = p['full'].split('/')[2]
    m = f'/album/{rub}/m/{pid}.jpg'
    im = Image.open(os.path.join(SITE, 'public', p['full'][1:]))
    p['m'] = m
    p['mw'], p['mh'] = save(im, os.path.join(SITE, 'public', m[1:]), 1200, 82)

# ---- sections, repérées par (album, titre[, n-ième occurrence])
def sec(rub, title, nth=0):
    hits = [g for g in album[rub] if g['title'] == title]
    if len(hits) <= nth:
        raise SystemExit(f'section introuvable : {rub} / {title}')
    return hits[nth]

moves = []   # (photos, album cible, section cible, 'start'|'end')
def mv(rub, title, nums, drub, dtitle, where='end', nth=0, dnth=0):
    s = sec(rub, title, nth)
    n = len(s['photos'])
    idx = list(range(1, n + 1)) if nums == 'all' else [n + k + 1 if k < 0 else k for k in nums]
    moves.append(([s['photos'][i - 1] for i in idx], drub, dtitle, where, dnth))

def new_section(rub, title, after, nth=0):
    i = album[rub].index(sec(rub, after, nth))
    album[rub].insert(i + 1, {'title': title, 'photos': []})

# #42 Laos
mv('laos', 'Vientiane', [1], 'chine', 'Yangshuo')
# #43 Bali
mv('bali', 'Volcan Kawah Ijen (Java)', [-3, -2, -1], 'bali', 'Bali (Umalas)')
# #44 Australie
mv('australie', 'Townsville', [-1], 'australie', 'Îles Whitsunday', 'start')
mv('australie', 'Brisbane', [-1], 'australie', 'Fraser Island, Hervey Bay')
# #45 Nouvelle-Zélande
new_section('nouvelle-zelande', 'Christchurch', 'Wellington')
mv('nouvelle-zelande', 'Wellington', [-3, -2, -1], 'nouvelle-zelande', 'Christchurch')
mv('nouvelle-zelande', 'Queenstown', 'all', 'nouvelle-zelande', 'Glenorchy')
mv('nouvelle-zelande', 'Glacier Fox', [8, 9], 'nouvelle-zelande', 'Glenorchy')
mv('nouvelle-zelande', 'Waiotapu, Auckland', [-4], 'nouvelle-zelande', 'Murchison')
mv('nouvelle-zelande', 'Waiotapu, Auckland', [-3], 'nouvelle-zelande', 'Napier, Parc de Tongariro')
# #46 Polynésie
mv('polynesie', 'Huahine', [1, 2, 3, 4], 'polynesie', 'Papeete, Moorea')
mv('polynesie', 'Rangiroa', [1, 2, 3, 4], 'polynesie', 'Fakarava')
# #47 Île de Pâques
mv('ile-de-paques', 'Rapa Nui', [-2, -1], 'chili', 'Santiago du Chili', 'start')
# #48 Patagonie
mv('patagonie', 'Torres del Paine, Puerto Natales', 'all', 'patagonie', 'Puerto Natales')
mv('patagonie', 'Punta Arenas', [1, 2, 4, 5, 6, 7, 8], 'patagonie', 'Cap Horn')
mv('patagonie', 'Punta Arenas', [3], 'patagonie', 'El Calafate')
# #49 Chili
mv('chili', 'Calama, San Pedro de Atacama', [14, 15, 16], 'chili', 'Santiago du Chili')
mv('chili', 'Calama, San Pedro de Atacama', [-3, -2, -1], 'bolivie', 'Laguna Verde, Sol de Mañana, Laguna Colorada…', 'start')
# #50 Bolivie
B1 = 'Laguna Verde, Sol de Mañana, Laguna Colorada…'
mv('bolivie', "Salar d'Uyuni", [1, 2, 3, 4, 5, 6, 7], 'bolivie', B1)
mv('bolivie', 'Sucre', [5, 6, 7], 'bolivie', "Salar d'Uyuni")
mv('bolivie', 'Cochabamba', 'all', 'bolivie', 'Torotoro')
mv('bolivie', 'La Paz', [5, 6], 'bolivie', 'Torotoro')
mv('bolivie', 'Copacabana, Isla del Sol', [6], 'bolivie', 'La Paz')
mv('bolivie', 'Autres photos du récit « La mer de sel »', 'all', 'bolivie', "Salar d'Uyuni")
# #51 États-Unis
U = 'etats-unis'
mv(U, 'Kingman', [1], U, 'Los Angeles', 'start')
mv(U, 'Kingman', [2, 3, 4], U, 'Bagdad Café, Las Vegas')
mv(U, 'Monument Valley', [k for k in range(1, 11) if k != 4], U, 'Page')
mv(U, 'Monument Valley', [4], U, 'Grand Canyon')
mv(U, 'Moab', [1, 2, 3, 4], U, 'Page')
mv(U, 'Gold Beach', [2, 3], U, 'Moab')
mv(U, 'Gold Beach', [4, 5, 6, 7], U, 'Yellowstone')
mv(U, 'Bodie', [1], U, 'San Francisco')
mv(U, 'Bodie', [2, 3], U, 'Yosemite, Fresno')
mv(U, 'Yosemite, Fresno', [5, 6, 7], U, 'San Francisco')
mv(U, 'San Diego', [4], U, 'San Clemente', 'start')
mv(U, 'San Diego', [2], U, 'San Clemente')
mv(U, 'San Diego', [3], U, 'Yosemite, Fresno')
mv(U, 'Los Angeles', 'all', U, 'San Diego', nth=1)
mv(U, 'Chicago', [4, 5], U, 'San Diego')
mv(U, 'New York', [18, 19], U, 'Chicago')
mv(U, 'New York', list(range(42, 52)), U, 'San Diego')

# application : on retire d'abord toutes les photos déplacées, puis on les insère
for photos, *_ in moves:
    for p in photos:
        for groups in album.values():
            for g in groups:
                if p in g['photos']:
                    g['photos'].remove(p)
targets = []
for photos, drub, dtitle, where, dnth in moves:
    targets.append((sec(drub, dtitle, dnth), photos, where))
for g, photos, where in targets:
    if where == 'start':
        g['photos'][0:0] = photos
    else:
        g['photos'].extend(photos)

# photos envoyées à part le 17 octobre (absentes des archives)
NEW = [('2cf35650', 'laos', 'Luang Prabang', '2007_1102LuangPrabang0111'),
       ('010e9e72', 'bali', 'Bali (Umalas)', 'CIMG0234'),
       ('3b1d1098', 'bali', 'Bali (Umalas)', 'CIMG0229'),
       ('9090a395', 'chili', 'Calama, San Pedro de Atacama', 'CIMG1023'),
       ('c137203b', 'polynesie', 'Papeete, Moorea', 'CIMG0424')]
for up, rub, title, stem in NEW:
    sec(rub, title)['photos'].append(make(rub, title, stem, os.path.join(UP, up + '-image.jpg')))

# renommages
RENAME = {
    ('laos', 'Plateau des Bolavens'): 'Plateau des Bolovens',
    ('nouvelle-zelande', 'Milford Sound'): 'Fiordland',
    ('nouvelle-zelande', 'Murchison'): 'Murchison, Hanmer Springs et Kaikoura',
    ('patagonie', 'Puerto Natales'): 'Torres del Paine, Puerto Natales',
    ('chili', 'Calama, San Pedro de Atacama'): 'San Pedro de Atacama',
    ('bolivie', B1): 'Sud Lipez',
    ('bolivie', "Salar d'Uyuni"): "Salar d'Uyuni, Uyuni",
    ('bolivie', 'Torotoro'): 'Torotoro, Cochabamba',
    (U, 'Page'): 'Page, Monument Valley',
    (U, 'Moab'): 'Moab et Grand Teton',
    (U, 'Yosemite, Fresno'): 'Yosemite',
    (U, 'San Clemente'): 'Santa Barbara, San Clemente',
}
for (rub, old), new in RENAME.items():
    sec(rub, old)['title'] = new
# sections fusionnées : dates réunies
pn = sec('patagonie', 'Torres del Paine, Puerto Natales')
pn['to'] = '2008-04-10'
for groups in album.values():
    for g in groups:
        if not g.get('from'):
            ds = sorted(p['date'] for p in g['photos'] if p.get('date'))
            if ds:
                g['from'], g['to'] = ds[0], ds[-1]
for rub in album:
    album[rub] = [g for g in album[rub] if g['photos']]
    for g in album[rub]:
        g.pop('link', None) if not g['title'].startswith('Autres photos') else None

# version moyenne pour les photos reprises dans les récits
USED = ['IMG_1978', 'IMG_2007 2', '2008_0108Uluru0007', '2008_0108Uluru0054', '2008_0108Uluru0196',
        '2008_0116Queensland0005 2', '2008_0116Queensland0020 2', 'Photo06_3A', '2008_0307Moorea0022',
        '2008_0310Moorea0081', 'CIMG0424', 'CIMG0229']
for groups in album.values():
    for g in groups:
        for p in g['photos']:
            if p.get('stem') in USED:
                medium(p)
found = {p.get('stem') for gs in album.values() for g in gs for p in g['photos']}
print('manquantes :', [s for s in USED if s not in found])
json.dump(album, open(os.path.join(SITE, 'src/data/album-final.json'), 'w'), ensure_ascii=False, indent=1)
for rub, groups in album.items():
    print(rub, sum(len(g['photos']) for g in groups), [(g['title'], len(g['photos'])) for g in groups])
print('total', sum(len(g['photos']) for gs in album.values() for g in gs))
