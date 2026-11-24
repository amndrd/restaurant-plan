# Restaurant : le plan interactif

Un projet du studio, qui sera présenté sur son site. À partir des plans d'un restaurant, on modélise le lieu en 3D dans Blender, dans un style de carte de jeu en vue isométrique. Le but : un système de gestion où l'équipe voit la salle en direct. On y suit les tables libres et prises, depuis combien de temps les clients attendent, et les plats commandés à chaque table.

Les plans sont ceux du **LAIR Restaurant & Bar** (Gurugram, Inde, 2024), conçu par **RENESA Architecture Design Interiors Studio**, avec des photos d'Avesh Gaur, publié sur ArchDaily. Le détail est dans `recherche/11-lair-archdaily/source.md`. Le restaurant de la démo sera fictif : son nom, sa carte et son équipe seront inventés.

On travaille étage par étage, en commençant par **floor1**, le rez-de-chaussée avec l'entrée, l'accueil, la salle et le bar. On avance étape par étape : chaque étape est montrée en captures et validée avant la suivante.

## Où en est-on (24/11/2026)

**Étape 5 : la carte interactive.** En attente de tes choix.

- **La carte** (`carte/`) est une application web en three.js. Pour l'ouvrir : double-clic sur `carte/ouvrir-la-carte.command`. Elle reprend le modèle de Blender exporté en glTF, avec les mêmes vues, le même soleil et les traits redessinés en direct.
- **Ce qu'on y fait :**
  - déplacer, tourner, incliner et zoomer, à la souris, au trackpad ou au doigt ;
  - basculer entre la vue du haut et la vue 3D ;
  - ouvrir la fiche d'une table : son état, les personnes, l'attente et la commande ;
  - changer le style ;
  - choisir l'étage (le 1er étage arrive ensuite).
- **Le service est simulé** pour l'instant, avec des données provisoires.
- **Quatre prototypes pour l'état des tables :** A halo au sol, B plateau, C places occupées, D minuteur.
- **Cinq dessins de numéros :** cachés par défaut, à choisir dans les réglages.
- **Les rendus :** les captures et la vidéo de manipulation sont dans `rendus/6-carte/`.
- **La page :** `pages/5-carte-interactive.png`.

**Étape 4 : le mobilier.** Validée : les hauteurs sont justes. La numérotation est gardée dans les données, mais pas affichée.

- **Le mobilier** (`rendus/5-mobilier/`), placé d'après le plan :
  - 13 tables de service : 4 tables rondes dans les tambours, 2 dans la rangée, 3 dans la salle et 4 tables hautes le long de la façade droite ;
  - 3 mange-debout en bois, les 7 tabourets du bar et son repose-pieds ;
  - les chaises, les fauteuils et les tabourets, 3 jardinières avec un arbre, les suspensions et les lampes de table ;
  - la tablette de la façade droite et la console de l'alcôve.
- **Les numéros de la carte :** `rendus/5-mobilier/tables-numerotees.png`. La liste des tables, avec leurs places et leurs positions, est dans `modele/floor1-tables.json` : c'est ce que lira la couche en direct.
- **Les rendus :** les deux vues de la carte en fantôme et en fil de fer, et trois vues rapprochées cadrées comme les photos 10, 8 et 31.
- **Trois corrections de l'étape 3 :** le rideau de l'alcôve, refait en drapé ; l'assise des banquettes des tambours, ramenée à la profondeur du plan ; la tablette de la façade droite, qui manquait.
- **La page** `pages/4-mobilier.png`.

**Étape 3 : les éléments fixes, d'après les photos.** Validée. On garde les rideaux et la sculpture.

- **Le style retenu** à l'étape 2 : le fantôme par défaut. L'équipe pourra choisir une autre variante dans l'application, le fil de fer par exemple. L'orientation de la vue du haut est validée.
- **Les éléments fixes** (`rendus/4-elements-fixes/`) :
  - le bar et l'arrière-bar ;
  - les banquettes des quatre tambours ;
  - l'escalier détaillé, avec la sculpture en miroir ;
  - les façades en pavés de verre ;
  - le jardin de pierres ;
  - l'accueil et les rideaux.
- **Les rendus :** les deux vues de la carte en fantôme et en fil de fer, et quatre vues rapprochées en blanc, à pleine hauteur.
- **La page** `pages/3-elements-fixes.png` met chaque élément à côté de la photo d'après laquelle il est modélisé.

**Étape 2 : le style blanc, vu du haut et en 3D.** Validée : le fantôme.

- **Cinq variantes** (`rendus/3-styles-blancs/`), chacune dans les deux vues de la carte : blanc, blanc sur grille, fantôme, transparent, fil de fer.
- **Le passage animé** de la vue du haut à la vue 3D, sur la variante fantôme : `passage-dessus-3d-fantome.mp4`.
- **La page** `pages/2-styles-blancs.png` réunit les variantes, mon avis, la source et ce que les photos ont appris.

**Étape 1 : le plan lu, mesuré, et la coque.** Validée.

- **L'analyse** (`pages/1-plan-et-coque.png`) :
  - l'échelle du plan, déduite de cinq objets de taille connue : 120 px = 1 m ;
  - les dimensions et les hauteurs, ces dernières d'après la coupe 3d-1 ;
  - l'inventaire : 13 tables et le comptoir, environ 65 couverts ;
  - les questions.
