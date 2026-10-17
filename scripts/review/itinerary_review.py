"""Itinéraire : textes et corrections de la relecture de Laurent (#6). Part de itinerary.base.json."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
stops = json.load(open(os.path.join(HERE, 'itinerary.base.json')))

def find(date, name):
    hits = [s for s in stops if s['date'] == date and s['name'] == name]
    assert len(hits) == 1, (date, name, len(hits))
    return hits[0]

# étape à supprimer : 4 octobre, Stone Town
stops.remove(find('2007-10-04', 'Stone Town'))

g = find('2007-09-20', 'Cratère du Ngorongoro')
g.update(name="Gibb's Farm", lat=-3.33, lon=35.69)
find('2007-11-09', 'Plateau des Bolavens')['name'] = 'Plateau des Bolovens'
find('2007-11-15', 'Siem Reap (Angkor)')['name'] = 'Angkor (Siem Reap)'
find('2008-02-05', 'Milford Sound')['name'] = 'Fiordland'
find('2007-12-23', 'Denpasar')['transit'] = False   # nuit sur place avant le vol pour l'Australie

NOTES = {
    ('2007-09-17', 'Colombes'): 'Départ pour 316 jours de tour du monde.',
    ('2007-09-20', "Gibb's Farm"): "Marche sur le versant de l'ancien volcan Ngorongoro.",
    ('2007-09-21', 'Serengeti'): 'Poursuite du safari en 4x4. Lions, guépards et léopards.',
    ('2007-09-23', 'Cratère du Ngorongoro'): 'Safari au fond du cratère, véritable arche de Noé.',
    ('2007-09-25', 'Stone Town'): 'Trois jours à Stone Town, capitale de Zanzibar.',
    ('2007-09-28', 'Paje'): '1 semaine de plage et de repos.',
    ('2007-10-14', 'Chengde'): "Ancienne ville d'été impériale, au nord de la Grande Muraille.",
    ('2007-10-15', 'Pékin'): 'Poursuite de la découverte de la ville et de sa gare !',
    ('2007-10-17', 'Shanghai'): 'Ancienne concession française, croisière sur la Huangpu et visite du zoo.',
    ('2007-10-20', 'Guilin'): 'Ville-étape pour préparer la logistique de la prochaine semaine et assister à un spectacle sur les minorités.',
    ('2007-10-26', 'Guilin'): 'Arrivée en bus depuis Yangshuo et départ direct pour 24h de train vers Kunming.',
    ('2007-10-27', 'Kunming'): 'Étape de 24h dans la capitale du Yunnan.',
    ('2007-10-28', 'Vientiane'): 'Patuxai, Pha That Luang, baguettes et croissants.',
    ('2007-11-05', 'Vientiane'): '24h pour retrouver un guide Lonely Planet et départ en bus vers le sud.',
    ('2007-11-15', 'Angkor (Siem Reap)'): "6 jours dans les temples d'Angkor et sur le lac Tonlé Sap.",
    ('2007-11-21', 'Bali (Umalas)'): "Sédentaires pendant 1 mois dans une villa à Umalas : surf, plongée et visite de l'île.",
    ('2007-12-23', 'Denpasar'): "Départ vers l'Australie.",
    ('2008-01-06', 'Cairns'): 'Retour en climat tropical sous la pluie.',
    ('2008-01-12', 'Airlie Beach'): "Porte d'entrée des Whitsunday Islands.",
    ('2008-01-19', 'Airlie Beach'): 'Retour du Kokomo à son propriétaire et départ immédiat vers le sud.',
    ('2008-01-28', 'Christchurch'): 'Arrivée par ferry et train TranzCoastal avant la récupération de notre camping-car.',
    ('2008-02-05', 'Fiordland'): 'Hydravion au-dessus de Doubtful Sound depuis Te Anau, puis bateau dans Milford Sound.',
    ('2008-02-06', 'Glenorchy'): 'Sur les traces du Seigneur des anneaux, à cheval.',
    ('2008-02-08', 'Glacier Fox'): 'Randonnée de trois heures sur le glacier.',
    ('2008-02-11', 'Hanmer Springs'): "3 jours de repos et de bains dans les sources d'eaux chaudes.",
    ('2008-02-14', 'Kaikoura'): 'Rendez-vous manqué avec les baleines.',
    ('2008-02-15', 'Christchurch'): 'Fin de notre première expérience de camping-car.',
    ('2008-03-10', 'Huahine'): "Une semaine dans une belle maison à Maroe, avec voiture et barque à moteur. Tour de l'île et rencontre des anguilles aux yeux bleus.",
    ('2008-03-17', 'Bora-Bora'): '24h de luxe au milieu du voyage.',
    ('2008-03-18', 'Fakarava'): 'Atoll, plongées, perles et lagon vert.',
    ('2008-04-09', 'Puerto Natales'): 'Base pour le parc Torres del Paine.',
    ('2008-04-10', 'Puerto Natales'): "Retour à l'hôtel Francis Drake, départ en bus pour l'Argentine sous la neige.",
    ('2008-04-12', 'El Calafate'): 'Chalet et découverte de la Patagonie argentine.',
    ('2008-04-13', 'El Calafate'): 'Retour au chalet avant le vol pour la Terre de Feu.',
    ('2008-04-16', 'Cap Horn'): "Débarquement en zodiac à l'aube sur l'île mythique.",
    ('2008-04-19', 'Punta Arenas'): 'Fin de la croisière.',
    ('2008-04-20', 'Santiago du Chili'): 'Cerro San Cristobal, Cajón del Maipo et beaucoup de temps à la Poste centrale.',
    ('2008-04-25', 'Santiago du Chili'): 'Retour dans la capitale pour prendre un vol vers le nord du pays.',
    ('2008-05-03', 'Laguna Colorada'): 'Poursuite du périple dans le Sud Lipez.',
    ('2008-05-05', 'Uyuni'): 'Étape chez José avant de quitter le Sud Lipez.',
    ('2008-05-12', 'Sucre'): 'Capitale administrative, belle ville coloniale, CNED et Alliance française.',
    ('2008-05-19', 'La Paz'): "Quatre jours pour reprendre les cours du CNED, visiter les différents quartiers et faire du shopping à presque 4 000 m d'altitude.",
    ('2008-05-24', 'Copacabana'): "Port d'accès au lac Titicaca côté bolivien.",
    ('2008-06-01', 'Cuzco'): "Retour chez Antoine avant de s'envoler vers Lima, puis Los Angeles.",
    ('2008-06-10', 'Bagdad Café'): 'Pause sur la route 66 entre Los Angeles et Las Vegas.',
    ('2008-06-10', 'Las Vegas'): '2 jours sur le Strip à fréquenter hôtels démesurés et casinos.',
    ('2008-07-08', 'Yosemite'): 'Lembert Dome et séquoias géants.',
    ('2008-07-12', 'San Diego'): 'Surf à Pacific Beach et visite de Sea World.',
}
for (d, n), note in NOTES.items():
    find(d, n)['note'] = note
for s in stops:
    if s['transit']:
        s['note'] = ''   # simple escale : pas de texte
json.dump(stops, open(os.path.join(HERE, '../../src/data/itinerary.json'), 'w'), ensure_ascii=False, indent=1)
print(len(stops), 'étapes dont', sum(not s['transit'] for s in stops), 'hors escales')
