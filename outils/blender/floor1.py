# Floor1 (ground floor) of the restaurant: the plan laid on the ground at real scale and the shell
# modelled over it (walls, columns, glazing, booth drums, spiral stair, floors).
# The script is the source: the .blend is regenerated, never saved by hand.
#
# usage: blender -b -P floor1.py -- [vue=dessus,iso,coupe,entree] [coupe=1.2] [plan=1] [ech=100]
#                                    [save=<file.blend>] [rendu=1] [out=<dossier>]
#        blender -b -P floor1.py -- variante=blanc|blanc-grille|fantome|transparent|fil-de-fer [samples=96]
#            (step 2: the white styles, each rendered in the two views of the map, top and 3D)
#        blender -b -P floor1.py -- variante=fantome elements=1 [plans=bar,banquette,escalier,facade,rideau]
#            (step 3: the fixed elements modelled from the photos: bar, booths, stair, glass blocks,
#             rock garden, concierge desk, curtains; plans = close-ups in the solid white model)
#        blender -b -P floor1.py -- variante=fantome mobilier=1 [plans=salle,tabourets,tambour]
#            (step 4: the furniture of the plan, over the fixed elements; also writes modele/floor1-tables.json)
#        blender -b -P floor1.py -- variante=fantome|fil-de-fer mobilier=1 export=carte/modele/floor1-<x>.glb
#            (step 6: the banquette by the bar replaces the standing tables; plans=zone for its close-up)
#            (step 5: the model for the interactive map, in glTF; each object carries its role and its table number)
import bpy, bmesh, json, math, random, sys
from pathlib import Path
from mathutils import Matrix, Vector

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
MOBILIER = ARGS.get('mobilier') == '1'   # step 4: the furniture (tables, chairs, stools, planters, pendants)
ELEMENTS = ARGS.get('elements') == '1' or MOBILIER   # step 3: fixed elements (glass blocks, stair, bar, booths...)


def P(x, y, z=0.0):
    return Vector(((x - CX) * PX, -(y - CY) * PX, z))


# ---------------------------------------------------------------- scene
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
for c in ('Plan', 'Coque', 'Sols', 'Vitrages', 'Traits-fins', 'Tambours', 'Escalier'):
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


# the rock garden at the foot of the stair; with the detailed stair it goes round the core (r 42 px)
GRAVIER_HAUT = [(855, 2040), (912, 2046), (960, 2060), (1003, 2078), (1040, 2100)]
GRAVIER = GRAVIER_HAUT + [(1082, 2172), (1262, 2172), (1273, 2368), (855, 2368)]
if ELEMENTS:
    GRAVIER = GRAVIER_HAUT + [(1082 + 42 * math.cos(math.radians(a)), 2172 + 42 * math.sin(math.radians(a)))
                              for a in range(240, -1, -15)] + [(1262, 2172), (1273, 2368), (855, 2368)]


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
    extrude_loops('gravier', [GRAVIER], 0.0, 0.03, 'Sols', M_GRAVIER)


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
        if ELEMENTS and bas == 0.0:             # glass blocks (photos 2, 8, 9, 37) in deeper steel frames;
            x_ep = 5.0                          # above the map cut (bas > 0) a plain see-through pane is lighter
            paves(name, 'y', x, [(y0 + (y1 - y0) * k / n + 3, y0 + (y1 - y0) * (k + 1) / n - 3) for k in range(n)],
                  bas, top)
        else:
            box(name + '-verre', x - 1.2, y0, x + 1.2, y1, bas, top, 'Vitrages', M_VERRE)
        m_bas = max(bas, 0.06) if ELEMENTS else bas
        m_top = top - 0.08 if (ELEMENTS and cut is None) else top
        for k in range(n + 1):
            y = y0 + (y1 - y0) * k / n
            box(f'{name}-montant-{k}', x - x_ep, y - 3, x + x_ep, y + 3, m_bas, m_top, 'Vitrages', M_CADRE)
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
    if ELEMENTS and bas == 0.0:
        paves('entree', 'x', 2406.5, [(1068 + 3, 1308 - 3)], bas, top)
    else:
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
    for k in range(0 if ELEMENTS else n - 1):  # step 3: replaced by the detailed stair (escalier_detail)
        z = rise * (k + 1)
        if z - rise > top:
            break
        if z - 0.05 < bas:
            continue
        ring(f'marche-{k:02d}', cx, cy, r1, r0, a + k * step_a, a + (k + 1) * step_a + 1.5, z - 0.05, z, 'Escalier',
             M_MARCHE, seg=120)
    if not ELEMENTS:
        helix_band('limon', cx, cy, r1 + 5, r1, a, a + (n - 1) * step_a, rise / step_a, top, bas=bas)
        cylinder('fut', cx, cy, r0, bas, min(H, top), 'Escalier', M_MARCHE)

    # curves -> meshes (cleaner for the later line styles)
    for o in list(bpy.data.objects):
        if o.type == 'CURVE':
            o.select_set(True)
    bpy.context.view_layer.objects.active = next((o for o in bpy.data.objects if o.type == 'CURVE'), None)
    if bpy.context.view_layer.objects.active:
        bpy.ops.object.convert(target='MESH')



# ---------------------------------------------------------------- step 3: the fixed elements, from the photos
# Built at full height as closed meshes (world metres, identity transforms); the map styles cut them afterwards
# at the plan height (separer): the solid part below, the see-through part above.
M_BANQUETTE = mat('banquette', (0.11, 0.10, 0.09), 0.6)
M_PIERRE = mat('pierre', (0.20, 0.19, 0.18), 0.95)
M_COMPTOIR = mat('comptoir', (0.05, 0.05, 0.05), 0.3)
M_MEUBLE = mat('meuble', (0.09, 0.085, 0.08), 0.5)
M_PAVE = mat('pave', (0.80, 0.84, 0.85), 0.15, transmission=0.9)
M_MIROIR = mat('miroir', (0.92, 0.92, 0.92), 0.05)
M_ROCHER = mat('rocher', (0.24, 0.24, 0.23), 0.9)
M_RIDEAU = mat('rideau', (0.07, 0.07, 0.07), 0.8)
M_BORDURE = mat('bordure', (0.10, 0.10, 0.10), 0.5)


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
    relief(M_PIERRE, 18, 0.7)                   # the lava stone band of the booths (photos 17, 23)
    relief(M_GRAVIER, 90, 0.45)


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


