"""Affiche la structure d'un récit : blocs de texte (b#) et groupes de photos (indices)."""
import json, sys, re
from bs4 import BeautifulSoup
arts = {a['slug']: a for a in json.load(open('/home/claude/tdma4/src/data/articles.json'))}
def blocks(html):
    s = BeautifulSoup(html, 'html.parser')
    return [str(c) for c in s.children if str(c).strip()]
for slug in sys.argv[1:]:
    a = arts[slug]; n = 0
    print('=====', slug, '|', a['title'], '|', len(a['photos']), 'photos')
    for part in a['body']:
        if part['type'] == 'html':
            for b in blocks(part['html']):
                t = re.sub(r'<[^>]+>', '', b).strip().replace('\n', ' ')
                print(f'  b{n:<3} {t[:110]}'); n += 1
        elif part['type'] == 'photos':
            print('  [P]', part['items'], ('« ' + part['caption'] + ' »') if part.get('caption') else '')
        else:
            print('  [F]', part['file'])
