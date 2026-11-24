# The working page of step 5: the interactive map (carte/), its two views and its controls, the table card, the four
# prototypes for the state of the tables, the five numbering designs, the styles, and the ideas for the data.
# Writes outils/pages/etape-5.html, then pages/5-carte-interactive.png with outils/pages/export.mjs.
# usage: outils/.venv/bin/python outils/page_etape5.py   (after node outils/carte_captures.mjs)
import subprocess
from pathlib import Path

R = Path(__file__).resolve().parents[1]
PG = R / 'outils' / 'pages'
C = '../../rendus/6-carte/'

ETATS = [
    ('A', 'halo', 'A · Halo au sol',
     'Une tache de couleur sous la table et ses chaises. Elle se lit aussi bien d\'en haut qu\'en 3D, de loin comme de '
     'près, et laisse le modèle blanc.'),
    ('B', 'plateau', 'B · Plateau',
     'Seul le plateau prend la couleur. C\'est le plus discret : très lisible en 3D, plus petit vu du haut.'),
    ('C', 'places', 'C · Places occupées',
     'Chaque place occupée prend la couleur : on compte les clients d\'un coup d\'œil. Pour les tambours, les fauteuils '
     'puis la banquette.'),
    ('D', 'minuteur', 'D · Minuteur',
     'Un anneau au-dessus de la table se remplit avec le temps passé dans l\'état. On lit les minutes, l\'alerte pulse '
     'en rouge.'),
]

NUMEROS = [
    ('1', 'Peints au sol',
     'Le numéro est peint dans l\'allée, comme la signalétique d\'une salle de spectacle (Futura, gris).'),
    ('2', 'Plaque sur la table',
     'Un petit disque de laiton gravé, posé au bord de la table (Didot). C\'est aussi un objet pour le vrai lieu.'),
    ('3', 'Étiquette',
     'Une pastille noire au-dessus de la table, reliée par un fil fin : une légende de carte, toujours face à l\'écran.'),
    ('4', 'Repère d\'architecte',
     'Un cercle au trait et une courte attache vers la table : le langage des plans, dans le style de la carte.'),
    ('5', 'Zones',
     'Une lettre de zone et un numéro : T tambours, R rangée, S salle, F façade, D debout. Utile pour répartir '
     'le service.'),
]

GESTES = [
    ('Glisser', 'déplace la carte'),
    ('Clic droit, Maj + glisser, deux doigts', 'tourne autour de la salle et l\'incline'),
    ('Molette, pincer', 'zoome vers le pointeur'),
    ('Haut · 3D', 'bascule entre les deux vues, avec la transition animée'),
    ('⟲ ⟳ ◎', 'tourne de 45°, recentre'),
    ('Clic sur une table', 'ouvre sa fiche'),
    ('RDC · 1er', 'change d\'étage (le 1er arrive à l\'étape suivante)'),
    ('Horloge', 'met le service en pause, ou l\'accélère (×1, ×30, ×120)'),
    ('Réglages', 'le style, le système des états, les numéros'),
]

IDEES = [
    '<b>Les serveurs</b> : une couleur par serveur, sa zone sur la carte et sa charge (tables, couverts, alertes).',
    '<b>Placer un groupe</b> : on tape « 6 personnes », la carte éclaire les tables libres qui conviennent.',
    '<b>Les réservations</b> : la table se teinte 30 min avant, avec le nom et l\'heure au survol, et une frise de la '
    'soirée.',
    '<b>La cuisine</b> : les plats en cours, table par table, triés par temps d\'attente, sur un écran mural.',
    '<b>Assembler et séparer les tables</b> : la grande table en 6a, 6b, 6c, ou deux tables poussées l\'une contre '
    'l\'autre.',
    '<b>Rejouer le service</b> : une barre de temps pour revoir la soirée, les rotations et les temps morts.',
    '<b>Les seuils d\'alerte</b> réglables, et des notes client sur la fiche (allergie, anniversaire).',
    '<b>Le chiffre par table</b>, si la caisse est reliée.',
]

QUESTIONS = [
    'Quel système d\'états retenir ? Je propose A, le halo au sol, avec les minutes de D seulement pour les tables en '
    'alerte et pour la table choisie. C pourrait rester un mode « couverts » dans les réglages.',
    'Les numéros restent cachés par défaut, comme tu l\'as demandé. Si l\'un des cinq dessins te plaît pour plus tard, '
    'je pencherais pour le 4 sur la carte, et le 2 comme objet du vrai lieu.',
    'Parmi les idées pour les données, lesquelles veux-tu en premier ?',
    'Ensuite, le 1er étage (la mezzanine du plan floor2), avec le même système et le changement d\'étage. On y va ?',
]


