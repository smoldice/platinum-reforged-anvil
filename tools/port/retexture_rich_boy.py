#!/usr/bin/env python3
"""Black 2's Rich Boy, sprite 41 of a/0/7/1, with its own animation, recoloured to Platinum's Rich Boy: the suit
Platinum's white with its purple edges, the hair and shoes Platinum's purples, the teal cuffs Platinum's purple cuffs,
an orange Poké Ball, and Platinum's skin. A recolour only: every shape stays Black 2's. The
settings for retexture.py, which says how.

build(b2_files, src) returns the 8 files, from sprite 41's files and Platinum's front.png.

Usage, to preview and check (in the container, from tools/port):
  retexture_rich_boy.py B2_ROM POKEPLATINUM_DIR OUT_DIR
"""
import sys

import retexture

B2_SPRITE = 41
PLATINUM_CLASS = "rich_boy"

WHITE, HAIR_LIGHT, SKIN_LIGHT, HAIR_DARK, SKIN_LINE = 3, 8, 11, 13, 14
# Black 2's palette slots, with Platinum's colours. The suit's lavender greys Platinum's white and light grey, its lines
# Platinum's purple; the hair's browns (also the shoes' and the ball's edge) Platinum's purples, lightest to darkest;
# the cuffs' teals the light and mid purples of Platinum's cuffs (the owner's note), the ball's red orange, the skin
# Platinum's. Slot 8, which Black 2 leaves unused, takes the hair's light purple (Black 2 lights his hair with a skin
# tone); slot 14, a second white, the skin's darkest (Black 2 lines his face with the hair's dark brown)
PALETTE = {1: (90, 82, 131), 2: (197, 197, 205), WHITE: (255, 255, 255), 4: (90, 82, 131), 5: (41, 41, 49),
           6: (90, 82, 131), 7: (139, 115, 164), HAIR_LIGHT: (139, 115, 164), 9: (222, 115, 65),
           10: (255, 213, 189), SKIN_LIGHT: (222, 164, 123), 12: (189, 123, 98), HAIR_DARK: (57, 57, 90),
           SKIN_LINE: (123, 74, 90)}
# By cell: (first row, last row) of the cell, and old slot -> new slot there. The second white is the first everywhere
WHITES = ((0, 63), {SKIN_LINE: WHITE})
HEAD = [WHITES, ((0, 9), {SKIN_LIGHT: HAIR_LIGHT}), ((18, 23), {HAIR_DARK: SKIN_LINE})]
REMAPS = {0: HEAD, 1: HEAD, **{c: [WHITES] for c in (2, 3, 4, 5)}}
CHARS_REMAP = {}
HEADS = {}  # no hair graft
CUFF_LIGHT = 7
# By cell, {(x, y) in the cell: slot}, after the remaps. The ball arm: the skin pixel in the cuff's step, the cuff's
# light purple (the owner's note: frame pixel 72,72 at tick 0)
TOUCH_UPS = {4: {(18, 22): CUFF_LIGHT}}


def customize(sprite, src, tick):
    px = sprite["tex"].load()
    for c, pixels in TOUCH_UPS.items():
        s, t, w, h = retexture.cell_box(sprite, c)
        for (x, y), v in pixels.items():
            px[s + x, t + y] = v


def build(b2_files, src):
    return retexture.build(sys.modules[__name__], b2_files, src)


if __name__ == "__main__":
    sys.argv[3:3] = ["retexture_rich_boy"]
    retexture.main()
