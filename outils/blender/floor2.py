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
#        blender -b -P floor2.py -- variante=fantome|fil-de-fer elements=1 bloc=0..4 [vues=3d] [plans=ile,ile-bas]
#            (the prototypes for the island over the entry, where the block was)
#        blender -b -P floor2.py -- variante=fantome|fil-de-fer|detail mobilier=1 [plans=...]
#            (step 3, the furniture, as floor1's step 4; also writes modele/floor2-tables.json)
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
PX = 1 / DATA['echelle_px_par_m']        # metres per plan pixel
CX, CY = 837, 1230                       # plan pixel at the world origin (as floor1)
H = 3.0                                  # the mezzanine's clear height (floor to the roof slab), from the section
H_RDC = 3.35                             # the ground floor under it (floor1.py)
DALLE = 0.30                             # the slab
ELEMENTS = ARGS.get('elements') == '1'   # step 2: the fixed elements
MOBILIER = ARGS.get('mobilier') == '1'   # step 3: the furniture (and its table numbers for the map)
ELEMENTS = ELEMENTS or MOBILIER
BLOC_P = int(ARGS.get('bloc', 0))        # the island over the entry, where the block was: 0 empty, 1-4 the prototypes


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
SOL = [(384, 140), (1457, 140), (1457, 2245), (1286, 2245), (1286, 2213), (856, 2213), (856, 2373), (601, 2373),
       (601, 2245), (232, 2245), (232, 842), (384, 842)]          # with the island over the entry, where the block was
# the void over the room: along the ledge (y 1172), round the corner, down the right side, then round the stair
VIDE = [(237, 1172), (1012, 1172)] + arc(1012, 1242, 70, -90, 0, 12)[1:] + [(1082, 1917)] + \
    arc(1020, 1917, 62, 0, 90, 12)[1:] + [(1000, 1990), (861, 2044), (861, 1896), (601, 1896), (601, 2250), (237, 2250)]
# the void over the rock garden (the gravel seen from above on floor2.png)
JARDIN = [(861, 2040), (1057, 2040), (1057, 2126), (1238, 2126)] + arc(1238, 2187, 61, -90, 0, 10)[1:] + \
    [(1299, 2370), (861, 2370)]
HX, HY, R_ESC = 1082, 2172, 184          # the spiral stair (floor1.py: hub, treads to r 180) and its opening
BLOC = (601, 1896, 856, 2373)            # the island over the entry: the block of the plan, removed (25/11), the roof of the entry
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


# ---------------------------------------------------------------- the island over the entry, where the block was
# The user removed the block (25/11) and asked for something else, plant-like. Once the block is gone, its footprint
# is an island over the entry (2.1 x 4.0 m), the roof of the entry box of the ground floor, with the void on three
# sides and no way in from the mezzanine: a place to look at, from above and from below. bloc=1 a hanging garden;
# 2 a curtain of trailing plants falling into the double height; 3 a large tree whose crown spreads over the void;
# 4 a green wall, the volume of the block kept but planted. Each in a planter whose rim is the island's edge.
M_FEUILLE = mat('feuillage', (0.20, 0.26, 0.14), 0.8)
M_TERRE = mat('terre', (0.10, 0.08, 0.06), 1.0)
M_ECORCE = mat('ecorce', (0.15, 0.11, 0.08), 0.8)


def touffe(bm, c, r, graine, sub=2, aplati=1.0):
    """A lump of leaves: a noisy icosphere (as floor1's planters), a little flattened if asked."""
    rnd = random.Random(graine)
    tmp = bmesh.new(); bmesh.ops.create_icosphere(tmp, subdivisions=sub, radius=1.0)
    ph = [rnd.uniform(0, math.tau) for _ in range(3)]
    vs = {}
    for v in tmp.verts:
        k = r * (1 + 0.13 * math.sin(3 * v.co.x + ph[0]) * math.sin(3 * v.co.y + ph[1]) + 0.08 * math.sin(4 * v.co.z + ph[2]))
        vs[v] = bm.verts.new(c + Vector((v.co.x * k, v.co.y * k, v.co.z * k * aplati)))
    for f in tmp.faces:
        bm.faces.new([vs[v] for v in f.verts]).smooth = True
    tmp.free()


def bac(h=0.45, e=10):
    """The planter: a rim of e px round the island, h m high, and its soil 5 cm below the rim."""
    x0, y0, x1, y1 = BLOC
    bm = bmesh.new()
    bm_box(bm, x0, y0, x1, y0 + e, 0.0, h); bm_box(bm, x0, y1 - e, x1, y1, 0.0, h)
    bm_box(bm, x0, y0 + e, x0 + e, y1 - e, 0.0, h); bm_box(bm, x1 - e, y0 + e, x1, y1 - e, 0.0, h)
    mesh_obj('ile-bac', bm, 'Ile', M_MEUBLE)
    bm = bmesh.new(); bm_box(bm, x0 + e, y0 + e, x1 - e, y1 - e, 0.0, h - 0.05)
    mesh_obj('ile-terre', bm, 'Ile', M_TERRE)


