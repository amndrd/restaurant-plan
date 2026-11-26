# The final plans of the two floors, drawn from the model (26/11): an architect's plan, not a picture of the model.
# It reads the model cut at 1.20 m (modele/trace/<etage>.json, written by outils/blender/plan_modele.py through
# floor1.py / floor2.py `trace=`), keeps what an architect draws, and lays it out on an A2 sheet at 1:50:
#   - the cut walls and columns in black, the drums in dark grey, the low walls in outline;
#   - the glazing, the glass blocks and their steel frames, as cut;
#   - the fixed elements and the furniture seen from above, in fine lines, painted from the lowest to the highest;
#     no small objects (bottles, glasses, cups, pots, utensils, cartons, lamps, stock…);
#   - above the cut, dashed: the hood, the soffit over the bar, the edge of the mezzanine over the ground floor;
#   - the doors drawn open at 90 degrees with their swing, the spiral stair with its cut line and walking line;
#   - the column grid, the overall dimensions, the rooms with their areas, the levels, a scale bar, a title block.
# The drawing is turned like the map's top view (the bar on the left, the street on the right) and both sheets share
# the same frame, so that the two can be laid one over the other in the site's film.
# Writes rendus/26-plans-finaux/<etage>.svg, .png (300 dpi) and .pdf.
# usage: outils/.venv/bin/python outils/plans/plan_final.py [rdc] [etage1]
import base64
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import LineString, Point, Polygon, box

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / 'outils' / 'blender'))
import refonte  # noqa: E402  (plain data, no Blender)

OUT = R / 'rendus' / '26-plans-finaux'
PX_M = 120.0                                  # plan pixels per metre
COUPE = 1.2

# ---------------------------------------------------------------- the sheet: A2 landscape, 1:50
W_MM, H_MM = 594.0, 420.0
DPI = 300
S = 1000.0 / PX_M / 50.0                      # mm on paper per plan pixel at 1:50
CXP, CYP = 840.0, 1228.0                      # the plan point at the centre of the drawing area
OX, OY = 238.0, 206.0                         # its place on the sheet (mm)
CART = 466.0                                  # the title block's left edge


def ecran(x, y):
    """Plan pixels -> sheet mm, turned like the map's top view: plan +x up, plan +y to the right."""
    return OX + (y - CYP) * S, OY - (x - CXP) * S


def f(v):
    return f'{v:.2f}'.rstrip('0').rstrip('.')


# ---------------------------------------------------------------- reading the model's trace
def tris(fl):
    a = np.asarray(fl, float).reshape(-1, 3, 2)
    ps = shapely.polygons(np.concatenate([a, a[:, :1]], axis=1))
    ps = ps[shapely.area(ps) > 1e-4]
    if not len(ps):
        return None
    g = shapely.union_all(ps, grid_size=0.01)
    return None if g.is_empty else g


def coupe(seg):
    """The section of a part: its closed rings, filled even-odd, and its open lines (a pane, a curtain)."""
    a = np.asarray(seg, float).reshape(-1, 2, 2)
    m = shapely.line_merge(shapely.union_all(shapely.linestrings(a), grid_size=0.01))
    pleins, lignes = None, []
    for l in shapely.get_parts(m):
        if l.is_ring and len(l.coords) > 3:
            p = Polygon(l.coords)
            if p.is_valid and p.area > 0.01:
                pleins = p if pleins is None else pleins.symmetric_difference(p)
        else:
            lignes.append(l)
    return pleins, lignes


# ---------------------------------------------------------------- what an architect draws, and what not
# small objects, stock and the closed door leaves (the doors are drawn open, as symbols); the stair (as a symbol)
EXCLURE = re.compile(
    r'bouteille|verres|bocaux|cartons|caisses|poignee|escabeau|^lampe|^suspension|tapis|manteaux|parapluies|'
    r'cave-echelle|jardin-spot|lumieres|station-plateaux|labo-batteur|labo-cloche|labo-lames|accueil-lames|'
    r'omakase-vitrines|omakase-lames|omakase-casiers|^porte-\d|cave-porte|cuisine-porte|wc-porte|reserve-est-porte|'
    r'bar-portillon|wc-miroir|^sol$|^sol-clair$|escalier-marches|cuisine-bocaux|cuisine-etagere|-joints$|'
    r'repose-pieds-pattes|arriere-bar-haut|^ile-terre|vestiaire-banc-pieds|accueil-banc-pieds|reserve-est-poignees')
# within an element made of several materials: the materials that are its small things
EXCLURE_MAT = {
    'cuisine-ligne': {'acier', 'bois', 'plateau', 'ceramique', 'verre', 'lumiere'},
    'cuisine-froid': {'acier', 'comptoir', 'lumiere'},
    'cuisine-reserve': {'acier', 'meuble', 'ceramique'},
    'cuisine-comptoir': {'acier', 'ceramique', 'terre', 'plateau', 'bois'},
    'cuisine-plonge': {'acier', 'ceramique'},
    'arriere-bar': {'acier', 'ceramique', 'verre'},
    'service': {'acier', 'comptoir', 'verre', 'ceramique'},
    'bar': {'ceramique', 'acier'},
    'wc': {'miroir'},
}
# above the cut: drawn dashed (the hood, the soffit over the bar)
TIRETS = {'cuisine-ligne-inox', 'cuisine-retombee', 'cuisine-retombee-mur', 'cuisine-equipements'}


