# The first floor (the mezzanine, floor2.png), redrawn: the walls vectorised from the plan
# (outils/vectoriser_etage1.py -> modele/etage1-murs.json), the rest measured on gridded zooms of floor2.png.
# The void over the room shows what is below (the drums, the column, the rock garden) in light lines.
import json
import math
import random

from dessin import (PX, Plan, arc, chaise, fauteuil, rrect, R)

D = json.loads((R / 'modele' / 'etage1-murs.json').read_text())


def dessiner(p: Plan):
    # ---- floors; the void over the room (lighter), the void over the entry (hatched)
    p.poly('sol', [(384, 140), (1457, 140), (1457, 2245), (1286, 2245), (1286, 2213), (602, 2213), (602, 2245),
                   (232, 2245), (232, 842), (384, 842)], 'sol')
    vide = [(237, 1172), (1012, 1172)] + arc(1012, 1242, 70, -90, 0, 12) + [(1082, 1917)] + \
        arc(1020, 1917, 62, 0, 90, 12) + [(1000, 1990), (861, 2044), (861, 1896), (601, 1896), (601, 2245), (237, 2245)]
    p.poly('sol', vide, 'vide')
    p.rect('sol', 601, 1896, 856, 2373, 'hachure')
    # the rock garden under the stair
    gravier = [(861, 2044), (1057, 2044), (1057, 2126), (1238, 2126)] + arc(1238, 2187, 61, -90, 0, 10) + \
        [(1299, 2365), (861, 2365)]
    p.poly('sol', gravier, 'gravier')

    # ---- below, seen through the void: the drums of the ground floor, light lines
    for cy in (1312.7, 1718.9, 2022.4):
        p.cercle('hachures', 406, cy, 152, 'dessous')
        p.ligne('hachures', arc(406, cy, 131, 90, 270, 40), 'dessous-l')
        p.cercle('hachures', 394, cy - 4, 58, 'dessous-l')
    p.rect('hachures', 467, 2172, 593, 2243, 'dessous-l')

    # ---- walls, columns
    for m in D['murs']:
        p.polys('poche', [m['contour']] + m['trous'], 'poche')
    p.rect('poche', 200, 752, 401, 842, 'poche')                 # the outer wall by the lab
    p.rect('poche', 200, 842, 232, 2276, 'poche')
    p.rect('poche', 200, 2245, 602, 2276, 'poche')
    for c in D['poteaux']:
        cx, cy, r = (407.5, 801.5, 49.5) if c['id'] == 841 else (c['cx'], c['cy'], c['r'])
        p.cercle('poche', cx, cy, r, 'poche')

    # ---- glass-block facades and their steel mullions
    def facade(x, montants, w=4.5):
        for y0, y1 in zip(montants, montants[1:]):
            p.rect('vitrage', x - w, y0, x + w, y1, 'vitrage')
        for y in montants:
            p.rect('vitrage', x - w - 1.5, y - 2.5, x + w + 1.5, y + 2.5, 'poche')
    facade(417.5, [145, 281.5, 421, 560, 656, 750])
    facade(1450.5, [637, 741]); facade(1450.5, [851, 862, 972, 1094]); facade(1450.5, [1169, 1263.5, 1360, 1453])
    facade(1450.5, [1579, 1692, 1822.5, 1952, 2082.5, 2210])
    facade(238.5, [1172 + (2245 - 1172) * k / 9 for k in range(10)], w=4)

    # ---- the void's edge: the drinks ledge with its six stools, the glass parapet
    p.poly('mobilier', [(459.5, 1114.6), (1012, 1114.6)] + arc(1012, 1172, 57.4, -90, 0, 10) + [(459.5, 1172)], 'meuble-g')
    p.ligne('detail', [(237, 1176)] + [(1008, 1176)] + arc(1012, 1242, 66, -90, 0, 12) + [(1078, 1917)], 'trait')
    for x in (536.8, 608.5, 719.9, 792, 902.9, 975.6):
        for pts in chaise(x, 1080, (x, 1172)):
            p.poly('mobilier', pts, 'cuir')

    # ---- the long table: ten chairs, three feet
    p.rect('mobilier', 588, 802, 1106, 895, 'meuble')
    for x in (634, 714.5, 839.5, 974.5, 1054.5):
        for y, v in ((762.7, 848), (933, 848)):
            for pts in chaise(x, y, (x, v)):
                p.poly('mobilier', pts, 'cuir')
    for x in (681.5, 849, 1018):
        p.cercle('mobilier', x, 848.5, 4.8, 'trait')

    # ---- the two half drums: the shell, a banquette, a round table, two armchairs
    for cy in (770, 1031):
        cx = 1298.5
        p.poly('poche', arc(cx, cy, 125, -90, 90, 50) + arc(cx, cy, 110, 90, -90, 50), 'poche')
        for s in (-1, 1):
            p.rect('poche', 1281, cy + s * 110, cx, cy + s * 125, 'poche')
        p.poly('mobilier', [(1290, cy - 110)] + arc(cx, cy, 110, -90, 90, 40) + [(1290, cy + 110), (1290, cy + 60)] +
               arc(cx, cy, 60, 90, -90, 30) + [(1290, cy - 60)], 'cuir')
        p.ligne('mobilier', arc(cx, cy, 88, -90, 90, 30), 'fin')
        p.cercle('mobilier', cx, cy, 48, 'meuble')
        p.cercle('mobilier', cx, cy, 4.8, 'trait')
        for dy in (-45, 43):
            for pts in fauteuil(1232.5, cy + dy, (cx, cy)):
                p.poly('mobilier', pts, 'cuir')

    # ---- the tables along the right facade, against a planter of greenery around the column
    for y0, y1, chaises in ((1215, 1437.5, (1250, 1330, 1410)), (1604, 1750, (1637.5, 1717.5)), (1808, 1955, (1843.6, 1925))):
        for y in chaises:
            for pts in chaise(1245, y, (1333, y)):
                p.poly('mobilier', pts, 'cuir')
        p.rect('mobilier', 1286, y0, 1381, y1, 'meuble')
    jard = [(1387 - (10 * math.sin(math.pi * (y - 1460) / 112) if 1460 < y < 1572 else 0), y) for y in range(1172, 2007, 4)]
    dos = []
    for y in range(2006, 1171, -4):
        x = 1440
        if abs(y - 1515.3) < 70:
            x = min(x, 1476.2 - math.sqrt(70 ** 2 - (y - 1515.3) ** 2))
        dos.append((x, y))
    p.poly('mobilier', jard + dos, 'meuble-g')
    rnd = random.Random(12)
    for k in range(70):
        y = 1180 + (2000 - 1180) * k / 69 + rnd.uniform(-4, 4)
        if abs(y - 1515) < 62:
            continue
        p.cercle('detail', 1413 + rnd.uniform(-8, 8), y, rnd.uniform(9, 13), 'feuille')
    p.rect('mobilier', 1372, 2006, 1441, 2210, 'meuble-g')         # a cupboard

    # ---- the omakase bar: the bottle wall, the back counter, the bartenders' counter, the guests' counter, six stools
    p.rect('mobilier', 582, 260, 1125, 330, 'meuble-g')
    for k in range(24):
        x = 595 + (1110 - 595) * k / 23
        p.ligne('mobilier', [(x, 262), (x, 307)], 'fin')
    p.rect('mobilier', 582, 307, 1125, 330, 'meuble')
    p.rect('mobilier', 585, 447, 1125, 510, 'meuble')
    p.rect('mobilier', 586, 450, 648, 508, 'meuble-g')
    p.rect('mobilier', 1107, 470, 1117, 480, 'trait')
    p.rect('mobilier', 582, 510, 1177, 580, 'meuble')
    for x in (678.5, 750, 842.5, 914, 998.5, 1071):
        for pts in chaise(x, 615, (x, 560)):
            p.poly('mobilier', pts, 'cuir')
    p.rect('detail', 1140, 511, 1188, 557, 'fin')

    # ---- the curtains (wavy lines of the plan)
    for (x0, y0), (x1, y1), g in (((427, 287), (570, 287), 4), ((1177, 555), (1295, 610), 6)):
        L = math.hypot(x1 - x0, y1 - y0); tx, ty = (x1 - x0) / L, (y1 - y0) / L
        rnd = random.Random(g); ph = [rnd.uniform(0, 2 * math.pi) for _ in range(3)]
        pli = lambda u: (math.sin(2 * math.pi * u / 0.14 + ph[0]) + 0.45 * math.sin(2 * math.pi * u * 2.1 / 0.14 + ph[1])) / 1.45
        p.ligne('detail', [(x0 + tx * L * k / 120 - ty * 5 * pli(L * PX * k / 120), y0 + ty * L * k / 120 + tx * 5 * pli(L * PX * k / 120))
                           for k in range(121)], 'trait')

    # ---- the straight stair up to the second floor
    p.rect('mobilier', 485, 140, 852, 247, 'marche')
    for k in range(8):
        x = 572 + 35 * k
        p.ligne('mobilier', [(x, 140), (x, 247)], 'fin')
    p.ligne('detail', [(500, 193.5), (790, 193.5)], 'haut')
    p.poly('detail', [(804, 193.5), (788, 186), (788, 201)], 'fleche')
    p.cercle('detail', 500, 193.5, 5, 'fleche')

    # ---- the spiral stair arriving from the ground floor
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
    descente = arc(hx, hy, 140, -14, 255, 60)
    p.ligne('detail', descente, 'haut')
    ax, ay = descente[-1]; bx, by = descente[-2]
    ang = math.atan2(ay - by, ax - bx)
    p.poly('detail', [(ax + 14 * math.cos(ang), ay + 14 * math.sin(ang)), (ax + 7 * math.cos(ang + 2.2), ay + 7 * math.sin(ang + 2.2)),
                      (ax + 7 * math.cos(ang - 2.2), ay + 7 * math.sin(ang - 2.2))], 'fleche')
    p.cercle('detail', *descente[0], 5, 'fleche')

    # ---- service rooms: the lab, the toilets, the lift shaft
    p.rect('mobilier', 400, 872, 471, 1080, 'meuble-g')            # the lab's counter and its machines
    for y in (925, 979, 1024.6):
        p.ligne('mobilier', [(400, y), (471, y)], 'fin')
    p.rect('mobilier', 416, 886, 426, 896, 'trait')
    p.cercle('mobilier', 431.5, 895, 4.5, 'trait')
    p.cercle('mobilier', 418, 991.5, 4, 'trait')
    p.cercle('mobilier', 429, 1050, 9, 'trait')
    p.rect('sol', 1132, 142, 1425, 247, 'carrelage')               # the toilets: tiled floor, a vanity, a WC
    p.rect('mobilier', 1225, 142, 1315, 172, 'meuble')
    p.poly('mobilier', [(a + 1270, b + 157) for a, b in rrect(0, 0, 42, 20, 7)], 'meuble')
    p.rect('mobilier', 1358, 142, 1394, 152, 'meuble')
    p.poly('mobilier', [(1355, 152)] + arc(1376, 165, 21, 180, 0, 20)[::-1][::-1] + [(1397, 152)], 'meuble')
    p.rect('detail', 1342, 297, 1430, 625, 'fin')                  # the lift shaft
    p.ligne('detail', [(1342, 297), (1430, 625)], 'fin')
    p.ligne('detail', [(1430, 297), (1342, 625)], 'fin')
    p.texte(700, 1560, 'VIDE SUR LA SALLE', 'lbl')


LEGENDE = [(1, 'Salle'), (2, 'Laboratoire'), (3, 'Bar omakase'), (4, 'Gaine d’ascenseur'), (5, 'Toilettes')]
NUMEROS = [(1, 845, 1030), (1, 1165, 1540), (2, 320, 990), (3, 853, 541), (4, 1394, 450), (5, 1180, 205)]
