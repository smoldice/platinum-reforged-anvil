#!/usr/bin/env python3
"""Black 2's Waitress, sprite 9 of a/0/7/1, with its own animation, recoloured to Platinum's Waitress: her dress in
Platinum's blues, its shading and edges in Platinum's dark blue, and her shoes white, as Platinum's. A recolour only:
every shape, and every other colour (her hair, skin, apron and tray), stays Black 2's. The settings for retexture.py,
which says how.

build(b2_files, src) returns the 8 files, from sprite 9's files and Platinum's front.png.

Usage, to preview and check (in the container, from tools/port):
  retexture_waitress.py B2_ROM POKEPLATINUM_DIR OUT_DIR
"""
import sys

import retexture

B2_SPRITE = 9
PLATINUM_CLASS = "waitress"

BLUE_DARK, GREY = 2, 4
# Black 2's palette slots, with Platinum's colours: the dress's oranges its blues. Black 2's darkest grey joins its mid
# grey (Platinum's tray and apron have two greys, Black 2's three), and its slot takes the dress's dark blue
PALETTE = {BLUE_DARK: (57, 57, 90), 7: (98, 139, 230), 8: (90, 98, 164)}
# Black 2 edges and shades the dress in its dark browns (slots 5, 6, 9), which also draw her hair and shoes: in the
# dress's parts they're the dark blue. Everywhere, the darkest grey is the mid grey
GREYS = {BLUE_DARK: GREY}
DRESS = {**GREYS, 5: BLUE_DARK, 6: BLUE_DARK, 9: BLUE_DARK}
# Her shoes, in the same browns with an orange shine: white as Platinum's, shaded in Black 2's mid grey, and their
# darkest brown, which edges them, black
SHOES = {**GREYS, 9: 14, 8: 14, 5: GREY, 6: 15}
# By cell: (first row, last row) of the cell, and old slot -> new slot there
REMAPS = {
    **{c: [((0, 47), GREYS)] for c in (0, 3, 4, 9, 11, 15, 16)},
    1: [((0, 31), DRESS)],  # the arm with the tray, its sleeve
    2: [((0, 15), DRESS)],  # a sleeve
    5: [((0, 3), GREYS), ((4, 15), DRESS)],  # the bodice, below her neck
    6: [((0, 31), DRESS)],  # the skirt
    7: [((0, 15), DRESS)],  # the other arm, its sleeve
    8: [((0, 15), DRESS)],
    10: [((0, 12), GREYS), ((13, 23), SHOES)],  # a leg, its shoe below the ankle
    12: [((0, 15), SHOES)],  # the other foot
}
CHARS_REMAP = GREYS
HEADS = {}  # no hair graft


def build(b2_files, src):
    return retexture.build(sys.modules[__name__], b2_files, src)


if __name__ == "__main__":
    sys.argv[3:3] = ["retexture_waitress"]
    retexture.main()
