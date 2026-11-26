# Floor2 (the 1st floor, the mezzanine) of the restaurant: the plan laid at real scale and the model built over it,
# step by step like floor1 (outils/blender/floor1.py), with the same materials, styles and cameras.
# The same frame as floor1 (floor2.png is drawn in the pixels of floor1.png, 120 px = 1 m) and the same world origin;
# here z = 0 is the floor of the mezzanine (the top of its slab, 3.35 m over the ground floor).
# The script is the source: the .blend is regenerated, never saved by hand.
#
# usage: blender -b -P floor2.py -- [vue=dessus,iso,coupe] [ech=100] [save=<file.blend>] [out=<dossier>]
#            (step 1, the shell: walls, columns, facades, the slab and its voids, parapets, the two half drums, the
#             volume over the entry, the stair up, the top of the spiral stair)
#        blender -b -P floor2.py -- variante=fantome|fil-de-fer elements=1 [samples=96]
#            (step 2, the fixed elements, as floor1's step 3: glass blocks, the omakase bar, the banquettes of the half
#             drums, the ledge over the void, the lab counter, the curtains, the clad volume over the entry, the
#             detailed spiral stair; in the two views of the map, the ground floor seen through the voids)
#        blender -b -P floor2.py -- variante=detail elements=1 plans=omakase,banquette,rebord,bloc,escalier
#            (the close-ups of step 2, in the solid white model)
#        blender -b -P floor2.py -- variante=detail elements=1 plans=ile,ile-bas,garde-corps [prefixe=...]
#            (the ivy on the island over the entry, where the block was, and the joined parapets, close up)
#        blender -b -P floor2.py -- variante=fantome|fil-de-fer|detail mobilier=1 [plans=...]
#            (step 3, the furniture, as floor1's step 4; also writes modele/floor2-tables.json)
#        blender -b -P floor2.py -- variante=fantome|fil-de-fer mobilier=1 export=carte/modele/floor2-<x>.glb
#                                   [dessous=carte/modele/floor1-sous-dalle.glb]
#            (the model of the interactive map, and the ground floor under the slab as the map sets it under it)
# Since 25/11 the two storeys are one building: the slab runs out under the outer walls of both, the ground floor
# (floor1's whole model) stands under it in the same materials and lines, the columns go on up.
import bpy, bmesh, json, math, random, sys
from pathlib import Path
from mathutils import Matrix, Vector

ICI = Path(__file__).resolve().parent
RACINE = ICI.parents[1]
ARGS = dict(a.split('=', 1) for a in (sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []) if '=' in a)
VUES = ARGS.get('vue', '' if 'variante' in ARGS else 'dessus,iso,coupe').split(',')
ECH = int(ARGS.get('ech', 100))
OUT = Path(ARGS.get('out', RACINE / 'rendus' / '12-etage-coque'))

DATA = json.loads((RACINE / 'modele' / 'etage1-murs.json').read_text())
sys.path.insert(0, str(ICI))
import refonte                            # the reworked building (26/11), shared with floor1.py
PX = 1 / DATA['echelle_px_par_m']        # metres per plan pixel
CX, CY = 837, 1230                       # plan pixel at the world origin (as floor1)
H = 3.0                                  # the mezzanine's clear height (floor to the roof slab), from the section
H_RDC = 3.35                             # the ground floor under it (floor1.py)
DALLE = 0.30                             # the slab
ELEMENTS = ARGS.get('elements') == '1'   # step 2: the fixed elements
MOBILIER = ARGS.get('mobilier') == '1'   # step 3: the furniture (and its table numbers for the map)
ELEMENTS = ELEMENTS or MOBILIER
ANGLE = ARGS.get('angle', 'station')     # the south-east corner (26/11): a service station, or a table for two


def P(x, y, z=0.0):
    return Vector(((x - CX) * PX, -(y - CY) * PX, z))


# ---------------------------------------------------------------- scene
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
for c in ('Plan', 'Coque', 'Sols', 'Vitrages', 'Traits-fins', 'Tambours', 'Escalier', 'Dessous'):
    sc.collection.children.link(bpy.data.collections.new(c))


def coll(name):
    if name not in bpy.data.collections:
        sc.collection.children.link(bpy.data.collections.new(name))
    return bpy.data.collections[name]


def mat(name, rgb, rough=0.6, alpha=1.0, transmission=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = (*rgb, 1)
    b.inputs['Roughness'].default_value = rough
    if transmission:
        b.inputs['Transmission Weight'].default_value = transmission
        b.inputs['IOR'].default_value = 1.45
    if alpha < 1:
        b.inputs['Alpha'].default_value = alpha
    return m


# the materials of floor1 (same names, so the map styles set them the same way)
M_MUR = mat('mur', (0.82, 0.81, 0.79), 0.75)
M_SOL = mat('sol-sombre', (0.20, 0.20, 0.21), 0.55)
M_DALLE = mat('dalle', (0.86, 0.85, 0.83), 0.8)
M_GRAVIER = mat('gravier', (0.33, 0.33, 0.32), 0.9)
M_VERRE = mat('verre', (0.80, 0.88, 0.92), 0.05, transmission=1.0)
M_CADRE = mat('cadre', (0.10, 0.10, 0.11), 0.4)
M_TAMBOUR = mat('tambour', (0.16, 0.16, 0.17), 0.5)
M_POTEAU = mat('poteau', (0.86, 0.85, 0.83), 0.7)
M_MARCHE = mat('marche', (0.12, 0.12, 0.13), 0.45)


def obj(name, me, collection, material):
    o = bpy.data.objects.new(name, me)
    coll(collection).objects.link(o)
    me.materials.append(material)
    return o


def extrude_loops(name, loops, z0, z1, collection, material):
    """2D curve (even-odd fill, so holes work) extruded between z0 and z1, converted to mesh."""
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '2D'
    cu.fill_mode = 'BOTH'
    cu.extrude = (z1 - z0) / 2
    for loop in loops:
        sp = cu.splines.new('POLY')
        sp.points.add(len(loop) - 1)
        for k, (x, y) in enumerate(loop):
            v = P(x, y)
            sp.points[k].co = (v.x, v.y, 0, 1)
        sp.use_cyclic_u = True
    o = bpy.data.objects.new(name, cu)
    coll(collection).objects.link(o)
    o.location.z = (z0 + z1) / 2
    cu.materials.append(material)
    return o


def box(name, x0, y0, x1, y1, z0, z1, collection, material):
    return extrude_loops(name, [[(x0, y0), (x1, y0), (x1, y1), (x0, y1)]], z0, z1, collection, material)


def ring(name, cx, cy, r_out, r_in, a0, a1, z0, z1, collection, material, seg=96):
    """Ring sector between image angles a0 -> a1 (degrees, y down), r in plan pixels."""
    bm = bmesh.new()
    full = abs(a1 - a0) >= 359.9
    n = seg if full else max(8, int(seg * abs(a1 - a0) / 360))
    pts = [(math.cos(math.radians(a0 + (a1 - a0) * k / n)), math.sin(math.radians(a0 + (a1 - a0) * k / n)))
           for k in range(n + (0 if full else 1))]
    def v(r, c, z):
        return bm.verts.new(P(cx + r * c[0], cy + r * c[1], z))
    lo_o = [v(r_out, c, z0) for c in pts]; hi_o = [v(r_out, c, z1) for c in pts]
    lo_i = [v(r_in, c, z0) for c in pts]; hi_i = [v(r_in, c, z1) for c in pts]
    m = len(pts)
    for k in (range(m) if full else range(m - 1)):
        j = (k + 1) % m
        bm.faces.new((lo_o[k], lo_o[j], hi_o[j], hi_o[k])).smooth = True
        bm.faces.new((lo_i[j], lo_i[k], hi_i[k], hi_i[j])).smooth = True
        bm.faces.new((hi_o[k], hi_o[j], hi_i[j], hi_i[k]))
        bm.faces.new((lo_i[k], lo_i[j], lo_o[j], lo_o[k]))
    if not full:
        for k in (0, m - 1):
            bm.faces.new((lo_o[k], lo_i[k], hi_i[k], hi_o[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    return obj(name, me, collection, material)


def cylinder(name, cx, cy, r, z0, z1, collection, material, seg=64):
    bm = bmesh.new()
    lo = [bm.verts.new(P(cx + r * math.cos(2 * math.pi * k / seg), cy + r * math.sin(2 * math.pi * k / seg), z0)) for k in range(seg)]
    hi = [bm.verts.new(P(cx + r * math.cos(2 * math.pi * k / seg), cy + r * math.sin(2 * math.pi * k / seg), z1)) for k in range(seg)]
    for k in range(seg):
        j = (k + 1) % seg
        bm.faces.new((lo[k], lo[j], hi[j], hi[k])).smooth = True
    bm.faces.new(list(reversed(lo))); bm.faces.new(hi)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    return obj(name, me, collection, material)


def arc(cx, cy, r, a0, a1, n=None):
    n = n or max(8, int(abs(a1 - a0) / 3))
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * k / n)), cy + r * math.sin(math.radians(a0 + (a1 - a0) * k / n)))
            for k in range(n + 1)]


def to_mesh(o):
    """A curve object turned into a mesh (for the booleans and the cleaner line styles)."""
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.convert(target='MESH')
    return bpy.context.view_layer.objects.active


def soustraire(o, outils):
    """Boolean difference (exact), the tools removed afterwards."""
    for t in outils:
        md = o.modifiers.new('moins', 'BOOLEAN')
        md.operation = 'DIFFERENCE'
        md.solver = 'EXACT'
        md.object = t
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier=md.name)
    for t in outils:
        bpy.data.objects.remove(t, do_unlink=True)
    return o


