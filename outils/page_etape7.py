# The working page of step 7: the map as chosen (the banquette by the bar, the light command bar, the legend folded
# behind its button) and the dark theme, side by side with the light one.
# Writes outils/pages/etape-7.html, then pages/7-carte-finale.png with outils/pages/export.mjs.
# usage: outils/.venv/bin/python outils/page_etape7.py   (after node outils/carte_captures.mjs)
import subprocess
from pathlib import Path

R = Path(__file__).resolve().parents[1]
PG = R / 'outils' / 'pages'
C = '../../rendus/9-carte-finale/'
Z = '../../rendus/7-espace-du-bar/'

PAIRES = [
    ('dessus', 'La vue du haut'),
    ('3d', 'La vue 3D'),
    ('legende', 'La légende ouverte : les tables en attente des plats sont entourées'),
    ('fiche', 'La fiche d\'une table de la banquette'),
    ('menu', 'Un menu de la barre de commande'),
]

QUESTIONS = [
    'Le thème sombre change aussi la carte : les murs passent en anthracite et les traits en clair. Ça te va, ou tu '
    'préfères garder la carte blanche et ne foncer que les panneaux ?',
    'La légende est repliée à l\'ouverture de la carte. Faut-il qu\'elle reste ouverte si on l\'a ouverte la dernière '
    'fois, comme le thème ?',
    'On passe au 1er étage ? Je le modélise avec la même méthode (plan, coque, éléments fixes, mobilier), puis le bouton '
    '« 1er » s\'active dans la carte.',
]


def img(src, w, cap=None):
    c = f'<div class="cap">{cap}</div>' if cap else ''
    return f'<figure><img src="{src}" width="{w}">{c}</figure>'


html = f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><link rel="stylesheet" href="style.css">
<style>.lead{{max-width:900px}}</style></head><body>
<div class="colw">
<section style="width:1680px">
  <div class="stitle">Restaurant · floor1 · étape 7 : la carte telle que choisie, en clair et en sombre</div>
  <div class="snote">24/11/2026 · la banquette jardinière, la barre de commande en clair, la légende repliable, le thème sombre</div>
  <div class="txt lead">Tes trois choix sont appliqués. La banquette jardinière remplace les mange-debout, avec ses
  quatre tables (14 à 17). Les réglages sont dans la barre de commande, en bas à droite, en clair. La légende se replie
  derrière son bouton en bas à gauche : elle s'ouvre vers le haut, comme les menus. Le bouton en haut à droite passe
  l'interface en sombre, et la carte avec elle : les murs passent en anthracite et les traits en clair. Le choix est
  gardé d'une visite à l'autre. Les autres dessins sont retirés de la carte.</div>
  <div class="row">{img(Z + 'plan-zone-Z4.png', 820, 'La banquette jardinière, maintenant dans le modèle')}
  <div class="col" style="width:760px"><div class="txt">Une vidéo montre la carte en main, jusqu'au passage en sombre :
  <code>rendus/9-carte-finale/manipulation.mp4</code>.</div></div></div>
</section>
{''.join(f"""<section style="width:1680px">
  <div class="stitle">{t}</div>
  <div class="row">{img(C + f'clair-{k}.png', 785, 'Clair')}{img(C + f'sombre-{k}.png', 785, 'Sombre')}</div>
</section>""" for k, t in PAIRES[:2])}
</div>
<div class="colw">
{''.join(f"""<section style="width:1680px">
  <div class="stitle">{t}</div>
  <div class="row">{img(C + f'clair-{k}.png', 785, 'Clair')}{img(C + f'sombre-{k}.png', 785, 'Sombre')}</div>
</section>""" for k, t in PAIRES[2:])}
<section style="width:1680px">
  <div class="stitle">Questions</div>
  <ol class="list">{''.join(f'<li>{q}</li>' for q in QUESTIONS)}</ol>
</section>
</div>
</body></html>'''
(PG / 'etape-7.html').write_text(html)
out = R / 'pages' / '7-carte-finale.png'
subprocess.run(['node', str(PG / 'export.mjs'), str(PG / 'etape-7.html'), str(out), '1'], check=True)
