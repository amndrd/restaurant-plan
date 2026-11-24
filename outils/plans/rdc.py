# The ground floor, redrawn: the walls vectorised from floor1.png (modele/floor1-murs.json) and everything else from
# the measurements of the 3D model (outils/blender/floor1.py), so the plan and the map match exactly.
import json
import math
import random

from dessin import (PX, Plan, arc, chaise, fauteuil, plante, rrect, R)

D = json.loads((R / 'modele' / 'floor1-murs.json').read_text())


def dessiner(p: Plan):
    # ---- floors: the dark terrazzo, the light concrete, the street
    p.rect('fond', 560, 2412, 1575, 2575, 'exterieur')
    p.poly('sol', [(385, 146), (1418, 146), (1418, 283), (1473, 283), (1473, 2410), (575, 2410), (575, 2275),
                   (201, 2275), (201, 728), (385, 728)], 'sol')
    p.poly('sol', [(231, 728), (857, 728), (857, 1894), (604, 1894), (604, 2275), (231, 2275)], 'sol-clair')

    # ---- walls and columns (cut, solid)
    for m in D['murs']:
        p.polys('poche', [m['contour']] + m['trous'], 'poche')
    for c in D['poteaux']:
        cx, r = (405.1, 49.2) if c['id'] == 41 else (c['cx'], c['r'])
        p.cercle('poche', cx, c['cy'], r, 'poche')
    p.ligne('haut', arc(1477.5, 1516.7, 104, 112, 248, 40), 'pointille')   # the ring of lights around the facade column

    # ---- glass-block facades: the band of blocks between the steel mullions
    for x, y0, y1 in ((382, 150, 723), (224, 848, 1117), (224, 1211, 2170), (1452, 870, 1450), (1452, 1583, 2230)):
        p.rect('vitrage', x - 4.5, y0, x + 4.5, y1, 'vitrage')
        n = max(1, round((y1 - y0) * PX / 1.2))
        for k in range(n + 1):
            y = y0 + (y1 - y0) * k / n
            p.rect('vitrage', x - 6, y - 2.5, x + 6, y + 2.5, 'poche')
    p.rect('vitrage', 1068, 2402, 1308, 2411, 'vitrage')

    # ---- the drums: the shell (cut), the hung ring above (dashed), the U banquette, the round table, 3 armchairs
    for n, t in enumerate(sorted(D['tambours'], key=lambda t: t['cy'])):
        cx, cy = t['cx'], t['cy']
        coque = arc(cx, cy, 152, 90, 270, 60) + arc(cx, cy, 131, 270, 90, 60)
        p.poly('poche', coque, 'poche')
        for s in (-1, 1):
            p.rect('poche', cx, cy + s * 131, 444, cy + s * 152, 'poche')
        p.cercle('haut', cx, cy, 152, 'haut')
        assise = [(413, cy - 131)] + arc(cx, cy, 131, 270, 90, 60) + [(413, cy + 131), (413, cy + 75.8)] + \
            arc(cx, cy, 75.8, 90, 270, 50) + [(413, cy - 75.8)]
        p.poly('mobilier', assise, 'cuir')
        p.ligne('mobilier', arc(cx, cy, 104, 270, 90, 50), 'fin')            # the front of the rolled backrest
        tc = (cx - 12, cy - 4)
        p.cercle('mobilier', *tc, 58, 'meuble')
        p.cercle('mobilier', tc[0] + 18, tc[1], 4.8, 'trait')
        for dx, dy in ((64, -87), (105, -7), (64, 73)):
            for pts in fauteuil(cx + dx, cy + dy, tc):
                p.poly('mobilier', pts, 'cuir')

    # ---- the bar: counter, working shelf, glass-cell front; the back bar, its canopy above
    p.rect('mobilier', 413, 623, 1190, 737, 'meuble-g')
    p.rect('mobilier', 413, 623, 1190, 683, 'meuble')
    p.rect('mobilier', 409, 680, 1194, 752, 'meuble')
    p.rect('vitrage', 413, 737.5, 1190, 745, 'vitrage')
    p.ligne('detail', [(428, 757), (1176, 757)], 'trait')                    # the foot rail
    for k in range(6):
        x = 440 + (1165 - 440) * k / 5
        p.ligne('detail', [(x, 745), (x, 757)], 'fin')
    for x0, x1 in ((565, 625), (1110, 1170)):
        p.rect('mobilier', x0, 422, x1, 488, 'meuble-g')
    p.rect('mobilier', 625.5, 422, 1109.5, 490, 'meuble')
    p.rect('mobilier', 640, 425, 1095, 470, 'meuble-g')
    p.rect('mobilier', 640, 425, 1095, 448, 'meuble')
    p.rect('haut', 565, 422, 1170, 500, 'haut')
    for k in range(7):
        x = 657 + 71.67 * k
        for pts in chaise(x, 792.5, (x, 700)):
            p.poly('mobilier', pts, 'cuir')

    # ---- the tables of the room (the model's SALLE), lamps on the tables
    salle = [
        (664, 1208.5, 757.5, 1354, [(x, y) for x in (627.5, 793.5) for y in (1242.5, 1322.5)], [1281.25]),
        (664, 1446, 757.5, 1895, [(x, y) for x in (627.5, 793.5) for y in (1480, 1560, 1672.5, 1777.5, 1857.5)], [1595, 1741]),
        (996, 1301, 1090, 1447.5, [(x, y) for x in (957.5, 1130) for y in (1335, 1410)], [1374.25]),
        (996, 1560, 1090, 1655, [(957.5, 1612.5), (1130, 1612.5)], [1607.5]),
        (996, 1747.5, 1090, 1840, [(957.5, 1797.5), (1130, 1797.5)], [1793.75]),
        (1282.5, 890, 1376, 1037.5, [(1242.5, 925), (1242.5, 1005)], [963.75]),
        (1282.5, 1109, 1376, 1205, [(1242.5, 1160)], [1157]),
        (1282.5, 1285, 1376, 1430, [(1242.5, 1320), (1242.5, 1402.5)], [1357.5]),
        (1282.5, 1585, 1376, 1730, [(1242.5, 1620), (1242.5, 1700)], [1657.5]),
    ]
    for x0, y0, x1, y1, chaises, lampes in salle:
        cx = (x0 + x1) / 2
        for x, y in chaises:
            for pts in chaise(x, y, (cx, y)):
                p.poly('mobilier', pts, 'cuir')
        p.rect('mobilier', x0, y0, x1, y1, 'meuble')
        for yl in lampes:
            p.cercle('mobilier', cx, yl, 4.8, 'trait')
    # the ledge under the right facade, around the two columns
    cols = [(1477.5, 805.0, 68.8), (1477.5, 1516.7, 69.1)]
    front = [(1384 - (13 * math.sin(math.pi * (y - 1462) / 110) if 1462 < y < 1572 else 0), y) for y in range(857, 1756, 3)]
    back = []
    for y in range(1755, 856, -3):
        x = 1434
        for cx_, cy_, r in cols:
            if abs(y - cy_) < r:
                x = min(x, cx_ - math.sqrt(r * r - (y - cy_) ** 2))
        back.append((x, y))
    p.poly('mobilier', front + back, 'meuble-g')

    # ---- the banquette by the bar: its planter of low greenery, four tables for two
    p.rect('mobilier', 660, 915, 1110, 930, 'meuble-g')
    p.rect('mobilier', 660, 930, 1110, 993, 'cuir')
    p.rect('mobilier', 660, 930, 1110, 941, 'cuir')
    rnd = random.Random(4)
    for k in range(28):
        x = 670 + (1100 - 670) * k / 27 + rnd.uniform(-4, 4)
        p.cercle('detail', x, 922.5 + rnd.uniform(-3, 3), rnd.uniform(7, 10), 'feuille')
    for x in (717, 829, 941, 1053):
        p.poly('mobilier', [(a + x, b + 967.1) for a, b in rrect(0, 0, 0.83 / PX, 0.43 / PX, 0.05 / PX)], 'cuir')
        for pts in chaise(x, 1106.5, (x, 1034)):
            p.poly('mobilier', pts, 'cuir')
        p.rect('mobilier', x - 42, 998, x + 42, 1070, 'meuble')
        p.cercle('mobilier', x, 1044, 4.8, 'trait')

    # ---- planters with a small tree
    for k, (x, y) in enumerate(((711, 1401), (1044, 1252.5), (1044, 1702.5))):
        bulles = plante(x, y, 44.4, k + 1)
        for b in bulles:
            p.cercle('detail', *b, 'feuille')
        for b in bulles:
            p.cercle('detail', b[0], b[1], b[2] - 1.2, 'feuille-p')

    # ---- the spiral stair: the parapet, the steps, the twisted mirror core, the way up
    hx, hy, r0, r1 = 1082, 2172, 40, 179.5
    p.cercle('mobilier', hx, hy, r1, 'marche')
    for k in range(18):
        a = -55.5 + 21 * k
        p.ligne('mobilier', [(hx + r0 * math.cos(math.radians(a)), hy + r0 * math.sin(math.radians(a))),
                             (hx + r1 * math.cos(math.radians(a)), hy + r1 * math.sin(math.radians(a)))], 'fin')
    p.polys('poche', [arc(hx, hy, r1 + 5.5, 0, 360, 120), arc(hx, hy, r1 + 0.5, 360, 0, 120)], 'poche')
    p.cercle('mobilier', hx, hy, r0, 'meuble-g')
    p.poly('mobilier', [(hx + (30 + 7 * math.sin(2 * a + 0.9 * math.sin(3 * a))) * math.cos(a),
                         hy + (30 + 7 * math.sin(2 * a + 0.9 * math.sin(3 * a))) * math.sin(a))
                        for a in [2 * math.pi * k / 72 for k in range(72)]], 'miroir')
    rm = (r0 + r1) / 2 + 12
    montee = arc(hx, hy, rm, -45, 230, 60)
    p.ligne('detail', montee, 'haut')
    ax, ay = montee[-1]; bx, by = montee[-2]
    ang = math.atan2(ay - by, ax - bx)
    p.poly('detail', [(ax + 14 * math.cos(ang), ay + 14 * math.sin(ang)), (ax + 7 * math.cos(ang + 2.2), ay + 7 * math.sin(ang + 2.2)),
                      (ax + 7 * math.cos(ang - 2.2), ay + 7 * math.sin(ang - 2.2))], 'fleche')
    sx, sy = hx + rm * math.cos(math.radians(-45)), hy + rm * math.sin(math.radians(-45))
    p.cercle('detail', sx, sy, 5, 'fleche')

    # ---- the rock garden: gravel around the stair, a low curb, the rocks
    gravier = [(855, 2040), (912, 2046), (960, 2060), (1003, 2078), (1040, 2100)] + \
        [(1082 + 42 * math.cos(math.radians(a)), 2172 + 42 * math.sin(math.radians(a))) for a in range(240, -1, -15)] + \
        [(1262, 2172), (1273, 2368), (855, 2368)]
    p.poly('sol', gravier, 'gravier')
    p.ligne('detail', [(1273, 2368), (855, 2368), (855, 2040), (912, 2046), (960, 2060), (1003, 2078), (1040, 2100)], 'trait')
    rnd = random.Random(9)
    for x, y, sx_, sy_ in ((900, 2290, 0.55, 0.42), (935, 2335, 0.45, 0.38), (884, 2338, 0.24, 0.2), (922, 2088, 0.42, 0.34),
                           (1232, 2338, 0.34, 0.3), (1196, 2352, 0.2, 0.17), (880, 2152, 0.22, 0.2), (960, 2250, 0.18, 0.15)):
        rot = rnd.uniform(0, math.pi)
        pts = []
        for k in range(9):
            a = 2 * math.pi * k / 9 + rnd.uniform(-0.15, 0.15)
            ex, ey = sx_ / 2 / PX * math.cos(a) * rnd.uniform(0.85, 1.05), sy_ / 2 / PX * math.sin(a) * rnd.uniform(0.85, 1.05)
            pts.append((x + ex * math.cos(rot) - ey * math.sin(rot), y + ex * math.sin(rot) + ey * math.cos(rot)))
        p.poly('hachures', pts, 'rocher')       # under the stair, as in the model

    # ---- the entry: the concierge desk and console, the curtains, the coat rail, the door, the sideboard of the alcove
    p.rect('mobilier', 611, 2044, 723, 2096, 'meuble')
    p.poly('mobilier', [(611, 1908), (722, 1908)] + [(702 + 20 * math.cos(math.radians(a)), 1955 + 20 * math.sin(math.radians(a)))
                                                     for a in range(0, 91, 10)] + [(611, 1975)], 'meuble-g')
    for (x0, y0), (x1, y1), amp, onde, g in (((455, 1872), (600, 1872), 3.5, 0.20, 7), ((840, 2012), (840, 2100), 4.5, 0.12, 3),
                                             ((840, 2255), (840, 2348), 4.5, 0.12, 5)):
        L = math.hypot(x1 - x0, y1 - y0)
        tx, ty = (x1 - x0) / L, (y1 - y0) / L
        rnd = random.Random(g)
        ph = [rnd.uniform(0, 2 * math.pi) for _ in range(3)]
        pli = lambda u: (math.sin(2 * math.pi * u / onde + ph[0]) + 0.45 * math.sin(2 * math.pi * u * 2.1 / onde + ph[1])
                         + 0.3 * math.sin(2 * math.pi * u * 0.47 / onde + ph[2])) / 1.75
        pts = [(x0 + tx * L * k / 120 - ty * amp * 1.1 * pli(L * PX * k / 120), y0 + ty * L * k / 120 + tx * amp * 1.1 * pli(L * PX * k / 120))
               for k in range(121)]
        p.ligne('detail', pts, 'trait')
    p.ligne('haut', [(455, 1872), (600, 1872)], 'haut')
    p.ligne('haut', [(840, 2008), (840, 2352)], 'haut')
    p.rect('mobilier', 640, 2195, 646, 2398, 'meuble-g')                     # the coat rail
    p.rect('mobilier', 467, 2172, 593, 2243, 'meuble-g')                     # the sideboard of the alcove
    p.ligne('detail', arc(582, 2410, 58, 270, 360, 24), 'fin')               # the entry door
    p.ligne('detail', [(582, 2410), (582, 2352)], 'trait')
    p.rect('fond', 947, 2443, 1320, 2497, 'meuble-g')                         # the planter box on the street
    p.poly('detail', [(718, 2425), (690, 2470), (746, 2470)], 'fleche')       # the way in

    # ---- service rooms: toilets, the liquor store, the electrical panels, the lift shaft
    for x0, x1 in ((675, 722), (1075, 1122)):                                 # two WCs
        p.rect('mobilier', x0 + 2, 380, x1 - 2, 392, 'meuble')
        p.poly('mobilier', [(x0, 380)] + arc((x0 + x1) / 2, 352, (x1 - x0) / 2, 180, 360, 20) + [(x1, 380)], 'meuble')
    for yc in (276, 372):                                                     # two urinals
        p.poly('mobilier', [(895, yc - 21)] + arc(875, yc, 21, 270, 90, 20)[1:-1] + [(895, yc + 21)], 'meuble')
    p.poly('mobilier', [(a + 966, b + 378.5) for a, b in rrect(0, 0, 68, 47, 12)], 'meuble')
    p.cercle('mobilier', 966, 381, 3, 'trait')
    p.rect('mobilier', 652, 147, 712, 195, 'meuble')                         # the vanity of the men's toilet
    for x in (673, 683):
        p.cercle('mobilier', x, 217, 3.5, 'trait')
    p.rect('mobilier', 1336, 304, 1424, 631, 'meuble-g')                      # the electrical cabinet
    for y0, y1 in ((432, 484), (542, 597)):
        p.rect('mobilier', 1342.5, y0, 1346, y1, 'meuble')
    p.rect('detail', 1285, 1767, 1412, 2197, 'fin')                           # the lift car
    p.ligne('detail', [(1275, 1775), (1340, 1842)], 'trait')
    p.ligne('detail', arc(1275, 1775, 92, 45, 90, 12), 'fin')


LEGENDE = [(1, 'Entrée'), (2, 'Conciergerie'), (3, 'Salle'), (4, 'Gaine d’ascenseur'), (5, 'Bar'),
           (6, 'Réserve des alcools'), (7, 'Toilettes hommes'), (8, 'Toilettes femmes'), (9, 'Tableaux électriques')]
NUMEROS = [(1, 724, 2326), (2, 660, 2122), (3, 538, 1500), (3, 1188, 1500), (4, 1348, 1940), (5, 868, 560), (6, 530, 220),
           (7, 812, 205), (8, 962, 205), (9, 1384, 470)]
