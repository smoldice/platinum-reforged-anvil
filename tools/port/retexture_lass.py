#!/usr/bin/env python3
"""Black 2's Lass, sprite 3 of a/0/7/1, with its own animation, retextured to look like Platinum's Lass: Platinum's
colours (a navy sailor top with white sleeves and collar, the neckerchief in the oranges of Platinum's bow
(SCARF_STYLE), an orange skirt and Poké Ball, navy socks, khaki hair and shoes, Platinum's skin), and Platinum's hair
(HAIR_STYLE): its crown, bangs and hair clip on Black 2's face, one mass with the hair behind her head (Black 2's, in
khaki: BACK_HAIR_STYLE). The face has the user's touch-ups (HEAD_FIXES). The settings for retexture.py, which says how.

build(b2_files, src) returns the 8 files, from sprite 3's files and Platinum's front.png.

Usage, to preview and check (in the container, from tools/port):
  retexture_lass.py B2_ROM POKEPLATINUM_DIR OUT_DIR
"""
import sys

import retexture

B2_SPRITE = 3
PLATINUM_CLASS = "lass"

GREY_BLUE, ORANGE_MID, ORANGE_DARK = 1, 2, 3
KHAKI, KHAKI_DARK, KHAKI_LIGHT = 4, 5, 8
BLUE, NAVY = 6, 7
ORANGE = 9
SKIN_SHADE, SKIN_OUTLINE, WHITE = 12, 13, 14
# Black 2's palette slots, with Platinum's colours. The greys become the skirt's oranges (its lightest is the ball's
# red's slot, Platinum's orange) and the collar's grey-blue; the yellows the top's blue and navy, the darkest freed
# for the hair's lightest khaki; the browns Platinum's khaki
PALETTE = {GREY_BLUE: (172, 180, 189), ORANGE_MID: (193, 94, 53), ORANGE_DARK: (156, 82, 57),
           KHAKI: (123, 115, 65), KHAKI_DARK: (82, 74, 65), BLUE: (90, 115, 148), NAVY: (65, 74, 90),
           KHAKI_LIGHT: (172, 156, 65), ORANGE: (230, 106, 49),
           10: (255, 213, 189), 11: (222, 164, 123), SKIN_SHADE: (189, 123, 98), SKIN_OUTLINE: (123, 74, 90),
           WHITE: (238, 238, 255)}
# The parts' remaps: old slot -> new slot
HEAD = {2: GREY_BLUE, 3: GREY_BLUE}  # the grey by her eye and at her collar
HAIR_STREAKS = {SKIN_OUTLINE: KHAKI_DARK}  # Black 2's mauve streaks in her hair
COLLAR = {1: WHITE, 3: GREY_BLUE, 2: GREY_BLUE, WHITE: NAVY, 8: NAVY}  # and its stripe navy; the top's darkest navy
SLEEVE = {6: WHITE, 7: WHITE, 8: GREY_BLUE, 1: GREY_BLUE, 3: GREY_BLUE}
SKIRT = {1: ORANGE, 2: ORANGE_MID, 3: ORANGE_DARK}
SOCK = {1: BLUE, WHITE: BLUE, 2: NAVY, 3: NAVY}
SHOE = {SKIN_SHADE: KHAKI_LIGHT, SKIN_OUTLINE: KHAKI_DARK}
# The first torso drawing's bottom row: two pixels of the skirt's dark grey show at her waist, the skirt's dark orange
WAIST_ROW = 20
# By cell: (first row, last row) of the cell, and old slot -> new slot there
REMAPS = {
    0: [((0, 23), HEAD), ((0, 10), HAIR_STREAKS)],  # the heads
    1: [((0, 23), HEAD), ((0, 10), HAIR_STREAKS)],
    3: [((0, WAIST_ROW - 1), COLLAR), ((WAIST_ROW, WAIST_ROW), SKIRT)],  # the torso
    4: [((0, 23), COLLAR)],
    5: [((21, 31), SLEEVE)],  # the arm raising the ball
    6: [((23, 31), SLEEVE)],
    7: [((0, 23), SLEEVE)],  # the other arm
    8: [((0, 23), SLEEVE)],
    9: [((0, 16), SKIRT), ((31, 40), SOCK), ((41, 47), SHOE)],  # the legs
    10: [((0, 17), SKIRT), ((32, 41), SOCK), ((42, 47), SHOE)],
    11: [((0, 16), SKIRT), ((17, 27), SOCK)],
    12: [((0, 16), SKIRT), ((31, 40), SOCK), ((41, 47), SHOE)],
}
# File 0's change: the top's darkest yellow, whose slot the hair takes, to navy
CHARS_REMAP = {8: NAVY}

