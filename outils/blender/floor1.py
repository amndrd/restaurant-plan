# Floor1 (ground floor) of the restaurant: the plan laid on the ground at real scale and the shell
# modelled over it (walls, columns, glazing, booth drums, spiral stair, floors).
# The script is the source: the .blend is regenerated, never saved by hand.
#
# usage: blender -b -P floor1.py -- [vue=dessus,iso,coupe,entree] [coupe=1.2] [plan=1] [ech=100]
#                                    [save=<file.blend>] [rendu=1] [out=<dossier>]
#        blender -b -P floor1.py -- variante=blanc|blanc-grille|fantome|transparent|fil-de-fer [samples=96]
#            (step 2: the white styles, each rendered in the two views of the map, top and 3D)
import bpy, bmesh, json, math, sys
from pathlib import Path
from mathutils import Vector

ICI = Path(__file__).resolve().parent
RACINE = ICI.parents[1]
ARGS = dict(a.split('=', 1) for a in (sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []) if '=' in a)
VUES = ARGS.get('vue', '' if 'variante' in ARGS else 'dessus,iso,coupe,entree').split(',')
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


def helix_band(name, cx, cy, r_out, r_in, a0, a1, dz_per_deg, top, depth=0.28, seg=200, bas=0.0):
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
        zb = max(min(z - depth, top), bas)
        if zt <= bas:
            continue
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


def build(cut, bas=0.0):
    """Shell of floor1. cut = height at which walls are cut (None = full storey height).
    bas = height the walls start from (0 = the floor; above 0 only the upper part is built, no plan, no floors)."""
    top = H if cut is None else cut
    if bas == 0.0:
        build_sols()
    build_coque(cut, top, bas)


def build_sols():

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


def build_coque(cut, top, bas):
    # ---- walls (vectorised from the plan, see outils/vectoriser.py)
    for k, mu in enumerate(DATA['murs']):
        o = extrude_loops(f"mur-{mu['id']}-{k}", [mu['contour']] + mu['trous'], bas, top, 'Coque', M_MUR)

    # ---- columns: two in the street facades (dia 1.1 m), two on the inner grid (dia 0.8 m)
    for p in DATA['poteaux']:
        cx, cy, r = p['cx'], p['cy'], p['r']
        if p['id'] == 41:                       # half hidden in the corner pier: same column as 257
            cx, r = 405.1, 49.2
        cylinder(f"poteau-{p['id']}", cx, cy, r, bas, top, 'Coque', M_POTEAU)

    # ---- glazed facades: glass + black frame, mullions about every 1.2 m
    def facade(name, x, y0, y1, x_ep=3.0):
        n = max(1, round((y1 - y0) * PX / 1.2))
        box(name + '-verre', x - 1.2, y0, x + 1.2, y1, bas, top, 'Vitrages', M_VERRE)
        for k in range(n + 1):
            y = y0 + (y1 - y0) * k / n
            box(f'{name}-montant-{k}', x - x_ep, y - 3, x + x_ep, y + 3, bas, top, 'Vitrages', M_CADRE)
        if bas == 0.0:
            box(name + '-seuil', x - x_ep, y0, x + x_ep, y1, 0.0, 0.06, 'Vitrages', M_CADRE)
        if cut is None:
            box(name + '-imposte', x - x_ep, y0, x + x_ep, y1, top - 0.08, top, 'Vitrages', M_CADRE)

    facade('facade-gauche-haut', 382, 150, 723)
    facade('facade-gauche-a', 224, 848, 1117)
    facade('facade-gauche-b', 224, 1211, 2170)
    facade('facade-droite', 1452, 870, 1450)
    facade('facade-droite-b', 1452, 1583, 2230)
    facade('facade-droite-haut', 1452, 737, 740)
    box('entree-verre', 1068, 2404, 1308, 2409, bas, top, 'Vitrages', M_VERRE)
    if bas == 0.0:
        box('entree-cadre', 1068, 2402, 1308, 2411, 0.0, 0.06, 'Vitrages', M_CADRE)

    # ---- booth drums: a tall dark cylinder. Low part (0 - 2.2 m) = half shell open to the room,
    #      with short straight returns; high part (2.2 - 3.0 m) = a full ring hung over the booth (photo 24).
    #      Left open on top, so the booths stay visible from above on the map
    for t in DATA['tambours']:
        cx, cy = t['cx'], t['cy']
        r_out, r_in = 152, 131
        h_bas, h_haut = 2.2, 3.0
        zt = min(h_bas, top)
        if bas < h_bas:
            ring(f"tambour-{t['id']}-bas", cx, cy, r_out, r_in, 90, 270, bas, zt, 'Tambours', M_TAMBOUR)
            for s in (-1, 1):                   # straight returns to x = 444
                box(f"tambour-{t['id']}-retour{s}", cx, cy + s * r_in, 444, cy + s * r_out, bas, zt, 'Tambours',
                    M_TAMBOUR)
        if top > h_bas:
            ring(f"tambour-{t['id']}-haut", cx, cy, r_out, r_in, 0, 360, max(h_bas, bas), min(h_haut, top),
                 'Tambours', M_TAMBOUR)

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
        if z - 0.05 < bas:
            continue
        ring(f'marche-{k:02d}', cx, cy, r1, r0, a + k * step_a, a + (k + 1) * step_a + 1.5, z - 0.05, z, 'Escalier',
             M_MARCHE, seg=120)
    helix_band('limon', cx, cy, r1 + 5, r1, a, a + (n - 1) * step_a, rise / step_a, top, bas=bas)
    cylinder('fut', cx, cy, r0, bas, min(H, top), 'Escalier', M_MARCHE)

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


