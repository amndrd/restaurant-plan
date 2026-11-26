# The working page of the whole building (25/11): why the two floors did not meet, what joins them now (the slab's
# band all round, the ground floor drawn under the mezzanine, the columns going on up, the lift shaft), the building
# seen from the street, and the map with its 1st floor standing on the ground floor.
# Writes the before / after crops in rendus/18-batiment-entier/, outils/pages/etape-14.html, then
# pages/14-batiment-entier.png.
# usage: outils/.venv/bin/python outils/page_etape14.py
#        (after floor2.py ... plans=facade-ouest,angle-entree,est out=rendus/18-batiment-entier, the step 3 renders in
#         rendus/15-etage-mobilier/, and node outils/carte_captures.mjs etage)
import subprocess
from pathlib import Path
from PIL import Image

R = Path(__file__).resolve().parents[1]
PG = R / 'outils' / 'pages'
D = R / 'rendus' / '18-batiment-entier'
Z = '../../rendus/18-batiment-entier/'
C = '../../rendus/19-carte-deux-etages/'

# the same corners of the map's 3D view, before (the ivy step's render) and after
for nom, src in (('avant', R / 'rendus' / '17-etage-lierre-et-garde-corps' / 'fantome-3d.png'),
                 ('apres', R / 'rendus' / '15-etage-mobilier' / 'fantome-3d.png')):
    im = Image.open(src)
    im.crop((180, 380, 900, 900)).save(D / f'{nom}-facade.png')
    im.crop((1000, 650, 1850, 1250)).save(D / f'{nom}-entree.png')

POURQUOI = [
    '<b>Deux modèles à part.</b> Chaque étage avait son propre script. Dans les vues du 1er, le rez-de-chaussée '
    'n\'était qu\'un fond pâle, sans traits, coupé sous la dalle : il se lisait comme un autre objet.',
    '<b>Une fente tout autour.</b> La dalle du 1er s\'arrêtait à la face intérieure de ses murs extérieurs. Sous ces '
    'murs, il restait 30 cm de vide entre le haut du rez-de-chaussée et le bas du 1er : c\'est la bande sombre que tu '
    'as entourée.',
    '<b>Une façade ouverte.</b> Sur le plan du 1er, la gaine d\'ascenseur et la bande extérieure de la façade droite '
    'sont dessinées en gris foncé, pas en noir. La vectorisation les avait manquées : la façade est du 1er restait '
    'ouverte sur 3 m.',
    '<b>Un toit manquant.</b> Le petit local du rez-de-chaussée, au-delà de la façade droite, n\'avait rien au-dessus.',
]
FAIT = [
    '<b>La dalle</b> passe sous les murs extérieurs des deux niveaux, jusqu\'aux faces du bâtiment. Une bande de 30 cm '
    'fait le tour, entre les murs du bas et ceux du haut, comme sur la coupe du lieu.',
    '<b>Le rez-de-chaussée</b> est le modèle entier, avec son mobilier, posé sous la dalle. Il a les mêmes matières et '
    'les mêmes traits que le 1er. Son escalier s\'arrête à 1 m sous le plancher du haut, là où celui du 1er prend la '
    'suite.',
    '<b>Les poteaux</b> du bas montent aux mêmes places. Celui du vide est un seul fût, du sol du bas au plafond du '
    'haut.',
    '<b>La gaine d\'ascenseur et la bande est</b> sont modélisées sur les mesures du plan, au-dessus des murs du bas : '
    'la façade droite se lit sur les deux niveaux.',
    '<b>Le local</b> du bas est couvert par la dalle.',
    '<b>Rien ne se croise.</b> Il ne reste que des contacts voulus : les pieds sur la dalle, les murs qui se '
    'rejoignent. L\'ouverture de l\'escalier est élargie de 2 cm pour laisser passer sa main courante.',
]
CARTE = [
    '<b>Le bouton « 1er »</b> est actif. Il montre le 1er étage posé sur le rez-de-chaussée : le bâtiment entier, le '
    '1er coupé à 1,20 m comme le bas. Le bouton « RDC » montre le rez-de-chaussée seul, comme avant.',
    '<b>Le service</b> tourne sur les deux étages, à la même heure. Le panneau, la légende et les fiches suivent '
    'l\'étage affiché : 6 tables et 2 comptoirs au 1er, le bar omakase et la tablette au bord du vide, chacun suivi '
    'tabouret par tabouret.',
    '<b>À travers le vide,</b> on voit les tables du bas, en blanc.',
    '<b>Le 1er se charge</b> à la première demande, pour que la carte s\'ouvre aussi vite qu\'avant. Dans la carte, le '
    'lierre est allégé (feuilles à 8 points) et ombré sans contour.',
]
QUESTIONS = [
    'Le raccord des deux étages te va-t-il, vu de la rue comme sur la carte ?',
    'Au 1er, faut-il aussi colorer les tables du bas qu\'on voit à travers le vide, ou les laisser blanches ?',
    'Rappel : le lien et la licence du modèle « ivy-for-walls », pour le créditer.',
    'Ensuite : je propose de donner son identité au restaurant fictif de la démo (nom, carte, équipe), à la place '
    'des données provisoires du service. On y va ?',
]


