"""The rig of Platinum's Aroma Lady, class TRAINER_CLASS_AROMA_LADY: her long hair, flowing behind her, bobs up and
down, and each sparkle floating around her bobs on its own, in one of three rhythms, so neighbours are out of step. Her
arms stay still (ARM_STYLE "still", the user's choice). 96 ticks; the last frame is Platinum's.

With ARM_STYLE "rises" (the user's earlier try, kept), her straight arm also rises from the shoulder and comes back
down to where Platinum draws it: its sleeve turns at the shoulder, its outline put back after (trainer_rig.outline());
its hand and cuff ride on the wrist without turning, so they keep Platinum's pixels. What the moving parts uncover is
painted in, hidden behind them at rest. The cuts are by Platinum's pixels (x, y in its 80x80 frame). See trainer_rig.py
for what a rig is.
"""
import math

from PIL import Image

from trainer_rig import free_edges, keyframes, outline

ORIGIN = (40, 80)
TICKS, STEP = 96, 4
HAIR_SLOTS = (0x3, 0x4, 0x5, 0x6)
HAIR, GREY, GREY_EDGE = 0x4, 0x1, 0x2
NEIGHBOURS = ((1, 0), (-1, 0), (0, 1), (0, -1))

# Her long hair behind her, flowing out to the left: the hair's colours left of her head (to x 33) from row 24, and
# left of her dress (to x 38) below her shoulder, down to its tips; only the hair itself, joined to this pixel of it,
# not the sparkles around her in the same greens. Its top rows, where it comes from behind her head, stay with her
# head; the rest bobs, from a row above where they end (drawn by both), so it doesn't come away as it drops
BACK_HAIR_ROWS = range(24, 43)
BACK_HAIR_TO_X = {**{y: 33 for y in range(24, 28)}, **{y: 38 for y in range(28, 43)}}
BACK_HAIR_SEED = (25, 33)
HAIR_TOP_TO_ROW, HAIR_MOVES_FROM_ROW = 27, 26
# Behind her folded arm and her dress, where they hide it at rest, the hair goes on (this many pixels past its edge),
# so as it bobs, hair shows beside them, not gaps
HAIR_UNDER_REACH, HAIR_UNDER_ROWS, HAIR_UNDER_X = 3, range(26, 43), range(28, 41)
# Platinum leaves a pixel of background between her hair and her dress, at (37, 41); the hair's pixel over it stays
# with her body, so as the hair bobs (a pixel up at most), the gap doesn't close round into a hole
HAIR_BY_GAP = {(37, 40)}

# Her straight arm: "still" (the user's choice: it stays in her body, and only her hair and the sparkles move) or
# "rises" (their earlier try: from its place, up and back down into place)
ARM_STYLE = "still"
# The straight arm, as the user marked it on her sprite: by row, its first and last columns, from the top of its
# sleeve at her shoulder down to her hand. All of it turns
ARM = {30: (45, 45), 31: (45, 46), 32: (46, 46), 33: (47, 47), 34: (47, 48), 35: (47, 49), 36: (46, 49), 37: (46, 50),
       38: (46, 51), 39: (47, 52), 40: (47, 52), 41: (48, 53), 42: (48, 54), 43: (48, 55), 44: (49, 57), 45: (50, 58),
       46: (51, 58), 47: (53, 59), 48: (55, 58)}
# Its top rows, at her shoulder, are drawn again behind it, where they stay, so as it turns, no hole opens in her
# shoulder; below them, where it comes away from her side, the background shows between them, as under her arm, the
# arm's dark grey edge closing the gap at the top
SHOULDER_TO_ROW = 35
ARMPIT = {(46, 36): GREY_EDGE}
# Its hand and white cuff, from where the cuff starts in each row; the sleeve goes on under the cuff's first columns,
# in its grey, hidden by it, so where the turned sleeve's end and the cuff land a pixel apart, sleeve shows
CUFF = {41: 52, 42: 51, 43: 50, 44: 50, 45: 50, 46: 51, 47: 53, 48: 55}
SHOULDER, WRIST = (47, 33), (51, 43)

# The sparkles: the frame's pieces not joined to her (split() finds them, each a part of its own, in front); pieces
# this close together are one sparkle (a ring and the dot beside it), so they don't drift into each other
SPARKLE_MAX = 20  # pixels
SPARKLE_GAP = 3
BASE_ORDER = ["hair", "shoulder", "sleeve", "hand", "body"]  # back to front, the sparkles after
ORDER = list(BASE_ORDER)
PIVOTS = {"body": ORIGIN, "hair": (30, 33), "shoulder": ORIGIN, "sleeve": SHOULDER, "hand": WRIST}
# The straight arm's turn: from its place, up (anticlockwise on screen) and back down into place
ARM_TURN = [(0, 0), (8, 0), (32, -18), (60, 0)]
# The long hair's bob, in pixels: a pixel up and down (more opens gaps where it comes from behind her head)
HAIR_BOB = [(0, 0), (14, -1), (32, 1), (50, -1), (68, 1), (84, 0)]
# The sparkles' bobs: three rhythms, each a quarter beat behind the last (so neighbours never swing into each other),
# taken in turn by the sparkles from the top of the frame down, this many pixels up and down
SPARKLE_BEATS = [[(0, 0), (10, -1), (26, 1), (42, -1), (58, 1), (74, 0)],
                 [(0, 0), (16, -1), (32, 1), (48, -1), (64, 1), (80, 0)],
                 [(0, 0), (22, -1), (38, 1), (54, -1), (70, 1), (86, 0)]]
