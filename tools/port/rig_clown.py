"""The rig of Platinum's Clown, class TRAINER_CLASS_CLOWN: he juggles, keeping his balance. His outstretched arms
seesaw slowly from the shoulders, one rising as the other falls, and each Poké Ball in the air moves against its arm:
as the left arm rises, the left ball sinks and the right ball, over the falling right arm, rises. Up, down and up
again, floating, then back to rest. 120 ticks; the last frame is Platinum's.

Each arm's sleeve turns at the shoulder; its hand and cuff ride on the wrist without turning, so the small hand keeps
Platinum's pixels (turned, its fingers smear). The cuts are by Platinum's pixels (x, y in its 80x80 frame). The
shoulder the right-hand ball hides is painted in, under it (UNDER_BALL_B). A turned sleeve's thin outline breaks;
touch_up() puts it back along the sleeve's free edges. See trainer_rig.py for what a rig is.
"""
import math

from PIL import Image

from trainer_rig import free_edges, keyframes, outline

ORIGIN = (40, 80)
TICKS, STEP = 120, 4
OUTLINE, PURPLE, YELLOW, YELLOW_DARK = 0xF, 0x2, 0x3, 0x4

# The balls in the air: above his left hand, and on his right shoulder
BALL_A = {(x, y) for y in range(9, 16) for x in range(19, 26)}
BALL_B = ({(x, 29) for x in range(52, 55)} | {(x, 30) for x in range(51, 56)}
          | {(x, y) for y in (31, 32) for x in range(50, 57)} | {(x, 33) for x in range(51, 57)}
          | {(x, 34) for x in range(51, 56)} | {(x, 35) for x in range(52, 55)})
# His left arm, raised: each row's last column, from the hand down to the sleeve's tip in his armpit. The sleeve meets
# his face, then his ruffled collar, then his body; its column there is drawn by both, so turning it opens no gap
LEFT_ARM = {**{y: 24 for y in range(16, 25)}, 25: 26, 26: 27, 27: 28, **{y: 26 for y in range(28, 32)}, 32: 27, 33: 27,
            **{y: 26 for y in range(34, 37)}}
LEFT_SEAM_FROM = 25  # the rows where it meets him
# His right arm, held out: each row's first column, from the shoulder down to the sleeve's underside. Its first column
# by his body is drawn by both, as the left's last
RIGHT_ARM = {**{y: 46 for y in range(31, 42)}, 42: 48, 43: 51, 44: 51}
RIGHT_SEAM_TO = 42
# and in his armpit, where the sleeve's underside lifts off his body as the arm rises, the body keeps its first pixels,
# its outline carried on along them (the sleeve hides them at rest)
RIGHT_ARMPIT = {(x, 42) for x in range(48, 52)} | {(51, 43), (52, 43)}
ARMPIT_OUTLINE = {(52, 43): OUTLINE}
# The shoulder under the right-hand ball, as it would be: its outline running on from his collar to the sleeve's top
# (the ball's right edge drew its last pixel), and the sleeve's yellow below it
UNDER_BALL_B = {(50, 31): OUTLINE, (50, 32): YELLOW, (51, 32): OUTLINE, (52, 32): OUTLINE, (53, 32): OUTLINE,
                (51, 33): YELLOW_DARK, (52, 33): YELLOW_DARK, (53, 33): YELLOW_DARK, (54, 33): OUTLINE,
                (55, 33): OUTLINE, (56, 33): OUTLINE, **{(x, 34): YELLOW_DARK for x in range(51, 56)},
                **{(x, 35): YELLOW for x in range(52, 55)}}

# The hands, with the cuffs: the left's, above its sleeve (its red wrist ruffle and the skin and outline around it),
# and the right's, from the brown seam between sleeve and purple cuff out, the seam drawn by the sleeve too (by row,
# its column; above and below the cuff, the hand starts at the fingers). Each rides on its wrist
HAND_SLOTS = (0x1, 0xA, 0xB, 0xC, 0xD)
LEFT_HAND_TO_ROW, LEFT_WRIST_ROWS = 22, range(23, 26)
RIGHT_CUFF = {**{y: 62 for y in range(29, 34)}, 34: 59, 35: 59, **{y: 58 for y in range(36, 40)}, 40: 59,
              **{y: 60 for y in range(41, 45)}}
SHOULDERS = {"left": (26, 32), "right": (47, 38)}
WRISTS = {"left": (18, 24), "right": (59, 38)}

# The right-hand ball's outline at its lower left, which Platinum leaves to his shoulder's dark edge: it rides with the
# ball, drawn behind the sleeve, so at rest the shoulder's pixel shows, and once the ball rises, the outline
BALL_B_RIM = {(50, 33): OUTLINE}

ORDER = ["body", "ball_b_rim", "left", "left_hand", "right", "right_hand", "ball_a", "ball_b"]  # back to front
PIVOTS = {"body": ORIGIN, **SHOULDERS, "left_hand": WRISTS["left"], "right_hand": WRISTS["right"], "ball_a": (22, 12),
          "ball_b": (53, 32), "ball_b_rim": (50, 33)}
# The seesaw's beat: 1 is the left hand up and the right down, -1 the other way. Both arms turn the same way at once:
# clockwise on screen raises the raised left arm and lowers the outstretched right one. Slow and eased, half a second
# a swing
BEAT = [(0, 0), (8, 0), (34, 1), (64, -1), (94, 1), (112, 0)]
ARM_TURN = 10  # degrees, at the top and bottom of the beat
# The balls move against their arms, this many pixels up and down: the left ball down as the left arm rises, the
# right ball up as the right arm falls
BALL_RISE = 4