def blocs(bm, axe, d0, d1, u0, u1, z0, z1, pas_u=0.2, pas_z=0.2, bas=0.0, top=99.0, joint=0.012):
    """A grid of glass blocks: axe 'y' = wall plane x in [d0, d1] running along y in [u0, u1] (px),
    axe 'x' = wall plane y in [d0, d1] running along x. Heights z0 - z1, blocks clipped to [bas, top]."""
    cols = max(1, round((u1 - u0) * PX / pas_u)); pu = (u1 - u0) / cols
    rows = max(1, round((z1 - z0) / pas_z)); pz = (z1 - z0) / rows
    j = joint / 2
    for i in range(cols):
        a, b = u0 + i * pu + j / PX, u0 + (i + 1) * pu - j / PX
        for r in range(rows):
            za, zb = max(z0 + r * pz + j, bas), min(z0 + (r + 1) * pz - j, top)
            if zb - za < 0.004:
                continue
            if axe == 'y':
                bm_box(bm, d0, a, d1, b, za, zb)
            else:
                bm_box(bm, a, d0, b, d1, za, zb)


def paves(name, axe, c, travees, bas, top, ep=4.0):
    """Glass block facade panels between the mullions (photos 2, 8, 9, 37): blocks of about 0.2 m,
    from the sill (0.06 m) to the head of the frame (H - 0.08), clipped to [bas, top]."""
    bm = bmesh.new()
    for u0, u1 in travees:
        if u1 - u0 > 6:
            blocs(bm, axe, c - ep, c + ep, u0, u1, 0.06, H - 0.08, bas=bas, top=top)
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


# ---- the bar (photos 6, 11, 25; plan zone 5): a counter 6.5 m long, the customer top at 1.08 m over a front of
#      ribbed glass cells, the bartender's working shelf at 0.90 m behind; the back bar against the toilets block:
#      two tall units, the base cabinet, two lit display steps for the decanters, a band of glass cells, a canopy
def bar():
    bm = bmesh.new()
    bm_box(bm, 420, 630, 1183, 730, 0.0, 0.10)          # recessed plinth
    bm_box(bm, 413, 623, 1190, 737, 0.10, 0.86)         # body
    bm_box(bm, 413, 683, 1190, 737, 0.86, 1.03)         # upstand under the customer top
    mesh_obj('bar-corps', bm, 'Bar', M_MEUBLE)
    bm = bmesh.new()
    bm_box(bm, 413, 623, 1190, 683, 0.86, 0.90)         # bartender's working shelf (the light band of the plan)
    bm_box(bm, 409, 680, 1194, 752, 1.03, 1.08)         # customer top (the dark band of the plan)
    mesh_obj('bar-plateaux', bm, 'Bar', M_COMPTOIR)
    bm = bmesh.new()
    blocs(bm, 'x', 737.5, 745, 413, 1190, 0.10, 1.02, pas_u=0.2, pas_z=0.23)
    mesh_obj('bar-facade-verre', bm, 'Traits-fins', M_PAVE)
    # back bar
    bm = bmesh.new()
    bm_box(bm, 565, 422, 625, 488, 0.0, 2.196)          # tall units at both ends
    bm_box(bm, 1110, 422, 1170, 488, 0.0, 2.196)
    bm_box(bm, 627, 426, 1108, 482, 0.0, 0.10)          # plinth
    bm_box(bm, 625.5, 422, 1109.5, 488, 0.10, 0.86)     # base cabinet
    bm_box(bm, 625.5, 422, 1109.5, 425, 0.90, 2.196)    # back panel
    bm_box(bm, 640, 425, 1095, 470, 0.90, 1.02)         # display steps (lit, photo 25)
    bm_box(bm, 640, 425, 1095, 448, 1.02, 1.18)
    bm_box(bm, 565, 422, 1170, 500, 2.20, 2.42)         # canopy with the lights
    mesh_obj('arriere-bar', bm, 'Bar', M_MEUBLE)
    bm = bmesh.new()
    bm_box(bm, 625.5, 422, 1109.5, 490, 0.86, 0.90)     # worktop
    mesh_obj('arriere-bar-plan', bm, 'Bar', M_COMPTOIR)
    bm = bmesh.new()
    blocs(bm, 'x', 425, 431, 640, 1095, 1.30, 1.74, pas_u=0.2, pas_z=0.22)   # band of glass cells
    mesh_obj('arriere-bar-cases', bm, 'Traits-fins', M_PAVE)


