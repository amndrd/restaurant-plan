# The research board: the concept video, ten styles (6 images each), the existing tools and my opinion.
# Reads recherche/sources.json, writes outils/pages/recherche.html, then recherche/planche.png
# (the board stays local: it shows third-party images; the repository only keeps the links).
# usage: outils/.venv/bin/python outils/page_recherche.py
import html, json, subprocess
from pathlib import Path

R = Path(__file__).resolve().parents[1]
PG = R / 'outils' / 'pages'
SRC = json.loads((R / 'recherche' / 'sources.json').read_text())

THEMES = [
    ('01-trait-isometrique', 'Trait isométrique', 'le style de la vidéo',
     "Volumes blancs, traits fins, ombres douces. La couleur ne sert qu'à l'information. Pour une carte de gestion, c'est le plus lisible : rien ne concurrence l'état des tables. 01·03 montre comment empiler les étages."),
    ('02-pieces-3d-isometriques', 'Pièces 3D isométriques', 'Blender, rendu soigné',
     "La pièce coupée comme une boîte, avec ses matières et une lumière chaude. Le plus « jeu » et le plus séduisant pour la vitrine du studio. C'est plus chargé : les états devront se détacher (halo, pastille, couleur du sol sous la table)."),
    ('03-low-poly', 'Low poly', 'formes simplifiées, couleurs franches',
     "Léger à afficher en temps réel sur une tablette. Mais pour un restaurant de ce niveau, le rendu peut vite faire « jouet »."),
    ('04-pixel-art', 'Pixel art isométrique', 'Habbo, jeux indépendants',
     "Très identitaire et lisible en petit. Il s'éloigne pourtant du lieu réel (matières, ambiance). C'est plutôt une variante ludique qu'une base."),
    ('05-maquette-blanche', "Maquette d'architecte", 'carton blanc, bois, plexi',
     "Élégant et architectural, cohérent avec un restaurant haut de gamme. Une table occupée pourrait « s'allumer » sur la maquette."),
    ('06-ligne-claire', 'Ligne claire', 'Hergé, Floc\'h, Chaland',
     "Cerne noir régulier, aplats, pas d'ombres. Lisible, singulier et très belge. Il faut un rendu « toon » soigné : contours et aplats. 06·01 montre une salle de restaurant entière."),
    ('07-restaurants-isometriques', 'Restaurants isométriques', "l'existant, souvent du stock vectoriel",
     "Ce qu'on trouve déjà : des façades colorées et le cliché « fast-food ». Utile surtout pour voir ce qu'il faut éviter."),
    ('08-ecorches', 'Écorchés et étages éclatés', 'coupes, maisons de poupée',
     "Le principe de navigation : on soulève un étage pour voir celui du dessous, ou on écarte les niveaux. C'est ce que fait la vidéo avec son bouton d'étage."),
    ('09-cartes-3d-interfaces', 'Cartes 3D et interfaces', "plans d'orientation, jumeaux numériques",
     "09·01 : un plan d'orientation par niveaux, en couleurs par usage. 09·02 : un jumeau numérique sombre. Le mode sombre compte : en service, la salle est tamisée, et un écran blanc éblouit."),
    ('10-gestion-de-salle', 'Gestion de salle', 'les applications qui existent',
     "Les logiciels (Toast, SevenRooms, OpenTable, Zenchef…) montrent des plans plats : des rectangles et des pastilles. La place à prendre, c'est une vraie carte du lieu, lisible d'un coup d'œil."),
]

VIDEO = [('t01.5', 'la ville au trait, on zoome sur le bâtiment'), ('t11.0', 'un espace cliqué : sa fiche (nom, une phrase)'),
         ('t16.0', "le bouton d'étage coupe le bâtiment"), ('t21.0', 'un autre niveau, les zones en couleur'),
         ('t25.0', 'la vue tourne autour du bâtiment'), ('t30.5', 'deux couleurs seulement : public, VIP')]


def e(s):
    return html.escape(s, quote=True)


def section(tid, titre, sous, note):
    n = tid[:2]
    figs = ''.join(f'<figure><img class="th" src="../../recherche/{tid}/{k:02d}.jpg"><div class="cap"><b>{n}·{k:02d}</b></div></figure>'
                   for k in range(1, 7) if f'{tid}/{k:02d}.jpg' in SRC)
    return (f'<section class="theme"><div class="stitle">{n} {e(titre)}</div><div class="snote">{e(sous)}</div>'
            f'<div class="grid">{figs}</div><div class="txt">{e(note)}</div></section>')