def mur_suivant(name, pts, z0, z1, ep, collection, material):
    """A thin wall (a parapet) along a polyline, ep in plan px."""
    bm = bmesh.new()
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        if L < 1e-6:
            continue
        nx, ny = -(y1 - y0) / L * ep / 2, (x1 - x0) / L * ep / 2
        q = [(x0 + nx, y0 + ny), (x1 + nx, y1 + ny), (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)]
        lo = [bm.verts.new(P(x, y, z0)) for x, y in q]
        hi = [bm.verts.new(P(x, y, z1)) for x, y in q]
        bm.faces.new(lo[::-1]); bm.faces.new(hi)
        for k in range(4):
            j = (k + 1) % 4
            bm.faces.new((lo[k], lo[j], hi[j], hi[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    return obj(name, me, collection, material)


def face_colonne(x0, x1, col, s):
    """Where a straight end (from x0 to x1, across a facade or a wall) first meets a column's round side: the y of the
    column's nearest point over that width. s = +1: the column lies towards +y."""
    cx, cy, r = col
    ys = [cy - s * math.sqrt(max(r * r - (cx - (x0 + (x1 - x0) * k / 20)) ** 2, 0.0)) for k in range(21)]
    return min(ys) if s > 0 else max(ys)


def joue(name, x0, x1, y_f, col, s, z0, z1, collection, material):
    """(26/11) Fills the sliver between a straight end at y_f (from x0 to x1) and a column's round side: no gap where
    a facade or a wall meets a column."""
    cx, cy, r = col
    pts = [(x0, y_f), (x1, y_f)]
    for k in range(13):
        x = x1 + (x0 - x1) * k / 12
        p_ = (x, cy - s * math.sqrt(max(r * r - (cx - x) ** 2, 0.0)))
        if abs(p_[1] - pts[-1][1]) > 1e-4 or abs(p_[0] - pts[-1][0]) > 1e-4:
            pts.append(p_)
    if abs(pts[-1][1] - pts[0][1]) < 1e-4 and abs(pts[-1][0] - pts[0][0]) < 1e-4:
        pts.pop()
    if len(pts) >= 3 and z1 - z0 > 0.002:
        bm = bmesh.new(); prisme(bm, pts, z0, z1); mesh_obj(name, bm, collection, material)


# ---------------------------------------------------------------- the plan of the floor
SOL = [(384, 140), (1457, 140), (1457, 2403), (576, 2403),
       (576, 2276), (601, 2276), (601, 2245), (232, 2245), (232, 842), (384, 842)]          # with the island over the entry, where the block was,
# and (26/11) the south-east corner: the floor goes on to the street facade there, the corner is part of the room
# the void over the room: along the ledge (y 1172), round the corner, down the right side to the stair, whose opening
# it meets (25/11: no more strip of slab between the void and the stair, so one parapet instead of two side by side)
VIDE = [(237, 1172), (1012, 1172)] + arc(1012, 1242, 70, -90, 0, 12)[1:] + [(1082, 1984)] + \
    arc(1082, 2172, 188, -90, -136, 16)[1:] + [(861, 2046), (861, 1896), (601, 1896), (601, 2250), (237, 2250)]
# the void over the rock garden (the gravel seen from above on floor2.png)
JARDIN = [(861, 2040), (1057, 2040), (1057, 2126), (1238, 2126)] + arc(1238, 2187, 61, -90, 0, 10)[1:] + \
    [(1299, 2403), (861, 2403)]          # down to the street facade (26/11): the entry's double height against its glass
HX, HY, R_ESC = 1082, 2172, 186          # the spiral stair (floor1.py: hub, treads to r 180, its rail to 185) and its opening
ESCALIER_HAUT = (485, 140, 852, 247)     # the stair up to the roof floor, rising towards +x from x 572
# the parapet, one line on the slab edge: round the corner of the void, down its right side, then on round the
# stair's opening (r 190) to the stair's arrival (-40 deg); past the arrival, along the rock garden's opening to the
# wall 1064. Along the room side, the ledge (step 2) or, on the shell alone, the glass carries on to the lab.
R_GC = R_ESC + 4
A_GC = -math.degrees(math.acos(1.5 / R_GC))                  # where the ring meets the void's right side (x 1083.5)
GARDE_CORPS = arc(1012, 1242, 71.5, -90, 0, 32) + arc(HX, HY, R_GC, A_GC, -40, 30)
_jardin = [p_ for p_ in arc(1238, 2187, 62.5, -90, 0, 30) if math.hypot(p_[0] - HX, p_[1] - HY) >= R_GC]
A_PALIER = math.atan2(_jardin[0][1] - HY, _jardin[0][0] - HX)    # where the stair's landing ends (-12 deg)
# (26/11 evening) the parapet starts at the stair's core: it closes the landing's side on the void
_u, _n = (math.cos(A_PALIER), math.sin(A_PALIER)), (math.sin(A_PALIER), -math.cos(A_PALIER))   # 3 px onto the landing
GARDE_CORPS_JARDIN = [(HX + 43 * _u[0] + 3 * _n[0], HY + 43 * _u[1] + 3 * _n[1]),
                      (HX + R_GC * _u[0] + 3 * _n[0], HY + R_GC * _u[1] + 3 * _n[1])] + _jardin + \
    [(1300.5, 2209), (1300.5, 2401)]     # on along the corner, now floor (26/11), to the street facade

# ---- the whole building (25/11): the two floors are one building, not two models set one on the other.
# The ground floor's walls (floor1.py's, vectorised from floor1.png, in the same pixels)
DATA_RDC = json.loads((RACINE / 'modele' / 'floor1-murs.json').read_text())
# The outer walls round the lab, which the plan leaves black
# (they meet without overlapping: shared faces of two walls render as dark streaks)
# 26/11: over the void, between the piers of the ground floor (y 1208 - 2173), the left facade is glass blocks on
# both storeys, the solid wall kept only round the lab and at the corners
MURS_LABO = [(200, 752, 382, 842), (200, 842, 232, 1208), (200, 2173, 232, 2245), (200, 2245, 599.5, 2276),
             (232, 1167, 384, 1173), (569, 2276, 580, 2286)]   # the last one closes the 8 cm slit before wall 1065
FACADE_OUEST = [1211 + (2170 - 1211) * k / 7 for k in range(8)]      # floor1's mullions of facade-gauche-b
# the walls of the plan left out or cut (26/11): the inner layers of the left facade (15, 16), the outer band in
# front of the right glass blocks (860), the walls of the south-east corner (1064, 1066) and the blind wall over the
# entry (1068), which becomes glass blocks
ETAGE_SANS = {16, 860, 1064, 1066, 1068,
              17, 731, 732, 733, 741, 767, 768,   # (26/11 evening) the small walls round the omakase bar
              734, 770}                           # (26/11 night) the lift shaft's stubs: the shaft became a storeroom
# (walls 9, 10, 11, 14 fill notches of the north wall 5: kept; the slit between 10 and 11 is filled)
ETAGE_JOINTS = [(1313, 99, 1316, 113),
                (1445.5, 626, 1458, 634), (1455.5, 634, 1458, 644)]   # the shaft's corner on the facade
ETAGE_REMPLACE = {15: [(382, 751), (399, 751), (399, 841), (382, 841)]}
ANGLE_SE = refonte.ANGLE_SE               # the corner pier, over the ground floor's
# (26/11 evening) the omakase bar redrawn: the kitchen corner at its west end (x 396 - 600, y 140 - 434), open on the
# chef's aisle, closed on the room by a glazed partition; the storeroom behind the bar's back; the toilets' door
CUISINE_CLOISON = (396, 434, 584, 444)
MURS_WC = [(1290, 139, 1300, 152), (1290, 236, 1300, 248)]           # the door between them, y 152 - 236
# The lift shaft (4 on floor2.png, measured there: drawn in dark grey, the vectorising missed it) stood over the ground
# floor's shaft (floor1's wall 16). Both are gone (26/11 night: the ground floor's became the kitchen's corner): up here
# its place, from the toilets' wall (730) to the facade, is a storeroom behind the toilets' passage, closed by a thin
# wall with a door (RESERVE_PORTE) and by the shaft's old south wall. The outer band of the right facade, also missed
# by the vectorising, stands over floor1's (walls 17, 55, 288): the right facade reads on the two storeys.
RESERVE = (1333, 260, 1458, 626)
RESERVE_PORTE = (300, 408)
RESERVE_MURS = [(1321, 260, 1333, RESERVE_PORTE[0]), (1321, RESERVE_PORTE[1], 1333, 626), (1321, 626, 1445.5, 644)]
BANDE_EST = [(1458, 140, 1481, 644)]     # along the shaft only (26/11): elsewhere the glass blocks show
# The columns: the ground floor's go on up (floor1.py's positions); the one in the void (257) is one shaft, from the
# ground floor through the slab's level to the mezzanine's ceiling
POTEAUX = {841: (405.1, 805.7, 49.2), 995: (405.1, 1516.5, 49.2),
           # (26/11) the right facade's two columns as the ground floor's (the plan drew them thinner up here)
           843: (1477.5, 805.0, 66.8), 989: (1477.5, 1516.7, 67.1)}
DEMI_CX = 1286.5                          # the half drums, 10 cm off the column's side (26/11; the plan: 1298.5)


def dans(pt, poly):
    x, y = pt; c = False
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            c = not c
    return c


def build_plan_image():
    W, Hh = 2000, 2828
    me = bpy.data.meshes.new('plan')
    bm = bmesh.new()
    vs = [bm.verts.new(P(x, y, -0.002)) for x, y in ((0, Hh), (W, Hh), (W, 0), (0, 0))]
    f = bm.faces.new(vs)
    uv = bm.loops.layers.uv.new()
    for l, c in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        l[uv].uv = c
    bm.to_mesh(me); bm.free()
    m = bpy.data.materials.new('plan')
    m.use_nodes = True
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(str(RACINE / 'floor2.png'))
    tex.interpolation = 'Cubic'
    nt.links.new(tex.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.9
    obj('plan', me, 'Plan', m)


def murs_etage():
    """This floor's walls from the plan (name, outline), reworked (26/11)."""
    out = []
    for mu in DATA['murs']:
        if mu['id'] in ETAGE_SANS:
            continue
        out.append((str(mu['id']), ETAGE_REMPLACE.get(mu['id'], mu['contour'])))
    return out


def unir(o, outils):
    """Boolean union (exact) of o with the tools, joined first into one mesh; the tools removed afterwards."""
    bpy.ops.object.select_all(action='DESELECT')
    for t in outils:
        t.select_set(True)
    bpy.context.view_layer.objects.active = outils[0]
    bpy.ops.object.join()
    t = bpy.context.view_layer.objects.active
    md = o.modifiers.new('plus', 'BOOLEAN')
    md.operation = 'UNION'
    md.solver = 'EXACT'
    md.use_self = True
    md.object = t
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.modifier_apply(modifier=md.name)
    bpy.data.objects.remove(t, do_unlink=True)
    return o


def build_dalle():
    """The slab with its openings: the void over the room, the rock garden, the round opening of the stair. It runs
    out under the outer walls of both storeys, to the faces of the building (25/11): one band of slab all round,
    between the ground floor's walls and the mezzanine's, as on the section of the place (3d-1.png)."""
    dalle = to_mesh(extrude_loops('dalle', [SOL], -DALLE, 0.0, 'Sols', M_SOL))
    pieds = [c for _, c in murs_etage()] + [b[0] for _, b in refonte.murs_rdc(DATA_RDC)]
    pieds += [[(x0, y0), (x1, y0), (x1, y1), (x0, y1)] for x0, y0, x1, y1 in
              MURS_LABO + RESERVE_MURS + BANDE_EST + [ANGLE_SE, (200, 842, 232, 2276), (580, 2403, 1445.5, 2414)]]
    # (the last two: the slab's band under the glass blocks of the left facade and of the street facade)
    outils = [to_mesh(extrude_loops(f't-pied-{k}', [c], -DALLE, 0.0, 'Sols', M_SOL)) for k, c in enumerate(pieds)]
    for k, p in enumerate(DATA['poteaux'] + DATA_RDC['poteaux']):
        cx, cy, r = POTEAUX.get(p['id'], (p['cx'], p['cy'], p['r']))
        if p['id'] == 41:                       # floor1.py's own correction: the corner column, half in the pier
            cx, r = 405.1, 49.2
        outils.append(cylinder(f't-poteau-{k}', cx, cy, r, -DALLE, 0.0, 'Sols', M_SOL))
    unir(dalle, outils)
    outils = [to_mesh(extrude_loops('t-vide', [VIDE], -1, 1, 'Sols', M_SOL)),
              to_mesh(extrude_loops('t-jardin', [JARDIN], -1, 1, 'Sols', M_SOL)),
              cylinder('t-escalier', HX, HY, R_ESC, -1, 1, 'Sols', M_SOL, seg=120)]
    soustraire(dalle, outils)
    # its edge and underside in a light concrete, the walking surface dark (as floor1's floors)
    dalle.data.materials.append(M_DALLE)
    for p in dalle.data.polygons:
        p.material_index = 0 if (p.normal.z > 0.9) else 1


# ---------------------------------------------------------------- step 2 helpers (as floor1's step 3)
M_BANQUETTE = mat('banquette', (0.11, 0.10, 0.09), 0.6)
M_PIERRE = mat('pierre', (0.20, 0.19, 0.18), 0.95)
M_COMPTOIR = mat('comptoir', (0.05, 0.05, 0.05), 0.3)
M_MEUBLE = mat('meuble', (0.09, 0.085, 0.08), 0.5)
M_PAVE = mat('pave', (0.80, 0.84, 0.85), 0.15, transmission=0.9)
M_MIROIR = mat('miroir', (0.92, 0.92, 0.92), 0.05)
M_RIDEAU = mat('rideau', (0.07, 0.07, 0.07), 0.8)


def relief(m, scale, strength):
    """Bump from a noise texture in object space (rough stone, gravel)."""
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = scale
    nz.inputs['Detail'].default_value = 6
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    bu = nt.nodes.new('ShaderNodeBump')
    bu.inputs['Strength'].default_value = strength
    nt.links.new(nz.outputs['Fac'], bu.inputs['Height'])
    nt.links.new(bu.outputs['Normal'], b.inputs['Normal'])


if ELEMENTS:
    relief(M_PIERRE, 18, 0.7)                   # the lava stone band of the booths


def mesh_obj(name, bm, collection, material):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    return obj(name, me, collection, material)


def bm_box(bm, x0, y0, x1, y1, z0, z1):
    """Box given by two plan corners (px) and two heights (m)."""
    a, b = P(x0, y0), P(x1, y1)
    X0, X1, Y0, Y1 = min(a.x, b.x), max(a.x, b.x), min(a.y, b.y), max(a.y, b.y)
    vs = [bm.verts.new((x, y, z)) for z in (z0, z1) for y in (Y0, Y1) for x in (X0, X1)]
    for f in ((0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)):
        bm.faces.new([vs[i] for i in f])


def prisme(bm, pts, z0, z1):
    """Vertical prism on a plan polygon (px)."""
    lo = [bm.verts.new(P(x, y, z0)) for x, y in pts]
    hi = [bm.verts.new(P(x, y, z1)) for x, y in pts]
    bm.faces.new(list(reversed(lo))); bm.faces.new(hi)
    for k in range(len(pts)):
        j = (k + 1) % len(pts)
        bm.faces.new((lo[k], lo[j], hi[j], hi[k]))


def blocs(bm, axe, d0, d1, u0, u1, z0, z1, pas_u=0.2, pas_z=0.2, bas=0.0, top=99.0, joint=0.012, bj=None):
    """A grid of glass blocks: axe 'y' = wall plane x in [d0, d1] running along y in [u0, u1] (px),
    axe 'x' = wall plane y in [d0, d1] running along x. Heights z0 - z1, blocks clipped to [bas, top].
    bj: (26/11) the mortar of the joints, 2 mm back from the faces, filling every joint and the half joints along the
    frame: the panel has no gap through it."""
    cols = max(1, round((u1 - u0) * PX / pas_u)); pu = (u1 - u0) / cols
    rows = max(1, round((z1 - z0) / pas_z)); pz = (z1 - z0) / rows
    j = joint / 2
    def boite(b_, ua, ub, za, zb, da, db):
        if axe == 'y':
            bm_box(b_, da, ua, db, ub, za, zb)
        else:
            bm_box(b_, ua, da, ub, db, za, zb)
    for i in range(cols):
        a, b = u0 + i * pu + j / PX, u0 + (i + 1) * pu - j / PX
        for r in range(rows):
            za, zb = max(z0 + r * pz + j, bas), min(z0 + (r + 1) * pz - j, top)
            if zb - za < 0.004:
                continue
            boite(bm, a, b, za, zb, d0, d1)
    if bj is None:
        return
    da, db = d0 + 0.002 / PX, d1 - 0.002 / PX
    zba, zbb = max(z0, bas), min(z1, top)
    if zbb - zba < 0.004:
        return
    for i in range(cols + 1):                    # the upright joints, the whole height
        ua, ub = max(u0, u0 + i * pu - j / PX), min(u1, u0 + i * pu + j / PX)
        boite(bj, ua, ub, zba, zbb, da, db)
    for i in range(cols):                        # the level joints, between the uprights
        a, b = u0 + i * pu + j / PX, u0 + (i + 1) * pu - j / PX
        for r in range(rows + 1):
            za, zb = max(z0, z0 + r * pz - j, bas), min(z1, z0 + r * pz + j, top)
            if zb - za > 0.0005:
                boite(bj, a, b, za, zb, da, db)


def paves(name, axe, c, travees, bas, top, ep=5.0):
    """Glass block facade panels between the mullions (as floor1): blocks of about 0.2 m, from the sill (0.06 m) to
    the head of the frame (H - 0.08), clipped to [bas, top]."""
    bm = bmesh.new(); bj = bmesh.new()
    for u0, u1 in travees:
        if u1 - u0 > 6:
            blocs(bm, axe, c - ep, c + ep, u0, u1, 0.06, H - 0.08, bas=bas, top=top, bj=bj)
    if len(bj.verts):                            # (26/11) the mortar, as thin lines
        mesh_obj(name + '-joints', bj, 'Traits-fins', M_MUR)
    else:
        bj.free()
    if len(bm.verts):
        return mesh_obj(name + '-paves', bm, 'Traits-fins', M_PAVE)
    bm.free()


def sweep(name, path, profil, collection, material, ref=None):
    """A closed profile [(d, z, smooth)] swept along a path of world points: d is the offset along the path's
    normal, which points towards `ref` when given. smooth applies to the face from that point to the next."""
    bm = bmesh.new()
    n = len(path)
    rings = []
    for i, p in enumerate(path):
        a_, b_ = path[max(i - 1, 0)], path[min(i + 1, n - 1)]
        t = Vector((b_.x - a_.x, b_.y - a_.y, 0)).normalized()
        nn = Vector((-t.y, t.x, 0))
        if ref is not None and nn.dot(Vector((ref.x - p.x, ref.y - p.y, 0))) < 0:
            nn = -nn
        rings.append([bm.verts.new((p.x + nn.x * d, p.y + nn.y * d, z)) for d, z, _ in profil])
    m = len(profil)
    for i in range(n - 1):
        A, B = rings[i], rings[i + 1]
        for j in range(m):
            k = (j + 1) % m
            bm.faces.new((A[j], B[j], B[k], A[k])).smooth = profil[j][2]
    bm.faces.new(rings[0]); bm.faces.new(list(reversed(rings[-1])))
    return mesh_obj(name, bm, collection, material)


def arrondi(cx_, cz, rd, rz, a0, a1, seg, lisse=True):
    return [(cx_ + rd * math.cos(math.radians(a0 + (a1 - a0) * k / seg)),
             cz + rz * math.sin(math.radians(a0 + (a1 - a0) * k / seg)), lisse) for k in range(seg + 1)]


def couper(o, z, garder):
    """Bisect a closed mesh at height z, keep 'bas' or 'haut', and close the cut."""
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-6, plane_co=(0, 0, z),
                           plane_no=(0, 0, 1), clear_outer=garder == 'bas', clear_inner=garder == 'haut')
    bord = [e for e in bm.edges if e.is_boundary]
    if bord:
        for f in bmesh.ops.holes_fill(bm, edges=bord, sides=0)['faces']:
            f.smooth = False
    bm.to_mesh(o.data); bm.free()


def separer(objs, cut, m_ghost=None):
    """The map cut: below `cut` the element stays solid; above, a see-through copy (m_ghost) or nothing."""
    for o in objs:
        zz = [v.co.z for v in o.data.vertices]
        if max(zz) <= cut:
            continue
        if m_ghost is not None:
            g = o.copy(); g.data = o.data.copy(); g.name = o.name + '-fantome'
            coll('Fantome').objects.link(g)
            if any(c.name == 'Traits-fins' for c in o.users_collection):
                coll('Traits-fins').objects.link(g)   # keeps the thin light lines
            if min(zz) < cut:
                couper(g, cut + 0.004, 'haut')
            g.data.materials.clear(); g.data.materials.append(m_ghost)
            g.visible_shadow = False
        if min(zz) >= cut:
            bpy.data.objects.remove(o)
        else:
            couper(o, cut, 'bas')


# ---------------------------------------------------------------- step 1: the shell
def build_coque(top, bas=0.0):
    # ---- walls (vectorised from floor2.png), and the outer walls round the lab that the plan leaves black; the lab
    #      is closed on the void side like wall 952
    for k, (nom, c) in enumerate(murs_etage()):
        extrude_loops(f"mur-{nom}-{k}", [c], bas, top, 'Coque', M_MUR)
    box('mur-angle-se', *ANGLE_SE, bas, top, 'Coque', M_MUR)
    for k, (x0, y0, x1, y1) in enumerate(MURS_LABO):
        box(f'mur-labo-{k}', x0, y0, x1, y1, bas, top, 'Coque', M_MUR)
    # the storeroom where the lift shaft was (26/11 night), its door's lintel
    for k, (x0, y0, x1, y1) in enumerate(RESERVE_MURS):
        box(f'mur-reserve-{k}', x0, y0, x1, y1, bas, top, 'Coque', M_MUR)
    if top > 2.10:
        box('mur-reserve-linteau', 1321, RESERVE_PORTE[0], 1333, RESERVE_PORTE[1], max(bas, 2.10), top, 'Coque', M_MUR)
    for k, (x0, y0, x1, y1) in enumerate(ETAGE_JOINTS):
        box(f'mur-joint-{k}', x0, y0, x1, y1, bas, top, 'Coque', M_MUR)
    for k, (x0, y0, x1, y1) in enumerate(MURS_WC):
        box(f'mur-wc-{k}', x0, y0, x1, y1, bas, top, 'Coque', M_MUR)
    if top > 2.10:
        box('mur-wc-linteau', 1290, 152, 1300, 236, max(bas, 2.10), top, 'Coque', M_MUR)
    # the kitchen's partition: a low wall, steel-framed glass over it, a lintel
    cx0, cy0, cx1, cy1 = CUISINE_CLOISON
    for nom_, z0, z1, m_ in (('allege', 0.0, 0.95, M_MUR), ('linteau', 2.40, H, M_MUR)):
        z0, z1 = max(z0, bas), min(z1, top)
        if z1 - z0 > 0.002:
            box(f'cuisine-cloison-{nom_}', cx0, cy0, cx1, cy1, z0, z1, 'Coque', m_)
    z0, z1 = max(0.95, bas), min(2.40, top)
    if z1 - z0 > 0.002:
        for k, x in enumerate((cx0 + 2, (cx0 + cx1) / 2, cx1 - 2)):
            box(f'cuisine-cloison-montant-{k}', x - 2, cy0, x + 2, cy1, z0, z1, 'Vitrages', M_CADRE)
        for k, (xa, xb) in enumerate(((cx0 + 4, (cx0 + cx1) / 2 - 2), ((cx0 + cx1) / 2 + 2, cx1 - 4))):
            box(f'cuisine-cloison-verre-{k}', xa, (cy0 + cy1) / 2 - 1.2, xb, (cy0 + cy1) / 2 + 1.2, z0, z1, 'Vitrages', M_VERRE)
    for k, (x0, y0, x1, y1) in enumerate(BANDE_EST):
        box(f'mur-est-{k}', x0, y0, x1, y1, bas, top, 'Coque', M_MUR)
    # ---- columns, on the ground floor's: the one standing in the void goes down through the slab's level to meet its
    #      ground floor part (cut under the slab, dessous)
    for c in DATA['poteaux']:
        cx, cy, r = POTEAUX.get(c['id'], (c['cx'], c['cy'], c['r']))
        z0 = -DALLE - 0.002 if (bas == 0.0 and dans((cx, cy), VIDE)) else bas
        cylinder(f"poteau-{c['id']}", cx, cy, r, z0, top, 'Coque', M_POTEAU)

    # ---- facades: between steel mullions (measured on the plan), plain glass on the shell, glass blocks at step 2
    #      (as floor1: the blocks below the map cut, a plain see-through pane above it)
    def facade(name, x, montants, ep=4.5):
        if ELEMENTS and bas == 0.0:
            ep = 5.0
            paves(name, 'y', x, [(y0 + 3, y1 - 3) for y0, y1 in zip(montants, montants[1:])], bas, top, ep=ep)
        else:
            for k, (y0, y1) in enumerate(zip(montants, montants[1:])):
                box(f'{name}-verre-{k}', x - 1.2, y0, x + 1.2, y1, bas, top, 'Vitrages', M_VERRE)
        m_bas = max(bas, 0.06) if ELEMENTS else bas
        m_top = min(top, H - 0.08)                       # (26/11) the mullions stop under the head rail
        for k, y in enumerate(montants):
            if m_top > m_bas:
                box(f'{name}-montant-{k}', x - ep, y - 3, x + ep, y + 3, m_bas, m_top, 'Vitrages', M_CADRE)
        if bas == 0.0:
            box(f'{name}-seuil', x - ep, montants[0], x + ep, montants[-1], 0.0, 0.06, 'Vitrages', M_CADRE)
        if top > H - 0.08:                               # the head rail, as floor1's imposte
            box(f'{name}-tete', x - ep, montants[0] - 3, x + ep, montants[-1] + 3, max(bas, H - 0.08), top, 'Vitrages', M_CADRE)
    facade('facade-gauche', 391, [143, 281.5, 421, 560, 656, 748])        # 26/11: the one layer, over floor1's
    facade('facade-ouest', 224, FACADE_OUEST)                              # 26/11: over the void, as floor1's
    # (26/11) at the columns, the end mullions stop on the column's nearest point, a cheek fills the rest (joue)
    C843, C989 = POTEAUX[843], POTEAUX[989]
    fa, fb0 = face_colonne(1445.5, 1455.5, C843, 1), face_colonne(1445.5, 1455.5, C843, -1)
    fb1, fd0 = face_colonne(1445.5, 1455.5, C989, 1), face_colonne(1445.5, 1455.5, C989, -1)
    facade('facade-droite-a', 1450.5, [637, fa - 3])
    # (26/11) one run from column to column: the plan's gap at y 1094 - 1169, hidden behind the outer band, closed
    facade('facade-droite-b', 1450.5, [fb0 + 3, 972, 1094, 1169, 1263.5, 1360, fb1 - 3])
    facade('facade-droite-d', 1450.5, [fd0 + 3, 1692, 1822.5, 1952, 2082.5, 2210, 2302, 2394])   # on to the corner pier
    for k, (yf, col, s_) in enumerate(((fa, C843, 1), (fb0, C843, -1), (fb1, C989, 1), (fd0, C989, -1))):
        joue(f'facade-droite-joue-{k}', 1445.5, 1455.5, yf, col, s_, bas, top, 'Vitrages', M_CADRE)

    # the street facade over the entry (26/11, where the plan had a blind wall): glass blocks from the island's side
    # wall to the corner pier, the light of the entry's double height and of the ivy
    def facade_x(name, y, montants, ep=5.0):
        if ELEMENTS and bas == 0.0:
            paves(name, 'x', y, [(x0 + 3, x1 - 3) for x0, x1 in zip(montants, montants[1:])], bas, top, ep=ep)
        else:
            for k, (x0, x1) in enumerate(zip(montants, montants[1:])):
                box(f'{name}-verre-{k}', x0, y - 1.2, x1, y + 1.2, bas, top, 'Vitrages', M_VERRE)
        m_bas = max(bas, 0.06) if ELEMENTS else bas
        m_top = min(top, H - 0.08)
        for k, x in enumerate(montants):
            if m_top > m_bas:
                box(f'{name}-montant-{k}', x - 3, y - ep, x + 3, y + ep, m_bas, m_top, 'Vitrages', M_CADRE)
        if bas == 0.0:
            box(f'{name}-seuil', montants[0], y - ep, montants[-1], y + ep, 0.0, 0.06, 'Vitrages', M_CADRE)
        if top > H - 0.08:
            box(f'{name}-tete', montants[0] - 3, y - ep, montants[-1] + 3, y + ep, max(bas, H - 0.08), top, 'Vitrages', M_CADRE)
    facade_x('facade-sud', 2408, [583, 720.5, 861, 964.5, 1068, 1183.75, 1299.5, 1371, 1442.5])

    # ---- the parapets: one design everywhere (25/11), a steel shoe (5 cm, up to 8 cm), 2 cm of glass, a steel cap
    #      (4 cm) at 1.06 m; one continuous line from the void's corner round to the stair's arrival, another from
    #      the arrival along the rock garden's opening
    if bas < 1.06:
        # (26/11) the glass runs the whole edge of the void, along the ledge too: on its run the ledge (step 2) is the
        # parapet's cap, the handrail takes over where it ends
        bord = [(459.5, 1173.5), (1012, 1173.5)] + GARDE_CORPS[1:]
        for nom, pts in (('garde-corps-vide', bord), ('garde-corps-jardin', GARDE_CORPS_JARDIN)):
            chemin = [P(x, y) for x, y in pts]             # swept as one piece: smooth joints along the curves
            for suffixe, demi, z0, z1, m in (('-sabot', 0.025, 0.0, 0.08, M_CADRE), ('', 0.01, 0.08, 1.02, M_VERRE),
                                             ('-main-courante', 0.02, 1.02, 1.06, M_CADRE)):
                z0, z1 = max(bas, z0), min(top, z1)
                if ELEMENTS and nom == 'garde-corps-vide' and suffixe == '-main-courante':
                    chemin = [P(TABLETTE_FIN, 1173.5)] + [P(x, y) for x, y in pts if x > TABLETTE_FIN + 2]
                if z1 - z0 > 0.002:
                    sweep(nom + suffixe, chemin, [(-demi, z0, False), (demi, z0, False), (demi, z1, False), (-demi, z1, False)],
                          'Vitrages', m)

    # ---- the two half drums of the booths on the right (open to the room, the round side against the facade)
    for k, cy in enumerate((770, 1031)):
        cx = DEMI_CX
        zt = min(2.2, top)
        if bas < zt:
            ring(f'demi-tambour-{k}', cx, cy, 125, 110, -90, 90, bas, zt, 'Tambours', M_TAMBOUR)
            box(f'demi-tambour-{k}-retour-a', cx - 17.5, cy - 125, cx, cy - 110, bas, zt, 'Tambours', M_TAMBOUR)
            box(f'demi-tambour-{k}-retour-b', cx - 17.5, cy + 110, cx, cy + 125, bas, zt, 'Tambours', M_TAMBOUR)
        if bas < zt and k == 0:                        # (26/11) between the two drums' returns: no slit
            box('demi-tambours-joint', cx - 17.5, 895, cx, 906, bas, zt, 'Tambours', M_TAMBOUR)

    # ---- (26/11) the plan's stair up led to a floor this restaurant does not have: it is gone; behind the omakase
    #      bar's back panel its place is the bar's storeroom (reserve, step 2)

    # ---- the top of the spiral stair, coming up from the ground floor through its opening (floor1.py: 19 risers of
    #      H_RDC/19, 21 deg each from -55.5 deg; the last one lands at -18 deg, the DN mark of the plan). At step 2 the
    #      detailed stair of floor1 replaces it (escalier_detail)
    if bas == 0.0 and not ELEMENTS:
        rise = H_RDC / 19
        for k in range(19):
            z = rise * (k + 1) - H_RDC
            if z < -1.0:                         # the treads just under the floor: the stair reads as going down
                continue
            ring(f'marche-{k:02d}', HX, HY, 180, 40, -55.5 + k * 21, -55.5 + (k + 1) * 21 + 1.5, z - 0.05, min(z, -0.002),
                 'Escalier', M_MARCHE, seg=120)
        cylinder('fut', HX, HY, 40, -1.0, min(top, 1.1), 'Escalier', M_MARCHE)


def build(cut, bas=0.0):
    top = H if cut is None else cut
    if bas == 0.0:
        build_plan_image()
        build_dalle()
    build_coque(top, bas)
    for o in list(bpy.data.objects):
        if o.type == 'CURVE':
            to_mesh(o)


# ---------------------------------------------------------------- step 2: the fixed elements
# Built at full height as closed meshes (world metres, identity transforms); the map styles cut them afterwards at
# the plan height (separer), as on floor1.

# ---- the omakase bar (plan zone 3; photos 11 and 12: a grid of open cubbies over the back counter, a dark counter
#      with high stools). Between the end walls of the plan (x 603 - 1093 at the back, 584 - 1124 in front):
#      the back unit (base cabinet, worktop at 0.90 m, a full-height back panel, the cubbies for the bottles from
#      1.25 to 2.35 m: 24 bays, 3 rows, as the 24 slots of the plan); the bartenders' counter (the steel band of the
#      plan, at 0.90 m) and the guests' top at 1.08 m, as floor1's bar
def bar_omakase():
    x0, x1 = 603, 1093
    bm = bmesh.new()
    bm_box(bm, x0 + 6, 266, x1 - 6, 324, 0.0, 0.10)       # recessed plinth
    bm_box(bm, x0, 262.4, x1, 330, 0.10, 0.86)            # base cabinet
    mesh_obj('omakase-arriere', bm, 'Bar', M_MEUBLE)
    bm = bmesh.new()
    bm_box(bm, x0, 262.4, x1, 330, 0.86, 0.90)            # worktop
    mesh_obj('omakase-arriere-plan', bm, 'Bar', M_COMPTOIR)
    bm = bmesh.new()
    bm_box(bm, x0, 257, x1, 262.4, 0.0, H - 0.002)        # the back panel, floor to ceiling
    mesh_obj('omakase-fond', bm, 'Bar', M_MEUBLE)
    # the cubbies: 4 shelves, 25 uprights between them (2 cm boards, 0.30 m deep), no board through another
    bm = bmesh.new()
    zs = [1.25 + (2.35 - 1.25) * r / 3 for r in range(4)]
    e = 0.01 / PX
    for z in zs:
        bm_box(bm, x0, 262.4, x1, 298, z - 0.01, z + 0.01)
    for k in range(25):
        x = x0 + e + (x1 - x0 - 2 * e) * k / 24
        for za, zb in zip(zs, zs[1:]):
            bm_box(bm, x - e, 262.4, x + e, 298, za + 0.01, zb - 0.01)
    mesh_obj('omakase-casiers', bm, 'Bar', M_MEUBLE)
    # the counters: one L-shaped body (the bartenders' side stops at the end wall, x 1124), a recessed plinth, and as
    # on floor1's bar the upstand under the guests' top on the body (no two faces of the body on top of each other)
    bm = bmesh.new()
    prisme(bm, [(590, 453), (1118, 453), (1118, 524), (1171, 524), (1171, 574), (590, 574)], 0.0, 0.10)
    prisme(bm, [(584, 447), (1124, 447), (1124, 518), (1177, 518), (1177, 580), (584, 580)], 0.10, 0.86)
    bm_box(bm, 584, 518, 1177, 580, 0.86, 1.03)
    mesh_obj('omakase-comptoir', bm, 'Bar', M_MEUBLE)
    bm = bmesh.new()
    bm_box(bm, 584, 447, 1124, 518, 0.86, 0.90)           # the bartenders' steel worktop
    mesh_obj('omakase-plan-chef', bm, 'Bar', M_COMPTOIR)
    bm = bmesh.new()
    bm_box(bm, 584, 518, 1177, 584, 1.03, 1.08)           # the guests' top in hinoki, a small overhang on their side
    mesh_obj('omakase-plateaux', bm, 'Bar', M_BOIS)
    # (26/11 evening) dressed: the counter's front in vertical oak slats, a steel foot rail, glass neta cases on the
    # guests' top by the chef, bottles in half the cubbies, a panel closing the back unit's end
    bm = bmesh.new()
    x = 586.0
    while x < 1175:                                       # slats on the front (y 580 - 583)
        bm_box(bm, x, 580, x + 2.2, 583, 0.12, 1.02); x += 5.0
    y = 520.0
    while y < 578:                                        # and on the return's end (x 1177 - 1180)
        bm_box(bm, 1177, y, 1180, y + 2.2, 0.12, 1.02); y += 5.0
    mesh_obj('omakase-lames', bm, 'Bar', M_BOIS)
    bm = bmesh.new()
    for x in (600, 760, 920, 1080, 1165):                 # the foot rail on its brackets
        bm_box(bm, x - 1, 583, x + 1, 588, 0.20, 0.23)
    bm_box(bm, 595, 586, 1170, 589, 0.20, 0.23)
    mesh_obj('omakase-repose-pieds', bm, 'Bar', M_ACIER)
    bm = bmesh.new()
    vb = bmesh.new()
    for xa, xb in ((612, 762), (776, 926), (940, 1090)):  # the neta cases: a steel base and top frame, glass between
        bm_box(bm, xa, 519, xb, 537, 1.08, 1.095)
        bm_box(bm, xa, 519, xb, 537, 1.285, 1.30)
        vb_ = bm_box(vb, xa + 1, 520, xb - 1, 536, 1.095, 1.285)
    mesh_obj('omakase-vitrines-cadre', bm, 'Bar', M_ACIER)
    mesh_obj('omakase-vitrines', vb, 'Bar', M_VERRE)
    bm = bmesh.new()
    rnd = random.Random(5)
    for k in range(24):
        xc = x0 + (x1 - x0) * (k + 0.5) / 24
        for za, zb in zip(zs, zs[1:]):
            if rnd.random() < 0.55:
                c = Vector((xc + rnd.uniform(-2, 2), 280))
                h = min(zb - za - 0.06, rnd.uniform(0.24, 0.30))
                r = rnd.uniform(0.032, 0.040) / PX
                pts = [c + Vector((math.cos(a), math.sin(a))) * r for a in (math.tau * i / 8 for i in range(8))]
                prisme(bm, [(p_.x, p_.y) for p_ in pts], za + 0.011, za + 0.011 + h * 0.65)
                pts = [c + Vector((math.cos(a), math.sin(a))) * r * 0.35 for a in (math.tau * i / 8 for i in range(8))]
                prisme(bm, [(p_.x, p_.y) for p_ in pts], za + 0.011 + h * 0.65, za + 0.011 + h)
    mesh_obj('omakase-bouteilles', bm, 'Bar', M_COMPTOIR)
    bm = bmesh.new(); bm_box(bm, x1, 257, x1 + 6, 330, 0.0, H - 0.002)
    mesh_obj('omakase-joue', bm, 'Bar', M_MEUBLE)


# ---- the banquettes of the two half drums (as floor1's booths, photos 17, 20, 23): along the shell from one return
#      to the other, a plinth, the seat cushion with a rounded front, three rolls for the back, the lava stone band
def chemin_demi(cx, cy, r, x_bout, seg=40):
    pts = [P(x_bout, cy - r)]
    for k in range(seg + 1):
        a = math.radians(-90 + 180 * k / seg)
        pts.append(P(cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts + [P(x_bout, cy + r)]


def banquettes():
    base = [(0.005, 0.0, False), (0.36, 0.0, False), (0.36, 0.08, False), (0.42, 0.08, False), (0.42, 0.40, False),
            (0.09, 0.40, False), (0.09, 0.98, False), (0.005, 0.98, False)]
    coussin = [(0.09, 0.401, False), (0.42, 0.401, True)] + arrondi(0.42, 0.441, 0.04, 0.04, -90, 90, 8)[1:-1] + \
              [(0.42, 0.481, False), (0.09, 0.481, False)]
    for k, cy in enumerate((770, 1031)):
        cx = DEMI_CX
        ch = chemin_demi(cx, cy, 110, cx - 16.5)
        c = P(cx, cy)
        sweep(f'banquette-demi-{k}-assise', ch, base, 'Banquettes', M_BANQUETTE, ref=c)
        sweep(f'banquette-demi-{k}-coussin', ch, coussin, 'Banquettes', M_BANQUETTE, ref=c)
        for i, z in enumerate((0.56, 0.715, 0.87)):
            sweep(f'banquette-demi-{k}-boudin-{i}', ch, arrondi(0.168, z, 0.07, 0.075, 0, 360, 20)[:-1],
                  'Banquettes', M_BANQUETTE, ref=c)
        sweep(f'banquette-demi-{k}-pierre', ch, [(0.005, 1.0, False), (0.04, 1.0, False), (0.04, 1.46, False),
                                                 (0.005, 1.46, False)], 'Banquettes', M_PIERRE, ref=c)


# ---- the ledge over the void (plan: y 1114.6 - 1172, from the lab wall to a rounded end): a counter at the height of
#      the bar tops, its body on the void side (it is the guard there, 1.08 m), the top overhanging 0.24 m on the
#      stools' side for the knees, a recessed plinth
TABLETTE_FIN = 1019.25                   # where the ledge's rounded end stops, on the parapet's line


def tablette_vide():
    """The ledge over the void (26/11, reworked: it did not go with the glass parapet): one with the parapet now. The
    glass runs under it, its oak top (0.30 m deep, rounded end) is the parapet's cap at 1.02 - 1.08 m, carried on the
    room side by slender steel legs, with a foot rail between them for the stools; the handrail starts at its end."""
    yv, prof = 1173.5, 36                               # the glass's line; the top's depth (0.30 m)
    yf = yv - prof
    dessus = [(459.5, yf), (1000, yf)] + arc(1000, yf + 19.25, 19.25, -90, 90, 12)[1:] + [(459.5, yv + 2.5)]
    bm = bmesh.new()
    prisme(bm, dessus, 1.02, 1.08)
    mesh_obj('tablette-vide-plateau', bm, 'Bar', M_BOIS)
    pieds = [470 + (985 - 470) * k / 4 for k in range(5)]
    bm = bmesh.new()
    for x in pieds:                                     # legs, 2 cm square, under the top's front edge
        bm_box(bm, x - 1.2, yf + 3, x + 1.2, yf + 5.4, 0.0, 1.02)
    for xa, xb in zip(pieds, pieds[1:]):                # the foot rail, from leg to leg
        bm_box(bm, xa + 1.2, yf + 3, xb - 1.2, yf + 5.4, 0.22, 0.245)
    mesh_obj('tablette-vide', bm, 'Bar', M_ACIER)


# ---- the lab (plan zone 2), redesigned (26/11 evening: the counter looked hasty): its counter facing the room, an
#      oak body in vertical slats on a recessed plinth, a stone top with a rounded overhang; behind it, along the
#      left facade, the lab's work counter (sink, steel top) under two open shelves
def labo():
    bm = bmesh.new()
    bm_box(bm, 410, 880, 462, 1066, 0.0, 0.10)                 # the plinth, recessed
    bm_box(bm, 404, 874, 466, 1072, 0.10, 0.88)                # the body (clear of wall 936 at y 1080)
    mesh_obj('labo-comptoir', bm, 'Bar', M_MEUBLE)
    bm = bmesh.new()
    y = 876.0
    while y < 1070:                                            # slats on its face to the room (x 466 - 469)
        bm_box(bm, 466, y, 469, y + 2.2, 0.12, 0.86); y += 5.0
    x = 406.0
    while x < 465:                                             # and on its two ends
        for ya, yb in ((871, 874), (1072, 1075)):
            bm_box(bm, x, ya, x + 2.2, yb, 0.12, 0.86)
        x += 5.0
    mesh_obj('labo-lames', bm, 'Bar', M_BOIS)
    bm = bmesh.new()
    pts = [(400, 868), (466, 868)] + arc(466, 874, 6, -90, 0, 4)[1:] + [(472, 1072)] + arc(466, 1072, 6, 0, 90, 4)[1:] + \
        [(400, 1078)]
    prisme(bm, pts, 0.88, 0.92)                                # the stone top, rounded at the room's corners
    mesh_obj('labo-plan', bm, 'Bar', M_COMPTOIR)
    # the work counter along the facade's pier and the lab's wall
    bm = bmesh.new()
    bm_box(bm, 238, 866, 292, 1160, 0.0, 0.10)
    bm_box(bm, 234, 862, 296, 1164, 0.10, 0.86)
    mesh_obj('labo-arriere', bm, 'Bar', M_MEUBLE)
    bm = bmesh.new()
    bm_box(bm, 233, 860, 298, 1166, 0.86, 0.90)
    mesh_obj('labo-arriere-plan', bm, 'Bar', M_ACIER)
    bm = bmesh.new()
    bm_box(bm, 246, 960, 286, 1010, 0.894, 0.901)              # the sink's basin, dark in the steel
    mesh_obj('labo-evier', bm, 'Bar', M_COMPTOIR)
    bm = bmesh.new()
    pts = [(240 + 3 * math.cos(a), 985 + 3 * math.sin(a)) for a in (math.tau * k / 8 for k in range(8))]
    prisme(bm, pts, 0.90, 1.22)                                # the tap
    bm_box(bm, 238, 983.5, 258, 986.5, 1.19, 1.22)
    for z in (1.40, 1.78):                                     # two open shelves on the wall
        bm_box(bm, 233, 870, 262, 1156, z, z + 0.025)
    mesh_obj('labo-etageres', bm, 'Bar', M_ACIER)


# ---- curtains (the wavy lines of the plan), as floor1's: heavy drapes hung from a ceiling track, 2 cm over the floor.
#      One closes the landing of the stair up (y 287), the other the passage between the omakase bar and the lift
def rideau(name, p0, p1, amp, onde, graine):
    """A drape from p0 to p1 (plan px): folds of mean wavelength `onde` (m) and amplitude `amp` (px)."""
    a, b = Vector(p0), Vector(p1)
    L = (b - a).length * PX
    t = (b - a).normalized(); nrm = Vector((-t.y, t.x))
    rnd = random.Random(graine)
    ondes = [(1.0, 1.0), (0.45, 2.1), (0.3, 0.47)]
    phases = [rnd.uniform(0, math.tau) for _ in ondes]
    tot = sum(w for w, _ in ondes)

    def pli(u):
        return sum(w * math.sin(math.tau * u * f / onde + ph) for (w, f), ph in zip(ondes, phases)) / tot
    z0, z1 = 0.02, H - 0.07
    nu, nz = max(16, int(L / onde * 12)), 10
    e = 0.006 / PX
    bm = bmesh.new()
    faces = []
    for cote in (1, -1):
        g = []
        for j in range(nz + 1):
            z = z0 + (z1 - z0) * j / nz
            ouv = 1.25 - 0.4 * j / nz
            g.append([bm.verts.new(P(*(a + (b - a) * (i / nu) + nrm * (amp * ouv * pli(L * i / nu) + cote * e)), z))
                      for i in range(nu + 1)])
        faces.append(g)
    av, ar = faces
    for j in range(nz):
        for i in range(nu):
            bm.faces.new((av[j][i], av[j][i + 1], av[j + 1][i + 1], av[j + 1][i])).smooth = True
            bm.faces.new((ar[j][i], ar[j + 1][i], ar[j + 1][i + 1], ar[j][i + 1])).smooth = True
        for i in (0, nu):
            bm.faces.new((av[j][i], av[j + 1][i], ar[j + 1][i], ar[j][i]))
    for j in (0, nz):
        for i in range(nu):
            bm.faces.new((av[j][i], ar[j][i], ar[j][i + 1], av[j][i + 1]))
    o = mesh_obj(name, bm, 'Rideaux', M_RIDEAU)
    coll('Traits-fins').objects.link(o)


def tringle(name, p0, p1):
    """The ceiling track, 3 cm wide, just above the head of the curtain (any direction)."""
    (x0, y0), (x1, y1) = p0, p1
    L = math.hypot(x1 - x0, y1 - y0)
    w = 0.015 / PX
    nx, ny = -(y1 - y0) / L * w, (x1 - x0) / L * w
    bm = bmesh.new()
    prisme(bm, [(x0 + nx, y0 + ny), (x1 + nx, y1 + ny), (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)], H - 0.06, H - 0.025)
    mesh_obj(name, bm, 'Rideaux', M_CADRE)


def rideaux():
    rideau('rideau-passage', (1188, 560.2), (1292, 608.5), amp=4.0, onde=0.16, graine=13)   # clear of the bar's end
    tringle('tringle-passage', (1185, 558.8), (1295, 610))


# ---- the spiral stair of floor1 (photos 2, 3, 4, 28, 30), built as there and moved down by the height of the ground
#      floor: its last treads in the opening of the slab, the solid parapet up to the mezzanine floor, the twisted
#      mirror sculpture, which goes on up to the mezzanine's ceiling. Kept from 1 m under the floor (as step 1)
def escalier_detail():
    cx, cy, r0, r1 = 1082, 2172, 40, 179.5
    n, pas_a, rise, a0, T, m = 19, 21.0, H_RDC / 19, -55.5, 0.30, 6
    rr = [r0 + (r1 - r0) * i / 6 for i in range(7)]

    def V(r, a, z):
        return P(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)), z - H_RDC)

    def nez(a):
        return rise * ((a - a0) / pas_a + 1)

    def zs(a):
        return max(0.0, nez(a) - T)
    bm = bmesh.new()
    last = None
    for k in range(n - 1):
        zt = rise * (k + 1)
        for j in range(m + 1):
            a = a0 + pas_a * (k + j / m)
            if j == 0 and last is not None:
                c = dict(B=last['B'], M=last['T'], T=(bm.verts.new(V(r0, a, zt)), bm.verts.new(V(r1, a, zt))))
                bm.faces.new((c['M'][0], c['M'][1], c['T'][1], c['T'][0]))
            else:
                zb = zs(a)
                c = dict(B=[bm.verts.new(V(r, a, zb)) for r in rr], M=None,
                         T=(bm.verts.new(V(r0, a, zt)), bm.verts.new(V(r1, a, zt))))
                if last is None:
                    bm.faces.new(c['B'] + [c['T'][1], c['T'][0]])
                else:
                    for s, b_ in ((0, 0), (1, -1)):
                        f = [last['B'][b_], c['B'][b_], c['T'][s], last['T'][s]] + ([last['M'][s]] if last['M'] else [])
                        bm.faces.new(f).smooth = True
                    bm.faces.new((last['T'][0], c['T'][0], c['T'][1], last['T'][1]))
                    for i in range(len(rr) - 1):
                        bm.faces.new((last['B'][i], last['B'][i + 1], c['B'][i + 1], c['B'][i])).smooth = True
            last = c
    bm.faces.new(last['B'] + [last['T'][1], last['T'][0]])
    marches = mesh_obj('escalier-marches', bm, 'Escalier', M_MARCHE)

    bm = bmesh.new()
    a_fin, seg = a0 + pas_a * (n - 1), 180
    rows = []
    for i in range(seg + 1):
        a = a0 + (a_fin - a0) * i / seg
        zb, zt = zs(a), min(nez(a) + 0.90, H_RDC)
        rows.append([bm.verts.new(V(r, a, z)) for r, z in ((r1 + 0.5, zb), (r1 + 0.5, zt), (r1 + 5.5, zt), (r1 + 5.5, zb))])
    for i in range(seg):
        A, B = rows[i], rows[i + 1]
        for q in range(4):
            w = (q + 1) % 4
            bm.faces.new((A[q], B[q], B[w], A[w])).smooth = q in (0, 2)
    bm.faces.new(rows[0]); bm.faces.new(list(reversed(rows[-1])))
    garde = mesh_obj('escalier-garde-corps', bm, 'Escalier', M_MARCHE)

    bm = bmesh.new()
    sa, sz = 72, 96
    grid = []
    for iz in range(sz + 1):
        z = (H_RDC + H - 0.002) * iz / sz                  # the same twist as floor1, carried on to this ceiling
        grid.append([bm.verts.new(V(30 + 7 * math.sin(2 * a + 2.4 * z + 0.9 * math.sin(3 * a - 1.3 * z)),
                                    math.degrees(a), z)) for a in (2 * math.pi * ia / sa for ia in range(sa))])
    for iz in range(sz):
        for ia in range(sa):
            ja = (ia + 1) % sa
            bm.faces.new((grid[iz][ia], grid[iz][ja], grid[iz + 1][ja], grid[iz + 1][ia])).smooth = True
    bm.faces.new(list(reversed(grid[0]))); bm.faces.new(grid[-1])
    sculpture = mesh_obj('sculpture-miroir', bm, 'Escalier', M_MIROIR)
    for o in (marches, garde, sculpture):
        couper(o, -1.0, 'haut')
    # (26/11 evening) the landing, the 19th step: the last tread stopped 18 cm under the floor, at the edge of the
    # opening, and the stair gave onto the void. The landing is at the floor's level, in the slab's thickness, from
    # the last riser to the rock garden's parapet, which closes its side on the void; one steps off it to the east
    ring('escalier-palier', cx, cy, R_ESC, r0, a0 + pas_a * (n - 1), math.degrees(A_PALIER) % 360, -DALLE, 0.0,
         'Escalier', M_MARCHE, seg=360)


# ---------------------------------------------------------------- the void over the drums: the three columns
# On the real place (photo 33) the drums of the ground floor read on the whole double height. Of the four prototypes
# (25/11: the cables, the columns, the halos, a lantern for the block), the user chose the three columns (V2): each
# drum rises from its ring to the mezzanine's ceiling. The others are out of the script (their renders stay in
# rendus/14-etage-prototypes-vide/).
TAMBOURS_VIDE = [(407.0, 1312.7), (408.1, 1718.9), (405.5, 2022.4)]   # the drums of floor1 under the void
M_LUMIERE = mat('lumiere', (0.96, 0.93, 0.86), 0.4)


def fil(bm, a, b, r=0.004, n=6):
    """A thin cylinder (a cable) between two world points."""
    d = b - a
    t = d.normalized(); u = t.orthogonal().normalized(); v = t.cross(u)
    ra = [bm.verts.new(a + (u * math.cos(math.tau * k / n) + v * math.sin(math.tau * k / n)) * r) for k in range(n)]
    rb = [bm.verts.new(b + (u * math.cos(math.tau * k / n) + v * math.sin(math.tau * k / n)) * r) for k in range(n)]
    for k in range(n):
        j = (k + 1) % n
        bm.faces.new((ra[k], ra[j], rb[j], rb[k]))
    bm.faces.new(ra[::-1]); bm.faces.new(rb)


def vide_colonnes():
    """Each drum rises from its ring (3.0 m over the ground floor) to the mezzanine's ceiling, a tube of six staves
    with slits of light between them (photo 33), open at the top: seen from above the booths still show."""
    for k, (cx, cy) in enumerate(TAMBOURS_VIDE):
        for i in range(6):
            a0 = 30 + 60 * i + 1.6
            ring(f'colonne-{k}-{i}', cx, cy, 139, 127, a0, a0 + 60 - 3.2, -0.35, H - 0.002, 'Vide', M_TAMBOUR, seg=240)
        bm = bmesh.new()
        for i in range(6):
            a = math.radians(30 + 60 * i)
            x, y = cx + 133 * math.cos(a), cy + 133 * math.sin(a)
            # the light in the slit, set back in it
            lo = P(x, y, -0.20); hi = P(x, y, H - 0.15)
            fil(bm, lo, hi, r=0.012, n=8)
        mesh_obj(f'colonne-{k}-lumieres', bm, 'Vide', M_LUMIERE)


# ---------------------------------------------------------------- the island over the entry: the ivy
# The block of the plan is removed (25/11): its footprint, the roof of the entry box of the ground floor, is an island
# (2.2 x 4.2 m) with the void on three sides and no way in from the mezzanine. After four plant prototypes, the user
# asked for ivy, from a model they supplied (outils/assets/ivy-for-walls/, third-party, not in the repository).
# Analysed (outils/blender/lierre_feuilles.py): a wall patch of 430,000 faces, 40,000 leaves that are flat octagons,
# 6.6 cm long once at real size (the model is at 1/10; 4 to 8.5 cm), on ribbon stems. What is kept: the size and the
# spread of the leaves, their density, stems carrying alternate leaves. What is modelled again: a real ivy leaf (five
# pointed lobes, a heart-shaped base, a slight fold along the midrib), and the plant grown on the island itself:
# runners from a low planter cover the roof, go over its rim and hang down into the double height on the three sides,
# kept off the walls of the entry box below (y 1898, x 599) and 2.2 m over the ground floor.
M_FEUILLE = mat('feuillage', (0.16, 0.24, 0.12), 0.7)
M_TERRE = mat('terre', (0.10, 0.08, 0.06), 1.0)
M_ECORCE = mat('ecorce', (0.15, 0.11, 0.08), 0.8)
ILE = (601, 1896, 861, 2403)          # the planted island: the block's footprint, to the street facade (wall 1068)
LIERRE_TAILLE = (0.045, 0.085)        # leaf lengths (m), the model's 10th - 90th percentiles at real size


LEGER = bool(ARGS.get('export'))       # the map's model: the same ivy, lighter (8-point leaves, 4-sided stems)


def feuille_lierre(variante):
    """An ivy leaf in its own frame (base at the origin, along +y, length 1, face +z): five lobes, a heart-shaped
    base, the halves folded a little along the midrib. Three variants: lobes more or less deep."""
    p_ = (0.0, 0.10, 0.20)[variante]
    droite = [(0.0, 0.06), (0.16, -0.03), (0.31, 0.06), (0.30 - p_ * 0.3, 0.22), (0.52, 0.40 + p_ * 0.1),
              (0.30 - p_, 0.54), (0.20, 0.72), (0.0, 1.0)]
    if LEGER:                                   # the lobes' tips and the sinuses between them only
        droite = [(0.0, 0.06), (0.31, 0.06), (0.52, 0.40 + p_ * 0.1), (0.26 - p_, 0.58), (0.0, 1.0)]
    contour = droite + [(-x, y) for x, y in reversed(droite[1:-1])]
    def z(x, y):
        return -0.07 * abs(x) + 0.04 * (y - 0.5) ** 2           # the fold along the midrib, a slight cup
    vs = [(0.0, 0.45, z(0, 0.45) + 0.01)] + [(x, y, z(x, y)) for x, y in contour]
    n = len(contour)
    fs = [(0, 1 + k, 1 + (k + 1) % n) for k in range(n)]
    return vs, fs


FEUILLES = [feuille_lierre(k) for k in range(3)]


def tube(bm, pts, r0, r1, n=4 if LEGER else 6):
    """A stem: a tube along world points, its radius going from r0 to r1."""
    anneaux = []
    for i, p_ in enumerate(pts):
        a_, b_ = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]
        t = (b_ - a_).normalized()
        u = t.orthogonal().normalized(); v = t.cross(u)
        r = r0 + (r1 - r0) * i / max(1, len(pts) - 1)
        anneaux.append([bm.verts.new(p_ + (u * math.cos(math.tau * k / n) + v * math.sin(math.tau * k / n)) * r)
                        for k in range(n)])
    for A, B in zip(anneaux, anneaux[1:]):
        for k in range(n):
            j = (k + 1) % n
            bm.faces.new((A[k], A[j], B[j], B[k])).smooth = True
    bm.faces.new(anneaux[0][::-1]); bm.faces.new(anneaux[-1])


def poser_feuille(bm, base, y, z, taille, rnd):
    """One leaf: its base at `base`, its midrib along y, its face towards z (world vectors)."""
    y = y.normalized(); z = (z - y * z.dot(y)).normalized(); x = y.cross(z)
    vs, fs = FEUILLES[rnd.randrange(3)]
    vv = [bm.verts.new(base + (x * a + y * b + z * c) * taille) for a, b, c in vs]
    for f in fs:
        bm.faces.new([vv[i] for i in f]).smooth = True


def bac_lierre():
    """The planter of the ivy: a low rim (0.26 m) following the island, its soil at 0.24 m."""
    x0, y0, x1, y1 = ILE
    y1 -= 1                                       # clear of the street facade's wall (y 2403)
    e = 8
    bm = bmesh.new()
    bm_box(bm, x0, y0, x1, y0 + e, 0.0, 0.26); bm_box(bm, x0, y1 - e, x1, y1, 0.0, 0.26)
    bm_box(bm, x0, y0 + e, x0 + e, y1 - e, 0.0, 0.26); bm_box(bm, x1 - e, y0 + e, x1, y1 - e, 0.0, 0.26)
    mesh_obj('ile-bac', bm, 'Ile', M_MEUBLE)
    bm = bmesh.new(); bm_box(bm, x0 + e, y0 + e, x1 - e, y1 - e, 0.0, 0.24)
    mesh_obj('ile-terre', bm, 'Ile', M_TERRE)


def lierre():
    """The ivy over the island: runners on the soil, and strands over the three edges on the void."""
    x0, y0, x1, y1 = ILE
    rnd = random.Random(31)
    tiges, feuilles = bmesh.new(), bmesh.new()
    haut = Vector((0, 0, 1))

    def feuilles_le_long(pts, regard, pendante):
        """Alternate leaves every 4 - 5 cm along a stem; `regard(p)` gives the way they face; on a strand, the leaves
        over the soil and the rim lie open, those below it hang (pendante = None: decided by the height)."""
        long = 0.0; cote = 1; prochaine = rnd.uniform(0.02, 0.04)
        for a_, b_ in zip(pts, pts[1:]):
            seg = (b_ - a_).length
            t = (b_ - a_).normalized()
            while long + seg >= prochaine:
                q = a_ + t * (prochaine - long)
                pend = pendante(q) if callable(pendante) else pendante
                n = regard(q) if pend else haut
                s_ = t.cross(n).normalized() * cote
                if s_.length < 0.5:
                    s_ = Vector((-t.y, t.x, 0)).normalized() * cote
                taille = rnd.uniform(*LIERRE_TAILLE) * (1.12 if pend else 1.0)
                if pend:                            # hanging: the tips down, the faces out and a little up
                    y = (s_ * 0.55 + Vector((0, 0, -0.75)) + n * 0.35 + Vector([rnd.uniform(-0.25, 0.25) for _ in range(3)]))
                    z = n + haut * 0.35
                else:                                   # on the soil: the leaves lie open to the light
                    y = (s_ * 0.8 + t * 0.35 + haut * 0.12 + Vector([rnd.uniform(-0.3, 0.3) for _ in range(2)] + [0]))
                    pente = 0.18 if q.z > 0.275 else 0.4         # over the rim: almost flat
                    z = haut + Vector([rnd.uniform(-pente, pente) for _ in range(2)] + [0])
                base = q + s_ * 0.012 + n * (0.004 if pend else 0.008)
                poser_feuille(feuilles, base, y, z, taille, rnd)
                cote = -cote
                prochaine += rnd.uniform(0.032, 0.046) if pend else rnd.uniform(0.036, 0.05)
            long += seg

    # runners on the soil: from a dozen roots, wandering with some persistence, staying within the rim
    racines = [(x0 + 30 + (x1 - x0 - 60) * rnd.random(), y0 + 30 + (y1 - y0 - 60) * rnd.random()) for _ in range(34)]
    for rx, ry in racines:
        for _ in range(rnd.randint(6, 8)):
            ang = rnd.uniform(0, math.tau); x, y = rx, ry
            pts = [P(x, y, 0.255)]
            for i in range(rnd.randint(22, 40)):
                ang += rnd.uniform(-0.45, 0.45)
                nx_, ny_ = x + 5.4 * math.cos(ang), y + 5.4 * math.sin(ang)          # 4.5 cm steps
                if not (x0 + 14 < nx_ < x1 - 14 and y0 + 14 < ny_ < y1 - 24):
                    ang += math.pi * rnd.uniform(0.6, 1.0); continue
                x, y = nx_, ny_
                pts.append(P(x, y, 0.258 + 0.03 * abs(math.sin(i * 0.7 + rx))))
            if len(pts) > 3:
                tube(tiges, pts, 0.005, 0.002)
                feuilles_le_long(pts, lambda q: haut, False)

    # strands over the edges: from inside the rim, over it, then down, kept off the walls below
    def suite(a_, b_):                                    # irregular spacing: 5 to 15 px, in clumps
        u, out = a_, []
        while u < b_:
            out.append(u); u += rnd.choice((5, 6, 7, 9, 12, 15))
        return out
    bords = [([(x, y0) for x in suite(x0 + 16, x1 - 16)], Vector((0, 1, 0)), 'n'),      # clear of the corners' rims
             ([(x0, y) for y in suite(y0 + 16, 2224)], Vector((-1, 0, 0)), 'o'),
             ([(x1, y) for y in suite(y0 + 16, y1 - 18)], Vector((1, 0, 0)), 'e')]
    for pts_bord, sortie, cote_ in bords:
        for bx, by in pts_bord:
            dedans = P(bx, by) - sortie * rnd.uniform(0.12, 0.32)
            bord = P(bx, by)
            h_ = rnd.uniform(0.285, 0.32)                     # over the rim (0.26 m), each at its own height
            L = rnd.uniform(0.15, 1.0) ** 1.6 * 1.40           # most short, a few long (up to 1.40 m)
            ph = rnd.uniform(0, math.tau)
            ecart = 0.075 + rnd.uniform(0, 0.03)             # off the edge: clear of the walls below
            pts = [Vector((dedans.x, dedans.y, 0.255)), Vector((bord.x, bord.y, 0.0)) - sortie * 0.085 + Vector((0, 0, h_ - 0.012)),
                   Vector((bord.x, bord.y, 0.0)) - sortie * 0.03 + Vector((0, 0, h_ - 0.005)),
                   Vector((bord.x, bord.y, h_)) + sortie * 0.02,
                   Vector((bord.x, bord.y, 0.0)) + sortie * ecart * 0.85 + Vector((0, 0, h_ - 0.04))]
            n = max(3, int(L / 0.045))
            for i in range(1, n + 1):
                z = 0.27 - L * i / n
                lat = Vector((-sortie.y, sortie.x, 0)) * 0.02 * math.sin(ph + i * 0.35)
                pts.append(Vector((bord.x, bord.y, z)) + sortie * (ecart + 0.01 * math.sin(ph + i * 0.2)) + lat)
            tube(tiges, pts, 0.0045, 0.0018)
            dehors = lambda q, b=bord, s=sortie: (q - b).dot(s) > 0.005 or q.z < 0.20      # past the rim: they hang
            feuilles_le_long(pts, lambda q, s=sortie: s, dehors)
            if L > 0.5 and rnd.random() < 0.45:              # a branch, leaving the strand sideways and falling
                k0 = rnd.randint(4, max(5, len(pts) // 2))
                lat = Vector((-sortie.y, sortie.x, 0)) * rnd.choice((-1, 1))
                br = [pts[k0]]
                for i in range(1, rnd.randint(5, 14)):
                    br.append(pts[k0] + lat * 0.012 * i + sortie * 0.003 * i + Vector((0, 0, -0.04 * i)))
                tube(tiges, br, 0.0025, 0.0015)
                feuilles_le_long(br, lambda q, s=sortie: s, True)
    mesh_obj('ile-lierre-tiges', tiges, 'Ile', M_ECORCE)
    o = mesh_obj('ile-lierre-feuilles', feuilles, 'Ile', M_FEUILLE)
    coll('Traits-fins').objects.link(o)                  # thin light lines: a texture of leaves, not a scribble


def reserve():
    """The omakase bar's storeroom (26/11), behind its back panel, where the plan's stair up was: steel shelving along
    the back wall, 2.2 m high, sake and wine bottles laid on its shelves, a few crates on the floor."""
    x0, y0, x1, y1 = ESCALIER_HAUT
    xa, xb, ya, yb = 612, 1088, y0 + 1, y0 + 56         # the shelving, behind the bar's back (26/11 evening): 4 m
    bm = bmesh.new()
    for x in (xa, (xa + xb) / 2, xb - 3):                # the uprights
        bm_box(bm, x, ya, x + 3, yb, 0.0, 2.20)
    niveaux = (0.12, 0.58, 1.04, 1.50, 1.96)
    for z in niveaux:                                    # the shelves
        bm_box(bm, xa + 3, ya, xb - 3, yb, z, z + 0.025)
    mesh_obj('reserve-etageres', bm, 'Bar', M_CADRE)
    rnd = random.Random(23)
    bm = bmesh.new()
    milieu = (xa + xb) / 2
    for z in niveaux[1:]:
        x = xa + 4                                       # the left edge of the next bottle, clear of the upright
        while True:
            r = rnd.uniform(0.035, 0.045) / PX
            h = rnd.uniform(0.28, 0.34)
            if milieu - 2 * r - 1 < x < milieu + 4:      # step over the middle upright
                x = milieu + 4; continue
            if x + 2 * r > xb - 4:
                break
            for y in (ya + 14, yb - 14):                 # two rows, standing, 1 mm over the shelf
                if rnd.random() < 0.88:
                    c = Vector((x + r, y))
                    pts = [c + Vector((math.cos(a), math.sin(a))) * r for a in (math.tau * k / 8 for k in range(8))]
                    prisme(bm, [(p_.x, p_.y) for p_ in pts], z + 0.026, z + 0.026 + h * 0.62)
                    pts = [c + Vector((math.cos(a), math.sin(a))) * r * 0.35 for a in (math.tau * k / 8 for k in range(8))]
                    prisme(bm, [(p_.x, p_.y) for p_ in pts], z + 0.026 + h * 0.62, z + 0.026 + h)
            x += 2 * r + rnd.uniform(1.0, 3.0)
    mesh_obj('reserve-bouteilles', bm, 'Bar', M_COMPTOIR)
    bm = bmesh.new()
    for k, (cx_, cy_) in enumerate(((660, y0 + 80), (710, y0 + 82), (662, y0 + 80))):
        h0 = 0.0 if k < 2 else 0.30
        bm_box(bm, cx_ - 22, cy_ - 15, cx_ + 22, cy_ + 15, h0, h0 + 0.30)      # crates
    mesh_obj('reserve-caisses', bm, 'Bar', M_MEUBLE)


def reserve_est():
    """(26/11 night) The storeroom where the lift shaft was (RESERVE, 1.0 x 3.0 m inside), behind the toilets' passage:
    its oak door (closed); steel shelving 2 m high along the facade (cartons, bottles standing in two rows, jars) and a
    shorter one along the toilets' wall (napkins, paper rolls); wine cases stacked at the far end, a step stool."""
    x0, y0, x1, y1 = RESERVE
    pa, pb = RESERVE_PORTE
    rnd = random.Random(31)
    bm = bmesh.new()
    bm_box(bm, 1325, pa + 1, 1329, pb - 1, 0.01, 2.09)                        # the door
    mesh_obj('reserve-est-porte', bm, 'Bar', M_BOIS)
    bm = bmesh.new()
    for xa, xb in ((1322, 1325), (1329, 1332)):                                 # its handles, both faces
        bm_box(bm, xa, pb - 12, xb, pb - 10, 0.98, 1.00)
    e = bmesh.new()
    niveaux = (0.12, 0.55, 0.98, 1.41, 1.84)
    # the long shelving, along the facade (x 1414 - 1456), uprights at its ends and its middle
    xa, xb, ya, yb = 1414, 1456, 264, 622
    for y in (ya, (ya + yb) / 2 - 1.5, yb - 3):
        for x in (xa, xb - 3):
            bm_box(e, x, y, x + 3, y + 3, 0.0, 2.00)
    for z in niveaux:
        bm_box(e, xa, ya, xb, yb, z, z + 0.02)
    # the short one, along the toilets' wall (y 262 - 300), from the door's wall to the long shelving
    xc, xd, yc, yd = 1336, 1410, 262, 300
    for x in (xc, xd - 3):
        for y in (yc, yd - 3):
            bm_box(e, x, y, x + 3, y + 3, 0.0, 1.60)
    for z in niveaux[:4]:
        bm_box(e, xc, yc, xd, yd, z, z + 0.02)
    mesh_obj('reserve-est-etageres', e, 'Bar', M_CADRE)
    cartons = bmesh.new()
    bouteilles = bmesh.new()
    # on the long shelving: cartons on the bottom and fourth shelves, two rows of bottles on the others (all inset
    # from the uprights, which stand at the shelves' edges)
    for k, z in enumerate(niveaux[:-1]):
        y = ya + 4.0
        while y < yb - 8:
            if k in (0, 3):
                l_ = rnd.uniform(28, 46)
                if y + l_ > yb - 4:
                    break
                bm_box(cartons, xa + 4, y, xb - 4, y + l_, z + 0.02, z + 0.02 + rnd.uniform(0.22, 0.36))
                y += l_ + rnd.uniform(1.5, 4)
            else:
                r = rnd.uniform(0.035, 0.042) / PX
                if y + 2 * r > yb - 4:
                    break
                h = rnd.uniform(0.27, 0.32)
                for x in (xa + 12, xb - 12):
                    if rnd.random() < 0.9:
                        c = Vector((x, y + r))
                        pts = [c + Vector((math.cos(a), math.sin(a))) * r for a in (math.tau * i / 8 for i in range(8))]
                        prisme(bouteilles, [(p_.x, p_.y) for p_ in pts], z + 0.021, z + 0.021 + h * 0.62)
                        pts = [c + Vector((math.cos(a), math.sin(a))) * r * 0.35 for a in (math.tau * i / 8 for i in range(8))]
                        prisme(bouteilles, [(p_.x, p_.y) for p_ in pts], z + 0.021 + h * 0.62, z + 0.021 + h)
                y += 2 * r + rnd.uniform(1.0, 2.5)
    # on the short one: packs of napkins and paper rolls
    for z in niveaux[:4]:
        x = xc + 5.0
        while x < xd - 20:
            l_ = rnd.uniform(14, 22)
            bm_box(cartons, x, yc + 4, x + l_, yd - 4, z + 0.02, z + 0.02 + rnd.uniform(0.12, 0.25))
            x += l_ + rnd.uniform(2, 5)
    # wine cases stacked at the far end, a step stool
    for k, (cx_, cy_, h0) in enumerate(((1356, 598, 0.0), (1390, 598, 0.0), (1360, 598, 0.18))):
        bm_box(cartons, cx_ - 16, cy_ - 22, cx_ + 16, cy_ + 22, h0, h0 + 0.18)
    mesh_obj('reserve-est-cartons', cartons, 'Bar', M_MEUBLE)
    mesh_obj('reserve-est-bouteilles', bouteilles, 'Bar', M_COMPTOIR)
    mesh_obj('reserve-est-poignees', bm, 'Bar', M_ACIER)
    bm = bmesh.new()                                                              # the step stool
    bm_box(bm, 1345, 520, 1385, 548, 0.0, 0.22)
    bm_box(bm, 1345, 534, 1385, 548, 0.22, 0.44)
    mesh_obj('reserve-est-escabeau', bm, 'Bar', M_MEUBLE)


def cuisine():
    """The kitchen corner (26/11 evening), at the omakase bar's west end, behind its glazed partition: the cooking
    line along the back wall under its hood (two induction plates, a plancha, a stockpot), the prep counter and its
    sink along the left facade, a fridge column; open on the chef's aisle and the storeroom."""
    bm = bmesh.new()
    bm_box(bm, 408, 145, 596, 190, 0.0, 0.10)                  # the cooking line, on a recessed plinth
    bm_box(bm, 404, 141, 596, 196, 0.10, 0.88)
    bm_box(bm, 400, 214, 452, 352, 0.10, 0.88)                 # the prep counter
    bm_box(bm, 404, 218, 452, 348, 0.0, 0.10)
    mesh_obj('cuisine-meubles', bm, 'Bar', M_ACIER)
    bm = bmesh.new()
    bm_box(bm, 402, 141, 598, 198, 0.88, 0.92)                 # the steel tops
    bm_box(bm, 398, 212, 454, 354, 0.88, 0.92)
    bm_box(bm, 400, 141, 598, 144, 0.92, 1.20)                 # the upstand along the back wall
    mesh_obj('cuisine-plans', bm, 'Bar', M_ACIER)
    bm = bmesh.new()
    for xa in (420, 476):                                      # two induction plates
        bm_box(bm, xa, 152, xa + 46, 188, 0.92, 0.926)
    bm_box(bm, 412, 250, 446, 300, 0.914, 0.921)               # the sink's basin
    mesh_obj('cuisine-plaques', bm, 'Bar', M_COMPTOIR)
    bm = bmesh.new()
    bm_box(bm, 534, 148, 590, 190, 0.92, 0.955)                # the plancha
    pts = [(443 + 13 * math.cos(a), 170 + 13 * math.sin(a)) for a in (math.tau * k / 16 for k in range(16))]
    prisme(bm, pts, 0.926, 1.14)                               # a stockpot on the first plate
    pts = [(402 + 3 * math.cos(a), 275 + 3 * math.sin(a)) for a in (math.tau * k / 8 for k in range(8))]
    prisme(bm, pts, 0.92, 1.24)                                # the tap
    bm_box(bm, 400, 273.5, 420, 276.5, 1.21, 1.24)
    bm_box(bm, 400, 358, 452, 430, 0.0, 2.00)                  # the fridge column
    bm_box(bm, 452, 368, 455, 370, 0.95, 1.65)                 # its handle
    bm_box(bm, 404, 141, 596, 212, 1.95, 2.40)                 # the hood
    bm_box(bm, 480, 141, 520, 166, 2.40, H - 0.002)            # its duct to the ceiling
    mesh_obj('cuisine-equipements', bm, 'Bar', M_ACIER)
    bm = bmesh.new()
    bm_box(bm, 397, 216, 410, 346, 1.45, 1.475)                # a shelf over the prep counter, its jars
    mesh_obj('cuisine-etagere', bm, 'Bar', M_ACIER)
    bm = bmesh.new()
    for k in range(6):
        c = (403.5, 228 + 21 * k)
        pts = [(c[0] + 4.5 * math.cos(a), c[1] + 4.5 * math.sin(a)) for a in (math.tau * i / 10 for i in range(10))]
        prisme(bm, pts, 1.476, 1.476 + (0.14 if k % 2 else 0.18))
    mesh_obj('cuisine-bocaux', bm, 'Bar', M_VERRE)


def wc():
    """The 1st floor's toilets (plan zone 5), behind the curtain of the passage: their door (closed), a wall-hung
    bowl against the right wall, a basin and its mirror on the back wall."""
    bm = bmesh.new()
    bm_box(bm, 1293, 153, 1297, 235, 0.01, 2.09)               # the door leaf
    mesh_obj('wc-porte', bm, 'Mobilier', M_MEUBLE)
    bm = bmesh.new()
    bm_box(bm, 1288, 220, 1290, 230, 1.00, 1.02)               # the handle and its rose, room side
    bm_box(bm, 1290, 222, 1293, 228, 0.99, 1.03)
    mesh_obj('wc-poignee', bm, 'Mobilier', M_ACIER)
    bm = bmesh.new()
    bm_box(bm, 1376, 174, 1427, 214, 0.36, 0.42)               # the bowl, wall hung
    bm_box(bm, 1392, 178, 1427, 210, 0.20, 0.36)
    bm_box(bm, 1330, 141, 1372, 168, 0.80, 0.88)               # the basin on the back wall
    mesh_obj('wc-sanitaires', bm, 'Mobilier', M_MIROIR)
    bm = bmesh.new()
    bm_box(bm, 1328, 140, 1374, 141, 1.05, 1.75)               # the mirror
    mesh_obj('wc-miroir', bm, 'Mobilier', M_MIROIR)


def build_elements():
    """Step 2: the fixed elements, at full height, the three columns over the drums, and the island's prototype, if
    any. Returns the new objects."""
    for c in ('Bar', 'Banquettes', 'Rideaux', 'Vide', 'Ile'):
        coll(c)
    avant = set(bpy.data.objects)
    bar_omakase(); banquettes(); tablette_vide(); labo(); rideaux(); escalier_detail(); reserve(); cuisine(); wc()
    reserve_est()
    vide_colonnes()
    bac_lierre(); lierre()
    return [o for o in bpy.data.objects if o not in avant]


# ---- the ground floor under the mezzanine (25/11: the whole building): floor1's whole model (the map's, uncut, with
#      its furniture), 3.35 m down, stopped under the slab, its stair 1 m under the mezzanine's floor where this
#      floor's stair takes over. Each piece keeps its material (the same names as here, so the same whites) and its
#      place in the line sets: the ground floor is drawn as the mezzanine is, the storey the mezzanine stands on.
SOUS_DALLE = -DALLE - 0.002


def dessous(cut=None, m_ghost=None):
    """(cut, m_ghost: the map's cut, for the pendants of the void, which rise above the slab)"""
    import re
    chemin = RACINE / 'carte' / 'modele' / 'floor1-entier.glb'
    avant, avant_m = set(bpy.data.objects), set(bpy.data.materials)
    vide_suspendus = []
    bpy.ops.import_scene.gltf(filepath=str(chemin))
    for o in [o for o in bpy.data.objects if o not in avant]:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        if o.type != 'MESH':
            bpy.data.objects.remove(o)
            continue
        coll('Dessous').objects.link(o)
        if o.get('fin'):
            coll('Traits-fins').objects.link(o)
        o.data = o.data.copy()
        o.data.transform(o.matrix_world); o.matrix_world.identity()
        o.data.transform(Matrix.Translation((0, 0, -H_RDC)))
        # (26/11) the pendants of the tables under the void hung from nothing, their cords stopping at the level of
        # the slab: in the double height, they hang on long cables from the mezzanine's ceiling (the roof)
        if o.get('role') == 'suspension':
            c = sum((v.co for v in o.data.vertices), Vector()) / len(o.data.vertices)
            if dans((c.x / PX + CX, -c.y / PX + CY), VIDE):
                for v in o.data.vertices:
                    if v.co.z > -0.03:
                        v.co.z = H - 0.002
                vide_suspendus.append(o)
                continue
        haut = -1.0 if o.get('role') == 'escalier' else SOUS_DALLE
        if max(v.co.z for v in o.data.vertices) > haut:
            couper(o, haut, 'bas')
        if not len(o.data.polygons):
            bpy.data.objects.remove(o)
            continue
        for i, m in enumerate(o.data.materials):            # this floor's material of the same name, if it has one
            nom = re.sub(r'\.\d+$', '', m.name)
            ici = bpy.data.materials.get(nom)
            if ici is None:
                m.name = nom
            elif ici is not m:
                o.data.materials[i] = ici
    for m in set(bpy.data.materials) - avant_m:
        if m.users == 0:
            bpy.data.materials.remove(m)
    if cut is not None:                                 # the cables above the map's cut, see-through, as the walls'
        separer(vide_suspendus, cut, m_ghost)


# ---------------------------------------------------------------- step 3: the furniture (as floor1's step 4)
# The same pieces as on the ground floor (each built in its own frame, metres, facing +y, turned towards what it faces
# and set on its plan point; one object per piece, named for the live map). From the plan: the omakase bar's 6 stools,
# the long table and its 10 chairs, the 6 stools of the ledge over the void, a round table and 2 tub armchairs in each
# half drum, 3 high tables with stools along the right facade in front of a wooden ledge under the glass blocks (as the
# ground floor's facade, photo 8), the machines of the lab, a sideboard. The tables are numbered after floor1's (1-17).
M_PLATEAU = mat('plateau', (0.05, 0.05, 0.05), 0.3)
M_ACIER = mat('acier', (0.035, 0.035, 0.04), 0.4)
M_CUIR = mat('cuir', (0.08, 0.075, 0.07), 0.55)
M_BOIS = mat('bois', (0.15, 0.10, 0.065), 0.6)
M_LAITON = mat('laiton', (0.55, 0.45, 0.30), 0.35)


def rrect(cx_, cy_, w, d, r, seg=6):
    """Rounded rectangle outline (local metres), counter-clockwise from the right side."""
    pts = []
    for qx, qy, a0 in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
        ox, oy = cx_ + qx * (w / 2 - r), cy_ + qy * (d / 2 - r)
        pts += [(ox + r * math.cos(math.radians(a0 + 90 * k / seg)), oy + r * math.sin(math.radians(a0 + 90 * k / seg)))
                for k in range(seg + 1)]
    return pts


class Piece:
    """A bmesh in a local frame; each part keeps its material (as floor1)."""
    def __init__(self):
        self.bm = bmesh.new(); self.mats = []

    def _fin(self, n0, m):
        self.bm.faces.ensure_lookup_table()
        if m not in self.mats:
            self.mats.append(m)
        for f in self.bm.faces[n0:]:
            f.material_index = self.mats.index(m)

    def prisme(self, pts, z0, z1, m):
        n0 = len(self.bm.faces)
        lo = [self.bm.verts.new((x, y, z0)) for x, y in pts]
        hi = [self.bm.verts.new((x, y, z1)) for x, y in pts]
        self.bm.faces.new(list(reversed(lo))); self.bm.faces.new(hi)
        for k in range(len(pts)):
            j = (k + 1) % len(pts)
            self.bm.faces.new((lo[k], lo[j], hi[j], hi[k]))
        self._fin(n0, m)

    def boite(self, x0, y0, x1, y1, z0, z1, m):
        self.prisme([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z0, z1, m)

    def cyl(self, cx_, cy_, r0, r1, z0, z1, m, seg=24):
        n0 = len(self.bm.faces)
        lo = [self.bm.verts.new((cx_ + r0 * math.cos(math.tau * k / seg), cy_ + r0 * math.sin(math.tau * k / seg), z0))
              for k in range(seg)]
        hi = [self.bm.verts.new((cx_ + r1 * math.cos(math.tau * k / seg), cy_ + r1 * math.sin(math.tau * k / seg), z1))
              for k in range(seg)]
        self.bm.faces.new(list(reversed(lo))); self.bm.faces.new(hi)
        for k in range(seg):
            j = (k + 1) % seg
            self.bm.faces.new((lo[k], lo[j], hi[j], hi[k]))
        self._fin(n0, m)

    def barre(self, a, b, w, m):
        a, b = Vector(a), Vector(b)
        d = (b - a).normalized()
        u = d.cross(Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))).normalized() * (w / 2)
        v = d.cross(u).normalized() * (w / 2)
        n0 = len(self.bm.faces)
        c = [[self.bm.verts.new(p + su * u + sv * v) for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1))] for p in (a, b)]
        self.bm.faces.new(list(reversed(c[0]))); self.bm.faces.new(c[1])
        for k in range(4):
            j = (k + 1) % 4
            self.bm.faces.new((c[0][k], c[0][j], c[1][j], c[1][k]))
        self._fin(n0, m)

    def bande(self, R, cy_, t, a, z0, z1, m, seg=14):
        ang = [math.radians(-a + 2 * a * k / seg) for k in range(seg + 1)]
        inner = [(R * math.sin(q), cy_ - R * math.cos(q)) for q in ang]
        outer = [((R + t) * math.sin(q), cy_ - (R + t) * math.cos(q)) for q in reversed(ang)]
        self.prisme(inner + outer, z0, z1, m)


def poser(name, pc, x, y, vers=None, collection='Mobilier', z=0.0):
    """Turn the piece so its +y faces the plan point `vers`, set it on the plan point (x, y), make the object."""
    o_ = P(x, y, z)
    ang = 0.0
    if vers is not None:
        w = P(*vers) - P(x, y)
        ang = math.atan2(w.y, w.x) - math.pi / 2
    bmesh.ops.transform(pc.bm, matrix=Matrix.Translation(o_) @ Matrix.Rotation(ang, 4, 'Z'), verts=pc.bm.verts)
    bmesh.ops.recalc_face_normals(pc.bm, faces=pc.bm.faces)
    me = bpy.data.meshes.new(name)
    pc.bm.to_mesh(me); pc.bm.free()
    for m in pc.mats:
        me.materials.append(m)
    for p_ in me.polygons:
        p_.use_smooth = True
    me.set_sharp_from_angle(angle=math.radians(40))
    ob = bpy.data.objects.new(name, me)
    coll(collection).objects.link(ob)
    return ob


def chaise(haute=False):
    """The thin steel chair of the ground floor (seat 0.47 m); haute: its stool (seat 0.77 m, footrest)."""
    pc = Piece()
    s = 0.30 if haute else 0.0
    zs = 0.42 + s
    pc.prisme(rrect(0, 0, 0.46, 0.44, 0.14), zs, zs + 0.05, M_CUIR)
    pieds = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            a, b = (sx * 0.20, sy * 0.18, 0.0), (sx * 0.17, sy * 0.14, zs)
            pc.barre(a, b, 0.018, M_ACIER)
            pieds.append((Vector(a), Vector(b)))
    if haute:
        t = 0.28 / zs
        q = [a.lerp(b, t) for a, b in pieds]
        for i, j in ((0, 1), (1, 3), (3, 2), (2, 0)):
            pc.barre(q[i], q[j], 0.014, M_ACIER)
    zb = 0.66 + s
    for sx in (-1, 1):
        pc.barre((sx * 0.17, -0.15, zs + 0.05), (sx * 0.17, -0.168, zb), 0.018, M_ACIER)
    pc.bande(0.30, 0.10, 0.03, 36, zb, zb + 0.15, M_CUIR)
    return pc


def fauteuil():
    """The tub armchair of the ground floor's drums."""
    pc = Piece()
    for sx in (-1, 1):
        for sy in (-1, 1):
            pc.barre((sx * 0.20, sy * 0.17, 0.0), (sx * 0.18, sy * 0.15, 0.33), 0.02, M_ACIER)
    pc.prisme(rrect(0, 0, 0.58, 0.54, 0.21), 0.33, 0.39, M_CUIR)
    pc.prisme(rrect(0, 0.025, 0.475, 0.49, 0.15), 0.39, 0.45, M_CUIR)
    ext = [p_ for p_ in rrect(0, 0, 0.58, 0.54, 0.21, 10) if p_[1] < 0.05]
    inn = [p_ for p_ in rrect(0, 0, 0.49, 0.45, 0.165, 10) if p_[1] < 0.05]
    u = [(-0.29, 0.05)] + ext + [(0.29, 0.05), (0.245, 0.05)] + list(reversed(inn)) + [(-0.245, 0.05)]
    pc.prisme(u, 0.39, 0.70, M_CUIR)
    return pc


def table_rect(W, L, h, pieds):
    pc = Piece()
    pc.boite(-W / 2, -L / 2, W / 2, L / 2, h - 0.03, h, M_PLATEAU)
    p_ = 0.44 if h < 1 else 0.50
    for yp in pieds:
        pc.cyl(0, yp, 0.035, 0.035, 0.02, h - 0.03, M_ACIER, 12)
        pc.boite(-p_ / 2, yp - p_ / 2, p_ / 2, yp + p_ / 2, 0.0, 0.02, M_ACIER)
    return pc


def table_ronde(r=0.48):
    pc = Piece()
    pc.cyl(0, 0, r, r, 0.72, 0.75, M_PLATEAU, 48)
    pc.cyl(0, 0, 0.22, 0.06, 0.0, 0.72, M_ACIER, 32)
    return pc


def lampe():
    pc = Piece()
    pc.cyl(0, 0, 0.04, 0.04, 0.0005, 0.03, M_LAITON, 16)
    pc.cyl(0, 0, 0.008, 0.008, 0.03, 0.22, M_LAITON, 8)
    pc.cyl(0, 0, 0.055, 0.03, 0.22, 0.25, M_LAITON, 16)
    return pc


def suspension(z, R):
    pc = Piece()
    pc.cyl(0, 0, R, R, z, z + 0.012, M_LAITON, 32)
    pc.cyl(0, 0, R, 0.03, z + 0.012, z + 0.06, M_ACIER, 32)
    pc.cyl(0, 0, 0.003, 0.003, z + 0.06, H - 0.002, M_ACIER, 6)
    return pc


# (id, name, cx, cy, ...) in plan px
DEMI = [(18, 'Demi-tambour 1', 770), (19, 'Demi-tambour 2', 1031)]          # table at (1298.5, cy), r 0.40 m
GRANDE = (20, 'Grande table', 588, 802, 1106, 895, [681.5, 849, 1018],
          [(x, y) for x in (632.4, 713.8, 840, 974.6, 1054.4) for y in (762.7, 933)])
FACADE = [(21, 'Façade, table haute 1', 1287, 1214, 1381, 1437, [1250, 1330, 1410]),
          (22, 'Façade, table haute 2', 1287, 1603, 1381, 1749, [1638, 1718]),
          (23, 'Façade, table haute 3', 1287, 1808, 1381, 1955, [1843, 1924])]
TABOURETS_OMAKASE = [678.5, 750, 842.5, 914, 998.5, 1071]                   # y 615, facing the counter
TABOURETS_VIDE = [536.8, 608.5, 719.9, 792, 902.9, 975.6]                   # y 1080, facing the void


def tablette_facade():
    """The wooden ledge under the right glass blocks, behind the high tables (as floor1's), round the facade column."""
    cx_, cy_, r = 1477.5, 1516.7, 69.5                 # round the column (as the ground floor's)
    y0, y1, xb = 1172, 2004, 1440
    front = [(1387 - (10 * math.sin(math.pi * (y - 1460) / 112) if 1460 < y < 1572 else 0), y) for y in range(y0, y1 + 1, 4)]
    back = []
    for y in range(y1, y0 - 1, -4):
        x = xb
        if abs(y - cy_) < r:
            x = min(x, cx_ - math.sqrt(r * r - (y - cy_) ** 2))
        back.append((x, y))
    bm = bmesh.new(); prisme(bm, front + back, 0.0, 1.02); mesh_obj('tablette-facade', bm, 'Mobilier', M_BOIS)
    bm = bmesh.new(); prisme(bm, front + back, 1.02, 1.05); mesh_obj('tablette-facade-plateau', bm, 'Mobilier', M_PLATEAU)


def labo_machines():
    """On the lab's counter (26/11 evening): a glass cloche on an oak board, three jars of ferments, a stand mixer,
    a scale; on the work counter's shelves, jars and bowls."""
    pc = Piece(); pc.boite(-0.14, -0.22, 0.14, 0.22, 0.0, 0.02, M_BOIS)
    pc.cyl(0, 0, 0.12, 0.12, 0.02, 0.16, M_PAVE, 24); pc.cyl(0, 0, 0.012, 0.012, 0.16, 0.20, M_PAVE, 8)
    poser('labo-cloche', pc, 436, 905, collection='Mobilier', z=0.92)
    pc = Piece()
    for k, dy in enumerate((-0.11, 0.0, 0.11)):
        pc.cyl(0, dy, 0.045, 0.045, 0.0, 0.17 + 0.03 * (k % 2), M_PAVE, 16)
        pc.cyl(0, dy, 0.047, 0.047, 0.17 + 0.03 * (k % 2), 0.19 + 0.03 * (k % 2), M_BOIS, 16)
    poser('labo-bocaux', pc, 434, 972, collection='Mobilier', z=0.92)
    pc = Piece(); pc.boite(-0.10, -0.14, 0.10, 0.14, 0.0, 0.05, M_ACIER); pc.boite(-0.05, 0.06, 0.05, 0.14, 0.05, 0.34, M_ACIER)
    pc.boite(-0.05, -0.12, 0.05, 0.14, 0.34, 0.42, M_ACIER); pc.cyl(0, -0.02, 0.07, 0.09, 0.05, 0.22, M_ACIER, 20)
    poser('labo-batteur', pc, 434, 1040, collection='Mobilier', z=0.92)
    pc = Piece()
    for k in range(5):                                         # jars on the shelves
        for z in (1.425, 1.805):
            pc.cyl(-0.05 + 0.05 * (k % 2), -1.00 + 0.48 * k, 0.05, 0.05, z - 1.40, z - 1.40 + 0.16, M_PAVE, 14)
    poser('labo-pots', pc, 248, 1010, collection='Mobilier', z=1.40)


def angle_se():
    """The south-east corner (26/11), now part of the room, by the stair's arrival, behind glass blocks on two sides:
    station: the waiters' station, a counter along the glass blocks (glasses, carafes, a cutlery tray), where the
             sideboard was, on to the corner;
    table: a table for two in the corner, the sideboard kept at the end of the facade."""
    if ANGLE == 'table':
        bm = bmesh.new(); bm_box(bm, 1374, 2008, 1440, 2208, 0.0, 0.85)
        mesh_obj('console-facade', bm, 'Mobilier', M_BOIS)
        tc = (1372, 2318)
        poser('table-24', table_rect(0.70, 0.70, 0.75, [0.0]), *tc, collection='Tables')
        poser('lampe-24', lampe(), tc[0], tc[1], collection='Tables', z=0.75)
        poser('suspension-24', suspension(1.85, 0.20), *tc, collection='Suspensions')
        for k, dy in enumerate((-58, 58)):
            poser(f'chaise-24-{k + 1}', chaise(), tc[0], tc[1] + dy, vers=tc, collection='Assises')
        return
    x0, x1, y0, y1 = 1388, 1440, 2016, 2388
    bm = bmesh.new(); bm_box(bm, x0, y0, x1, y1, 0.0, 0.90)
    mesh_obj('station', bm, 'Mobilier', M_BOIS)
    bm = bmesh.new(); bm_box(bm, x0 - 2, y0 - 2, x1, y1 + 2, 0.90, 0.93)
    mesh_obj('station-plateau', bm, 'Mobilier', M_PLATEAU)
    bm = bmesh.new()
    for i in range(3):                                   # glasses upside down, 3 x 4, on a tray
        for j in range(4):
            c = Vector((1404 + 11 * i, 2250 + 11 * j))
            pts = [c + Vector((math.cos(a), math.sin(a))) * 4.0 for a in (math.tau * k / 10 for k in range(10))]
            prisme(bm, [(p_.x, p_.y) for p_ in pts], 0.935, 1.05)
    for k, y in enumerate((2318, 2336)):                 # two carafes
        c = Vector((1414, y))
        pts = [c + Vector((math.cos(a), math.sin(a))) * 5.5 for a in (math.tau * k / 12 for k in range(12))]
        prisme(bm, [(p_.x, p_.y) for p_ in pts], 0.93, 1.16)
    mesh_obj('station-verres', bm, 'Mobilier', M_VERRE)
    bm = bmesh.new()
    bm_box(bm, 1398, 2244, 1438, 2294, 0.93, 0.935)      # the tray under the glasses
    bm_box(bm, 1396, 2360, 1432, 2380, 0.93, 0.98)       # the cutlery tray
    bm_box(bm, 1396, 2040, 1432, 2110, 0.93, 1.02)       # a stack of plates
    mesh_obj('station-plateaux', bm, 'Mobilier', M_ACIER)


def build_mobilier():
    """Step 3: the furniture. Returns the new objects; writes the table list for the live map."""
    for c in ('Mobilier', 'Tables', 'Assises', 'Suspensions'):
        coll(c)
    avant = set(bpy.data.objects)
    liste = []
    for tid, nom, cy in DEMI:
        tc = (DEMI_CX, cy)
        poser(f'table-{tid:02d}', table_ronde(0.40), *tc, collection='Tables')
        poser(f'lampe-{tid:02d}', lampe(), tc[0] + 15, tc[1], collection='Tables', z=0.75)
        poser(f'suspension-{tid:02d}', suspension(1.85, 0.26), *tc, collection='Suspensions')
        for k, dy in enumerate((-44, 44)):
            poser(f'chaise-{tid:02d}-{k + 1}', fauteuil(), DEMI_CX - 66, cy + dy, vers=tc, collection='Assises')
        liste.append(dict(id=tid, nom=nom, type='tambour', centre_px=[tc[0], tc[1]], places=4,
                          assises='banquette en demi-cercle et 2 fauteuils', zone='D'))
    tid, nom, x0, y0, x1, y1, pieds, chaises = GRANDE
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    W, L = (y1 - y0) * PX, (x1 - x0) * PX
    poser(f'table-{tid:02d}', table_rect(W, L, 0.75, [(xp - cx) * PX for xp in pieds]), cx, cy, vers=(cx + 100, cy),
          collection='Tables')
    for k, xp in enumerate(pieds):
        poser(f'lampe-{tid:02d}-{k + 1}', lampe(), xp, cy, collection='Tables', z=0.75)
        poser(f'suspension-{tid:02d}-{k + 1}', suspension(1.75, 0.20), xp, cy, collection='Suspensions')
    for k, (x, y) in enumerate(chaises):
        poser(f'chaise-{tid:02d}-{k + 1}', chaise(), x, y, vers=(x, cy), collection='Assises')
    liste.append(dict(id=tid, nom=nom, type='table', centre_px=[cx, cy], taille_m=[round(L, 2), round(W, 2)],
                      places=len(chaises), assises='chaises', zone='G'))
    for tid, nom, x0, y0, x1, y1, ys in FACADE:
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        W, L = (x1 - x0) * PX, (y1 - y0) * PX
        poser(f'table-{tid:02d}', table_rect(W, L, 1.05, [0.0] if L < 1.4 else [-(L / 2 - 0.35), L / 2 - 0.35]),
              cx, cy, collection='Tables')
        poser(f'lampe-{tid:02d}', lampe(), cx, cy, collection='Tables', z=1.05)
        poser(f'suspension-{tid:02d}', suspension(2.05, 0.20), cx, cy, collection='Suspensions')
        for k, y in enumerate(ys):
            poser(f'chaise-{tid:02d}-{k + 1}', chaise(haute=True), 1245, y, vers=(cx, y), collection='Assises')
        liste.append(dict(id=tid, nom=nom, type='table haute', centre_px=[cx, cy], taille_m=[round(W, 2), round(L, 2)],
                          places=len(ys), assises='tabourets', zone='F'))
    for k, x in enumerate((700, 850, 1000)):                   # (26/11 evening) three pendants over the omakase bar
        poser(f'suspension-omakase-{k + 1}', suspension(1.85, 0.18), x, 551, collection='Suspensions')
    for k, x in enumerate(TABOURETS_OMAKASE):
        poser(f'tabouret-omakase-{k + 1}', chaise(haute=True), x, 615, vers=(x, 540), collection='Assises')
    liste.append(dict(id=100, nom='Bar omakase', type='bar', centre_px=[880.5, 549], places=6, assises='tabourets'))
    for k, x in enumerate(TABOURETS_VIDE):
        poser(f'tabouret-vide-{k + 1}', chaise(haute=True), x, 1080, vers=(x, 1172), collection='Assises')
    liste.append(dict(id=101, nom='Tablette du vide', type='bar', centre_px=[756, 1143], places=6, assises='tabourets'))
    tablette_facade()
    labo_machines()
    angle_se()
    for t in liste:
        x, y = t['centre_px']; v = P(x, y)
        t['centre_m'] = [round(v.x, 3), round(v.y, 3)]
    (RACINE / 'modele' / 'floor2-tables.json').write_text(json.dumps(dict(
        note='floor2 (1er étage, la mezzanine) : les tables de la carte en direct, numérotées après celles du '
             'rez-de-chaussée. centre_px : sur floor2.png (les pixels de floor1.png) ; centre_m : dans le modèle (même '
             'origine que floor1). zone : D demi-tambours, G grande table, F façade ; 100 le bar omakase, 101 la '
             'tablette au bord du vide.',
        tables=liste, total_places=sum(t['places'] for t in liste)), ensure_ascii=False, indent=1))
    return [o for o in bpy.data.objects if o not in avant]


# ---------------------------------------------------------------- light, render (as floor1)
def setup_render():
    sc.render.engine = 'CYCLES'
    try:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type = 'METAL'
        prefs.get_devices()
        for d in prefs.devices:
            d.use = True
        sc.cycles.device = 'GPU'
    except Exception:
        pass
    sc.cycles.samples = int(ARGS.get('samples', 96))
    sc.cycles.use_denoising = True
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Medium High Contrast'
    w = bpy.data.worlds.new('monde')
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0.62, 0.63, 0.65, 1)
    bg.inputs['Strength'].default_value = 0.55
    sun = bpy.data.lights.new('soleil', 'SUN')
    sun.energy = 2.6
    sun.angle = math.radians(12)
    so = bpy.data.objects.new('soleil', sun)
    sc.collection.objects.link(so)
    so.rotation_euler = (math.radians(38), 0, math.radians(-38))


