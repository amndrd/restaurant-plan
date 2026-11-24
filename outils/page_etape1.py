# The working page of step 1: floor1 read and measured, then the shell modelled over it.
# Writes outils/pages/etape-1.html, then pages/1-plan-et-coque.png with outils/pages/export.mjs.
# usage: outils/.venv/bin/python outils/page_etape1.py
import subprocess
from pathlib import Path

R = Path(__file__).resolve().parents[1]
PG = R / 'outils' / 'pages'
K = 120  # plan pixels per metre


def m(px):
    return f'{px / K:.2f}'.replace('.', ',')


# ---------------------------------------------------------------- annotated plan (plan pixel coordinates)
def cote_h(x0, x1, y, txt, up=True):
    t = y - 14 if up else y + 30
    return (f'<line class="dim" x1="{x0}" y1="{y}" x2="{x1}" y2="{y}"/>'
            f'<line class="dim" x1="{x0}" y1="{y-14}" x2="{x0}" y2="{y+14}"/><line class="dim" x1="{x1}" y1="{y-14}" x2="{x1}" y2="{y+14}"/>'
            f'<text class="cote" x="{(x0+x1)/2}" y="{t}" text-anchor="middle">{txt}</text>')


def cote_v(y0, y1, x, txt):
    return (f'<line class="dim" x1="{x}" y1="{y0}" x2="{x}" y2="{y1}"/>'
            f'<line class="dim" x1="{x-14}" y1="{y0}" x2="{x+14}" y2="{y0}"/><line class="dim" x1="{x-14}" y1="{y1}" x2="{x+14}" y2="{y1}"/>'
            f'<text class="cote" x="{x+22}" y="{(y0+y1)/2}" transform="rotate(90 {x+22} {(y0+y1)/2})" text-anchor="middle">{txt}</text>')


def tag(x, y, s):
    return f'<circle class="tag" cx="{x}" cy="{y}" r="26"/><text class="tagt" x="{x}" y="{y+10}" text-anchor="middle">{s}</text>'


TAGS = [(470, 1010, 'A'), (470, 1313, 'A'), (470, 1719, 'A'), (470, 2022, 'A'),
        (712, 1270, 'B'), (712, 1660, 'B'), (1030, 1300, 'C'), (930, 1600, 'C'), (930, 1760, 'C'),
        (1330, 960, 'D'), (1330, 1150, 'D'), (1330, 1345, 'D'), (1330, 1645, 'D'),
        (800, 650, 'E'), (1180, 2150, 'F'), (630, 1003, 'G'), (818, 1003, 'G'), (1103, 1003, 'G')]

svg = ['<svg class="plan" viewBox="150 20 1520 2500" width="900" height="1480">',
       '<image href="../../floor1.png" x="0" y="0" width="2000" height="2828" style="filter:invert(1) grayscale(1) contrast(.9) brightness(1.05)"/>']
svg += [cote_h(201, 1473, 2470, '10,60 m (intérieur)', up=False), cote_v(146, 2410, 1600, '18,90 m (intérieur)'),
        f'<line class="grid" x1="405" y1="805" x2="1478" y2="805"/><line class="grid" x1="405" y1="1517" x2="1478" y2="1517"/>',
        f'<line class="grid" x1="405" y1="805" x2="405" y2="1517"/><line class="grid" x1="1478" y1="805" x2="1478" y2="1517"/>',
        f'<text class="cote" x="1180" y="1505" text-anchor="middle">trame des poteaux 8,94 × 5,93 m</text>',
        f'<circle class="ring" cx="406" cy="1313" r="152"/><text class="cote" x="290" y="1500" text-anchor="middle">⌀ 2,53 m</text>',
        f'<circle class="ring" cx="1082" cy="2172" r="180"/><text class="cote" x="1082" y="2385" text-anchor="middle">⌀ 3,00 m</text>',
        cote_h(412, 1187, 615, '6,45 m')]
svg += [tag(*t) for t in TAGS]
svg.append('</svg>')
PLAN = '\n'.join(svg)


def row(cells, th=False):
    t = 'th' if th else 'td'
    return '<tr>' + ''.join(f'<{t}>{c}</{t}>' for c in cells) + '</tr>'


ECHELLE = [('Cuvette de WC (largeur)', '45 px', '0,36 – 0,40 m', '113 – 125'),
           ('Vasque des WC femmes', '70 × 50 px', '0,60 × 0,45 m', '111 – 117'),
           ('Fauteuil (largeur)', '70 px', '0,55 – 0,62 m', '113 – 127'),
           ('Entraxe des tabourets du bar', '72 px', '0,60 – 0,65 m', '111 – 120'),
           ('Table carrée de deux', '92 px', '0,75 – 0,80 m', '115 – 123')]