def lot(o, m):
    return o[:-(len(m) + 1)] if o.endswith('-' + m) else o


def classe(p):
    """The drawing's layer of a traced part, or None."""
    o, m, cs = p['o'], p['m'], p['c']
    if 'Dessous' in cs or EXCLURE.search(o):
        return None
    if m in EXCLURE_MAT.get(lot(o, m), ()):
        return None
    if o == 'cuisine-sol-ceramique':
        return 'carreaux'
    if o.startswith('gravier-ratisse'):
        return 'ratisse'
    if o == 'gravier':
        return 'gravier'
    if 'Sols' in cs or o == 'dalle':
        return None
    if 'Coque' in cs:
        return 'mur'
    if m == 'tambour':
        return 'tambour'
    if m == 'pave':
        return 'paves'
    if m == 'verre':
        return 'verre'
    if m == 'cadre' or o.startswith('escalier-garde-corps'):
        return 'cadre'
    if m == 'rideau':
        return 'rideau'
    if m == 'feuillage':
        return 'plante'
    return 'meuble'


def petit(g, p):
    """A small thing on its own: under 25 cm2 seen from above, or round and under 120 cm2 (a bottle, a pot, a cup),
    but the burners of the range and its kind, flush with a worktop, stay."""
    a = g.area / PX_M ** 2
    if a < 0.0025:
        return True
    c = g.centroid
    rmax = max(Point(xy).distance(c) for xy in shapely.get_coordinates(g)) or 1
    rond = g.area / (math.pi * rmax * rmax) > 0.8
    if rond and a < 0.012 and not (p['m'] == 'comptoir' and 0.88 <= p['z0'] <= 0.95):
        return True
    if rond and a < 0.1 and p['z0'] >= 0.88 and p['m'] != 'comptoir':    # set on a worktop: a pot, a bowl, a cup
        return True
    return False


def lire(etage):
    d = json.load(open(R / 'modele' / 'trace' / f'{etage}.json'))
    calques = {k: [] for k in ('carreaux', 'gravier', 'ratisse', 'meuble', 'plante', 'mur', 'muret', 'tambour',
                               'paves', 'verre', 'cadre', 'rideau', 'tirets', 'coupe-meuble', 'seuil')}
    sol = []
    for p in d['parties']:
        o = p['o']
        if 'Dessous' in p['c']:
            continue
        if o in ('sol', 'sol-clair', 'dalle') or (o == 'gravier' and 'Sols' in p['c']):
            g = tris(p['bas'])
            if g is not None:
                sol.append(g)
        k = classe(p)
        if k is None:
            continue
        if k == 'plante':                                     # a crown: its silhouette, whatever the cut
            g = tris(p['bas'])
            if g is not None:
                calques['plante'].append((g, p))
            continue
        if p['seg']:
            pleins, lignes = coupe(p['seg'])
            if k == 'meuble':
                k2 = 'coupe-meuble'
            elif k == 'rideau':
                calques['rideau'] += lignes + ([pleins.boundary] if pleins is not None else [])
                continue
            else:
                k2 = k
            if pleins is not None and not pleins.is_empty and not (k2 == 'coupe-meuble' and petit(pleins, p)):
                calques[k2].append((pleins, p))
            if lignes and k in ('verre', 'cadre'):
                calques['verre'] += [(l.buffer(0.6), p) for l in lignes]
            continue
        if p['bas']:
            g = tris(p['bas'])
            if g is None:
                continue
            if k == 'mur':
                k = 'muret'                                   # below the cut: a low wall, a threshold
            if k == 'cadre':
                k = 'seuil'
            if k in ('meuble', 'seuil', 'verre') and petit(g, p):
                continue
            calques[k if k in calques else 'meuble'].append((g, p))
        elif p['haut'] and o in TIRETS and p['z0'] >= 1.4:
            g = tris(p['haut'])
            if g is not None:
                calques['tirets'].append((g, p))
    sol = shapely.union_all(sol, grid_size=0.01) if sol else None
    return calques, sol


# ---------------------------------------------------------------- SVG
def d_poly(g):
    out = []
    for q in shapely.get_parts(g):
        if q.geom_type != 'Polygon' or q.is_empty:
            continue
        for r in [q.exterior, *q.interiors]:
            c = [ecran(x, y) for x, y in r.coords]
            out.append('M' + ' L'.join(f'{f(X)},{f(Y)}' for X, Y in c) + 'Z')
    return ' '.join(out)


def d_ligne(l):
    out = []
    for q in shapely.get_parts(l):
        if q.geom_type == 'Polygon':
            out.append(d_poly(q)); continue
        c = [ecran(x, y) for x, y in q.coords]
        if len(c) > 1:
            out.append('M' + ' L'.join(f'{f(X)},{f(Y)}' for X, Y in c))
    return ' '.join(out)


def polices():
    pol = R / 'outils' / 'pages' / 'polices'
    return ''.join(f'@font-face{{font-family:"Inter";font-weight:{w};src:url(data:font/woff2;base64,'
                   f'{base64.b64encode((pol / f"inter-latin-{w}-normal.woff2").read_bytes()).decode()}) format("woff2")}}'
                   for w in (400, 500, 600))


