#!/usr/bin/env python3
"""Black 2's Worker, sprite 26 of a/0/7/1 (class WORKER_26), with its own animation, recoloured to Platinum's Worker:
a green top and pants, shaded alike, brown gloves and belt, and an all-yellow hard hat and yellow boots, in Platinum's colours,
with Platinum's skin. A recolour only: every shape stays Black 2's (the hat's lamp and its flash too). The settings for
retexture.py, which says how.

build(b2_files, src) returns the 8 files, from sprite 26's files and Platinum's front.png.

Usage, to preview and check (in the container, from tools/port):
  retexture_worker.py B2_ROM POKEPLATINUM_DIR OUT_DIR
"""
import sys

import retexture

B2_SPRITE = 26
PLATINUM_CLASS = "worker"

GREEN_LIGHT, GREEN_MID, GREEN_DARK = 1, 2, 3
YELLOW_LIGHT, YELLOW, YELLOW_DARK = 4, 5, 6
BROWN, DARK_BROWN = 7, 13
BLACK, WHITE = 14, 15
# Black 2's palette slots, with Platinum's colours. The jacket's greys become Platinum's greens, the pants' oranges its
# yellows (for the hat and boots, which take them), the skin its skin. The dark slate becomes the gloves' and belt's
# brown; its other pixels, and the grey's, are remapped below (the grey's slot is left unused)
PALETTE = {GREEN_LIGHT: (115, 164, 123), GREEN_MID: (98, 115, 90), GREEN_DARK: (57, 74, 65),
           YELLOW_LIGHT: (255, 213, 98), YELLOW: (197, 172, 98), YELLOW_DARK: (131, 115, 74),
           BROWN: (123, 82, 49), DARK_BROWN: (65, 49, 49),
           9: (255, 213, 189), 10: (222, 164, 123), 11: (189, 123, 98), 12: (123, 74, 90)}
# By cell: (first row, last row) of the cell, and old slot -> new slot there
HAT_ROWS = range(0, 18)  # the head cell's rows above the face
# The top's darkest shading (old slot 3) is the pants' mid green, as on the pants (whose own darkest stays)
TOP_SHADE = {3: GREEN_MID}
REMAPS = {
    # the head: the hard hat (above the face) Platinum's bright yellow with a white shine, its darker parts tan (its
    # strap, slots 1 and 3, goes in customize()); the eyes' grey glints white
    0: [((0, HAT_ROWS[-1]), {12: YELLOW_LIGHT, 13: YELLOW, 11: WHITE}),
        ((18, 31), {8: WHITE, 7: BLACK, **TOP_SHADE})],  # and the collar
    # the torso: the belt brown (Platinum's belt in shadow) with a tan buckle; the keyring below it white
    1: [((0, 22), TOP_SHADE),
        ((18, 22), {12: BROWN, 13: DARK_BROWN, 8: YELLOW}),
        ((23, 31), {8: WHITE})],
    # the arms, the gloves brown, shaded dark brown
    2: [((0, 23), TOP_SHADE)],
    3: [((0, 31), {WHITE: BROWN, 8: DARK_BROWN, **TOP_SHADE}),
        ((7, 14), {1: DARK_BROWN})],  # the glove's outline, Platinum's dark brown
    4: [((0, 23), TOP_SHADE)],
    5: [((0, 31), {WHITE: BROWN, 8: DARK_BROWN, 7: DARK_BROWN, 5: DARK_BROWN, **TOP_SHADE}),
        ((16, 16), {GREEN_LIGHT: BLACK})],  # the black line between sleeve and glove, which Black 2 broke with slate
    # the legs: the pants (oranges) green like the top; the jacket's tail green too
    6: [((0, 39), {4: GREEN_LIGHT, 5: GREEN_MID, 6: GREEN_DARK, 7: GREEN_MID, 8: GREEN_LIGHT, **TOP_SHADE})],
    # the boots yellow, their soles dark brown
    7: [((0, 23), {12: YELLOW, 13: YELLOW_DARK, 11: YELLOW_LIGHT, 8: DARK_BROWN, 1: BLACK})],  # (a slate outline pixel)
    # the hat's lamp: its grey white, its housing brown
    8: [((0, 15), {8: WHITE, 12: BROWN, 11: YELLOW_LIGHT, 3: BLACK, 1: WHITE})],
}
CHARS_REMAP = {}
HEADS = {}  # no hair graft


def customize(sprite, src, tick):
    """The hard hat's strap goes: it's all Platinum's yellow, but for the hat's own outline, black."""
    px = sprite["tex"].load()
    s, t, w, h = retexture.cell_box(sprite, 0)
    get = lambda x, y: px[s + x, t + y] if 0 <= x < w and 0 <= y < h else 0  # noqa: E731
    strap = {(x, y): get(x, y) for y in HAT_ROWS for x in range(w) if get(x, y) in (1, 3)}
    for (x, y), v in strap.items():
        edge = any(get(x + a, y + b) == 0 for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        px[s + x, t + y] = BLACK if v == 3 and edge else YELLOW_LIGHT


def build(b2_files, src):
    return retexture.build(sys.modules[__name__], b2_files, src)


if __name__ == "__main__":
    sys.argv[3:3] = ["retexture_worker"]
    retexture.main()
