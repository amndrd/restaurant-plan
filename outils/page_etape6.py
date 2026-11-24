# The working page of step 6: the settings kept with their options, the space by the bar once the standing tables
# are gone (four layouts), and the new designs for the settings (R1-R3) and the legend (L1-L3).
# Writes outils/pages/etape-6.html, then pages/6-reglages-et-espace-du-bar.png with outils/pages/export.mjs.
# usage: outils/.venv/bin/python outils/page_etape6.py   (after the zone renders and node outils/carte_captures.mjs)
import subprocess
from pathlib import Path

R = Path(__file__).resolve().parents[1]
PG = R / 'outils' / 'pages'
Z = '../../rendus/7-espace-du-bar/'
U = '../../rendus/8-reglages-legende/'
C = '../../rendus/6-carte/'

ZONES = [
    ('Z1', 'Tables de deux', '8 couverts',
     'Quatre tables carrées de 0,68 m, deux chaises face à face. La plus souple pour le service : on les pousse '
     'l\'une contre l\'autre pour un groupe de quatre ou de six.'),
    ('Z2', 'Table d\'hôtes', '10 couverts',
     'Une seule table de 3,40 m sous une suspension linéaire, comme celles de la photo 10. Une table commune près du '
     'bar, pour les clients seuls et les petits groupes.'),
    ('Z3', 'Salon d\'attente', '8 places',
     'Deux tapis, chacun avec une table basse et quatre fauteuils comme ceux des tambours. On y attend sa table, ou on y '
     'prend un verre quand le bar est plein.'),
    ('Z4', 'Banquette jardinière', '8 couverts',
     'Une banquette adossée à un bac de plantes basses, qui sépare le passage du bar de la salle. Devant, quatre tables '
     'pour deux. Elle reprend le cuir et la courbe des banquettes des tambours.'),
]

REGLAGES = [
    ('R1', 'Barre d\'options',
     'Toujours visible en haut, au centre. L\'option choisie montre son nom, les deux autres leur icône (leur nom au '
     'survol). Un seul clic pour changer, rien à ouvrir.'),
    ('R2', 'Calques',
     'Le bouton du haut des outils ouvre un panneau, comme dans les applications de cartes. Chaque option a sa vignette, '
     'un vrai aperçu de la carte : on voit ce qu\'on choisit.'),
    ('R3', 'Barre de commande',
     'Une barre sombre en bas à droite, avec l\'horloge. Chaque menu s\'ouvre vers le haut, avec une ligne pour dire ce '
     'que fait l\'option.'),
]

LEGENDES = [
    ('L1', 'Compteurs',
     'Chaque état avec son nombre de tables. Au survol ou au clic, les tables de cet état sont entourées sur la carte '
     '(ici, en attente des plats). Les états vides s\'effacent.'),
    ('L2', 'Jauge',
     'La salle en une barre : chaque état prend la place de ses tables, avec le compte dedans. Les alertes sont à part, '
     'en rouge.'),
    ('L3', 'Frise du service',
     'La soirée de 18h30 à 23h30 : les clients dans chaque état, l\'heure actuelle et les réservations à venir '
     '(triangles). On voit le coup de feu arriver.'),
]

QUESTIONS = [
    'L\'espace du bar : laquelle des quatre propositions ? Je recommande Z4, la banquette jardinière. Elle sépare le '
    'passage du bar de la salle, ajoute 8 couverts et prolonge le langage des tambours. Z1 est l\'option la plus souple '
    'si tu préfères.',
    'Les réglages : R1, R2 ou R3 ? Je recommande R2, les calques. La carte reste dégagée, et les vignettes rendent le '
    'choix évident. R1 est plus rapide si l\'équipe change souvent de réglage.',
    'La légende : L1, L2 ou L3 ? Je recommande L1, les compteurs, pour le service : on compte et on repère les tables '
    'd\'un geste. L3, la frise, servirait plus tard à rejouer la soirée.',
    'Ensuite, le 1er étage avec le même système et le changement d\'étage. On y va dès que les trois choix sont faits ?',
]


def img(src, w, cap=None):
    c = f'<div class="cap">{cap}</div>' if cap else ''
    return f'<figure><img src="{src}" width="{w}">{c}</figure>'


