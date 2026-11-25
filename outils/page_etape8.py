# The working page of the 1st floor's step 1 (as floor1's step 1, page_etape1.py): floor2 read and measured, then the
# shell modelled over it. Writes outils/pages/etape-8.html, then pages/8-etage-coque.png with outils/pages/export.mjs.
# usage: outils/.venv/bin/python outils/page_etape8.py
import subprocess
from pathlib import Path

R = Path(__file__).resolve().parents[1]
PG = R / 'outils' / 'pages'


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


TAGS = [(1240, 770, 'A'), (1240, 1031, 'A'), (847, 848, 'B'), (850, 640, 'C'), (740, 1050, 'D'),
        (1225, 1330, 'E'), (1225, 1677, 'E'), (1225, 1880, 'E'), (1082, 2172, 'F'), (700, 193, 'G'),
        (730, 2130, 'H')]
svg = ['<svg class="plan" viewBox="150 20 1520 2500" width="900" height="1480">',
       '<image href="../../floor2.png" x="0" y="0" width="2000" height="2828" style="filter:invert(1) grayscale(1) contrast(.9) brightness(1.05)"/>']
svg += [cote_h(232, 1457, 2470, '10,20 m (intérieur)', up=False), cote_v(140, 2245, 1600, '17,55 m (intérieur)'),
        cote_h(237, 1082, 1250, '7,05 m (le vide)')]
svg += [tag(*t) for t in TAGS]
svg.append('</svg>')
PLAN = '\n'.join(svg)


def row(cells, th=False):
    t = 'th' if th else 'td'
    return '<tr>' + ''.join(f'<{t}>{c}</{t}>' for c in cells) + '</tr>'


def table(head, rows):
    return '<table>' + row(head, th=True) + ''.join(row(r) for r in rows) + '</table>'


DIMS = [('Intérieur hors tout', '10,2 × 17,6 m, le vide compris'),
        ('Le vide sur la salle', '7,05 m de large ; il descend le long de la façade gauche jusqu\'au fond'),
        ('Le vide sur le jardin', 'au-dessus du gravier et de l\'escalier hélicoïdal (ouverture ⌀ 3,07 m)'),
        ('Poteaux', 'les quatre du rez-de-chaussée montent : ⌀ 0,80 à 1,15 m'),
        ('Demi-tambours (A)', '⌀ 2,08 m hors tout, paroi 0,13 m, table ronde ⌀ 0,80 m'),
        ('Grande table (B)', '4,3 × 0,78 m, 10 chaises'),
        ('Bar omakase (C)', 'plan des barmen 4,5 m, plateau client 4,9 m, 6 tabourets'),
        ('Tablette (D)', '5,1 m au bord du vide, 0,48 m de profondeur, 6 tabourets')]

HAUTEURS = [('Sol de la mezzanine', '+ 3,35 m', 'le dessus de la dalle de 0,30 m, au niveau de la 19e marche'),
            ('Sous plafond', '≈ 3,00 m', 'hypothèse, d\'après la coupe 3d-1'),
            ('Demi-tambours', '2,20 m', 'comme la partie basse des tambours du rez-de-chaussée'),
            ('Garde-corps', '1,05 m', 'en verre, au bord du vide et de l\'ouverture de l\'escalier')]

INVENTAIRE = [('A', 'Demi-tambours', '2', 'table ronde, 2 fauteuils et banquette', '≈ 8'),
              ('B', 'Grande table', '1', '10 chaises', '10'),
              ('C', 'Bar omakase', '1', '6 tabourets', '6'),
              ('D', 'Tablette au bord du vide', '1', '6 tabourets', '6'),
              ('E', 'Tables le long de la façade', '3', '3, 2 et 2 chaises, une bande continue derrière', '7 +'),
              ('', '<b>Total</b>', '<b>7 + bar + tablette</b>', '', '<b>≈ 37 couverts</b>'),
              ('F', 'Escalier hélicoïdal', '1', 'son arrivée (repère DN)', ''),
              ('G', 'Escalier droit', '1', 'vers l\'étage du toit (UP)', ''),
              ('H', 'Volume au-dessus de l\'entrée', '1', 'plein sur le plan, une boîte fermée sur l\'axonométrie', ''),
              ('', 'Laboratoire, toilettes, ascenseur', '', 'zones 2, 5 et 4 du plan', ''),
              ('', 'Rideaux', '2', 'le palier de l\'escalier droit, le passage vers l\'ascenseur', '')]

