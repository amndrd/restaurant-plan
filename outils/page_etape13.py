# The working page of the ivy on the roof of the entry and of the joined parapets (1st floor): the ivy model supplied by
# the user analysed, the ivy grown again on the island, the parapet of the void joined to the stair's, and the map views
# of the floor as it stands (columns, ivy, furniture).
# Writes crops in rendus/17-etage-lierre-et-garde-corps/, outils/pages/etape-13.html, then pages/13-etage-lierre.png.
# usage: outils/.venv/bin/python outils/page_etape13.py   (after floor2.py ... out=rendus/17-etage-lierre-et-garde-corps)
import subprocess
from pathlib import Path
from PIL import Image

R = Path(__file__).resolve().parents[1]
PG = R / 'outils' / 'pages'
D = R / 'rendus' / '17-etage-lierre-et-garde-corps'
Z = '../../rendus/17-etage-lierre-et-garde-corps/'

# the map views cropped: the island and the stair in the top view, the island in the 3D view
haut = Image.open(D / 'fantome-dessus.png')
haut.crop((1330, 250, 1900, 900)).save(D / 'dessus-escalier-ile.png')
Image.open(D / 'fantome-3d.png').crop((760, 420, 1720, 1140)).save(D / 'carte-ile.png')

ANALYSE = [
    '<b>Ce que c\'est :</b> un panneau de lierre pour mur, en un seul maillage de 430 000 faces, sans texture.',
    '<b>Ses feuilles :</b> environ 40 000, mais ce sont des octogones plats de 7 faces. De loin, l\'ensemble se lit '
    'comme du lierre ; de près, ce sont des disques.',
    '<b>Son échelle :</b> 1/10. Remise à la vraie taille, une feuille mesure 6,6 cm en moyenne, entre 4 et 8,5 cm, '
    'comme un vrai lierre.',
    '<b>Sa forme :</b> un rectangle vertical, fait pour couvrir un mur. Posé tel quel sur un toit, il ne suivrait ni le '
    'bac ni les bords.',
]
GARDE = [
    'Entre le bord du vide et l\'ouverture de l\'escalier, il restait une bande de dalle de quelques centimètres : deux '
    'garde-corps couraient côte à côte (ta capture). La bande est supprimée : le vide rejoint l\'ouverture de '
    'l\'escalier.',
    'Il n\'y a plus qu\'une ligne : elle fait le tour du coin du vide, descend son bord droit, puis continue autour de '
    'l\'escalier jusqu\'à son arrivée. De l\'autre côté de l\'arrivée, une seconde ligne longe le jardin de pierres '
    'jusqu\'au mur : ce bord n\'était pas protégé.',
    'Le même dessin partout : un sabot d\'acier de 5 cm, 2 cm de verre, une main courante d\'acier de 4 cm à 1,06 m. '
    'Chaque garde-corps est tiré d\'un seul tenant le long de sa courbe : plus de joints entre les panneaux.',
]

QUESTIONS = [
    'Le lierre te plaît-il ? Je peux le rendre plus dense sur le toit, ou laisser tomber les retombées plus bas : elles '
    's\'arrêtent aujourd\'hui à 2,20 m au-dessus du sol du bas.',
    'Le garde-corps te va-t-il ainsi, d\'une seule ligne de l\'escalier au coin du vide ?',
    'Pour le crédit : d\'où vient le modèle « ivy-for-walls » (le lien et sa licence) ? Il reste hors du dépôt public, '
    'mais il faut le citer si on montre le travail.',
    'Ensuite : je refais les rendus des étapes du 1er étage avec les colonnes et le lierre, puis l\'export pour la carte '
    'et le bouton « 1er ». On y va ?',
]


def img(src, w, cap=None):
    c = f'<div class="cap">{cap}</div>' if cap else ''
    return f'<figure><img src="{src}" width="{w}">{c}</figure>'


