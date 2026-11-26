# Restaurant : le plan interactif

Un projet du studio, qui sera présenté sur son site. À partir des plans d'un restaurant, on modélise le lieu en 3D dans Blender, dans un style de carte de jeu en vue isométrique. Le but : un système de gestion où l'équipe voit la salle en direct. On y suit les tables libres et prises, depuis combien de temps les clients attendent, et les plats commandés à chaque table.

Les plans sont ceux du **LAIR Restaurant & Bar** (Gurugram, Inde, 2024), conçu par **RENESA Architecture Design Interiors Studio**, avec des photos d'Avesh Gaur, publié sur ArchDaily. Le détail est dans `recherche/11-lair-archdaily/source.md`. Le restaurant de la démo sera fictif : son nom, sa carte et son équipe seront inventés.

On travaille étage par étage, en commençant par **floor1**, le rez-de-chaussée avec l'entrée, l'accueil, la salle et le bar. On avance étape par étape : chaque étape est montrée en captures et validée avant la suivante.

## Où en est-on (26/11/2026)

**Les plans finaux des deux étages, tirés du modèle (26/11, nuit).** Validés tels quels. Ce sont de vrais plans d'architecte, pas des captures du modèle. Ils serviront de feuilles dans le film du site : les plans se posent au sol, puis la maquette en sort.
- **Comment ils sont faits :** `outils/plans/plan_final.py` lit le modèle coupé à 1,20 m (`modele/trace/rdc.json`, `etage1.json`, écrits par `floor1.py` / `floor2.py -- variante=detail mobilier=1 trace=…`). Il ne garde que ce qu'un architecte dessine :
  - les murs et les poteaux coupés en noir, les tambours et les colonnes en gris foncé, les murets en contour ;
  - les pavés de verre, les vitrages et leurs cadres en acier ;
  - le mobilier et les équipements vus de dessus, en trait fin, peints du plus bas au plus haut ;
  - pas de petits objets : bouteilles, verres, tasses, casseroles, saladiers, ustensiles, cartons, stock, lampes. Ils sont écartés par leur nom, leur matière, ou parce qu'ils sont petits, ronds, posés sur un plan de travail ;
  - en tirets, ce qui est au-dessus du plan de coupe : la hotte, la retombée du bar, et le bord de la mezzanine sur le plan du rez-de-chaussée ;
  - les portes ouvertes à 90° avec leur débattement (double pour la porte de la cuisine), et l'escalier avec sa ligne de coupe et sa ligne de foulée (19 × 17,6 cm) ;
  - le vide du 1er avec sa croix, le jardin suspendu en trame végétale, les carreaux de la cuisine, le jardin sec ratissé ;
  - la trame des poteaux (1-2, A-B), les cotes, chaque pièce avec sa surface calculée sur le modèle, les niveaux (±0,00 et +3,35), un cartouche (légende, surfaces, échelle graphique, planche A-101 / A-102).
- **Le format :** A2 paysage au 1:50, tourné comme la vue du haut de la carte, avec le même cadrage pour les deux feuilles. Chaque plan est livré en SVG, en PNG 300 dpi (7016 × 4961) et en PDF dans `rendus/26-plans-finaux/` (`outils/.venv/bin/python outils/plans/plan_final.py [rdc] [etage1]`, il faut shapely).
- **La carte** a maintenant le style Transparent par défaut, en tête du menu des styles.

**Au 1er, la gaine d'ascenseur devient une réserve (26/11, nuit).** La gaine (`GAINE`, et les bouts de murs 734 et 770) est retirée de `floor2.py`. À sa place, entre le mur des toilettes et la façade, il y a une réserve de 1,0 × 3,0 m (`RESERVE`, `reserve_est`). Elle est fermée par une cloison avec une porte en chêne qui ouvre sur le passage des toilettes, derrière le rideau. Dedans :
- une étagère de 2 m le long de la façade, avec des cartons et des bouteilles ;
- une étagère plus basse contre le mur des toilettes, avec des serviettes et des rouleaux ;
- des caisses de vin au fond et un escabeau.