# ---- the booths (photos 17, 20, 23, 24, 26): in each drum a U banquette along the shell, a plinth, the seat
#      cushion with a rounded front, three rolls for the back; above it a band of rough lava stone
def chemin_u(cx, cy, r, x_bout, seg=48):
    pts = [P(x_bout, cy - r)]
    for k in range(seg + 1):
        a = math.radians(270 - 180 * k / seg)
        pts.append(P(cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts + [P(x_bout, cy + r)]


def banquettes():
    # the seat front at 0.46 m from the shell and the U ending at x 413, as drawn on the plan
    base = [(0.005, 0.0, False), (0.36, 0.0, False), (0.36, 0.08, False), (0.42, 0.08, False), (0.42, 0.40, False),
            (0.09, 0.40, False), (0.09, 0.98, False), (0.005, 0.98, False)]
    coussin = [(0.09, 0.401, False), (0.42, 0.401, True)] + arrondi(0.42, 0.441, 0.04, 0.04, -90, 90, 8)[1:-1] + \
              [(0.42, 0.481, False), (0.09, 0.481, False)]
    for t in DATA['tambours']:
        cx, cy, k = t['cx'], t['cy'], t['id']
        ch = chemin_u(cx, cy, 131, 413)
        c = P(cx, cy)
        sweep(f'banquette-{k}-assise', ch, base, 'Banquettes', M_BANQUETTE, ref=c)
        sweep(f'banquette-{k}-coussin', ch, coussin, 'Banquettes', M_BANQUETTE, ref=c)
        for i, z in enumerate((0.56, 0.715, 0.87)):
            sweep(f'banquette-{k}-boudin-{i}', ch, arrondi(0.168, z, 0.07, 0.075, 0, 360, 20)[:-1],
                  'Banquettes', M_BANQUETTE, ref=c)
        sweep(f'banquette-{k}-pierre', ch, [(0.005, 1.0, False), (0.04, 1.0, False), (0.04, 1.46, False),
                                            (0.005, 1.46, False)], 'Banquettes', M_PIERRE, ref=c)


# ---- the spiral stair (photos 2, 3, 4, 28, 30): solid steps with closed risers and a helical soffit, a solid
#      parapet on the outer edge, and around the core the twisted mirror sculpture
def escalier_detail():
    cx, cy, r0, r1 = 1082, 2172, 40, 179.5
    n, pas_a, rise, a0, T, m = 19, 21.0, H / 19, -55.5, 0.30, 6
    rr = [r0 + (r1 - r0) * i / 6 for i in range(7)]    # the soffit is split radially: a twisted surface, kept smooth

    def V(r, a, z):
        return P(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)), z)

    def nez(a):                                 # nosing line
        return rise * ((a - a0) / pas_a + 1)

    def zs(a):                                  # soffit
        return max(0.0, nez(a) - T)

    bm = bmesh.new()
    last = None
    for k in range(n - 1):
        zt = rise * (k + 1)
        for j in range(m + 1):
            a = a0 + pas_a * (k + j / m)
            if j == 0 and last is not None:     # riser: shares the bottom, the previous top becomes the middle
                c = dict(B=last['B'], M=last['T'], T=(bm.verts.new(V(r0, a, zt)), bm.verts.new(V(r1, a, zt))))
                bm.faces.new((c['M'][0], c['M'][1], c['T'][1], c['T'][0]))
            else:
                zb = zs(a)
                c = dict(B=[bm.verts.new(V(r, a, zb)) for r in rr], M=None,
                         T=(bm.verts.new(V(r0, a, zt)), bm.verts.new(V(r1, a, zt))))
                if last is None:
                    bm.faces.new(c['B'] + [c['T'][1], c['T'][0]])
                else:
                    for s, b_ in ((0, 0), (1, -1)):     # inner and outer sides
                        f = [last['B'][b_], c['B'][b_], c['T'][s], last['T'][s]] + ([last['M'][s]] if last['M'] else [])
                        bm.faces.new(f).smooth = True
                    bm.faces.new((last['T'][0], c['T'][0], c['T'][1], last['T'][1]))
                    for i in range(len(rr) - 1):
                        bm.faces.new((last['B'][i], last['B'][i + 1], c['B'][i + 1], c['B'][i])).smooth = True
            last = c
    bm.faces.new(last['B'] + [last['T'][1], last['T'][0]])
    mesh_obj('escalier-marches', bm, 'Escalier', M_MARCHE)

    # parapet: a band 5 px thick from the soffit to 0.90 m over the nosings, stopped at the mezzanine floor
    bm = bmesh.new()
    a_fin, seg = a0 + pas_a * (n - 1), 180
    rows = []
    for i in range(seg + 1):
        a = a0 + (a_fin - a0) * i / seg
        zb, zt = zs(a), min(nez(a) + 0.90, H)
        rows.append([bm.verts.new(V(r, a, z)) for r, z in ((r1 + 0.5, zb), (r1 + 0.5, zt), (r1 + 5.5, zt), (r1 + 5.5, zb))])
    for i in range(seg):
        A, B = rows[i], rows[i + 1]
        for q in range(4):
            w = (q + 1) % 4
            bm.faces.new((A[q], B[q], B[w], A[w])).smooth = q in (0, 2)
    bm.faces.new(rows[0]); bm.faces.new(list(reversed(rows[-1])))
    mesh_obj('escalier-garde-corps', bm, 'Escalier', M_MARCHE)

    # the mirror sculpture: a twisted column inside the treads (r 23 - 37 px, the treads start at 40)
    bm = bmesh.new()
    sa, sz = 72, 64
    grid = []
    for iz in range(sz + 1):
        z = H * iz / sz
        grid.append([bm.verts.new(V(30 + 7 * math.sin(2 * a + 2.4 * z + 0.9 * math.sin(3 * a - 1.3 * z)),
                                    math.degrees(a), z)) for a in (2 * math.pi * ia / sa for ia in range(sa))])
    for iz in range(sz):
        for ia in range(sa):
            ja = (ia + 1) % sa
            bm.faces.new((grid[iz][ia], grid[iz][ja], grid[iz + 1][ja], grid[iz + 1][ia])).smooth = True
    bm.faces.new(list(reversed(grid[0]))); bm.faces.new(grid[-1])
    mesh_obj('sculpture-miroir', bm, 'Escalier', M_MIROIR)


# ---- the rock garden (photos 4, 7, 30): a low curb round the gravel, a tall crystal-like rock and smaller stones
def rocher(name, x, y, sx, sy, sz, seed, subdiv=2):
    rnd = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=1.0)
    for v in bm.verts:                          # cut facets: the fine ones get a rougher noise
        v.co *= 1 + rnd.uniform(-0.22, 0.22) * (1.0 if subdiv == 1 else 1.5)
        v.co.z = max(v.co.z, -0.45)             # a flat base, laid on the gravel
    zmin = min(v.co.z for v in bm.verts); zmax = max(v.co.z for v in bm.verts)
    rot = rnd.uniform(0, math.tau)
    c, s_ = math.cos(rot), math.sin(rot)
    o_ = P(x, y)
    for v in bm.verts:
        px_, py_ = v.co.x * sx / 2, v.co.y * sy / 2
        v.co = Vector((o_.x + c * px_ - s_ * py_, o_.y + s_ * px_ + c * py_, 0.03 + (v.co.z - zmin) / (zmax - zmin) * sz))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    return mesh_obj(name, bm, 'Jardin', M_ROCHER)


def jardin():
    bord = [P(1273, 2368), P(855, 2368), P(855, 2040)] + [P(x, y) for x, y in GRAVIER_HAUT[1:]]
    sweep('bordure', bord, [(-0.05, 0.0, False), (-0.002, 0.0, False), (-0.002, 0.10, False), (-0.05, 0.10, False)],
          'Jardin', M_BORDURE, ref=P(1000, 2300))
    for k, (x, y, sx, sy, sz, sub) in enumerate((
            (900, 2290, 0.55, 0.42, 0.85, 1), (935, 2335, 0.45, 0.38, 0.34, 2), (884, 2338, 0.24, 0.2, 0.17, 1),
            (922, 2088, 0.42, 0.34, 0.52, 1), (1232, 2338, 0.34, 0.3, 0.28, 2), (1196, 2352, 0.2, 0.17, 0.14, 1),
            (880, 2152, 0.22, 0.2, 0.16, 2), (960, 2250, 0.18, 0.15, 0.12, 1))):
        rocher(f'rocher-{k}', x, y, sx, sy, sz, seed=k + 3, subdiv=sub)


# ---- the entry (plan zones 1, 2): the concierge desk and a console with a rounded corner
def accueil():
    bm = bmesh.new()
    bm_box(bm, 618, 2051, 716, 2089, 0.0, 0.08)
    bm_box(bm, 613, 2046, 721, 2094, 0.08, 1.01)
    bm_box(bm, 611, 2044, 723, 2096, 1.01, 1.05)
    prisme(bm, [(611, 1908), (722, 1908)] + [(702 + 20 * math.cos(math.radians(a)), 1955 + 20 * math.sin(math.radians(a)))
                                             for a in range(0, 91, 10)] + [(611, 1975)], 0.0, 0.90)
    mesh_obj('accueil', bm, 'Accueil', M_MEUBLE)