def camera(name, loc, target, ortho=None, lens=35):
    cd = bpy.data.cameras.new(name)
    if ortho:
        cd.type = 'ORTHO'
        cd.ortho_scale = ortho
    else:
        cd.lens = lens
    cd.clip_end = 500
    co = bpy.data.objects.new(name, cd)
    sc.collection.objects.link(co)
    co.location = loc
    co.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return co


def render(name, cam, res):
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = ECH
    OUT.mkdir(parents=True, exist_ok=True)
    sc.render.filepath = str(OUT / f'{name}.png')
    bpy.ops.render.render(write_still=True)
    print('rendu', sc.render.filepath)


def show(collections_hidden=()):
    for c in bpy.data.collections:
        c.hide_render = c.name in collections_hidden


# ---------------------------------------------------------------- the map styles (as floor1)
VARIANTES = {
    'fantome':    dict(cut=1.2,  grid=True, alpha=1.0,  ghost=True,  hidden=(0.72,) * 3),
    'fil-de-fer': dict(cut=None, grid=True, alpha=0.03, ghost=False, hidden=(0.62,) * 3),
    'detail':     dict(cut=None, grid=True, alpha=1.0,  ghost=False, hidden=None),   # the close-ups
}

# step 2 close-ups: camera (plan px, z), target (plan px, z), lens
PLANS = {
    'omakase':   ((1190, 770, 1.75), (760, 380, 1.00), 24),    # photos 11, 12
    'banquette': ((1095, 905, 1.20), (1300, 770, 0.85), 24),   # photos 17, 20: the upper half drum
    'rebord':    ((700, 900, 1.75), (760, 1180, 0.60), 24),    # photo 26: the ledge over the void
    'bloc':      ((1250, 1560, 1.65), (760, 2060, 1.30), 26),  # photo 37 (the portal on the street)
    'escalier':  ((1300, 1930, 1.70), (1080, 2170, -0.40), 24),  # photo 28: the spiral stair seen from above
    # the prototypes for the void: across it, from the mezzanine's right side, towards the drums
    'vide':      ((1165, 1470, 1.65), (420, 1740, 0.10), 17),
    # the island over the entry: from the mezzanine across the void, and from the ground floor's room, looking up
    'ile':       ((1230, 1560, 2.45), (720, 2110, 0.70), 22),
    'ile-bas':   ((960, 1480, -1.90), (690, 2000, 0.60), 18),
    'lierre':    ((690, 1790, 0.75), (735, 1900, 0.05), 32),       # the ivy close up, over the north edge
    'garde-corps': ((1150, 1860, 1.75), (1090, 2030, 0.35), 22),   # the parapet joined to the stair's
    # step 3
    'grande':    ((1160, 1140, 1.55), (800, 820, 0.70), 22),     # the long table and the omakase bar beyond
    'demi':      ((1080, 1180, 1.40), (1290, 900, 0.75), 24),    # the two half drums
    'facade':    ((1150, 2090, 1.55), (1330, 1350, 0.95), 26),   # the high tables along the facade
    # the whole building (25/11), from the street: the two storeys and the slab's band between them
    'facade-ouest': ((-760, 2960, 0.40), (450, 1450, -1.50), 24),   # along the left facade, from its far corner
    'angle-entree': ((180, 3060, 0.60), (880, 2250, -1.60), 20),    # the corner of the entry, the island over it
    'est':          ((2080, 1180, 0.90), (1460, 470, -0.90), 20),   # the right facade, the lift shaft's band
    # the reworked building (26/11): outside, the street front and the corners; inside, the reworked places
    'rue-sud':      ((930, 3330, -1.45), (900, 2380, -0.55), 24),   # the street front: shopfront, glass blocks, corner
    'angle-se':     ((1900, 3100, 1.00), (1150, 2250, -1.30), 22),  # the south-east corner from outside, as image 2
    'facade-est':   ((2330, 2420, 0.10), (1460, 1240, -0.90), 24),  # along the right facade, from the corner
    'angle-1er':    ((1230, 2000, 1.65), (1420, 2360, 0.60), 20),   # the corner of the 1st floor, by the stair
    'reserve':      ((560, 235, 2.60), (760, 165, 0.60), 18),       # the omakase bar's storeroom
    'rdc-entree':   ((720, 2090, -1.75), (780, 2400, -2.25), 20),   # the shopfront, from the concierge
    'vestiaire':    ((1180, 2385, -1.65), (1400, 2330, -2.30), 18), # the cloakroom, from the foot of the stair
    # the reworked places (26/11 evening)
    'tablette':     ((1150, 1075, 1.65), (975, 1175, 0.90), 24),    # the ledge, one with the glass parapet
    'vide-lumieres': ((1150, 1960, -1.85), (760, 1450, 1.60), 18),  # the pendants of the void on their long cables, from below
    'bar':          ((850, 790, 1.60), (850, 400, 1.05), 22),       # the omakase bar
    'cuisine':      ((590, 420, 1.65), (430, 160, 0.90), 18),       # the kitchen corner, from its corner by the aisle
    'labo':         ((585, 1000, 1.60), (370, 960, 0.80), 22),      # the lab's counter
    'colonne-est':  ((1760, 1010, 0.80), (1440, 800, -0.20), 22),   # the right facade's column, glass blocks on it
    'palier':       ((1310, 2060, 1.65), (1120, 2200, -0.30), 18),   # the stair's landing, from the arrival
    'palier-haut':  ((1330, 1880, 1.80), (1082, 2172, -0.60), 20),   # the same, from the corner
    'colonne-1er':  ((1235, 1290, 1.60), (1462, 1560, 1.05), 20),   # the other column, from inside the 1st floor
}