# The hair: "recolour" keeps Black 2's in Platinum's khaki; "platinum" puts on Platinum's crown, bangs and orange hair
# clip, mirrored (retexture.py's hair graft), over Black 2's face, which stays as drawn: it blinks and talks
HAIR_STYLE = "platinum"
# The heads: head cell -> its rows' offset from head 0's (the two faces' hair is the same)
HEADS = {0: 0, 1: 0} if HAIR_STYLE == "platinum" else {}
HEAD_SIZE = 24
HAIR_DARK, HAIR_MID, HAIR_LIGHT = KHAKI_DARK, KHAKI, KHAKI_LIGHT
B2_HAIR = {KHAKI: KHAKI, KHAKI_DARK: KHAKI_DARK}  # Black 2's hair, already khaki
B2_HAIR_SHADE = SKIN_OUTLINE
FACE = {ORANGE, 10, 11, SKIN_SHADE, SKIN_OUTLINE, WHITE}
# The eyes, which the hair never covers: these slots, and the dark pixels by the skin in these rows and columns
EYE_SLOTS = (WHITE, GREY_BLUE)
EYE_ROWS, EYE_COLS = range(13, 16), range(4, 15)
EYE_DARK, EYE_NEAR = (15, SKIN_OUTLINE), (10, 11, SKIN_SHADE, WHITE)
# Black 2 (x, y) <- Platinum (PT_MIRROR - x, y - PT_DY - dy): Platinum's near eye's white (39, 26) on Black 2's
# (13, 14)
PT_MIRROR, PT_DY = 52, -12
# Platinum's hair above the eyes: the crown, the bangs and the clip (not the ball in her hand, right of x 49)
PT_HAIR_ROWS, PT_HAIR_COLS = range(14, 25), range(26, 50)
# Platinum's black pixels in its hair: the outline of its far side, a strand
PT_HAIR_OUTLINE = {(46, 17), (47, 18), (48, 20), (48, 21), (49, 23), (49, 24), (31, 24)}
# Platinum's khakis (its darkest, the hair's outline, black as Black 2 outlines) and the clip's orange
PT_TO_B2 = {4: KHAKI_LIGHT, 5: KHAKI, 6: KHAKI_DARK, 7: 15, 8: ORANGE}
# Platinum's forehead showing under the bangs comes along, in Black 2's skin
PT_SKIN_TO_B2 = {0xA: 10, 0xB: 11, 0xC: SKIN_SHADE}
PT_SKIN_MAX_ROW = 24
# Platinum's hair may reach past Black 2's head down to this row
TRIM_ROW = 9
# Head pixels fixed by hand, last, by head cell: (x, y) -> slot. On both heads: Black 2's bangs' black tips, left on
# her forehead under Platinum's shorter bangs, are skin; Platinum's dark outline above her far eye and the side lock's
# black edge by her ear are hair; and the hair's outline at the top right steps out row by row, as Black 2's does,
# where Platinum's wider crown met Black 2's hair behind her head with a notch. With the eyes open, the black at the
# far eye's outer corner is hair (as Black 2 has hair left of it), and without its lashes the eye's pupil is two
# pixels tall (down a pixel), as the near eye's. In head 1, the blink, the far eye's closed line is Black 2's own at
# its outer corner, without the end that rose onto her forehead
BOTH_HEADS = {(8, 12): 11, (10, 12): 11, (8, 13): 11, (9, 13): 10, (11, 13): 11, (6, 12): KHAKI_DARK,
              (19, 15): KHAKI_DARK, (21, 10): KHAKI_DARK, (22, 10): 15}
