# Restaurant : le plan interactif

Un projet du studio, qui sera présenté sur son site. À partir des plans d'un restaurant, on modélise le lieu en 3D dans Blender, dans un style de carte de jeu en vue isométrique. Le but : un système de gestion où l'équipe voit la salle en direct. On y suit les tables libres et prises, depuis combien de temps les clients attendent, et les plats commandés à chaque table.

On travaille étage par étage, en commençant par **floor1**, le rez-de-chaussée avec l'entrée, l'accueil, la salle et le bar. On avance étape par étape : chaque étape est montrée en captures et validée avant la suivante.

## Où en est-on (24/11/2026)

**Étape 1 : le plan lu, mesuré, et la coque.** En attente de ta validation.

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
modele/         floor1-murs.json (les murs, poteaux et tambours lus sur le plan), floor1-coque.blend
rendus/         1-coque/, 2-styles-sur-la-coque/
pages/          la page de chaque étape, en PNG
recherche/      00-video-concept/, 01 … 10 (les images retenues), sources.json, planche.png, _tri/ (les planches de tri)
outils/         les scripts (voir plus bas)
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
  - `save=<fichier.blend>` enregistre la scène.

  Le `.blend` n'est jamais enregistré à la main : c'est le script qui le refait.
- **La recherche :**
  - `pinterest.py` liste les épingles d'une page publique ;
  - `planches_contact.py` fait les planches de tri ;
  - `recherche_choix.py` télécharge les images retenues et écrit `sources.json`.
- **Les pages :** `page_etape1.py` et `page_recherche.py` écrivent le HTML dans `outils/pages/` (Inter, style minimal) et l'exportent en PNG avec `outils/pages/export.mjs`.

## Ce qui n'est pas dans le dépôt

Le dépôt ne contient pas le contenu de tiers :
- les plans, la coupe, l'axonométrie et la vidéo, dont la source est à confirmer et à citer ;
- les images de la recherche (Pinterest), dont `recherche/sources.json` garde les liens ;
- les rendus et pages qui montrent le dessin du plan.

Le détail est dans `.gitignore`.
