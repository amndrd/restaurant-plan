# The working page of the 1st floor's step 3 (as floor1's step 4, page_etape4.py): the furniture of the mezzanine,
# placed from the plan, in the two map views, the table numbers of the live map (after floor1's), three close-ups next
# to the photos they echo.
# Writes outils/pages/etape-11.html, then pages/11-etage-mobilier.png with outils/pages/export.mjs.
# usage: outils/.venv/bin/python outils/page_etape11.py   (after floor2.py mobilier=1 and numeros_tables.py etage1)
import json
import subprocess
from pathlib import Path

R = Path(__file__).resolve().parents[1]
PG = R / 'outils' / 'pages'
RS = '../../rendus/15-etage-mobilier/'
PH = '../../recherche/11-lair-archdaily/'

tables = json.loads((R / 'modele' / 'floor2-tables.json').read_text())['tables']
places = sum(t['places'] for t in tables)

PLANS = [
    ('grande', 10, 'La grande table et le bar omakase',
     'La grande table est à 0,75 m, avec les dix chaises fines en acier du rez-de-chaussée, sur trois pieds : ce sont '
     'les trois points du plan. Une suspension plate au-dessus de chaque pied. Derrière, les six tabourets du bar '
     'omakase, comme ceux du bar du bas.'),
    ('demi', 20, 'Les deux demi-tambours',
     'Dans chacun, une table ronde de 0,80 m sur un pied conique (le cercle du plan), deux fauteuils côté salle et la '
     'banquette en demi-cercle. Une suspension plate et une lampe, comme dans les tambours du bas.'),
    ('facade', 8, 'Les tables hautes de la façade droite',
     'Trois tables hautes à 1,05 m, avec 3, 2 et 2 tabourets côté salle. Derrière elles, la bande continue du plan est '
     'une tablette en bois sous les pavés de verre, qui contourne le poteau : exactement comme au rez-de-chaussée.'),
]

CHOIX = [
    '<b>La bande le long de la façade droite</b> (ma question d\'hier, pas claire) : derrière les trois tables de '
    'droite, le plan dessine une bande continue qui longe la vitre et fait le tour du poteau. Au rez-de-chaussée, la '
    'même bande est une tablette en bois, avec des tables hautes et des tabourets (photo 8). Je l\'ai donc faite '
    'pareille ici, pour que les deux étages soient cohérents.',
    '<b>La tablette au bord du vide</b> a ses six tabourets, tournés vers le vide : on y boit un verre en regardant la '
    'salle du bas.',
    '<b>Le laboratoire</b> a ses trois machines du plan sur le comptoir : un appareil, un mixeur et un bol.',
    '<b>Au bout de la façade</b>, le rectangle du plan est une console basse en bois.',
    '<b>Les numéros</b> suivent ceux du rez-de-chaussée (1 à 17) : 18 et 19 les demi-tambours, 20 la grande table, '
    '21 à 23 les tables hautes. Le bar omakase et la tablette sont suivis tabouret par tabouret, comme le bar du bas.',
    '<b>Les suspensions</b> sont masquées dans la vue du haut, comme en bas.',
]

QUESTIONS = [
    'Les tables, les hauteurs et la tablette de la façade te vont-elles ?',
    'La numérotation (18 à 23, plus l\'omakase et la tablette) te va-t-elle pour la carte ?',
    'La suite : l\'export du 1er étage pour la carte, puis le bouton « 1er » qui fait passer d\'un étage à l\'autre, '
    'avec le service simulé sur les deux étages. On y va ?',
]


def vues(code, titre, texte):
    return f'''<section>
  <div class="stitle">{titre}</div>
  <div class="txt lead">{texte}</div>
  <div class="row">
    <figure><img src="{RS}{code}-dessus.png" width="800"><div class="cap">Vue du haut</div></figure>
    <figure><img src="{RS}{code}-3d.png" width="800"><div class="cap">Vue 3D</div></figure>
  </div>
</section>'''