DIMS = [('Intérieur hors tout', '10,6 × 18,9 m, environ 188 m²'),
        ('Salle (zone 3)', 'environ 10 × 9,6 m'),
        ('Trame des poteaux', '8,94 m en largeur, 5,93 m en profondeur'),
        ('Poteaux', '⌀ 1,10 m dans la façade droite, ⌀ 0,80 m côté banquettes'),
        ('Banquettes-tambours (A)', '⌀ 2,53 m hors tout, paroi 0,17 m, table ronde ⌀ 0,95 m'),
        ('Grandes tables (B)', '0,79 × 1,2 m (4 places) et 0,79 × 3,7 m (12 places)'),
        ('Comptoir du bar (E)', '6,45 m, arrière-bar 5,0 m, 7 tabourets à 0,60 m'),
        ('Escalier hélicoïdal (F)', '⌀ 3,0 m, 19 marches de 21°, environ 400° en tout'),
        ('Façades vitrées', 'gauche 11,1 m + 4,8 m (bar), droite 12,4 m, entrée 2,0 m')]

HAUTEURS = [('Rez-de-chaussée sous la mezzanine', '≈ 3,35 m de sol à sol', 'le bar, les tables de droite'),
            ('Double hauteur', '≈ 5,0 m', 'au-dessus des tambours et des grandes tables (le vide de floor2)'),
            ('Tambours', '≈ 3,0 m', 'ouverts jusqu\'à 2,2 m, couronne fermée au-dessus'),
            ('Marches', '19 × 17,6 cm', 'la 19e arrive à −18° sur floor2 (repère DN), le compte tombe juste')]

INVENTAIRE = [('A', 'Banquettes-tambours', '4', '3 fauteuils + banquette courbe', '≈ 20'),
              ('B', 'Grandes tables', '2', '4 et 12 chaises', '16'),
              ('C', 'Tables centrales', '3', '4, 2 et 2 chaises', '8'),
              ('D', 'Tables sur banquette', '4', 'chaises d\'un côté, banquette murale de l\'autre', '14'),
              ('E', 'Comptoir du bar', '1', '7 tabourets', '7'),
              ('', '<b>Total</b>', '<b>13 + bar</b>', '', '<b>≈ 65 couverts</b>'),
              ('F', 'Escalier hélicoïdal', '1', 'au-dessus d\'un lit de gravier et de rochers', ''),
              ('G', 'Postes de service (?)', '3', 'carrés de 0,57 m, symbole ▯▯ : à confirmer', ''),
              ('', 'Plantes en pot', '3', '', ''),
              ('', 'Rideaux', '3', 'devant l\'accueil et au bout des tambours', '')]

QUESTIONS = [
    '<b>« Floor1 »</b> : c\'est bien le rez-de-chaussée, avec l\'entrée, l\'accueil et le bar (le fichier floor1.png) ?',
    '<b>D\'où vient le plan</b> (le projet, l\'architecte) ? Les photos de la vraie salle donneraient les matières, et il faudra le citer si le projet est montré.',
    '<b>Le restaurant</b> : on garde ce plan tel quel et on invente un nom, une carte et une équipe fictifs pour les données en direct ?',
    '<b>Les carrés G</b> (▯▯) : postes de service, consoles ou prises au sol ? Et la zone 10, en haut à droite : une cour, une ruelle ?',
    '<b>Le style</b> : voir la planche de la recherche. Je propose de prototyper trois styles sur cette coque avant de modéliser le mobilier.',
]


def table(head, rows):
    return '<table>' + row(head, th=True) + ''.join(row(r) for r in rows) + '</table>'