html = f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><link rel="stylesheet" href="style.css">
<style>.lead{{max-width:820px}} td:first-child{{font-weight:600;white-space:nowrap}} td b{{font-weight:600}}</style></head><body>
<div class="colw">
<section style="width:1680px">
  <div class="stitle">Restaurant · floor1 · étape 6 : les réglages, et l'espace du bar</div>
  <div class="snote">24/11/2026 · les choix appliqués, puis trois sujets en prototypes</div>
  <div class="txt lead">Les réglages sont réduits à tes choix, avec leur option par défaut. Les autres options sont
  retirées de la carte. Les trois mange-debout sont retirés du plan. Il reste trois sujets à trancher : ce qu'on met à
  leur place, le dessin des réglages et celui de la légende.</div>
  <div class="row">
    {img(C + 'carte-defaut-3d.png', 1000, 'La carte avec les réglages par défaut, la barre d\'options R1, les compteurs L1 et la proposition Z4')}
    <div class="col" style="width:600px">
      <table><tr><th>Réglage</th><th>Par défaut</th><th>Au choix</th></tr>
      <tr><td>Style</td><td><b>Fantôme</b></td><td>Transparent, Fil de fer</td></tr>
      <tr><td>Tables</td><td><b>Places occupées</b> (C)</td><td>Plateau (B), Minuteur (D)</td></tr>
      <tr><td>Numéros</td><td><b>Étiquette</b></td><td>Zones, Aucun</td></tr></table>
      <div class="txt">Retirés : le style Blanc, le halo au sol (A), les numéros peints au sol, la plaque et le repère
      d'architecte.</div>
    </div>
  </div>
</section>
<section style="width:1680px">
  <div class="stitle">L'espace du bar : quatre propositions</div>
  <div class="txt lead">Sans les mange-debout, il reste un espace de 4,1 × 1,7 m une fois les passages gardés : 0,8 m
  derrière les tabourets du bar, 0,75 m devant le tambour 1 et 0,65 m jusqu'à la rangée. Chaque proposition est
  modélisée à l'échelle et ne touche rien. Ses tables sont branchées sur le service simulé, numérotées de 14 à 17.</div>
  <div class="row">{img(Z + 'plan-zone-vide.png', 520, 'L\'espace vide')}{img(Z + 'zone-vide-dessus.png', 520, 'Vu du haut')}{img(Z + 'zone-vide-3d.png', 520, 'Sur la carte')}</div>
  {''.join(f'<div class="row">{img(Z + f"plan-zone-{k}.png", 520)}{img(Z + f"zone-{k}-dessus.png", 520)}{img(Z + f"zone-{k}-3d.png", 520)}</div><div class="txt" style="max-width:1600px;margin-top:-8px"><b>{k} · {t}</b>, {n}. {d}</div>' for k, t, n, d in ZONES)}
</section>
</div>
<div class="colw">
<section style="width:1680px">
  <div class="stitle">Les réglages : trois dessins</div>
  {''.join(f'<div class="row">{img(U + f"{k}.png", 1000)}<div class="col" style="width:600px">{img(U + f"{k}-proche.png", 600)}<div class="lbl">{k} · {t}</div><div class="txt">{d}</div></div></div>' for k, t, d in REGLAGES)}
  <div class="row">{img(U + 'R3-style-proche.png', 600, 'R3, le menu du style ouvert')}</div>
</section>
</div>
<div class="colw">
<section style="width:1680px">
  <div class="stitle">La légende : trois dessins</div>
  {''.join(f'<div class="row">{img(U + f"{k}.png", 1000)}<div class="col" style="width:600px">{img(U + f"{k}-proche.png", 600)}<div class="lbl">{k} · {t}</div><div class="txt">{d}</div></div></div>' for k, t, d in LEGENDES)}
</section>
<section style="width:1680px">
  <div class="stitle">Questions</div>
  <ol class="list">{''.join(f'<li>{q}</li>' for q in QUESTIONS)}</ol>
</section>
</div>
</body></html>'''
(PG / 'etape-6.html').write_text(html)
out = R / 'pages' / '6-reglages-et-espace-du-bar.png'
subprocess.run(['node', str(PG / 'export.mjs'), str(PG / 'etape-6.html'), str(out), '1'], check=True)
