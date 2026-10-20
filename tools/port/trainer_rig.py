#!/usr/bin/env python3
"""Animated trainer sprites made from Platinum's own art: a rig cuts one of Platinum's front sprites into parts and
moves them the way Black 2 animates its trainers (one multi-cell whose nodes each play a cell animation), written as
Black 2's MCSS sprite: the 8 files of a/0/7/1, in make_trainer_sprites.py's layout (characters, texture and cell
animations LZ-compressed, the rest raw, as mcss.c reads them).

Every angle a part takes is drawn ahead with RotSprite (Scale2x three times, turned by nearest neighbour, sampled
back at 1x) and cleaned of outline pixels left sticking out, as a cell of its own. The cell animations only swap
cells and move them by whole pixels, so the game never turns anything and shows exactly the pixels drawn here.

A rig is a module with:
  ORIGIN         the sprite's origin in Platinum's 80x80 frame: its bottom middle, (40, 80)
  TICKS, STEP    the animation's length and its key spacing, in ticks (MCSS advances one tick per update)
  ORDER          the parts, back to front
  PIVOTS         {part: (x, y)} in the frame: where each part turns, and where its node sits
  split(src)     {part: indexed 80x80 image}: the parts, with what moving parts uncover painted in. src is
                 Platinum's picture: its still frame, with its intro frames below it for the classes that have them
  key(part, t)   (degrees, dx, dy): the part's turn (clockwise on screen) and shift at tick t; or (degrees, dx, dy,
                 image) to draw another of split()'s images for the part (a blink, a hand in another pose), which may
                 be empty to hide it
  touch_up(part, degrees, image, source)   (optional) the turned part's image, touched up: called for every angle but
                 0, with source the part's image unturned (split()'s)
The rigs made in Aseprite are data for anim_rig.py (anim_<class>.py, packed by aseprite_rig.py).
The still frame (the second multi-cell animation, which Black 2 shows when the trainer comes back after the battle)
is Platinum's frame itself, and the animation must end on it; or, for a rig with STILL_IS_END = True, it's the
animation's last frame, whatever that is.

make_trainer_sprites.py builds a class with a rig through build(rig, src, template) in place of make_sprite.

Usage, to preview and check a rig (in the container):
  trainer_rig.py B2_ROM POKEPLATINUM_DIR RIG_MODULE CLASS_DIR OUT_DIR
  e.g. trainer_rig.py b2.nds /host/game rig_roughneck roughneck /host/scratch/rig
It writes the 8 files, preview.gif (60 ticks a second) and sha1.txt, and checks the still frame.
"""
import hashlib
import importlib
import math
import struct
import sys
from pathlib import Path

from PIL import Image

import make_trainer_sprites as mts

MARGIN = 16  # room around a turned part


def ease(a, b, u):
    u = max(0.0, min(1.0, u))
    return a + (b - a) * (0.5 - 0.5 * math.cos(math.pi * u))


def keyframes(points, t):
    """The value through [(tick, value)...] at tick t, eased between points and held outside them."""
    if t <= points[0][0]:
        return points[0][1]
    for (t0, v0), (t1, v1) in zip(points, points[1:]):
        if t <= t1:
            return ease(v0, v1, (t - t0) / (t1 - t0))
    return points[-1][1]


def scale2x(img):
    """EPX/Scale2x of an indexed image."""
    w, h = img.size
    p = img.load()
    out = Image.new("P", (w * 2, h * 2), 0)
    out.putpalette(img.getpalette())
    q = out.load()
    get = lambda x, y: p[min(max(x, 0), w - 1), min(max(y, 0), h - 1)]  # noqa: E731
    for y in range(h):
        for x in range(w):
            e = p[x, y]
            a, b, c, d = get(x, y - 1), get(x + 1, y), get(x - 1, y), get(x, y + 1)
            q[2 * x, 2 * y] = a if c == a and c != d and a != b else e
            q[2 * x + 1, 2 * y] = b if a == b and a != c and b != d else e
            q[2 * x, 2 * y + 1] = c if d == c and d != b and c != a else e
            q[2 * x + 1, 2 * y + 1] = d if b == d and b != a and d != c else e
    return out


def clear_neighbours(p, x, y, w, h):
    return sum(1 for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))
               if not (0 <= x + a < w and 0 <= y + b < h) or p[x + a, y + b] == 0)


