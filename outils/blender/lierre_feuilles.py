# The leaves of the ivy model (outils/assets/ivy-for-walls/, a third-party model, not in the repository): its leaves
# are modelled (about 40,000 loose parts of 7 faces, at 1/10 of their real size), with ribbon stems. This takes a set
# of typical leaves out of it, each set in its own frame (the base, where it is nearest to a stem, at the origin; the
# leaf along +y, its length 1; its face towards +z), for floor2.py to grow its own ivy on the island over the entry.
# Writes outils/assets/ivy-for-walls/feuilles.json (and a check image in the same folder).
# usage: blender -b -P outils/blender/lierre_feuilles.py
import bpy, bmesh, json, math, random, statistics
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree

D = Path(__file__).resolve().parents[1] / 'assets' / 'ivy-for-walls'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(D / 'source' / 'case_evy.fbx'))
o = next(o for o in bpy.data.objects if o.type == 'MESH')
mw = o.matrix_world
bm = bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table()
i_feuille = [m.name for m in o.data.materials].index('leaf')

# the stems: a KD tree on their vertices
tige = {v for f in bm.faces if f.material_index != i_feuille for v in f.verts}
kd = KDTree(len(tige))
for k, v in enumerate(tige):
    kd.insert(mw @ v.co, k)
kd.balance()

# the leaves: loose parts of the leaf material
vu, feuilles = set(), []
for f in bm.faces:
    if f.material_index != i_feuille or f.index in vu:
        continue
    pile, fs = [f], []
    vu.add(f.index)
    while pile:
        g = pile.pop(); fs.append(g)
        for e in g.edges:
            for h in e.link_faces:
                if h.index not in vu and h.material_index == i_feuille:
                    vu.add(h.index); pile.append(h)
    feuilles.append(fs)
print('feuilles', len(feuilles))

rnd = random.Random(3)
tailles = []
def cadre(fs):
    vs = list({v for g in fs for v in g.verts})
    ws = {v: mw @ v.co for v in vs}
    base = min(vs, key=lambda v: kd.find(ws[v])[2])            # the vertex nearest to a stem
    b = ws[base]
    bout = max(vs, key=lambda v: (ws[v] - b).length)
    L = (ws[bout] - b).length
    y = (ws[bout] - b).normalized()
    n = Vector()
    for g in fs:
        n += (mw.to_3x3() @ g.normal) * g.calc_area()
    n = (n - y * n.dot(y)).normalized()
    x = y.cross(n)
    loc = {v: ((ws[v] - b).dot(x) / L, (ws[v] - b).dot(y) / L, (ws[v] - b).dot(n) / L) for v in vs}
    larg = max(c[0] for c in loc.values()) - min(c[0] for c in loc.values())
    return vs, loc, L, larg

candidats = rnd.sample(feuilles, 4000)
mesures = []
for fs in candidats:
    vs, loc, L, larg = cadre(fs)
    mesures.append((L, larg, fs))
Ls = sorted(m[0] for m in mesures)
med = statistics.median(Ls)
print('longueur mediane', round(med, 5), 'p10', round(Ls[len(Ls) // 10], 5), 'p90', round(Ls[9 * len(Ls) // 10], 5))
# typical leaves: length within 15 % of the median, a real blade (width 0.5 - 1.1 of the length), 7 faces
bons = [m for m in mesures if abs(m[0] - med) < 0.15 * med and 0.5 < m[1] < 1.1 and len(m[2]) == 7]
choix = rnd.sample(bons, 8)
sortie = []
for L, larg, fs in choix:
    vs, loc, _, _ = cadre(fs)
    idx = {v: k for k, v in enumerate(vs)}
    sortie.append(dict(v=[[round(c, 4) for c in loc[v]] for v in vs], f=[[idx[v] for v in g.verts] for g in fs],
                       largeur=round(larg, 3)))
(D / 'feuilles.json').write_text(json.dumps(dict(
    note='Feuilles extraites du modèle ivy-for-walls (tiers, hors dépôt) : repère propre, base en 0, longueur 1.',
    longueur_import_m=round(med, 5), echelle_reelle=10, feuilles=sortie)))
print('écrit', D / 'feuilles.json', len(sortie), 'feuilles,', len(bons), 'candidates')

# a check image: the eight leaves side by side, from the front
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob)
me = bpy.data.meshes.new('verif'); b2 = bmesh.new()
for k, fl in enumerate(sortie):
    vv = [b2.verts.new((x + 1.3 * k, y, z)) for x, y, z in fl['v']]
    for f in fl['f']:
        b2.faces.new([vv[i] for i in f])
b2.to_mesh(me); b2.free()
ob = bpy.data.objects.new('verif', me); bpy.context.scene.collection.objects.link(ob)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.show_object_outline = True
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 10.8
co = bpy.data.objects.new('c', cd); sc.collection.objects.link(co)
co.location = (4.55, 0.5, 10); sc.camera = co
sc.render.resolution_x, sc.render.resolution_y = 1600, 300
sc.render.filepath = str(D / 'feuilles-verif.png')
bpy.ops.render.render(write_still=True)
