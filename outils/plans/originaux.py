# The client's two plans reproduced as they are (same framing, colours, textures and lettering), in 4K: 2716 x 3840,
# the A-format proportions of the originals (floor1.png, floor2.png, 2000 x 2828).
# - every bright line of the original is redrawn as a vector of constant width along its centreline (skeleton);
# - the thick white shapes (dots, arrows, the leaves of the plants) are traced as shapes (potrace);
# - the lettering is set again in Century Gothic, the originals' typeface, at the measured size and place;
# - under them, the original's own fills (its concrete, metal and wood textures), with the lines and the letters
#   taken out, scaled to 4K.
# The output reproduces a third-party drawing: it stays out of the repository (see .gitignore).
# needs: potrace (brew install potrace), scikit-image, fonttools; Century Gothic (a macOS downloadable font).
# usage: outils/.venv/bin/python outils/plans/originaux.py [rdc] [etage1]
import base64
import io
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np
from fontTools.ttLib import TTCollection, TTFont
from PIL import Image
from skimage.morphology import skeletonize

R = Path(__file__).resolve().parents[2]
ICI = Path(__file__).parent
OUT = R / 'rendus' / '11-plans-d-origine'
K = 4                              # the lines are found on the original enlarged 4 times
H4K = 3840
CG = Path('/System/Library/PrivateFrameworks/FontServices.framework/Versions/A/Resources/Fonts/ApplicationSupport/'
          'CenturyGothic.ttc')
POLICES = ICI / '_polices'         # the two faces taken out of the macOS collection (not in the repository)

# the lettering of each plan: (text, bold, window x0, y0, x1, y1 where its letters are, in original pixels)
LEG1 = ['1. ENTRY', '2. CONCIERGE', '3. DINING SPACE', '4. LIFT SHAFT', '5. BAR', '6. LIQUOR STORE', '7. MEN’S TOILET',
        '8. LADIES’ TOILET', '9. LT PANELS']
LEG2 = ['1. DINING AREA', '2. IN-HOUSE LAB', '3. OMAKASE BAR', '4. LIFT SHAFT', '5. UNISEX TOILETS']


def legende(lignes):
    return [('LEGEND', True, 1540, 2425, 1700, 2466)] + \
        [(t, False, 1540, 2487 + 34.4 * k, 1985, 2522 + 34.4 * k) for k, t in enumerate(lignes)]


TEXTES = {
    'rdc': [('6', False, 510, 170, 555, 215), ('7', False, 795, 170, 835, 215), ('8', False, 945, 170, 985, 215),
            ('10', False, 1715, 190, 1770, 235), ('9', False, 1370, 430, 1405, 475), ('5', False, 850, 520, 890, 565),
            ('3', False, 520, 1475, 560, 1520), ('3', False, 1170, 1475, 1210, 1520), ('4', False, 1330, 1920, 1370, 1965),
            ('2', False, 680, 2045, 720, 2090), ('1', False, 705, 2305, 745, 2350), ('UP', False, 1108, 2035, 1150, 2074)]
    + legende(LEG1),
    'etage1': [('5', False, 1258, 180, 1298, 225), ('4', False, 1376, 430, 1416, 475), ('3', False, 836, 520, 876, 565),
               ('UP', False, 530, 178, 572, 214), ('2', False, 312, 968, 352, 1013), ('1', False, 830, 982, 870, 1027),
               ('1', False, 1126, 1476, 1166, 1521), ('DN', False, 1192, 2075, 1240, 2112)]
    + legende(LEG2),
}


# ---------------------------------------------------------------- the typeface
def polices():
    POLICES.mkdir(exist_ok=True)
    faces = {}
    for i, nom in ((0, 'cg'), (1, 'cg-gras')):
        f = POLICES / f'{nom}.ttf'
        if not f.exists():
            TTCollection(str(CG)).fonts[i].save(str(f))
        faces[nom] = f
    return faces