# ---------------------------------------------------------------- step 2: the white styles, two views
# Each variant is rendered in the two views of the staff map: from the top (a plan, long side across the
# screen, entry on the right) and in 3D (the same corner as the axonometry, 16:10 like a tablet).
VARIANTES = {
    # cut: wall height of the solid model (None = full storey); grid: 1 m / 5 m grid on the ground and floors;
    # alpha: opacity of the walls, drums, stair; ghost: upper part of the walls above the cut, see-through;
    # hidden: colour of the hidden lines (seen through), None = not drawn
    'blanc':        dict(cut=1.2,  grid=False, alpha=1.0,  ghost=False, hidden=None),
    'blanc-grille': dict(cut=1.2,  grid=True,  alpha=1.0,  ghost=False, hidden=None),
    'fantome':      dict(cut=1.2,  grid=True,  alpha=1.0,  ghost=True,  hidden=(0.72,) * 3),
    'transparent':  dict(cut=None, grid=True,  alpha=0.42, ghost=False, hidden=(0.66,) * 3),
    'fil-de-fer':   dict(cut=None, grid=True,  alpha=0.03, ghost=False, hidden=(0.62,) * 3),
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


def ground(material):
    me = bpy.data.meshes.new('terrain'); bm_ = bmesh.new()
    bm_.faces.new([bm_.verts.new((x, y, -0.052)) for x, y in ((-200, -200), (200, -200), (200, 200), (-200, 200))])
    bm_.to_mesh(me); bm_.free()
    return obj('terrain', me, 'Sols', material)


def freestyle_lines(visible, hidden, thickness=1.0):
    sc.render.use_freestyle = True
    sc.render.line_thickness_mode = 'ABSOLUTE'
    sc.render.line_thickness = 1.0
    vl = sc.view_layers[0]
    vl.use_freestyle = True
    fs = vl.freestyle_settings
    fs.crease_angle = math.radians(140)
    sets = [('visibles', 'VISIBLE', visible, 1.15 * thickness)]
    if hidden:
        sets.append(('cachees', 'HIDDEN', hidden, 0.75 * thickness))
    for k, (nom, vis, col, ep) in enumerate(sets):
        ls = fs.linesets[k] if len(fs.linesets) > k else fs.linesets.new(nom)
        ls.select_by_visibility = True
        ls.visibility = vis
        ls.select_silhouette = ls.select_border = ls.select_crease = True
        ls.linestyle = bpy.data.linestyles.new(nom)
        ls.linestyle.color = col
        ls.linestyle.thickness = ep


if ARGS.get('variante'):
    nom = ARGS['variante']
    V = VARIANTES[nom]
    num = list(VARIANTES).index(nom) + 1
    OUT = Path(ARGS.get('out', RACINE / 'rendus' / '3-styles-blancs'))
    sc.collection.children.link(bpy.data.collections.new('Fantome'))

    build(V['cut'])
    if V['ghost']:                              # the walls above the cut, see-through
        avant = set(bpy.data.objects)
        build(None, bas=V['cut'] + 0.004)     # 4 mm gap: no face shared with the top of the solid walls
        m_ghost = mat('fantome', (0.98, 0.98, 0.98), 0.6, alpha=0.16)
        for o in set(bpy.data.objects) - avant:
            for c in o.users_collection:
                c.objects.unlink(o)
            coll('Fantome').objects.link(o)
            o.data.materials.clear(); o.data.materials.append(m_ghost)
            o.visible_shadow = False            # only the solid walls cast shadows: no grey smudges seen from above

    # materials: white, the floors a touch warmer than the walls, the ground a light grey
    a = V['alpha']
    for name, rgb in (('mur', (0.965,) * 3), ('tete-de-mur', (0.98,) * 3), ('poteau', (0.96,) * 3),
                      ('tambour', (0.93, 0.93, 0.925)), ('marche', (0.90,) * 3)):
        set_mat(name, rgb, 0.85, a)
    set_mat('cadre', (0.80,) * 3, 0.6, max(a, 0.25) if a < 1 else 1.0)
    set_mat('verre', (0.97, 0.98, 0.99), 0.3, 0.16 if a == 1.0 else min(a, 0.16))
    set_mat('gravier', (0.88, 0.875, 0.865), 0.95)
    o_c = P(837, 1278)
    if V['grid']:
        m_int = mat_grille('sol-grille', (0.975, 0.972, 0.965), (0.80, 0.80, 0.80), 0.35, 0.55, o_c)
        m_ext = mat_grille('terrain-grille', (0.90, 0.898, 0.89), (0.66, 0.66, 0.66), 0.45, 0.8, o_c, fade=(14, 30))
    else:
        m_int = mat('sol-blanc', (0.975, 0.972, 0.965), 0.9)
        m_ext = mat('terrain-blanc', (0.90, 0.898, 0.89), 0.9)
    for o_name in ('sol', 'sol-clair'):
        me_ = bpy.data.objects[o_name].data
        me_.materials.clear(); me_.materials.append(m_int)
    ground(m_ext)

    # light: soft sky + a soft sun; display in Standard so the whites stay white
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    bg = sc.world.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0.97, 0.965, 0.955, 1)
    bg.inputs['Strength'].default_value = 0.67        # sky + sun sized so the floor lands near 0.93, not clipped
    sun = bpy.data.objects['soleil']
    sun.data.energy = 1.25
    sun.data.angle = math.radians(25)
    sc.cycles.transparent_max_bounces = 24
    freestyle_lines((0.30, 0.30, 0.30), V['hidden'], 1.25 if nom == 'fil-de-fer' else 1.0)
    show(collections_hidden=('Plan',))

    # one sun fixed in the world for both views, as in the live map: high, from the left of the 3D camera
    sun.rotation_euler = (math.radians(35), 0, math.radians(-121))

    # top view: straight down, the long side across the screen (screen up = +x, entry on the right)
    cam_top = camera('cam-dessus', o_c + Vector((0, 0, 60)), o_c, ortho=21.6)
    cam_top.rotation_euler = (0, 0, math.radians(-90))
    # 3D view: the corner of the axonometry
    d = Vector((-1, -1.05, 1.15)).normalized()
    c3 = o_c + Vector((0, 0, 0.9))
    cam_3d = camera('cam-3d', c3 + d * 60, c3, ortho=25.5)

    if ARGS.get('transition'):
        # the switch from the top view to the 3D view: rotation slerped, scale and target eased
        q0 = cam_top.rotation_euler.to_quaternion(); q1 = cam_3d.rotation_euler.to_quaternion()
        n_img = int(ARGS.get('images', 48))
        dossier = OUT / f'transition-{nom}'
        sc.render.resolution_x, sc.render.resolution_y = 1600, 1000
        sc.render.resolution_percentage = 100
        sc.camera = cam_top
        for k in range(n_img + 1):
            t = k / n_img
            e = t * t * (3 - 2 * t)
            q = q0.slerp(q1, e)
            cible = o_c.lerp(c3, e)
            cam_top.rotation_euler = q.to_euler()
            cam_top.location = cible - (q @ Vector((0, 0, -1))) * 60
            cam_top.data.ortho_scale = 21.6 + (25.5 - 21.6) * e
            sc.render.filepath = str(dossier / f'{k:03d}.png')
            bpy.ops.render.render(write_still=True)
            print('image', k)
    else:
        render(f'{num}-{nom}-dessus', cam_top, (2000, 1250))
        render(f'{num}-{nom}-3d', cam_3d, (2000, 1250))
    if ARGS.get('save'):
        bpy.ops.wm.save_as_mainfile(filepath=ARGS['save'])
