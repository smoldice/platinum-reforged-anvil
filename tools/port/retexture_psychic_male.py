#!/usr/bin/env python3
"""Black 2's Psychic (male), sprite 35 of a/0/7/1, with its own animation, recoloured to Platinum's Psychic: the tunic
Platinum's purple robe, all purple up to the neck, a dark green sash, the trousers purple, the hair Platinum's green,
the glow Platinum's pale yellow, a black-edged red Poké Ball, and Platinum's skin. A recolour only: every shape stays
Black 2's (his trousers and shoes too). The settings for retexture.py, which says how.

build(b2_files, src) returns the 8 files, from sprite 35's files and Platinum's front.png.

Usage, to preview and check (in the container, from tools/port):
  retexture_psychic_male.py B2_ROM POKEPLATINUM_DIR OUT_DIR
"""
import sys

import retexture

B2_SPRITE = 35
PLATINUM_CLASS = "psychic_male"

GREEN, GREEN_DARK, PURPLE, PURPLE_DARK, WHITE, GREY = 1, 2, 5, 6, 7, 8
BLACK = 15
# Black 2's palette slots, with Platinum's colours: the hair's teal Platinum's greens (also the sash's), the trousers'
# blues Platinum's purples, the trims' lilacs Platinum's dark purple and near-black, the glow, the ball's red, and the
# skin, its four browns Platinum's four tones, lightest to darkest
PALETTE = {GREEN: (74, 90, 82), GREEN_DARK: (49, 57, 49), 3: (106, 82, 106), 4: (49, 49, 57),
           PURPLE: (172, 90, 156), PURPLE_DARK: (106, 82, 106), WHITE: (255, 255, 255), GREY: (172, 172, 197),
           9: (222, 90, 57), 10: (255, 255, 180), 11: (189, 123, 98), 12: (123, 74, 90), 13: (222, 164, 123),
           14: (255, 213, 189)}
# The tunic's white and grey (which the ball and eyes keep) Platinum's purples
ROBE = {WHITE: PURPLE, GREY: PURPLE_DARK}
# By cell: (first row, last row) of the cell, and old slot -> new slot there
CHEST_SLEEVE, CUFF_LINE = 2, 4
REMAPS = {
    CHEST_SLEEVE: [((0, 23), ROBE)],  # the sleeve at his chest
    4: [((0, 31), ROBE)],  # the raised arm's sleeve
    # the torso all purple, up to the neck (the owner's note); the sash (the lilacs) dark green
    5: [((0, 17), ROBE),
        ((18, 20), {**ROBE, 3: GREEN, 4: GREEN_DARK, PURPLE_DARK: GREEN_DARK}),
        ((21, 31), ROBE)],
    # the ball, in each of its drawings: edged black (Black 2's darkest brown, which is the skin's darkest here)
    **{c: [((0, 23), {12: BLACK})] for c in (10, 11, 12, 13, 14)},
}
CHARS_REMAP = {}
HEADS = {}  # no hair graft


def customize(sprite, src, tick):
    """The sleeve at his chest: the sleeve's last pixels before its cuff's line take the dark purple, so the cuff's
    edge is in one purple, as the female Psychic's are (the owner's note; Black 2 draws them white there)."""
    px = sprite["tex"].load()
    s, t, w, h = retexture.cell_box(sprite, CHEST_SLEEVE)
    for y in range(h):
        for x in range(w - 1):
            if px[s + x, t + y] == PURPLE and px[s + x + 1, t + y] == CUFF_LINE:
                px[s + x, t + y] = PURPLE_DARK


def build(b2_files, src):
    return retexture.build(sys.modules[__name__], b2_files, src)


if __name__ == "__main__":
    sys.argv[3:3] = ["retexture_psychic_male"]
    retexture.main()
