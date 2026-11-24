# Floor2 (the 1st floor, the mezzanine) of the restaurant: the plan laid at real scale and the shell modelled over it.
# The same frame as floor1 (floor2.png is drawn in the pixels of floor1.png, 120 px = 1 m) and the same world origin;
# here z = 0 is the floor of the mezzanine (the top of its slab, 3.35 m over the ground floor).
# The script is the source: the .blend is regenerated, never saved by hand.
#
# step 1, the shell: the walls (vectorised from floor2.png, see outils/vectoriser_etage1.py), the columns, the facades,
# the slab with its voids (over the room, over the rock garden and round the spiral stair), the glass parapets, the two
# half drums of the booths, the solid volume over the entry, the stair up and the top of the spiral stair.
#
# usage: blender -b -P floor2.py -- [vue=dessus,iso,coupe] [ech=100] [save=<file.blend>] [out=<dossier>]
import bpy, bmesh, json, math, sys
from pathlib import Path
from mathutils import Vector

ICI = Path(__file__).resolve().parent
RACINE = ICI.parents[1]
ARGS = dict(a.split('=', 1) for a in (sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []) if '=' in a)
VUES = ARGS.get('vue', 'dessus,iso,coupe').split(',')
ECH = int(ARGS.get('ech', 100))
OUT = Path(ARGS.get('out', RACINE / 'rendus' / '12-etage-coque'))

DATA = json.loads((RACINE / 'modele' / 'etage1-murs.json').read_text())
PX = 1 / DATA['echelle_px_par_m']        # metres per plan pixel
CX, CY = 837, 1230                       # plan pixel at the world origin (as floor1)
H = 3.0                                  # the mezzanine's clear height (floor to the roof slab), from the section
H_RDC = 3.35                             # the ground floor under it (floor1.py)
DALLE = 0.30                             # the slab


def P(x, y, z=0.0):
    return Vector(((x - CX) * PX, -(y - CY) * PX, z))


# ---------------------------------------------------------------- scene
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
for c in ('Plan', 'Coque', 'Sols', 'Vitrages', 'Tambours', 'Escalier'):
    sc.collection.children.link(bpy.data.collections.new(c))


def coll(name):
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


# the materials of floor1's step 1, so both floors read the same
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


# ---------------------------------------------------------------- the plan of the floor
SOL = [(384, 140), (1457, 140), (1457, 2245), (1286, 2245), (1286, 2213), (602, 2213), (602, 2245), (232, 2245),
       (232, 842), (384, 842)]
# the void over the room: along the ledge (y 1172), round the corner, down the right side, then round the stair
VIDE = [(237, 1172), (1012, 1172)] + arc(1012, 1242, 70, -90, 0, 12)[1:] + [(1082, 1917)] + \
    arc(1020, 1917, 62, 0, 90, 12)[1:] + [(1000, 1990), (861, 2044), (861, 1896), (601, 1896), (601, 2250), (237, 2250)]
# the void over the rock garden (the gravel seen from above on floor2.png)
JARDIN = [(861, 2040), (1057, 2040), (1057, 2126), (1238, 2126)] + arc(1238, 2187, 61, -90, 0, 10)[1:] + \
    [(1299, 2370), (861, 2370)]
HX, HY, R_ESC = 1082, 2172, 184          # the spiral stair (floor1.py: hub, treads to r 180) and its opening
BLOC = (601, 1896, 856, 2373)            # the solid volume over the entry (black on the plan, white box on the axonometry)
ESCALIER_HAUT = (485, 140, 852, 247)     # the stair up to the roof floor, rising towards +x from x 572


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


def build_dalle():
    """The slab with its openings: the void over the room, the rock garden, the round opening of the stair."""
    dalle = to_mesh(extrude_loops('dalle', [SOL], -DALLE, 0.0, 'Sols', M_SOL))
    outils = [to_mesh(extrude_loops('t-vide', [VIDE], -1, 1, 'Sols', M_SOL)),
              to_mesh(extrude_loops('t-jardin', [JARDIN], -1, 1, 'Sols', M_SOL)),
              cylinder('t-escalier', HX, HY, R_ESC, -1, 1, 'Sols', M_SOL, seg=120)]
    soustraire(dalle, outils)
    # its edge and underside in a light concrete, the walking surface dark (as floor1's floors)
    dalle.data.materials.append(M_DALLE)
    for p in dalle.data.polygons:
        p.material_index = 0 if (p.normal.z > 0.9) else 1


