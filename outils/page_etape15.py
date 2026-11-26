# The working page of the reworked building (26/11): the model no longer follows the client's plan where it made no
# sense. For each place, before and after: the south-east corner (the two places the user circled), the entry, the
# blind facades, the stair that led nowhere, the cloakroom; the whole building; the questions.
# Writes the crops in rendus/20-refonte/, outils/pages/etape-15.html, then pages/15-refonte.png.
# usage: outils/.venv/bin/python outils/page_etape15.py   (after the renders of rendus/20-refonte/)
import subprocess
from pathlib import Path
from PIL import Image

R = Path(__file__).resolve().parents[1]
PG = R / 'outils' / 'pages'
D = R / 'rendus' / '20-refonte'
Z = '../../rendus/20-refonte/'
AVANT = R / 'rendus' / '15-etage-mobilier' / 'fantome-3d.png'          # the map view before (26/11, morning)
AVANT_3D = R / 'rendus' / '18-batiment-entier' / 'detail-3d.png'        # the uncut building before
Z18 = '../../rendus/18-batiment-entier/'

# the same crops of the map's 3D view and of the uncut view, before and after
for nom, src in (('avant', AVANT), ('apres', D / 'fantome-3d.png')):
    im = Image.open(src)
    im.crop((1180, 560, 1780, 1010)).save(D / f'{nom}-angle-1er.png')      # the 1st floor's south-east corner
    im.crop((180, 120, 780, 570)).save(D / f'{nom}-escalier-haut.png')     # the back of the omakase bar
for nom, src in (('avant', AVANT_3D), ('apres', D / 'detail-3d.png')):
    Image.open(src).crop((1220, 700, 1900, 1250)).save(D / f'{nom}-angle-se.png')

LIEUX = [
    ('L\'angle sud-est du 1er (ta 1re capture)',
     'Une console, un bout de mur isolé, deux morceaux de garde-corps et, derrière, une poche fermée au-dessus d\'une '
     'pièce du bas : le plan laissait ce coin sans usage.',
     'Le plancher va jusqu\'aux deux façades : le coin fait partie de la salle, derrière des pavés de verre sur deux '
     'côtés. Le garde-corps du jardin de pierres continue d\'un seul tenant jusqu\'à la façade. Dans le coin, je '
     'propose une station de service (A) le long des pavés de verre, ou une table pour deux (B).',
     [('avant-angle-1er.png', 'Avant'), ('apres-angle-1er.png', 'Après, sur la carte')]),
    ('L\'angle sud-est du bâtiment (ta 2e capture)',
     'Une boîte vide collée à la façade droite, ouverte sur le côté, et une fente ouverte entre elle et l\'entrée : '
     'l\'angle du bâtiment ne se refermait pas, et le 1er s\'arrêtait en retrait au-dessus.',
     'La boîte est retirée. À sa place, le vestiaire de l\'entrée, derrière les mêmes pavés de verre. Un pilier d\'angle '
     'ferme le bâtiment sur les deux étages, et le 1er va jusqu\'à l\'angle.',
     [('avant-angle-se.png', 'Avant'), ('apres-angle-se.png', 'Après')]),
]
AUTRES = [
    ('L\'entrée', 'Le plan laissait la devanture ouverte : la rue entrait dans l\'accueil sans porte ni vitrage. '
     'Elle a maintenant une devanture en acier : deux vitres fixes, une double porte vitrée avec de longues poignées, '
     'une imposte. Les pavés de verre continuent devant le jardin de pierres et le vestiaire. Au-dessus, le mur aveugle '
     'du 1er devient des pavés de verre : la double hauteur de l\'escalier et le lierre prennent le jour.'),
    ('Les façades aveugles', 'À droite, sur les deux étages, une bande pleine passait devant les pavés de verre : vue de '
     'la rue, la façade était un mur. Elle est retirée, les pavés se voient entre les poteaux. À gauche, le 1er avait '
     'un mur plein doublé d\'une vitre : au-dessus du vide, c\'est maintenant une façade de pavés de verre sur deux '
     'niveaux, alignée sur celle du bas. Au coin nord-ouest, trois couches de murs n\'en font plus qu\'une.'),
    ('L\'escalier qui menait nulle part', 'Derrière le bar omakase, sept marches montaient vers un étage que le '
     'restaurant n\'a pas. Elles sont retirées : c\'est la réserve du bar, des étagères en acier avec les bouteilles de '
     'saké et de vin, quelques caisses. Le rideau qui la ferme est gardé.'),
    ('Un trou dans la façade droite du 1er', 'Entre deux panneaux de pavés de verre, un vide de 60 cm que la bande '
     'pleine cachait : refermé.'),
]
QUESTIONS = [
    'Le coin du 1er : la station de service (A) ou la table pour deux (B) ?',
    'Les façades en pavés de verre sur les deux étages, et la devanture de l\'entrée, te vont-elles ?',
    'Y a-t-il d\'autres endroits qui te gênent ? Je les reprends de la même façon.',
    'Une fois le modèle validé : je refais les plans des deux étages d\'après le modèle, et je remets la carte à jour.',
]


