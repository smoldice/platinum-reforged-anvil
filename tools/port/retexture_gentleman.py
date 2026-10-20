#!/usr/bin/env python3
"""Black 2's Gentleman, sprite 75 of a/0/7/1, with its own animation, recoloured to Platinum's Gentleman: his jacket,
hat and shoes Platinum's browns, his trousers Platinum's greys, his waistcoat Platinum's green a shade darker with a
green stripe, his hat band and cane Platinum's green, and Platinum's skin. His white scarf and hair stay. A recolour
only: every shape stays Black 2's (his hat on his head, where Platinum's is in his hand). The settings for
retexture.py, which says how.

build(b2_files, src) returns the 8 files, from sprite 75's files and Platinum's front.png.

Usage, to preview and check (in the container, from tools/port):
  retexture_gentleman.py B2_ROM POKEPLATINUM_DIR OUT_DIR
"""
import sys

import retexture

B2_SPRITE = 75
PLATINUM_CLASS = "gentleman"

TAN, TAN_DARK, TAN_LINE, GREEN, PURPLE, GREY_LIGHT, GREY, NAVY = 1, 2, 3, 4, 6, 7, 8, 9
GREEN_DARK = PURPLE
# Black 2's palette slots, with Platinum's colours: the suit's tans (his hat's and shoes' too) Platinum's browns, the
# cane's greens Platinum's green, their shade and the hat band's navy Platinum's slate, the greys Platinum's, the skin
# Platinum's. The tie's purple slot takes Platinum's green a shade darker (5-bit 8, 13, 12 against 11, 18, 16), for
# the waistcoat (the owner's note); the purple's other pixels are the green
PALETTE = {TAN: (180, 148, 115), TAN_DARK: (139, 106, 74), TAN_LINE: (115, 82, 57), GREEN: (90, 148, 131),
           5: (82, 82, 98), GREEN_DARK: (66, 107, 99), GREY_LIGHT: (189, 189, 197), GREY: (139, 139, 139),
           NAVY: (82, 82, 98), 10: (255, 213, 189), 11: (222, 164, 123), 12: (189, 123, 98), 13: (98, 65, 74),
           14: (255, 255, 255)}
TROUSERS = {TAN: GREY_LIGHT, TAN_DARK: GREY, TAN_LINE: NAVY}
# By cell: (first row, last row) of the cell, and old slot -> new slot there
REMAPS = {
    **{c: [((0, 31), {PURPLE: GREEN})] for c in (0, 1)},  # the hat band, in both heads
    # the waistcoat under the scarf keeps Black 2's dark and light where they are: the dark green, its stripe green
    2: [((0, 31), {PURPLE: GREEN, NAVY: GREEN_DARK})],
    3: [((0, 31), {NAVY: GREEN_DARK})],  # the jacket, where the waistcoat shows beside it
    14: [((0, 23), {PURPLE: GREEN})],  # a scarf end, over the tie
    9: [((0, 23), TROUSERS)],  # the thighs
    10: [((0, 31), TROUSERS)],  # a leg
    12: [((0, 39), TROUSERS)],  # the other leg
}
CHARS_REMAP = {}
HEADS = {}  # no hair graft


def build(b2_files, src):
    return retexture.build(sys.modules[__name__], b2_files, src)


if __name__ == "__main__":
    sys.argv[3:3] = ["retexture_gentleman"]
    retexture.main()
