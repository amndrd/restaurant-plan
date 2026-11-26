# The working page of the reworked places (26/11 evening): the six places the user pointed out on the map, in the
# order of the captures, each before (the user's capture) and after (the renders of rendus/21-reprises/).
# Writes outils/pages/etape-16.html, then pages/16-reprises.png.
# usage: outils/.venv/bin/python outils/page_etape16.py   (after the renders of rendus/21-reprises/)
import subprocess
from pathlib import Path

R = Path(__file__).resolve().parents[1]
PG = R / 'outils' / 'pages'
Z = '../../rendus/21-reprises/'

POINTS = [
    ('1 · La tablette du balcon et le garde-corps',
     'Le corps plein de la tablette s\'arrêtait net contre le verre : deux hauteurs et deux matières côte à côte.',
     'Le garde-corps en verre court maintenant tout le long du vide, sous la tablette. La tablette en chêne (30 cm de '
     'profondeur, bout arrondi) en devient le chapeau, de 1,02 à 1,08 m. Côté salle, des pieds fins en acier la '
     'portent, avec un repose-pieds pour les tabourets. La main courante prend le relais là où la tablette s\'arrête.',
     ['plan-tablette.png']),
    ('2 · Les lumières au-dessus du vide',
     'Les suspensions des tables du bas, sous le vide, pendaient d\'un fil coupé au niveau de la dalle.',
     'Elles descendent maintenant du plafond du 1er au bout de longs câbles, à travers la double hauteur. Sur la carte, '
     'comme les murs, les câbles sont pleins jusqu\'à 1,20 m au-dessus du plancher du 1er et transparents au-dessus.',
     ['plan-vide-lumieres.png']),
    ('3 · Le bar omakase et sa cuisine',
     'L\'escalier était déjà retiré depuis midi : ta capture venait de l\'ancien modèle, gardé en cache par le '
     'navigateur (la carte recharge maintenant toujours ses modèles). Autour du bar, le plan laissait huit petits murs '
     'sans usage, et des doublures dans le mur du fond.',
     'Les petits murs sont retirés. <b>Le bar</b> a un plateau en hinoki et un devant en lattes de chêne verticales, '
     'un repose-pieds en acier, trois vitrines à neta côté chef, des bouteilles de saké dans la moitié des casiers et '
     'trois suspensions au-dessus du comptoir. <b>La cuisine</b> est au bout du bar, côté façade : la ligne de cuisson '
     'sous sa hotte (deux plaques à induction, une plancha), le plan de préparation et son évier le long des pavés de '
     'verre, une armoire froide. Elle est ouverte sur l\'allée du chef et sur la réserve, et fermée côté salle par une '
     'cloison vitrée. <b>La réserve</b> passe derrière le fond du bar, sur toute sa longueur. <b>Les toilettes</b> ont '
     'maintenant leur porte, derrière le rideau du passage.',
     ['plan-bar.png', 'plan-cuisine.png']),
    ('4 · Le comptoir du labo',
     'Un simple bloc, trois objets dessus.',
     'Un meuble en chêne à lattes verticales sur un socle en retrait, sous un plateau de pierre arrondi côté salle. '
     'Dessus, une cloche en verre sur une planche, trois bocaux de fermentation et un batteur. Derrière, le long du '
     'mur, le plan de travail du labo avec son évier et deux étagères ouvertes chargées de bocaux.',
     ['plan-labo.png']),
    ('5 · Le jardin sec sous l\'escalier',
     'Un sol de gravier plat, des roches taillées à facettes.',
     'Le gravier est ratissé, en lignes droites et en cercles autour des groupes de pierres. Les pierres sont refaites, '
     'polies par l\'eau : une grande pierre dressée avec deux plus basses, une paire, et une pierre seule sous '
     'l\'escalier. Deux petits projecteurs posés dans le gravier les éclairent par en dessous.',
     ['plan-jardin-sec.png']),
    ('6 · L\'accueil du rez-de-chaussée',
     'Une boîte en guise de bureau et une console, dans un couloir vide.',
     'Le bureau d\'accueil est contre le mur : son devant forme un léger arc en lattes de chêne, sous un plateau de '
     'pierre à 1,05 m, avec un tabouret haut et une suspension. Derrière, un panneau de tasseaux de chêne porte une '
     'niche éclairée et une plaque en laiton. Il y a aussi un banc en chêne sur deux blocs de pierre près du rideau, '
     'un tapis de la porte à la salle, et un olivier dans un pot de pierre près de l\'entrée.',
     ['plan-accueil.png']),
]
QUESTIONS = [
    'Ces six reprises te vont-elles ?',
    'Y a-t-il d\'autres endroits à reprendre ?',
    'Ensuite : je refais les plans des deux étages d\'après le modèle, et je refais les captures de la carte.',
    'Rappel : le lien et la licence du modèle « ivy-for-walls », pour le créditer.',
]


def img(src, w, cap=None):
    c = f'<div class="cap">{cap}</div>' if cap else ''
    return f'<figure><img src="{src}" width="{w}">{c}</figure>'


blocs = []
for k, (titre, avant, apres, rendus) in enumerate(POINTS, start=1):
    larg = 470 if len(rendus) > 1 else 600
    imgs = img(Z + f'avant-{k}.png', 420 if len(rendus) > 1 else 480, 'Avant (ta capture)') + \
        ''.join(img(Z + r, larg, 'Après') for r in rendus)
    blocs.append(f'''<div class="lbl" style="margin-top:20px">{titre}</div>
  <div class="row">{imgs}</div>
  <div class="txt" style="max-width:1460px"><b>Ce qui n'allait pas.</b> {avant}</div>
  <div class="txt" style="max-width:1460px"><b>Ce que j'ai fait.</b> {apres}</div>''')

html = f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><link rel="stylesheet" href="style.css">
<style>.lead{{max-width:900px}}</style></head><body>
<div class="colw">
<section style="width:1520px">
  <div class="stitle">Restaurant · les endroits repris, un par un</div>
  <div class="snote">26/11/2026 · le coin du 1er en station de service (A), et les six endroits de tes captures</div>
  <div class="txt lead">Tu as choisi la station de service pour le coin du 1er. Voici les six endroits de tes captures,
  dans leur ordre, chacun avant et après.</div>
  {''.join(blocs[:3])}
</section>
</div>
<div class="colw">
<section style="width:1520px">
  {''.join(blocs[3:])}
</section>
<section style="width:1520px">
  <div class="stitle">Sur la carte</div>
  <div class="row">{img(Z + 'fantome-3d.png', 740, 'Le 1er, sur le rez-de-chaussée')}{img(Z + 'rdc/fantome-3d.png', 740, 'Le rez-de-chaussée seul')}</div>
</section>
<section style="width:760px">
  <div class="stitle">Questions</div>
  <ol class="list">{''.join(f'<li>{q}</li>' for q in QUESTIONS)}</ol>
</section>
</div>
</body></html>'''
(PG / 'etape-16.html').write_text(html)
out = R / 'pages' / '16-reprises.png'
subprocess.run(['node', str(PG / 'export.mjs'), str(PG / 'etape-16.html'), str(out), '1'], check=True)