def plan(code, photo, titre, texte):
    return f'''<section style="width:max-content">
  <div class="stitle">{titre}</div>
  <div class="row">
    <figure><img src="{RS}plan-{code}.png" height="520"><div class="cap">Le modèle, en blanc et à pleine hauteur</div></figure>
    <figure><img class="th" src="{PH}photo-{photo}.jpg" height="520"><div class="cap">Le vrai lieu, photo {photo} (au rez-de-chaussée)</div></figure>
  </div>
  <div class="txt" style="max-width:760px">{texte}</div>
</section>'''


NOMS_BARS = {100: 'Omakase', 101: 'Tablette'}


def ligne(t):
    num = NOMS_BARS.get(t['id'], str(t['id']))
    return f'<tr><td><b>{num}</b></td><td>{t["nom"]}</td><td>{t["places"]}</td><td>{t["assises"]}</td></tr>'


html = f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><link rel="stylesheet" href="style.css">
<style>.lead{{max-width:760px}}</style></head><body>
<div class="colw">
<section>
  <div class="stitle">Restaurant · 1er étage · étape 3 : le mobilier</div>
  <div class="snote">25/11/2026 · comme l'étape 4 du rez-de-chaussée : placé d'après le plan, en fantôme et en fil de fer</div>
  <div class="txt lead">Tu as validé la liste du mobilier. Voici celui de la mezzanine, avec les mêmes pièces qu'au
  rez-de-chaussée : 6 tables de service, le bar omakase et ses 6 tabourets, la tablette au bord du vide et ses 6
  tabourets, la tablette en bois de la façade, les machines du laboratoire, les suspensions et les lampes de table.
  Chaque table porte un numéro, à la suite de ceux du rez-de-chaussée. Aucun meuble ne touche un autre élément du
  modèle.</div>
</section>
{vues('fantome', 'Fantôme, le style par défaut',
      'Le mobilier est coupé à 1,20 m comme le reste. Vu du haut, les suspensions sont masquées ; en 3D, elles sont en '
      'fantôme. Sous la mezzanine, le rez-de-chaussée meublé, en gris clair.')}
<section style="width:max-content">
  <div class="stitle">Les numéros de la carte</div>
  <div class="row">
    <figure><img src="{RS}tables-numerotees.png" width="1100"><div class="cap">La vue du haut, avec le numéro de chaque table</div></figure>
    <div class="col" style="width:520px">
      <table><tr><th>N°</th><th>Table</th><th>Places</th><th>Assises</th></tr>
      {''.join(ligne(t) for t in tables)}</table>
      <div class="txt">{places} places à l'étage, 68 au rez-de-chaussée. La liste est dans
      <code>modele/floor2-tables.json</code>, avec la position de chaque table sur le plan et dans le modèle.</div>
    </div>
  </div>
</section>
</div>
<div class="colw">
{''.join(plan(*p) for p in PLANS)}
</div>
<div class="colw">
{vues('fil-de-fer', 'Fil de fer, au choix dans l\'application', 'Le même modèle, en arêtes seulement.')}
<section style="width:760px">
  <div class="stitle">Les choix que j'ai faits</div>
  <ul class="list">{''.join(f'<li>{c}</li>' for c in CHOIX)}</ul>
</section>
<section style="width:760px">
  <div class="stitle">Questions</div>
  <ol class="list">{''.join(f'<li>{q}</li>' for q in QUESTIONS)}</ol>
</section>
<section style="width:760px">
  <div class="stitle">Sources</div>
  <div class="txt">LAIR Restaurant &amp; Bar, Gurugram, par RENESA Architecture Design Interiors Studio (2024). Les
  photos sont d'Avesh Gaur, sur ArchDaily. Elles servent seulement de référence pour la modélisation.</div>
</section>
</div>
</body></html>'''
(PG / 'etape-11.html').write_text(html)
out = R / 'pages' / '11-etage-mobilier.png'
subprocess.run(['node', str(PG / 'export.mjs'), str(PG / 'etape-11.html'), str(out), '1'], check=True)
