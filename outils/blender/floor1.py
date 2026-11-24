# Floor1 (ground floor) of the restaurant: the plan laid on the ground at real scale and the shell
# modelled over it (walls, columns, glazing, booth drums, spiral stair, floors).
# The script is the source: the .blend is regenerated, never saved by hand.
#
# usage: blender -b -P floor1.py -- [vue=dessus,iso,coupe,entree] [coupe=1.2] [plan=1] [ech=100]
#                                    [save=<file.blend>] [rendu=1] [out=<dossier>]
import bpy, bmesh, json, math, sys
from pathlib import Path
from mathutils import Vector

ICI = Path(__file__).resolve().parent
RACINE = ICI.parents[1]
ARGS = dict(a.split('=', 1) for a in (sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []) if '=' in a)
VUES = ARGS.get('vue', 'dessus,iso,coupe,entree').split(',')
ECH = int(ARGS.get('ech', 100))
OUT = Path(ARGS.get('out', RACINE / 'rendus' / '1-coque'))

DATA = json.loads((RACINE / 'modele' / 'floor1-murs.json').read_text())
PX = 1 / DATA['echelle_px_par_m']        # metres per plan pixel (120 px = 1 m, see analyse/)
CX, CY = 837, 1230                       # plan pixel placed at the world origin
H = 3.35                                 # ground floor storey height (floor to the mezzanine slab), from the section


def P(x, y, z=0.0):
    return Vector(((x - CX) * PX, -(y - CY) * PX, z))


# ---------------------------------------------------------------- scene
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
for c in ('Plan', 'Coque', 'Sols', 'Vitrages', 'Tambours', 'Escalier'):
    sc.collection.children.link(bpy.data.collections.new(c))


def coll(name):
    return bpy.data.collections[name]


def mat(name, rgb, rough=0.6, alpha=1.0, transmission=0.0, emit=None):
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


M_MUR = mat('mur', (0.82, 0.81, 0.79), 0.75)
M_TETE = mat('tete-de-mur', (0.93, 0.92, 0.90), 0.8)
M_SOL_SOMBRE = mat('sol-sombre', (0.20, 0.20, 0.21), 0.55)
M_SOL_CLAIR = mat('sol-clair', (0.55, 0.55, 0.54), 0.5)
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


