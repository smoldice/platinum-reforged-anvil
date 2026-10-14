#!/usr/bin/env python3
"""Black 2's Ace Trainer (female), sprite 48 of a/0/7/1, with its own animation, retextured to look like Platinum's
Ace Trainer (female): Platinum's colours (brown jacket and skirt, orange chest, dark legs, green boots and hair) and
Platinum's hair, all dark green at its edges as Platinum draws it, mirrored onto Black 2's heads. Black 2's skirt
stays, in the jacket's colours. Black 2's curly pigtails go: Platinum's ponytail hangs from the back of her head
on the pigtail that hung there, drawn behind her. The settings for retexture.py, which says how.

build(b2_files, src) returns the 8 files, from sprite 48's files and Platinum's front.png.

Usage, to preview and check (in the container, from tools/port):
  retexture_ace_trainer_female.py B2_ROM POKEPLATINUM_DIR OUT_DIR
"""
import sys

import retexture

B2_SPRITE = 48
PLATINUM_CLASS = "ace_trainer_female"
# Black 2's palette slots, with Platinum's colours (Platinum's Ace Trainers share one palette). Slot 1, a reddish trim,
# becomes the darkest hair green
PALETTE = {1: (49, 65, 57), 3: (205, 123, 90), 4: (98, 74, 65), 5: (65, 106, 74), 6: (98, 148, 82), 7: (139, 82, 82),
           14: (65, 49, 65)}
HAIR_DARK, HAIR_MID, HAIR_LIGHT = 1, 5, 6
# By cell: (first row, last row) of the cell, and old slot -> new slot there
REMAPS = {
    # the pigtails: their navy shading green, their navy outline black, their hair ties brown
    3: [((0, 31), {4: HAIR_DARK, 14: 15, 3: 7, 1: 4})],
    4: [((0, 39), {4: HAIR_DARK, 14: 15, 3: 7, 1: 4})],
    5: [((0, 31), {1: 7})],  # the jacket's reddish panels -> brown
    6: [((0, 31), {1: 7})],  # the skirt's reddish hem -> brown (its orange is Platinum's orange)
    7: [((0, 31), {3: 7, 1: 4})],  # cuffs -> brown
    8: [((0, 15), {3: 7, 1: 4})],
    9: [((0, 31), {3: 7, 1: 4})],
    13: [((0, 31), {3: HAIR_LIGHT, 1: HAIR_MID, 11: HAIR_DARK})],  # the front boot -> green
    14: [((0, 31), {3: HAIR_LIGHT, 1: HAIR_MID, 11: HAIR_DARK})],
    16: [((0, 31), {1: HAIR_MID, 11: HAIR_DARK})],  # the back boot -> green
}
# File 0's change: slot 1's pixels, the reddish trim, to brown
CHARS_REMAP = {1: 4}

# The heads: Black 2's three (the second blinks, the third talks), all at the same rows
HEADS = {0: 0, 1: 0, 2: 0}
HEAD_SIZE = 32
B2_HAIR = {6: HAIR_LIGHT, 5: HAIR_MID}  # Black 2's hair slots, and the green each becomes
B2_HAIR_SHADE = 4  # the slot that shades Black 2's hair (and colours its clothes): dark green where it touches hair
FACE = {2, 8, 9, 10, 11, 12, 13}
# Platinum edges her hair in dark green. Black 2 edges it in black and, at the back of her head where the pigtails
# were tied, in its dark reddish brown: where those touch her hair and not her skin, they're dark green, and so is the
# hair's lower outline
HAIR_EDGE, SKIN = (11, 15), {2, 8, 9, 10, 12, 13}
EDGE_DARK = HAIR_DARK
# The eyes, which the hair never covers: these slots, and the dark pixels by the skin in these rows and columns
EYE_SLOTS = (12, 13)
EYE_ROWS, EYE_COLS = range(15, 21), range(12, 24)
EYE_DARK, EYE_NEAR = (4, 11, 15), (8, 9, 10, 11, 12, 13)
# Black 2 (x, y) <- Platinum (PT_MIRROR - x, y - PT_DY - dy): Platinum's near eye (x 43, rows 19-20) on Black 2's
# (x 16, rows 18-19), its far eye (x 36) a pixel past Black 2's (x 22)
PT_MIRROR, PT_DY = 59, -1
# Platinum's hair, right of her raised hand
PT_HAIR_ROWS, PT_HAIR_COLS = range(6, 30), range(32, 64)
# Platinum's black pixels that outline her hair, not her face, clothes or hand
PT_HAIR_OUTLINE = {(33, 17), (34, 18), (60, 20), (58, 21), (59, 21), (56, 22), (57, 22), (55, 23), (56, 24), (57, 25),
                   (58, 25), (59, 26), (46, 27), (59, 27), (47, 28), (48, 28), (52, 28), (53, 28), (57, 28), (58, 28),
                   (49, 29), (50, 29), (51, 29), (54, 29), (55, 29), (56, 29)}