ENCRE = '#161616'
STYLE = f'''
text{{font-family:Inter,sans-serif;fill:{ENCRE}}}
.mur{{fill:{ENCRE};stroke:{ENCRE};stroke-width:.1}}
.tambour{{fill:#4a4a48;stroke:{ENCRE};stroke-width:.18}}
.muret{{fill:#e3e2de;stroke:{ENCRE};stroke-width:.25}}
.paves{{fill:#eef1f2;stroke:#3a3a3a;stroke-width:.06}}
.verre{{fill:#fff;stroke:{ENCRE};stroke-width:.13}}
.cadre{{fill:#2a2a2a;stroke:none}}
.seuil{{fill:none;stroke:#555;stroke-width:.1}}
.meuble{{fill:#fff;stroke:#222;stroke-width:.13;stroke-linejoin:round}}
.coupe-meuble{{fill:#f1f0ec;stroke:{ENCRE};stroke-width:.3;stroke-linejoin:round}}
.plante{{fill:#f3f4f1;stroke:#5b5f57;stroke-width:.12}}
.carreaux{{fill:none;stroke:#bdbcb7;stroke-width:.06}}
.gravier{{fill:url(#gravier);stroke:#777;stroke-width:.1}}
.ratisse{{fill:none;stroke:#a5a49f;stroke-width:.07}}
.rideau{{fill:none;stroke:#333;stroke-width:.2;stroke-linecap:round;stroke-linejoin:round}}
.tirets{{fill:none;stroke:#333;stroke-width:.18;stroke-dasharray:1.6 .9}}
.tirets-fins{{fill:none;stroke:#555;stroke-width:.13;stroke-dasharray:1.2 .8}}
.porte{{fill:none;stroke:{ENCRE};stroke-width:.25}}
.arc{{fill:none;stroke:#333;stroke-width:.1}}
.arc-t{{fill:none;stroke:#555;stroke-width:.1;stroke-dasharray:.8 .6}}
.marche{{fill:none;stroke:#222;stroke-width:.13}}
.marche-t{{fill:none;stroke:#555;stroke-width:.12;stroke-dasharray:1 .7}}
.ligne-foulee{{fill:none;stroke:{ENCRE};stroke-width:.18}}
.axe{{fill:none;stroke:#8a8a86;stroke-width:.1;stroke-dasharray:6 1 .6 1}}
.bulle{{fill:#fff;stroke:{ENCRE};stroke-width:.25}}
.cote{{fill:none;stroke:#333;stroke-width:.1}}
.cote-t{{fill:none;stroke:#333;stroke-width:.25}}
.vide{{fill:none;stroke:#444;stroke-width:.12}}
.cadre-feuille{{fill:none;stroke:{ENCRE};stroke-width:.5}}
.filet{{fill:none;stroke:{ENCRE};stroke-width:.18}}
.vegetal{{fill:url(#vegetal);stroke:#5b5f57;stroke-width:.12}}
'''
DEFS = '''<defs>
<pattern id="gravier" width="1.2" height="1.2" patternUnits="userSpaceOnUse">
<circle cx=".3" cy=".35" r=".09" fill="#8f8e89"/><circle cx=".9" cy=".25" r=".06" fill="#a3a29c"/>
<circle cx=".7" cy=".85" r=".1" fill="#96958f"/><circle cx=".15" cy=".95" r=".05" fill="#a9a8a2"/></pattern>
<pattern id="vegetal" width="3" height="3" patternUnits="userSpaceOnUse">
<rect width="3" height="3" fill="#f4f5f2"/>
<path d="M.4 1.2 q.5 -.7 1 0 M1.7 2.6 q.5 -.7 1 0 M1.9 .6 q.4 -.55 .8 0 M.2 2.6 q.35 -.5 .7 0" fill="none" stroke="#6b7066" stroke-width=".09"/></pattern>
</defs>'''


class Feuille:
    def __init__(self):
        self.el = []

    def add(self, s):
        self.el.append(s)

    def path(self, d, cls, extra=''):
        if d:
            self.add(f'<path class="{cls}" d="{d}" {extra}/>')

    def texte(self, X, Y, t, taille, poids=400, ancre='middle', couleur=None, ls=0, extra=''):
        t = t.replace('&', '&amp;').replace('<', '&lt;')
        c = f' fill="{couleur}"' if couleur else ''
        l = f' letter-spacing="{ls}"' if ls else ''
        self.add(f'<text x="{f(X)}" y="{f(Y)}" font-size="{taille}" font-weight="{poids}" text-anchor="{ancre}"'
                 f'{c}{l} {extra}>{t}</text>')

    def svg(self, w_px, h_px):
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w_px}" height="{h_px}" viewBox="0 0 {W_MM} {H_MM}">'
                f'<style>{polices()}{STYLE}</style>{DEFS}<rect width="{W_MM}" height="{H_MM}" fill="#fff"/>'
                f'{"".join(self.el)}</svg>')


