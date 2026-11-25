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
import bpy, bmesh, json, math, random, sys
from pathlib import Path
from mathutils import Vector

ICI = Path(__file__).resolve().parent
RACINE = ICI.parents[1]
ARGS = dict(a.split('=', 1) for a in (sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []) if '=' in a)
VUES = ARGS.get('vue', '' if 'variante' in ARGS else 'dessus,iso,coupe').split(',')
ECH = int(ARGS.get('ech', 100))
OUT = Path(ARGS.get('out', RACINE / 'rendus' / '12-etage-coque'))

DATA = json.loads((RACINE / 'modele' / 'etage1-murs.json').read_text())
PX = 1 / DATA['echelle_px_par_m']        # metres per plan pixel
CX, CY = 837, 1230                       # plan pixel at the world origin (as floor1)
H = 3.0                                  # the mezzanine's clear height (floor to the roof slab), from the section
H_RDC = 3.35                             # the ground floor under it (floor1.py)
DALLE = 0.30                             # the slab
ELEMENTS = ARGS.get('elements') == '1'   # step 2: the fixed elements


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
BLOC = (601, 1896, 856, 2373)            # the closed volume over the entry (black on the plan, a box on the axonometry)
ESCALIER_HAUT = (485, 140, 852, 247)     # the stair up to the roof floor, rising towards +x from x 572
# the glass parapet on the slab edge (1.5 px off the void, on the slab): round the corner, down the right side and
# along the stair; along the room side, the ledge (step 2) or, on the shell alone, the glass carries on to the lab
GARDE_CORPS = arc(1012, 1242, 71.5, -90, 0, 32) + [(1083.5, 1917)] + arc(1020, 1917, 63.5, 0, 90, 12)[1:] + \
    [(1000.6, 1991.4), (861.5, 2045.4)]


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


