#!/usr/bin/env python3
"""The area list's picture of Sinnoh (GAME-146, GAME-149), in the copy of Black 2's archive 157 the game opens
(pokedex_art.py): the build runs it through gen5_archives.platinum_copy, Anvil on the player's ROMs. It reads Platinum's
art only through platinum_rom.py (by way of dex_map_art.py, for the reduction below), and imports nothing GPL.

Black 2's area list (pokebw2 ov304 zukan_area_list_view.c ZukanAreaListView_CreateActors, the HABITAT LIST menu) shows
a small picture of Unova in its selector, above "A:INFO": the "decide" sprite, cell 17 of NCER 63 (animation 15 of
NANR 73, cells 13 to 17 its bobbing frames), whose 64x64 OAM is characters 34 on of NCGR 57 (1D, 128-byte names) in
NCLR 53's palette 4. Only those cells use palette 4. The picture is 45x33 at (10, 15) of the 64x64, inside a dark
frame of Black 2's (1 pixel left and right, 3 above and below), which stays.

The port's picture (GAME-149, the owner's choice of 2026-10-19) is dex_area_picture_art.py's: a painted Sinnoh of
WIDTH x HEIGHT in at most as many colours as the frame leaves free, drawn into the palette entries the frame doesn't
use. Before it (FROM_ART False, GAME-146): the area page's map (dex_map_art.page: the owner's picture of the land
around Platinum's map, with Platinum's map through it) cropped around Platinum's panel, CROP, and reduced 4 to 1 by
the mean of each 4x4 block (the most common colour of each, tried too, keeps every route's outline and reads as
clutter at this size), in those entries by a median cut (deterministic, so the build's and Anvil's are the same); at
that size Platinum's routes read as orange lines and blobs.

  dex_area_picture.py pack PICTURE.png    a WIDTH x HEIGHT picture (opaque) into dex_area_picture_art.py
  dex_area_picture.py unpack OUT.png      that picture back
"""
import struct
import sys

import dex_area_picture_art
import dex_map_art
import platinum_ui

# The picture from dex_area_picture_art.py; False: the area page's map, reduced (GAME-146's)
FROM_ART = True

ARCHIVE = 157
CHARS, PALETTE = 57, 53
PICTURE_PALETTE = 4
# The 64x64 OAM's first character name, and the bytes a name stands for (1D mapping, shift 2)
FIRST_NAME, NAME_BYTES = 34, 128
SIZE = 64
# The picture inside the frame
X, Y, WIDTH, HEIGHT = 10, 15, 45, 33
SCALE = 4
# The area page's 256x168 cropped to WIDTH x HEIGHT times SCALE, around Platinum's panel (dex_map_art.PANEL_X, _Y,
# 168x128) with a little of the land around it
CROP_X, CROP_Y = dex_map_art.PANEL_X - 6, dex_map_art.PANEL_Y - 2


def art_indices() -> list:
    """dex_area_picture_art.py's picture: rows of WIDTH x HEIGHT indices into its PALETTE."""
    art = dex_area_picture_art
    pixels = [i for i, n in art.RUNS for _ in range(n)]
    assert (art.WIDTH, art.HEIGHT) == (WIDTH, HEIGHT) and len(pixels) == WIDTH * HEIGHT, \
        f"dex_area_picture_art: not {WIDTH}x{HEIGHT}"
    return [pixels[y * WIDTH:(y + 1) * WIDTH] for y in range(HEIGHT)]


def picture(platinum) -> list:
    """The picture: rows of WIDTH x HEIGHT 15-bit colours, each the mean of its 4x4 block (on 5-bit channels)."""
    page = dex_map_art.page(platinum)
    rows = []
    for y in range(HEIGHT):
        row = []
        for x in range(WIDTH):
            block = [_channels(page[CROP_Y + y * SCALE + j][CROP_X + x * SCALE + i])
                     for j in range(SCALE) for i in range(SCALE)]
            mean = [round(sum(c[k] for c in block) / len(block)) for k in range(3)]
            row.append(mean[0] | mean[1] << 5 | mean[2] << 10)
        rows.append(row)
    return rows


