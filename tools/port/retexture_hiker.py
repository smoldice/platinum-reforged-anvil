#!/usr/bin/env python3
"""Black 2's Hiker, sprite 73 of a/0/7/1, with its own animation, recoloured to Platinum's Hiker: green sleeves and
collar, yellow trousers, a red pack and straps, a brown stick, and Platinum's skin, all in Platinum's colours. His hat,
vest, bedroll and boots keep their colours (Platinum's are alike), and his hat its red band. A recolour only: every
shape stays Black 2's. The settings for retexture.py, which says how.

build(b2_files, src) returns the 8 files, from sprite 73's files and Platinum's front.png.

Usage, to preview and check (in the container, from tools/port):
  retexture_hiker.py B2_ROM POKEPLATINUM_DIR OUT_DIR
"""
import sys

import retexture

B2_SPRITE = 73
PLATINUM_CLASS = "hiker"

GREEN_DARK, YELLOW, TAN, GREY_BROWN, BROWN, GREEN, RED, RED_DARK = 1, 2, 3, 5, 6, 7, 8, 9
BLACK = 15
# Black 2's palette slots, with Platinum's colours, which match them one for one but for Black 2's darkest brown
# (slot 7) and Platinum's mid green: the darkest brown goes (black in the beard, the dark brown elsewhere) and its slot
# takes the sleeves' green
PALETTE = {GREEN_DARK: (49, 90, 82), YELLOW: (238, 213, 123), TAN: (189, 164, 106), 4: (139, 123, 98),
           GREY_BROWN: (106, 90, 90), BROWN: (74, 57, 49), GREEN: (65, 139, 98), RED: (238, 98, 65),
           RED_DARK: (180, 65, 74), 10: (255, 213, 189), 11: (222, 164, 123), 12: (172, 123, 98), 13: (123, 74, 90),
           14: (238, 238, 255)}
NO_DARKEST = {7: BROWN}
# The sleeves' oranges Platinum's greens; the pack's green (and its straps') Platinum's red
SLEEVE = {RED: GREEN, RED_DARK: GREEN_DARK}
PACK = {GREEN_DARK: RED_DARK}
# By cell: (first row, last row) of the cell, and old slot -> new slot there
REMAPS = {
    0: [((0, 31), {7: BLACK})],  # the head: the beard's darkest strands black
    # the vest: its collar the shirt's, its straps the pack's; below its bottom line (rows 34-36) Black 2 draws the
    # trousers' top in this part, which takes the trousers' colours (the owner's note: their shadow under the belly is
    # one colour, as Black 2's)
    1: [((0, 33), {**NO_DARKEST, **SLEEVE, **PACK}), ((34, 39), {7: TAN, BROWN: YELLOW})],
    2: [((0, 39), {7: TAN, BROWN: YELLOW})],  # the trousers yellow, tan in the belly's shadow
    3: [((0, 31), PACK)],  # the bedroll, and the pack's top
    4: [((0, 31), PACK)],  # the pack
    5: [((0, 31), {**NO_DARKEST, **SLEEVE})],  # the waving arm
    6: [((0, 31), {**NO_DARKEST, **SLEEVE, **PACK})],  # the shoulder, and the pack behind it
    7: [((0, 31), {**NO_DARKEST, **SLEEVE, **PACK})],  # the other arm, and the strap beside it
    8: [((0, 23), NO_DARKEST)],  # the boots
    # the stick, below the hand, Platinum's wood: Black 2's white pole grey-brown, edged dark brown
    9: [((0, 17), NO_DARKEST), ((18, 55), {14: GREY_BROWN, **NO_DARKEST})],
}
CHARS_REMAP = {}
HEADS = {}  # no hair graft
TROUSERS, LIGHT_BROWN, STICK = 2, 4, 9
# The owner's paint, 2026-10-17, from sheets at tick 0 (scratch/hiker_boots/boots_paint_2.png, frame x 40-75,
# y 98-121; scratch/hiker_stick/stick_paint.png, frame x 54-79, y 68-123), by cell: {(x, y) in the cell: slot}, after
# the remaps. The trousers' hem over the left boot, which Black 2 outlines black, light brown; the stick's flecks of
# Black 2's tans grey-brown, one dark brown
TOUCH_UPS = {
    TROUSERS: {(19, 32): LIGHT_BROWN, (14, 33): LIGHT_BROWN, (15, 33): LIGHT_BROWN, (16, 33): LIGHT_BROWN},
    STICK: {(13, 19): GREY_BROWN, (12, 20): GREY_BROWN, (14, 26): GREY_BROWN, (12, 27): GREY_BROWN, (15, 36): BROWN,
            (13, 37): GREY_BROWN},
}


def customize(sprite, src, tick):
    px = sprite["tex"].load()
    for c, pixels in TOUCH_UPS.items():
        s, t, w, h = retexture.cell_box(sprite, c)
        for (x, y), v in pixels.items():
            px[s + x, t + y] = v


def build(b2_files, src):
    return retexture.build(sys.modules[__name__], b2_files, src)


if __name__ == "__main__":
    sys.argv[3:3] = ["retexture_hiker"]
    retexture.main()