# ---------------------------------------------------------------- step 2 helpers (as floor1's step 3)
M_BANQUETTE = mat('banquette', (0.11, 0.10, 0.09), 0.6)
M_PIERRE = mat('pierre', (0.20, 0.19, 0.18), 0.95)
M_COMPTOIR = mat('comptoir', (0.05, 0.05, 0.05), 0.3)
M_MEUBLE = mat('meuble', (0.09, 0.085, 0.08), 0.5)
M_PAVE = mat('pave', (0.80, 0.84, 0.85), 0.15, transmission=0.9)
M_MIROIR = mat('miroir', (0.92, 0.92, 0.92), 0.05)
M_RIDEAU = mat('rideau', (0.07, 0.07, 0.07), 0.8)
M_METAL = mat('metal', (0.06, 0.06, 0.065), 0.45)     # the black metal of the entry portal (photo 37)


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
    """Glass block facade panels between the mullions (as floor1): blocks of about 0.2 m, from the sill (0.06 m) to
    the head of the frame (H - 0.08), clipped to [bas, top]."""
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
    for k, mu in enumerate(DATA['murs']):
        extrude_loops(f"mur-{mu['id']}-{k}", [mu['contour']] + mu['trous'], bas, top, 'Coque', M_MUR)
    for k, (x0, y0, x1, y1) in enumerate(((200, 752, 384, 842), (200, 842, 232, 2276), (200, 2245, 599.5, 2276),
                                          (232, 1167, 384, 1173))):
        box(f'mur-labo-{k}', x0, y0, x1, y1, bas, top, 'Coque', M_MUR)
    # ---- the closed volume over the entry (step 2: clad in black metal, see bloc_entree)
    if not ELEMENTS:
        box('bloc-entree', *BLOC, bas, top, 'Coque', M_MUR)
    # ---- columns
    for c in DATA['poteaux']:
        cx, cy, r = (407.5, 801.5, 49.5) if c['id'] == 841 else (c['cx'], c['cy'], c['r'])
        cylinder(f"poteau-{c['id']}", cx, cy, r, bas, top, 'Coque', M_POTEAU)

    # ---- facades: between steel mullions (measured on the plan), plain glass on the shell, glass blocks at step 2
    #      (as floor1: the blocks below the map cut, a plain see-through pane above it)
    def facade(name, x, montants, ep=4.5):
        if ELEMENTS and bas == 0.0:
            ep = 5.0
            paves(name, 'y', x, [(y0 + 3, y1 - 3) for y0, y1 in zip(montants, montants[1:])], bas, top)
        else:
            for k, (y0, y1) in enumerate(zip(montants, montants[1:])):
                box(f'{name}-verre-{k}', x - 1.2, y0, x + 1.2, y1, bas, top, 'Vitrages', M_VERRE)
        m_bas = max(bas, 0.06) if ELEMENTS else bas
        for k, y in enumerate(montants):
            box(f'{name}-montant-{k}', x - ep, y - 3, x + ep, y + 3, m_bas, top, 'Vitrages', M_CADRE)
        if bas == 0.0:
            box(f'{name}-seuil', x - ep, montants[0], x + ep, montants[-1], 0.0, 0.06, 'Vitrages', M_CADRE)
    facade('facade-gauche', 417.5, [145, 281.5, 421, 560, 656, 750])
    facade('facade-droite-a', 1450.5, [637, 741])
    facade('facade-droite-b', 1450.5, [851, 862, 972, 1094])
    facade('facade-droite-c', 1450.5, [1169, 1263.5, 1360, 1453])
    facade('facade-droite-d', 1450.5, [1579, 1692, 1822.5, 1952, 2082.5, 2210])
    # the double-height facade over the void: its upper part, from the slab level
    facade('facade-vide', 238.5, [1172 + (2245 - 1172) * k / 9 for k in range(10)])

    # ---- glass parapets on the edges of the void (1.05 m, 2 cm glass in a thin steel shoe)
    if bas < 1.05:
        # with the ledge, the glass starts where it leaves the ledge's rounded end (y 1176), the ledge guarding the rest
        bord = [p_ for p_ in GARDE_CORPS if p_[1] >= 1176] if ELEMENTS else [(459.5, 1173.5), (1012, 1173.5)] + GARDE_CORPS[1:]
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
            box(f'demi-tambour-{k}-retour-a', 1281, cy - 125, cx, cy - 110, bas, zt, 'Tambours', M_TAMBOUR)
            box(f'demi-tambour-{k}-retour-b', 1281, cy + 110, cx, cy + 125, bas, zt, 'Tambours', M_TAMBOUR)

    # ---- the stair up (to the roof floor): the 7 solid treads of the plan (35 px, x 572 - 817, up to its end wall),
    #      rising 0.18 m towards +x, a landing on the left
    x0, y0, x1, y1 = ESCALIER_HAUT
    for k in range(7):
        z = 0.18 * (k + 1)
        if z - 0.05 < bas or z - 0.05 > top:
            continue
        box(f'marche-haut-{k}', 572 + 35 * k, y0 + 2, 572 + 35 * (k + 1), y1 - 2, max(bas, 0.0), z, 'Escalier', M_MARCHE)

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
    bm_box(bm, 584, 518, 1177, 584, 1.03, 1.08)           # the guests' top, a small overhang on the stools' side
    mesh_obj('omakase-plateaux', bm, 'Bar', M_COMPTOIR)


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
        cx = 1298.5
        ch = chemin_demi(cx, cy, 110, 1282)
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
def tablette_vide():
    dessus = [(459.5, 1114.6), (1012, 1114.6)] + arc(1012, 1172, 57.4, -90, 0, 12)[1:] + [(459.5, 1172)]
    corps = [(459.5, 1143.5), (1012, 1143.5)] + arc(1012, 1172, 28.5, -90, 0, 8)[1:] + [(459.5, 1172)]
    socle = [(459.5, 1147.5), (1012, 1147.5)] + arc(1012, 1170, 22.5, -90, 0, 8)[1:] + [(459.5, 1170)]
    bm = bmesh.new()
    prisme(bm, socle, 0.0, 0.10)
    prisme(bm, corps, 0.10, 1.03)
    mesh_obj('tablette-vide', bm, 'Bar', M_MEUBLE)
    bm = bmesh.new()
    prisme(bm, dessus, 1.03, 1.08)
    mesh_obj('tablette-vide-plateau', bm, 'Bar', M_COMPTOIR)


