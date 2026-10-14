#!/usr/bin/env python3
"""Black 2's Fisherman, sprite 29 of a/0/7/1, with its own animation, retextured to look like Platinum's Fisherman:
Platinum's colours (orange vest, tan pants, dark blue boots, Platinum's skin) and Platinum's orange cap in place of
Black 2's bucket hat with its glasses. HEAD_STYLE picks how much of Platinum's head he takes: "cap" (Black 2's face
under Platinum's cap and the hair below it) or "face" (Platinum's whole head, cap and face): the user picked "face".
Both heads face the same way, so Platinum's goes on as it is, lined up by the eyes. The cooler stays Black 2's. The settings for retexture.py, which says how.

build(b2_files, src) returns the 8 files, from sprite 29's files and Platinum's front.png.

Usage, to preview and check (in the container, from tools/port):
  retexture_fisherman.py B2_ROM POKEPLATINUM_DIR OUT_DIR
"""
import sys

import retexture

B2_SPRITE = 29
PLATINUM_CLASS = "fisherman"
HEAD_STYLE = "face"

# Black 2's palette slots, with Platinum's colours. Slot 4, the hat's and pants' lightest khaki, joins slot 5 (both
# are Platinum's tan) and becomes Platinum's fourth skin tone, which its face needs
PALETTE = {1: (246, 131, 57), 2: (180, 98, 49), 3: (123, 82, 49), 4: (189, 123, 98), 5: (205, 156, 90),
           6: (123, 82, 49), 8: (255, 213, 189), 9: (222, 164, 123), 10: (123, 74, 90), 11: (49, 49, 74),
           12: (90, 90, 131), 13: (156, 156, 180)}
# By cell: (first row, last row) of the cell, and old slot -> new slot there
REMAPS = {c: [((0, 79), {4: 5})] for c in range(10)}
CHARS_REMAP = {4: 5}
HEADS = {}  # no hair graft: customize() changes the head

# The head: Black 2's cell 0, played by cell animation 0. Black 2 (x, y) <- Platinum (x - PT_DX, y - PT_DY): Platinum's
# eyes (x 32 and 39, rows 29-30) on Black 2's (x 10 and 17, row 18). The faces are the same size
HEAD_CELL = 0
HEAD_SEQ, TORSO_SEQ = 0, 1  # the cell animations the head's and the torso's nodes play
PT_DX, PT_DY = 22, 11
# Platinum's colours -> Black 2's slots
PT_TO_B2 = {3: 1, 4: 2, 2: 3, 14: 14, 9: 13, 1: 13, 5: 12, 6: 11, 15: 15, 10: 8, 11: 9, 12: 4, 13: 10, 7: 5, 8: 6}
PT_SKIN = {10, 11, 12, 13}
# Platinum's cap: rows 18-28, right of his raised arm (from x 30, and from x 26 for the visor, rows 25-28, without
# the arm's skin); with the hair below it at the back (rows 29-31, from x 40). His whole head adds his face (rows
# 29-36, from x 30, right of his sleeve)
CAP_ROWS, VISOR_ROWS, FACE_ROWS = range(18, 25), range(25, 29), range(29, 37)
# the greys of his sleeve, behind his cheek, to this column
SLEEVE, SLEEVE_TO_X = (1, 5, 9), 32
HAIR_ROWS, HAIR_FROM_X = range(29, 32), 40
# Black 2's hat: everything above its face (to row HAT_ROW), and the hat's colours, its lens and their black outlines
# below that, down to row HAT_LOW
HAT_ROW, HAT_LOW = 16, 20
HAT_SLOTS = (4, 5, 6, 12)
B2_FACE = {8, 9, 10, 14}
VEST = (1, 2, 3)  # Black 2's vest's slots (Platinum's orange)


def platinum_head(src, style):
    """Platinum's cap (and face, for "face") as {(x, y): Black 2 slot}, in Black 2's head cell's pixels."""
    pp = src.load()
    out = {}
    for y in range(CAP_ROWS.start, FACE_ROWS.stop):
        for x in range(80):
            v = pp[x, y]
            if not v:
                continue
            if y in CAP_ROWS:
                take = x >= 30
            elif y in VISOR_ROWS:
                take = x >= 26 and v not in PT_SKIN
            elif style == "face":
                take = x >= 30 and not (x <= SLEEVE_TO_X and v in SLEEVE)
            else:
                take = y in HAIR_ROWS and x >= HAIR_FROM_X and v in (6, 15)
            if take:
                out[(x - PT_DX, y - PT_DY)] = PT_TO_B2[v]
    return out


def customize(sprite, src, tick):
    tex = sprite["tex"]
    px = tex.load()
    s, t, w, h = retexture.cell_box(sprite, HEAD_CELL)
    old = {(x, y): px[s + x, t + y] for y in range(h) for x in range(w) if px[s + x, t + y]}

    def near(x, y, kinds):
        return any(old.get((x + a, y + b)) in kinds for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))

    head = dict(old)
    for (x, y), v in old.items():
        hat = v in HAT_SLOTS or (v == 15 and not near(x, y, B2_FACE))
        if y <= HAT_ROW or (y <= HAT_LOW and hat):
            del head[(x, y)]
    collar = {}
    if HEAD_STYLE == "face":
        # Black 2's face goes too: only its vest's collar stays (the vest's colours, and the black outlining them, not
        # Black 2's chin), drawn over Platinum's chin and neck, as it stands up around his neck in Black 2's art
        collar = {q: v for q, v in head.items()
                  if v in VEST or (v == 15 and near(*q, VEST) and not near(*q, B2_FACE))}
        head = dict(collar)
    platinum = platinum_head(src, HEAD_STYLE)
    if HEAD_STYLE == "face":
        # The vest's collar, where Black 2's torso draws it (its head drew nothing there), shows over Platinum's chin,
        # which is a pixel wider; Platinum's black outline of the chin stays
        hx, hy, _ = retexture.cell_origin(sprite, HEAD_SEQ, tick)
        tx, ty, torso = retexture.cell_origin(sprite, TORSO_SEQ, tick)
        ts, tt, tw, th = retexture.cell_box(sprite, torso)
        for (x, y), v in list(platinum.items()):
            u, w_ = hx + x - tx, hy + y - ty
            if v != 15 and (x, y) not in old and 0 <= u < tw and 0 <= w_ < th and px[ts + u, tt + w_] in VEST:
                del platinum[(x, y)]
    head.update(platinum)
    head.update(collar)
    retexture.clear_cell(tex, (s, t, w, h))
    for (x, y), v in head.items():
        if 0 <= x < w and 0 <= y < h:
            px[s + x, t + y] = v


def build(b2_files, src):
    return retexture.build(sys.modules[__name__], b2_files, src)


if __name__ == "__main__":
    sys.argv[3:3] = ["retexture_fisherman"]
    retexture.main()
