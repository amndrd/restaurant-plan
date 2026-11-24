# Drawing kit for the redrawn plans: an SVG in the plan's own pixels (floor1.png / floor2.png, 120 px = 1 m),
# turned and scaled once by a group matrix so the plan reads like the map's top view (bar on the left, entry on the
# right), with constant line widths. Exact primitives only: polygons, true circles and arcs, the furniture of the
# 3D model as clean symbols.
import base64
import math
from pathlib import Path

R = Path(__file__).resolve().parents[2]
PX = 1 / 120                     # metres per plan pixel
W, H = 3840, 2160                # 4K

ENCRE = '#1d1d1d'
TRAIT = '#2a2a2a'
FIN = '#6d6d6a'


def f(v):
    return f'{v:.2f}'.rstrip('0').rstrip('.')


def chemin(pts, ferme=True):
    return 'M' + ' L'.join(f'{f(x)},{f(y)}' for x, y in pts) + (' Z' if ferme else '')


def rrect(cx, cy, w, d, r, seg=6):
    """Rounded rectangle outline, centred, in the given units."""
    pts = []
    for qx, qy, a0 in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
        ox, oy = cx + qx * (w / 2 - r), cy + qy * (d / 2 - r)
        pts += [(ox + r * math.cos(math.radians(a0 + 90 * k / seg)), oy + r * math.sin(math.radians(a0 + 90 * k / seg)))
                for k in range(seg + 1)]
    return pts


def arc(cx, cy, r, a0, a1, n=None):
    """Points of an arc (degrees, plan pixels: y down, angles clockwise on screen)."""
    n = n or max(8, int(abs(a1 - a0) / 3))
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * k / n)), cy + r * math.sin(math.radians(a0 + (a1 - a0) * k / n)))
            for k in range(n + 1)]


def poser(pts_m, x, y, vers):
    """Local symbol (metres, +y towards what it faces) set at plan point (x, y), facing the plan point `vers`."""
    fx, fy = (vers[0] - x, vers[1] - y) if vers else (0, -1)
    n = math.hypot(fx, fy) or 1
    fx, fy = fx / n, fy / n
    rx, ry = -fy, fx
    return [(x + (lx * rx + ly * fx) / PX, y + (lx * ry + ly * fy) / PX) for lx, ly in pts_m]


# ---- the symbols of the furniture (the same shapes as the model)
def chaise(x, y, vers):
    siege = poser(rrect(0, 0, 0.46, 0.44, 0.14), x, y, vers)
    a = [math.radians(-36 + 72 * k / 14) for k in range(15)]
    dos = [(0.30 * math.sin(q), 0.10 - 0.30 * math.cos(q)) for q in a] + \
          [(0.33 * math.sin(q), 0.10 - 0.33 * math.cos(q)) for q in reversed(a)]
    return [siege, poser(dos, x, y, vers)]


def fauteuil(x, y, vers):
    ext = [p for p in rrect(0, 0, 0.58, 0.54, 0.21, 10) if p[1] < 0.05]
    inn = [p for p in rrect(0, 0, 0.49, 0.45, 0.165, 10) if p[1] < 0.05]
    coque = [(-0.29, 0.05)] + ext + [(0.29, 0.05), (0.245, 0.05)] + list(reversed(inn)) + [(-0.245, 0.05)]
    return [poser(rrect(0, 0, 0.58, 0.54, 0.21), x, y, vers), poser(rrect(0, 0.025, 0.475, 0.49, 0.15), x, y, vers),
            poser(coque, x, y, vers)]


def plante(x, y, r_pot, graine):
    """A crown of leaves seen from above: overlapping lumps (the outline of their union is drawn)."""
    import random
    rnd = random.Random(graine)
    bulles = [(x, y, r_pot * 0.55)]
    for k in range(9):
        a = 2 * math.pi * k / 9 + rnd.uniform(-0.3, 0.3)
        d = r_pot * rnd.uniform(0.45, 0.85)
        bulles.append((x + d * math.cos(a), y + d * math.sin(a), r_pot * rnd.uniform(0.34, 0.48)))
    return bulles