def build_coque(top, bas=0.0):
    # ---- walls (vectorised from floor2.png), and the outer walls round the lab that the plan leaves black
    for k, mu in enumerate(DATA['murs']):
        extrude_loops(f"mur-{mu['id']}-{k}", [mu['contour']] + mu['trous'], bas, top, 'Coque', M_MUR)
    for k, (x0, y0, x1, y1) in enumerate(((200, 752, 384, 842), (200, 842, 232, 2276), (200, 2245, 602, 2276))):
        box(f'mur-labo-{k}', x0, y0, x1, y1, bas, top, 'Coque', M_MUR)
    # ---- the solid volume over the entry
    box('bloc-entree', *BLOC, bas, top, 'Coque', M_MUR)
    # ---- columns
    for c in DATA['poteaux']:
        cx, cy, r = (407.5, 801.5, 49.5) if c['id'] == 841 else (c['cx'], c['cy'], c['r'])
        cylinder(f"poteau-{c['id']}", cx, cy, r, bas, top, 'Coque', M_POTEAU)

    # ---- facades: glass between steel mullions (the mullions measured on the plan)
    def facade(name, x, montants, ep=4.5):
        for k, (y0, y1) in enumerate(zip(montants, montants[1:])):
            box(f'{name}-verre-{k}', x - 1.2, y0, x + 1.2, y1, bas, top, 'Vitrages', M_VERRE)
        for k, y in enumerate(montants):
            box(f'{name}-montant-{k}', x - ep, y - 3, x + ep, y + 3, bas, top, 'Vitrages', M_CADRE)
        if bas == 0.0:
            box(f'{name}-seuil', x - ep, montants[0], x + ep, montants[-1], 0.0, 0.06, 'Vitrages', M_CADRE)
    facade('facade-gauche', 417.5, [145, 281.5, 421, 560, 656, 750])
    facade('facade-droite-a', 1450.5, [637, 741])
    facade('facade-droite-b', 1450.5, [851, 862, 972, 1094])
    facade('facade-droite-c', 1450.5, [1169, 1263.5, 1360, 1453])
    facade('facade-droite-d', 1450.5, [1579, 1692, 1822.5, 1952, 2082.5, 2210])
    # the double-height facade over the void: its upper part, from the slab level down to the ground floor's
    facade('facade-vide', 238.5, [1172 + (2245 - 1172) * k / 9 for k in range(10)])

    # ---- glass parapets on the edges of the void (1.05 m, 2 cm glass in a thin steel shoe)
    if bas < 1.05:
        bord = [(237, 1176)] + [(1008, 1176)] + arc(1012, 1242, 66, -90, 0, 14)[1:] + [(1078, 1917)] + \
            arc(1020, 1917, 58, 0, 90, 12)[1:] + [(998, 1986), (857, 2040), (857, 1896)]
        mur_suivant('garde-corps-vide', bord, max(bas, 0.0), min(top, 1.05), 2.4, 'Vitrages', M_VERRE)
        mur_suivant('garde-corps-vide-sabot', bord, max(bas, 0.0), min(top, 0.06), 6, 'Vitrages', M_CADRE)
        # round the stair opening where the slab borders it, open at the arrival (the stair ends at -18 deg)
        pts = []
        for a in range(-200, 160, 2):
            x, y = HX + (R_ESC + 4) * math.cos(math.radians(a)), HY + (R_ESC + 4) * math.sin(math.radians(a))
            sur_dalle = dans((x, y), SOL) and not dans((x, y), VIDE) and not dans((x, y), JARDIN)
            if sur_dalle and not (-40 <= a <= 12):
                pts.append((x, y))
            elif len(pts) > 1:
                mur_suivant(f'garde-corps-escalier-{a}', pts, max(bas, 0.0), min(top, 1.05), 2.4, 'Vitrages', M_VERRE)
                pts = []
            else:
                pts = []
        if len(pts) > 1:
            mur_suivant('garde-corps-escalier-fin', pts, max(bas, 0.0), min(top, 1.05), 2.4, 'Vitrages', M_VERRE)

    # ---- the two half drums of the booths on the right (open to the room, the round side against the facade)
    for k, cy in enumerate((770, 1031)):
        cx = 1298.5
        zt = min(2.2, top)
        if bas < zt:
            ring(f'demi-tambour-{k}', cx, cy, 125, 110, -90, 90, bas, zt, 'Tambours', M_TAMBOUR)
            for s in (-1, 1):
                box(f'demi-tambour-{k}-retour{s}', 1281, cy + s * 110 if s > 0 else cy - 125, cx,
                    cy + s * 125 if s > 0 else cy - 110, bas, zt, 'Tambours', M_TAMBOUR)

    # ---- the stair up (to the roof floor): 8 treads of 35 px rising 0.18 m towards +x, a landing on the left
    x0, y0, x1, y1 = ESCALIER_HAUT
    for k in range(8):
        z = 0.18 * (k + 1)
        if z - 0.05 < bas or z - 0.05 > top:
            continue
        box(f'marche-haut-{k}', 572 + 35 * k, y0 + 2, 572 + 35 * (k + 1) + 1, y1 - 2, max(bas, 0.0), z, 'Escalier', M_MARCHE)

    # ---- the top of the spiral stair, coming up from the ground floor through its opening (floor1.py: 19 risers of
    #      H_RDC/19, 21 deg each from -55.5 deg; the last one lands at -18 deg, the DN mark of the plan)
    if bas == 0.0:
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


setup_render()
centre = P(873, 1227)
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
if ARGS.get('save'):
    bpy.ops.wm.save_as_mainfile(filepath=ARGS['save'])