# ---------------------------------------------------------------- symbols: doors, stairs, grid, dimensions, labels
def porte(F, charniere, bout, cote_, va_et_vient=False):
    """A door leaf open at 90 degrees from its closed position (charniere -> bout), towards the side `cote_` (a plan
    vector), with its swing; a double-action door also gets its swing on the other side, dashed."""
    hx, hy = charniere
    vx, vy = bout[0] - hx, bout[1] - hy
    for signe, cls in ((1, 'arc'), (-1, 'arc-t')) if va_et_vient else ((1, 'arc'),):
        ox_, oy_ = -vy, vx                                    # the leaf turned a quarter
        if (ox_ * cote_[0] + oy_ * cote_[1]) * signe < 0:
            ox_, oy_ = vy, -vx
        o = (hx + ox_, hy + oy_)
        A, B, C = ecran(*charniere), ecran(*bout), ecran(*o)
        r = math.hypot(B[0] - A[0], B[1] - A[1])
        cross = (B[0] - A[0]) * (C[1] - A[1]) - (B[1] - A[1]) * (C[0] - A[0])
        F.add(f'<path class="{cls}" d="M{f(B[0])},{f(B[1])} A{f(r)},{f(r)} 0 0 {1 if cross > 0 else 0} {f(C[0])},{f(C[1])}"/>')
        if signe == 1:
            F.add(f'<path class="porte" d="M{f(A[0])},{f(A[1])} L{f(C[0])},{f(C[1])}"/>')