class Plan:
    """An SVG plan: layers drawn in plan pixels inside a turned, scaled group; labels in canvas pixels."""

    def __init__(self, centre, echelle, origine):
        self.cx, self.cy = centre          # plan px at the canvas point `origine`
        self.s = echelle                   # canvas px per plan px
        self.ox, self.oy = origine
        self.couches = {k: [] for k in ('fond', 'sol', 'hachures', 'poche', 'vitrage', 'mobilier', 'detail', 'haut')}
        self.textes = []

    def ecran(self, x, y):                # screen up = plan +x, screen right = plan +y
        return self.ox + (y - self.cy) * self.s, self.oy - (x - self.cx) * self.s

    def matrice(self):
        s = self.s
        return f'matrix(0 {f(-s)} {f(s)} 0 {f(self.ox - s * self.cy)} {f(self.oy + s * self.cx)})'

    def ajouter(self, couche, el):
        self.couches[couche].append(el)

    # primitives (plan px)
    def poly(self, couche, pts, cls, ferme=True):
        self.ajouter(couche, f'<path class="{cls}" d="{chemin(pts, ferme)}"/>')

    def polys(self, couche, loops, cls):
        self.ajouter(couche, f'<path class="{cls}" fill-rule="evenodd" d="{" ".join(chemin(l) for l in loops)}"/>')

    def rect(self, couche, x0, y0, x1, y1, cls):
        self.poly(couche, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], cls)

    def cercle(self, couche, x, y, r, cls):
        self.ajouter(couche, f'<circle class="{cls}" cx="{f(x)}" cy="{f(y)}" r="{f(r)}"/>')

    def ligne(self, couche, pts, cls):
        self.poly(couche, pts, cls, ferme=False)

    def texte(self, x, y, txt, cls, plan=True):
        X, Y = self.ecran(x, y) if plan else (x, y)
        self.textes.append(f'<text class="{cls}" x="{f(X)}" y="{f(Y)}">{txt}</text>')

    def svg(self, cartouche=''):
        polices = R / 'outils' / 'pages' / 'polices'
        ff = ''.join(f'@font-face{{font-family:"Inter";font-weight:{w};src:url(data:font/woff2;base64,'
                     f'{base64.b64encode((polices / f"inter-latin-{w}-normal.woff2").read_bytes()).decode()}) format("woff2")}}'
                     for w in (400, 500, 600))
        style = ff + f'''
.fond{{fill:#f4f3ef}} .sol{{fill:#fbfaf8}} .sol-clair{{fill:#fefefd}} .exterieur{{fill:#ecebe6}}
.poche{{fill:{ENCRE}}} .poche-l{{fill:#454543}}
.vitrage{{fill:#e4ebee;stroke:{TRAIT};stroke-width:1.3}} .montant{{fill:none;stroke:{TRAIT};stroke-width:1.3}}
.meuble{{fill:#fff;stroke:{TRAIT};stroke-width:1.7;stroke-linejoin:round}}
.meuble-g{{fill:#f1efea;stroke:{TRAIT};stroke-width:1.7;stroke-linejoin:round}}
.cuir{{fill:#f6f4ef;stroke:{TRAIT};stroke-width:1.5;stroke-linejoin:round}}
.trait{{fill:none;stroke:{TRAIT};stroke-width:1.5;stroke-linejoin:round;stroke-linecap:round}}
.fin{{fill:none;stroke:{FIN};stroke-width:1.1;stroke-linecap:round}}
.haut{{fill:none;stroke:#77756f;stroke-width:1.4;stroke-dasharray:9 6}}
.pointille{{fill:none;stroke:#8a8883;stroke-width:2.2;stroke-dasharray:0.1 7;stroke-linecap:round}}
.feuille{{fill:#e3e8dd;stroke:#55604f;stroke-width:1.3}} .feuille-p{{fill:#e3e8dd}}
.gravier{{fill:url(#gravier);stroke:{TRAIT};stroke-width:1.2}} .rocher{{fill:#e6e4df;stroke:{TRAIT};stroke-width:1.4}}
.miroir{{fill:#eef1f2;stroke:{TRAIT};stroke-width:1.4}}
.marche{{fill:#fff;stroke:{TRAIT};stroke-width:1.3}}
.fleche{{fill:{TRAIT}}}
.vide{{fill:#eceeed}} .hachure{{fill:url(#hachure);stroke:{TRAIT};stroke-width:1.3}} .carrelage{{fill:url(#carreaux)}}
.dessous{{fill:#e2e3e1;stroke:#9c9d99;stroke-width:1.1}} .dessous-l{{fill:none;stroke:#9c9d99;stroke-width:1.1}}
path,circle{{vector-effect:non-scaling-stroke}}
text{{font-family:Inter,sans-serif;fill:{ENCRE}}}
.num{{font-size:30px;font-weight:500;text-anchor:middle;dominant-baseline:central}}
.pastille{{fill:#fff;stroke:{ENCRE};stroke-width:1.6}}
.lbl{{font-size:22px;font-weight:600;letter-spacing:.14em;text-anchor:middle;dominant-baseline:central;fill:#5e5d59}}
.titre{{font-size:64px;font-weight:600;letter-spacing:-.01em}} .sous{{font-size:26px;fill:#6f6e69}}
.leg{{font-size:27px}} .leg-n{{font-size:22px;font-weight:600;text-anchor:middle;dominant-baseline:central}}
.ech{{font-size:22px;fill:#5e5d59;text-anchor:middle}} .note{{font-size:21px;fill:#8a8984}}'''
        defs = '''<defs><pattern id="gravier" width="14" height="14" patternUnits="userSpaceOnUse">
<rect width="14" height="14" fill="#f2f1ed"/><circle cx="3" cy="4" r="1.3" fill="#9c9a93"/><circle cx="10" cy="2.5" r="0.9" fill="#b2b0a9"/>
<circle cx="8" cy="9.5" r="1.4" fill="#a3a19a"/><circle cx="2" cy="11.5" r="0.8" fill="#b6b4ad"/><circle cx="12.5" cy="12" r="1" fill="#a9a7a0"/></pattern>
<pattern id="hachure" width="14" height="14" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
<rect width="14" height="14" fill="#f1f0ec"/><line x1="0" y1="0" x2="0" y2="14" stroke="#a6a49e" stroke-width="2"/></pattern>
<pattern id="carreaux" width="9" height="9" patternUnits="userSpaceOnUse">
<rect width="9" height="9" fill="#f7f7f5"/><path d="M9 0V9H0" fill="none" stroke="#d3d3cf" stroke-width="0.8"/></pattern></defs>'''
        corps = ''.join(f'<g>{"".join(self.couches[k])}</g>' for k in self.couches)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
                f'<style>{style}</style>{defs}<rect class="fond" width="{W}" height="{H}"/>'
                f'<g transform="{self.matrice()}">{corps}</g>{"".join(self.textes)}{cartouche}</svg>')