def img(src, w, cap=None):
    c = f'<div class="cap">{cap}</div>' if cap else ''
    return f'<figure><img src="{src}" width="{w}">{c}</figure>'


def liste(l):
    return '<ul class="list">' + ''.join(f'<li>{x}</li>' for x in l) + '</ul>'


html = f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><link rel="stylesheet" href="style.css">
<style>.lead{{max-width:900px}}</style></head><body>
<div class="colw">
<section style="width:1520px">
  <div class="stitle">Restaurant · le bâtiment entier : les deux étages raccordés</div>
  <div class="snote">25/11/2026 · la dalle sous les murs, le rez-de-chaussée sous le 1er, la carte à deux étages</div>
  <div class="txt lead">Le rez-de-chaussée et le 1er étage forment maintenant un seul bâtiment : la façade du bas
  monte jusqu'à la bande de la dalle, et le 1er pose dessus. Sur la carte, le bouton « 1er » montre l'étage sur le
  rez-de-chaussée.</div>
  <div class="row">{img(Z + 'avant-facade.png', 560, 'Avant : la fente sous les murs du 1er')}{img(Z + 'apres-facade.png', 560, 'Après : la bande de la dalle')}
  <div class="col" style="width:340px"><div class="lbl">Pourquoi ils ne se touchaient pas</div>{liste(POURQUOI)}</div></div>
  <div class="row">{img(Z + 'avant-entree.png', 560, 'Avant : l\'angle de l\'entrée')}{img(Z + 'apres-entree.png', 560, 'Après')}
  <div class="col" style="width:340px"><div class="lbl">Ce qui les raccorde</div>{liste(FAIT)}</div></div>
</section>
<section style="width:1520px">
  <div class="stitle">Le bâtiment entier, sans coupe</div>
  <div class="row">{img(Z + 'detail-3d.png', 1480, 'Les deux étages à pleine hauteur, depuis l\'angle de la carte')}</div>
  <div class="row">{img(Z + 'plan-facade-ouest.png', 470, 'La façade gauche : les pavés de verre du bas, la bande de la dalle, le mur du 1er')}{img(Z + 'plan-angle-entree.png', 470, 'L\'angle de l\'entrée, sous l\'îlot de lierre')}{img(Z + 'plan-est.png', 470, 'La façade droite : les poteaux et la bande est sur les deux niveaux')}</div>
</section>
</div>
<div class="colw">
<section style="width:1520px">
  <div class="stitle">La carte : le 1er étage sur le rez-de-chaussée</div>
  <div class="row">{img(C + 'etage-3d.png', 900, 'Le 1er, en 3D : le bâtiment entier')}
  <div class="col" style="width:560px">{liste(CARTE)}
  {img(C + 'etage-fiche-omakase-proche.png', 330, 'La fiche du bar omakase')}</div></div>
  <div class="row">{img(C + 'etage-dessus.png', 720, 'Le 1er, vu du haut')}{img(C + 'etage-fil-de-fer.png', 720, 'En fil de fer : le bas sous le haut')}</div>
  <div class="txt" style="max-width:1460px">Les rendus des étapes du 1er sont refaits avec le modèle d'aujourd'hui
  (colonnes, lierre, garde-corps, bâtiment raccordé) : <code>rendus/12-etage-coque/</code>,
  <code>13-etage-elements-fixes/</code> et <code>15-etage-mobilier/</code>.</div>
</section>
<section style="width:760px">
  <div class="stitle">Questions</div>
  <ol class="list">{''.join(f'<li>{q}</li>' for q in QUESTIONS)}</ol>
</section>
</div>
</body></html>'''
(PG / 'etape-14.html').write_text(html)
out = R / 'pages' / '14-batiment-entier.png'
subprocess.run(['node', str(PG / 'export.mjs'), str(PG / 'etape-14.html'), str(out), '1'], check=True)
