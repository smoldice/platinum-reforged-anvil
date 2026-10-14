"""The rig of Platinum's Roughneck, class TRAINER_CLASS_ROUGHNECK: he tosses his Poké Ball up and catches it, the
way Black 2's Ace Trainer (male) does. Platinum draws him with the ball in the air above his open right hand; here
the ball starts in his palm, he winds up and throws it high (Black 2's timing: about 16 ticks up, 16 down), and
catches it, ending with it in his palm. His forearm and hand turn at the elbow: lowering as he winds up, flicking up
as he throws, dipping as he catches. His other arm, hanging straight, starts swung in, partly hidden behind his body,
swings out from the shoulder to where Platinum draws it, and back in. 80 ticks; the still frame is the last, the ball
in his hand and the arm swung in.

The cuts are by Platinum's pixels (x, y in its 80x80 frame). See trainer_rig.py for what a rig is.
"""
import math

from PIL import Image

from trainer_rig import keyframes

ORIGIN = (40, 80)
TICKS, STEP = 80, 4
STILL_IS_END = True

# The ball, floating above his hand
BALL = {(x, y) for y in range(29, 36) for x in range(59, 66)}
# His right forearm, wristband and hand, from the elbow out; the two columns where it meets the upper arm are drawn
# by both, so turning it opens no gap
FOREARM_ROWS, FOREARM_FROM_X, SEAM_FROM_X = range(39, 50), 50, 48
ELBOW = (48, 45)
# Where the ball sits when it's in his palm: this much below where Platinum draws it
IN_HAND = 8
PALM = (62, 40)  # the ball's centre in his palm, which turns with the forearm

# His other arm, hanging at his side: each row's last pixel (its black outline against his vest, which the vest
# keeps too so it stays outlined when the arm swings out), from just under the shoulder pad down to the fist. Its top
# row overlaps the pad's, so turning it opens no gap at the shoulder
ARM_ROWS = {**{y: 22 for y in range(30, 36)}, **{y: 21 for y in range(36, 41)}, **{y: 20 for y in range(41, 47)},
            **{y: 21 for y in range(47, 51)}, **{y: 19 for y in range(51, 58)}}
ARM_SEAM_ROW = 30
VEST_TO_ROW = 51  # the arm borders his vest above this row; below, the fist stands clear
SHOULDER = (21, 31)

ORDER = ["arm", "body", "ball", "forearm"]  # back to front: the other arm is behind his body, the ball behind his fingers
PIVOTS = {"body": ORIGIN, "arm": SHOULDER, "ball": (62, 32), "forearm": ELBOW}
# The forearm's turn in degrees, clockwise on screen (positive dips the hand)
FOREARM = [(0, 0), (8, 0), (16, 8), (20, -8), (32, -3), (48, -2), (52, 6), (60, 2), (68, 0)]
# The other arm's turn (negative swings it in, behind his body): out to his place and back in. Never past his place:
# Platinum cuts the arm along his vest, so swinging it further out would show the cut
ARM = [(0, -12), (4, -12), (40, 0), (76, -12)]
# The ball's flights: (ticks), from and to its height below where Platinum draws it. Between flights it's in his hand
FLIGHT = [((18, 34), IN_HAND, -20), ((34, 50), -20, IN_HAND)]


def split(src):
    px = src.load()
    opaque = {(x, y) for y in range(80) for x in range(80) if px[x, y]}
    ball = BALL & opaque
    forearm = {(x, y) for x, y in opaque - ball if y in FOREARM_ROWS and x >= FOREARM_FROM_X}
    seam = {(x, y) for x, y in opaque if y in FOREARM_ROWS and SEAM_FROM_X <= x < FOREARM_FROM_X}
    arm = {(x, y) for x, y in opaque if y in ARM_ROWS and x <= ARM_ROWS[y]}
    edge = {(ARM_ROWS[y], y) for y in ARM_ROWS if y < VEST_TO_ROW} & opaque
    body = (opaque - ball - forearm - {(x, y) for x, y in arm if y != ARM_SEAM_ROW}) | edge

    def layer(pixels):
        im = Image.new("P", src.size, 0)
        im.putpalette(src.getpalette())
        p = im.load()
        for x, y in pixels:
            p[x, y] = px[x, y]
        return im

    return {"body": layer(body), "arm": layer(arm), "ball": layer(ball), "forearm": layer(forearm | seam)}


def turned(point, degrees):
    """Where a point goes when the forearm turns by `degrees` at the elbow."""
    a = math.radians(degrees)
    x, y = point[0] - ELBOW[0], point[1] - ELBOW[1]
    return ELBOW[0] + x * math.cos(a) - y * math.sin(a), ELBOW[1] + x * math.sin(a) + y * math.cos(a)


def ease_in(a, b, u):
    u = max(0.0, min(1.0, u))
    return a + (b - a) * u * u


def ease_out(a, b, u):
    u = max(0.0, min(1.0, u))
    return a + (b - a) * (1 - (1 - u) * (1 - u))


def ball_height(t):
    """The ball's offset below Platinum's place for it at tick t: in the air (falling eases in, rising eases out),
    or in his palm, riding his hand."""
    for (t0, t1), y0, y1 in FLIGHT:
        if t0 <= t < t1:
            u = (t - t0) / (t1 - t0)
            return ease_in(y0, y1, u) if y1 > y0 else ease_out(y0, y1, u), False
    return IN_HAND, True


def key(part, t):
    if part == "arm":
        return keyframes(ARM, t), 0, 0
    turn = keyframes(FOREARM, t)
    if part == "forearm":
        return turn, 0, 0
    if part == "ball":
        dy, in_hand = ball_height(t)
        if in_hand:
            px, py = turned(PALM, turn)
            return 0, px - PALM[0], py - PALM[1] + dy
        return 0, 0, dy
    return 0, 0, 0
