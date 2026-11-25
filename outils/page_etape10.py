# The working page of the 1st floor's prototypes (as floor1's step 6 page for the space by the bar): what stands over
# the drums in the double height, four proposals, each modelled to scale (outils/blender/floor2.py vide=1..4), seen
# across the void from the mezzanine and on the map's 3D view; the real place for reference (photo 33).
# Writes the map crops (rendus/14-etage-prototypes-vide/v*-carte.png), outils/pages/etape-10.html, then
# pages/10-etage-le-vide.png with outils/pages/export.mjs.
# usage: outils/.venv/bin/python outils/page_etape10.py
import subprocess
from pathlib import Path
from PIL import Image

R = Path(__file__).resolve().parents[1]
PG = R / 'outils' / 'pages'
D = R / 'rendus' / '14-etage-prototypes-vide'
Z = '../../rendus/14-etage-prototypes-vide/'
PH = '../../recherche/11-lair-archdaily/'

PROTOS = [
    (0, 'Aujourd\'hui', 'le vide est laissé vide',
     'Les tambours du rez-de-chaussée s\'arrêtent à 3,00 m, sous leur anneau. Au-dessus, rien jusqu\'au plafond de la '
     'mezzanine : 3,35 m de vide.'),
    (1, 'Le vrai lieu', 'les câbles tendus et leurs petites lampes',
     'C\'est ce que montrent les photos 9, 26 et 33. Au-dessus des tables, de petites lampes cylindriques pendent au bout '
     'de câbles tendus en diagonale jusqu\'aux deux bords du vide, à 2,50 m du sol du bas. Les câbles se croisent en '
     'une toile légère. Sur la carte, ce sont des traits fins qui ne cachent rien.'),
    (2, 'Trois colonnes', 'les tambours montent jusqu\'au plafond',
     'Chaque tambour se prolonge au-dessus de son anneau par un tube de six lames, séparées par des fentes de lumière, '
     'jusqu\'au plafond de la mezzanine (photo 33, où les tambours montent haut avec leurs fentes). Le haut reste ouvert : '
     'vu d\'en haut, on voit toujours les banquettes. Ce sont tes « trois colonnes », qui traversent les deux étages.'),
    (3, 'Trois halos', 'un anneau de lumière au-dessus de chaque tambour',
     'Un anneau fin de 2,5 m de diamètre, suspendu par trois câbles au-dessus de chaque tambour, à 0,90 m au-dessus du '
     'sol de la mezzanine : à hauteur des yeux pour qui est à la tablette. Vu du bas, il couronne la banquette. Le vide '
     'reste ouvert.'),
    (4, 'Trois colonnes et une lanterne', 'le bloc mêlé aux colonnes',
     'Les trois colonnes de V2, et le bloc au-dessus de l\'entrée devient une lanterne en pavés de verre dans un cadre '
     'd\'acier noir, comme les façades. Elle est creuse : un puits de lumière au-dessus de l\'entrée, qui prolonge la '
     'rangée de colonnes. Quatre volumes de lumière au bord du vide.'),
]

QUESTIONS = [
    'Lequel des quatre prototypes pour le vide ? On peut aussi en combiner deux : les câbles de V1 vont avec les '
    'colonnes de V2 ou les halos de V3.',
    'Pour le bloc : on le garde en métal noir (V1 à V3), ou il devient la lanterne de V4 ?',
]


def img(src, w, cap=None):
    c = f'<div class="cap">{cap}</div>' if cap else ''
    return f'<figure><img src="{src}" width="{w}">{c}</figure>'


for k, *_ in PROTOS:                            # the map view, cropped on the void
    src = D / f'v{k}-fantome-3d.png'
    if src.exists():
        Image.open(src).crop((520, 380, 1480, 1160)).save(D / f'v{k}-carte.png')

rangs = ''.join(
    f'<div class="row">{img(Z + f"v{k}-plan-vide.png", 800)}{img(Z + f"v{k}-carte.png", 610)}</div>'
    f'<div class="txt" style="max-width:1500px;margin-top:-8px"><b>V{k} · {t}</b>, {n}. {d}</div>'
    for k, t, n, d in PROTOS)

html = f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><link rel="stylesheet" href="style.css">
<style>.lead{{max-width:900px}}</style></head><body>
<div class="colw">
<section style="width:1520px">
  <div class="stitle">Restaurant · 1er étage · le vide au-dessus des tambours : quatre propositions</div>
  <div class="snote">25/11/2026 · chaque proposition est modélisée à l'échelle, vue depuis la mezzanine et sur la carte</div>
  <div class="txt lead">Au-dessus des tables, on n'avait encore rien modélisé. Dans le vrai lieu, ce n'est pas vide :
  les tambours se lisent sur toute la double hauteur, et des câbles tendus portent de petites lampes au-dessus des
  tables (photo 33). Voici quatre façons de le traiter, dont une pour le bloc au-dessus de l'entrée. Le rez-de-chaussée
  est en gris clair ; les vues de gauche sont prises depuis le bord droit du vide, celles de droite sont la vue 3D de la
  carte, en fantôme.</div>
  <div class="row">{img(PH + 'photo-33.jpg', 420, 'Le vrai lieu, photo 33 : les tambours, les câbles, les lampes')}</div>
</section>
<section style="width:1520px">
  {rangs}
</section>
<section style="width:1520px">
  <div class="stitle">Questions</div>
  <ol class="list">{''.join(f'<li>{q}</li>' for q in QUESTIONS)}</ol>
</section>
</div>
</body></html>'''
(PG / 'etape-10.html').write_text(html)
out = R / 'pages' / '10-etage-le-vide.png'
subprocess.run(['node', str(PG / 'export.mjs'), str(PG / 'etape-10.html'), str(out), '1'], check=True)
