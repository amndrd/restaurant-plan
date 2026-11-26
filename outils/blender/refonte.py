# The reworked building (26/11): from here on the model no longer follows the client's plan where it made no sense
# for a two-storey restaurant. Shared by floor1.py (the ground floor) and floor2.py (the slab under the mezzanine
# runs under the same walls). Plan pixels, as floor1-murs.json.
#
# The ground floor's walls changed:
# - 55 and the right part of 288: an outer band in front of the right facade's glass blocks, which hid them from the
#   street (the facade read as a blind wall): removed, the glass blocks show between the columns;
# - 437: a box stuck past the right facade, open at the side, with nothing in it: removed. Its place, between the
#   entry and the right facade, becomes the cloakroom of the entry, behind the same glass blocks as the entry;
# - 440: the wall between the entry and that corner gets an opening (the cloakroom's door);
# - a corner pier closes the building at the south-east, on both storeys; the cloakroom has glass blocks on the
#   street and on the right side, as the room next to it.

RDC_SANS = {55, 437}
RDC_REMPLACE = {
    288: [[(1272, 2245), (1447, 2245), (1447, 2233), (1457, 2233), (1457, 2276), (1272, 2276)]],
    440: [[(1299.5, 2276), (1308.5, 2276), (1308.5, 2298), (1299.5, 2298)],
          [(1299.5, 2378), (1308.5, 2378), (1308.5, 2411.5), (1299.5, 2411.5)]],
    # (26/11, no gap left in the walls) the entry's left wall down to the street front, room 4's two south walls as one
    439: [[(567, 2276), (576, 2276), (576, 2411.5), (567, 2411.5)]],
    432: [[(1285, 2228), (1447, 2228), (1447, 2245), (1285, 2245)]],
}
# the slits the plan left between walls that meet (1 - 3 cm): filled
RDC_JOINTS = [(480, 41.5, 482, 146.5), (1419, 42, 1421, 146), (1451, 281, 1453, 635), (596.5, 2243, 608, 2276),
              (426, 146, 435, 148), (640, 148, 642, 227), (1283, 2228, 1285, 2245), (1273, 2243, 1283, 2245),
              # the pocket between the room of wall 16, wall 17 and column 40 (with a cheek on the column, floor1.py)
              (1447, 635, 1453, 737.5), (1453, 636.5, 1461, 737.5)]
ANGLE_SE = (1445.5, 2397, 1481, 2414)     # the south-east corner pier, the same on both storeys
RDC_AJOUT = [[(ANGLE_SE[0], ANGLE_SE[1]), (ANGLE_SE[2], ANGLE_SE[1]), (ANGLE_SE[2], ANGLE_SE[3]), (ANGLE_SE[0], ANGLE_SE[3])],
             # (26/11) the north-east corner: the plan left the right side open between walls 7 and 17 (y 146 - 281)
             [(1453, 146), (1481, 146), (1481, 281), (1453, 281)]]

# the cloakroom (between the entry and the corner pier, inside the glass blocks) and the street front (y 2406.5):
# the mullions of the glass blocks, from the shopfront to the corner pier
VESTIAIRE = (1308.5, 2276, 1447, 2402)
MONTANTS_SUD = [861, 1068, 1296.5, 1311.5, 1442.5]
DEVANTURE = (576, 861)              # the shopfront: a fixed pane, the double door, a fixed pane
PORTE = (650, 790)


def murs_rdc(data):
    """The ground floor's wall outlines (lists of (x, y)), reworked; with their holes, as (name, loops)."""
    murs = []
    for mu in data['murs']:
        if mu['id'] in RDC_SANS:
            continue
        if mu['id'] in RDC_REMPLACE:
            for k, c in enumerate(RDC_REMPLACE[mu['id']]):
                murs.append((f"{mu['id']}-{k}", [c]))
            continue
        murs.append((str(mu['id']), [mu['contour']] + mu['trous']))
    for k, c in enumerate(RDC_AJOUT):
        murs.append((f'angle-{k}', [c]))
    for k, (x0, y0, x1, y1) in enumerate(RDC_JOINTS):
        murs.append((f'joint-{k}', [[(x0, y0), (x1, y0), (x1, y1), (x0, y1)]]))
    return murs