# ---- curtains (the wavy lines of the plan): heavy drapes hung from a ceiling track, down to 2 cm above the floor.
#      One closes the alcove of the last drum (photo 10: the dark curtain at the end of the row of drums); in the
#      entry, two stacks are drawn back at the two ends of one track (the architects' axonometry). The folds are
#      soft and irregular, like the plan's squiggle, and open a little towards the hem.
def rideau(name, p0, p1, amp, onde, graine):
    """A drape from p0 to p1 (plan px): folds of mean wavelength `onde` (m) and amplitude `amp` (px)."""
    a, b = Vector(p0), Vector(p1)
    L = (b - a).length * PX
    t = (b - a).normalized(); nrm = Vector((-t.y, t.x))
    rnd = random.Random(graine)
    ondes = [(1.0, 1.0), (0.45, 2.1), (0.3, 0.47)]          # (weight, frequency factor): an irregular fold
    phases = [rnd.uniform(0, math.tau) for _ in ondes]
    tot = sum(w for w, _ in ondes)

    def pli(u):
        return sum(w * math.sin(math.tau * u * f / onde + ph) for (w, f), ph in zip(ondes, phases)) / tot
    z0, z1 = 0.02, H - 0.07
    nu, nz = max(16, int(L / onde * 12)), 10
    e = 0.006 / PX                                          # half the thickness of the cloth, px
    bm = bmesh.new()
    faces = []
    for cote in (1, -1):
        g = []
        for j in range(nz + 1):
            z = z0 + (z1 - z0) * j / nz
            ouv = 1.25 - 0.4 * j / nz                       # the folds open towards the hem
            g.append([bm.verts.new(P(*(a + (b - a) * (i / nu) + nrm * (amp * ouv * pli(L * i / nu) + cote * e)), z))
                      for i in range(nu + 1)])
        faces.append(g)
    av, ar = faces
    for j in range(nz):
        for i in range(nu):
            bm.faces.new((av[j][i], av[j][i + 1], av[j + 1][i + 1], av[j + 1][i])).smooth = True
            bm.faces.new((ar[j][i], ar[j + 1][i], ar[j + 1][i + 1], ar[j][i + 1])).smooth = True
        for i in (0, nu):                                   # the side hems
            bm.faces.new((av[j][i], av[j + 1][i], ar[j + 1][i], ar[j][i]))
    for j in (0, nz):                                       # the head and the bottom hem
        for i in range(nu):
            bm.faces.new((av[j][i], ar[j][i], ar[j][i + 1], av[j][i + 1]))
    o = mesh_obj(name, bm, 'Rideaux', M_RIDEAU)
    coll('Traits-fins').objects.link(o)


def tringle(name, p0, p1):
    """The ceiling track, 3 cm wide, just above the head of the curtains (plan px, axis-aligned)."""
    (x0, y0), (x1, y1) = p0, p1
    w = 0.015 / PX
    bm = bmesh.new()
    if x0 == x1:
        bm_box(bm, x0 - w, y0, x0 + w, y1, H - 0.06, H - 0.025)
    else:
        bm_box(bm, x0, y0 - w, x1, y0 + w, H - 0.06, H - 0.025)
    mesh_obj(name, bm, 'Rideaux', M_CADRE)


def rideaux():
    # the alcove: y 1872 rather than the symbol's middle (1878), so the cloth passes between the hung rings
    # of drums 3 and 4 (outer edges at y 1863.5 and 1878.7 where the curtain starts, x 455)
    rideau('rideau-alcove', (455, 1872), (600, 1872), amp=3.5, onde=0.20, graine=7)
    tringle('tringle-alcove', (455, 1872), (600, 1872))
    rideau('rideau-accueil-a', (840, 2012), (840, 2100), amp=4.5, onde=0.12, graine=3)
    rideau('rideau-accueil-b', (840, 2255), (840, 2348), amp=4.5, onde=0.12, graine=5)
    tringle('tringle-accueil', (840, 2008), (840, 2352))


def build_elements():
    """Step 3: the fixed elements, at full height. Returns the new objects."""
    for c in ('Bar', 'Banquettes', 'Accueil', 'Rideaux', 'Jardin'):
        if c not in bpy.data.collections:
            sc.collection.children.link(bpy.data.collections.new(c))
    avant = set(bpy.data.objects)
    bar(); banquettes(); escalier_detail(); jardin(); accueil(); rideaux()
    return [o for o in bpy.data.objects if o not in avant]


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


# ---------------------------------------------------------------- step 4: the furniture, from the plan and the photos
# Each piece is built in its own frame (metres, origin on the floor under its centre, facing +y), turned towards what
# it faces and set on its plan point. One object per piece, named for the live map: table-05, chaise-05-2...
# Heights from the photos: dining tables at 0.75 m with thin steel chairs (photos 9, 10); along the right facade,
# high tables at 1.05 m with stools and a ledge under the glass blocks (photo 8); in the drums a round table on a
# conical foot with three tub armchairs (photos 17, 31); wooden standing tables on A-frames (photo 31).
M_PLATEAU = mat('plateau', (0.05, 0.05, 0.05), 0.3)       # dark stone table tops
M_ACIER = mat('acier', (0.035, 0.035, 0.04), 0.4)          # thin black steel
M_CUIR = mat('cuir', (0.08, 0.075, 0.07), 0.55)            # leather
M_BOIS = mat('bois', (0.15, 0.10, 0.065), 0.6)             # wood: standing tables, ledge, sideboard
M_POT = mat('pot', (0.30, 0.30, 0.29), 0.85)
M_TERRE = mat('terre', (0.10, 0.08, 0.06), 1.0)
M_FEUILLE = mat('feuillage', (0.20, 0.26, 0.14), 0.8)
M_LAITON = mat('laiton', (0.55, 0.45, 0.30), 0.35)         # the lamps


def rrect(cx_, cy_, w, d, r, seg=6):
    """Rounded rectangle outline (local metres), counter-clockwise from the right side."""
    pts = []
    for qx, qy, a0 in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
        ox, oy = cx_ + qx * (w / 2 - r), cy_ + qy * (d / 2 - r)
        pts += [(ox + r * math.cos(math.radians(a0 + 90 * k / seg)), oy + r * math.sin(math.radians(a0 + 90 * k / seg)))
                for k in range(seg + 1)]
    return pts


