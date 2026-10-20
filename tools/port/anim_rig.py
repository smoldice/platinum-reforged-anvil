"""The rigs made in Aseprite (aseprite_rig.py packs them): each anim_<class>.py holds one as data, and this turns the
data into a rig for trainer_rig.py, from Platinum's own picture.

The data has no pixel of Platinum's. Each image is a part as drawn on some steps: which of Platinum's pixels it takes
(rows of runs, in one of Platinum's frames: the class's still frame, 0, or one of its intro frames, which the picture
stacks one pixel apart), and the pixels painted on it (palette slots), at their place in the 80x80 frame. A track is
each part's image, turn (degrees clockwise) and shift on each step. The parts in `outlines` get their outline put
back once turned (trainer_rig.outline), along every edge that faces clear space: a thin rim or a cloth's edge that
RotSprite would break up.

Anvil runs this on the player's ROM, so it imports nothing but PIL (and trainer_rig, which Anvil runs too, to touch
up a turned part).
"""
from PIL import Image

FRAME = 80
FRAME_PITCH = 81  # Platinum's frames are stacked one pixel apart in its picture (platinum_rom.py)


class Rig:
    ORIGIN = (40, 80)
    # The still frame (shown when the trainer comes back after the battle) is the animation's last
    STILL_IS_END = True

    def __init__(self, step, order, pivots, images, tracks, outlines=()):
        """step: ticks per step; order: the parts, back to front; pivots: {part: (x, y)}; images: {name: (frame,
        {y: ((x0, x1), ...)}, {(x, y): slot})}, runs from x0 up to x1 excluded; tracks: {part: [(image, degrees, dx,
        dy), ...]}, one per step; outlines: the parts whose outline is put back once turned."""
        self.STEP, self.ORDER, self.PIVOTS = step, list(order), dict(pivots)
        self.images, self.tracks, self.outlines = images, tracks, list(outlines)
        steps = {len(t) for t in tracks.values()}
        assert len(steps) == 1 and set(tracks) == set(order), "every part needs a track, all of the same length"
        self.TICKS = step * steps.pop()

    def split(self, src):
        sp = src.load()
        out = {}
        for name, (frame, runs, painted) in self.images.items():
            im = Image.new("P", (FRAME, FRAME), 0)
            im.putpalette(src.getpalette())
            p = im.load()
            top = frame * FRAME_PITCH
            for y, row in runs.items():
                for x0, x1 in row:
                    for x in range(x0, x1):
                        p[x, y] = sp[x, top + y]
            for (x, y), slot in painted.items():
                p[x, y] = slot
            out[name] = im
        return out

    def key(self, part, t):
        image, degrees, dx, dy = self.tracks[part][min(t // self.STEP, len(self.tracks[part]) - 1)]
        return degrees, dx, dy, image

    def touch_up(self, part, degrees, image, source):
        """A part in `outlines`, turned: its outline put back along the edges that face clear space."""
        if part not in self.outlines:
            return image
        from trainer_rig import free_edges, outline
        return outline(image, free_edges(source, set()), self.PIVOTS[part], degrees)
