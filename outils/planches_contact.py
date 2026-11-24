# Research step 1: for each theme, list the pins of its Pinterest pages, download small thumbnails
# and make a numbered contact sheet to choose from. Writes recherche/_tri/<theme>/{liste.json, planche.jpg}.
# usage: .venv/bin/python planches_contact.py
import json, subprocess, sys, urllib.request, concurrent.futures as cf
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ICI = Path(__file__).resolve().parent
TRI = ICI.parent / 'recherche' / '_tri'
UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'}
P = 'https://www.pinterest.com/ideas/'
THEMES = {
    '01-trait-isometrique': [P + 'isometric-line-drawing/952974121636/', P + 'axonometric-line-drawing/897603423419/'],
    '02-pieces-3d-isometriques': [P + 'isometric-room-3d-model/903477569003/', P + 'blender-isometric-view/949719293124/'],
    '03-low-poly': [P + 'low-poly-isometric-room/957360182635/', P + '3d-low-poly-room/914693717232/'],
    '04-pixel-art': [P + 'pixel-isometric-art/924706240376/', P + 'pixel-art-room-inspiration/913176312410/'],
    '05-maquette-blanche': [P + 'interior-maquette/924090536646/', P + 'maquette-architecture-models/896569952085/'],
    '06-ligne-claire': [P + 'ligne-claire/931120801054/'],
    '07-restaurants-isometriques': [P + 'isometric-restaurant/939426085372/'],
    '08-ecorches': [P + 'isometric-cutaway/942827018762/', P + 'dollhouse-illustration-art/936936870010/'],
    '09-cartes-3d-interfaces': [P + '3d-maps-design/924430512006/', P + 'isometric-digital-city-design/907634736897/'],
    '10-gestion-de-salle': [P + 'restaurant-pos-ux/935928253047/', P + 'restaurant-operations-dashboard/906348994299/',
                            P + 'table-booking-app/904111769546/'],
}
try:
    F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 22)
except Exception:
    F = ImageFont.load_default()


def pins(url):
    r = subprocess.run([sys.executable, str(ICI / 'pinterest.py'), url, '80'], capture_output=True, text=True, timeout=90)
    return [dict(json.loads(l), page=url) for l in r.stdout.splitlines() if l.strip()]


def get(url, dest):
    try:
        dest.write_bytes(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read())
        return dest
    except Exception:
        return None


for theme, urls in THEMES.items():
    d = TRI / theme
    d.mkdir(parents=True, exist_ok=True)
    lst, seen = [], set()
    for u in urls:
        for p in pins(u):
            if p['image'] not in seen:
                seen.add(p['image']); lst.append(p)
    lst = lst[:60]
    for k, p in enumerate(lst):
        p['n'] = k + 1
        p['vignette'] = p['image'].replace('/originals/', '/236x/').replace('/736x/', '/236x/')
    with cf.ThreadPoolExecutor(12) as ex:
        res = list(ex.map(lambda p: get(p['vignette'], d / f"v{p['n']:02d}.jpg"), lst))
    (d / 'liste.json').write_text(json.dumps(lst, indent=1, ensure_ascii=False))
    ims = []
    for p, f in zip(lst, res):
        if f:
            try:
                ims.append((p['n'], Image.open(f).convert('RGB')))
            except Exception:
                pass
    cols, w, h = 10, 200, 220
    rows = max(1, (len(ims) + cols - 1) // cols)
    sheet = Image.new('RGB', (cols * w, rows * h), 'white')
    dr = ImageDraw.Draw(sheet)
    for i, (n, im) in enumerate(ims):
        im.thumbnail((w - 8, h - 8))
        x, y = (i % cols) * w, (i // cols) * h
        sheet.paste(im, (x + (w - im.width) // 2, y + (h - im.height) // 2))
        dr.rectangle((x + 2, y + 2, x + 36, y + 28), fill='black')
        dr.text((x + 5, y + 3), str(n), fill='white', font=F)
    sheet.save(d / 'planche.jpg', quality=82)
    print(theme, len(lst), 'épingles,', len(ims), 'vignettes')