PT_TO_B2 = {4: HAIR_LIGHT, 5: HAIR_MID, 6: HAIR_DARK}
# Platinum's forehead showing between locks (to this row) comes along, in Black 2's skin
PT_SKIN_TO_B2 = {0xA: 8, 0xB: 9, 0xC: 10}
PT_SKIN_MAX_ROW = 17
# Platinum's hair may reach past Black 2's head down to this row (below, the ponytail takes it), and covers Black 2's
# face only above this one, her eyes'
TRIM_ROW = 14
FACE_KEEP_FROM_ROW = 16


# The parts this changes: the cell animations their nodes play
HEAD_SEQ, PONYTAIL_SEQ, OTHER_PIGTAIL_SEQ = 0, 2, 1
# The ponytail: Platinum's hair, mirrored as on the head, from this row of the head down and this column back
PONYTAIL_FROM_ROW, PONYTAIL_TO_COL = 12, 12


def customize(sprite, src, tick):
    tex = sprite["tex"]
    px = tex.load()

    # The pigtails go
    for seq in (PONYTAIL_SEQ, OTHER_PIGTAIL_SEQ):
        for frame in sprite["nanr"][seq][1]:
            retexture.clear_cell(tex, retexture.cell_box(sprite, frame[0]))

    # The ponytail: Platinum's hair behind and below the head, where the head's graft puts it, drawn by the back
    # pigtail's node, which goes behind everything else
    hx, hy, _ = retexture.cell_origin(sprite, HEAD_SEQ, tick)
    pp = src.load()
    hair = {}
    for py in PT_HAIR_ROWS:
        for ptx in PT_HAIR_COLS:
            v = pp[ptx, py]
            bx, by = PT_MIRROR - ptx, py + PT_DY
            if by < PONYTAIL_FROM_ROW or bx > PONYTAIL_TO_COL:
                continue
            if v in PT_TO_B2:
                hair[(hx + bx, hy + by)] = PT_TO_B2[v]
            elif v == 0xF and (ptx, py) in PT_HAIR_OUTLINE:
                hair[(hx + bx, hy + by)] = 15
    nx, ny, cell = retexture.node_at(sprite, PONYTAIL_SEQ, tick)
    s, t, w, h = retexture.cell_box(sprite, cell)
    left, top = min(x for x, _ in hair), min(y for _, y in hair)
    width, height = max(x for x, _ in hair) - left + 1, max(y for _, y in hair) - top + 1
    assert width <= w and height <= h, "the ponytail doesn't fit the pigtail's room"
    for (x, y), v in hair.items():
        px[s + x - left, t + y - top] = v
    sprite["rects"][cell] = ((left - nx) * 256, (ny - top) * 256, width * 4096, height * 4096, s * 4096, t * 4096)
    nodes = sprite["nmcr"][0]
    pony = next(n for n in nodes if n[0] == PONYTAIL_SEQ)
    nodes.remove(pony)
    nodes.append(pony)


def build(b2_files, src):
    return retexture.build(sys.modules[__name__], b2_files, src)


if __name__ == "__main__":
    sys.argv[3:3] = ["retexture_ace_trainer_female"]
    retexture.main()