La carte du 1er est réexportée. **À partir de maintenant, une fois une modification modélisée, on ne fait plus de rendus : seule la carte 3D est mise à jour.**

**La cuisine ouverte, telle que choisie (26/11, nuit).** En attente de ta validation.

- **Le prototype A est retenu** : la cuisine ouverte sur le bar par-dessus un muret, la retombée avec les verres et les bouteilles suspendus, le comptoir en lattes de chêne. B et C sortent du script (l'option `cuisine=` n'existe plus) ; leurs rendus restent dans `rendus/24-cuisine-et-bar/`.
- **Le « couloir ouvert »** était la gaine sous celle du 1er (murs 16 et 36) : une boîte de 90 cm, ouverte au sud. Elle est retirée (`refonte.RDC_SANS`), et le nu intérieur de la façade droite est redressé d'un seul tenant (x 1447).
- **La cuisine va jusqu'à la façade** (`refonte.KITCHEN`) : après la plonge, une table propre, une étagère de vaisselle (assiettes, casiers à verres), le lave-mains près des portes, une étagère à assiettes au-dessus.
- **Les portes** sont replacées et élargies à 1,57 m (`refonte.KITCHEN_PORTE`) : deux battants de chêne à double action, avec chacun un hublot et une plaque de poussée sur les deux faces, et des plinthes inox.
- **Le poste de service** devant les portes (`refonte.SERVICE`, `service_rdc`) : un meuble en chêne avec tiroirs à couverts, portes et plateau de pierre, la caisse, des carafes et des verres ; un lambris de tasseaux de chêne et une étagère.
- **Vérifié :** il ne reste que des assemblages voulus.
- **Les rendus** sont dans `rendus/25-cuisine-ouverte/`, avec tes captures (`avant-couloir`, `avant-portes`) et la carte (`node outils/carte_captures.mjs cuisine`). La page est `pages/19-cuisine-ouverte.png`.
- **La carte est réexportée** (les deux étages et le rez-de-chaussée sous sa dalle), et `floor1-tables.json` est recopié dans `carte/donnees/`.
- **Au 1er,** la boîte de l'ancienne « gaine d'ascenseur » est devenue une réserve (voir plus haut).

**La cuisine et le bar du rez-de-chaussée (26/11, nuit).** Trois prototypes ; le A est choisi (voir ci-dessus).

- **Le fond du rez-de-chaussée est redessiné** (`refonte.py`, `floor1.py`). Les cloisons des deux toilettes (mur 14), le mur de la réserve le long de la façade (13), les bouts du local électrique (15, 35) disparaissent. À leur place :
  - **la cuisine**, juste derrière le bar (`refonte.KITCHEN`, `cuisine_rdc`) : la ligne de cuisson sous sa hotte (friteuse, grill au charbon, fourneau sur four, plancha, salamandre), deux armoires réfrigérées et un congélateur, une étagère de réserve sèche, le comptoir de préparation avec son évier, la saladette, la passe à la tablette chauffante, la plonge dans l'angle nord-est (table de débarrassage et douchette, lave-vaisselle à capot, table propre), un lave-mains près de la porte, un sol en carreaux de 30 cm et un caniveau ;
  - **la passe** au bout du bar, côté service, et **la porte de la cuisine** à double battant sur le couloir à droite du bar (`portes_rdc`) ;
  - **un WC accessible** au bout d'un passage le long des pavés de verre (`refonte.WC`, `wc_rdc`) ;
  - **le comptoir raccourci de 1,40 m** à l'ouest (`COMPTOIR`) : le passage fait 1,05 m contre la colonne 41, les 7 tabourets ne bougent pas ;
  - **le bar rhabillé** (`comptoir`, `arriere_bar`) : éviers, bac à glace, rail à bouteilles, lave-verres, colonne à bière, vitrines réfrigérées, machine à café, quatre suspensions ;
  - **la gaine** sous celle du 1er, fermée par deux portes sur le couloir.