# And the user's own touch-ups, painted on the heads (scratch/mcss/lass/edit), last of all. On both: her ear
# outlined in mauve, as skin is, not black; the hair by her cheek a pixel longer, in its lightest khaki; the black by
# her hair clip dark khaki (they painted Platinum's darkest hair olive, which the palette hasn't room for, here and by
# the clip's new place); her bangs longer, down over her forehead to her eyes; the hair clip a pixel lower and a pixel
# in, its plus centred on (15, 12) with black under it, and the bangs' strands shaded anew around it; the hair down
# the right of her face lighter (the darkest olive painted at (14, 19) too)
TOUCH_UPS = {(18, 15): SKIN_OUTLINE, (18, 16): SKIN_OUTLINE, (17, 17): SKIN_OUTLINE, (13, 17): KHAKI_LIGHT,
             (15, 10): KHAKI_DARK,
             (7, 9): KHAKI, (6, 10): KHAKI_DARK, (8, 10): KHAKI, (5, 11): KHAKI, (8, 11): KHAKI, (9, 11): KHAKI,
             (10, 11): KHAKI, (8, 12): KHAKI_DARK, (9, 12): KHAKI_DARK, (10, 12): KHAKI, (11, 12): KHAKI,
             (12, 12): KHAKI, (5, 13): KHAKI_DARK, (10, 13): KHAKI_DARK, (11, 13): KHAKI_DARK, (12, 13): KHAKI,
             (13, 13): KHAKI, (14, 13): KHAKI_DARK, (14, 14): KHAKI_DARK,
             (14, 12): ORANGE, (15, 12): ORANGE, (15, 13): ORANGE, (15, 14): 15, (16, 14): 15,
             (16, 10): KHAKI, (16, 11): KHAKI_DARK, (17, 11): KHAKI,
             (11, 8): KHAKI, (10, 9): KHAKI_DARK, (12, 9): KHAKI, (13, 9): KHAKI, (16, 9): KHAKI, (11, 10): KHAKI_DARK,
             (12, 10): KHAKI_DARK, (14, 10): KHAKI, (17, 10): KHAKI, (13, 11): KHAKI_DARK, (14, 11): KHAKI_DARK,
             (18, 11): KHAKI, (19, 11): KHAKI, (5, 12): KHAKI, (18, 12): KHAKI, (16, 13): KHAKI_DARK,
             (21, 9): KHAKI, (20, 10): KHAKI, (21, 10): KHAKI, (20, 11): KHAKI, (20, 12): KHAKI, (19, 13): KHAKI,
             (17, 14): KHAKI_DARK, (18, 14): KHAKI, (19, 14): KHAKI, (19, 15): KHAKI, (18, 17): KHAKI,
             (17, 18): KHAKI, (14, 19): KHAKI_DARK}
# With the eyes open: the far eye's iris blue at its top and the near eye's white grey-blue at its top, as Platinum
# draws eyes, the near eye a row lower, under the longer bangs; her cheeks' shading; the hair off her near cheek. (A
# pixel of the hair's outline at the right, (22, 9), was khaki too, a gap in the outline: black again, 2026-10-14)
OPEN_TOUCH_UPS = {(7, 13): BLUE, (12, 14): 15, (13, 14): GREY_BLUE, (5, 14): KHAKI_DARK, (9, 13): 11,
                  (8, 14): 10, (11, 14): 11, (6, 15): 11, (8, 15): 10,
                  (14, 15): 11, (14, 16): 10, (13, 17): 10, (14, 17): 10}
# And on the hair behind her head (its own cell's pixels): none now
BACK_HAIR_TOUCH_UPS = {}
HEAD_FIXES = {0: {**BOTH_HEADS, (4, 14): KHAKI_DARK, (7, 15): 15, **TOUCH_UPS, **OPEN_TOUCH_UPS},
              1: {**BOTH_HEADS, (4, 14): KHAKI_DARK, (5, 14): 15, (6, 14): 15, (7, 14): 11, **TOUCH_UPS}}

# The neckerchief in the V of her collar, which Black 2 draws in the collar's greys: its knot, and its tails hanging
# down to either side. "red" (the user's pick) takes Platinum's bow's oranges, "white" keeps the collar's colours. By
# torso cell (the two drawings sit a pixel or two apart, the left tail a row longer in the second): (x, y) -> slot.
# Black 2's light grey is the orange, its mid grey the mid orange, its dark grey the dark orange, its white highlight
# the orange
SCARF_STYLE = "red"
O, OM, OD = ORANGE, ORANGE_MID, ORANGE_DARK
SCARF = {
    3: {(10, 11): O, (11, 11): OD, (9, 12): O, (10, 12): OM, (11, 12): O, (9, 13): O, (10, 13): OD, (11, 13): O,
        (11, 14): OD, (12, 14): OD, (10, 15): OM, (11, 15): O, (12, 15): OD, (10, 16): OD, (11, 16): O,
        (11, 17): OD,
        (8, 13): OD, (7, 14): OD, (8, 14): O, (9, 14): OD, (6, 15): OD, (7, 15): O, (8, 15): O, (6, 16): OD},
    4: {(10, 11): O, (11, 11): OD, (10, 12): O, (11, 12): OM, (12, 12): O, (10, 13): O, (11, 13): OD, (12, 13): O,
        (12, 14): OD, (13, 14): OD, (11, 15): OM, (12, 15): O, (13, 15): OD, (11, 16): OD, (12, 16): O,
        (12, 17): OD,
        (9, 13): OD, (8, 14): OD, (9, 14): O, (10, 14): OD, (6, 15): OD, (7, 15): OD, (8, 15): O, (9, 15): O,
        (7, 16): OD, (8, 16): O},
}

