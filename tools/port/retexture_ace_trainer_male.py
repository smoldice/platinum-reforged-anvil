#!/usr/bin/env python3
"""Black 2's Ace Trainer (male), sprite 49 of a/0/7/1, with its own animation, retextured to look like Platinum's Ace
Trainer (male): Platinum's colours (brown jacket and pants, orange chest, green belt, boots and hair) and Platinum's
hair, mirrored onto Black 2's head. The settings for retexture.py, which says how.

build(b2_files, src) returns the 8 files, from sprite 49's files and Platinum's front.png.

Usage, to preview and check (in the container, from tools/port):
  retexture_ace_trainer_male.py B2_ROM POKEPLATINUM_DIR OUT_DIR
"""
import sys

import retexture

B2_SPRITE = 49
PLATINUM_CLASS = "ace_trainer_male"
# Black 2's palette slots, with Platinum's colours. Slot 6, a reddish trim, becomes the third hair green
PALETTE = {1: (65, 49, 65), 2: (65, 106, 74), 3: (98, 148, 82), 4: (98, 74, 65), 5: (139, 82, 82), 6: (49, 65, 57),
           8: (205, 123, 90)}
HAIR_DARK, HAIR_MID, HAIR_LIGHT = 6, 2, 3
# By cell: (first row, last row) of the cell, and old slot -> new slot there
REMAPS = {
    2: [((0, 22), {6: 5}),  # the chest's reddish shading -> brown
        ((23, 25), {6: HAIR_LIGHT, 5: HAIR_MID, 12: HAIR_DARK, 4: HAIR_DARK})],  # the belt -> green
    3: [((0, 31), {6: 11, 8: 10})],  # the hanging hand -> skin
    5: [((0, 31), {8: 5, 6: 4})],  # cuffs -> brown
    6: [((0, 31), {8: 5, 6: 4})],
    # the pants: darker than the jacket, as Platinum's (front leg brown, back leg dark purple), black outlines
    7: [((0, 31), {5: 4, 4: 1, 1: 15})],
    8: [((0, 17), {5: 4, 4: 1, 1: 15}),
        ((0, 31), {6: HAIR_MID, 8: HAIR_LIGHT, 12: HAIR_DARK})],  # the back boot -> green
    9: [((0, 31), {8: 4, 6: 4, 5: 4, 4: 1, 1: 15})],  # no stripe: solid, as Platinum's
    10: [((0, 14), {8: 4, 6: 4, 5: 4, 4: 1, 1: 15}),
         ((15, 31), {8: HAIR_LIGHT, 6: HAIR_MID, 12: HAIR_DARK, 5: 4, 4: 1, 1: 15})],  # the front boot -> green
}
# File 0's change: slot 6's pixels, the reddish trim, to brown
CHARS_REMAP = {6: 5}

# The heads: head cell -> its rows' offset from head 0's (the second is Black 2's grin, one row lower)
HEADS = {0: 0, 1: 1}
HEAD_SIZE = 32
B2_HAIR = {3: HAIR_LIGHT, 2: HAIR_MID}  # Black 2's hair slots, and the green each becomes
B2_HAIR_SHADE = 4  # the slot that shades Black 2's hair (and colours its clothes): dark green where it touches hair
FACE = {7, 9, 10, 11, 12, 13, 14}
# The eyes, which the hair never covers: these slots, and the dark pixels by the skin in these rows and columns
EYE_SLOTS = (13, 14)
EYE_ROWS, EYE_COLS = range(15, 20), range(9, 19)
EYE_DARK, EYE_NEAR = (4, 15), (9, 10, 11, 12, 13, 14)
# Black 2 (x, y) <- Platinum (PT_MIRROR - x, y - PT_DY - dy): Platinum's near eye (x 38-40, rows 15-17) on Black 2's
# (x 16-17, rows 16-18). The faces are the same size
PT_MIRROR, PT_DY = 56, 1
PT_HAIR_ROWS, PT_HAIR_COLS = range(4, 18), range(80)
# Platinum's black pixels that outline its hair (the underside of the spikes, the side lock), not its face
PT_HAIR_OUTLINE = {(28, 13), (29, 14), (30, 14), (30, 15), (31, 16), (31, 17)}
PT_TO_B2 = {4: HAIR_LIGHT, 5: HAIR_MID, 6: HAIR_DARK}
# Platinum's forehead showing between locks (to this row) comes along, in Black 2's skin
PT_SKIN_TO_B2 = {0xA: 9, 0xB: 10, 0xC: 11}
PT_SKIN_MAX_ROW = 15
# Platinum's hair may reach past Black 2's head down to this row (head 0's)
TRIM_ROW = 15


def build(b2_files, src):
    return retexture.build(sys.modules[__name__], b2_files, src)


if __name__ == "__main__":
    sys.argv[3:3] = ["retexture_ace_trainer_male"]
    retexture.main()
