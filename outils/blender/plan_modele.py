# The plans drawn from the model (26/11): run at the end of floor1.py / floor2.py (`trace=<file.json>`), it reads the
# built model as an architect's plan reads a building, cut by a horizontal plane at 1.20 m:
#   - every object is split into its loose parts (a chair: its legs, its seat, its back);
#   - a part crossing the plane gives its section: the edges where the plane cuts it (`seg`), closed rings for a solid,
#     open lines for a sheet (a pane, a curtain);
#   - what lies under the plane is seen from above: the part's faces below the cut, projected flat (`bas`);
#   - what lies above it is dropped, except for the collections asked for (the stair's upper treads, dashed: `haut`).
# The coordinates are written in the plan's own pixels (120 px = 1 m, the frame of floor1.png / floor2.png), so the
# drawing (outils/plans/depuis_modele.py) keeps the kit and the framing of the redrawn plans.
import json
import bmesh
import bpy


# what lies above the cut and is drawn dashed on an architect's plan: the stair's upper flight, the hood, the soffits
# and lintels, the glazing's heads (the drawing keeps only the parts entirely above the cut)
HAUT = ('Escalier', 'Cuisine', 'Coque', 'Vitrages', 'Bar')


def tracer(chemin, CX, CY, PX, coupe=1.2, haut=('Escalier',), exclure=('Plan', 'Sans-trait')):
    dg = bpy.context.evaluated_depsgraph_get()
    k = 1 / PX

    def px(v):
        return round(v.x * k + CX, 2), round(CY - v.y * k, 2)

    parties = []
    for o in bpy.data.objects:
        if o.type != 'MESH' or o.name == 'terrain':
            continue
        cs = [c.name for c in o.users_collection]
        if any(c in exclure for c in cs):
            continue
        oe = o.evaluated_get(dg)
        me = oe.to_mesh()
        bm = bmesh.new()
        bm.from_mesh(me)
        oe.to_mesh_clear()
        bm.transform(o.matrix_world)
        if not bm.faces:
            bm.free()
            continue
        mats = [s.material.name if s.material else '' for s in o.material_slots]

        # loose parts: union-find over the edges
        bm.verts.index_update()
        pere = list(range(len(bm.verts)))

        def racine(a):
            while pere[a] != a:
                pere[a] = pere[pere[a]]
                a = pere[a]
            return a
        for e in bm.edges:
            a, b = racine(e.verts[0].index), racine(e.verts[1].index)
            if a != b:
                pere[a] = b
        lay = bm.faces.layers.int.new('partie')
        ids = {}
        for f in bm.faces:
            f[lay] = ids.setdefault(racine(f.verts[0].index), len(ids))
        n = len(ids)
        z0, z1 = [9e9] * n, [-9e9] * n
        compte = [dict() for _ in range(n)]
        for f in bm.faces:
            p = f[lay]
            for v in f.verts:
                z = v.co.z
                if z < z0[p]:
                    z0[p] = z
                if z > z1[p]:
                    z1[p] = z
            m = mats[f.material_index] if f.material_index < len(mats) else ''
            compte[p][m] = compte[p].get(m, 0) + 1
        coupees = {p for p in range(n) if z0[p] < coupe - 1e-4 and z1[p] > coupe + 1e-4}

        seg = [[] for _ in range(n)]
        if coupees:
            res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, coupe),
                                         plane_no=(0, 0, 1))
            for e in res['geom_cut']:
                if isinstance(e, bmesh.types.BMEdge) and e.link_faces:
                    p = e.link_faces[0][lay]
                    if p in coupees:
                        a, b = px(e.verts[0].co), px(e.verts[1].co)
                        if a != b:
                            seg[p] += [*a, *b]

        bas = [[] for _ in range(n)]
        dessus = [[] for _ in range(n)]
        garder_haut = any(c in haut for c in cs)
        for tri in bm.calc_loop_triangles():
            f = tri[0].face
            a, b, c = (px(l.vert.co) for l in tri)
            aire = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
            if abs(aire) < 0.02:                    # a vertical face: no area seen from above
                continue
            zc = sum(l.vert.co.z for l in tri) / 3
            if zc <= coupe + 1e-5:
                bas[f[lay]] += [*a, *b, *c]
            elif garder_haut:
                dessus[f[lay]] += [*a, *b, *c]
        bm.free()
        for p in range(n):
            if not (bas[p] or seg[p] or dessus[p]):
                continue
            parties.append(dict(o=o.name, c=cs, m=max(compte[p], key=compte[p].get), p=p,
                                z0=round(z0[p], 4), z1=round(z1[p], 4), bas=bas[p], seg=seg[p], haut=dessus[p]))
    with open(chemin, 'w') as fh:
        json.dump(dict(coupe=coupe, px_par_m=k, parties=parties), fh, separators=(',', ':'))
    print('trace', chemin, len(parties), 'parties,', sum(len(p['bas']) for p in parties) // 6, 'triangles,',
          sum(len(p['seg']) for p in parties) // 4, 'segments')
