# Restaurant : le plan interactif

Un projet du studio, qui sera présenté sur son site. À partir des plans d'un restaurant, on modélise le lieu en 3D dans Blender, dans un style de carte de jeu en vue isométrique. Le but : un système de gestion où l'équipe voit la salle en direct. On y suit les tables libres et prises, depuis combien de temps les clients attendent, et les plats commandés à chaque table.

Les plans sont ceux du **LAIR Restaurant & Bar** (Gurugram, Inde, 2024), conçu par **RENESA Architecture Design Interiors Studio**, avec des photos d'Avesh Gaur, publié sur ArchDaily. Le détail est dans `recherche/11-lair-archdaily/source.md`. Le restaurant de la démo sera fictif : son nom, sa carte et son équipe seront inventés.

On travaille étage par étage, en commençant par **floor1**, le rez-de-chaussée avec l'entrée, l'accueil, la salle et le bar. On avance étape par étape : chaque étape est montrée en captures et validée avant la suivante.

## Où en est-on (25/11/2026)

**1er étage, étape 3 : le mobilier.** En attente de ta validation.

- **Fait comme l'étape 4 du rez-de-chaussée,** avec les mêmes pièces : `floor2.py -- variante=fantome|fil-de-fer mobilier=1`, puis `variante=detail plans=grande,demi,facade` pour les gros plans.
- **Le mobilier :**
  - les 6 tabourets du bar omakase ;
  - la grande table et ses 10 chaises ;
  - les 6 tabourets de la tablette au bord du vide ;
  - dans les deux demi-tambours, une table ronde et 2 fauteuils chacun ;
  - 3 tables hautes à tabourets devant une tablette en bois sous les pavés de verre, comme au rez-de-chaussée ;
  - les machines du laboratoire, une console, les suspensions et les lampes.
- **Les tables sont numérotées** après celles du bas : 18 à 23, puis 100 pour le bar omakase et 101 pour la tablette, suivis tabouret par tabouret. Il y a 37 places à l'étage. La liste est dans `modele/floor2-tables.json`, et `outils/numeros_tables.py etage1` fait l'image des numéros.
- **Les rendus** sont dans `rendus/15-etage-mobilier/`. La page, `pages/11-etage-mobilier.png`, reste hors dépôt (photos).

**1er étage : le vide au-dessus des tambours, quatre prototypes.** En attente de ton choix.

- **Le constat :** dans le vrai lieu, les tambours se lisent sur toute la double hauteur, et des câbles tendus portent de petites lampes (photo 33). Dans le modèle, rien n'était fait au-dessus de 3 m.
- **Les quatre prototypes** (`floor2.py -- ... vide=1..4`) :
  - V1, le vrai lieu : les câbles et les lampes ;
  - V2, trois colonnes : les tambours montent jusqu'au plafond, avec des fentes de lumière ;
  - V3, trois halos : des anneaux de lumière suspendus à hauteur des yeux de la mezzanine ;
  - V4, les trois colonnes et une lanterne : le bloc de l'entrée devient une lanterne en pavés de verre.
- **Les rendus** sont dans `rendus/14-etage-prototypes-vide/`. La page, `pages/10-etage-le-vide.png`, reste hors dépôt (photo 33).

**1er étage, étape 2 : les éléments fixes, d'après les photos.** Validée.

- **Faite comme l'étape 3 du rez-de-chaussée,** avec les mêmes fonctions, matériaux, styles et caméras : `floor2.py -- variante=fantome|fil-de-fer elements=1`, puis `variante=detail plans=omakase,banquette,rebord,bloc,escalier` pour les gros plans.
- **Les éléments :**
  - les façades en pavés de verre ;
  - le bar omakase : la grille de 24 × 3 casiers à bouteilles (photos 11 et 12), le plan des barmen à 0,90 m et le plateau client à 1,08 m ;
  - les banquettes des deux demi-tambours, comme celles du bas ;
  - la tablette au bord du vide, à 1,08 m, dont le corps plein sert de garde-corps ;
  - le comptoir du laboratoire, fermé côté vide par un mur ;
  - les deux rideaux ;
  - le haut de l'escalier hélicoïdal et sa sculpture en miroir, qui monte jusqu'au plafond.
- **Le volume au-dessus de l'entrée :** aucune photo ne le montre. Il est habillé comme le portail d'entrée côté rue (photo 37) : du métal noir à joints debout tous les 0,30 m, un creux d'ombre au pied et une couvertine.
- **Sous la mezzanine,** le rez-de-chaussée (`carte/modele/floor1-fantome.glb`) est affiché en gris clair, sans trait. Vu du haut, il n'apparaît qu'à travers les vides ; vu en 3D, c'est le bâtiment qui porte la mezzanine.
- **Aucun élément n'en traverse un autre.** Il ne reste que des faces posées les unes contre les autres.
- **Les rendus** sont dans `rendus/13-etage-elements-fixes/`. La page, `pages/9-etage-elements-fixes.png`, montre chaque gros plan à côté de sa photo ; elle reste hors du dépôt à cause des photos.

