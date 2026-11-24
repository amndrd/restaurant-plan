# The working page of step 2: the white styles, each in the two views of the map (top and 3D),
# the switch between the two views, and what the ArchDaily photos of the real restaurant teach.
# Writes outils/pages/etape-2.html, then pages/2-styles-blancs.png with outils/pages/export.mjs.
# usage: outils/.venv/bin/python outils/page_etape2.py
import subprocess
from pathlib import Path

R = Path(__file__).resolve().parents[1]
PG = R / 'outils' / 'pages'
RS = '../../rendus/3-styles-blancs/'
PH = '../../recherche/11-lair-archdaily/'

VARIANTES = [
    ('1-blanc', '1 · Blanc',
     'Les murs pleins, coupés à 1,20 m, avec des ombres douces et des contours gris. C\'est la plus lisible vue du haut. '
     'En 3D, elle ressemble à une maquette.'),
    ('2-blanc-grille', '2 · Blanc sur grille',
     'La même, posée sur une grille au mètre, avec un trait plus marqué tous les 5 m. La grille donne l\'échelle et '
     'l\'air d\'une carte. Elle s\'efface au loin.'),
    ('3-fantome', '3 · Fantôme',
     'Le bas des murs est plein jusqu\'à 1,20 m, le haut est presque invisible, comme du verre dépoli. On garde la '
     'lecture de plan de la 1 et on voit en plus le volume de la salle : façades, poteaux, anneaux des tambours.'),
    ('4-transparent', '4 · Transparent',
     'Toute la hauteur en blanc translucide, avec les arêtes cachées en gris clair. On voit à travers tout.'),
    ('5-fil-de-fer', '5 · Fil de fer',
     'Seulement les arêtes : les arêtes visibles en gris foncé, les arêtes cachées en gris clair. C\'est un dessin '
     'technique, très léger.'),
]

PHOTOS = [
    (17, 'La banquette dans un tambour : dossier courbe, bandeau de pierre éclairé, table ronde sur pied, suspension.'),
    (24, 'Le haut du tambour est un anneau de métal suspendu au-dessus de la banquette.'),
    (33, 'Deux tambours de face, avec le poteau entre les deux.'),
    (3, 'L\'escalier hélicoïdal en métal sombre, et les façades en pavés de verre.'),
    (4, 'Au pied de l\'escalier, un jardin de pierres : c\'est la zone de gravier du plan.'),
    (6, 'Le bar et son étagère rétroéclairée.'),
]

ETAPES_PASSAGE = [0, 9, 18, 27, 36]

QUESTIONS = [
    'Quelle variante retiens-tu ? On peut aussi en mélanger deux, par exemple le fantôme sur la grille, '
    'ou le blanc avec le fil de fer en 3D seulement.',
    'Pour la vue du haut, le plan est tourné pour remplir l\'écran d\'une tablette posée à l\'horizontale : '
    'le bar à gauche, l\'entrée à droite, la rue en bas. Ça te va ?',
    'Ensuite, je modélise les éléments fixes d\'après les photos : le bar, les banquettes dans les tambours, '
    'l\'escalier en détail, les pavés de verre et le jardin de pierres. Puis viendra le mobilier. On continue comme ça ?',
]


def variante(code, titre, texte):
    return f'''<section>
  <div class="stitle">{titre}</div>
  <div class="txt lead">{texte}</div>
  <div class="row">
    <figure><img src="{RS}{code}-dessus.png" width="800"><div class="cap">Vue du haut</div></figure>
    <figure><img src="{RS}{code}-3d.png" width="800"><div class="cap">Vue 3D</div></figure>
  </div>
</section>'''


photos = ''.join(f'<figure style="width:210px"><img class="th" src="{PH}photo-{n}.jpg" width="210" height="262">'
                 f'<div class="cap">{n} · {t}</div></figure>' for n, t in PHOTOS)
passage = ''.join(f'<figure><img src="{RS}transition-fantome/{k:03d}.png" width="316">'
                  f'<div class="cap">{f"{k / 24:.2f}".replace(".", ",")} s</div></figure>' for k in ETAPES_PASSAGE)