def massif(pas=30, rmin=0.14, rmax=0.22, z0=0.40, graine=1, nom='ile-massif'):
    """A dense bed of low plants over the island."""
    x0, y0, x1, y1 = BLOC
    rnd = random.Random(graine); bm = bmesh.new(); k = 0
    for x in range(x0 + 24, x1 - 20, pas):
        for y in range(y0 + 24, y1 - 20, pas):
            r = rnd.uniform(rmin, rmax)
            cx_, cy_ = x + rnd.uniform(-6, 6), y + rnd.uniform(-6, 6)
            rp = r / PX + 2
            pres = min(cx_ - x0, x1 - cx_, cy_ - y0, y1 - cy_) < 10 + rp       # would cross the rim (10 px)
            touffe(bm, P(cx_, cy_, (0.452 + r * 0.95) if pres else (z0 + r * 0.55)), r, graine * 1000 + k, 2, 0.8)
            k += 1
    mesh_obj(nom, bm, 'Ile', M_FEUILLE)


def retombees(longueur, pas, graine, nom):
    """Trailing plants over the three edges on the void, from the rim down `longueur` m, 14 px off the rim: they stay
    outside the walls of the entry box of the ground floor (y 1898, x 599) and stop 2.15 m over its floor."""
    x0, y0, x1, y1 = BLOC
    rnd = random.Random(graine); bm = bmesh.new(); k = 0
    # (start, direction along the edge, outwards); the east side skips the end of the glass parapet (861, 2045)
    bords = [([(x, y0 - 14) for x in range(x0 + 8, x1 - 6, pas)], (1, 0), (0, -1)),
             ([(x0 - 14, y) for y in range(y0 + 8, 2228, pas)], (0, 1), (-1, 0)),
             ([(x1 + 14, y) for y in range(y0 + 8, y1 - 6, pas) if abs(y - 2042) > 24], (0, 1), (1, 0))]
    for pts, (ux, uy), (ox, oy) in bords:
        for x, y in pts:
            L = longueur * rnd.uniform(0.4, 1.0)
            n = max(4, int(L / 0.07))
            ph = rnd.uniform(0, math.tau)
            for i in range(n + 1):
                z = 0.42 - L * i / n
                for j in range(3 if i < n * 0.6 else 2):
                    a = rnd.uniform(-5, 5); b = rnd.uniform(0, 5) + 2 * math.sin(ph + i * 0.6)
                    r = rnd.uniform(0.035, 0.058) * (1 - 0.3 * i / n)
                    b = max(0.0, b)
                    touffe(bm, P(x + ux * a + ox * b, y + uy * a + oy * b, z + rnd.uniform(-0.02, 0.02)), r,
                           graine * 10000 + k, 1)
                    k += 1
    mesh_obj(nom, bm, 'Ile', M_FEUILLE)


def arbre(x, y, h, rc, n, graine, nom):
    """A small tree: a slightly leaning trunk from the soil, a crown of clumps (as floor1's planter trees)."""
    rnd = random.Random(graine)
    bm = bmesh.new()
    pied, tete = P(x, y, 0.40), P(x + rnd.uniform(-8, 8), y + rnd.uniform(-8, 8), h)
    fil(bm, pied, tete, r=0.035, n=8)
    mesh_obj(nom + '-tronc', bm, 'Ile', M_ECORCE)
    bm = bmesh.new()
    for k in range(2 * n):
        a = math.tau * k / (2 * n) + rnd.uniform(-0.3, 0.3)
        d = rc * rnd.uniform(0.15, 0.85)
        c = tete + Vector((d * math.cos(a), d * math.sin(a), rnd.uniform(-0.25, 0.30)))
        touffe(bm, c, rc * rnd.uniform(0.28, 0.38), graine * 100 + k, 2, 0.85)
    touffe(bm, tete + Vector((0, 0, 0.22)), rc * 0.34, graine * 100 + 99, 2, 0.85)
    mesh_obj(nom + '-couronne', bm, 'Ile', M_FEUILLE)


def ile_jardin():
    """bloc=1, the hanging garden: a dense bed, three small trees, plants spilling over the edges (1 m)."""
    bac(); massif()
    arbre(680, 2000, 1.75, 0.42, 8, 3, 'ile-arbre-1'); arbre(785, 2150, 2.05, 0.48, 9, 5, 'ile-arbre-2')
    arbre(690, 2290, 1.6, 0.38, 7, 7, 'ile-arbre-3')
    retombees(1.0, 36, 11, 'ile-retombees')


