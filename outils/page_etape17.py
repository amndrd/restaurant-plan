# The working page of the late 26/11 corrections: the 1st floor's column and the gaps in the walls, the corner by the
# stair on the ground floor (the wine room, the cloakroom), the stair's landing on the 1st floor, and on the map the
# legend, the "3D" button that follows the gesture, the 1st floor without a loading screen.
# Writes outils/pages/etape-17.html, then pages/17-cave-palier-carte.png.
# usage: outils/.venv/bin/python outils/page_etape17.py
#        (after the renders of rendus/22-sans-espace/ and rendus/23-cave-palier-carte/, and the map captures there)
import subprocess
from pathlib import Path

R = Path(__file__).resolve().parents[1]
PG = R / 'outils' / 'pages'
Z = '../../rendus/23-cave-palier-carte/'
Z22 = '../../rendus/22-sans-espace/'

QUESTIONS = [
    'La cave à vin à la place de la bande vide, et le vestiaire refait : ça te va ?',
    'Le palier de l\'escalier au 1er te va-t-il ?',
    'La légende, le bouton 3D et le passage au 1er : est-ce bien ce que tu voulais ?',
    'Ensuite : je refais les plans des deux étages d\'après le modèle, et les captures de la carte.',
    'Rappel : le lien et la licence du modèle « ivy-for-walls », pour le créditer.',
]


def img(src, w, cap=None):
    c = f'<div class="cap">{cap}</div>' if cap else ''
    return f'<figure><img src="{src}" width="{w}">{c}</figure>'


def txt(avant, apres):
    return (f'<div class="txt" style="max-width:1460px"><b>Ce qui n\'allait pas.</b> {avant}</div>'
            f'<div class="txt" style="max-width:1460px"><b>Ce que j\'ai fait.</b> {apres}</div>')


html = f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><link rel="stylesheet" href="style.css">
<style>.lead{{max-width:900px}}</style></head><body>
<div class="colw">
<section style="width:1520px">
  <div class="stitle">Restaurant · la cave à vin, le palier, la légende</div>
  <div class="snote">26/11/2026 · tes derniers points, dans l'ordre de tes messages</div>
  <div class="txt lead">La colonne du 1er et les espaces dans les murs, le coin à côté de l'escalier au rez-de-chaussée,
  la dernière marche au 1er, puis la carte : la légende, le bouton 3D, le 1er étage sans écran de chargement.</div>

  <div class="lbl" style="margin-top:20px">1 · La colonne du 1er et les pavés de verre</div>
  <div class="row">{img(Z22 + 'plan-colonne-1er.png', 720, 'La colonne de la façade droite, depuis le 1er')}{img(Z22 + 'plan-colonne-est.png', 720, 'La même, de la rue : le même diamètre aux deux étages')}</div>
  {txt('Au 1er, les deux colonnes de la façade droite étaient dessinées plus fines que celles du bas : les pavés de '
       'verre s\'arrêtaient sur le dessin du plan et laissaient un vide contre la colonne. Ailleurs, des fentes de 1 à 3 '
       'cm restaient là où deux murs du plan se rejoignaient, et l\'angle nord-est du bas était ouvert.',
       'Les colonnes du 1er ont la position et le diamètre de celles du rez-de-chaussée. Les pavés de verre vont jusqu\'à '
       'elles, et une joue en acier comble l\'arrondi. Les joints de mortier sont entre les pavés, toutes les fentes sont '
       'comblées aux deux étages et l\'angle nord-est est fermé. Une coupe du modèle à 1,50 m le vérifie : plus aucun '
       'passage entre l\'intérieur et l\'extérieur. Les demi-tambours ont avancé de 10 cm pour laisser la colonne entière.')}
