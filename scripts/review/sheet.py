"""Planche contact des photos d'un récit (numéros = indices dans article.photos). Usage : sheet.py slug sortie.jpg"""
import json, sys, os
from PIL import Image, ImageDraw, ImageFont
SITE = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
a = [x for x in json.load(open(os.path.join(SITE, 'scripts/review/articles.base.json'))) if x['slug'] == sys.argv[1]][0]
W, H, C = 260, 195, 5
n = len(a['photos'])
sheet = Image.new('RGB', (W * C, H * ((n + C - 1) // C)), 'white')
font = ImageFont.load_default(size=28)
for i, p in enumerate(a['photos']):
    im = Image.open(os.path.join(SITE, 'public', p['src'].lstrip('/'))).convert('RGB')
    im.thumbnail((W - 6, H - 6))
    x, y = (i % C) * W, (i // C) * H
    sheet.paste(im, (x + 3, y + 3))
    d = ImageDraw.Draw(sheet)
    d.rectangle([x + 3, y + 3, x + 40, y + 36], fill='black')
    d.text((x + 7, y + 4), str(i), fill='yellow', font=font)
sheet.save(sys.argv[2], quality=85)