# ---- the counter of the lab (plan zone 2, x 400 - 471, y 872 - 1080): a base unit and its worktop, the pass to the room
def labo():
    bm = bmesh.new()
    bm_box(bm, 406, 878, 471, 1074, 0.0, 0.10)
    bm_box(bm, 400, 872, 471, 1080, 0.10, 0.86)
    mesh_obj('labo-comptoir', bm, 'Bar', M_MEUBLE)
    bm = bmesh.new()
    bm_box(bm, 400, 872, 471, 1080, 0.86, 0.90)
    mesh_obj('labo-plan', bm, 'Bar', M_COMPTOIR)


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
    rideau('rideau-palier', (427, 287), (570, 287), amp=3.5, onde=0.20, graine=11)
    tringle('tringle-palier', (424, 287), (573, 287))
    rideau('rideau-passage', (1180, 556.5), (1292, 608.5), amp=4.0, onde=0.16, graine=13)
    tringle('tringle-passage', (1177, 555), (1295, 610))


# ---- the volume over the entry: the top of the entry portal, which is black metal on the street (photo 37). No photo
#      shows it from the mezzanine, so it is clad like the portal: standing-seam panels about 0.30 m wide, a shadow
#      gap at the floor, a thin capping at the ceiling. A closed mass, as on the plan and the axonometry
def bloc_entree():
    x0, y0, x1, y1 = BLOC
    r = 1.2                                       # the seams stand 1 cm off the panels (1.2 px)
    bm = bmesh.new()
    bm_box(bm, x0 + 1.5, y0 + 1.5, x1 - 1.5, y1 - 1.5, 0.0, 0.08)                 # shadow gap
    bm_box(bm, x0, y0, x1, y1, 0.08, H - 0.05)                                     # the panels
    bm_box(bm, x0 - r, y0 - r, x1 + r, y1 + r, H - 0.05, H - 0.002)                # capping
    mesh_obj('bloc-entree', bm, 'Accueil', M_METAL)
    bm = bmesh.new()
    pas = 0.30 / PX
    for (ax, a0, a1, fixe, signe) in (('x', x0, x1, y0, -1), ('x', x0, x1, y1, 1), ('y', y0, y1, x0, -1),
                                      ('y', y0, y1, x1, 1)):
        n = max(2, round((a1 - a0) / pas))
        for k in range(1, n):
            u = a0 + (a1 - a0) * k / n
            d0, d1 = sorted((fixe, fixe + signe * r))
            if ax == 'x':
                bm_box(bm, u - 1.0, d0, u + 1.0, d1, 0.08, H - 0.05)
            else:
                bm_box(bm, d0, u - 1.0, d1, u + 1.0, 0.08, H - 0.05)
    mesh_obj('bloc-entree-joints', bm, 'Accueil', M_METAL)


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


def build_elements():
    """Step 2: the fixed elements, at full height. Returns the new objects."""
    for c in ('Bar', 'Banquettes', 'Accueil', 'Rideaux'):
        coll(c)
    avant = set(bpy.data.objects)
    bar_omakase(); banquettes(); tablette_vide(); labo(); rideaux(); bloc_entree(); escalier_detail()
    return [o for o in bpy.data.objects if o not in avant]