class Police:
    def __init__(self, f):
        self.t = TTFont(str(f))
        self.em = self.t['head'].unitsPerEm
        self.cmap = self.t.getBestCmap()
        self.glyf, self.hmtx = self.t['glyf'], self.t['hmtx']

    def encre(self, s):
        """Ink box of a string at 1 unit per em: x0, x1, y0 (down from the baseline is negative), y1, advance."""
        x = 0; X0 = Y0 = 1e9; X1 = Y1 = -1e9
        for c in s:
            g = self.cmap[ord(c)]
            gl = self.glyf[g]
            if getattr(gl, 'numberOfContours', 0):
                gl.recalcBounds(self.glyf)
                X0 = min(X0, x + gl.xMin); X1 = max(X1, x + gl.xMax); Y0 = min(Y0, gl.yMin); Y1 = max(Y1, gl.yMax)
            x += self.hmtx[g][0]
        return X0 / self.em, X1 / self.em, Y0 / self.em, Y1 / self.em, x / self.em


# ---------------------------------------------------------------- the lines: centrelines of the bright strokes
VOISINS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def chaines(sk):
    """The skeleton as chains of pixels between its nodes (ends and junctions), plus its closed loops."""
    ys, xs = np.nonzero(sk)
    pts = set(zip(ys.tolist(), xs.tolist()))
    deg = {p: sum((p[0] + dy, p[1] + dx) in pts for dy, dx in VOISINS) for p in pts}
    noeuds = {p for p, d in deg.items() if d != 2}
    vu, out = set(), []

    def suivre(a, b):
        ch = [a, b]; vu.add((a, b)); vu.add((b, a))
        while ch[-1] not in noeuds:
            c, nx = ch[-1], None
            for dy, dx in VOISINS:
                q = (c[0] + dy, c[1] + dx)
                if q in pts and q != ch[-2] and (c, q) not in vu:
                    nx = q; break
            if nx is None:
                break
            vu.add((c, nx)); vu.add((nx, c)); ch.append(nx)
            if nx == ch[0]:
                break
        return ch
    for n in list(noeuds):
        for dy, dx in VOISINS:
            q = (n[0] + dy, n[1] + dx)
            if q in pts and (n, q) not in vu:
                out.append(suivre(n, q))
    libres = {p for p in pts if p not in noeuds and not any((p, (p[0] + dy, p[1] + dx)) in vu for dy, dx in VOISINS)}
    while libres:
        a = libres.pop()
        nb = [(a[0] + dy, a[1] + dx) for dy, dx in VOISINS if (a[0] + dy, a[1] + dx) in pts]
        if not nb:
            continue
        noeuds.add(a); deg[a] = 2
        ch = suivre(a, nb[0]); out.append(ch); libres -= set(ch)
    return out, deg


def lisser(c, k=2):
    c = np.asarray(c, float)
    if len(c) < 2 * k + 3:
        return c
    ferme = np.allclose(c[0], c[-1])
    n = len(c) - (1 if ferme else 0)
    out = c.copy()
    for i in range(len(c)):
        if not ferme and (i < k or i >= len(c) - k):
            continue
        out[i] = c[[(i + j) % n for j in range(-k, k + 1)]].mean(0)
    if ferme:
        out[-1] = out[0]
    return out


def rdp(c, eps):
    if len(c) < 3:
        return c
    a, b = c[0], c[-1]; d = b - a; L = np.hypot(*d)
    dd = np.hypot(*(c - a).T) if L < 1e-9 else np.abs(d[0] * (c[:, 1] - a[1]) - d[1] * (c[:, 0] - a[0])) / L
    i = int(np.argmax(dd))
    if dd[i] > eps:
        return np.vstack([rdp(c[:i + 1], eps)[:-1], rdp(c[i:], eps)])
    return np.array([a, b])


def potrace(masque, couleur, echelle):
    """Traces a mask (1 = shape) and returns an SVG group in output pixels."""
    with tempfile.TemporaryDirectory() as d:
        Image.fromarray(((1 - masque) * 255).astype(np.uint8)).convert('1').save(f'{d}/m.pbm')
        subprocess.run(['potrace', f'{d}/m.pbm', '-s', '-o', f'{d}/m.svg', '--alphamax', '1.0', '--opttolerance', '0.2',
                        '-t', '4'], check=True)
        sv = Path(f'{d}/m.svg').read_text()
    if '<path' not in sv:
        return ''
    tr = re.search(r'<g transform="([^"]+)"', sv).group(1)
    return f'<g transform="scale({echelle:.6f}) {tr}" fill="{couleur}">{sv[sv.index("<path"):sv.rindex("</g>")]}</g>'


