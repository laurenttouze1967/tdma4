"""Construit src/data/itinerary.json à partir de l'itinéraire Travellerspoint (voyage 524886).

Entrées : tp_map.json (réponse _getUserMapJSON), ancien itinerary.json (pour les notes et les liens vers les récits)
"""
import json, re, sys, unicodedata

TP, OLD, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
trip = [t for t in json.load(open(TP))['data']['trips'] if t['tid'] == 524886][0]
old = json.load(open(OLD))

MODE = {1: 'avion', 2: 'bus', 3: 'train', 4: 'route', 5: 'bateau', 0: None}
COUNTRY = {'FR': 'France', 'GB': 'Royaume-Uni', 'TZ': 'Tanzanie', 'KE': 'Kenya', 'ZA': 'Afrique du Sud', 'HK': 'Chine',
           'CN': 'Chine', 'LA': 'Laos', 'KH': 'Cambodge', 'MY': 'Malaisie', 'ID': 'Indonésie', 'AU': 'Australie',
           'NZ': 'Nouvelle-Zélande', 'PF': 'Polynésie française', 'CL': 'Chili', 'AR': 'Argentine', 'BO': 'Bolivie',
           'PE': 'Pérou', 'US': 'États-Unis'}
# libellés Travellerspoint -> noms courts en français
RENAME = {
    'Julius Nyerere International Airport': 'Dar es Salaam',
    'Aéroport international du Kilimandjaro': 'Arusha (aéroport du Kilimandjaro)',
    'Manyara': 'Lac Manyara', 'Mara': 'Serengeti', 'Ngorongoro': 'Cratère du Ngorongoro',
    'Viangchan': 'Vientiane', 'Louang Prabang': 'Luang Prabang', 'Na Hin': 'Na Hin (grotte de Kong Lo)',
    'Savannakhét': 'Savannakhet', 'Paksé': 'Paksé',
    'Siem Reap': 'Siem Reap (Angkor)', 'Xian de Yangshuo': 'Yangshuo', 'Pékin': 'Pékin',
    'Denpasar': 'Bali (Umalas)', 'Aéroport international de Denpasar (DPS)': 'Denpasar',
    'Kawah Ijen': 'Volcan Kawah Ijen (Java)',
    'Sydney Nouvelle Galles du Sud': 'Sydney', 'Uluru Territoire du Nord 0872': 'Uluru',
    'Kings Canyon Airport (KBJ)': 'Kings Canyon', 'Alice Springs Territoire du Nord 0870': 'Alice Springs',
    'Îles Whitsunday': 'Îles Whitsunday', 'Île Fraser': 'Fraser Island', 'Noosa Heads Beach': 'Noosa',
    'Hanmer': 'Hanmer Springs', 'Lac Pukaki': 'Lac Pukaki', 'Catlins Lake': 'Les Catlins', 'Fox Glacier 7886': 'Glacier Fox', 'Fox Glacier': 'Glacier Fox',
    'Parc national de Tongariro': 'Parc de Tongariro',
    "Pape'ete": 'Papeete', 'Papeotai': 'Moorea', 'Huahine': 'Huahine', 'Atoll Rangiroa': 'Rangiroa',
    'Easter Island': 'Île de Pâques', 'Santiago du Chili': 'Santiago du Chili',
    'Parc national Torres del Paine': 'Torres del Paine', 'perito moreno glacier': 'Glacier Perito Moreno',
    'Ushuaïa': 'Ushuaïa', 'Parc national Cabo de Hornos': 'Cap Horn', 'Lagune Colorada': 'Laguna Colorada',
    'Salar de Uyuni': "Salar d'Uyuni", 'Grand Canyon Village': 'Grand Canyon', 'Parc national de Yellowstone': 'Yellowstone',
    'Parc national de Yosemite': 'Yosemite', 'Bagdad': 'Bagdad Café', 'Machu Picchu': 'Machu Picchu',
}
CC_FIX = {'Hong Kong': 'HK', 'perito moreno glacier': 'AR', 'Easter Island': 'CL'}