# ---- the ground floor under the mezzanine: floor1's map model (the fantôme, its see-through tops included, so its
#      walls rise to the slab), in one light grey without lines, 3.35 m down, stopped under the slab: seen from
#      above it shows only through the voids, seen from the side it is the building the mezzanine stands on
def dessous():
    chemin = RACINE / 'carte' / 'modele' / 'floor1-fantome.glb'
    avant = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(chemin))
    m = mat('dessous', (0.90, 0.90, 0.89), 0.9)
    for o in [o for o in bpy.data.objects if o not in avant]:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        if o.type != 'MESH':
            bpy.data.objects.remove(o)
            continue
        coll('Dessous').objects.link(o)
        o.data = o.data.copy()
        o.data.transform(o.matrix_world); o.matrix_world.identity()
        o.data.transform(__import__('mathutils').Matrix.Translation((0, 0, -H_RDC)))
        if max(v.co.z for v in o.data.vertices) > -DALLE - 0.002:
            couper(o, -DALLE - 0.002, 'bas')
        if not len(o.data.vertices):
            bpy.data.objects.remove(o)
            continue
        o.data.materials.clear(); o.data.materials.append(m)
        o.visible_shadow = False


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
    """As floor1, except that the ground floor seen through the voids (Dessous) is drawn without lines."""
    sc.render.use_freestyle = True
    sc.render.line_thickness_mode = 'ABSOLUTE'
    sc.render.line_thickness = 1.0
    vl = sc.view_layers[0]
    vl.use_freestyle = True
    fs = vl.freestyle_settings
    fs.crease_angle = math.radians(140)
    exclus = coll('Sans-trait-plein')               # the thin-line objects and the ground floor: not in the main lines
    for o in list(coll('Traits-fins').objects) + list(coll('Dessous').objects):
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
    OUT = Path(ARGS.get('out', RACINE / 'rendus' / ('13-etage-elements-fixes' if ELEMENTS else '12-etage-coque')))
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
        if V['cut'] is not None:
            separer(nouveaux, V['cut'], m_ghost if V['ghost'] else None)
    dessous()

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
                                 ('metal', (0.945,) * 3, 0.6)):
            set_mat(name, rgb, rough, a)
        set_mat('pave', (0.95, 0.97, 0.98), 0.25, 0.55 if a == 1.0 else min(a, 0.3))
    o_c = P(837, 1278)
    m_int = mat_grille('sol-grille', (0.975, 0.972, 0.965), (0.80, 0.80, 0.80), 0.35, 0.55, o_c)
    m_ext = mat_grille('terrain-grille', (0.90, 0.898, 0.89), (0.66, 0.66, 0.66), 0.45, 0.8, o_c, fade=(14, 30))
    dalle = bpy.data.objects['dalle']
    dalle.data.materials[0] = m_int             # the walking surface; its edge and underside stay 'dalle'
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
    show(collections_hidden=('Plan',))
    sun.rotation_euler = (math.radians(35), 0, math.radians(-121))

    cam_top = camera('cam-dessus', o_c + Vector((0, 0, 60)), o_c, ortho=21.6)
    cam_top.rotation_euler = (0, 0, math.radians(-90))
    d = Vector((-1, -1.05, 1.15)).normalized()
    c3 = o_c + Vector((0, 0, 0.9))
    cam_3d = camera('cam-3d', c3 + d * 60, c3, ortho=25.5)
    if ARGS.get('plans'):
        for pl in ARGS['plans'].split(','):
            (x0, y0, z0), (x1, y1, z1), lens, *res = PLANS[pl]
            render(f'plan-{pl}', camera(f'cam-{pl}', P(x0, y0, z0), P(x1, y1, z1), lens=lens),
                   res[0] if res else (1500, 1000))
    else:
        render(f'{nom}-dessus', cam_top, (2000, 1250))
        render(f'{nom}-3d', cam_3d, (2000, 1250))
if ARGS.get('save'):
    bpy.ops.wm.save_as_mainfile(filepath=ARGS['save'])