# ---------------------------------------------------------------- one plan
def faire(nom, image):
    g = np.array(Image.open(R / image).convert('L')).astype(np.float32)
    h, w = g.shape
    E = H4K / h                                     # original px -> output px
    W4K = round(w * E)
    cg, cgb = (Police(f) for f in polices().values())

    # the lettering: where each text is (its letters, inside its window), then taken out of the plan
    bg7 = cv2.morphologyEx(g, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    lettres = np.zeros(g.shape, np.uint8)
    textes = []
    for t, gras, x0, y0, x1, y1 in TEXTES[nom]:
        x0, y0, x1, y1 = (int(round(v)) for v in (x0, y0, x1, y1))
        z = ((g[y0:y1, x0:x1] > 150) & (g[y0:y1, x0:x1] - bg7[y0:y1, x0:x1] > 40)).astype(np.uint8)
        n, lab, st, _ = cv2.connectedComponentsWithStats(z, 8)
        garde = [i for i in range(1, n) if st[i, cv2.CC_STAT_AREA] >= 3 and st[i, 2] < 60 and st[i, 3] < 45
                 and st[i, 0] > 0 and st[i, 1] > 0 and st[i, 0] + st[i, 2] < x1 - x0 and st[i, 1] + st[i, 3] < y1 - y0]
        if not garde:
            print('  texte introuvable :', t); continue
        bx0 = x0 + min(st[i, 0] for i in garde); by0 = y0 + min(st[i, 1] for i in garde)
        bx1 = x0 + max(st[i, 0] + st[i, 2] for i in garde); by1 = y0 + max(st[i, 1] + st[i, 3] for i in garde)
        for i in garde:
            lettres[y0:y1, x0:x1][lab == i] = 1
        p = cgb if gras else cg
        ex0, ex1, ey0, ey1, _ = p.encre(t)
        taille = (by1 - by0) / (ey1 - ey0)                         # the ink height gives the size
        esp = ((bx1 - bx0) - (ex1 - ex0) * taille) / max(len(t) - 1, 1)   # the ink width, the letter spacing
        textes.append((t, gras, (bx0 - ex0 * taille) * E, (by1 + ey0 * taille) * E, taille * E, esp * E))
    lettres = cv2.dilate(lettres, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))

    # the bright strokes, on the original enlarged 4 times: brighter than half-way between the local background
    # and the local peak
    pk = cv2.dilate(g, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    g4 = cv2.resize(g, None, fx=K, fy=K, interpolation=cv2.INTER_CUBIC)
    bg4 = cv2.resize(bg7, None, fx=K, fy=K, interpolation=cv2.INTER_LINEAR)
    pk4 = cv2.resize(pk, None, fx=K, fy=K, interpolation=cv2.INTER_LINEAR)
    sans = cv2.resize(1 - lettres, None, fx=K, fy=K, interpolation=cv2.INTER_NEAREST)
    m = ((g4 > bg4 + 0.5 * (pk4 - bg4)) & (pk4 - bg4 > 28) & (sans > 0)).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    del g4
    # thick parts (wider than ~3.7 px of the original) are traced as shapes, the rest becomes centrelines
    epais = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
    fin = m & (1 - cv2.dilate(epais, np.ones((3, 3), np.uint8)))
    dist = cv2.distanceTransform(m, cv2.DIST_L2, 5)
    sk = skeletonize(fin > 0)
    ch, deg = chaines(sk)
    print(f'  {nom}: {len(ch)} traits bruts')

    traits = []
    for c in ch:
        larg = 2 * float(np.median([dist[p] for p in c]))       # width, 4x px
        L = len(c)
        bouts = [deg.get(c[0], 2), deg.get(c[-1], 2)]
        if L < 4 and 1 in bouts:
            continue
        if bouts.count(1) == 1 and L < 1.6 * larg:               # a spur of the skeleton
            continue
        ton = float(np.median([pk4[p] for p in c]))
        pts = rdp(lisser(c), 0.6)
        larg_o = min(max(larg / K, 1.3), 3.4)                    # width in original px
        traits.append((round(ton / 8) * 8, round(larg_o * 4) / 4, pts))
    del pk4, bg4
    # grouped by tone and width, in output pixels
    groupes = {}
    for ton, lo, pts in traits:
        groupes.setdefault((ton, lo), []).append('M' + ' L'.join(f'{x * E / K:.2f},{y * E / K:.2f}' for y, x in pts))
    svg_traits = ''.join(
        f'<path stroke="rgb({min(255, int(t))},{min(255, int(t))},{min(255, int(t))})" stroke-width="{lo * E:.2f}" d="{" ".join(ds)}"/>'
        for (t, lo), ds in sorted(groupes.items()))
    # the thick shapes, white or grey after their tone
    n, lab = cv2.connectedComponents(epais, connectivity=8)
    tonc = np.zeros(n); cnt = np.zeros(n)
    gpk = cv2.resize(pk, None, fx=K, fy=K, interpolation=cv2.INTER_LINEAR)
    np.add.at(tonc, lab.ravel(), gpk.ravel()); np.add.at(cnt, lab.ravel(), 1)
    tonc = tonc / np.maximum(cnt, 1)
    formes = ''
    for t0, t1, coul in ((215, 999, '#ffffff'), (165, 215, '#d4d4d4'), (0, 165, '#a8a8a8')):
        sel = (tonc >= t0) & (tonc < t1); sel[0] = False
        mm = sel[lab].astype(np.uint8)
        if mm.any():
            formes += potrace(mm, coul, E / K)
    del lab, gpk

    # the fills: the original without its lines and its letters
    m1 = cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA) > 0
    trou = cv2.dilate((m1 | (lettres > 0)).astype(np.uint8), np.ones((3, 3), np.uint8))
    fond = np.where(trou > 0, bg7, g)
    lt = cv2.dilate(lettres, np.ones((5, 5), np.uint8))
    fond = cv2.inpaint(np.clip(fond, 0, 255).astype(np.uint8), lt, 5, cv2.INPAINT_TELEA).astype(np.float32)
    fond4 = cv2.resize(fond, (W4K, H4K), interpolation=cv2.INTER_LANCZOS4)
    buf = io.BytesIO()
    Image.fromarray(np.clip(fond4, 0, 255).astype(np.uint8)).save(buf, 'PNG')

    ff = ''.join(f'@font-face{{font-family:"{n_}";src:url(data:font/ttf;base64,{base64.b64encode(f.read_bytes()).decode()})}}'
                 for n_, f in (('CG', POLICES / 'cg.ttf'), ('CGB', POLICES / 'cg-gras.ttf')))
    svg_textes = ''.join(
        f'<text x="{x:.2f}" y="{y:.2f}" style="font-family:{"CGB" if gr else "CG"};font-size:{s:.2f}px;letter-spacing:{e:.2f}px">'
        f'{t}</text>' for t, gr, x, y, s, e in textes)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W4K}" height="{H4K}" viewBox="0 0 {W4K} {H4K}">'
           f'<style>{ff} text{{fill:#fff;font-kerning:none;white-space:pre}}</style>'
           f'<image href="data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}" width="{W4K}" height="{H4K}"/>'
           f'{formes}<g fill="none" stroke-linecap="round" stroke-linejoin="round">{svg_traits}</g>{svg_textes}</svg>')
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f'{nom}.svg').write_text(svg)
    subprocess.run(['node', str(ICI / 'rendre.mjs'), str(OUT / f'{nom}.svg'), str(OUT / f'{nom}.png')], check=True)


if __name__ == '__main__':
    quels = sys.argv[1:] or ['rdc', 'etage1']
    for nom, image in (('rdc', 'floor1.png'), ('etage1', 'floor2.png')):
        if nom in quels:
            faire(nom, image)