def img(nom, w, cap=None):
    c = f'<div class="cap">{cap}</div>' if cap else ''
    return f'<figure><img src="{C}{nom}.png" width="{w}">{c}</figure>'


html = f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><link rel="stylesheet" href="style.css">
<style>.lead{{max-width:820px}} td:first-child{{white-space:nowrap;font-weight:600}}</style></head><body>
<div class="colw">
<section style="width:1680px">
  <div class="stitle">Restaurant · floor1 · étape 5 : la carte interactive</div>
  <div class="snote">24/11/2026 · une application web, le modèle de Blender en three.js, un service simulé</div>
  <div class="txt lead">Les hauteurs sont validées, et la numérotation reste dans les données sans s'afficher. Voici la
  carte qu'on manipule. C'est le modèle de Blender, exporté tel quel, avec les mêmes vues, le même soleil et les traits
  redessinés en direct. Pour l'ouvrir, double-clic sur <code>carte/ouvrir-la-carte.command</code>. En attendant les
  vraies données, un service simulé fait vivre la salle de 18h30 à la fermeture (données provisoires).</div>
  <div class="row">{img('carte-dessus', 800, 'La vue du haut, le système A')}{img('carte-3d', 800, 'La vue 3D')}</div>
</section>
<section style="width:1680px">
  <div class="stitle">La fiche d'une table, et ce qu'on peut faire</div>
  <div class="row">
    {img('carte-fiche', 1000, 'Un clic sur la grande table : son état, les personnes, l\'attente, la commande plat par plat')}
    <div class="col" style="width:580px">
      <table>{''.join(f'<tr><td>{g}</td><td>{d}</td></tr>' for g, d in GESTES)}</table>
      <div class="txt">Une vidéo montre la carte en main : <code>rendus/6-carte/manipulation.mp4</code>.</div>
    </div>
  </div>
</section>
<section style="width:1680px">
  <div class="stitle">Les styles, au choix dans les réglages</div>
  <div class="row">{img('style-fil-de-fer', 515, 'Fil de fer')}{img('style-transparent', 515, 'Transparent, système B')}
  {img('style-blanc', 515, 'Blanc, sans les hauts en fantôme')}</div>
</section>
</div>
<div class="colw">
<section style="width:1680px">
  <div class="stitle">L'état des tables : quatre prototypes</div>
  <div class="txt lead">Sept états suivent le service : libre, réservée, installée (à commander), en attente des plats,
  servie, addition, à débarrasser. Une table passe en alerte après 8 min sans commande, ou 22 min d'attente des plats :
  un anneau rouge pulse autour d'elle, dans tous les prototypes.</div>
  <div class="row wrap">{''.join(f'<div class="col" style="width:780px">{img(f"etats-{k}-{n}", 780, t)}<div class="txt">{d}</div></div>' for k, n, t, d in ETATS)}</div>
  <div class="row">{img('etats-A-proche', 510, 'A, de près')}{img('etats-C-proche', 510, 'C, de près')}{img('etats-D-proche', 510, 'D, de près')}</div>
</section>
</div>
<div class="colw">
<section style="width:1680px">
  <div class="stitle">Les numéros : cinq dessins, cachés par défaut</div>
  {''.join(f'<div class="row">{img(f"numeros-{k}-dessus", 620)}{img(f"numeros-{k}-proche", 620)}<div class="col" style="width:300px"><div class="lbl">{k} · {t}</div><div class="txt">{d}</div></div></div>' for k, t, d in NUMEROS)}
</section>
</div>
<div class="colw">
<section style="width:820px">
  <div class="stitle">Pour les données : ce que je propose ensuite</div>
  <ul class="list">{''.join(f'<li>{i}</li>' for i in IDEES)}</ul>
</section>
<section style="width:820px">
  <div class="stitle">Questions</div>
  <ol class="list">{''.join(f'<li>{q}</li>' for q in QUESTIONS)}</ol>
</section>
<section style="width:820px">
  <div class="stitle">Références</div>
  <div class="txt">Les états et les minuteurs des logiciels de salle (SevenRooms, Square, Toast, Oracle Simphony,
  Infor), le sélecteur d'étages de Mapbox, les cartes 3D de salles et de stades (3D Digital Venue, StadiView) et les
  numéros de table en laiton gravé. Les liens sont dans <code>recherche/12-carte-interactive/sources.md</code>.</div>
</section>
</div>
</body></html>'''
(PG / 'etape-5.html').write_text(html)
out = R / 'pages' / '5-carte-interactive.png'
subprocess.run(['node', str(PG / 'export.mjs'), str(PG / 'etape-5.html'), str(out), '1'], check=True)
