# The working page of the open kitchen as chosen (A, 26/11 night): the shaft under the 1st floor's removed (the
# "open corridor"), the kitchen to the right facade, its doors wider, the service bay in front of them; the map
# re-exported. Writes outils/pages/etape-19.html, then pages/19-cuisine-ouverte.png.
# usage: outils/.venv/bin/python outils/page_etape19.py   (after the renders of rendus/25-cuisine-ouverte/ and the
#        map captures there: carte-rdc-3d.png, carte-rdc-cuisine.png, carte-rdc-dessus.png)
import subprocess
from pathlib import Path

R = Path(__file__).resolve().parents[1]
PG = R / 'outils' / 'pages'
Z = '../../rendus/25-cuisine-ouverte/'
Z24 = '../../rendus/24-cuisine-et-bar/'

QUESTIONS = [
    'La place devant les portes (le poste de service, le lambris de chêne) et les portes élargies te vont-elles ?',
    'Au 1er, la boîte de l\'ancienne « gaine d\'ascenseur » n\'a plus rien en dessous. Je la garde comme réserve '
    'fermée, ou je l\'ouvre sur la salle ?',
    'Ensuite : le plan final des deux étages, d\'après le modèle, puis les captures de la carte.',
]


def img(src, w, cap=None):
    c = f'<div class="cap">{cap}</div>' if cap else ''
    return f'<figure><img src="{src}" width="{w}">{c}</figure>'


def txt(avant, apres):
    return (f'<div class="txt" style="max-width:1460px"><b>Ce qui n\'allait pas.</b> {avant}</div>'
            f'<div class="txt" style="max-width:1460px"><b>Ce que j\'ai fait.</b> {apres}</div>')


html = f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><link rel="stylesheet" href="style.css">
<style>.lead{{max-width:900px}}</style></head><body>
<div class="colw">
<section style="width:1520px">
  <div class="stitle">Restaurant · la cuisine ouverte, telle que choisie</div>
  <div class="snote">26/11/2026 · le prototype A, et tes deux points</div>
  <div class="txt lead">Le prototype A est maintenant le seul dans le script : la cuisine ouverte sur le bar par-dessus
  un muret, la retombée avec les verres et les bouteilles suspendus, le comptoir en lattes de chêne. Les rendus de B et
  C restent dans <code>rendus/24-cuisine-et-bar/</code>.</div>
  <div class="lbl" style="margin-top:12px">1 · Le « couloir ouvert », les portes, le coin de la cuisine</div>
  <div class="row">{img(Z + 'avant-couloir.png', 720, 'Avant (ta capture) : le couloir ouvert')}{img(Z + 'avant-portes.png', 720, 'Avant (ta capture) : les portes, le coin à combler')}</div>
  {txt('Le « couloir » était la gaine sous celle du 1er. Le plan en faisait une boîte de 90 cm de large, fermée sur '
       'trois côtés et ouverte au sud : on aurait dit un couloir sans issue. Elle coupait le coin de la cuisine, et la '
       'porte de la cuisine, coincée contre elle, ne faisait que 90 cm.',
       'La gaine est retirée. Le mur de la cuisine file jusqu\'à la façade droite, et le coin nord-est devient de la '
       'cuisine : après la plonge, une table propre, une étagère de vaisselle (assiettes, casiers à verres) et le '
       'lave-mains, avec une étagère à assiettes au-dessus. Le nu intérieur de la façade est redressé d\'un seul tenant. '
       'Les portes de la cuisine sont replacées là où tu les as dessinées et élargies à 1,57 m : deux battants de chêne '
       'à double action, avec chacun un hublot et une plaque de poussée sur les deux faces, et des plinthes inox.')}
  <div class="row">{img(Z24 + 'A-plan-cuisine-dessus.png', 720, 'Avant : le fond vu du dessus')}{img(Z + 'plan-cuisine-dessus.png', 720, 'Après')}</div>
</section>
<section style="width:1520px">
  <div class="lbl">2 · La place devant les portes : le poste de service</div>
  <div class="row">{img(Z + 'plan-cuisine-service.png', 720, 'Depuis la salle : le poste de service et les portes')}{img(Z + 'plan-cuisine-passe.png', 720, 'Le bout du bar, la passe et les portes')}</div>
  <div class="txt" style="max-width:1460px">À la place de la gaine, entre le bout du bar, les portes et la façade, une
  place de 2,1 × 2,7 m sert les serveurs. Le long du mur, en dehors du débattement des portes, il y a un meuble de
  service en chêne : trois tiroirs à couverts, deux portes, un plateau de pierre. Dessus : la caisse (une tablette sur
  son pied), des carafes et un plateau de verres. Le mur est habillé de tasseaux de chêne, comme celui de l'accueil, et
  une étagère porte des verres et des serviettes. Les serveurs prennent les assiettes à la passe et les boissons au bout
  du bar, puis repartent vers la salle sans croiser le barman.</div>
  <div class="row">{img(Z + 'plan-cuisine-coin.png', 720, 'Le coin de la cuisine, jusqu\'à la façade, et les portes vues de dedans')}{img(Z + 'plan-cuisine-plonge.png', 720, 'La plonge, puis la table propre le long de la façade')}</div>
</section>
</div>
<div class="colw">
<section style="width:1520px">
  <div class="lbl">3 · Le bar et la cuisine ouverte</div>
  <div class="row">{img(Z + 'plan-cuisine-salle.png', 720, 'Depuis la salle')}{img(Z + 'plan-cuisine-comptoir.png', 720, 'Au bout du comptoir')}</div>
  <div class="row">{img(Z + 'plan-cuisine-ligne.png', 720, 'La ligne de cuisson, depuis les portes')}{img(Z + 'plan-cuisine-vol.png', 720, 'Comme sur la carte (style fantôme)')}</div>
  <div class="lbl" style="margin-top:12px">4 · Dans la carte</div>
  <div class="row">{img(Z + 'carte-rdc-cuisine.png', 720, 'La carte réexportée : la cuisine, le bar, le poste de service')}{img(Z + 'carte-rdc-dessus.png', 720, 'La vue du haut')}</div>
  <div class="txt" style="max-width:1460px">Les modèles de la carte sont réexportés avec la cuisine ouverte : le
  rez-de-chaussée, le 1er et le rez-de-chaussée sous sa dalle. L'étiquette « Bar » suit le comptoir raccourci, et les 7
  tabourets restent suivis un par un. Une vérification sans intersection a été refaite : il ne reste que des assemblages
  voulus.</div>
</section>
<section style="width:760px">
  <div class="stitle">Questions</div>
  <ol class="list">{''.join(f'<li>{q}</li>' for q in QUESTIONS)}</ol>
</section>
</div>
</body></html>'''
(PG / 'etape-19.html').write_text(html)
out = R / 'pages' / '19-cuisine-ouverte.png'
subprocess.run(['node', str(PG / 'export.mjs'), str(PG / 'etape-19.html'), str(out), '1'], check=True)
print('page', out)