def img(src, w, cap=None):
    c = f'<div class="cap">{cap}</div>' if cap else ''
    return f'<figure><img src="{src}" width="{w}">{c}</figure>'


lieux = ''.join(
    f'''<div class="lbl" style="margin-top:18px">{t}</div>
  <div class="row">{''.join(img(Z + f, 470, c) for f, c in imgs)}
  <div class="col" style="width:500px"><div class="txt"><b>Ce qui n'allait pas.</b> {av}</div>
  <div class="txt"><b>Ce que je propose.</b> {ap}</div></div></div>''' for t, av, ap, imgs in LIEUX)

html = f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><link rel="stylesheet" href="style.css">
<style>.lead{{max-width:900px}}</style></head><body>
<div class="colw">
<section style="width:1520px">
  <div class="stitle">Restaurant · le modèle repensé : ce qui était étrange, et ce que je propose</div>
  <div class="snote">26/11/2026 · le plan du client n'est plus suivi là où il n'avait pas de sens pour un restaurant de deux étages</div>
  <div class="txt lead">J'ai repris les deux endroits que tu as entourés, puis passé tout le bâtiment en revue,
  de la rue et de l'intérieur. Voici chaque endroit repris, avant et après.</div>
  {lieux}
  <div class="row" style="margin-top:14px">{img(Z + 'plan-angle-1er.png', 720, 'A · la station de service, à l\'arrivée de l\'escalier')}{img(Z + 'table-plan-angle-1er.png', 720, 'B · une table pour deux dans le coin')}</div>
  <div class="row">{img(Z + 'plan-angle-se.png', 720, 'L\'angle sud-est, de la rue')}{img(Z + 'plan-vestiaire.png', 720, 'Le vestiaire, depuis le pied de l\'escalier')}</div>
</section>
<section style="width:1520px">
  <div class="stitle">Les autres endroits repris</div>
  <div class="row">{img(Z + 'plan-rue-sud.png', 720, 'Après : la rue, la devanture, les pavés de verre sur deux étages')}{img(Z18 + 'plan-angle-entree.png', 720, 'Avant : l\'entrée ouverte, le mur aveugle au-dessus')}</div>
  <div class="row">{img(Z + 'plan-rdc-entree.png', 720, 'La double porte, depuis l\'accueil')}{img(Z + 'plan-reserve.png', 720, 'La réserve du bar omakase, à la place de l\'escalier')}</div>
  <div class="row">{img(Z + 'plan-facade-est.png', 720, 'Après : la façade droite, les pavés de verre entre les poteaux')}{img(Z18 + 'plan-est.png', 720, 'Avant : la même façade, aveugle')}</div>
  <div class="row">{img(Z + 'plan-facade-ouest.png', 720, 'Après : la façade gauche, les pavés de verre sur deux niveaux')}{img(Z18 + 'plan-facade-ouest.png', 720, 'Avant : le mur plein du 1er')}</div>
  <div class="row">{img(Z + 'avant-escalier-haut.png', 490, 'Avant : l\'escalier vers nulle part, derrière le bar')}{img(Z + 'apres-escalier-haut.png', 490, 'Après : la réserve')}
  <div class="col" style="width:480px"><ul class="list">{''.join(f'<li><b>{t}.</b> {d}</li>' for t, d in AUTRES)}</ul></div></div>
</section>
</div>
<div class="colw">
<section style="width:1520px">
  <div class="stitle">Le bâtiment repensé</div>
  <div class="row">{img(Z + 'detail-3d.png', 1480, 'Les deux étages à pleine hauteur')}</div>
  <div class="row">{img(Z + 'fantome-3d.png', 720, 'Comme sur la carte, en fantôme')}{img(Z + 'fantome-dessus.png', 720, 'Vu du haut')}</div>
</section>
<section style="width:760px">
  <div class="stitle">Questions</div>
  <ol class="list">{''.join(f'<li>{q}</li>' for q in QUESTIONS)}</ol>
</section>
</div>
</body></html>'''
(PG / 'etape-15.html').write_text(html)
out = R / 'pages' / '15-refonte.png'
subprocess.run(['node', str(PG / 'export.mjs'), str(PG / 'etape-15.html'), str(out), '1'], check=True)