class Piece:
    """A bmesh in a local frame; each part keeps its material."""
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
        """A vertical frustum: radius r0 at z0, r1 at z1."""
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
        """A square bar of width w from point a to point b."""
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
        """A curved backrest: arc of inner radius R about (0, cy_), opening towards -y, from -a to +a degrees."""
        ang = [math.radians(-a + 2 * a * k / seg) for k in range(seg + 1)]
        inner = [(R * math.sin(q), cy_ - R * math.cos(q)) for q in ang]
        outer = [((R + t) * math.sin(q), cy_ - (R + t) * math.cos(q)) for q in reversed(ang)]
        self.prisme(inner + outer, z0, z1, m)

    def bulle(self, c, r, graine, m):
        """A lump of foliage: a noisy icosphere."""
        rnd = random.Random(graine)
        n0 = len(self.bm.faces)
        tmp = bmesh.new()
        bmesh.ops.create_icosphere(tmp, subdivisions=3, radius=1.0)
        me = bpy.data.meshes.new('tmp'); tmp.to_mesh(me); tmp.free()
        ph = [rnd.uniform(0, math.tau) for _ in range(3)]     # a smooth lumpy surface, not random spikes
        vs = [self.bm.verts.new(Vector(c) + v.co * r * (1 + 0.12 * math.sin(3 * v.co.x + ph[0]) * math.sin(3 * v.co.y + ph[1])
                                                          + 0.08 * math.sin(4 * v.co.z + ph[2]))) for v in me.vertices]
        for p in me.polygons:
            self.bm.faces.new([vs[i] for i in p.vertices])
        bpy.data.meshes.remove(me)
        self._fin(n0, m)


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
    for p in me.polygons:
        p.use_smooth = True
    me.set_sharp_from_angle(angle=math.radians(40))
    ob = bpy.data.objects.new(name, me)
    coll(collection).objects.link(ob)
    return ob


# ---- the pieces
def chaise(haute=False):
    """The thin steel chair of photos 9 and 10 (seat 0.47 m); haute: the stool of photo 8 (seat 0.77 m, footrest)."""
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
    if haute:                                   # the footrest ring, at 0.28 m
        t = 0.28 / zs
        q = [a.lerp(b, t) for a, b in pieds]    # order: (-,-), (-,+), (+,-), (+,+)
        for i, j in ((0, 1), (1, 3), (3, 2), (2, 0)):
            pc.barre(q[i], q[j], 0.014, M_ACIER)
    zb = 0.66 + s
    for sx in (-1, 1):                          # the back posts, from the seat to the backrest
        pc.barre((sx * 0.17, -0.15, zs + 0.05), (sx * 0.17, -0.168, zb), 0.018, M_ACIER)
    pc.bande(0.30, 0.10, 0.03, 36, zb, zb + 0.15, M_CUIR)
    return pc


def fauteuil():
    """The tub armchair of the drums (photos 10, 31): an upholstered shell, a cushion, short steel legs."""
    pc = Piece()
    for sx in (-1, 1):
        for sy in (-1, 1):
            pc.barre((sx * 0.20, sy * 0.17, 0.0), (sx * 0.18, sy * 0.15, 0.33), 0.02, M_ACIER)
    pc.prisme(rrect(0, 0, 0.58, 0.54, 0.21), 0.33, 0.39, M_CUIR)          # the thin seat shell
    pc.prisme(rrect(0, 0.025, 0.475, 0.49, 0.15), 0.39, 0.45, M_CUIR)       # the cushion, inside the back
    # the back and arms: a 4.5 cm shell around the back half, open at the front (y > 0.05)
    ext = [p for p in rrect(0, 0, 0.58, 0.54, 0.21, 10) if p[1] < 0.05]     # left side -> back -> right side
    inn = [p for p in rrect(0, 0, 0.49, 0.45, 0.165, 10) if p[1] < 0.05]
    u = [(-0.29, 0.05)] + ext + [(0.29, 0.05), (0.245, 0.05)] + list(reversed(inn)) + [(-0.245, 0.05)]
    pc.prisme(u, 0.39, 0.70, M_CUIR)
    return pc


def table_rect(W, L, h, pieds):
    """A table W x L (m, L along y) at height h, on pedestals (local y) with square base plates."""
    pc = Piece()
    pc.boite(-W / 2, -L / 2, W / 2, L / 2, h - 0.03, h, M_PLATEAU)
    p = 0.44 if h < 1 else 0.50
    for yp in pieds:
        pc.cyl(0, yp, 0.035, 0.035, 0.02, h - 0.03, M_ACIER, 12)
        pc.boite(-p / 2, yp - p / 2, p / 2, yp + p / 2, 0.0, 0.02, M_ACIER)
    return pc


def table_ronde():
    pc = Piece()
    pc.cyl(0, 0, 0.48, 0.48, 0.72, 0.75, M_PLATEAU, 48)
    pc.cyl(0, 0, 0.22, 0.06, 0.0, 0.72, M_ACIER, 32)       # the conical foot (photo 17)
    return pc


def lampe():
    """The small cordless table lamp (photos 9, 10, 15)."""
    pc = Piece()
    pc.cyl(0, 0, 0.04, 0.04, 0.0005, 0.03, M_LAITON, 16)
    pc.cyl(0, 0, 0.008, 0.008, 0.03, 0.22, M_LAITON, 8)
    pc.cyl(0, 0, 0.055, 0.03, 0.22, 0.25, M_LAITON, 16)
    return pc


def suspension(z, R):
    """A flat saucer pendant (photos 15, 17) with its cable up to the slab."""
    pc = Piece()
    pc.cyl(0, 0, R, R, z, z + 0.012, M_LAITON, 32)
    pc.cyl(0, 0, R, 0.03, z + 0.012, z + 0.06, M_ACIER, 32)
    pc.cyl(0, 0, 0.003, 0.003, z + 0.06, H - 0.002, M_ACIER, 6)
    return pc


def jardiniere(graine):
    """A round planter (the plan's 0.75 m circles) with a small tree, as in the architects' axonometry."""
    pc = Piece()
    pc.cyl(0, 0, 0.37, 0.37, 0.0, 0.55, M_POT, 40)
    pc.cyl(0, 0, 0.33, 0.33, 0.55, 0.555, M_TERRE, 40)
    pc.cyl(0, 0, 0.035, 0.022, 0.555, 1.62, M_BOIS, 10)
    rnd = random.Random(graine)
    for k in range(9):                          # an airy crown of small clumps, within 0.55 m of the trunk
        a = math.tau * k / 9 + rnd.uniform(-0.3, 0.3)
        d = rnd.uniform(0.12, 0.30)
        pc.bulle((d * math.cos(a), d * math.sin(a), 1.55 + rnd.uniform(0.0, 0.75)), rnd.uniform(0.15, 0.21),
                 graine * 10 + k, M_FEUILLE)
    pc.bulle((0.02, -0.01, 2.25), 0.18, graine * 10 + 9, M_FEUILLE)
    return pc