# The hair behind her head: its cell, and the cell animations its node and the head's play
BACK_HAIR_CELL, BACK_HAIR_SEQ, HEAD_SEQ = 2, 1, 0
# "black2" keeps it Black 2's, wavy, in Platinum's khaki: the user picked it. "smooth" draws it smooth, as Platinum's
# hair hangs (smooth_back_hair())
BACK_HAIR_STYLE = "black2"
# Black 2's curl at its tip, which goes: Platinum's hair hangs straight
CURL = {(x, y) for y in (28, 29) for x in range(20, 24)}
HAIR_SLOTS = (KHAKI, KHAKI_DARK, KHAKI_LIGHT)


def hull(points):
    """The convex hull of points, counterclockwise (Andrew's monotone chain)."""
    pts = sorted(set(points))

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def smooth_back_hair(px, box):
    """The hair behind her head, smooth as Platinum's: Black 2's outline without its waves (its convex hull) and
    without the curl at its tip, outlined black, mid khaki, darker at its ends and along its outer edge."""
    s, t, w, h = box
    old = {(x, y) for y in range(h) for x in range(w) if px[s + x, t + y]} - CURL
    poly = hull(old)

    def inside(x, y):
        return all((b[0] - a[0]) * (y - a[1]) - (b[1] - a[1]) * (x - a[0]) >= 0
                   for a, b in zip(poly, poly[1:] + poly[:1]))

    mask = {(x, y) for y in range(h) for x in range(w) if inside(x, y)}
    outline = {(x, y) for x, y in mask
               if any((x + a, y + b) not in mask for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
    inner = mask - outline
    for y in range(h):
        for x in range(w):
            px[s + x, t + y] = 0
    for x, y in outline:
        px[s + x, t + y] = 15
    for x, y in inner:
        ends = (x, y + 2) not in inner or (x, y + 3) not in inner
        edge = (x + 1, y) not in inner and x > w // 2
        px[s + x, t + y] = KHAKI_DARK if ends or edge else KHAKI


def customize(sprite, src, tick):
    """The neckerchief as SCARF_STYLE says. And the hair, as one mass like Platinum's: the hair behind her head as
    BACK_HAIR_STYLE says, the head's stray black pixels fixed (HEAD_FIXES), and the black pixels between the head's
    hair and the hair behind it dark khaki, where both pieces draw hair around them (in the still frame's pose)."""
    px = sprite["tex"].load()
    if SCARF_STYLE == "red":
        for c, pixels in SCARF.items():
            s, t, _, _ = retexture.cell_box(sprite, c)
            for (x, y), v in pixels.items():
                px[s + x, t + y] = v
    if HAIR_STYLE != "platinum":
        return
    back = retexture.cell_box(sprite, BACK_HAIR_CELL)
    if BACK_HAIR_STYLE == "smooth":
        smooth_back_hair(px, back)
    hx, hy, head = retexture.cell_origin(sprite, HEAD_SEQ, tick)
    bx, by, _ = retexture.cell_origin(sprite, BACK_HAIR_SEQ, tick)
    bs, bt, bw, bh = back

    def back_at(x, y):  # on screen
        u, v = x - bx, y - by
        return px[bs + u, bt + v] if 0 <= u < bw and 0 <= v < bh else 0

    def head_at(c, x, y):  # on screen, head cell c
        s, t, w, h = retexture.cell_box(sprite, c)
        u, v = x - hx, y - hy
        return px[s + u, t + v] if 0 <= u < w and 0 <= v < h else 0

    def between(c, x, y):
        return all(head_at(c, x + a, y + b) or back_at(x + a, y + b) for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))

    for c in HEADS:
        s, t, w, h = retexture.cell_box(sprite, c)
        cell = {(x, y): px[s + x, t + y] for y in range(h) for x in range(w)}

        def near(x, y, kinds):
            return any(cell.get((x + a, y + b)) in kinds for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))

        for (x, y), v in cell.items():
            if (v == 15 and near(x, y, HAIR_SLOTS) and not near(x, y, FACE) and back_at(hx + x, hy + y)
                    and between(c, hx + x, hy + y)):
                px[s + x, t + y] = KHAKI_DARK
        for (x, y), v in HEAD_FIXES[c].items():
            px[s + x, t + y] = v
    # the hair behind's own outline, where it shows between the head's hair and its own
    for v in range(bh):
        for u in range(bw):
            x, y = bx + u, by + v
            if (px[bs + u, bt + v] == 15 and not head_at(head, x, y) and between(head, x, y)
                    and any(head_at(head, x + a, y + b) in HAIR_SLOTS for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))):
                px[bs + u, bt + v] = KHAKI_DARK
    for (u, v), value in BACK_HAIR_TOUCH_UPS.items():
        px[bs + u, bt + v] = value


def build(b2_files, src):
    return retexture.build(sys.modules[__name__], b2_files, src)


if __name__ == "__main__":
    sys.argv[3:3] = ["retexture_lass"]
    retexture.main()
