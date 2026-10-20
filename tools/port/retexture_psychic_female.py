#!/usr/bin/env python3
"""Black 2's Psychic (female), sprite 36 of a/0/7/1, with its own animation, recoloured to Platinum's Psychic: the tunic
Platinum's purple robe, all purple up to the neck, a dark green sash, the trousers purple, the hair Platinum's green,
the glow Platinum's pale yellow, a black-edged red Poké Ball, and Platinum's skin. A recolour only: every shape stays
Black 2's (her bob and trousers too). The settings for retexture.py, which says how.

build(b2_files, src) returns the 8 files, from sprite 36's files and Platinum's front.png.

Usage, to preview and check (in the container, from tools/port):
  retexture_psychic_female.py B2_ROM POKEPLATINUM_DIR OUT_DIR
"""
import sys

import retexture

B2_SPRITE = 36
PLATINUM_CLASS = "psychic_female"

GREEN, GREEN_DARK, NEAR_BLACK, PURPLE, PURPLE_DARK, SKIN_DARKEST, BLACK, GREY, WHITE = 1, 2, 4, 5, 6, 10, 13, 14, 15
# Black 2's palette slots, with Platinum's colours: the hair's plum Platinum's greens (also the sash's), the trousers'
# blues Platinum's purples, the trims' lilacs Platinum's dark purple and near-black, the ball's red, the glow, and the
# skin, its four tones Platinum's, lightest to darkest
PALETTE = {GREEN: (74, 90, 82), GREEN_DARK: (49, 57, 49), 3: (106, 82, 106), NEAR_BLACK: (49, 49, 57),
           PURPLE: (172, 90, 156), PURPLE_DARK: (106, 82, 106), 7: (222, 90, 57), 8: (255, 255, 180),
           9: (189, 123, 98), SKIN_DARKEST: (123, 74, 90), 11: (222, 164, 123), 12: (255, 213, 189),
           GREY: (172, 172, 197), WHITE: (255, 255, 255)}
# The tunic's white and grey (which the ball and eyes keep) Platinum's purples, the blue that edges it near-black
ROBE = {WHITE: PURPLE, GREY: PURPLE_DARK, PURPLE: NEAR_BLACK}
# By cell: (first row, last row) of the cell, and old slot -> new slot there
REMAPS = {
    0: [((0, 31), {7: SKIN_DARKEST})],  # the head: her mouth, which has the ball's red, Platinum's darkest skin
    # the torso all purple, up to the neck (the owner's note), the collar's blue lining dark purple; the sash (the
    # lilacs) dark green
    2: [((0, 9), {**ROBE, PURPLE: PURPLE_DARK}),
        ((10, 14), ROBE),
        ((15, 18), {**ROBE, 3: GREEN, NEAR_BLACK: GREEN_DARK}),
        ((19, 31), ROBE)],
    3: [((0, 31), ROBE)],  # the raised arm's sleeve
    4: [((0, 23), ROBE)],  # the other arm's sleeve
    # the ball, in each of its drawings: edged black (Black 2's darkest skin brown here)
    **{c: [((0, 23), {SKIN_DARKEST: BLACK})] for c in (7, 8, 9)},
}
CHARS_REMAP = {}
HEADS = {}  # no hair graft


def build(b2_files, src):
    return retexture.build(sys.modules[__name__], b2_files, src)


if __name__ == "__main__":
    sys.argv[3:3] = ["retexture_psychic_female"]
    retexture.main()
