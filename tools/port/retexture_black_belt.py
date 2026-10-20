#!/usr/bin/env python3
"""Black 2's Black Belt, sprite 50 of a/0/7/1, with its own animation, recoloured to Platinum's Black Belt: the gi in
Platinum's white and pinkish greys, its folds and edges in Platinum's grey-brown, the hair and belt navy, the headband
Platinum's brighter red, and Platinum's skin. A recolour only: every shape stays Black 2's. The settings for
retexture.py, which says how.

build(b2_files, src) returns the 8 files, from sprite 50's files and Platinum's front.png.

Usage, to preview and check (in the container, from tools/port):
  retexture_black_belt.py B2_ROM POKEPLATINUM_DIR OUT_DIR
"""
import sys

import retexture

B2_SPRITE = 50
PLATINUM_CLASS = "black_belt"

RED_DARK, GI_EDGE, HAIR_LIGHT = 5, 6, 9
# Black 2's palette slots, with Platinum's colours. The gi's cream and khaki become Platinum's greys, its olive folds
# and edges Platinum's grey-brown; the hair's dark olive and the belt's slate Platinum's navy. Slot 9, which Black 2
# leaves unused, takes the hair's light navy (the olive that lights Black 2's hair also edges the gi: remapped below)
PALETTE = {1: (255, 255, 255), 2: (205, 189, 189), 3: (148, 131, 123), 4: (255, 98, 90), RED_DARK: (197, 65, 65),
           GI_EDGE: (106, 90, 82), 7: (49, 57, 82), 8: (49, 57, 82), HAIR_LIGHT: (82, 90, 115),
           10: (255, 213, 189), 11: (222, 164, 123), 12: (189, 123, 98), 13: (98, 65, 74), 14: (255, 255, 255)}
# By cell: (first row, last row) of the cell, and old slot -> new slot there
REMAPS = {
    # the head: the hair's olive light navy (above the face); the mouth's red Platinum's darker red, as dark as Black
    # 2's (the headband's red is brighter)
    0: [((0, 11), {GI_EDGE: HAIR_LIGHT}),
        ((18, 23), {4: RED_DARK})],
}
CHARS_REMAP = {}
HEADS = {}  # no hair graft


def build(b2_files, src):
    return retexture.build(sys.modules[__name__], b2_files, src)


if __name__ == "__main__":
    sys.argv[3:3] = ["retexture_black_belt"]
    retexture.main()
