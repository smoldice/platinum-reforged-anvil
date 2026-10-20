#!/usr/bin/env python3
"""Black 2's Youngster, sprite 2 of a/0/7/1, with its own animation, recoloured to Platinum's Youngster: the cap
Platinum's blues, the tank top Platinum's reds, the shorts and shoes Platinum's blues, the Poké Ball and the greys and
white Platinum's, and Platinum's skin. A recolour only: every shape stays Black 2's. The settings for retexture.py,
which says how.

build(b2_files, src) returns the 8 files, from sprite 2's files and Platinum's front.png.

Usage, to preview and check (in the container, from tools/port):
  retexture_youngster.py B2_ROM POKEPLATINUM_DIR OUT_DIR
"""
import sys

import retexture

B2_SPRITE = 2
PLATINUM_CLASS = "youngster"

CAP, CAP_SHADE, CAP_DARK, RED, GREY, HAIR_DARK, HAIR, RED_SHADE, RED_DARK = 1, 2, 3, 4, 5, 6, 7, 8, 9
SKIN_LIGHT, SKIN, SKIN_DARK, SKIN_LINE, WHITE = 10, 11, 12, 13, 14
# Black 2's palette slots, with Platinum's colours. The oranges draw both his cap and his tank top: they become the
# cap's blues, and the tank top takes Platinum's shirt reds (remapped below). The red of the ball and the mouth is the
# shirt's light red; slots 8 and 9, which Black 2 leaves unused, its shade and its darkest. The shorts' olives (also
# the shoes') take the cap's blues, Platinum's shorts being the same blues, which frees slots 6 and 7 for Platinum's
# hair browns (Black 2 draws his hair black). The grey and white Platinum's
PALETTE = {CAP: (65, 106, 222), CAP_SHADE: (49, 74, 172), CAP_DARK: (49, 57, 82), RED: (230, 90, 65),
           GREY: (172, 180, 172), HAIR_DARK: (57, 49, 49), HAIR: (123, 90, 65), RED_SHADE: (164, 74, 57),
           RED_DARK: (98, 57, 65), SKIN_LIGHT: (255, 213, 189), SKIN: (222, 164, 123), SKIN_DARK: (189, 123, 98),
           SKIN_LINE: (123, 74, 90), WHITE: (238, 238, 255)}
# By cell: (first row, last row) of the cell, and old slot -> new slot there. The tank top: the torso (cell 4), the
# shoulders' edges (3, 7) and, in the still frame (13), everything below the head. The shorts and shoes: every cell
# with them, after the tank top's remap
SHIRT = {CAP: RED, CAP_SHADE: RED_SHADE, CAP_DARK: RED_DARK}
SHORTS = ((0, 63), {6: CAP, 7: CAP_SHADE})
REMAPS = {3: [((0, 15), SHIRT)], 4: [((0, 39), SHIRT), SHORTS], 7: [((0, 15), SHIRT)],
          8: [SHORTS], 9: [SHORTS], 10: [SHORTS], 12: [SHORTS], 13: [((22, 63), SHIRT), SHORTS]}
CHARS_REMAP = {}
HEADS = {}  # no hair graft
# By cell, {(x, y) in the cell: slot}, after the remaps: the hair Platinum's browns where Black 2 draws it black. In
# the cap's opening, dark above and brown below as Platinum's; and, the owner's paint (2026-10-20), the hair down both
# sides of his face brown and the outline at the far side's sideburn the skin's line (the fringe under the cap's band
# stays Black 2's black). Both faces (0, 1) and the still frame (13: 16 px right, 2 up)
HAIR_PIXELS = {(13, 10): HAIR_DARK, (14, 10): HAIR_DARK, (12, 11): HAIR_DARK, (13, 11): HAIR, (14, 11): HAIR,
               (15, 11): HAIR,
               (7, 16): SKIN_LINE, (8, 16): HAIR, (9, 16): HAIR, (9, 17): HAIR,
               (19, 16): HAIR, (20, 16): HAIR, (21, 16): HAIR, (20, 17): HAIR, (20, 18): HAIR, (21, 20): HAIR,
               (20, 21): HAIR, (19, 22): HAIR}
TOUCH_UPS = {0: HAIR_PIXELS, 1: HAIR_PIXELS, 13: {(x + 16, y - 2): v for (x, y), v in HAIR_PIXELS.items()}}


def customize(sprite, src, tick):
    px = sprite["tex"].load()
    for c, pixels in TOUCH_UPS.items():
        s, t, w, h = retexture.cell_box(sprite, c)
        for (x, y), v in pixels.items():
            px[s + x, t + y] = v


def build(b2_files, src):
    return retexture.build(sys.modules[__name__], b2_files, src)


if __name__ == "__main__":
    sys.argv[3:3] = ["retexture_youngster"]
    retexture.main()