video = ''.join(f'<figure><img src="../../recherche/00-video-concept/{f}.jpg" width="330"><div class="cap">{e(c)}</div></figure>'
                for f, c in VIDEO)
cols = [THEMES[:5], THEMES[5:]]
colhtml = ''.join('<div class="colw">' + ''.join(section(*t) for t in c) + '</div>' for c in cols)

AVIS = '''
<section style="width:760px">
  <div class="stitle">Mon avis</div>
  <div class="txt"><b>Le projet tient debout, et il est bien choisi pour le site du studio.</b> Les logiciels de salle se ressemblent tous : des plans plats. Une carte 3D fidèle au lieu, qui vit pendant le service, se remarque tout de suite. Elle montre en plus tout le savoir-faire : modéliser, designer une interface, travailler la donnée en direct.</div>
  <div class="lbl">Trois directions à prototyper sur notre coque</div>
  <ol class="list">
    <li><b>A · Trait</b> (01, 09) : le style de la vidéo, blanc au trait, avec sa version sombre pour le service. Le plus lisible.</li>
    <li><b>B · Maquette</b> (05) : carton blanc et bois, comme une maquette d'architecte posée sur la table. Élégant.</li>
    <li><b>C · Pièce de jeu</b> (02) : matières et lumière douces. Le plus spectaculaire pour le site.</li>
  </ol>
  <div class="txt">La <b>ligne claire</b> (06) est une quatrième piste, plus risquée et plus singulière. Le pixel art et le low poly me semblent moins justes pour ce lieu.</div>
  <div class="lbl">Ce que la carte peut montrer en direct</div>
  <ul class="list">
    <li>L'état de chaque table, par sa couleur : libre, réservée, installée, commande prise, plats envoyés, dessert, addition, à débarrasser.</li>
    <li>Le temps : depuis combien de temps la table est là, depuis quand elle attend. Elle pulse quand ça dépasse un seuil.</li>
    <li>Au clic, la fiche de la table, comme dans la vidéo : couverts, plats commandés et où ils en sont, allergies, serveur, note.</li>
    <li>Les rangs des serveurs, en couleur au sol. La liste d'attente à l'accueil, avec une suggestion de table selon le nombre.</li>
    <li>Le bouton d'étage pour passer de floor1 à floor2 et floor3 (la cuisine est au dernier niveau, elle pourrait recevoir les bons).</li>
    <li>À la fin du service, le replay : toute la soirée rejouée en accéléré sur la carte.</li>
  </ul>
  <div class="lbl">Comment je le construirais</div>
  <div class="txt">Le modèle se fait dans Blender, puis passe dans le navigateur (three.js, format glTF) pour la carte interactive. Le style « trait » se refait en temps réel avec des contours, et marche sur tablette. Blender garde les rendus et les vidéos de présentation pour le site. Pour la démo, un service simulé : un restaurant fictif, sa carte et son équipe.</div>
</section>'''

page = f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><link rel="stylesheet" href="style.css">
<style>
.theme{{width:760px}}
.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}}
.grid img.th{{width:100%;height:220px;object-fit:cover;background:#f4f4f4}}
.vid{{display:grid;grid-template-columns:repeat(2,330px);gap:14px}}
</style></head><body>
<div class="colw">
<section style="width:760px">
  <div class="stitle">Restaurant · la recherche : styles et références</div>
  <div class="snote">24/11/2026 · 60 images en 10 thèmes · les sources sont dans recherche/sources.json</div>
  <div class="txt">Ton concept vidéo, puis dix familles de styles pour la carte, de la plus sobre à la plus ludique, puis ce qui existe déjà pour gérer une salle. On les désigne par leur numéro, par exemple 02·03.</div>
</section>
<section style="width:760px">
  <div class="stitle">00 Le concept : la vidéo</div>
  <div class="snote">plan-design.mp4, 34 s, le site de l'adidas arena</div>
  <div class="vid">{video}</div>
  <div class="txt">À garder : le trait blanc et les ombres douces, le passage de la ville au bâtiment, le bouton d'étage, deux couleurs d'information seulement, la fiche au clic. Pour nous, les zones colorées deviennent les tables et leur état.</div>
</section>
{AVIS}
</div>
{colhtml}
</body></html>'''
(PG / 'recherche.html').write_text(page)
out = R / 'recherche' / 'planche.png'
subprocess.run(['node', str(PG / 'export.mjs'), str(PG / 'recherche.html'), str(out), '1'], check=True)