def _channels(colour: int) -> tuple:
    return tuple(colour >> shift & 31 for shift in (0, 5, 10))


def median_cut(pixels: list, count: int) -> list:
    """At most count 15-bit colours for the pixels: Heckbert's median cut on 5-bit channels, splitting the box with the
    widest channel at its median, each box's colour its pixels' mean."""
    boxes = [sorted(_channels(c) for c in pixels)]
    while len(boxes) < count:
        def spread(box):
            return max(max(c[k] for c in box) - min(c[k] for c in box) for k in range(3))
        widest = max(range(len(boxes)), key=lambda i: (spread(boxes[i]), -i))
        box = boxes[widest]
        if spread(box) == 0:
            break
        channel = max(range(3), key=lambda k: (max(c[k] for c in box) - min(c[k] for c in box), -k))
        box = sorted(box, key=lambda c: (c[channel], c))
        half = len(box) // 2
        boxes[widest:widest + 1] = [box[:half], box[half:]]
    colours = []
    for box in boxes:
        mean = [round(sum(c[k] for c in box) / len(box)) for k in range(3)]
        colour = mean[0] | mean[1] << 5 | mean[2] << 10
        if colour not in colours:
            colours.append(colour)
    return colours


def nearest(colour: int, palette: dict) -> int:
    """The index of palette ({index: colour}) nearest a colour (ties: the lowest index)."""
    r, g, b = _channels(colour)
    return min(sorted(palette), key=lambda i: sum((a - c) ** 2 for a, c in zip((r, g, b), _channels(palette[i]))))


def _chars_offset(d) -> int:
    t = platinum_ui.blocks(d)[b"RAHC"]
    return t + 8 + struct.unpack_from("<I", d, t + 8 + 0x14)[0]


def _palette_offset(d) -> int:
    t = platinum_ui.blocks(d)[b"TTLP"]
    return t + 8 + struct.unpack_from("<I", d, t + 0x14)[0] + PICTURE_PALETTE * 32


def _pixel_offset(x: int, y: int) -> tuple:
    """A pixel of the 64x64 OAM: its byte from the first name, and whether it's the high nibble."""
    tile = y // 8 * (SIZE // 8) + x // 8
    return FIRST_NAME * NAME_BYTES + tile * 32 + (y % 8) * 4 + (x % 8) // 2, x & 1


def read_sprite(chars: bytes, palette: bytes) -> tuple:
    """Black 2's 64x64 (rows of palette indices) and palette 4's 16 colours, from NCGR 57 and NCLR 53."""
    d, p = bytearray(chars), bytearray(palette)
    if d[0] in (0x10, 0x11):
        d = bytearray(platinum_ui.mts.unlz(bytes(d)))
    if p[0] in (0x10, 0x11):
        p = bytearray(platinum_ui.mts.unlz(bytes(p)))
    base, pal = _chars_offset(d), _palette_offset(p)
    rows = []
    for y in range(SIZE):
        row = []
        for x in range(SIZE):
            offset, high = _pixel_offset(x, y)
            row.append(d[base + offset] >> 4 if high else d[base + offset] & 15)
        rows.append(row)
    return rows, [struct.unpack_from("<H", p, pal + i * 2)[0] for i in range(16)]


def inside(x: int, y: int) -> bool:
    return X <= x < X + WIDTH and Y <= y < Y + HEIGHT


