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

RDC_SANS = {55, 437,
            408, 421,     # (26/11 evening) the thin partition by the stair, with a closed strip behind: the wine room
            13, 14, 15, 35,   # (26/11 night) the back of house behind the bar: the store's wall along the facade, the
                              # two toilets' maze of thin walls, the stubs of the electrical room (see KITCHEN below)
            16, 36}           # (26/11 night, A chosen) the shaft under the 1st floor's: a 0.9 m box open at its south
                              # end, which read as a dead-end corridor; the kitchen takes the corner to the facade
RDC_REMPLACE = {
    288: [[(1272, 2245), (1447, 2245), (1447, 2233), (1457, 2233), (1457, 2276), (1272, 2276)]],
    440: [[(1299.5, 2276), (1308.5, 2276), (1308.5, 2298), (1299.5, 2298)],
          [(1299.5, 2378), (1308.5, 2378), (1308.5, 2411.5), (1299.5, 2411.5)]],
    # (26/11, no gap left in the walls) the entry's left wall down to the street front, room 4's two south walls as one
    439: [[(567, 2276), (576, 2276), (576, 2411.5), (567, 2411.5)]],
    432: [[(1285, 2228), (1447, 2228), (1447, 2245), (1285, 2245)]],
    # (26/11 night) a stub on the right facade went 4 cm into the glass blocks: stopped on their inner face
    364: [[(1411.0, 1757.0), (1447.0, 1757.0), (1447.0, 1767.0), (1411.0, 1767.0)]],
}
# the slits the plan left between walls that meet (1 - 3 cm): filled
RDC_JOINTS = [(480, 41.5, 482, 146.5), (1419, 42, 1421, 146), (596.5, 2243, 608, 2276),
              (1273, 2228, 1285, 2245),
              # the pocket between the room of wall 16, wall 17 and column 40 (with a cheek on the column, floor1.py)
              (1447, 635, 1453, 737.5), (1453, 636.5, 1461, 737.5)]
ANGLE_SE = (1445.5, 2397, 1481, 2414)     # the south-east corner pier, the same on both storeys
RDC_AJOUT = [[(ANGLE_SE[0], ANGLE_SE[1]), (ANGLE_SE[2], ANGLE_SE[1]), (ANGLE_SE[2], ANGLE_SE[3]), (ANGLE_SE[0], ANGLE_SE[3])],
             # (26/11) the north-east corner: the plan left the right side open between walls 7 and 17 (y 146 - 281)
             [(1453, 146), (1481, 146), (1481, 281), (1453, 281)],
             # (26/11 night) the kitchen's west wall, which is the toilets' east wall; the toilets' south wall on either
             # side of their door (397 - 505); the lobby's south wall, behind the back bar's west end
             [(640, 146.5), (650, 146.5), (650, 470), (640, 470)],
             [(387, 352), (397, 352), (397, 362), (387, 362)],
             [(505, 352), (640, 352), (640, 362), (505, 362)],
             [(580, 460), (640, 460), (640, 470), (580, 470)],
             # (26/11 night) without the shaft, the right facade's inner face made straight (x 1447) from the north
             # wall to the pocket by column 40: the kitchen's east wall, then the service bay's
             [(1447, 146), (1453, 146), (1453, 635), (1447, 635)]]

# (26/11 night) the back of house behind the bar, reworked (floor1.py): the kitchen right behind the bar, open on it
# over a low wall (prototype A, chosen), from the toilets' wall to the right facade; the pass at the bar's service end;
# the double swing door, 1.57 m wide, on the service bay right of the bar
KITCHEN = (650, 105, 1447, 460)
KITCHEN_SUD = (460, 470)
PASSE = (1072, 1182)
KITCHEN_PORTE = (1208, 1396)
SERVICE = (1194, 470, 1447, 737.5)       # the service bay, between the bar's end, the kitchen's doors and the facade
WC = (387, 146.5, 640, 352)
WC_PORTE = (397, 505)

# (26/11 evening) the wine room: the strip between the stair's garden and the right facade, which the plan closed
# with a thin partition (408, 421) and left empty. Glazed on the stair's side (x 1273 - 1283, as the partition was)
# and at its north end (y 1884 - 1894), with a glass door there; inside, from its glass to the glass blocks
CAVE = (1283, 1894, 1447, 2228)
CAVE_PORTE = (1284, 1380)           # the door leaf, hinged by the corner post

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