R1 = '../../rendus/1-coque/'
html = f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><link rel="stylesheet" href="style.css">
<style>
svg.plan .dim{{stroke:#111;stroke-width:3}}
svg.plan .grid{{stroke:#111;stroke-width:2.5;stroke-dasharray:14 10;fill:none}}
svg.plan .ring{{fill:none;stroke:#111;stroke-width:3;stroke-dasharray:6 6}}
svg.plan .cote{{font:500 30px Inter,sans-serif;fill:#111;paint-order:stroke;stroke:#fff;stroke-width:9px;stroke-linejoin:round}}
svg.plan .tag{{fill:#111}}
svg.plan .tagt{{fill:#fff;font:600 28px Inter,sans-serif}}
.lead{{max-width:560px}}
td:first-child{{white-space:nowrap}}
</style></head><body>
<div class="colw">
<section>
  <div class="stitle">Restaurant · floor1 · étape 1 : le plan lu, mesuré, et la coque</div>
  <div class="snote">24/11/2026 · d'après floor1.png et la coupe 3d-1.png</div>
  <div class="txt lead">Le plan est lu, mesuré et posé au sol dans Blender, à l'échelle réelle. La coque est modélisée par-dessus : murs, poteaux, façades vitrées, tambours des banquettes et escalier. Le mobilier viendra à l'étape suivante, une fois le style choisi.</div>
</section>
<section>
  <div class="stitle">Le plan, lu et coté</div>
  <div class="snote">lettres : les éléments de la salle (voir l'inventaire) · cotes à 120 px = 1 m</div>
  {PLAN}
</section>
</div>
<div class="colw">
<section style="width:640px">
  <div class="stitle">L'échelle</div>
  <div class="snote">le plan n'a pas d'échelle : cinq objets de taille connue la donnent</div>
  {table(['Objet', 'Sur le plan', 'En vrai', 'px / m'], ECHELLE)}
  <div class="txt">Les cinq mesures se recoupent autour de <b>120 px par mètre</b> (1 px ≈ 8,3 mm), à ±5 %. Les cotes ci-dessous en découlent.</div>
</section>
<section style="width:640px">
  <div class="stitle">Les dimensions</div>
  {table(['', ''], DIMS)}
</section>
<section style="width:640px">
  <div class="stitle">Les hauteurs</div>
  <div class="snote">d'après la coupe 3d-1, mise à la même échelle par la profondeur du bâtiment</div>
  {table(['', '', ''], HAUTEURS)}
</section>
<section style="width:640px">
  <div class="stitle">Ce que contient floor1</div>
  {table(['', 'Élément', 'Nombre', 'Détail', 'Couverts'], INVENTAIRE)}
  <div class="txt">Pour le système de gestion, la salle compte <b>13 tables et le comptoir</b>. Chacune aura un numéro, une capacité et une zone.</div>
</section>
</div>
<div class="colw">
<section>
  <div class="stitle">La coque dans Blender</div>
  <div class="snote">rendus en argile, sans mobilier · tout est refait par le script outils/blender/floor1.py</div>
  <div class="row">
    <figure><img src="{R1}1-calage-vue-de-dessus.png" width="480"><div class="cap">1 · Le calage, vu de dessus : les murs extrudés tombent sur ceux du plan.</div></figure>
    <div class="col">
      <figure><img src="{R1}3-coque-coupee-sur-le-plan.png" width="860"><div class="cap">2 · La coque coupée à 1,20 m, sur le plan : la lecture « carte ».</div></figure>
    </div>
  </div>
  <div class="row">
    <figure><img src="{R1}2-coque-axonometrie.png" width="680"><div class="cap">3 · Toute la hauteur du rez-de-chaussée (3,35 m), sans plafond.</div></figure>
    <figure><img src="{R1}4-coque-depuis-le-bar.png" width="660"><div class="cap">4 · Depuis le bar : les quatre tambours, l'escalier et l'entrée.</div></figure>
  </div>
</section>
<section>
  <div class="stitle">Quatre styles, essayés sur la coque</div>
  <div class="snote">la même coque coupée à 1,20 m, sans mobilier : un premier aperçu, à juger avec la planche de la recherche</div>
  <div class="row">
    <figure><img src="../../rendus/2-styles-sur-la-coque/style-trait.png" width="680"><div class="cap">A · Trait, comme la vidéo : blanc, traits fins, ombres douces.</div></figure>
    <figure><img src="../../rendus/2-styles-sur-la-coque/style-trait-sombre.png" width="680"><div class="cap">A′ · Trait sombre : la même carte pour le service, en salle tamisée.</div></figure>
  </div>
  <div class="row">
    <figure><img src="../../rendus/2-styles-sur-la-coque/style-maquette.png" width="680"><div class="cap">B · Maquette : carton blanc et bois, posée sur son socle.</div></figure>
    <figure><img src="../../rendus/2-styles-sur-la-coque/style-jeu.png" width="680"><div class="cap">C · Pièce de jeu : couleurs chaudes, arêtes adoucies, lumière dorée.</div></figure>
  </div>
</section>
<section>
  <div class="stitle">Questions</div>
  <ol class="list">{''.join(f'<li>{q}</li>' for q in QUESTIONS)}</ol>
</section>
</div>
</body></html>'''
(PG / 'etape-1.html').write_text(html)
(R / 'pages').mkdir(exist_ok=True)
out = R / 'pages' / '1-plan-et-coque.png'
subprocess.run(['node', str(PG / 'export.mjs'), str(PG / 'etape-1.html'), str(out), '1'], check=True)
