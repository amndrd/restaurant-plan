# First floor (floor2.png, the mezzanine): vectorises the walls kept by hand among the dark regions, fits the
# columns, and outlines the void over the room (its lighter tone). Pixel coordinates of floor2.png, the same frame
# as floor1.png. Writes modele/etage1-murs.json and analyse/_controle-etage1.png.
# usage: outils/.venv/bin/python outils/vectoriser_etage1.py
import json
import math
from pathlib import Path

import cv2
import numpy as np

R = Path(__file__).resolve().parents[1]
SEUIL = 60
# ids from composantes.py on floor2.png (threshold 60), sorted by hand: walls, partitions, ends of the bar
MURS = [4, 5, 6, 9, 14, 10, 11, 15, 16, 17, 39, 730, 731, 732, 733, 734, 741, 767, 768, 770, 936, 952, 1064, 1065,
        1066, 1068, 860]
POTEAUX = [841, 843, 989, 995]

g = cv2.imread(str(R / 'floor2.png'), cv2.IMREAD_GRAYSCALE)
mask = (g < SEUIL).astype(np.uint8)
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
n, lab, stats, cent = cv2.connectedComponentsWithStats(mask, 8)


def ortho(pts, tol=6):
    pts = [list(map(float, p)) for p in pts]
    for k in range(len(pts)):
        a, b = pts[k], pts[(k + 1) % len(pts)]
        if abs(a[0] - b[0]) <= tol and abs(a[1] - b[1]) > tol:
            m = round((a[0] + b[0]) / 2, 1); a[0] = b[0] = m
        elif abs(a[1] - b[1]) <= tol and abs(a[0] - b[0]) > tol:
            m = round((a[1] + b[1]) / 2, 1); a[1] = b[1] = m
    return pts


murs = []
for i in MURS:
    m = (lab == i).astype(np.uint8)
    m = cv2.dilate(m, np.ones((5, 5), np.uint8))          # the white outline sits half on the wall
    cs, hier = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    if hier is None:
        continue
    hier = hier[0]
    for k, c in enumerate(cs):
        if hier[k][3] != -1 or cv2.contourArea(c) < 40:
            continue
        loops = [c] + [cs[j] for j in range(len(cs)) if hier[j][3] == k and cv2.contourArea(cs[j]) > 40]
        polys = [ortho(cv2.approxPolyDP(L, 1.6, True)[:, 0, :].tolist()) for L in loops]
        murs.append({'id': i, 'contour': polys[0], 'trous': polys[1:]})


def cercle(pts):
    x, y = pts[:, 0].astype(float), pts[:, 1].astype(float)
    A = np.c_[2 * x, 2 * y, np.ones_like(x)]
    (cx, cy, c), *_ = np.linalg.lstsq(A, x * x + y * y, rcond=None)
    return cx, cy, math.sqrt(c + cx * cx + cy * cy)


poteaux = []
for i in POTEAUX:
    cs, _ = cv2.findContours((lab == i).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    pts = max(cs, key=cv2.contourArea)[:, 0, :]
    cx, cy, r = cercle(pts)
    poteaux.append({'id': i, 'cx': round(cx, 1), 'cy': round(cy, 1), 'r': round(r + 2, 1)})

# the void: the lighter tone inside the building (the room below seen from above), its outer outline
vide = ((g > 85) & (g < 215)).astype(np.uint8)
vide[:1150, :] = 0; vide[:, :230] = 0; vide[:, 1100:] = 0; vide[2260:, :] = 0
vide = cv2.morphologyEx(vide, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
nv, lv, sv, _ = cv2.connectedComponentsWithStats(vide, 8)
k = 1 + int(np.argmax(sv[1:, cv2.CC_STAT_AREA]))
cs, _ = cv2.findContours((lv == k).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
contour_vide = cv2.approxPolyDP(max(cs, key=cv2.contourArea), 2.0, True)[:, 0, :].tolist()

out = {'echelle_px_par_m': 120, 'image': 'floor2.png', 'murs': murs, 'poteaux': poteaux, 'vide': contour_vide}
(R / 'modele' / 'etage1-murs.json').write_text(json.dumps(out, indent=1))

vis = (cv2.cvtColor(g, cv2.COLOR_GRAY2BGR) * 0.55).astype(np.uint8)
for mu in murs:
    for p in [mu['contour']] + mu['trous']:
        cv2.polylines(vis, [np.array(p, np.int32)], True, (40, 40, 255), 2)
for p in poteaux:
    cv2.circle(vis, (int(p['cx']), int(p['cy'])), int(p['r']), (255, 200, 0), 2)
cv2.polylines(vis, [np.array(contour_vide, np.int32)], True, (0, 220, 120), 2)
cv2.imwrite(str(R / 'analyse' / '_controle-etage1.png'), vis)
print(len(murs), 'murs ;', len(contour_vide), 'points pour le vide ;', poteaux)