def rotsprite(piece, pivot, degrees):
    """A part turned `degrees` clockwise on screen about `pivot`, RotSprite's way, on a canvas MARGIN pixels larger
    on each side (the pivot moves by MARGIN). A pixel left with three clear neighbours is dropped, unless it comes
    from one that was a tip in the part already."""
    big = scale2x(scale2x(scale2x(piece)))
    bp, sp = big.load(), piece.load()
    w, h = piece.size
    out = Image.new("P", (w + 2 * MARGIN, h + 2 * MARGIN), 0)
    out.putpalette(piece.getpalette())
    op = out.load()
    a = math.radians(degrees)
    c, s = math.cos(a), math.sin(a)
    source = {}
    for y in range(out.height):
        for x in range(out.width):
            X, Y = x + 0.5 - MARGIN - pivot[0], y + 0.5 - MARGIN - pivot[1]
            sx, sy = X * c + Y * s + pivot[0], -X * s + Y * c + pivot[1]
            bx, by = int(math.floor(sx * 8)), int(math.floor(sy * 8))
            if 0 <= bx < big.width and 0 <= by < big.height and bp[bx, by]:
                op[x, y] = bp[bx, by]
                source[(x, y)] = (min(int(sx), w - 1), min(int(sy), h - 1))
    for (x, y), (sx, sy) in source.items():
        if clear_neighbours(op, x, y, out.width, out.height) >= 3 and clear_neighbours(sp, sx, sy, w, h) < 3:
            op[x, y] = 0
    return out


def free_edges(part, solid):
    """A part's pixels that face empty space (a neighbour neither in the part nor in `solid`, the frame's pixels that
    stay put), with their colours: where its outline is. For outline() to put back after turning it."""
    p = part.load()
    w, h = part.size
    return {(x, y): p[x, y] for y in range(h) for x in range(w) if p[x, y] and any(
        (x + a, y + b) not in solid and not (0 <= x + a < w and 0 <= y + b < h and p[x + a, y + b])
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))}