def set_mat(name, rgb, rough=0.85, alpha=1.0):
    b = next(n for n in bpy.data.materials[name].node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = (*rgb, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Transmission Weight'].default_value = 0.0
    b.inputs['Alpha'].default_value = alpha


def mat_grille(name, base, line, minor, major, origin, fade=None):
    """Matte material with a 1 m grid (strength `minor`) and a 5 m grid (strength `major`), in world metres.
    fade = (r0, r1): the grid fades out between r0 and r1 metres from `origin`."""
    m = mat(name, base, 0.9)
    nt = m.node_tree; N = nt.nodes; L = nt.links
    b = next(n for n in N if n.type == 'BSDF_PRINCIPLED')
    geo = N.new('ShaderNodeNewGeometry')
    sep = N.new('ShaderNodeSeparateXYZ'); L.new(geo.outputs['Position'], sep.inputs[0])

    def op(kind, a, b_=None):
        n = N.new('ShaderNodeMath'); n.operation = kind
        for i, v in enumerate((a, b_)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                L.new(v, n.inputs[i])
        return n.outputs[0]

    def lines(axis, o, step, half):
        u = op('SUBTRACT', sep.outputs[axis], o)
        d = op('MULTIPLY', op('ABSOLUTE', op('SUBTRACT', op('FRACT', op('ADD', op('DIVIDE', u, step), 0.5)), 0.5)), step)
        mr = N.new('ShaderNodeMapRange'); L.new(d, mr.inputs['Value'])
        mr.inputs['From Min'].default_value = half; mr.inputs['From Max'].default_value = half + 0.009
        mr.inputs['To Min'].default_value = 1.0; mr.inputs['To Max'].default_value = 0.0
        return mr.outputs['Result']

    g1 = op('MULTIPLY', op('MAXIMUM', lines(0, origin.x, 1.0, 0.004), lines(1, origin.y, 1.0, 0.004)), minor)
    g5 = op('MULTIPLY', op('MAXIMUM', lines(0, origin.x, 5.0, 0.008), lines(1, origin.y, 5.0, 0.008)), major)
    g = op('MAXIMUM', g1, g5)
    if fade:
        dist = N.new('ShaderNodeVectorMath'); dist.operation = 'DISTANCE'
        L.new(geo.outputs['Position'], dist.inputs[0]); dist.inputs[1].default_value = (origin.x, origin.y, 0)
        mr = N.new('ShaderNodeMapRange'); L.new(dist.outputs['Value'], mr.inputs['Value'])
        mr.inputs['From Min'].default_value, mr.inputs['From Max'].default_value = fade
        mr.inputs['To Min'].default_value = 1.0; mr.inputs['To Max'].default_value = 0.0
        g = op('MULTIPLY', g, mr.outputs['Result'])
    mix = N.new('ShaderNodeMix'); mix.data_type = 'RGBA'
    L.new(g, mix.inputs[0])
    mix.inputs[6].default_value = (*base, 1); mix.inputs[7].default_value = (*line, 1)
    L.new(mix.outputs[2], b.inputs['Base Color'])
    return m


def ground(material, z):
    me = bpy.data.meshes.new('terrain'); bm_ = bmesh.new()
    bm_.faces.new([bm_.verts.new((x, y, z)) for x, y in ((-200, -200), (200, -200), (200, 200), (-200, 200))])
    bm_.to_mesh(me); bm_.free()
    return obj('terrain', me, 'Sols', material)


def freestyle_lines(visible, hidden, thickness=1.0):
    """As floor1; the ground floor under the slab (Dessous) is drawn as the mezzanine is (the whole building)."""
    sc.render.use_freestyle = True
    sc.render.line_thickness_mode = 'ABSOLUTE'
    sc.render.line_thickness = 1.0
    vl = sc.view_layers[0]
    vl.use_freestyle = True
    fs = vl.freestyle_settings
    fs.crease_angle = math.radians(140)
    exclus = coll('Sans-trait-plein')               # the thin-line objects and the ivy: not in the main lines
    lierre_ = [o for o in coll('Ile').objects if o.name.startswith('ile-lierre')] if 'Ile' in bpy.data.collections else []
    proches = {'ile', 'ile-bas', 'lierre', 'garde-corps'}      # the close-ups of the ivy keep its lines
    if not (ARGS.get('variante') == 'detail' and proches & set(ARGS.get('plans', '').split(','))):
        for o in lierre_:       # elsewhere it is shaded without lines: thousands of leaves would only make a grey
                                # mass, and take an hour to draw
            if o.name in coll('Traits-fins').objects:
                coll('Traits-fins').objects.unlink(o)
            if o.name not in coll('Sans-trait').objects:
                coll('Sans-trait').objects.link(o)
    for o in list(coll('Traits-fins').objects) + list(coll('Sans-trait').objects):
        if o.name not in exclus.objects:
            exclus.objects.link(o)
    sets = [('visibles', 'VISIBLE', visible, 1.15 * thickness)]
    if hidden:
        sets.append(('cachees', 'HIDDEN', hidden, 0.75 * thickness))
    fins = len(coll('Traits-fins').all_objects) > 0
    if fins:
        sets.append(('fins', 'VISIBLE', tuple(min(1.0, c_ + 0.30) for c_ in visible), 0.6 * thickness))
    for k, (nom, vis, col, ep) in enumerate(sets):
        ls = fs.linesets[k] if len(fs.linesets) > k else fs.linesets.new(nom)
        ls.select_by_visibility = True
        ls.visibility = vis
        ls.select_silhouette = ls.select_border = ls.select_crease = True
        ls.select_by_collection = True
        if nom == 'fins':
            ls.collection = coll('Traits-fins'); ls.collection_negation = 'INCLUSIVE'
        else:
            ls.collection = exclus; ls.collection_negation = 'EXCLUSIVE'
        ls.linestyle = bpy.data.linestyles.new(nom)
        ls.linestyle.color = col
        ls.linestyle.thickness = ep


# ---------------------------------------------------------------- the model of the interactive map (as floor1's step 5)
# glTF export of the built variant (fantôme: the mezzanine cut at 1.2 m with its see-through tops; fil-de-fer: uncut),
# raised by 3.35 m so it stands on the ground floor's frame of the map. Each object carries its role, 'fin' for the
# thin-line objects, 'feuillage' for the ivy (shaded without lines), its table number (18 - 23, 100 the omakase bar's
# stools, 101 the ledge's) and, on the two counters, the bar they belong to. The ground floor under the slab, as these
# renders show it, goes to its own file (dessous=...): the map sets it under the mezzanine.
ROLES = {'Coque': 'mur', 'Vitrages': 'vitrage', 'Tambours': 'tambour', 'Escalier': 'escalier', 'Sols': 'sol',
         'Bar': 'element', 'Banquettes': 'element', 'Rideaux': 'element', 'Vide': 'element', 'Ile': 'element',
         'Mobilier': 'element', 'Tables': 'table', 'Assises': 'assise', 'Suspensions': 'suspension'}
BARS = {'omakase-plateaux': 100, 'tablette-vide-plateau': 101}


def export_web(chemin, objets, dessous=False):
    import re
    chemin = Path(chemin) if Path(chemin).is_absolute() else RACINE / chemin
    chemin.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT')
    monter = Matrix.Translation((0, 0, H_RDC))
    for o in objets:
        cs = [c.name for c in o.users_collection]
        if not dessous:
            o['role'] = 'fantome' if 'Fantome' in cs else next((ROLES[c] for c in cs if c in ROLES), 'fin' if 'Traits-fins' in cs else 'element')
            o['fin'] = int('Traits-fins' in cs and not o.name.startswith('ile-lierre'))
            o['feuillage'] = int(o.name.startswith('ile-lierre'))
            m = re.match(r'^(table|chaise|lampe|suspension)-(\d\d)', o.name)
            if m:
                o['table'] = int(m.group(2))
            elif o.name.startswith('tabouret-omakase'):
                o['table'] = 100
            elif o.name.startswith('tabouret-vide'):
                o['table'] = 101
            if o.name in BARS:
                o['bar'] = BARS[o.name]
        elif 'table' in o:
            del o['table']                      # under the slab, the ground floor's tables are decor
        o.matrix_world = monter @ o.matrix_world
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(chemin), export_format='GLB', use_selection=True, export_extras=True,
                              export_apply=True, export_yup=True, export_cameras=False, export_lights=False)
    for o in objets:
        o.matrix_world = monter.inverted() @ o.matrix_world
    print('export', chemin, len(objets), 'objets,', sum(len(o.data.polygons) for o in objets), 'faces')


setup_render()
centre = P(873, 1227)

if not ARGS.get('variante'):
    # ---------------------------------------------------------------- step 1 views
    build(None)
    if 'dessus' in VUES:
        # calibration: the plan with the walls over it, the slab hidden so the drawing shows through
        show(collections_hidden=('Sols', 'Escalier'))
        bpy.data.objects['soleil'].rotation_euler = (0, 0, 0)
        cam = camera('cam-dessus', centre + Vector((0, 0, 60)), centre, ortho=21.0)
        render('1-calage-vue-de-dessus', cam, (1500, 2000))
    bpy.data.objects['soleil'].rotation_euler = (math.radians(38), 0, math.radians(-38))
    show(collections_hidden=('Plan',))
    if 'iso' in VUES:
        d = Vector((-1, -1.05, 1.15)).normalized()
        cam = camera('cam-iso', centre + d * 60, centre, ortho=24.5)
        render('2-coque-axonometrie', cam, (2000, 1500))
    if 'coupe' in VUES:
        # the walls cut at 1.2 m, as on the map, seen from the same corner
        for o in list(bpy.data.objects):
            if o.type == 'MESH' and o.users_collection[0].name in ('Coque', 'Tambours', 'Vitrages'):
                zs = [(o.matrix_world @ v.co).z for v in o.data.vertices]
                if zs and max(zs) > 1.2:
                    bm = bmesh.new(); bm.from_mesh(o.data)
                    co = o.matrix_world.inverted() @ Vector((0, 0, 1.2))      # the cut in the object's own frame
                    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=co,
                                           plane_no=(0, 0, 1), clear_outer=True)
                    bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary])
                    bm.to_mesh(o.data); bm.free()
                    for f_ in o.data.polygons:
                        f_.use_smooth = False
        d = Vector((-1, -1.05, 1.15)).normalized()
        cam = camera('cam-coupe', centre + d * 60, centre, ortho=24.5)
        render('3-coque-coupee-a-1m20', cam, (2000, 1500))