def build(chars: bytes, palette: bytes, platinum) -> tuple:
    """NCGR 57 and NCLR 53 (their bytes) with Sinnoh's picture: the frame's indices (Black 2's pixels outside the
    picture) and their colours kept, the picture in the others."""
    sprite, colours = read_sprite(chars, palette)
    frame = sorted({v for y, row in enumerate(sprite) for x, v in enumerate(row) if v and not inside(x, y)})
    free = [i for i in range(1, 16) if i not in frame]
    if FROM_ART:
        if len(dex_area_picture_art.PALETTE) > len(free):
            raise ValueError(f"dex_area_picture_art has {len(dex_area_picture_art.PALETTE)} colours; the frame leaves "
                             f"{len(free)}")
        own = dict(zip(free, dex_area_picture_art.PALETTE))
        indices = [free[i] for row in art_indices() for i in row]
    else:
        pixels = [c for row in picture(platinum) for c in row]
        own = dict(zip(free, median_cut(pixels, len(free))))
        indices = [nearest(c, own) for c in pixels]

    def change_chars(d):
        base = _chars_offset(d)
        for y in range(HEIGHT):
            for x in range(WIDTH):
                offset, high = _pixel_offset(X + x, Y + y)
                v = indices[y * WIDTH + x]
                b = d[base + offset]
                d[base + offset] = (b & 0x0F | v << 4) if high else (b & 0xF0 | v)

    def change_palette(d):
        pal = _palette_offset(d)
        for i, colour in own.items():
            struct.pack_into("<H", d, pal + i * 2, colour)

    return platinum_ui.edit(chars, change_chars), platinum_ui.edit(palette, change_palette)


def apply(narc, platinum) -> None:
    """The copy of archive 157 (a nitro.NARC) with Sinnoh's picture."""
    narc.files[CHARS], narc.files[PALETTE] = build(narc.files[CHARS], narc.files[PALETTE], platinum)


def render(chars: bytes, palette: bytes, scale: int = 8):
    """The 64x64 sprite as a Pillow image (transparent index 0), scaled."""
    from PIL import Image

    sprite, colours = read_sprite(chars, palette)
    image = Image.new("RGBA", (SIZE, SIZE))
    image.putdata([(0, 0, 0, 0) if v == 0 else dex_map_art.to_rgb(colours[v]) + (255,) for row in sprite for v in row])
    return image.resize((SIZE * scale, SIZE * scale), Image.NEAREST)


# --- the picture's module ---

def pack(path: str, out: str):
    """A WIDTH x HEIGHT picture into dex_area_picture_art.py: its colours (15-bit, in the order they come) and its
    pixels as runs of indices. The module's notes are kept."""
    from PIL import Image

    img = Image.open(path).convert("RGBA")
    if img.size != (WIDTH, HEIGHT):
        sys.exit(f"{path}: {img.size[0]}x{img.size[1]}, the picture is {WIDTH}x{HEIGHT}")
    pixels = []
    for i, (r, g, b, a) in enumerate(img.get_flattened_data()):
        if a != 255:
            sys.exit(f"{path}: a transparent pixel at {i % WIDTH},{i // WIDTH}: the picture is opaque")
        pixels.append((r >> 3) | (g >> 3) << 5 | (b >> 3) << 10)
    palette = list(dict.fromkeys(pixels))
    runs = []
    for c in pixels:
        i = palette.index(c)
        if runs and runs[-1][0] == i:
            runs[-1][1] += 1
        else:
            runs.append([i, 1])
    text = open(dex_area_picture_art.__file__, encoding="utf-8").read()
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(text[:text.index("# The picture's size")])
        f.write(f"# The picture's size\nWIDTH, HEIGHT = {WIDTH}, {HEIGHT}\n")
        f.write("# Its colours, 15-bit (BGR555, as the DS's palettes)\nPALETTE = [%s]\n"
                % ", ".join("0x%04X" % c for c in palette))
        f.write("# Its pixels in raster order, as runs of (index into PALETTE, length)\nRUNS = [\n")
        for k in range(0, len(runs), 8):
            f.write("    " + " ".join("(%d, %d)," % tuple(r) for r in runs[k:k + 8]) + "\n")
        f.write("]\n")
    print(f"{len(palette)} colours, {len(runs)} runs")


def unpack(out: str):
    """dex_area_picture_art.py's picture back, as a PNG."""
    from PIL import Image

    image = Image.new("RGB", (WIDTH, HEIGHT))
    image.putdata([dex_map_art.to_rgb(dex_area_picture_art.PALETTE[i]) for row in art_indices() for i in row])
    image.save(out)


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "pack":
        pack(sys.argv[2], dex_area_picture_art.__file__)
    elif len(sys.argv) >= 3 and sys.argv[1] == "unpack":
        unpack(sys.argv[2])
    else:
        sys.exit(__doc__)