# ---- the plan: the 13 service tables (numbers for the live map), the standing tables, the bar, the planters
# drums: table centre (cx - 12, cy - 4) on the plan; armchairs at these offsets from the drum centre
FAUTEUILS = [(64, -87), (105, -7), (64, 73)]
# (id, name, x0, y0, x1, y1, height, chairs: (x, y) facing the table's long axis, pedestals, lamps, pendants) in plan px
SALLE = [
    (5, 'Rangée, table 1', 664, 1208.5, 757.5, 1354, 0.75,
     [(x, y) for x in (627.5, 793.5) for y in (1242.5, 1322.5)], [1281.25], [1281.25], [1281.25]),
    (6, 'Rangée, grande table', 664, 1446, 757.5, 1895, 0.75,
     [(x, y) for x in (627.5, 793.5) for y in (1480, 1560, 1672.5, 1777.5, 1857.5)], [1518.5, 1671, 1811],
     [1595, 1741], [1518.5, 1671, 1811]),
    (7, 'Salle, table 1', 996, 1301, 1090, 1447.5, 0.75,
     [(x, y) for x in (957.5, 1130) for y in (1335, 1410)], [1374.25], [1374.25], [1374.25]),
    (8, 'Salle, table 2', 996, 1560, 1090, 1655, 0.75, [(957.5, 1612.5), (1130, 1612.5)], [1607.5], [1607.5], [1607.5]),
    (9, 'Salle, table 3', 996, 1747.5, 1090, 1840, 0.75, [(957.5, 1797.5), (1130, 1797.5)], [1793.75], [1793.75],
     [1793.75]),
    (10, 'Façade, table haute 1', 1282.5, 890, 1376, 1037.5, 1.05, [(1242.5, 925), (1242.5, 1005)], [963.75], [963.75],
     [963.75]),
    (11, 'Façade, table haute 2', 1282.5, 1109, 1376, 1205, 1.05, [(1242.5, 1160)], [1157], [1157], [1157]),
    (12, 'Façade, table haute 3', 1282.5, 1285, 1376, 1430, 1.05, [(1242.5, 1320), (1242.5, 1402.5)], [1357.5],
     [1357.5], [1357.5]),
    (13, 'Façade, table haute 4', 1282.5, 1585, 1376, 1730, 1.05, [(1242.5, 1620), (1242.5, 1700)], [1657.5], [1657.5],
     [1657.5]),
]
# the plan's three standing tables (dark wooden squares near the bar) were removed at step 6: see ESPACE_BAR below
TABOURETS_BAR = [657 + 71.67 * k for k in range(7)]       # y 792.5, facing the counter
JARDINIERES = [(711, 1401), (1044, 1252.5), (1044, 1702.5)]


def tablette_facade():
    """The ledge under the right glass blocks, behind the high tables: 0.42 m deep, around the two facade columns."""
    cols = [(1477.5, 805.0, 68.8), (1477.5, 1516.7, 69.1)]
    y0, y1, xf, xb = 857, 1755, 1384, 1434
    front = []
    for y in range(y0, y1 + 1, 3):
        x = xf - (13 * math.sin(math.pi * (y - 1462) / 110) if 1462 < y < 1572 else 0)
        front.append((x, y))
    back = []
    for y in range(y1, y0 - 1, -3):
        x = xb
        for cx_, cy_, r in cols:
            if abs(y - cy_) < r:
                x = min(x, cx_ - math.sqrt(r * r - (y - cy_) ** 2))
        back.append((x, y))
    bm = bmesh.new(); prisme(bm, front + back, 0.0, 1.02); mesh_obj('tablette-facade', bm, 'Mobilier', M_BOIS)
    bm = bmesh.new(); prisme(bm, front + back, 1.02, 1.05); mesh_obj('tablette-facade-plateau', bm, 'Mobilier', M_PLATEAU)


def repose_pieds():
    """The foot rail along the bar (photo 31), on small brackets."""
    sweep('bar-repose-pieds', [P(428, 757), P(1176, 757)],
          [(0.02 * math.cos(math.tau * k / 12), 0.22 + 0.02 * math.sin(math.tau * k / 12), True) for k in range(12)],
          'Mobilier', M_ACIER, ref=P(800, 900))
    bm = bmesh.new()
    for k in range(6):
        x = 440 + (1165 - 440) * k / 5
        bm_box(bm, x - 1.2, 745.2, x + 1.2, 754.5, 0.21, 0.23)
    mesh_obj('bar-repose-pieds-pattes', bm, 'Mobilier', M_ACIER)


# ---- step 6: the space between the bar and the room. The three standing tables of the plan are gone (the user did
#      not want tables without chairs). Of the four layouts proposed for the free space (4.1 x 1.7 m once the aisles are
#      kept: 0.8 m behind the bar stools, 0.75 m in front of drum 1, 0.65 m to the row), the user chose the banquette
#      backed by a planter (Z4, 24/11): a low hedge separates the bar aisle from the room, four tables for two in front.
ESPACE_BAR = [(14 + k, f'Banquette {k + 1}', x, 1034, 2) for k, x in enumerate((717, 829, 941, 1053))]