def ring(name, cx, cy, r_out, r_in, a0, a1, z0, z1, collection, material, seg=96, cap=False):
    """Ring sector between image angles a0 -> a1 (degrees, y down), r in plan pixels."""
    bm = bmesh.new()
    full = abs(a1 - a0) >= 359.9
    n = seg if full else max(8, int(seg * abs(a1 - a0) / 360))
    pts = []
    for k in range(n + (0 if full else 1)):
        a = math.radians(a0 + (a1 - a0) * k / n)
        pts.append((math.cos(a), math.sin(a)))
    def v(r, c, z):
        return bm.verts.new(P(cx + r * c[0], cy + r * c[1], z))
    lo_o = [v(r_out, c, z0) for c in pts]; hi_o = [v(r_out, c, z1) for c in pts]
    lo_i = [v(r_in, c, z0) for c in pts]; hi_i = [v(r_in, c, z1) for c in pts]
    m = len(pts)
    rng = range(m) if full else range(m - 1)
    for k in rng:
        j = (k + 1) % m
        bm.faces.new((lo_o[k], lo_o[j], hi_o[j], hi_o[k])).smooth = True
        bm.faces.new((lo_i[j], lo_i[k], hi_i[k], hi_i[j])).smooth = True
        bm.faces.new((hi_o[k], hi_o[j], hi_i[j], hi_i[k]))
        bm.faces.new((lo_i[k], lo_i[j], lo_o[j], lo_o[k]))
    if not full:
        for k in (0, m - 1):
            bm.faces.new((lo_o[k], lo_i[k], hi_i[k], hi_o[k]))
    if cap and full:
        bm.faces.new(list(reversed(hi_i)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    return obj(name, me, collection, material)


def helix_band(name, cx, cy, r_out, r_in, a0, a1, dz_per_deg, top, depth=0.28, seg=200):
    """Outer stringer of the spiral stair: a band that rises with the treads."""
    bm = bmesh.new()
    rows = []
    for k in range(seg + 1):
        a = a0 + (a1 - a0) * k / seg
        z = (a - a0) * dz_per_deg
        if z - depth > top:
            break
        c, s_ = math.cos(math.radians(a)), math.sin(math.radians(a))
        zt = min(z + 0.05, top)
        zb = max(min(z - depth, top), 0.0)
        rows.append([bm.verts.new(P(cx + r * c, cy + r * s_, zz)) for r, zz in
                     ((r_out, zb), (r_out, zt), (r_in, zt), (r_in, zb))])
    for k in range(len(rows) - 1):
        A, B = rows[k], rows[k + 1]
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((A[i], B[i], B[j], A[j]))
    if rows:
        bm.faces.new(rows[0]); bm.faces.new(list(reversed(rows[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    for p_ in me.polygons:
        p_.use_smooth = abs(p_.normal.z) < 0.5
    return obj(name, me, 'Escalier', M_MARCHE)


def cylinder(name, cx, cy, r, z0, z1, collection, material, seg=64):
    bm = bmesh.new()
    lo = [bm.verts.new(P(cx + r * math.cos(2 * math.pi * k / seg), cy + r * math.sin(2 * math.pi * k / seg), z0)) for k in range(seg)]
    hi = [bm.verts.new(P(cx + r * math.cos(2 * math.pi * k / seg), cy + r * math.sin(2 * math.pi * k / seg), z1)) for k in range(seg)]
    for k in range(seg):
        j = (k + 1) % seg
        f = bm.faces.new((lo[k], lo[j], hi[j], hi[k])); f.smooth = True
    bm.faces.new(list(reversed(lo))); bm.faces.new(hi)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    return obj(name, me, collection, material)


def build(cut):
    """Shell of floor1. cut = height at which walls are cut (None = full storey height)."""
    top = H if cut is None else cut

    # ---- the plan on the ground (calibration image, 1 px = 1/120 m)
    W, Hh = DATA['taille']
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
    tex.image = bpy.data.images.load(str(RACINE / DATA['image']))
    tex.interpolation = 'Cubic'
    nt.links.new(tex.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.9
    obj('plan', me, 'Plan', m)

    # ---- floors (raised 1 cm over the plan; hidden in the calibration view)
    sol = [(385, 146), (1418, 146), (1418, 283), (1473, 283), (1473, 2410), (575, 2410), (575, 2275),
           (201, 2275), (201, 728), (385, 728)]
    extrude_loops('sol', [sol], -0.05, 0.0, 'Sols', M_SOL_SOMBRE)
    extrude_loops('sol-clair', [[(231, 728), (857, 728), (857, 1894), (604, 1894), (604, 2275), (231, 2275)]],
                  0.0, 0.004, 'Sols', M_SOL_CLAIR)
    extrude_loops('gravier', [[(855, 2040), (960, 2060), (1040, 2100), (1082, 2172), (1262, 2172), (1273, 2368),
                               (855, 2368)]], 0.0, 0.03, 'Sols', M_GRAVIER)

    # ---- walls (vectorised from the plan, see outils/vectoriser.py)
    for k, mu in enumerate(DATA['murs']):
        o = extrude_loops(f"mur-{mu['id']}-{k}", [mu['contour']] + mu['trous'], 0.0, top, 'Coque', M_MUR)

    # ---- columns: two in the street facades (dia 1.1 m), two on the inner grid (dia 0.8 m)
    for p in DATA['poteaux']:
        cx, cy, r = p['cx'], p['cy'], p['r']
        if p['id'] == 41:                       # half hidden in the corner pier: same column as 257
            cx, r = 405.1, 49.2
        cylinder(f"poteau-{p['id']}", cx, cy, r, 0.0, top, 'Coque', M_POTEAU)

    # ---- glazed facades: glass + black frame, mullions about every 1.2 m
    def facade(name, x, y0, y1, x_ep=3.0):
        n = max(1, round((y1 - y0) * PX / 1.2))
        box(name + '-verre', x - 1.2, y0, x + 1.2, y1, 0.0, top, 'Vitrages', M_VERRE)
        for k in range(n + 1):
            y = y0 + (y1 - y0) * k / n
            box(f'{name}-montant-{k}', x - x_ep, y - 3, x + x_ep, y + 3, 0.0, top, 'Vitrages', M_CADRE)
        box(name + '-seuil', x - x_ep, y0, x + x_ep, y1, 0.0, 0.06, 'Vitrages', M_CADRE)
        if cut is None:
            box(name + '-imposte', x - x_ep, y0, x + x_ep, y1, top - 0.08, top, 'Vitrages', M_CADRE)

    facade('facade-gauche-haut', 382, 150, 723)
    facade('facade-gauche-a', 224, 848, 1117)
    facade('facade-gauche-b', 224, 1211, 2170)
    facade('facade-droite', 1452, 870, 1450)
    facade('facade-droite-b', 1452, 1583, 2230)
    facade('facade-droite-haut', 1452, 737, 740)
    box('entree-verre', 1068, 2404, 1308, 2409, 0.0, top, 'Vitrages', M_VERRE)
    box('entree-cadre', 1068, 2402, 1308, 2411, 0.0, 0.06, 'Vitrages', M_CADRE)

    # ---- booth drums: a tall dark cylinder. Low part (0 - 2.2 m) = half shell open to the room,
    #      with short straight returns; high part (2.2 - 3.0 m) = full ring, closed on top (seen from floor2)
    for t in DATA['tambours']:
        cx, cy = t['cx'], t['cy']
        r_out, r_in = 152, 131
        h_bas, h_haut = 2.2, 3.0
        zt = min(h_bas, top)
        ring(f"tambour-{t['id']}-bas", cx, cy, r_out, r_in, 90, 270, 0.0, zt, 'Tambours', M_TAMBOUR)
        for s in (-1, 1):                       # straight returns to x = 444
            box(f"tambour-{t['id']}-retour{s}", cx, cy + s * r_in, 444, cy + s * r_out, 0.0, zt, 'Tambours', M_TAMBOUR)
        if top > h_bas:
            ring(f"tambour-{t['id']}-haut", cx, cy, r_out, r_in, 0, 360, h_bas, min(h_haut, top), 'Tambours',
                 M_TAMBOUR, cap=(cut is None))

    # ---- spiral stair: hub (1082, 2172), treads from r 40 to 180 px, first riser at -55.5 deg,
    #      clockwise in plan; 19 risers of 0.176 m and 21 deg: the stair turns about 400 deg and arrives
    #      at -18 deg on floor2 (the DN mark of floor2.png), which confirms the count
    cx, cy, r0, r1 = 1082, 2172, 40, 180
    n, step_a, rise = 19, 21.0, H / 19
    a = -55.5
    for k in range(n - 1):
        z = rise * (k + 1)
        if z - rise > top:
            break
        ring(f'marche-{k:02d}', cx, cy, r1, r0, a + k * step_a, a + (k + 1) * step_a + 1.5, z - 0.05, z, 'Escalier',
             M_MARCHE, seg=120)
    helix_band('limon', cx, cy, r1 + 5, r1, a, a + (n - 1) * step_a, rise / step_a, top)
    cylinder('fut', cx, cy, r0, 0.0, min(H, top), 'Escalier', M_MARCHE)

    # curves -> meshes (cleaner for the later line styles)
    for o in list(bpy.data.objects):
        if o.type == 'CURVE':
            o.select_set(True)
    bpy.context.view_layer.objects.active = next((o for o in bpy.data.objects if o.type == 'CURVE'), None)
    if bpy.context.view_layer.objects.active:
        bpy.ops.object.convert(target='MESH')


# ---------------------------------------------------------------- light, render
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
    d = Vector(target) - Vector(loc)
    co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
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

if 'dessus' in VUES or 'iso' in VUES or 'entree' in VUES:
    build(None)
    if 'dessus' in VUES:
        # calibration: plan + walls seen from above, floors hidden so the drawing shows through
        show(collections_hidden=('Sols', 'Escalier'))
        bpy.data.objects['soleil'].rotation_euler = (0, 0, 0)
        for o in bpy.data.objects:
            if o.name.endswith('-haut'):
                o.hide_render = True
        cam = camera('cam-dessus', centre + Vector((0, 0, 60)), centre, ortho=21.0)
        render('1-calage-vue-de-dessus', cam, (1500, 2000))
    for o in bpy.data.objects:
        o.hide_render = False
    if 'iso' in VUES:
        bpy.data.objects['soleil'].rotation_euler = (math.radians(38), 0, math.radians(-38))
        show(collections_hidden=('Plan',))
        d = Vector((-1, -1.05, 1.15)).normalized()
        cam = camera('cam-iso', centre + d * 60, centre, ortho=24.5)
        render('2-coque-axonometrie', cam, (2000, 1500))
    if 'entree' in VUES:
        bpy.data.objects['soleil'].rotation_euler = (math.radians(38), 0, math.radians(-38))
        show(collections_hidden=('Plan',))
        cam = camera('cam-fond', P(1500, 250, 9.5), P(640, 1750, 0.4), lens=26)
        render('4-coque-depuis-le-bar', cam, (2000, 1333))
    if ARGS.get('save'):
        bpy.ops.wm.save_as_mainfile(filepath=ARGS['save'])

STYLES = {
    # name: (walls, wall caps, dark floor, light floor, gravel, drums, columns, treads, world, world strength, lines)
    'trait': ((0.96,) * 3, (0.99,) * 3, (0.90,) * 3, (0.94,) * 3, (0.86,) * 3, (0.80,) * 3, (0.97,) * 3,
              (0.70,) * 3, (0.97, 0.965, 0.955), 1.0, (0.05, 0.05, 0.05)),
    'trait-sombre': ((0.10,) * 3, (0.12,) * 3, (0.045,) * 3, (0.07,) * 3, (0.06,) * 3, (0.03,) * 3, (0.12,) * 3,
                     (0.06,) * 3, (0.025, 0.026, 0.03), 0.6, (0.80, 0.80, 0.80)),
    'maquette': ((0.86, 0.85, 0.83), (0.92, 0.91, 0.89), (0.62, 0.50, 0.36), (0.70, 0.58, 0.43), (0.80, 0.79, 0.77),
                 (0.46, 0.33, 0.22), (0.88, 0.87, 0.85), (0.50, 0.38, 0.26), (0.80, 0.80, 0.79), 0.75, None),
    'jeu': ((0.92, 0.86, 0.77), (0.97, 0.93, 0.86), (0.22, 0.30, 0.27), (0.70, 0.46, 0.28), (0.55, 0.53, 0.50),
            (0.14, 0.32, 0.28), (0.93, 0.88, 0.80), (0.20, 0.20, 0.22), (0.93, 0.80, 0.66), 0.8, None),
}


def apply_style(name):
    st = STYLES[name]
    pairs = (('mur', 0), ('tete-de-mur', 1), ('sol-sombre', 2), ('sol-clair', 3), ('gravier', 4), ('tambour', 5),
             ('poteau', 6), ('marche', 7))
    for mname, k in pairs:
        b = next(n for n in bpy.data.materials[mname].node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        b.inputs['Base Color'].default_value = (*st[k], 1)
        b.inputs['Roughness'].default_value = 0.85 if name != 'jeu' else 0.6
    bv = next(n for n in bpy.data.materials['verre'].node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bc = next(n for n in bpy.data.materials['cadre'].node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    if name == 'trait':
        bv.inputs['Base Color'].default_value = (0.97, 0.98, 0.99, 1); bv.inputs['Roughness'].default_value = 0.35
        bc.inputs['Base Color'].default_value = (0.85, 0.85, 0.85, 1)
    if name == 'trait-sombre':
        bv.inputs['Base Color'].default_value = (0.2, 0.25, 0.3, 1)
    if name == 'maquette':                      # the model on its board, like an architect's model
        sol = bpy.data.objects['sol']
        mn = [min(v.co[i] for v in sol.data.vertices) for i in range(2)]
        mx = [max(v.co[i] for v in sol.data.vertices) for i in range(2)]
        bm_ = bmesh.new()
        bmesh.ops.create_cube(bm_, size=1)
        me_ = bpy.data.meshes.new('socle'); bm_.to_mesh(me_); bm_.free()
        so_ = obj('socle', me_, 'Sols', mat('socle', (0.93, 0.92, 0.90), 0.9))
        so_.scale = (mx[0] - mn[0] + 1.6, mx[1] - mn[1] + 1.6, 0.3)
        so_.location = ((mx[0] + mn[0]) / 2, (mx[1] + mn[1]) / 2, -0.2)
    bg = sc.world.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (*st[8], 1)
    bg.inputs['Strength'].default_value = st[9]
    sun = bpy.data.objects['soleil']
    sun.rotation_euler = (math.radians(32), 0, math.radians(-30))
    sun.data.energy = {'trait': 1.2, 'trait-sombre': 0.9, 'maquette': 3.2, 'jeu': 3.0}[name]
    sun.data.angle = math.radians({'trait': 30, 'trait-sombre': 30, 'maquette': 8, 'jeu': 14}[name])
    if name == 'jeu':
        sun.data.color = (1.0, 0.93, 0.82)
        for o in bpy.data.objects:
            if o.type == 'MESH' and o.users_collection[0].name in ('Coque', 'Tambours'):
                mod = o.modifiers.new('biseau', 'BEVEL'); mod.width = 0.025; mod.segments = 3
                mod.limit_method = 'ANGLE'
    sc.view_settings.view_transform = 'Standard' if name.startswith('trait') else 'AgX'
    sc.view_settings.look = 'None' if name.startswith('trait') else 'AgX - Medium High Contrast'
    if st[10] is not None:
        sc.render.use_freestyle = True
        sc.render.line_thickness_mode = 'ABSOLUTE'
        sc.render.line_thickness = 1.0
        vl = sc.view_layers[0]
        vl.use_freestyle = True
        fs = vl.freestyle_settings
        fs.crease_angle = math.radians(140)
        ls = fs.linesets[0] if len(fs.linesets) else fs.linesets.new('lignes')
        ls.select_by_visibility = True
        ls.select_silhouette = ls.select_border = ls.select_crease = True
        if ls.linestyle is None:
            ls.linestyle = bpy.data.linestyles.new('trait')
        ls.linestyle.color = st[10]
        ls.linestyle.thickness = 1.4


if 'coupe' in VUES:
    for o in list(bpy.data.objects):
        if o.type != 'CAMERA' and o.type != 'LIGHT':
            bpy.data.objects.remove(o)
    build(float(ARGS.get('coupe', 1.2)))
    if ARGS.get('debug'):
        for o in bpy.data.objects:
            if o.type == 'MESH':
                print('DBG', o.name, tuple(round(v, 2) for v in o.dimensions), round(o.location.z, 2))
        raise SystemExit
    # walls cut at 1.2 m over the plan: the "map" reading, floors hidden so the drawing shows
    d = Vector((-1, -1.05, 1.15)).normalized()
    cam = camera('cam-coupe', centre + d * 60, centre, ortho=24.5)
    if ARGS.get('style'):
        apply_style(ARGS['style'])
        show(collections_hidden=('Plan',))
        render(f"style-{ARGS['style']}", cam, (2000, 1500))
    else:
        show(collections_hidden=('Sols',))
        render('3-coque-coupee-sur-le-plan', cam, (2000, 1500))
