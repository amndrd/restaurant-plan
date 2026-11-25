# The table numbers of the live map, over the top view in fantôme: one black badge per table, from
# modele/floor1-tables.json (written by outils/blender/floor1.py mobilier=1), or for the 1st floor from
# modele/floor2-tables.json (outils/blender/floor2.py mobilier=1; same camera, same frame).
# Writes rendus/5-mobilier/tables-numerotees.png, or rendus/15-etage-mobilier/tables-numerotees.png.
# usage: outils/.venv/bin/python outils/numeros_tables.py [etage1]
import json
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

R = Path(__file__).resolve().parents[1]
ETAGE = 'etage1' in sys.argv[1:]
DOS = R / 'rendus' / ('15-etage-mobilier' if ETAGE else '5-mobilier')
tables = json.loads((R / 'modele' / ('floor2-tables.json' if ETAGE else 'floor1-tables.json')).read_text())['tables']
NOMS_BARS = {0: 'Bar', 100: 'Omakase', 101: 'Tablette'}

# the top camera of floor1.py: ortho 21.6 m across 2000 px, centred on P(837, 1278) = (0, -0.4) m,
# turned -90 deg: screen right = world -y, screen up = world +x
K = 2000 / 21.6
OX, OY = 0.0, -0.4


def ecran(x, y):
    return 1000 - (y - OY) * K, 625 - (x - OX) * K


im = Image.open(DOS / 'fantome-dessus.png').convert('RGB')
d = ImageDraw.Draw(im)
police = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 22)
for t in tables:
    u, v = ecran(*t['centre_m'])
    if t['type'] == 'bar' and t['id'] == 0:
        v -= 0.10 * K                           # the badge on the counter, not on the bartender's side
    r = 19
    d.ellipse((u - r, v - r, u + r, v + r), fill=(17, 17, 17))
    txt = NOMS_BARS.get(t['id'], 'Bar') if t['type'] == 'bar' else str(t['id'])
    if t['type'] == 'bar':
        w = d.textlength(txt, font=police)
        d.rounded_rectangle((u - w / 2 - 12, v - r, u + w / 2 + 12, v + r), radius=r, fill=(17, 17, 17))
    d.text((u, v + 1), txt, font=police, fill='white', anchor='mm')
im.save(DOS / 'tables-numerotees.png')
print('écrit', DOS / 'tables-numerotees.png')