def ile_rideau():
    """bloc=2, the green curtain: a lower bed and long trailing plants falling 1.6 m into the double height, close set,
    like the curtains of the place."""
    bac(); massif(pas=36, rmin=0.11, rmax=0.17, graine=2)
    retombees(1.6, 14, 13, 'ile-rideau')


def ile_arbre():
    """bloc=3, the tree: one large multi-stemmed tree in the island, its crown at the mezzanine's eye level and above,
    spreading over the void beside the three columns; ground cover at its foot."""
    bac(); massif(pas=40, rmin=0.10, rmax=0.15, graine=3)
    rnd = random.Random(17)
    bm = bmesh.new(); couronne = bmesh.new()
    base = P(728, 2060, 0.40)
    for k, (tx, ty, th) in enumerate(((650, 1960, 2.35), (800, 1990, 2.55), (700, 2180, 2.2))):
        tete = P(tx, ty, th)
        mid = base.lerp(tete, 0.45) + Vector((0, 0, 0.15))
        fil(bm, base, mid, r=0.07, n=10); fil(bm, mid, tete, r=0.05, n=10)
        for j in range(42):                        # a crown of many small clumps, not a few balls
            a = rnd.uniform(0, math.tau); d = rnd.uniform(0.1, 1.05)
            c = tete + Vector((d * math.cos(a), d * math.sin(a), rnd.uniform(-0.25, 0.30) - 0.18 * d))
            c.z = min(c.z, H - 0.35)
            r = rnd.uniform(0.12, 0.20)
            px, py = c.x / PX + CX, -c.y / PX + CY      # the crown keeps clear of the three columns
            if any(math.hypot(px - tx_, py - ty_) < 139 + r / PX + 8 for tx_, ty_ in TAMBOURS_VIDE):
                continue
            rp = r / PX + 4                             # and of the wall at the end of the lab (x < 599.5, y 2245-2276)
            if px - rp < 599.5 and 2245 - rp < py < 2276 + rp:
                continue
            touffe(couronne, c, r, 1700 + 100 * k + j, 2, 0.85)
    mesh_obj('ile-grand-arbre-troncs', bm, 'Ile', M_ECORCE)
    mesh_obj('ile-grand-arbre-couronne', couronne, 'Ile', M_FEUILLE)


def ile_mur():
    """bloc=4, the green wall: the volume of the block kept (2.6 m), its four faces planted, its top too."""
    x0, y0, x1, y1 = BLOC
    e = 16
    bm = bmesh.new(); bm_box(bm, x0 + e, y0 + e, x1 - e, y1 - e, 0.0, 2.60); mesh_obj('ile-mur-noyau', bm, 'Ile', M_MEUBLE)
    rnd = random.Random(23); bm = bmesh.new(); k = 0
    for (ax, a0, a1, fixe, s_) in (('x', x0 + e, x1 - e, y0 + e, -1), ('x', x0 + e, x1 - e, y1 - e, 1),
                                   ('y', y0 + e, y1 - e, x0 + e, -1), ('y', y0 + e, y1 - e, x1 - e, 1)):
        L = (a1 - a0) * PX                          # the face, metres
        for nb, rmin, rmax, sortie in ((150, 0.05, 0.085, 0.6), (30, 0.085, 0.12, 0.75)):   # clumps per m2, two layers
            for i in range(int(L * 2.6 * nb)):
                u = rnd.uniform(a0 + 3, a1 - 3)
                r = rnd.uniform(rmin, rmax)
                z = rnd.uniform(r + 0.02, 2.58 - r * 0.3)
                off = r / PX * sortie
                pres = (ax == 'y' and s_ < 0 and 2230 < u < 2290) or (ax == 'y' and s_ > 0 and 2010 < u < 2075)
                if pres:                                 # the lab's wall (x 599.5) and the end of the glass parapet
                    off = min(off, e - r / PX - 1.5)
                d = fixe + s_ * off
                c = P(u, d, z) if ax == 'x' else P(d, u, z)
                touffe(bm, c, r, 23000 + k, 1); k += 1
    mesh_obj('ile-mur-feuilles', bm, 'Ile', M_FEUILLE)
    rnd = random.Random(29); bm = bmesh.new(); k = 0
    for x in range(x0 + 26, x1 - 20, 28):
        for y in range(y0 + 26, y1 - 20, 28):
            r = rnd.uniform(0.11, 0.16)
            touffe(bm, P(x, y, 2.60 + r * 0.5), r, 29000 + k, 2, 0.8); k += 1
    mesh_obj('ile-mur-dessus', bm, 'Ile', M_FEUILLE)


