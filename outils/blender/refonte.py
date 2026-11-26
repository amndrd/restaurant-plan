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
    440: [[(1299.5, 2284.5), (1308.5, 2284.5), (1308.5, 2298), (1299.5, 2298)],
          [(1299.5, 2378), (1308.5, 2378), (1308.5, 2399.5), (1299.5, 2399.5)]],
}
ANGLE_SE = (1445.5, 2397, 1481, 2414)     # the south-east corner pier, the same on both storeys
RDC_AJOUT = [[(ANGLE_SE[0], ANGLE_SE[1]), (ANGLE_SE[2], ANGLE_SE[1]), (ANGLE_SE[2], ANGLE_SE[3]), (ANGLE_SE[0], ANGLE_SE[3])]]

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
    return murs