DECISIONS = [
    '<b>Le repère</b> : floor2.png est dessiné dans les mêmes pixels que floor1.png. La mezzanine garde donc le même '
    'repère et la même origine que le rez-de-chaussée, et la carte pourra passer d\'un étage à l\'autre sans décalage.',
    '<b>Les murs</b> sont vectorisés depuis le plan (<code>outils/vectoriser_etage1.py</code>). Le laboratoire est fermé '
    'côté vide, dans le prolongement du mur dessiné.',
    '<b>Le volume au-dessus de l\'entrée</b> : aucune photo ne le montre. Il est modélisé plein, comme sur le plan et '
    'l\'axonométrie, et habillé à l\'étape 2 comme le portail d\'entrée.',
]

R1 = '../../rendus/12-etage-coque/'
html = f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><link rel="stylesheet" href="style.css">
<style>
.lead{{max-width:560px}}
td:first-child{{white-space:nowrap}}
</style></head><body>
<div class="colw">
<section>
  <div class="stitle">Restaurant · 1er étage · étape 1 : le plan lu, mesuré, et la coque</div>
  <div class="snote">24/11/2026 · d'après floor2.png, la coupe 3d-1.png et l'axonométrie 3d-2.png</div>
  <div class="txt lead">Comme pour le rez-de-chaussée, le plan de la mezzanine est lu, mesuré et posé dans Blender, à
  l'échelle réelle et 3,35 m plus haut. La coque est modélisée par-dessus : murs, poteaux, façades, la dalle percée de
  ses vides, les garde-corps, les deux demi-tambours, les escaliers et le volume au-dessus de l'entrée.</div>
</section>
<section>
  <div class="stitle">Le plan, lu et coté</div>
  <div class="snote">lettres : les éléments de la mezzanine (voir l'inventaire) · cotes à 120 px = 1 m, la même échelle qu'en bas</div>
  {PLAN}
</section>
</div>
<div class="colw">
<section style="width:640px">
  <div class="stitle">Les dimensions</div>
  {table(['', ''], DIMS)}
</section>
<section style="width:640px">
  <div class="stitle">Les hauteurs</div>
  {table(['', '', ''], HAUTEURS)}
</section>
<section style="width:640px">
  <div class="stitle">Ce que contient la mezzanine</div>
  {table(['', 'Élément', 'Nombre', 'Détail', 'Couverts'], INVENTAIRE)}
  <div class="txt">Pour le système de gestion, la mezzanine compte <b>6 tables, le bar omakase et la tablette</b>.
  Leurs numéros suivront ceux du rez-de-chaussée.</div>
</section>
<section style="width:640px">
  <div class="stitle">Les choix</div>
  <ul class="list">{''.join(f'<li>{d}</li>' for d in DECISIONS)}</ul>
</section>
</div>
<div class="colw">
<section>
  <div class="stitle">La coque dans Blender</div>
  <div class="snote">rendus en argile, sans mobilier · tout est refait par le script outils/blender/floor2.py</div>
  <div class="row">
    <figure><img src="{R1}1-calage-vue-de-dessus.png" width="480"><div class="cap">1 · Le calage, vu de dessus : les murs extrudés tombent sur ceux du plan.</div></figure>
    <div class="col">
      <figure><img src="{R1}3-coque-coupee-a-1m20.png" width="860"><div class="cap">2 · La coque coupée à 1,20 m : la lecture « carte ».</div></figure>
    </div>
  </div>
  <div class="row">
    <figure><img src="{R1}2-coque-axonometrie.png" width="860"><div class="cap">3 · Toute la hauteur de la mezzanine (3,00 m), sans plafond : la dalle percée de ses vides et les garde-corps.</div></figure>
  </div>
</section>
</div>
</body></html>'''
(PG / 'etape-8.html').write_text(html)
out = R / 'pages' / '8-etage-coque.png'
subprocess.run(['node', str(PG / 'export.mjs'), str(PG / 'etape-8.html'), str(out), '1'], check=True)
