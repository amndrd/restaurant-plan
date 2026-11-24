# Floor1 walls: vectorizes the dark regions of the plan kept as walls, and fits the circles
# (columns, booth drums). Pixel coordinates of floor1.png (2000 x 2828).
# usage: .venv/bin/python vectoriser.py   ->  ../modele/floor1-murs.json + ../analyse/_controle-murs.png
import json, math
from pathlib import Path
import cv2, numpy as np

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent
SEUIL = 60

# ids from composantes.py (threshold 60, 8-connectivity), sorted by hand
MURS = [4, 6, 7, 13, 14, 15, 16, 17, 35, 36, 39, 55, 101, 288, 363, 364, 408, 409, 411, 421, 425, 432, 437, 439, 440]
POTEAUX = [40, 251, 257, 41]
TAMBOURS = [49, 114, 306, 413]
ENVELOPPE = (195, 40, 1480, 2420)   # x0, y0, x1, y1: everything is clipped to it

g = cv2.imread(str(RACINE / 'floor1.png'), cv2.IMREAD_GRAYSCALE)
mask = (g < SEUIL).astype(np.uint8)
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
n, lab, stats, cent = cv2.connectedComponentsWithStats(mask, 8)
x0, y0, x1, y1 = ENVELOPPE
clip = np.zeros_like(mask); clip[y0:y1, x0:x1] = 1


def ortho(pts, tol=6):
    """Snap nearly horizontal / vertical edges (in place)."""
    pts = [list(p) for p in pts]
    for k in range(len(pts)):
        a, b = pts[k], pts[(k + 1) % len(pts)]
        if abs(a[0] - b[0]) <= tol and abs(a[1] - b[1]) > tol:
            m = round((a[0] + b[0]) / 2, 1); a[0] = b[0] = m
        elif abs(a[1] - b[1]) <= tol and abs(a[0] - b[0]) > tol:
            m = round((a[1] + b[1]) / 2, 1); a[1] = b[1] = m
    return pts


murs = []
for i in MURS:
    m = ((lab == i) & (clip == 1)).astype(np.uint8)
    # the white outline sits half on the wall: dilate by its half width so the walls meet
    m = cv2.dilate(m, np.ones((5, 5), np.uint8))
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
    sol, *_ = np.linalg.lstsq(A, x * x + y * y, rcond=None)
    cx, cy, c = sol
    return cx, cy, math.sqrt(c + cx * cx + cy * cy)


def anneau(i):
    """Center, outer and inner radii, angular extent of a curved band (image angles, degrees)."""
    m = (lab == i).astype(np.uint8)
    ys, xs = np.nonzero(m)
    pts = np.c_[xs, ys]
    cx, cy, r = cercle(pts)
    d = np.hypot(xs - cx, ys - cy)
    ang = np.degrees(np.arctan2(ys - cy, xs - cx))
    return {'id': i, 'cx': round(cx, 1), 'cy': round(cy, 1),
            'r_ext': round(float(np.percentile(d, 99.5)), 1), 'r_int': round(float(np.percentile(d, 0.5)), 1),
            'a0': round(float(ang.min()), 1), 'a1': round(float(ang.max()), 1)}


poteaux = []
for i in POTEAUX:
    ys, xs = np.nonzero(lab == i)
    cs, _ = cv2.findContours((lab == i).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    pts = max(cs, key=cv2.contourArea)[:, 0, :]
    cx, cy, r = cercle(pts)
    poteaux.append({'id': i, 'cx': round(cx, 1), 'cy': round(cy, 1), 'r': round(r + 2, 1)})

tambours = [anneau(i) for i in TAMBOURS]

out = {'echelle_px_par_m': 120, 'image': 'floor1.png', 'taille': [g.shape[1], g.shape[0]],
       'murs': murs, 'poteaux': poteaux, 'tambours': tambours}
(RACINE / 'modele').mkdir(exist_ok=True)
(RACINE / 'modele' / 'floor1-murs.json').write_text(json.dumps(out, indent=1))

vis = cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)
vis = (vis * 0.55).astype(np.uint8)
for mu in murs:
    for p in [mu['contour']] + mu['trous']:
        cv2.polylines(vis, [np.array(p, np.int32)], True, (40, 40, 255), 2)
for p in poteaux:
    cv2.circle(vis, (int(p['cx']), int(p['cy'])), int(p['r']), (255, 200, 0), 2)
for t in tambours:
    for r in (t['r_ext'], t['r_int']):
        cv2.ellipse(vis, (int(t['cx']), int(t['cy'])), (int(r), int(r)), 0, t['a0'], t['a1'], (0, 220, 120), 2)
(RACINE / 'analyse').mkdir(exist_ok=True)
cv2.imwrite(str(RACINE / 'analyse' / '_controle-murs.png'), vis)
print(len(murs), 'murs ;', 'points', sum(len(m['contour']) for m in murs))
print('poteaux', poteaux)
print('tambours', tambours)