def espace_bar():
    x0, x1, cx = 660, 1110, 885
    pc = Piece()           # local frame centred on (cx, 954), +y = plan up (towards the bar)
    ly = lambda yp: -(yp - 954) * PX
    lx = lambda xp: (xp - cx) * PX
    pc.boite(lx(x0), ly(930), lx(x1), ly(915), 0.0, 1.0, M_BOIS)                 # the planter, behind the backrest
    pc.boite(lx(x0 + 2), ly(928), lx(x1 - 2), ly(917), 1.0, 1.005, M_TERRE)
    pc.boite(lx(x0), ly(993), lx(x1), ly(930), 0.0, 0.40, M_MEUBLE)              # the seat base
    pc.boite(lx(x0), ly(941), lx(x1), ly(930), 0.40, 0.86, M_CUIR)               # the backrest cushion
    rnd = random.Random(4)
    for k in range(56):                                                          # a low hedge: two rows of clumps
        x = x0 + 10 + (x1 - x0 - 20) * (k // 2) / 27 + rnd.uniform(-5, 5)
        pc.bulle((lx(x), ly(922.5) + (0.035 if k % 2 else -0.035) + rnd.uniform(-0.01, 0.01), 1.05 + rnd.uniform(0.0, 0.08)),
                 rnd.uniform(0.065, 0.085), 40 + k, M_FEUILLE)
    poser('banquette-bar', pc, cx, 954, collection='Mobilier')
    for tid, _, x, y, _ in ESPACE_BAR:
        coussin = Piece(); coussin.prisme(rrect(0, 0, 0.83, 0.43, 0.05), 0.4005, 0.47, M_CUIR)
        poser(f'chaise-{tid}-2', coussin, x, 967.1, collection='Assises')       # its part of the banquette: seat 2
        poser(f'table-{tid}', table_rect(0.70, 0.60, 0.75, [0.0]), x, y, collection='Tables')
        poser(f'lampe-{tid}', lampe(), x, y + 10, collection='Tables', z=0.75)
        poser(f'suspension-{tid}', suspension(1.75, 0.20), x, y, collection='Suspensions')
        poser(f'chaise-{tid}-1', chaise(), x, 1106.5, vers=(x, y), collection='Assises')


def build_mobilier():
    """Step 4: the furniture. Returns the new objects; writes the table list for the live map."""
    for c in ('Mobilier', 'Tables', 'Assises', 'Jardinieres', 'Suspensions'):
        if c not in bpy.data.collections:
            sc.collection.children.link(bpy.data.collections.new(c))
    avant = set(bpy.data.objects)
    liste = []
    for n, t in enumerate(sorted(DATA['tambours'], key=lambda t: t['cy'])):
        cx, cy = t['cx'], t['cy']
        tc = (cx - 12, cy - 4)
        poser(f'table-{n + 1:02d}', table_ronde(), *tc, collection='Tables')
        poser(f'lampe-{n + 1:02d}', lampe(), tc[0] + 18, tc[1], collection='Tables', z=0.75)
        poser(f'suspension-{n + 1:02d}', suspension(1.95, 0.30), *tc, collection='Suspensions')
        for k, (dx, dy) in enumerate(FAUTEUILS):
            poser(f'chaise-{n + 1:02d}-{k + 1}', fauteuil(), cx + dx, cy + dy, vers=tc, collection='Assises')
        liste.append(dict(id=n + 1, nom=f'Tambour {n + 1}', type='tambour', centre_px=[round(tc[0], 1), round(tc[1], 1)],
                          places=6, assises='banquette en U et 3 fauteuils', zone='T'))
    for tid, nom, x0, y0, x1, y1, h, chaises, pieds, lampes, susp in SALLE:
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        W, L = (x1 - x0) * PX, (y1 - y0) * PX
        poser(f'table-{tid:02d}', table_rect(W, L, h, [-(yp - cy) * PX for yp in pieds]), cx, cy, collection='Tables')
        for k, yl in enumerate(lampes):
            poser(f'lampe-{tid:02d}' + (f'-{k + 1}' if len(lampes) > 1 else ''), lampe(), cx, yl, collection='Tables', z=h)
        for k, ys in enumerate(susp):
            poser(f'suspension-{tid:02d}' + (f'-{k + 1}' if len(susp) > 1 else ''),
                  suspension(h + 1.0, 0.20), cx, ys, collection='Suspensions')
        for k, (x, y) in enumerate(chaises):
            poser(f'chaise-{tid:02d}-{k + 1}', chaise(haute=h > 1), x, y, vers=(cx, y), collection='Assises')
        liste.append(dict(id=tid, nom=nom, type='table haute' if h > 1 else 'table', centre_px=[cx, cy],
                          taille_m=[round(W, 2), round(L, 2)], places=len(chaises),
                          assises='tabourets' if h > 1 else 'chaises', zone='F' if h > 1 else 'R' if tid <= 6 else 'S'))
    espace_bar()
    liste += [dict(id=tid, nom=nom, type='table', centre_px=[x, y], places=n, assises='banquette et chaise', zone='B')
              for tid, nom, x, y, n in ESPACE_BAR]
    for k, x in enumerate(TABOURETS_BAR):
        poser(f'tabouret-bar-{k + 1}', chaise(haute=True), x, 792.5, vers=(x, 700), collection='Assises')
    liste.append(dict(id=0, nom='Bar', type='bar', centre_px=[801.5, 716], places=len(TABOURETS_BAR), assises='tabourets'))
    for k, (x, y) in enumerate(JARDINIERES):
        poser(f'jardiniere-{k + 1}', jardiniere(k + 1), x, y, collection='Jardinieres')
    tablette_facade()
    repose_pieds()
    bm = bmesh.new(); bm_box(bm, 467, 2172, 593, 2243, 0.0, 0.80)       # the sideboard of the alcove
    mesh_obj('alcove-console', bm, 'Mobilier', M_BOIS)
    for t in liste:
        x, y = t['centre_px']; v = P(x, y)
        t['centre_m'] = [round(v.x, 3), round(v.y, 3)]
    (RACINE / 'modele' / 'floor1-tables.json').write_text(json.dumps(dict(
        note='floor1 (rez-de-chaussée) : les tables de la carte en direct. centre_px : sur floor1.png ; centre_m : dans '
             'le modèle (x vers la droite du plan, y vers le haut du plan, origine au pixel (837, 1230)). zone : T tambours, '
             'R rangée, S salle, F façade, B la banquette près du bar.',
        tables=liste, total_places=sum(t['places'] for t in liste)), ensure_ascii=False, indent=1))
    return [o for o in bpy.data.objects if o not in avant]



# ---------------------------------------------------------------- step 5: the model of the interactive map
# glTF export of the built variant (fantôme: cut at 1.2 m with the see-through tops; fil-de-fer: uncut). Each object
# carries in its extras a role (mur, sol, tambour, element, table, assise...), 'fin' for the thin-line objects (glass
# blocks, curtains) and, for the furniture, the number of its table (0 = the bar).
ROLES = {'Coque': 'mur', 'Vitrages': 'vitrage', 'Tambours': 'tambour', 'Escalier': 'escalier', 'Sols': 'sol',
         'Bar': 'element', 'Banquettes': 'element', 'Accueil': 'element', 'Rideaux': 'element', 'Jardin': 'element',
         'Mobilier': 'element', 'Tables': 'table', 'Assises': 'assise', 'Jardinieres': 'jardiniere',
         'Suspensions': 'suspension', 'Traits-fins': 'fin'}


def export_web(chemin):
    import re
    chemin = Path(chemin) if Path(chemin).is_absolute() else RACINE / chemin
    chemin.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT')
    n = 0
    for o in bpy.data.objects:
        cs = [c.name for c in o.users_collection]
        if o.type != 'MESH' or o.name == 'terrain' or 'Plan' in cs:
            continue
        o['role'] = 'fantome' if 'Fantome' in cs else next((ROLES[c] for c in cs if c in ROLES and c != 'Traits-fins'),
                                                           'fin' if 'Traits-fins' in cs else 'autre')
        o['fin'] = int('Traits-fins' in cs)
        m = re.match(r'^(table|chaise|lampe|suspension)-(\d\d)', o.name)
        if m:
            o['table'] = int(m.group(2))
        elif o.name.startswith('tabouret-bar'):
            o['table'] = 0
        o.select_set(True)
        n += 1
    bpy.ops.export_scene.gltf(filepath=str(chemin), export_format='GLB', use_selection=True, export_extras=True,
                              export_apply=True, export_yup=True, export_cameras=False, export_lights=False)
    print('export', chemin, n, 'objets')


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
    'detail':       dict(cut=None, grid=True,  alpha=1.0,  ghost=False, hidden=None),   # step 3 close-ups
}