SPARKLE_RISE = 2

FREE_EDGES = {}  # the sleeve's, from split()
SPARKLES = {}  # part name -> its rhythm, from split()


def flood(pixels, seed):
    """The pixels joined to seed (side by side, not corner to corner)."""
    found, todo = set(), [seed]
    while todo:
        q = todo.pop()
        if q in pixels and q not in found:
            found.add(q)
            todo += [(q[0] + a, q[1] + b) for a, b in NEIGHBOURS]
    return found


def split(src):
    px = src.load()
    opaque = {(x, y) for y in range(80) for x in range(80) if px[x, y]}
    # the sparkles: every piece but the biggest, her
    pieces, rest = [], set(opaque)
    while rest:
        piece = flood(opaque, min(rest))
        pieces.append(piece)
        rest -= piece
    small = [p for p in pieces if len(p) <= SPARKLE_MAX]
    her = opaque - set().union(*small)
    sparkles = []
    for piece in small:
        near = [s for s in sparkles if any(max(abs(x - u), abs(y - v)) <= SPARKLE_GAP for x, y in piece for u, v in s)]
        for s in near:
            sparkles.remove(s)
        sparkles.append(set(piece).union(*near))
    sparkles.sort(key=lambda p: (min(y for _, y in p), min(p)))

    hair = flood({(x, y) for x, y in her
                  if y in BACK_HAIR_ROWS and x <= BACK_HAIR_TO_X[y] and px[x, y] in HAIR_SLOTS}, BACK_HAIR_SEED)
    hair_top = {(x, y) for x, y in hair if y <= HAIR_TOP_TO_ROW}
    arm = {(x, y) for x, y in her if y in ARM and ARM[y][0] <= x <= ARM[y][1]} if ARM_STYLE == "rises" else set()
    hand = {(x, y) for x, y in arm if y in CUFF and x >= CUFF[y]}
    sleeve = arm - hand
    body = (her - hair - arm) | hair_top | (hair & HAIR_BY_GAP)
    under_cuff = {(x, y): GREY for y in range(41, 45) for x in range(CUFF[y], CUFF[y] + 3) if (x, y) in hand}
    near_hair = {(x + a, y + b) for x, y in hair for a in range(-HAIR_UNDER_REACH, HAIR_UNDER_REACH + 1)
                 for b in range(-HAIR_UNDER_REACH, HAIR_UNDER_REACH + 1)}
    under_hair = {q: HAIR for q in (near_hair & her) - hair
                  if q[1] in HAIR_UNDER_ROWS and q[0] in HAIR_UNDER_X and q not in arm}
    moving_hair = {(x, y) for x, y in hair if y >= HAIR_MOVES_FROM_ROW}

    def layer(pixels, painted=None):
        im = Image.new("P", src.size, 0)
        im.putpalette(src.getpalette())
        p = im.load()
        for x, y in pixels:
            p[x, y] = px[x, y]
        for (x, y), v in (painted or {}).items():
            p[x, y] = v
        return im

    shoulder = {(x, y) for x, y in arm if y <= SHOULDER_TO_ROW}

    parts = {"body": layer(body), "hair": layer(moving_hair, under_hair)}
    if arm:
        parts.update(shoulder=layer(shoulder, ARMPIT), sleeve=layer(sleeve, under_cuff), hand=layer(hand))
    ORDER[:] = [name for name in BASE_ORDER if name in parts]
    SPARKLES.clear()
    for i, sparkle in enumerate(sparkles):
        name = f"sparkle{i}"
        parts[name] = layer(sparkle)
        ORDER.append(name)
        PIVOTS[name] = min(sparkle)
        SPARKLES[name] = SPARKLE_BEATS[i % len(SPARKLE_BEATS)]
    FREE_EDGES.clear()
    if arm:
        FREE_EDGES["sleeve"] = free_edges(parts["sleeve"], her)
    return parts


def touch_up(part, degrees, image, source=None):
    """The turned sleeve, its outline put back along its free edges."""
    return outline(image, FREE_EDGES[part], PIVOTS[part], degrees) if part in FREE_EDGES else image


def turn(t):
    return round(keyframes(ARM_TURN, t))


def wrist_shift(t):
    """Where the wrist goes as the sleeve turns at the shoulder, from where Platinum draws it."""
    a = math.radians(turn(t))
    x, y = WRIST[0] - SHOULDER[0], WRIST[1] - SHOULDER[1]
    return x * math.cos(a) - y * math.sin(a) - x, x * math.sin(a) + y * math.cos(a) - y


def key(part, t):
    if part == "sleeve":
        return turn(t), 0, 0
    if part == "hand":
        return (0, *wrist_shift(t))
    if part == "hair":
        return 0, 0, keyframes(HAIR_BOB, t)
    if part in SPARKLES:
        return 0, 0, SPARKLE_RISE * keyframes(SPARKLES[part], t)
    return 0, 0, 0