# The sleeves' free edges, from split(): their pixels that face empty space (the balls count as empty, as they move
# off), with their colours: Platinum's outline there
FREE_EDGES = {}


def split(src):
    px = src.load()
    opaque = {(x, y) for y in range(80) for x in range(80) if px[x, y]}
    ball_a, ball_b = BALL_A & opaque, BALL_B & opaque
    left = {(x, y) for x, y in opaque - ball_a if y in LEFT_ARM and x <= LEFT_ARM[y]}
    right = {(x, y) for x, y in opaque - ball_b if y in RIGHT_ARM and x >= RIGHT_ARM[y]}
    seams = ({(LEFT_ARM[y], y) for y in LEFT_ARM if y >= LEFT_SEAM_FROM}
             | {(RIGHT_ARM[y], y) for y in RIGHT_ARM if y < RIGHT_SEAM_TO} | RIGHT_ARMPIT) & opaque
    body = (opaque - ball_a - ball_b - left - right) | seams

    def touches(x, y, kinds):
        return any(px[x + a, y + b] in kinds for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))

    # the left hand: everything above its sleeve, and at the wrist the ruffle, skin and their outline, and the
    # sleeve's purple and outline touching them, which the sleeve draws too: where the turned sleeve's end lands a
    # pixel off the hand's, the hand covers the gap
    left_hand = {(x, y) for x, y in left if y <= LEFT_HAND_TO_ROW or (y in LEFT_WRIST_ROWS and (
        px[x, y] in HAND_SLOTS or (px[x, y] in (PURPLE, OUTLINE) and touches(x, y, HAND_SLOTS))))}
    left_sleeve = (left - left_hand) | {(x, y) for x, y in left_hand
                                         if y in LEFT_WRIST_ROWS and px[x, y] in (PURPLE, OUTLINE)}
    # and under the wrist's ruffle, hidden by the hand, the sleeve goes on: where the hand and the turned sleeve's end
    # land a pixel apart, sleeve shows, not a hole (its outline where the ruffle's is)
    under_wrist = {(x, y): OUTLINE if px[x, y] == OUTLINE else YELLOW_DARK
                   for x, y in left_hand - left_sleeve if y in LEFT_WRIST_ROWS}
    right_hand = {(x, y) for x, y in right if y in RIGHT_CUFF and x >= RIGHT_CUFF[y]}
    right_sleeve = (right - right_hand) | {(x, y) for x, y in right_hand if px[x, y] == 0x5}
    # and the sleeve goes on under the cuff's first columns, hidden by it: where the turned sleeve's end and the cuff
    # land a pixel apart, sleeve shows, not a gap. Yellow, with its outline under the corners of the cuff's top and
    # bottom outlines, which it carries on
    under_cuff = {(x, y): YELLOW_DARK for y in range(35, 42) for x in range(RIGHT_CUFF[y], RIGHT_CUFF[y] + 3)
                  if (x, y) in right_hand and (x, y) not in right_sleeve}
    under_cuff.update({(RIGHT_CUFF[y], y): OUTLINE for y in (34, 42)})

    def layer(pixels, painted=None):
        im = Image.new("P", src.size, 0)
        im.putpalette(src.getpalette())
        p = im.load()
        for x, y in pixels:
            p[x, y] = px[x, y]
        for (x, y), v in (painted or {}).items():
            p[x, y] = v
        return im

    parts = {"body": layer(body, ARMPIT_OUTLINE), "left": layer(left_sleeve, under_wrist),
             "left_hand": layer(left_hand),
             "right": layer(right_sleeve, {**UNDER_BALL_B, **under_cuff}), "right_hand": layer(right_hand),
             "ball_a": layer(ball_a), "ball_b": layer(ball_b), "ball_b_rim": layer(set(), BALL_B_RIM)}
    for part in SHOULDERS:
        FREE_EDGES[part] = free_edges(parts[part], opaque - ball_a - ball_b)
    return parts


def touch_up(part, degrees, image):
    """A turned sleeve, its outline put back along its free edges (the edges where it joins his body and its cuff
    stay as they are)."""
    return outline(image, FREE_EDGES[part], PIVOTS[part], degrees) if part in FREE_EDGES else image


def turn(arm, t):
    """The arm's turn at tick t, in whole degrees, clockwise on screen: the left arm's up, the right arm's down."""
    return round(ARM_TURN * keyframes(BEAT, t))


def wrist_shift(arm, t):
    """Where the wrist goes as the sleeve turns at the shoulder, from where Platinum draws it."""
    a = math.radians(turn(arm, t))
    (sx, sy), (wx, wy) = SHOULDERS[arm], WRISTS[arm]
    x, y = wx - sx, wy - sy
    return x * math.cos(a) - y * math.sin(a) - x, x * math.sin(a) + y * math.cos(a) - y


def key(part, t):
    if part in SHOULDERS:
        return turn(part, t), 0, 0
    if part in ("left_hand", "right_hand"):
        return (0, *wrist_shift(part.removesuffix("_hand"), t))
    if part == "ball_a":
        return 0, 0, BALL_RISE * keyframes(BEAT, t)
    if part in ("ball_b", "ball_b_rim"):
        return 0, 0, -BALL_RISE * keyframes(BEAT, t)
    return 0, 0, 0