</section>
<section style="width:1520px">
  <div class="lbl">2 · Le coin à côté de l'escalier, au rez-de-chaussée</div>
  <div class="row">{img(Z + 'avant-coin-escalier.png', 520, 'Avant (ta capture)')}{img(Z + 'carte-coin-escalier-fantome.png', 900, 'Après, sur la carte (style fantôme)')}</div>
  {txt('Une cloison fine de 3 m longeait l\'escalier ; derrière elle, une bande de 1,40 m contre les pavés de verre '
       'restait vide et sans usage. À côté, le vestiaire n\'était qu\'une tablette et des manteaux en forme de planches.',
       '<b>La bande devient une cave à vin vitrée.</b> La cloison est remplacée par un vitrage en acier, comme la '
       'devanture (poteaux fins, imposte à 2,40 m). Au nord, il y a une porte vitrée à longue poignée. À l\'intérieur, un '
       'casier en chêne va du sol à 2,77 m contre les pavés de verre : les bouteilles sont couchées, le culot vers '
       'l\'allée, et une rangée est debout à hauteur des yeux. Une échelle de bibliothèque roule sur un rail en acier, et '
       'au fond, une console de dégustation porte une carafe, deux verres et une bouteille. '
       '<b>Le vestiaire est refait :</b> un lambris de lattes de chêne, une tablette à chapeaux, une tringle en acier, '
       'des manteaux sur cintres (avec leurs manches), un banc en chêne le long des pavés de verre et un porte-parapluies '
       'dans l\'angle. Sa baie est encadrée de chêne, sous un linteau à 2,20 m.')}
  <div class="row">{img(Z + 'plan-cave-salle.png', 720, 'La cave, depuis la salle : le vitrage, la porte, l\'escalier')}{img(Z + 'plan-cave.png', 720, 'Dans la cave : le casier, l\'échelle, la console')}</div>
  <div class="row">{img(Z + 'plan-vestiaire.png', 720, 'Le vestiaire, depuis l\'entrée')}{img(Z + 'carte-coin-escalier.png', 720, 'Sur la carte, en style transparent')}</div>
</section>
</div>
<div class="colw">
<section style="width:1520px">
  <div class="lbl">3 · L'escalier du 1er</div>
  <div class="row">{img(Z + 'avant-escalier-1er.png', 520, 'Avant (ta capture)')}{img(Z + 'plan-palier.png', 900, 'Après : le palier, depuis l\'arrivée')}</div>
  {txt('La dernière marche s\'arrêtait 18 cm sous le plancher, au bord de la trémie : l\'escalier donnait dans le vide.',
       'Un palier, la 19e marche, est au niveau du plancher, dans l\'épaisseur de la dalle. Il va de la dernière '
       'contremarche jusqu\'au garde-corps du jardin. Ce garde-corps part maintenant du noyau et ferme le côté du palier '
       'sur le vide. On sort de l\'escalier vers la façade droite, entre les deux garde-corps vitrés.')}
  <div class="row">{img(Z + 'plan-palier-haut.png', 720, 'Le palier, depuis le coin du 1er')}{img(Z + 'carte-palier.png', 720, 'Sur la carte')}</div>
</section>
<section style="width:1520px">
  <div class="lbl">4 · La légende</div>
  <div class="row">{img(Z + 'modele-legende.png', 380, 'Ton modèle')}{img(Z + 'carte-legende-proche.png', 380, 'La légende, en sombre')}{img(Z + 'carte-legende-survol.png', 640, 'Survoler un état repère ses tables')}</div>
  <div class="txt" style="max-width:1460px">Le bouton « Légende » est remplacé par une carte sombre, toujours visible
  en bas à gauche : les six états en deux colonnes, comme sur ton modèle (Installée, En attente des plats, Servie,
  Addition, Réservation avec son triangle, Alerte). Survoler un état entoure ses tables sur la carte ; un clic les garde
  entourées.</div>
  <div class="lbl" style="margin-top:20px">5 · Le bouton 3D et le 1er étage</div>
  <div class="row">{img(Z + 'carte-geste-3d.png', 720, 'La vue du haut inclinée d\'un geste : « 3D » s\'allume seul')}
  <div class="col" style="width:680px"><ul class="list">
  <li><b>Le bouton 3D.</b> Dès qu'un geste incline la vue du haut, le bouton « 3D » se sélectionne, comme si tu avais
  cliqué dessus. Ramenée à plat, la vue repasse sur « Haut ». Un pincement pour zoomer ne penche plus la vue : il faut
  l'incliner de plus de 4° pour passer en 3D.</li>
  <li><b>Le 1er sans écran de chargement.</b> Le rez-de-chaussée s'affiche d'abord, puis le 1er se charge en
  arrière-plan, déjà habillé pour le style en cours. Le bouton « 1er » l'affiche aussitôt, même la première fois : 32 ms
  au test, sans écran noir. Si on clique avant la fin du chargement, le bouton pulse doucement le temps qu'il arrive.</li>
  </ul></div></div>
</section>
<section style="width:760px">
  <div class="stitle">Questions</div>
  <ol class="list">{''.join(f'<li>{q}</li>' for q in QUESTIONS)}</ol>
</section>
</div>
</body></html>'''
(PG / 'etape-17.html').write_text(html)
out = R / 'pages' / '17-cave-palier-carte.png'
subprocess.run(['node', str(PG / 'export.mjs'), str(PG / 'etape-17.html'), str(out), '1'], check=True)