**1er étage, étape 1 : la coque.** Validée. La page est `pages/8-etage-coque.png`, hors dépôt car elle montre le plan. L'escalier droit a les 7 marches du plan.

- **`outils/blender/floor2.py`** construit la mezzanine dans le repère du rez-de-chaussée. Le z 0 est le dessus de sa dalle, 3,35 m au-dessus du rez-de-chaussée.
- **La coque comprend :**
  - les murs vectorisés depuis `floor2.png` (`modele/etage1-murs.json`), les poteaux et les façades vitrées avec leurs montants ;
  - la dalle, percée du vide sur la salle, du vide sur le jardin de pierres et de l'ouverture ronde de l'escalier ;
  - les garde-corps vitrés au bord des vides ;
  - les deux demi-tambours des banquettes, l'escalier droit qui monte vers le toit et le haut de l'escalier hélicoïdal ;
  - le volume plein au-dessus de l'entrée, noir sur le plan et blanc sur l'axonométrie de l'architecte.
- **Les rendus** sont dans `rendus/12-etage-coque/` : le calage sur le plan (hors dépôt, il montre le plan), l'axonométrie et la coque coupée à 1,20 m comme sur la carte.
- **Hypothèses :** 3,00 m sous plafond, des demi-tambours de 2,20 m, des retours du bar omakase pleine hauteur.

**Les plans redessinés, pour le site.**

- **Les deux plans du client**, le rez-de-chaussée et le 1er étage, sont redessinés en traits exacts dans `rendus/10-plans/`. Chacun existe en SVG vectoriel et en PNG 4K (3840 × 2160).
- **Ils sont orientés comme la vue du haut de la carte,** le bar à gauche et l'entrée à droite, avec le même cadrage pour les deux étages.
- **Le cartouche** donne le titre, la légende en français, l'échelle et le crédit à RENESA.
- **Le rez-de-chaussée** reprend la géométrie du modèle 3D, banquette jardinière comprise.
- **Le 1er étage** est relevé sur `floor2.png` : ses murs sont vectorisés (`modele/etage1-murs.json`) et son mobilier mesuré. Ces relevés serviront à le modéliser.

**Étape 7 : la carte telle que choisie.** Validée, avec cinq retouches :
- le bar suivi tabouret par tabouret ;
- le minuteur en alerte qui pulse sur place ;
- le survol de la légende en noir léger ;
- le sombre limité à l'interface ;
- puis l'interface en sombre seulement : le mode clair et son bouton sont retirés (24/11). La carte elle-même reste claire.

- **L'espace du bar :** la banquette jardinière (Z4) est maintenant dans le modèle, avec les tables 14 à 17. Les autres propositions sont retirées du script.
- **Les réglages** sont dans la barre de commande, en bas à droite.
- **La légende** se replie derrière son bouton, en bas à gauche, et s'ouvre vers le haut.
- **Les autres dessins** de réglages et de légende sont retirés de la carte.
- **Les rendus :** les captures et la vidéo sont dans `rendus/9-carte-finale/`. Les captures `sombre-*` montrent l'interface actuelle ; les `clair-*` restent comme trace de l'étape 7.
- **La page :** `pages/7-carte-finale.png`.

**Étape 6 : les réglages, et l'espace du bar.** Validée : Z4, R3 en clair, L1 repliable, avec un thème sombre en plus.

- **Les réglages sont réduits à tes choix,** avec leur option par défaut :
  - le style : fantôme, avec transparent et fil de fer au choix ;
  - les tables : places occupées (C), avec plateau (B) et minuteur (D) ;
  - les numéros : étiquette, avec zones et aucun.

  Les autres options sont retirées.
- **Les trois mange-debout sont retirés.** Quatre propositions occupent leur place (`rendus/7-espace-du-bar/`) :
  - Z1, des tables de deux ;
  - Z2, une table d'hôtes ;
  - Z3, un salon d'attente ;
  - Z4, une banquette jardinière.

  La carte montre celle qu'on choisit avec `?zone=Z1` à `Z4`.
- **Trois dessins pour les réglages** (`?ui=`) : R1, une barre d'options ; R2, des calques avec vignettes ; R3, une barre de commande.
- **Trois dessins pour la légende** (`?legende=`) : L1, des compteurs ; L2, une jauge ; L3, la frise du service. Les captures sont dans `rendus/8-reglages-legende/`.
- **La page :** `pages/6-reglages-et-espace-du-bar.png`.

**Étape 5 : la carte interactive.** Validée. Fantôme, places occupées et étiquette sont gardés par défaut.

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
                etage1-murs.json (les murs et poteaux du 1er étage, lus sur floor2.png)