- **La coque dans Blender** (`rendus/1-coque/`) : le plan posé au sol à l'échelle, avec par-dessus les murs, les poteaux, les façades vitrées, les quatre tambours des banquettes et l'escalier hélicoïdal. Quatre vues.
- **Quatre styles essayés sur la coque** (`rendus/2-styles-sur-la-coque/`) : trait, trait sombre, maquette, jeu.
- **La recherche** (`recherche/planche.png`) : 60 images en 10 styles, le concept vidéo, mon avis et les idées pour le direct.

## Le dossier

```
floor1.png … 3d-2.png, plan-design.mp4   tes fichiers de départ (les plans, la coupe, l'axonométrie, la vidéo)
analyse/        _controle-murs.png : les murs vectorisés posés sur le plan, pour vérifier
modele/         floor1-murs.json (les murs, poteaux et tambours lus sur le plan), floor1-tables.json (les tables de
                la carte en direct), floor1-coque.blend
rendus/         1-coque/, 2-styles-sur-la-coque/, 3-styles-blancs/ (les variantes blanches et la vidéo du passage),
                4-elements-fixes/ (les éléments fixes, en fantôme, en fil de fer et en vues rapprochées),
                5-mobilier/ (le mobilier, les numéros des tables), 6-carte/ (les captures et la vidéo de la carte)
pages/          la page de chaque étape, en PNG
recherche/      00-video-concept/, 01 … 10 (les images retenues), sources.json, planche.png, _tri/ (les planches de tri),
                11-lair-archdaily/ (les 37 photos et 5 dessins du vrai restaurant, source.md),
                12-carte-interactive/sources.md (les références de la carte)
outils/         les scripts (voir plus bas)
carte/          la carte interactive : index.html, js/, css/, modele/ (le modèle en glTF), donnees/, vendor/three (three.js,
                licence MIT), ouvrir-la-carte.command
```

## Les outils (`outils/`)

Il faut Blender 4.5, Node avec Playwright (celui de `~/Desktop/Portfolio/tools`), et l'environnement Python `outils/.venv`, qui contient numpy, OpenCV et Pillow. Pour le recréer : `python3.14 -m venv outils/.venv && outils/.venv/bin/pip install numpy opencv-python-headless pillow`.

- **Lire le plan :**
  - `grille.py` découpe le plan avec une grille de coordonnées, pour mesurer ;
  - `composantes.py` numérote les zones sombres du plan (murs, poteaux, extérieur) ;
  - `vectoriser.py` trace les murs retenus en polygones, et retrouve les cercles des poteaux et des tambours. Il écrit `modele/floor1-murs.json`.
- **Modéliser :** `blender/floor1.py` construit floor1 et fait les rendus. On le lance avec `blender -b -P outils/blender/floor1.py --` suivi des options :
  - `vue=dessus,iso,coupe,entree` choisit les vues ;
  - `coupe=1.2` donne la hauteur de coupe des murs ;
  - `style=trait|trait-sombre|maquette|jeu` applique un style ;
  - `samples=128` règle la qualité ;
  - `save=<fichier.blend>` enregistre la scène ;
  - `variante=blanc|blanc-grille|fantome|transparent|fil-de-fer` rend une variante blanche dans les deux vues ; avec `transition=1 images=36`, il rend les images du passage entre les deux vues ;
  - `elements=1` ajoute les éléments fixes de l'étape 3 (pavés de verre, escalier détaillé, bar, banquettes, jardin, accueil, rideaux) ; avec `variante=detail plans=bar,banquette,escalier,facade,rideau`, il rend les vues rapprochées ;
  - `mobilier=1` ajoute le mobilier de l'étape 4 et écrit `modele/floor1-tables.json` ; avec `variante=detail plans=salle,tabourets,tambour`, il rend les vues rapprochées ;
  - `export=carte/modele/floor1-fantome.glb` (avec `variante=fantome mobilier=1`) ou `floor1-entier.glb` (avec `variante=fil-de-fer mobilier=1`) exporte le modèle de la carte. Chaque objet garde son rôle et le numéro de sa table. Il faut ensuite recopier `modele/floor1-tables.json` dans `carte/donnees/`.
- **Numéroter les tables :** `numeros_tables.py` pose le numéro de chaque table sur la vue du haut en fantôme.
- **La carte :** `carte_captures.mjs` sert la carte, fait toutes les captures de `rendus/6-carte/`, puis la vidéo (`node outils/carte_captures.mjs video` pour la vidéo seule). Les réglages passent aussi par l'adresse de la carte : `?vue=3d&style=fil-de-fer&systeme=C&numeros=4&heure=20:40&vitesse=0&fiche=6`.

  Le `.blend` n'est jamais enregistré à la main : c'est le script qui le refait.
- **La recherche :**
  - `pinterest.py` liste les épingles d'une page publique ;
  - `planches_contact.py` fait les planches de tri ;
  - `recherche_choix.py` télécharge les images retenues et écrit `sources.json`.
- **Les pages :** `page_etape1.py` à `page_etape5.py` et `page_recherche.py` écrivent le HTML dans `outils/pages/` (Inter, style minimal) et l'exportent en PNG avec `outils/pages/export.mjs`.

## Ce qui n'est pas dans le dépôt

Le dépôt ne contient pas le contenu de tiers :
- les plans, la coupe, l'axonométrie et la vidéo. Les plans sont ceux de RENESA, publiés sur ArchDaily, et doivent être cités ;
- les photos d'ArchDaily (© Avesh Gaur), et les pages des étapes 2 à 4 qui en montrent ;
- les images de la recherche (Pinterest), dont `recherche/sources.json` garde les liens ;
- les rendus et pages qui montrent le dessin du plan.

Le détail est dans `.gitignore`.