# step 3 close-ups, each framed like a photo of the real place: camera (plan px, z), target (plan px, z), lens
PLANS = {
    'bar':       ((790, 1330, 1.55), (800, 560, 1.10), 32),    # photo 25
    'banquette': ((690, 1313, 1.15), (410, 1313, 0.92), 26),   # photo 17, drum 2
    'escalier':  ((1000, 1830, 1.55), (1040, 2210, 0.95), 24),  # photo 4
    'facade':    ((930, 1250, 1.50), (1452, 1050, 1.30), 26),   # photos 8, 9
    'rideau':    ((548, 1130, 1.30), (612, 1890, 1.10), 24, (1000, 1250)),   # photo 10, the alcove curtain
    # step 4
    'salle':     ((590, 1430, 1.30), (650, 1900, 1.00), 20, (1000, 1250)),   # photo 10, the tables along the drums
    'tabourets': ((1232, 1040, 1.15), (1195, 2150, 0.95), 30, (1000, 1250)),  # photo 8, the high tables on the right
    'tambour':   ((900, 860, 1.25), (400, 1010, 0.95), 30),                    # photo 31, drum 1, a standing table
    # step 6: the space between the bar and the room, seen from the room
    'zone':      ((560, 1330, 3.1), (900, 985, 0.30), 28),
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
    fins = 'Traits-fins' in bpy.data.collections and len(bpy.data.collections['Traits-fins'].all_objects) > 0
    if fins:                                    # glass blocks and curtains: thin light lines, so the block grids
        sets.append(('fins', 'VISIBLE', tuple(min(1.0, c_ + 0.30) for c_ in visible), 0.6 * thickness))
        #                                         and the folds read as texture, not as walls
    for k, (nom, vis, col, ep) in enumerate(sets):
        ls = fs.linesets[k] if len(fs.linesets) > k else fs.linesets.new(nom)
        ls.select_by_visibility = True
        ls.visibility = vis
        ls.select_silhouette = ls.select_border = ls.select_crease = True
        if fins:
            ls.select_by_collection = True
            ls.collection = bpy.data.collections['Traits-fins']
            ls.collection_negation = 'INCLUSIVE' if nom == 'fins' else 'EXCLUSIVE'
        ls.linestyle = bpy.data.linestyles.new(nom)
        ls.linestyle.color = col
        ls.linestyle.thickness = ep


if ARGS.get('variante'):
    nom = ARGS['variante']
    V = VARIANTES[nom]
    num = list(VARIANTES).index(nom) + 1
    OUT = Path(ARGS.get('out', RACINE / 'rendus' / ('5-mobilier' if MOBILIER else
                                                    '4-elements-fixes' if ELEMENTS else '3-styles-blancs')))
    sc.collection.children.link(bpy.data.collections.new('Fantome'))
    m_ghost = mat('fantome', (0.98, 0.98, 0.98), 0.6, alpha=0.16)

    build(V['cut'])
    if V['ghost']:                              # the walls above the cut, see-through
        avant = set(bpy.data.objects)
        build(None, bas=V['cut'] + 0.004)     # 4 mm gap: no face shared with the top of the solid walls
        for o in set(bpy.data.objects) - avant:
            for c in o.users_collection:
                c.objects.unlink(o)
            coll('Fantome').objects.link(o)
            o.data.materials.clear(); o.data.materials.append(m_ghost)
            o.visible_shadow = False            # only the solid walls cast shadows: no grey smudges seen from above
    if ELEMENTS:                                # the fixed elements, cut like the walls
        nouveaux = build_elements()
        if MOBILIER:
            nouveaux += build_mobilier()
        if V['cut'] is not None:
            separer(nouveaux, V['cut'], m_ghost if V['ghost'] else None)

    # materials: white, the floors a touch warmer than the walls, the ground a light grey
    a = V['alpha']
    for name, rgb in (('mur', (0.965,) * 3), ('tete-de-mur', (0.98,) * 3), ('poteau', (0.96,) * 3),
                      ('tambour', (0.93, 0.93, 0.925)), ('marche', (0.90,) * 3)):
        set_mat(name, rgb, 0.85, a)
    set_mat('cadre', (0.80,) * 3, 0.6, max(a, 0.25) if a < 1 else 1.0)
    set_mat('verre', (0.97, 0.98, 0.99), 0.3, 0.16 if a == 1.0 else min(a, 0.16))
    set_mat('gravier', (0.88, 0.875, 0.865), 0.95)
    if ELEMENTS:
        for name, rgb, rough in (('banquette', (0.955, 0.95, 0.94), 0.8), ('pierre', (0.915, 0.91, 0.90), 0.95),
                                 ('comptoir', (0.935,) * 3, 0.5), ('meuble', (0.96,) * 3, 0.85),
                                 ('miroir', (0.975,) * 3, 0.2), ('rocher', (0.905, 0.90, 0.89), 0.95),
                                 ('rideau', (0.975, 0.972, 0.965), 0.9), ('bordure', (0.93,) * 3, 0.8)):
            set_mat(name, rgb, rough, a)
        set_mat('pave', (0.95, 0.97, 0.98), 0.25, 0.55 if a == 1.0 else min(a, 0.3))
    if MOBILIER:                                # the furniture in the same whites; the steel a light grey
        for name, rgb, rough in (('plateau', (0.90,) * 3, 0.5), ('acier', (0.74,) * 3, 0.5),
                                 ('cuir', (0.955, 0.95, 0.94), 0.8), ('bois', (0.93, 0.92, 0.905), 0.8),
                                 ('pot', (0.94,) * 3, 0.9), ('terre', (0.86, 0.85, 0.83), 1.0),
                                 ('feuillage', (0.90, 0.92, 0.88), 0.9), ('laiton', (0.97,) * 3, 0.4)):
            set_mat(name, rgb, rough, a)
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
    if ELEMENTS and a < 0.1:                    # a line drawing: the stacked panes must not cast grey shadows
        for o in bpy.data.objects:
            o.visible_shadow = False
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

    if ARGS.get('export'):
        export_web(ARGS['export'])
    elif ARGS.get('transition'):
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
    elif ARGS.get('plans'):
        for pl in ARGS['plans'].split(','):
            (x0, y0, z0), (x1, y1, z1), lens, *res = PLANS[pl]
            render(f'plan-{pl}', camera(f'cam-{pl}', P(x0, y0, z0), P(x1, y1, z1), lens=lens),
                   res[0] if res else (1500, 1000))
    elif ELEMENTS:
        pendants = [o for o in bpy.data.objects if o.name.startswith('suspension')]
        for o in pendants:                      # seen from the top, the pendants would hide the tables
            o.hide_render = True
        render(f'{nom}-dessus', cam_top, (2000, 1250))
        for o in pendants:
            o.hide_render = False
        render(f'{nom}-3d', cam_3d, (2000, 1250))
    else:
        render(f'{num}-{nom}-dessus', cam_top, (2000, 1250))
        render(f'{num}-{nom}-3d', cam_3d, (2000, 1250))
    if ARGS.get('save'):
        bpy.ops.wm.save_as_mainfile(filepath=ARGS['save'])