rendus/         1-coque/, 2-styles-sur-la-coque/, 3-styles-blancs/ (les variantes blanches et la vidéo du passage),
                4-elements-fixes/ (les éléments fixes, en fantôme, en fil de fer et en vues rapprochées),
                5-mobilier/ (le mobilier, les numéros des tables), 6-carte/ (les captures et la vidéo de la carte),
                7-espace-du-bar/ (les propositions pour la place des mange-debout), 8-reglages-legende/,
                9-carte-finale/ (la carte telle que choisie, et la vidéo),
                10-plans/ (les plans redessinés du rez-de-chaussée et du 1er étage, SVG et PNG 4K)
                11-plans-d-origine/ (les copies 4K des plans du client, hors dépôt),
                12-etage-coque/ (la coque du 1er étage), 13-etage-elements-fixes/ (ses éléments fixes),
                14-etage-prototypes-vide/ (les prototypes pour le vide), 15-etage-mobilier/ (son mobilier)
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
- **Modéliser :** `blender/floor1.py` construit floor1 et fait les rendus ; `blender/floor2.py` construit la mezzanine : `-- vue=dessus,iso,coupe` pour la coque, puis `-- variante=fantome|fil-de-fer|detail elements=1` pour les éléments fixes, comme floor1. On le lance avec `blender -b -P outils/blender/floor1.py --` suivi des options :
  - `vue=dessus,iso,coupe,entree` choisit les vues ;
  - `coupe=1.2` donne la hauteur de coupe des murs ;
  - `style=trait|trait-sombre|maquette|jeu` applique un style ;
  - `samples=128` règle la qualité ;
  - `save=<fichier.blend>` enregistre la scène ;
  - `variante=blanc|blanc-grille|fantome|transparent|fil-de-fer` rend une variante blanche dans les deux vues ; avec `transition=1 images=36`, il rend les images du passage entre les deux vues ;
  - `elements=1` ajoute les éléments fixes de l'étape 3 (pavés de verre, escalier détaillé, bar, banquettes, jardin, accueil, rideaux) ; avec `variante=detail plans=bar,banquette,escalier,facade,rideau`, il rend les vues rapprochées ;
  - `mobilier=1` ajoute le mobilier de l'étape 4 et écrit `modele/floor1-tables.json` ; avec `variante=detail plans=salle,tabourets,tambour`, il rend les vues rapprochées ;
  - avec `variante=detail plans=zone`, il rend la vue rapprochée de la banquette jardinière, près du bar ;
  - `export=carte/modele/floor1-fantome.glb` (avec `variante=fantome mobilier=1`) ou `floor1-entier.glb` (avec `variante=fil-de-fer mobilier=1`) exporte le modèle de la carte. Chaque objet garde son rôle et le numéro de sa table. Il faut ensuite recopier `modele/floor1-tables.json` dans `carte/donnees/`.
- **Numéroter les tables :** `numeros_tables.py` pose le numéro de chaque table sur la vue du haut en fantôme.
- **Redessiner les plans :** `outils/plans/plans.py [rdc] [etage1]` écrit les SVG et les PNG 4K de `rendus/10-plans/`. Il s'appuie sur trois fichiers : `dessin.py` (le kit de dessin), `rdc.py` et `etage1.py` (un étage chacun). Les murs du 1er étage sont vectorisés par `outils/vectoriser_etage1.py`.
- **La carte :** `carte_captures.mjs` sert la carte, fait toutes les captures de `rendus/6-carte/`, puis la vidéo (`node outils/carte_captures.mjs video` pour la vidéo seule). Les réglages passent aussi par l'adresse de la carte : `?vue=3d&style=fil-de-fer&systeme=B&numeros=5&legende=1&ouvert=style&heure=20:40&vitesse=0&fiche=6`.

  Le `.blend` n'est jamais enregistré à la main : c'est le script qui le refait.
- **La recherche :**
  - `pinterest.py` liste les épingles d'une page publique ;
  - `planches_contact.py` fait les planches de tri ;
  - `recherche_choix.py` télécharge les images retenues et écrit `sources.json`.
- **Les pages :** `page_etape1.py` à `page_etape7.py` et `page_recherche.py` écrivent le HTML dans `outils/pages/` (Inter, style minimal) et l'exportent en PNG avec `outils/pages/export.mjs`.

## Ce qui n'est pas dans le dépôt

Le dépôt ne contient pas le contenu de tiers :
- les plans, la coupe, l'axonométrie et la vidéo. Les plans sont ceux de RENESA, publiés sur ArchDaily, et doivent être cités ;
- les photos d'ArchDaily (© Avesh Gaur), et les pages des étapes 2 à 4 qui en montrent ;
- les images de la recherche (Pinterest), dont `recherche/sources.json` garde les liens ;
- les rendus et pages qui montrent le dessin du plan.

Le détail est dans `.gitignore`.