def build_elements():
    """Step 2: the fixed elements, at full height, the three columns over the drums, and the island's prototype, if
    any. Returns the new objects."""
    for c in ('Bar', 'Banquettes', 'Rideaux', 'Vide', 'Ile'):
        coll(c)
    avant = set(bpy.data.objects)
    bar_omakase(); banquettes(); tablette_vide(); labo(); rideaux(); escalier_detail()
    vide_colonnes()
    {1: ile_jardin, 2: ile_rideau, 3: ile_arbre, 4: ile_mur}.get(BLOC_P, lambda: None)()
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
    cx_, cy_, r = 1476.2, 1515.3, 69.5
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
    """On the lab counter (plan zone 2): a machine, a blender, a bowl (the symbols of the plan)."""
    pc = Piece(); pc.boite(-0.17, -0.15, 0.17, 0.15, 0.0, 0.40, M_ACIER); poser('labo-machine', pc, 432, 900, collection='Mobilier', z=0.90)
    pc = Piece(); pc.cyl(0, 0, 0.07, 0.07, 0.0, 0.18, M_ACIER, 20); pc.cyl(0, 0, 0.06, 0.07, 0.18, 0.38, M_PAVE, 20)
    poser('labo-mixeur', pc, 425, 991.5, collection='Mobilier', z=0.90)
    pc = Piece(); pc.cyl(0, 0, 0.07, 0.11, 0.0, 0.10, M_ACIER, 28); poser('labo-bol', pc, 433, 1050, collection='Mobilier', z=0.90)


def build_mobilier():
    """Step 3: the furniture. Returns the new objects; writes the table list for the live map."""
    for c in ('Mobilier', 'Tables', 'Assises', 'Suspensions'):
        coll(c)
    avant = set(bpy.data.objects)
    liste = []
    for tid, nom, cy in DEMI:
        tc = (1298.5, cy)
        poser(f'table-{tid:02d}', table_ronde(0.40), *tc, collection='Tables')
        poser(f'lampe-{tid:02d}', lampe(), tc[0] + 15, tc[1], collection='Tables', z=0.75)
        poser(f'suspension-{tid:02d}', suspension(1.85, 0.26), *tc, collection='Suspensions')
        for k, dy in enumerate((-44, 44)):
            poser(f'chaise-{tid:02d}-{k + 1}', fauteuil(), 1232.5, cy + dy, vers=tc, collection='Assises')
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
    for k, x in enumerate(TABOURETS_OMAKASE):
        poser(f'tabouret-omakase-{k + 1}', chaise(haute=True), x, 615, vers=(x, 540), collection='Assises')
    liste.append(dict(id=100, nom='Bar omakase', type='bar', centre_px=[880.5, 549], places=6, assises='tabourets'))
    for k, x in enumerate(TABOURETS_VIDE):
        poser(f'tabouret-vide-{k + 1}', chaise(haute=True), x, 1080, vers=(x, 1172), collection='Assises')
    liste.append(dict(id=101, nom='Tablette du vide', type='bar', centre_px=[756, 1143], places=6, assises='tabourets'))
    tablette_facade()
    labo_machines()
    bm = bmesh.new(); bm_box(bm, 1374, 2008, 1440, 2208, 0.0, 0.85)            # the sideboard at the end of the facade
    mesh_obj('console-facade', bm, 'Mobilier', M_BOIS)
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
    # step 3
    'grande':    ((1160, 1140, 1.55), (800, 820, 0.70), 22),     # the long table and the omakase bar beyond
    'demi':      ((1080, 1180, 1.40), (1290, 900, 0.75), 24),    # the two half drums
    'facade':    ((1150, 2090, 1.55), (1330, 1350, 0.95), 26),   # the high tables along the facade
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
    OUT = Path(ARGS.get('out', RACINE / 'rendus' / ('16-etage-prototypes-ile' if 'bloc' in ARGS else
                                                    '15-etage-mobilier' if MOBILIER else
                                                    '13-etage-elements-fixes' if ELEMENTS else '12-etage-coque')))
    pre = f"b{BLOC_P}-" if 'bloc' in ARGS else ''
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
                                 ('lumiere', (0.995, 0.99, 0.975), 0.4), ('feuillage', (0.90, 0.92, 0.88), 0.9),
                                 ('terre', (0.86, 0.85, 0.83), 1.0), ('ecorce', (0.88, 0.87, 0.85), 0.9)):
            set_mat(name, rgb, rough, a)
        set_mat('pave', (0.95, 0.97, 0.98), 0.25, 0.55 if a == 1.0 else min(a, 0.3))
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