- **Les trois prototypes** (`cuisine=A|B|C`, B par défaut en attendant) ne changent que la façade de la cuisine sur le bar (`cuisine_cloison`), le haut du meuble arrière et le front du comptoir : A ouverte (muret, retombée, verres et bouteilles suspendus, lattes de chêne), B le mur de bouteilles éclairé (pavés de verre au comptoir), C vitrée (verrière en acier, étagères en verre, ailettes d'acier).
- **Vérifié :** plus aucune pièce ne traverse une autre de plus de 1 mm, sauf les assemblages voulus (pieds soudés aux étagères, brochettes dans la viande). Au passage, le mur 364 qui entrait de 4 cm dans les pavés de verre de la façade droite est raccourci.
- **Les rendus** sont dans `rendus/24-cuisine-et-bar/` (`floor1.py -- variante=detail mobilier=1 cuisine=B plans=cuisine-salle,cuisine-comptoir,cuisine-passe,cuisine-ligne,cuisine-froid,cuisine-plonge,cuisine-passage,cuisine-wc prefixe=B-`, puis `variante=fantome ... plans=cuisine-vol,cuisine-dessus`), avec l'état d'avant (`avant-*`). La page est `pages/18-cuisine-et-bar.png`.
- **La carte** n'est pas encore réexportée : elle le sera avec le prototype choisi. Sa carte « Restaurant » en haut à gauche est retirée ; le panneau des chiffres prend sa place.
- **Le plan lu dans le modèle** (pour le plan final) : `floor1.py` et `floor2.py` acceptent `trace=modele/trace/<etage>.json`. `outils/blender/plan_modele.py` coupe le modèle à 1,20 m, pièce par pièce, et projette ce qui est dessous.

**La cave à vin, le palier, la légende (26/11, fin de soirée).** Validés.

- **Plus aucun espace dans les murs :** au 1er, les deux colonnes de la façade droite ont la position et le diamètre de celles du bas (`POTEAUX` dans `floor2.py`). Les pavés de verre s'arrêtent sur elles, une joue comble l'arrondi (`face_colonne`, `joue`, dans les deux scripts). Il y a des joints de mortier entre les pavés (`blocs(..., bj=)`), les fentes entre murs sont comblées (`RDC_JOINTS` dans `refonte.py`, `ETAGE_JOINTS` dans `floor2.py`) et l'angle nord-est du bas est fermé. Les demi-tambours ont avancé de 10 cm (`DEMI_CX`). Une coupe à 1,50 m vérifie qu'il ne reste aucun passage entre l'intérieur et l'extérieur.
- **Le coin de l'escalier au RDC** (`floor1.py`, `refonte.py`) : la cloison fine (murs 408, 421) et la bande vide derrière deviennent une cave à vin vitrée (`CAVE`, `cave_vitrage`, `cave`). Elle a un vitrage en acier côté escalier, une porte vitrée au nord, un casier en chêne avec ses bouteilles, une échelle sur rail et une console de dégustation. Le vestiaire est refait (`vestiaire`, `manteau`, `vestiaire_baie`) : lambris, tablette, tringle, manteaux sur cintres, banc, porte-parapluies, baie encadrée de chêne.
- **L'escalier du 1er** (`floor2.py`, `escalier_detail`) : un palier au niveau du plancher, la 19e marche (`escalier-palier`, `A_PALIER`). Le garde-corps du jardin part du noyau et ferme son côté sur le vide.
- **La carte :** la légende est une carte sombre, toujours visible en bas à gauche, avec les six états en deux colonnes (`legende.js`). Le bouton « 3D » se sélectionne dès qu'un geste incline la vue du haut, et « Haut » revient quand on la ramène à plat (`camera.js`, `orbiter`). Le 1er se charge en arrière-plan et s'affiche sans écran de chargement (`main.js`, `scene.js`, `prechauffer`).
- **Les rendus** sont dans `rendus/22-sans-espace/` et `rendus/23-cave-palier-carte/` (avec tes captures `avant-coin-escalier`, `avant-escalier-1er` et ton modèle de légende). La page est `pages/17-cave-palier-carte.png`.

**Les endroits repris, un par un (26/11, soir).** En attente de ta validation. Pour le coin du 1er, tu as choisi la station de service (A, `angle=station`, par défaut).

- **La tablette du balcon :** le garde-corps en verre court tout le long du vide ; la tablette en chêne en est le chapeau (1,02 - 1,08 m), sur des pieds fins en acier avec un repose-pieds ; la main courante part de son bout (`tablette_vide`, `TABLETTE_FIN` dans `floor2.py`).
- **Les lumières au-dessus du vide :** les suspensions des tables du bas sous le vide descendent de longs câbles depuis le plafond du 1er (`dessous()`), coupés comme les murs sur la carte.
- **Le bar omakase et sa cuisine :** huit petits murs du plan retirés, et les doublures du mur du fond ; le bar en hinoki et lattes de chêne, repose-pieds, vitrines à neta, bouteilles dans les casiers, trois suspensions ; la cuisine au bout du bar côté façade (`cuisine()`, `CUISINE_CLOISON`), la réserve derrière le fond du bar, la porte des toilettes (`wc()`, `MURS_WC`). L'escalier vers nulle part était déjà retiré : la carte recharge maintenant toujours ses modèles (en-tête `Cache-Control: no-cache`).
- **Le comptoir du labo :** chêne à lattes, plateau de pierre, cloche, bocaux, batteur ; un plan de travail avec évier et étagères le long du mur (`labo`, `labo_machines`).
- **Le jardin sec sous l'escalier** (`floor1.py`, `jardin`) : gravier ratissé en lignes et en cercles (`gravier-ratisse`), pierres polies (`rocher_lisse`, `PIERRES`), deux projecteurs.
- **L'accueil** (`floor1.py`, `accueil`, `accueil_mobilier`) : bureau en arc à lattes de chêne et plateau de pierre, panneau de tasseaux avec niche et plaque, banc, tapis, tabouret, suspension, olivier.
- **Les rendus** sont dans `rendus/21-reprises/` (avec tes captures `avant-1` à `avant-6`), la page est `pages/16-reprises.png`. Les modèles de la carte sont réexportés.

**Le modèle repensé : prototypes.** En attente de ta validation. Le plan du client n'est plus suivi là où il n'avait pas de sens pour un restaurant de deux étages ; les plans des deux étages seront refaits d'après le modèle une fois celui-ci validé.

- **Les changements** sont décrits dans `outils/blender/refonte.py` (les murs du rez-de-chaussée, partagés par les deux scripts), puis dans `floor1.py` et `floor2.py` :
  - **l'angle sud-est :** au 1er, le plancher va jusqu'aux deux façades, le mur isolé, la console et la poche au-dessus du bas disparaissent, le garde-corps du jardin de pierres va jusqu'à la façade ; dans le coin, une station de service (`angle=station`, par défaut) ou une table pour deux (`angle=table`). Au rez-de-chaussée, la boîte vide collée à la façade droite (mur 437) est retirée : c'est le vestiaire de l'entrée, avec une ouverture dans le mur 440. Un pilier d'angle ferme le bâtiment sur les deux étages ;
  - **l'entrée :** une devanture en acier (deux vitres fixes, une double porte vitrée, une imposte), les pavés de verre devant le jardin de pierres et le vestiaire ; au 1er, le mur aveugle au-dessus devient des pavés de verre ;
  - **les façades :** la bande pleine devant les pavés de verre de droite est retirée sur les deux étages (murs 55 et 288 du bas, 860 et la bande est du haut) ; à gauche, au-dessus du vide, le mur plein du 1er doublé d'une vitre devient une façade de pavés de verre alignée sur celle du bas ; au coin nord-ouest, une seule couche ; un trou de 60 cm dans la façade droite du 1er est refermé ;
  - **l'escalier vers nulle part,** derrière le bar omakase, devient la réserve du bar (étagères, bouteilles, caisses).
- **Les vérifications :** il ne reste que des contacts voulus (cadres bout à bout, objets posés).
- **Les rendus** sont dans `rendus/20-refonte/` (`floor2.py -- variante=detail mobilier=1 plans=rue-sud,angle-se,angle-1er,rdc-entree,vestiaire,reserve,facade-est,facade-ouest out=rendus/20-refonte`, `angle=table prefixe=table-` pour la variante B), la page est `pages/15-refonte.png`.
- **La carte** est réexportée avec le modèle repensé (les deux étages, la station de service dans le coin) ; ses captures seront refaites après ta validation.

**Le bâtiment entier : les deux étages raccordés, et la carte à deux étages.** En attente de ta validation.

- **Pourquoi ils ne se touchaient pas :**
  - chaque étage avait son propre script ; dans les vues du 1er, le rez-de-chaussée n'était qu'un fond pâle, sans traits, coupé sous la dalle ;
  - la dalle du 1er s'arrêtait à la face intérieure de ses murs extérieurs : sous ces murs, une fente de 30 cm restait vide tout autour ;
  - la gaine d'ascenseur et la bande extérieure de la façade droite sont en gris foncé sur `floor2.png`, pas en noir : la vectorisation les avait manquées, la façade est restait ouverte ;
  - le petit local du bas, au-delà de la façade droite, n'avait pas de toit.
- **Ce qui les raccorde** (`floor2.py`) :
  - la dalle passe sous les murs extérieurs des deux niveaux (`floor1-murs.json` et `etage1-murs.json`), jusqu'aux faces du bâtiment : une bande de 30 cm fait le tour, comme sur la coupe du lieu ;
  - le rez-de-chaussée est le modèle entier de la carte (`carte/modele/floor1-entier.glb`), posé sous la dalle, dans les mêmes matières et avec les mêmes traits ; son escalier s'arrête à 1 m sous le plancher du haut, où celui du 1er prend la suite ;
  - les poteaux du bas montent aux mêmes places, celui du vide d'un seul fût ;
  - la gaine d'ascenseur (`GAINE`) et la bande est (`BANDE_EST`) sont mesurées sur le plan ; le local du bas est couvert ;
  - l'ouverture de l'escalier est élargie de 2 cm pour sa main courante. Il ne reste que des contacts voulus.
- **Les vues de la rue** sont dans `rendus/18-batiment-entier/` (`variante=detail mobilier=1 plans=facade-ouest,angle-entree,est`).
- **La carte :**
  - le bouton « 1er » montre l'étage posé sur le rez-de-chaussée ; « RDC » montre le rez-de-chaussée seul, comme avant ;
  - chaque étage a son service simulé, sur la même horloge ; le panneau, la légende et les fiches suivent l'étage affiché ; au 1er, le bar omakase (100) et la tablette (101) sont suivis tabouret par tabouret ;
  - le 1er se charge à la première demande ; dans la carte, le lierre est allégé et ombré sans contour ;
  - les modèles : `floor2.py -- variante=fantome mobilier=1 export=carte/modele/floor2-fantome.glb dessous=carte/modele/floor1-sous-dalle.glb`, puis `variante=fil-de-fer mobilier=1 export=carte/modele/floor2-entier.glb` ; recopier `modele/floor2-tables.json` dans `carte/donnees/` ;
  - l'adresse accepte `?etage=1` ; les captures sont dans `rendus/19-carte-deux-etages/` (`node outils/carte_captures.mjs etage`).
- **Les rendus des étapes du 1er** sont refaits avec le modèle d'aujourd'hui : `rendus/12-etage-coque/`, `13-etage-elements-fixes/` et `15-etage-mobilier/`.
- **La page** est `pages/14-batiment-entier.png`.

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

**1er étage : le lierre sur le toit de l'entrée, et un seul garde-corps.** En attente de ta validation.

- **Le lierre** vient de ton modèle `ivy-for-walls.zip` (« Ivy for walls », par arca_done sur Sketchfab, licence CC BY 4.0, voir **Crédits**), rangé dans `outils/assets/` et gardé hors dépôt.
  - **L'analyse :** un panneau mural de 430 000 faces, dont les 40 000 feuilles sont des octogones plats, à l'échelle 1/10 (6,6 cm une fois remis à taille réelle).
  - **L'extraction :** `outils/blender/lierre_feuilles.py` en tire les mesures dans `outils/assets/ivy-for-walls/feuilles.json`, hors dépôt.
  - **Le lierre remodélisé :** `floor2.py` dessine une vraie feuille de lierre (cinq lobes, base en cœur, en trois variantes) et fait pousser la plante sur l'îlot, de 2,2 × 4,2 m jusqu'au mur de façade. Les tiges partent d'un bac bas de 26 cm, couvrent le toit, passent le rebord et retombent dans le vide sur les trois côtés, jusqu'à 1,40 m. Rien ne touche les colonnes, les garde-corps ni les murs de l'accueil du bas.
- **Le garde-corps :**
  - la bande de dalle entre le vide et l'escalier est supprimée ;
  - une seule ligne va du coin du vide jusqu'à l'arrivée de l'escalier, et une autre longe le jardin de pierres ;
  - le même dessin partout : sabot d'acier, verre et main courante à 1,06 m, chaque ligne tirée d'un seul tenant.
- **Les rendus** sont dans `rendus/17-etage-lierre-et-garde-corps/`, la page est `pages/13-etage-lierre.png`.

**1er étage : l'îlot au-dessus de l'entrée, quatre premiers décors.** Remplacés par le lierre ; leurs rendus restent dans `rendus/16-etage-prototypes-ile/`.

- **Le bloc est retiré** (25/11). Il reste un îlot de 2,1 × 4,0 m, le toit de l'accueil du rez-de-chaussée, entouré par le vide sur trois côtés et inaccessible depuis la mezzanine. La dalle le couvre maintenant jusqu'à la rue.
- **Quatre décors végétaux** (`floor2.py -- ... bloc=1..4`, `bloc=0` pour l'îlot nu) :
  - B1, le jardin suspendu ;
  - B2, le rideau végétal ;
  - B3, le grand arbre ;
  - B4, le mur végétal.
- **Les rendus** sont dans `rendus/16-etage-prototypes-ile/`, la page est `pages/12-etage-ilot.png`.

**1er étage : le vide au-dessus des tambours.** Choix fait : les trois colonnes (V2). Les tambours montent jusqu'au plafond, ils font maintenant partie des éléments fixes. Les autres prototypes sont retirés du script ; leurs rendus restent dans `rendus/14-etage-prototypes-vide/`.

**Les prototypes du vide**, pour mémoire :

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
                14-etage-prototypes-vide/ (les prototypes pour le vide), 15-etage-mobilier/ (son mobilier),
                16-etage-prototypes-ile/ (les décors pour l'îlot, à la place du bloc),
                17-etage-lierre-et-garde-corps/ (le lierre, le garde-corps, l'étage tel qu'il est),
                18-batiment-entier/ (les deux étages raccordés, vus de la rue),
                19-carte-deux-etages/ (la carte avec le 1er étage), 20-refonte/ (le modèle repensé), 21-reprises/ (les endroits repris),
                22-sans-espace/ (les colonnes et les murs sans fente), 23-cave-palier-carte/ (la cave, le palier, la légende),
                24-cuisine-et-bar/ (la cuisine et le bar du rez-de-chaussée, trois prototypes),
                25-cuisine-ouverte/ (la cuisine ouverte retenue, le poste de service, la carte),
                26-plans-finaux/ (les plans d'architecte des deux étages, tirés du modèle : SVG, PNG, PDF),
                27-carte-readme/ (la carte telle qu'elle s'ouvre, les deux étages : l'image du README)
pages/          la page de chaque étape, en PNG
recherche/      00-video-concept/, 01 … 10 (les images retenues), sources.json, planche.png, _tri/ (les planches de tri),
                11-lair-archdaily/ (les 37 photos et 5 dessins du vrai restaurant, source.md),
                12-carte-interactive/sources.md (les références de la carte)
outils/         les scripts (voir plus bas)
carte/          la carte interactive : index.html, js/, css/, modele/ (les modèles en glTF : le rez-de-chaussée, le 1er
                étage et le rez-de-chaussée sous sa dalle), donnees/ (les tables des deux étages), vendor/three (three.js,
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
  - `plans=cuisine-salle,cuisine-comptoir,cuisine-passe,cuisine-service,cuisine-ligne,cuisine-froid,cuisine-plonge,cuisine-coin,cuisine-passage,cuisine-wc` (avec `variante=detail`) puis `cuisine-vol,cuisine-dessus` (avec `variante=fantome`) rendent les vues de la cuisine et du bar (une focale négative donne une vue orthographique de cette largeur) ; `prefixe=` préfixe les fichiers ;
  - `trace=modele/trace/rdc.json` lit le plan dans le modèle (la coupe à 1,20 m et ce qui est dessous), sans rendu ;
  - `export=carte/modele/floor1-fantome.glb` (avec `variante=fantome mobilier=1`) ou `floor1-entier.glb` (avec `variante=fil-de-fer mobilier=1`) exporte le modèle de la carte. Chaque objet garde son rôle et le numéro de sa table. Il faut ensuite recopier `modele/floor1-tables.json` dans `carte/donnees/`.
- **Numéroter les tables :** `numeros_tables.py` pose le numéro de chaque table sur la vue du haut en fantôme.
- **Redessiner les plans :** `outils/plans/plans.py [rdc] [etage1]` écrit les SVG et les PNG 4K de `rendus/10-plans/`. Il s'appuie sur trois fichiers : `dessin.py` (le kit de dessin), `rdc.py` et `etage1.py` (un étage chacun). Les murs du 1er étage sont vectorisés par `outils/vectoriser_etage1.py`.
- **La carte :** `carte_captures.mjs` sert la carte, fait toutes les captures de `rendus/9-carte-finale/` et `rendus/19-carte-deux-etages/`, puis la vidéo (`node outils/carte_captures.mjs video` pour la vidéo seule, `etage` pour les captures du 1er seules). Les réglages passent aussi par l'adresse de la carte : `?etage=1&vue=3d&style=fil-de-fer&systeme=B&numeros=5&legende=1&ouvert=style&heure=20:40&vitesse=0&fiche=6`.

  Le `.blend` n'est jamais enregistré à la main : c'est le script qui le refait.
- **La recherche :**
  - `pinterest.py` liste les épingles d'une page publique ;
  - `planches_contact.py` fait les planches de tri ;
  - `recherche_choix.py` télécharge les images retenues et écrit `sources.json`.
- **Les pages :** `page_etape1.py` à `page_etape19.py` et `page_recherche.py` écrivent le HTML dans `outils/pages/` (Inter, style minimal) et l'exportent en PNG avec `outils/pages/export.mjs`.

## Ce qui n'est pas dans le dépôt

Le dépôt ne contient pas le contenu de tiers :
- les plans, la coupe, l'axonométrie et la vidéo. Les plans sont ceux de RENESA, publiés sur ArchDaily, et doivent être cités ;
- les photos d'ArchDaily (© Avesh Gaur), et les pages des étapes 2 à 4 qui en montrent ;
- les images de la recherche (Pinterest), dont `recherche/sources.json` garde les liens ;
- les rendus et pages qui montrent le dessin du plan.

Le détail est dans `.gitignore`.

## Crédits

- **Les plans d'origine :** LAIR Restaurant & Bar, RENESA Architecture Design Interiors Studio (architecte principal Sanchit Arora), 2024, publiés sur ArchDaily ; photos © Avesh Gaur.
- **Le lierre de l'îlot au-dessus de l'entrée :** d'après « Ivy for walls » par arca_done (https://sketchfab.com/arca_done), publié sur Sketchfab le 25/05/2023 (https://sketchfab.com/3d-models/ivy-for-walls-b5e66f95a4de4cc19e68596f489eeaac), sous licence Creative Commons Attribution 4.0 (http://creativecommons.org/licenses/by/4.0/). Ses feuilles ont été mesurées, puis le lierre a été remodélisé par `floor2.py` ; le fichier d'origine reste hors dépôt.
- **three.js** (licence MIT), dans `carte/vendor/three/`.