def escalier(F, etage, H=3.35):
    """The spiral stair (floor1.py: hub (1082, 2172), treads from r 40 to 180 px, 19 risers of 21 degrees from -55.5,
    clockwise on the plan). Ground floor: the treads under the cut solid, the cut line, the rest dashed, the walking
    line up to the cut with its arrow. 1st floor: the treads seen down the opening, the walking line down."""
    cx, cy, r0, r1, n, pas, a0 = 1082, 2172, 40, 180, 19, 21.0, -55.5
    mont = H / n
    def pt(r, a):
        return ecran(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
    def rayon(a, cls):
        A, B = pt(r0, a), pt(r1, a)
        F.add(f'<path class="{cls}" d="M{f(A[0])},{f(A[1])} L{f(B[0])},{f(B[1])}"/>')
    def arc_(r, a_, b_, cls, nseg=40):
        pts = [pt(r, a_ + (b_ - a_) * k / nseg) for k in range(nseg + 1)]
        F.add(f'<path class="{cls}" d="M' + ' L'.join(f'{f(X)},{f(Y)}' for X, Y in pts) + '"/>')
    if etage == 'rdc':
        k_coupe = int(COUPE // mont)                          # the treads under the cut: 0 .. k_coupe - 1
        a_coupe = a0 + pas * (k_coupe + 0.5)
        for k in range(k_coupe + 1):
            rayon(a0 + pas * k, 'marche')
        for k in range(k_coupe + 1, 18):
            rayon(a0 + pas * k, 'marche-t')
        arc_(r1, a0, a_coupe, 'marche')
        arc_(r1, a_coupe, a0 + 360, 'marche-t')
        # the cut line: a break across the treads
        A, B = pt(r0 - 6, a_coupe - 4), pt(r1 + 8, a_coupe + 4)
        mx, my = (A[0] + B[0]) / 2, (A[1] + B[1]) / 2
        nx, ny = -(B[1] - A[1]), B[0] - A[0]
        nn = math.hypot(nx, ny)
        nx, ny = nx / nn * 1.6, ny / nn * 1.6
        F.add(f'<path class="ligne-foulee" d="M{f(A[0])},{f(A[1])} L{f(mx - (B[0]-A[0])*.06 + nx)},{f(my - (B[1]-A[1])*.06 + ny)} '
              f'L{f(mx + (B[0]-A[0])*.06 - nx)},{f(my + (B[1]-A[1])*.06 - ny)} L{f(B[0])},{f(B[1])}"/>')
        # the walking line, from the first tread to the cut, its start dot and its arrow
        rf = (r0 + r1) / 2 + 8
        arc_(rf, a0 + 6, a_coupe - 4, 'ligne-foulee')
        P0 = pt(rf, a0 + 6)
        F.add(f'<circle cx="{f(P0[0])}" cy="{f(P0[1])}" r=".55" fill="{ENCRE}"/>')
        fleche(F, pt(rf, a_coupe - 10), pt(rf, a_coupe - 4))
        Q = pt(rf - 34, a0 + 30)
        F.texte(Q[0], Q[1], '19 × 17,6', 1.7, 500, extra='')
    else:
        for k in range(1, 19):
            rayon(a0 + pas * k, 'marche')
        arc_(r1, a0 + pas, a0 + pas * 18, 'marche')
        rf = (r0 + r1) / 2 + 8
        a_fin = a0 + pas * 18
        arc_(rf, a_fin - 4, a_fin - 150, 'ligne-foulee')
        P0 = pt(rf, a_fin - 4)
        F.add(f'<circle cx="{f(P0[0])}" cy="{f(P0[1])}" r=".55" fill="{ENCRE}"/>')
        fleche(F, pt(rf, a_fin - 144), pt(rf, a_fin - 150))
    C = pt(0, 0)
    F.add(f'<circle cx="{f(C[0])}" cy="{f(C[1])}" r="{f(r0 * S)}" class="marche"/>')


def fleche(F, A, B, t=1.6):
    dx, dy = B[0] - A[0], B[1] - A[1]
    n = math.hypot(dx, dy) or 1
    ux, uy = dx / n, dy / n
    p1 = (B[0] - ux * t + uy * t * 0.42, B[1] - uy * t - ux * t * 0.42)
    p2 = (B[0] - ux * t - uy * t * 0.42, B[1] - uy * t + ux * t * 0.42)
    F.add(f'<path d="M{f(B[0])},{f(B[1])} L{f(p1[0])},{f(p1[1])} L{f(p2[0])},{f(p2[1])} Z" fill="{ENCRE}"/>')


def cote_h(F, ys, Y, ecrire=True):
    """A horizontal dimension chain on the sheet (plan y values), at sheet height Y."""
    Xs = [ecran(CXP, y)[0] for y in ys]
    F.add(f'<path class="cote" d="M{f(Xs[0] - 2)},{f(Y)} L{f(Xs[-1] + 2)},{f(Y)}"/>')
    for X in Xs:
        F.add(f'<path class="cote-t" d="M{f(X - .9)},{f(Y + .9)} L{f(X + .9)},{f(Y - .9)}"/>')
        F.add(f'<path class="cote" d="M{f(X)},{f(Y - 2)} L{f(X)},{f(Y + 2)}"/>')
    if ecrire:
        for a, b, ya, yb in zip(Xs, Xs[1:], ys, ys[1:]):
            F.texte((a + b) / 2, Y - 1.1, f'{(yb - ya) / PX_M:.2f}'.replace('.', ','), 2.0, 500)


def cote_v(F, xs, X, ecrire=True):
    """A vertical dimension chain on the sheet (plan x values), at sheet abscissa X."""
    Ys = [ecran(x, CYP)[1] for x in xs]
    F.add(f'<path class="cote" d="M{f(X)},{f(Ys[0] + 2)} L{f(X)},{f(Ys[-1] - 2)}"/>')
    for Y in Ys:
        F.add(f'<path class="cote-t" d="M{f(X - .9)},{f(Y + .9)} L{f(X + .9)},{f(Y - .9)}"/>')
        F.add(f'<path class="cote" d="M{f(X - 2)},{f(Y)} L{f(X + 2)},{f(Y)}"/>')
    if ecrire:
        for a, b, xa, xb in zip(Ys, Ys[1:], xs, xs[1:]):
            F.texte(X - 1.1, (a + b) / 2, f'{abs(xb - xa) / PX_M:.2f}'.replace('.', ','), 2.0, 500,
                    extra=f'transform="rotate(-90 {f(X - 1.1)} {f((a + b) / 2)})"')


def piece(F, x, y, nom, aire=None, petite=False):
    X, Y = ecran(x, y)
    t = 2.0 if petite else 2.6
    F.texte(X, Y, nom, t, 600, ls=0.25)
    if aire is not None:
        F.texte(X, Y + t * 1.15, f'{aire:.1f} m²'.replace('.', ','), t * 0.78, 400, couleur='#555')


def niveau(F, x, y, txt):
    X, Y = ecran(x, y)
    F.add(f'<path d="M{f(X - 1.4)},{f(Y - 2.4)} L{f(X + 1.4)},{f(Y - 2.4)} L{f(X)},{f(Y)} Z" fill="none" '
          f'stroke="{ENCRE}" stroke-width=".18"/><path d="M{f(X)},{f(Y)} L{f(X)},{f(Y - 2.4)} L{f(X + 1.4)},{f(Y - 2.4)} Z" '
          f'fill="{ENCRE}"/><path class="filet" d="M{f(X - 1.4)},{f(Y - 2.4)} L{f(X + 9)},{f(Y - 2.4)}"/>')
    F.texte(X + 2.0, Y - 3.1, txt, 1.9, 500, ancre='start')


# ---------------------------------------------------------------- the two floors
COL_X = [(405.1, '1'), (1477.5, '2')]         # the column grid: the ground floor's columns (floor1-murs.json)
COL_Y = [(805.4, 'A'), (1516.6, 'B')]


def rect(x0, y0, x1, y1):
    return box(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))


PIECES = {
    # name, label point (plan px), area polygon (None: the label only); the dining room takes the rest of the floor
    'rdc': [
        ('CUISINE', (930, 300), rect(*refonte.KITCHEN)),
        ('WC PMR', (470, 250), rect(*refonte.WC)),
        ('DÉGAGEMENT', (470, 600), rect(387, 362, 640, 470).union(rect(387, 470, 580, 760))),
        ('BAR', (880, 560), rect(580, 470, 1194, 760)),
        ('SERVICE', (1320, 560), rect(*refonte.SERVICE)),
        ('CAVE À VIN', (1360, 2060), rect(*refonte.CAVE)),
        ('VESTIAIRE', (1378, 2338), rect(*refonte.VESTIAIRE)),
        ('ENTRÉE', (790, 2265), rect(576, 1990, 861, 2406)),
        ('JARDIN SEC', (980, 2320), Polygon([(855, 2040), (912, 2046), (960, 2060), (1003, 2078), (1040, 2100),
                                             (1262, 2172), (1273, 2368), (855, 2368)])),
        ('SALLE', (840, 1500), 'reste'),
    ],
    'etage1': [
        ('BAR OMAKASE', (860, 520), rect(396, 247, 1180, 600)),
        ('CUISINE', (500, 300), rect(396, 140, 600, 434)),
        ('RÉSERVE', (850, 228), rect(600, 140, 1093, 257)),
        ('WC', (1345, 200), rect(1300, 140, 1458, 248)),
        ('RÉSERVE', (1395, 445), rect(1333, 260, 1458, 626)),
        ('LABORATOIRE', (300, 960), rect(232, 842, 400, 1172)),
        ('JARDIN SUSPENDU', (731, 2150), rect(601, 1896, 861, 2403)),
        ('SALLE', (1180, 900), 'reste'),
    ],
}
TITRES = {'rdc': ('Plan du rez-de-chaussée', '±0,00', 'A-101'), 'etage1': ('Plan de l’étage', '+3,35', 'A-102')}


def dessiner(etage):
    calques, sol = lire(etage)
    F = Feuille()
    # ---- the frame of the sheet
    F.add(f'<rect class="cadre-feuille" x="10" y="10" width="{W_MM - 20}" height="{H_MM - 20}"/>')
    F.add(f'<path class="filet" d="M{CART},10 L{CART},{H_MM - 10}"/>')
    # ---- the grid's lines, under everything
    murs = shapely.union_all([g for g, _ in calques['mur']], grid_size=0.01)
    x0b, y0b, x1b, y1b = murs.bounds
    for x, nom in COL_X:
        A, B = ecran(x, y0b - 60), ecran(x, y1b + 60)
        F.path(f'M{f(A[0])},{f(A[1])} L{f(B[0])},{f(B[1])}', 'axe')
    for y, nom in COL_Y:
        A, B = ecran(x0b - 60, y), ecran(x1b + 60, y)
        F.path(f'M{f(A[0])},{f(A[1])} L{f(B[0])},{f(B[1])}', 'axe')
    # ---- floors, finishes
    for g, _ in calques['carreaux']:
        F.path(d_poly(g), 'carreaux')
    for g, _ in calques['gravier']:
        F.path(d_poly(g), 'gravier')
    for g, _ in calques['ratisse']:
        F.path(d_poly(g), 'ratisse')
    # ---- the furniture and fixed elements under the cut, from the lowest to the highest
    for g, p in calques['meuble']:
        if p['m'] == 'pot' and (p['o'].startswith('jardiniere') or p['o'].startswith('accueil-olivier')):
            c = g.centroid
            calques['plante'].append((couronne(c.x, c.y, 0.55 if p['o'].startswith('jardiniere') else 0.45),
                                      dict(p, z1=1.19, m='feuillage')))
    meubles = [(g, p, k) for k in ('meuble', 'plante', 'muret', 'seuil') for g, p in calques[k]]
    meubles += [(g, p, 'verre') for g, p in calques['verre'] if not p['seg']]
    for g, p, k in sorted(meubles, key=lambda t: (min(t[1]['z1'], COUPE), -t[0].area)):
        F.path(d_poly(g), k)
    if etage == 'etage1':                                     # the planted island over the entry, inside its planter
        ile = rect(601, 1896, 861, 2403).intersection(sol.buffer(1)).buffer(-4)
        F.path(d_poly(ile), 'vegetal')
    # ---- what stands above the cut, dashed: the hood, the soffit; on the ground floor, the mezzanine's edge
    for g, _ in calques['tirets']:
        F.path(d_ligne(g.boundary), 'tirets')
    if etage == 'rdc':
        dalle = dalle_etage()
        if dalle is not None:
            for q in shapely.get_parts(dalle):
                for r in q.interiors:
                    if Polygon(r).area > 2000:
                        F.path(d_ligne(LineString(r.coords)), 'tirets-fins')
    # ---- the sections: cut furniture, curtains, glass blocks, glazing, frames, drums, walls
    for g, _ in calques['coupe-meuble']:
        F.path(d_poly(g), 'coupe-meuble')
    for l in calques['rideau']:
        F.path(d_ligne(l), 'rideau')
    for g, _ in calques['paves']:
        F.path(d_poly(g), 'paves')
    for g, p in calques['verre']:
        if p['seg']:
            F.path(d_poly(g), 'verre')
    for g, _ in calques['cadre']:
        F.path(d_poly(g), 'cadre')
    tamb = [g for g, _ in calques['tambour']]
    if tamb:
        F.path(d_poly(shapely.union_all(tamb, grid_size=0.01)), 'tambour')
    F.path(d_poly(murs), 'mur')
    # ---- the void on the 1st floor: its edge, a cross, its name
    if etage == 'etage1' and sol is not None:
        tremie = Point(1082, 2172).buffer(196, 64)            # the stair's opening: drawn by its stair, no cross
        for q in shapely.get_parts(sol):
            for r in q.interiors:
                v = Polygon(r).difference(tremie)
                if v.area < 20000:
                    continue
                for v_ in shapely.get_parts(v):
                    if v_.area < 20000:
                        continue
                    vx0, vy0, vx1, vy1 = v_.bounds
                    for a, b in (((vx0, vy0), (vx1, vy1)), ((vx0, vy1), (vx1, vy0))):
                        F.path(d_ligne(LineString([a, b]).intersection(v_.buffer(-8))), 'vide')
    # ---- doors and stairs
    for args in PORTES[etage]:
        porte(F, *args)
    escalier(F, etage)
    # ---- the grid's bubbles, the dimensions
    for x, nom in COL_X:
        for y in (y0b - 60, y1b + 60):
            X, Y = ecran(x, y)
            X += -3.4 if y < y0b else 3.4
            F.add(f'<circle class="bulle" cx="{f(X)}" cy="{f(Y)}" r="3.4"/>')
            F.texte(X, Y + 1.0, nom, 2.8, 600)
    for y, nom in COL_Y:
        for x in (x0b - 60, x1b + 60):
            X, Y = ecran(x, y)
            Y += 3.4 if x < x0b else -3.4
            F.add(f'<circle class="bulle" cx="{f(X)}" cy="{f(Y)}" r="3.4"/>')
            F.texte(X, Y + 1.0, nom, 2.8, 600)
    yb = ecran(x0b, 0)[1]
    cote_h(F, [y0b] + [y for y, _ in COL_Y] + [y1b], yb + 22)
    cote_h(F, [y0b, y1b], yb + 30)
    xg = ecran(0, y0b)[0]
    cote_v(F, [x0b] + [x for x, _ in COL_X] + [x1b], xg - 22)
    cote_v(F, [x0b, x1b], xg - 30)
    # ---- rooms, areas, levels
    libre = sol.difference(murs)                              # the floor, less the walls (and the 1st floor's void)
    reste = libre
    for nom, (x, y), zone in PIECES[etage]:
        if zone != 'reste':
            reste = reste.difference(zone)
    aires = []
    for nom, (x, y), zone in PIECES[etage]:
        a = (reste if zone == 'reste' else zone.intersection(libre)).area / PX_M ** 2
        aires.append((nom, a))
        piece(F, x, y, nom, a, petite=a < 6)
    if etage == 'etage1':
        piece(F, 760, 1600, 'VIDE SUR SALLE', None)
    titre, cote_niv, planche = TITRES[etage]
    nx, ny = (700, 2330) if etage == 'rdc' else (1180, 1180)
    niveau(F, nx, ny, cote_niv)
    cartouche(F, etage, aires)
    return F


def couronne(x, y, r, n=11):
    """A tree's crown seen from above: a ring of overlapping lobes (plan px)."""
    rp = r * PX_M
    lobes = [Point(x + rp * 0.62 * math.cos(math.tau * k / n), y + rp * 0.62 * math.sin(math.tau * k / n))
             .buffer(rp * 0.42, 12) for k in range(n)]
    return shapely.union_all(lobes + [Point(x, y).buffer(rp * 0.5, 16)])


_DALLE = None


def dalle_etage():
    """The 1st floor's slab (its openings: the void, the garden, the stair), read in the 1st floor's trace."""
    global _DALLE
    if _DALLE is None:
        d = json.load(open(R / 'modele' / 'trace' / 'etage1.json'))
        g = [tris(p['bas']) for p in d['parties'] if p['o'] == 'dalle']
        g = [x for x in g if x is not None]
        _DALLE = shapely.union_all(g, grid_size=0.01) if g else None
    return _DALLE


PORTES = {
    'rdc': [
        ((650, 2406.5), (720, 2406.5), (0, -1)),               # the shopfront's double door, opening in
        ((790, 2406.5), (720, 2406.5), (0, -1)),
        ((1284.5, 1889), (1379.5, 1889), (0, -1)),             # the wine room's glass door, onto the room
        ((397, 357), (505, 357), (0, 1)),                      # the toilet, opening out onto its lobby
        ((1208, 465), (1302, 465), (0, 1), True),              # the kitchen's double-action door
        ((1396, 465), (1302, 465), (0, 1), True),
        ((578, 510), (578, 621), (1, 0)),                      # the gate at the bar's end
    ],
    'etage1': [
        ((1295, 152), (1295, 236), (1, 0)),                    # the toilet
        ((1327, 300), (1327, 408), (-1, 0)),                   # the storeroom, opening onto the toilets' passage
    ],
}


def cartouche(F, etage, aires):
    titre, cote_niv, planche = TITRES[etage]
    x0, x1 = CART + 8, W_MM - 18
    y = 26
    F.texte(x0, y, 'RESTAURANT & BAR', 3.2, 600, ancre='start', ls=0.5)
    F.texte(x0, y + 5.5, 'Aménagement intérieur · deux niveaux', 2.3, 400, ancre='start', couleur='#555')
    F.path(f'M{f(x0)},{f(y + 10)} L{f(x1)},{f(y + 10)}', 'filet')
    y += 24
    F.texte(x0, y, titre, 6.2, 600, ancre='start')
    F.texte(x0, y + 7, f'Niveau {cote_niv} · plan de coupe à 1,20 m', 2.4, 400, ancre='start', couleur='#444')
    y += 18
    infos = [('Échelle', '1:50'), ('Format', 'A2'), ('Date', '26.11.2026'), ('Indice', 'A'), ('Planche', planche)]
    for k, (a, b) in enumerate(infos):
        yy = y + k * 6
        F.texte(x0, yy, a, 2.2, 400, ancre='start', couleur='#666')
        F.texte(x0 + 30, yy, b, 2.2, 600, ancre='start')
    y += len(infos) * 6 + 6
    F.path(f'M{f(x0)},{f(y)} L{f(x1)},{f(y)}', 'filet')
    # the legend
    y += 8
    F.texte(x0, y, 'LÉGENDE', 2.2, 600, ancre='start', ls=0.4)
    y += 6
    leg = [('mur', 'Mur, poteau (coupé)'), ('tambour', 'Tambour, colonne (coupés)'),
           ('paves', 'Pavés de verre'), ('verre', 'Vitrage, cadre acier'),
           ('coupe-meuble', 'Élément haut coupé'), ('meuble', 'Mobilier, équipement'),
           ('tirets', 'Au-dessus du plan de coupe')]
    for k, (cls, txt) in enumerate(leg):
        yy = y + k * 6.2
        if cls == 'tirets':
            F.path(f'M{f(x0)},{f(yy - 1)} L{f(x0 + 9)},{f(yy - 1)}', 'tirets')
        else:
            F.add(f'<rect class="{cls}" x="{f(x0)}" y="{f(yy - 2.6)}" width="9" height="3.2"/>')
            if cls == 'paves':
                for i in range(1, 4):
                    F.path(f'M{f(x0 + 2.25 * i)},{f(yy - 2.6)} L{f(x0 + 2.25 * i)},{f(yy + .6)}', 'seuil')
            if cls == 'verre':
                F.add(f'<rect class="cadre" x="{f(x0)}" y="{f(yy - 2.6)}" width="1.2" height="3.2"/>'
                      f'<rect class="cadre" x="{f(x0 + 7.8)}" y="{f(yy - 2.6)}" width="1.2" height="3.2"/>')
        F.texte(x0 + 13, yy, txt, 2.2, 400, ancre='start')
    y += len(leg) * 6.2 + 4
    F.path(f'M{f(x0)},{f(y)} L{f(x1)},{f(y)}', 'filet')
    # the areas
    y += 8
    F.texte(x0, y, 'SURFACES', 2.2, 600, ancre='start', ls=0.4)
    y += 6
    total = 0
    for nom, a in aires:
        F.texte(x0, y, nom.capitalize() if nom.isupper() else nom, 2.2, 400, ancre='start')
        F.texte(x1, y, f'{a:.1f} m²'.replace('.', ','), 2.2, 500, ancre='end')
        total += a
        y += 5.2
    F.path(f'M{f(x0)},{f(y - 3)} L{f(x1)},{f(y - 3)}', 'cote')
    F.texte(x0, y + 1.2, 'Total (surface utile)', 2.2, 600, ancre='start')
    F.texte(x1, y + 1.2, f'{total:.1f} m²'.replace('.', ','), 2.2, 600, ancre='end')
    y += 9
    F.path(f'M{f(x0)},{f(y)} L{f(x1)},{f(y)}', 'filet')
    # the scale bar: 0 - 5 m
    y += 10
    F.texte(x0, y - 3, 'Échelle graphique', 2.0, 400, ancre='start', couleur='#555')
    m = 1000 / 50                                           # mm per metre at 1:50
    for k in range(5):
        F.add(f'<rect x="{f(x0 + k * m)}" y="{f(y)}" width="{f(m)}" height="1.6" fill="{ENCRE if k % 2 == 0 else "#fff"}" '
              f'stroke="{ENCRE}" stroke-width=".18"/>')
    for k in range(6):
        F.texte(x0 + k * m, y + 5.2, str(k), 2.0, 500)
    F.texte(x0 + 5 * m + 4, y + 5.2, 'm', 2.0, 500)
    y += 14
    F.path(f'M{f(x0)},{f(y)} L{f(x1)},{f(y)}', 'filet')
    # the notes, the source
    y += 7
    notes = ['Cotes en mètres. Plan tiré de la maquette 3D du projet :',
             'les murs, les ouvrages et le mobilier y sont relevés tels',
             'que modélisés ; les petits objets ne sont pas représentés.',
             '',
             'D’après le LAIR Restaurant & Bar (RENESA Architecture',
             'Design Interiors Studio, Gurugram, 2024), remodelé.']
    for k, t in enumerate(notes):
        F.texte(x0, y + k * 3.6, t, 1.9, 400, ancre='start', couleur='#555')
    # the sheet's number
    F.path(f'M{f(CART)},{f(H_MM - 36)} L{f(W_MM - 10)},{f(H_MM - 36)}', 'filet')
    F.texte(x0, H_MM - 20, planche, 9, 600, ancre='start')
    F.texte(x1, H_MM - 25, 'Studio', 2.6, 600, ancre='end')
    F.texte(x1, H_MM - 20, 'Indice A · 26.11.2026', 2.0, 400, ancre='end', couleur='#555')


def ecrire(etage):
    F = dessiner(etage)
    OUT.mkdir(parents=True, exist_ok=True)
    w, h = round(W_MM / 25.4 * DPI), round(H_MM / 25.4 * DPI)
    (OUT / f'{etage}.svg').write_text(F.svg(w, h))
    subprocess.run(['node', str(Path(__file__).parent / 'rendre_plan.mjs'), str(OUT / f'{etage}.svg'),
                    str(OUT / f'{etage}.png'), str(OUT / f'{etage}.pdf')], check=True)


if __name__ == '__main__':
    for e in sys.argv[1:] or ['rdc', 'etage1']:
        ecrire(e)