html = f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><link rel="stylesheet" href="style.css">
<style>.lead{{max-width:760px}} td:first-child{{white-space:nowrap}}</style></head><body>
<div class="colw">
<section>
  <div class="stitle">Restaurant · floor1 · étape 2 : le style blanc, vu du haut et en 3D</div>
  <div class="snote">24/11/2026 · la coque de l'étape 1, sans mobilier</div>
  <div class="txt lead">Tu imaginais un style blanc, avec une grille, un peu transparent, et deux points de vue : une vue du
  haut, et une vue 3D vers laquelle on bascule. Voici cinq variantes, chacune dans les deux vues. Les deux vues ont le même
  cadre, au format 16:10 d'une tablette. Le soleil reste fixe, comme il le sera dans l'application : seule la caméra bouge.</div>
</section>
{''.join(variante(*v) for v in VARIANTES[:3])}
</div>
<div class="colw">
{''.join(variante(*v) for v in VARIANTES[3:])}
<section>
  <div class="stitle">Passer de la vue du haut à la vue 3D</div>
  <div class="snote">variante 3 · la caméra se penche et tourne de 45° en 1,5 s · la vidéo : rendus/3-styles-blancs/passage-dessus-3d-fantome.mp4</div>
  <div class="row tight">{passage}</div>
</section>
<section>
  <div class="stitle">Mon avis</div>
  <div class="txt lead">Je retiendrais <b>la 3, le fantôme, sur la grille</b>. Vue du haut, elle se lit comme un plan : les
  tables et leurs couleurs d'état ressortiront sur les murs bas, pleins et blancs. En 3D, elle garde le volume de la salle
  sans cacher les tables. La 4 et la 5 sont belles à vide, mais avec le mobilier, les arêtes vues par transparence vont
  s'empiler et brouiller la carte. La 1 et la 2 sont les plus sobres, mais la vue 3D y perd la hauteur de la salle.</div>
</section>
</div>
<div class="colw">
<section style="width:760px">
  <div class="stitle">La source : LAIR Restaurant &amp; Bar</div>
  <div class="snote">ArchDaily · les plans d'ArchDaily sont identiques à floor1, floor2, floor3, 3d-1 et 3d-2</div>
  <table>
    <tr><td>Architectes</td><td>RENESA Architecture Design Interiors Studio (architecte principal : Sanchit Arora)</td></tr>
    <tr><td>Lieu</td><td>Gurugram, Inde</td></tr>
    <tr><td>Année</td><td>2024</td></tr>
    <tr><td>Surface</td><td>4 500 ft², environ 418 m² sur les trois niveaux</td></tr>
    <tr><td>Photos</td><td>Avesh Gaur</td></tr>
    <tr><td>Lien</td><td>archdaily.com/1031034/lair-restaurant-bar-renesa-architecture-design-interiors-studio</td></tr>
  </table>
  <div class="txt">Le vrai lieu est un speakeasy sombre, en métal, en pierre et en pavés de verre. Pour la carte, on garde
  sa géométrie exacte, mais on la redessine en blanc. Les 37 photos sont dans <b>recherche/11-lair-archdaily</b>. Elles
  serviront à modéliser juste le bar, les banquettes, l'escalier et le mobilier.</div>
  <div class="row wrap tight">{photos}</div>
  <div class="txt">Ce que les photos ont changé dans le modèle : le haut des tambours est maintenant <b>ouvert</b>. C'est un
  anneau suspendu (photo 24), et la banquette reste visible depuis la vue du haut.</div>
</section>
<section style="width:760px">
  <div class="stitle">Questions</div>
  <ol class="list">{''.join(f'<li>{q}</li>' for q in QUESTIONS)}</ol>
</section>
</div>
</body></html>'''
(PG / 'etape-2.html').write_text(html)
out = R / 'pages' / '2-styles-blancs.png'
subprocess.run(['node', str(PG / 'export.mjs'), str(PG / 'etape-2.html'), str(out), '1'], check=True)
