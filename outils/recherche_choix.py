# Research step 2: downloads the chosen pins of each theme (736 px) into recherche/<theme>/ and writes
# recherche/sources.json (Pinterest page + image URL of every image). The images stay local (third party).
# usage: .venv/bin/python recherche_choix.py
import json, urllib.request, concurrent.futures as cf
from pathlib import Path
R = Path(__file__).resolve().parent.parent / 'recherche'
UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'}
CHOIX = {
    '01-trait-isometrique': [1, 12, 25, 30, 33, 22],
    '02-pieces-3d-isometriques': [1, 9, 15, 34, 39, 33],
    '03-low-poly': [9, 12, 17, 20, 22, 25],
    '04-pixel-art': [3, 9, 15, 16, 37, 30],
    '05-maquette-blanche': [3, 9, 17, 22, 29, 7],
    '06-ligne-claire': [4, 2, 5, 17, 18, 19],
    '07-restaurants-isometriques': [1, 3, 10, 17, 19, 16],
    '08-ecorches': [5, 6, 10, 15, 16, 20],
    '09-cartes-3d-interfaces': [1, 23, 28, 31, 37, 11],
    '10-gestion-de-salle': [12, 41, 46, 47, 48, 59],
}
sources = {}
jobs = []
for theme, nums in CHOIX.items():
    lst = {p['n']: p for p in json.loads((R / '_tri' / theme / 'liste.json').read_text())}
    (R / theme).mkdir(exist_ok=True)
    for k, n in enumerate(nums, 1):
        p = lst[n]
        url = p['image'].replace('/originals/', '/736x/')
        dest = R / theme / f'{k:02d}.jpg'
        jobs.append((url, p['image'], dest))
        sources[f'{theme}/{k:02d}.jpg'] = {'page': p['page'], 'image': p['image']}
def get(j):
    url, orig, dest = j
    for u in (url, orig):
        try:
            dest.write_bytes(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40).read())
            return True
        except Exception:
            pass
    return False
with cf.ThreadPoolExecutor(12) as ex:
    ok = list(ex.map(get, jobs))
(R / 'sources.json').write_text(json.dumps(sources, indent=1, ensure_ascii=False))
print(sum(ok), '/', len(ok), 'images')
for (u, o, d), k in zip(jobs, ok):
    if not k:
        print('raté', d)