def outline(image, free, pivot, degrees, reach=1.5):
    """A part turned by rotsprite(), its outline put back: turning breaks a one-pixel outline, so each pixel on the
    turned part's edge that comes from within `reach` pixels of one of the part's free edges (free_edges()) takes that
    edge's colour. Edges that join other parts stay as they are."""
    p = image.load()
    w, h = image.size
    a = math.radians(degrees)
    c, s = math.cos(a), math.sin(a)
    edge = [(x, y) for y in range(h) for x in range(w) if p[x, y] and any(
        not (0 <= x + dx < w and 0 <= y + dy < h) or not p[x + dx, y + dy]
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    for x, y in edge:
        # where the pixel comes from on the part, as rotsprite() maps it
        X, Y = x + 0.5 - MARGIN - pivot[0], y + 0.5 - MARGIN - pivot[1]
        sx, sy = X * c + Y * s + pivot[0], -X * s + Y * c + pivot[1]
        near = min(free, key=lambda q: (q[0] + 0.5 - sx) ** 2 + (q[1] + 0.5 - sy) ** 2)
        if (near[0] + 0.5 - sx) ** 2 + (near[1] + 0.5 - sy) ** 2 <= reach ** 2:
            p[x, y] = free[near]
    return image


def srt(index, px=0, py=0):
    return struct.pack("<HHiihh", index, 0, 4096, 4096, px, py)


def build(rig, src, template, still_frame=None):
    """The 8 files of the sprite. src is Platinum's front.png (indexed, 80x80); template the 8 files of the Black 2
    sprite whose headers the new files take (make_trainer_sprites.FRONT_TEMPLATE's). The still frame is Platinum's,
    or the animation's last for a rig with STILL_IS_END (drawn from a first build). src may have intro frames below
    its still frame, as Platinum's picture of a class with an intro does: the rig may take parts from them."""
    still_src = src.crop((0, 0, mts.FRAME, mts.FRAME)) if src.size != (mts.FRAME, mts.FRAME) else src
    if still_frame is None and getattr(rig, "STILL_IS_END", False):
        first = read(build(rig, src, template, still_src))
        return build(rig, src, template, frame(first, rig.TICKS - 1, size=still_src.size, origin=rig.ORIGIN))
    parts = rig.split(src)
    images, pivots = {}, {}

    def cell(part, image, degrees):
        name = (image, degrees)
        if name not in images:
            if degrees == 0:
                images[name], pivots[name] = parts[image], rig.PIVOTS[part]
            else:
                images[name] = rotsprite(parts[image], rig.PIVOTS[part], degrees)
                pivots[name] = (rig.PIVOTS[part][0] + MARGIN, rig.PIVOTS[part][1] + MARGIN)
                # a rig may touch up its turned parts (the Clown's sleeves get their outline back)
                if hasattr(rig, "touch_up"):
                    images[name] = rig.touch_up(part, degrees, images[name], parts[image])
        return name

    tracks = {}
    for part in rig.ORDER:
        tracks[part] = []
        for t in range(0, rig.TICKS, rig.STEP):
            degrees, dx, dy, *image = rig.key(part, t)
            degrees = round(degrees, 1) + 0.0
            tracks[part].append((cell(part, image[0] if image else part, degrees if degrees else 0.0),
                                 int(round(dx)), int(round(dy))))
    still = ("still", 0.0)
    images[still], pivots[still] = still_frame or still_src, rig.ORIGIN
    names = list(images)

    # The texture: each cell's opaque box, shelf-packed. An empty one (a part hidden on some steps) draws one clear
    # pixel
    boxes = {n: images[n].point(lambda v: 255 if v else 0).getbbox() or (0, 0, 1, 1) for n in names}
    placed = mts.pack([(n, b[2] - b[0], b[3] - b[1]) for n, b in boxes.items()])
    assert placed, "the parts don't fit the texture"
    tex = Image.new("P", (mts.TEX_W, mts.TEX_H), 0)
    for n in names:
        tex.paste(images[n].crop(boxes[n]), placed[n])
    texture = bytearray(mts.TEX_W * mts.TEX_H // 2)
    tp = tex.load()
    for i in range(mts.TEX_W * mts.TEX_H):
        texture[i // 2] |= (tp[i % mts.TEX_W, i // mts.TEX_W] & 15) << (4 * (i & 1))

    # The bin: each cell's rect, from its pivot (x right, y up)
    index = {n: i for i, n in enumerate(names)}
    bin_file = struct.pack("<I4H", len(names), 0, 0, 0, 0)
    for n in names:
        l, t, r, b = boxes[n]
        tx, ty = placed[n]
        px, py = pivots[n]
        bin_file += struct.pack("<6i", (l - px) * 256, (py - t) * 256, (r - l) * 4096, (b - t) * 4096, tx * 4096,
                                ty * 4096) + bytes(24)

    # Cell animations: one per part, then the still frame's; multi-cells: the parts at their pivots, front first
    # (mcss.c draws each node a step deeper than the one before), then the still frame; multi-cell animations: the
    # intro, played once, then the still frame
    sequences = [(1, 1, 1, [(rig.STEP, srt(index[n], dx, dy)) for n, dx, dy in tracks[p]]) for p in rig.ORDER]
    sequences.append((0, 1, 2, [(4, struct.pack("<H", index[still]))]))
    nanr = mts.nitro_file(b"RNAN", 0x0100, [mts.anim_block(sequences)])
    count = len(rig.ORDER)
    front_first = list(reversed(rig.ORDER))
    hier = b"".join(struct.pack("<HhhH", rig.ORDER.index(p), rig.PIVOTS[p][0] - rig.ORIGIN[0],
                                rig.PIVOTS[p][1] - rig.ORIGIN[1], k << 8 | 0x21) for k, p in enumerate(front_first))
    hier += struct.pack("<HhhH", count, 0, 0, 0x21)
    mcs = struct.pack("<HHI", count, count, 0) + struct.pack("<HHI", 1, 1, count * 8)
    nmcr = mts.nitro_file(b"RCMN", 0x0100, [mts.block(b"KBCM", struct.pack("<HHII8x", 2, 0xBEEF, 0x14, 0x14 + len(mcs))
                                                      + mcs + hier)])
    nmar = mts.nitro_file(b"RAMN", 0x0100, [mts.anim_block([(1, 2, 1, [(rig.TICKS, srt(0))]),
                                                            (1, 2, 2, [(4, srt(1))])])])

    # The palette, texture and 2D characters (Platinum's frame, 10x10 tiles) in the template's files, as
    # make_trainer_sprites.make_sprite does
    nclr = bytearray(mts.unlz(template[7]))
    data = struct.unpack_from("<I", nclr, 0x10 + 0x14)[0]
    pal = src.getpalette()
    for c in range(16):
        r, g, b = pal[c * 3:c * 3 + 3]
        struct.pack_into("<H", nclr, 0x10 + 0x08 + data + c * 2, (r >> 3) | (g >> 3) << 5 | (b >> 3) << 10)
    ncgr = bytearray(mts.unlz(template[1]))
    assert struct.unpack_from("<HH", ncgr, 0x18) == (mts.TEX_H // 8, mts.TEX_W // 8)
    assert struct.unpack_from("<I", ncgr, 0x2c)[0] == 0x18, "unexpected NCGR data offset"
    ncgr[0x30:0x30 + len(texture)] = texture
    chars = bytearray(mts.unlz(template[0]))
    assert struct.unpack_from("<HH", chars, 0x18) == (mts.FRAME // 8, mts.FRAME // 8)
    tiles = bytearray()
    sp = src.load()
    for ty in range(mts.FRAME // 8):
        for tx in range(mts.FRAME // 8):
            for y in range(8):
                for x in range(0, 8, 2):
                    tiles.append((sp[tx * 8 + x, ty * 8 + y] & 15) | (sp[tx * 8 + x + 1, ty * 8 + y] & 15) << 4)
    chars[0x30:0x30 + len(tiles)] = tiles

    return [mts.lz10(bytes(chars)), mts.lz10(bytes(ncgr)), template[2], mts.lz10(nanr), nmcr, nmar, bin_file,
            bytes(nclr)]


# Reading the files back and drawing them, for previews and checks. A rig's cells are never turned (see above), so
# its frames are each node's cell pasted at its place; Black 2's own sprites turn and scale theirs, which the preview
# draws by nearest neighbour (close to, not exactly, what the DS draws).

def _blocks(data):
    out, off = {}, 16
    for _ in range(struct.unpack_from("<H", data, 14)[0]):
        size = struct.unpack_from("<I", data, off + 4)[0]
        out[bytes(data[off:off + 4])] = data[off + 8:off + size]
        off += size
    return out


def _knba(data):
    b = _blocks(data)[b"KNBA"]
    nseq, _, seq_off, frame_off, res_off = struct.unpack_from("<HHIII", b, 0)
    seqs = []
    for s in range(nseq):
        n, _, elem, _, mode, foff = struct.unpack_from("<HHHHII", b, seq_off + s * 16)
        frames = []
        for f in range(n):
            roff, dur, _ = struct.unpack_from("<IHH", b, frame_off + foff + f * 8)
            sx = sy = 4096
            if elem == 0:  # the cell alone
                i, rot, px, py = struct.unpack_from("<H", b, res_off + roff)[0], 0, 0, 0
            elif elem == 1:  # turned, scaled and moved
                i, rot, sx, sy, px, py = struct.unpack_from("<HHiihh", b, res_off + roff)
            else:  # moved
                i, _, px, py = struct.unpack_from("<HHhh", b, res_off + roff)
                rot = 0
            frames.append((i, px, py, dur, rot, sx / 4096, sy / 4096))
        seqs.append((mode, frames))
    return seqs


def read(files):
    # every file but the bin may be LZ-compressed; the bin is always raw (its first byte, the cell count, can look
    # like LZ's)
    files = [bytes(f) if k == 6 else bytes(mts.unlz(f)) for k, f in enumerate(files)]
    b = _blocks(files[4])[b"KBCM"]
    n, _, mc_off, hier_off = struct.unpack_from("<HHII", b, 0)
    nmcr = []
    for m in range(n):
        nodes, _, hoff = struct.unpack_from("<HHI", b, mc_off + m * 8)
        nmcr.append([struct.unpack_from("<HhhH", b, hier_off + hoff + k * 8) for k in range(nodes)])
    count = struct.unpack_from("<I", files[6], 0)[0]
    rects = [struct.unpack_from("<6i", files[6], 12 + c * 48) for c in range(count)]
    nclr = files[7]
    data = struct.unpack_from("<I", nclr, 0x10 + 0x14)[0]
    pal = []
    for c in range(16):
        v = struct.unpack_from("<H", nclr, 0x10 + 0x08 + data + c * 2)[0]
        pal += [(v & 31) << 3, (v >> 5 & 31) << 3, (v >> 10 & 31) << 3]
    tex = Image.new("P", (mts.TEX_W, mts.TEX_H))
    tex.putpalette(pal + [0] * (768 - len(pal)))
    raw = files[1][0x30:]
    tex.putdata([raw[i // 2] >> (4 * (i & 1)) & 15 for i in range(mts.TEX_W * mts.TEX_H)])
    return {"tex": tex, "rects": rects, "nanr": _knba(files[3]), "nmcr": nmcr, "nmar": _knba(files[5])}


def _at(seq, t):
    mode, frames = seq
    total = sum(f[3] for f in frames)
    if t >= total:
        t = t % total if mode in (2, 4) else total - 1
    for f in frames:
        if t < f[3]:
            return f
        t -= f[3]
    return frames[-1]


def opaque(img):
    """The mask of an indexed image's non-zero pixels."""
    return Image.frombytes("L", img.size, bytes(255 if v else 0 for v in img.tobytes()))


def frame(sprite, t, seq=0, size=(80, 80), origin=(40, 80)):
    """The sprite at tick t of a multi-cell animation, as an indexed image (0 clear), origin at `origin`."""
    out = Image.new("P", size, 0)
    out.putpalette(sprite["tex"].getpalette())
    # mcss.c draws each node a step deeper than the one before: the first node is in front, so paint the last first
    whole = _at(sprite["nmar"][seq], t)
    assert whole[4] == 0 and whole[5:7] == (1, 1), "a multi-cell animation that turns or scales the whole sprite"
    # one that moves the whole sprite (Black 2's Lass hops) moves the origin
    origin = (origin[0] + whole[1], origin[1] + whole[2])
    for node_seq, x, y, _ in reversed(sprite["nmcr"][whole[0]]):
        c, px, py, _, rot, sx, sy = _at(sprite["nanr"][node_seq], t)
        rx, ry, w, h, s, tt = sprite["rects"][c]
        w, h, s, tt = w // 4096, h // 4096, s // 4096, tt // 4096
        piece = sprite["tex"].crop((s, tt, s + w, tt + h))
        nx, ny = origin[0] + x + px, origin[1] + y + py
        if rot == 0 and sx == sy == 1:
            out.paste(piece, (nx + rx // 256, ny - ry // 256), opaque(piece))
            continue
        # turned (clockwise on screen) and scaled about the node: each pixel back through it into the cell
        a = rot * 2 * math.pi / 65536
        c_, s_ = math.cos(a), math.sin(a)
        pp, op = piece.load(), out.load()
        for oy in range(size[1]):
            for ox in range(size[0]):
                X, Y = ox + 0.5 - nx, oy + 0.5 - ny
                lx, ly = (X * c_ + Y * s_) / sx, (-X * s_ + Y * c_) / sy
                u, v = math.floor(lx - rx / 256), math.floor(ly + ry / 256)
                if 0 <= u < w and 0 <= v < h and pp[u, v]:
                    op[ox, oy] = pp[u, v]
    return out


def main():
    import ndspy.narc
    import ndspy.rom
    rom, platinum = ndspy.rom.NintendoDSRom.fromFile(sys.argv[1]), Path(sys.argv[2])
    rig = importlib.import_module(sys.argv[3])
    src = Image.open(platinum / "res/trainers/classes" / sys.argv[4] / "front.png")
    out = Path(sys.argv[5])
    out.mkdir(parents=True, exist_ok=True)
    narc = ndspy.narc.NARC(rom.getFileByName("a/0/7/1"))
    files = build(rig, src, narc.files[mts.FRONT_TEMPLATE * 8:(mts.FRONT_TEMPLATE + 1) * 8])
    sums = []
    for k, f in enumerate(files):
        (out / f"file{k}.bin").write_bytes(f)
        sums.append(f"{hashlib.sha1(f).hexdigest()}  file{k}.bin")
    (out / "sha1.txt").write_text("\n".join(sums) + "\n")
    print("\n".join(sums))

    sprite = read(files)
    end = frame(sprite, rig.TICKS - 1)
    assert frame(sprite, 0, seq=1).tobytes() == end.tobytes(), "the still frame isn't the animation's last"
    if getattr(rig, "STILL_IS_END", False):
        print(f"{len(sprite['rects'])} cells; the still frame is the animation's last")
    else:
        assert end.tobytes() == src.crop((0, 0, mts.FRAME, mts.FRAME)).tobytes(), \
            "the animation doesn't end on Platinum's frame"
        print(f"{len(sprite['rects'])} cells; the last frame and the still frame are Platinum's")

    frames = []
    for t in range(0, rig.TICKS + 60, 2):
        f = frame(sprite, min(t, rig.TICKS - 1), size=(110, 124), origin=(55, 118))
        bg = Image.new("RGB", f.size, (232, 236, 240))
        bg.paste(f.convert("RGB"), (0, 0), opaque(f))
        frames.append(bg.resize((330, 372), Image.NEAREST))
    frames[0].save(out / "preview.gif", save_all=True, append_images=frames[1:], duration=33, loop=0)


if __name__ == "__main__":
    main()
