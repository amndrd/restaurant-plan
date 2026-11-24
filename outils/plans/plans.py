# The redrawn plans of the restaurant, for the site: the client's plans (floor1.png, floor2.png, low-resolution
# exports) redrawn with exact lines, in 4K (3840 x 2160), turned like the map's top view (bar on the left, entry on the
# right). Writes rendus/10-plans/<etage>.svg (vector, fonts embedded) and <etage>.png (4K, rendered by Chrome).
# usage: outils/.venv/bin/python outils/plans/plans.py [rdc] [etage1]
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dessin import Plan, R, cartouche  # noqa: E402

OUT = R / 'rendus' / '10-plans'
NOTE = ['Redessiné d’après les plans de RENESA Architecture', 'Design Interiors Studio (LAIR, Gurugram, 2024).']


def faire(nom, module, titre):
    p = Plan(centre=(837.5, 1308.5), echelle=1.15, origine=(1600, 1080))
    module.dessiner(p)
    for n, x, y in module.NUMEROS:
        X, Y = p.ecran(x, y)
        p.textes.append(f'<circle class="pastille" cx="{X:.1f}" cy="{Y:.1f}" r="20"/>'
                        f'<text class="num" x="{X:.1f}" y="{Y + 1:.1f}" style="font-size:24px;font-weight:600">{n}</text>')
    svg = p.svg(cartouche(3170, 330, titre, 'Plan redessiné', module.LEGENDE, p, NOTE))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f'{nom}.svg').write_text(svg)
    subprocess.run(['node', str(Path(__file__).parent / 'rendre.mjs'), str(OUT / f'{nom}.svg'), str(OUT / f'{nom}.png')], check=True)


if __name__ == '__main__':
    quels = sys.argv[1:] or ['rdc', 'etage1']
    if 'rdc' in quels:
        import rdc
        faire('rdc', rdc, 'Rez-de-chaussée')
    if 'etage1' in quels:
        import etage1
        faire('etage1', etage1, '1er étage')