def short(label):
    first = label.split(',')[0].strip()
    first = re.sub(r'\s+\d{4,5}$', '', first).strip()
    if first in RENAME:
        return RENAME[first]
    first = re.sub(r'\s+(Queensland|Territoire du Nord|Nouvelle Galles du Sud).*$', '', first)
    first = re.sub(r'\s+\d{4,5}$', '', first)
    return RENAME.get(first, first)


def norm(s):
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()


old_sorted = sorted(old, key=lambda s: s['date'])
stops = []
ss = trip['ss']
for i, s in enumerate(ss):
    first = s['l'].split(',')[0].strip()
    cc = s.get('cc') or CC_FIX.get(first, '')
    arrive = s['ad'] if s['ad'] and s['ad'] != '0000-00-00' else s['dd']
    leave = s['dd'] or arrive
    name = short(s['l'])
    if name.startswith('Colombes'):
        name = 'Colombes'
    country = COUNTRY.get(cc, 'Chine' if 'Hong Kong' in s['l'] else '')
    mode_in = MODE.get(ss[i - 1]['tr']) if i else None
    mode_out = MODE.get(s['tr'])
    transit = i not in (0, len(ss) - 1) and arrive == leave and mode_in == 'avion' and mode_out == 'avion'
    stops.append({'name': name, 'country': country, 'lat': round(s['lat'], 4), 'lon': round(s['lng'], 4),
                  'date': arrive, 'until': leave, 'dateApprox': False, 'mode': mode_in, 'transit': transit,
                  'article': None, 'note': ''})

# Récit et note : repris de l'ancien itinéraire (même lieu, sinon étape antérieure la plus proche du même pays)
for st in stops:
    same = [o for o in old if norm(o['name'].split(' (')[0]) in norm(st['name']) or norm(st['name']) in norm(o['name'])]
    same = [o for o in same if abs((int(o['date'][5:7]) * 31 + int(o['date'][8:10])) - (int(st['date'][5:7]) * 31 + int(st['date'][8:10]))) <= 12]
    if same:
        st['note'] = same[0]['note']
    prior = [o for o in old_sorted if o['date'] <= st['date'] and o['country'] == st['country']]
    if not prior:  # première étape d'un pays : on prend le premier récit de ce pays
        prior = [o for o in old_sorted if o['country'] == st['country']][:1]
    if not prior:
        prior = [o for o in old_sorted if o['date'] <= st['date']]
    if prior and prior[-1]['article']:
        st['article'] = prior[-1]['article']
# pays manquant : celui de l'étape précédente
for i, st in enumerate(stops):
    if not st['country'] and i:
        st['country'] = stops[i - 1]['country']
# escales d'une nuit à l'aéroport
for st in stops:
    if st['name'] in ('Johannesburg', 'Denpasar'):
        st['transit'] = True
# ajustements d'après les récits
FIX = {('Punta Arenas', '2008-04-08'): 'cap-horn', ('Santiago du Chili', '2008-04-05'): 'cap-horn',
       ('Calama', '2008-04-26'): 'la-cordillere-des-andes'}
for st in stops:
    if (st['name'], st['date']) in FIX:
        st['article'] = FIX[(st['name'], st['date'])]
stops[0]['article'] = 'depart'
stops[-1]['article'] = 'retour'
stops[-1]['note'] = stops[-1]['note'] or 'Retour à la maison : fin du tour du monde.'
json.dump(stops, open(OUT, 'w'), ensure_ascii=False, indent=1)
print(len(stops), 'étapes,', sum(s['transit'] for s in stops), 'escales,', sum(bool(s['note']) for s in stops), 'avec note')
for s in stops:
    print(f"{s['date']} {'·' if s['transit'] else ' '} {s['mode'] or '-':6} {s['name'][:34]:34} {s['country'][:14]:14} {s['article'] or ''}")