else:
    # ---------------------------------------------------------------- the map styles (as floor1's variants)
    nom = ARGS['variante']
    V = VARIANTES[nom]
    OUT = Path(ARGS.get('out', RACINE / 'rendus' / ('15-etage-mobilier' if MOBILIER else
                                                    '13-etage-elements-fixes' if ELEMENTS else '12-etage-coque')))
    pre = ARGS.get('prefixe', '')
    coll('Fantome')
    m_ghost = mat('fantome', (0.98, 0.98, 0.98), 0.6, alpha=0.16)

    build(V['cut'])
    if V['ghost']:                              # the walls above the cut, see-through
        avant = set(bpy.data.objects)
        build(None, bas=V['cut'] + 0.004)
        for o in set(bpy.data.objects) - avant:
            for c in o.users_collection:
                c.objects.unlink(o)
            coll('Fantome').objects.link(o)
            o.data.materials.clear(); o.data.materials.append(m_ghost)
            o.visible_shadow = False
    if ELEMENTS:
        nouveaux = build_elements()
        if MOBILIER:
            nouveaux += build_mobilier()
        if V['cut'] is not None:
            separer(nouveaux, V['cut'], m_ghost if V['ghost'] else None)
    dessous(V['cut'], m_ghost if V['ghost'] else None)

    # materials: white, as floor1's variants
    a = V['alpha']
    for name, rgb in (('mur', (0.965,) * 3), ('poteau', (0.96,) * 3), ('tambour', (0.93, 0.93, 0.925)),
                      ('marche', (0.90,) * 3)):
        set_mat(name, rgb, 0.85, a)
    set_mat('dalle', (0.95,) * 3, 0.85, 1.0)
    set_mat('cadre', (0.80,) * 3, 0.6, max(a, 0.25) if a < 1 else 1.0)
    set_mat('verre', (0.97, 0.98, 0.99), 0.3, 0.16 if a == 1.0 else min(a, 0.16))
    set_mat('gravier', (0.88, 0.875, 0.865), 0.95)
    if ELEMENTS:
        for name, rgb, rough in (('banquette', (0.955, 0.95, 0.94), 0.8), ('pierre', (0.915, 0.91, 0.90), 0.95),
                                 ('comptoir', (0.935,) * 3, 0.5), ('meuble', (0.96,) * 3, 0.85),
                                 ('miroir', (0.975,) * 3, 0.2), ('rideau', (0.975, 0.972, 0.965), 0.9),
                                 ('lumiere', (0.995, 0.99, 0.975), 0.4), ('feuillage', (0.90, 0.92, 0.88), 0.9),
                                 ('terre', (0.86, 0.85, 0.83), 1.0), ('ecorce', (0.88, 0.87, 0.85), 0.9)):
            set_mat(name, rgb, rough, a)
        set_mat('pave', (0.95, 0.97, 0.98), 0.25, 0.55 if a == 1.0 else min(a, 0.3))
    for name, rgb, rough in (('bordure', (0.93,) * 3, 0.6), ('pot', (0.95,) * 3, 0.85),
                             ('rocher', (0.92, 0.915, 0.905), 0.95)):       # the ground floor's own (floor1's whites)
        if name in bpy.data.materials:
            set_mat(name, rgb, rough, a)
    if MOBILIER:                                # the furniture in the same whites as floor1's
        for name, rgb, rough in (('plateau', (0.90,) * 3, 0.5), ('acier', (0.74,) * 3, 0.5),
                                 ('cuir', (0.955, 0.95, 0.94), 0.8), ('bois', (0.93, 0.92, 0.905), 0.8),
                                 ('laiton', (0.97,) * 3, 0.4)):
            set_mat(name, rgb, rough, a)
    o_c = P(837, 1278)
    m_int = mat_grille('sol-grille', (0.975, 0.972, 0.965), (0.80, 0.80, 0.80), 0.35, 0.55, o_c)
    m_ext = mat_grille('terrain-grille', (0.90, 0.898, 0.89), (0.66, 0.66, 0.66), 0.45, 0.8, o_c, fade=(14, 30))
    dalle = bpy.data.objects['dalle']
    dalle.data.materials[0] = m_int             # the walking surface; its edge and underside stay 'dalle'
    for o in coll('Dessous').objects:           # the ground floor's floors: the same grid
        for i, m in enumerate(o.data.materials):
            if m.name == 'sol-grille':
                o.data.materials[i] = m_int
    ground(m_ext, -H_RDC - 0.052)

    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    bg = sc.world.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0.97, 0.965, 0.955, 1)
    bg.inputs['Strength'].default_value = 0.67
    sun = bpy.data.objects['soleil']
    sun.data.energy = 1.25
    sun.data.angle = math.radians(25)
    sc.cycles.transparent_max_bounces = 24
    freestyle_lines((0.30, 0.30, 0.30), V['hidden'], 1.25 if nom == 'fil-de-fer' else 1.0)
    if ELEMENTS and a < 0.1:
        for o in bpy.data.objects:
            o.visible_shadow = False
    for o in coll('Escalier').objects:          # the stair's top: no deep shadow on the ground floor seen through it
        o.visible_shadow = False
    show(collections_hidden=('Plan',))
    sun.rotation_euler = (math.radians(35), 0, math.radians(-121))

    cam_top = camera('cam-dessus', o_c + Vector((0, 0, 60)), o_c, ortho=21.6)
    cam_top.rotation_euler = (0, 0, math.radians(-90))
    d = Vector((-1, -1.05, 1.15)).normalized()
    c3 = o_c + Vector((0, 0, 0.9))
    cam_3d = camera('cam-3d', c3 + d * 60, c3, ortho=25.5)
    if ARGS.get('trace'):                       # the plan drawn from the model (outils/plans/depuis_modele.py)
        import plan_modele
        plan_modele.tracer(RACINE / ARGS['trace'], CX, CY, PX)
    elif ARGS.get('export'):
        maillages = [o for o in bpy.data.objects if o.type == 'MESH' and o.name != 'terrain'
                     and not any(c.name == 'Plan' for c in o.users_collection)]
        sous = [o for o in maillages if 'Dessous' in [c.name for c in o.users_collection]]
        export_web(ARGS['export'], [o for o in maillages if o not in sous])
        if ARGS.get('dessous'):
            export_web(ARGS['dessous'], sous, dessous=True)
    elif ARGS.get('plans'):
        for pl in ARGS['plans'].split(','):
            (x0, y0, z0), (x1, y1, z1), lens, *res = PLANS[pl]
            render(f'{pre}plan-{pl}', camera(f'cam-{pl}', P(x0, y0, z0), P(x1, y1, z1), lens=lens),
                   res[0] if res else (1500, 1000))
    else:
        pendants = [o for o in bpy.data.objects if o.name.startswith('suspension')]
        for v in ARGS.get('vues', 'dessus,3d').split(','):
            for o in pendants:                  # as floor1: seen from the top, the pendants would hide the tables
                o.hide_render = v == 'dessus'
            render(f'{pre}{nom}-{v}', cam_top if v == 'dessus' else cam_3d, (2000, 1250))
if ARGS.get('save'):
    bpy.ops.wm.save_as_mainfile(filepath=ARGS['save'])