html = f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><link rel="stylesheet" href="style.css">
<style>.lead{{max-width:900px}}</style></head><body>
<div class="colw">
<section style="width:1520px">
  <div class="stitle">Restaurant · 1er étage · le lierre sur le toit de l'entrée, et un seul garde-corps</div>
  <div class="snote">25/11/2026 · le bloc retiré, le lierre refait d'après ton modèle, les garde-corps accordés</div>
  <div class="txt lead">Le bloc est retiré. Sur le toit de l'accueil, un lierre pousse dans un bac bas et retombe dans
  le vide sur les trois côtés. Il est refait d'après le modèle « ivy-for-walls ». Le garde-corps du balcon et celui de
  l'escalier ne font plus qu'un.</div>
  <div class="row">{img(Z + 'plan-lierre.png', 900, 'Le lierre de près : les feuilles à cinq lobes, les tiges qui passent le rebord du bac')}
  <div class="col" style="width:560px">
    <div class="lbl">Le modèle fourni, analysé</div>
    <ul class="list">{''.join(f'<li>{a}</li>' for a in ANALYSE)}</ul>
    <div class="lbl">Ce que j'en ai fait</div>
    <div class="txt">J'ai gardé sa taille de feuilles, sa densité et le principe de tiges portant des feuilles
    alternées. J'ai remodélisé une vraie feuille de lierre : cinq lobes pointus, une base en cœur, une légère pliure le
    long de la nervure, en trois variantes. Puis j'ai fait pousser le lierre sur l'îlot :</div>
    <ul class="list">
      <li>des tiges rampent sur la terre d'un bac bas de 26 cm et couvrent le toit ;</li>
      <li>d'autres passent le rebord et retombent dans le vide, espacées irrégulièrement, de 20 cm à 1,40 m ;</li>
      <li>quelques retombées se ramifient ;</li>
      <li>les feuilles pendantes regardent vers l'extérieur.</li>
    </ul>
    <div class="txt">Rien ne touche les colonnes, les garde-corps ni les murs de l'accueil du bas.</div>
  </div></div>
  <div class="row">{img(Z + 'plan-ile.png', 580, 'Depuis la mezzanine, de l\'autre côté du vide')}{img(Z + 'plan-ile-bas.png', 400, 'Depuis la salle du bas')}{img(Z + 'carte-ile.png', 400, 'Sur la carte, en fantôme')}</div>
</section>
<section style="width:1520px">
  <div class="stitle">Le garde-corps du balcon, accordé à celui de l'escalier</div>
  <div class="row">{img(Z + 'plan-garde-corps.png', 820, 'La ligne continue, du bord du vide à l\'escalier')}{img(Z + 'dessus-escalier-ile.png', 560, 'Vu du haut : plus de bande entre les deux')}</div>
  <ul class="list" style="max-width:1400px">{''.join(f'<li>{g}</li>' for g in GARDE)}</ul>
</section>
</div>
<div class="colw">
<section>
  <div class="stitle">Le 1er étage tel qu'il est : les colonnes, le lierre, le mobilier</div>
  <div class="row">{img(Z + 'fantome-dessus.png', 800, 'Fantôme, vue du haut')}{img(Z + 'fantome-3d.png', 800, 'Fantôme, vue 3D')}</div>
  <div class="row">{img(Z + 'fil-de-fer-dessus.png', 800, 'Fil de fer, vue du haut')}{img(Z + 'fil-de-fer-3d.png', 800, 'Fil de fer, vue 3D')}</div>
</section>
<section style="width:760px">
  <div class="stitle">Questions</div>
  <ol class="list">{''.join(f'<li>{q}</li>' for q in QUESTIONS)}</ol>
</section>
</div>
</body></html>'''
(PG / 'etape-13.html').write_text(html)
out = R / 'pages' / '13-etage-lierre.png'
subprocess.run(['node', str(PG / 'export.mjs'), str(PG / 'etape-13.html'), str(out), '1'], check=True)