def cartouche(x, y, titre, sous, legende, plan, note):
    """Title, legend and scale bar, in canvas pixels, from (x, y)."""
    el = [f'<text class="titre" x="{x}" y="{y}">{titre}</text>', f'<text class="sous" x="{x}" y="{y + 44}">{sous}</text>']
    yy = y + 130
    for n, nom in legende:
        el.append(f'<circle class="pastille" cx="{x + 18}" cy="{yy}" r="18"/><text class="leg-n" x="{x + 18}" y="{yy + 1}">{n}</text>'
                  f'<text class="leg" x="{x + 52}" y="{yy + 10}">{nom}</text>')
        yy += 50
    # scale bar: 0 1 2 3 m
    yy += 40
    m = plan.s / PX
    el.append(f'<text class="ech" x="{x}" y="{yy - 14}" style="text-anchor:start">Échelle</text>')
    for k in range(3):
        el.append(f'<rect x="{f(x + k * m)}" y="{yy}" width="{f(m)}" height="10" fill="{ENCRE if k % 2 == 0 else "#fff"}" '
                  f'stroke="{ENCRE}" stroke-width="1.4"/>')
    for k in range(4):
        el.append(f'<text class="ech" x="{f(x + k * m)}" y="{yy + 42}">{k}</text>')
    el.append(f'<text class="ech" x="{f(x + 3 * m + 30)}" y="{yy + 42}">m</text>')
    for k, ligne in enumerate(note):
        el.append(f'<text class="note" x="{x}" y="{yy + 110 + k * 30}">{ligne}</text>')
    return ''.join(el)
