#!/usr/bin/env python3
"""Platinum's ??? type, Curse's, in the Gen V battle's look. The battle gives Curse Black 2's type 17, which Black 2
keeps for typeless moves and draws nothing for (game/src/gen5/gen5_types.c); these are the graphics it points 17 at,
Platinum's own for ???, made from the player's ROMs (gen5_archives.convert; Anvil makes both archives on the player's
machine), never committed:

- The type tag, in archive 82 (Black 2's shared menu graphics: pokebw2 system/app_menu_common.c, whose type icons
  are members 0x22 + type, and COOL's, the first contest icon, at 0x22 + 17), in Black 2's tag style, the owner's
  choice (docs/decisions.md): it goes after the archive's members, as ICON_MEMBER, made from Black 2's Normal tag.
  Black 2's seventeen tags share one frame: a 32x12 box (rows 2 to 13 of the 32x16 cell), a 1-pixel outline with
  square corners round a flat body, no bevel; the outline is the type's dark shade, or Black 2's dark grey (14, in
  every row) for Normal and Steel. Their capitals are 7 pixels high, white (15) with a shadow of that dark grey to
  the right, below and below right, centred in the body, a letter 1 to 3 columns after the last (Ghost, Fire, Ice).
  The ??? tag keeps Normal's frame pixel for pixel and fills its body with Platinum's ??? colour (its type icon's
  body: type_icons/shared.pal, row 2, 10); its outline is that teal's dark shade, the owner's pick (dark_shade: the
  value scaled as Ghost's and Fire's outlines are from their bodies, hue and saturation kept), and its letters'
  shadow Black 2's dark grey, as Ghost's and Fire's.
  Both go into row ICON_ROW of Black 2's palette (member 0x21) at TAG_BODY and TAG_OUTLINE, slots Black 2's icons
  leave unused (magenta), so no other tag changes. Black 2's tags have no "?": QUESTION_MARK is the port's own drawing
  of one in their style, three of them spaced as Fire's letters. Black 2's look and Platinum's show it.
- The move tile's palette, in archive 11 (btlv_input.c loads the move tiles' palettes by type, 464 to 480): ???'s
  goes after the lower screen sets (lower_screen_sets.py), as TILE_PALETTE_MEMBER. In Platinum's look the copy
  takes Platinum's own (src/overlay011/move_palettes.c sMovePaletteMystery: platinum_battle_menus.py). Black 2's look
  has none, so it's made from Black 2's Normal palette, whose type colours are its six greys at 8 to 13, light to
  dark: each takes one of Platinum's ??? shades, those of the eight slots ??? and Normal differ in (2 to 9, Platinum's
  ??? being its Normal with mauve shades), the six whose Normal greys are nearest Black 2's in brightness, in order.

Usage (gen5_archives.py): add_icon(data, platinum) for archive 82, add_tile_palette(data, platinum) for archive 11
after its lower screen sets; platinum a PlatinumRom.
"""
import struct

import lower_screen_sets
import nitro
from make_trainer_sprites import lz10
from platinum_rom import BATTLE_SPRITES, TYPE_ICON_PALETTE

ICON_ARCHIVE = 82
B2_ICONS, B2_ICON_PALETTE = 0x22, 0x21  # Normal's tag, the first; their palette
B2_ICON_COUNT = 182  # the archive's members in Black 2
ICON_MEMBER = B2_ICON_COUNT  # gen5_types.c G5_MYSTERY_ICON
ICON_ROW = 2  # gen5_types.c G5_MYSTERY_ICON_ROW: Platinum's ??? icon's row too
ICON_SIZE = (32, 16)
PT_BODY = 10  # Platinum's ??? icon's body colour, in its palette's row ICON_ROW
TAG_BODY, TAG_OUTLINE = 10, 11  # where it and its dark shade go in Black 2's row
TAG_DARK, TAG_WHITE = 14, 15  # Black 2's dark grey (every tag's letter shadow) and white (their letters)
B2_UNUSED = 0x7C1F  # magenta
# The tags whose dark shade's relation to their body the ??? tag's follows (the owner's pick), and their palette rows
# (app_menu_common.c sTypeIconPalettes)
SHADE_TAGS = {7: 1, 9: 0}  # Ghost, Fire
# The port's own question mark, in Black 2's tag capitals' style: 7 high, 1-pixel strokes, the corners cut as in
# their C, 5 wide and its joint doubled for about their capitals' weight (the owner found a 4-wide one too light)
QUESTION_MARK = (
    ".###.",
    "#...#",
    "....#",
    "..##.",
    "..#..",
    ".....",
    "..#..",
)
TAG_TEXT = 3  # "???"
LETTER_GAP = 2  # columns from a letter to the next, the first the letter's shadow (Fire's)

TILE_ARCHIVE = 11
TILE_PALETTE_MEMBER = 1214  # gen5_types.c G5_MYSTERY_TILE_PALETTE: after the lower screen sets
B2_NORMAL_TILE = 464
B2_SHADES = range(8, 14)
PT_SHADES = range(2, 10)


# Nitro files, as platinum_battle_menus.py reads them (which imports this module for TILE_PALETTE_MEMBER)
def blocks(d: bytes) -> dict:
    """Each block's offset, by magic."""
    header_size, count = struct.unpack_from("<HH", d, 12)
    off, found = header_size, {}
    for _ in range(count):
        magic, size = bytes(d[off:off + 4]), struct.unpack_from("<I", d, off + 4)[0]
        found[magic] = off
        off += size
    return found


def unpack(data: bytes):
    compressed = data[0] in (0x10, 0x11)
    return bytearray(nitro.unlz(data) if compressed else data), compressed


def pack(d: bytearray, compressed: bool) -> bytes:
    return lz10(bytes(d)) if compressed else bytes(d)


def chars_base(d) -> int:
    r = blocks(d)[b"RAHC"]
    assert struct.unpack_from("<I", d, r + 12)[0] == 3, "4 bits a pixel"
    return r + 8 + struct.unpack_from("<I", d, r + 28)[0]


def palette_base(d) -> int:
    t = blocks(d)[b"TTLP"]
    return t + 8 + struct.unpack_from("<I", d, t + 20)[0]


def brightness(colour: int) -> float:
    r, g, b = colour & 31, colour >> 5 & 31, colour >> 10 & 31
    return 0.299 * r + 0.587 * g + 0.114 * b


def icon_grid(icon: bytes) -> list:
    """An icon's NCGR (4 bits a pixel, 8x8 characters left to right and down) as rows of colour indices."""
    width, height = ICON_SIZE
    base = chars_base(icon)
    assert struct.unpack_from("<I", icon, blocks(icon)[b"RAHC"] + 24)[0] == width * height // 2
    grid = [[0] * width for _ in range(height)]
    for i in range(width * height):
        tile, pixel = divmod(i, 64)
        x = tile % (width // 8) * 8 + pixel % 8
        y = tile // (width // 8) * 8 + pixel // 8
        grid[y][x] = icon[base + i // 2] >> (i & 1) * 4 & 15
    return grid


def set_icon_grid(icon: bytearray, grid: list):
    width, height = ICON_SIZE
    base = chars_base(icon)
    for i in range(0, width * height, 2):
        tile, pixel = divmod(i, 64)
        x = tile % (width // 8) * 8 + pixel % 8
        y = tile // (width // 8) * 8 + pixel // 8
        icon[base + i // 2] = grid[y][x] | grid[y][x + 1] << 4


def tag_frame(grid: list) -> tuple:
    """A Black 2 tag's box (left, top, right, bottom, inclusive): the cell's drawn pixels, all inside it, its edge
    one colour."""
    drawn = [(x, y) for y, row in enumerate(grid) for x, p in enumerate(row) if p]
    left, top = min(x for x, _ in drawn), min(y for _, y in drawn)
    right, bottom = max(x for x, _ in drawn), max(y for _, y in drawn)
    assert len(drawn) == (right - left + 1) * (bottom - top + 1), "a box"
    edge = {grid[y][x] for y in range(top, bottom + 1) for x in range(left, right + 1)
            if x in (left, right) or y in (top, bottom)}
    assert len(edge) == 1, edge
    return left, top, right, bottom


def dark_shade(body: int, tags: list) -> int:
    """body's dark shade as Black 2 shades a tag's outline from its body: its hue and saturation, its value (the
    brightest channel) scaled as in the tags given, each (body, outline), on average."""
    def value(c):
        return max(c & 31, c >> 5 & 31, c >> 10 & 31)
    scale = sum(value(outline) / value(fill) for fill, outline in tags) / len(tags)
    r, g, b = (round((body >> shift & 31) * scale) for shift in (0, 5, 10))
    return r | g << 5 | b << 10


def mystery_tag(normal: list) -> list:
    """The ??? tag: Normal's frame, Platinum's ??? body, three question marks in Black 2's tag lettering, the outline
    in the body's dark shade (TAG_OUTLINE), the letters' shadow Black 2's dark grey as every tag's."""
    left, top, right, bottom = tag_frame(normal)
    grid = [row[:] for row in normal]
    for y in range(top, bottom + 1):
        for x in range(left, right + 1):
            grid[y][x] = TAG_OUTLINE if x in (left, right) or y in (top, bottom) else TAG_BODY
    glyph_w, glyph_h = len(QUESTION_MARK[0]), len(QUESTION_MARK)
    text_w = TAG_TEXT * glyph_w + (TAG_TEXT - 1) * LETTER_GAP
    # the white strokes centred in the body, the shadow's row inside it below them
    x0 = left + 1 + (right - left - 1 - text_w) // 2
    y0 = top + 1 + (bottom - top - 1 - (glyph_h + 1)) // 2
    white = {(x0 + k * (glyph_w + LETTER_GAP) + gx, y0 + gy)
             for k in range(TAG_TEXT) for gy, line in enumerate(QUESTION_MARK) for gx, c in enumerate(line) if c == "#"}
    for x, y in {(x + dx, y + dy) for x, y in white for dx, dy in ((1, 0), (0, 1), (1, 1))} - white:
        grid[y][x] = TAG_DARK
    for x, y in white:
        grid[y][x] = TAG_WHITE
    assert all(left < x < right and top < y < bottom for x, y in white)
    return grid


def add_icon(data: bytes, platinum) -> bytes:
    narc = nitro.NARC(data)
    assert len(narc.files) == ICON_MEMBER, len(narc.files)
    icon, compressed = unpack(narc.files[B2_ICONS])
    set_icon_grid(icon, mystery_tag(icon_grid(icon)))
    narc.files.append(pack(icon, compressed))

    palette, compressed = unpack(narc.files[B2_ICON_PALETTE])
    base = palette_base(palette)

    def colour(row, index):
        return struct.unpack_from("<H", palette, base + row * 32 + index * 2)[0]
    shades = []
    for tag_type, row in SHADE_TAGS.items():
        grid = icon_grid(unpack(narc.files[B2_ICONS + tag_type])[0])
        left, top, _, _ = tag_frame(grid)
        shades.append((colour(row, grid[top + 1][left + 1]), colour(row, grid[top][left])))
    body = platinum.palette(BATTLE_SPRITES, TYPE_ICON_PALETTE)[ICON_ROW * 16 + PT_BODY] & 0x7FFF
    for index, value in ((TAG_BODY, body), (TAG_OUTLINE, dark_shade(body, shades))):
        assert colour(ICON_ROW, index) == B2_UNUSED, index
        struct.pack_into("<H", palette, base + ICON_ROW * 32 + index * 2, value)
    narc.files[B2_ICON_PALETTE] = pack(palette, compressed)
    return narc.save()


def tile_shades(b2_normal: list, pt_normal: list, pt_mystery: list) -> list:
    """Platinum's ??? shades for Black 2's Normal greys, light to dark: the six of Platinum's eight whose Normal
    colours are nearest in brightness, keeping their order (the least total difference)."""
    targets = [brightness(b2_normal[i]) for i in B2_SHADES]
    slots = sorted(PT_SHADES, key=lambda j: -brightness(pt_normal[j]))
    # best[k][m]: the least difference matching the first k greys with k of the first m slots
    inf = float("inf")
    best = [[0.0] * (len(slots) + 1)] + [[inf] * (len(slots) + 1) for _ in targets]
    for k, target in enumerate(targets, 1):
        for m in range(k, len(slots) + 1):
            best[k][m] = min(best[k][m - 1], best[k - 1][m - 1] + abs(target - brightness(pt_normal[slots[m - 1]])))
    chosen, m = [], len(slots)
    for k in range(len(targets), 0, -1):
        while best[k][m] == best[k][m - 1]:
            m -= 1
        chosen.append(slots[m - 1])
        m -= 1
    return [pt_mystery[j] for j in reversed(chosen)]


def add_tile_palette(data: bytes, platinum) -> bytes:
    narc = nitro.NARC(data)
    assert len(narc.files) == TILE_PALETTE_MEMBER, len(narc.files)
    palette, compressed = unpack(narc.files[B2_NORMAL_TILE])
    moves = platinum.move_palettes()
    base = palette_base(palette)
    b2_normal = list(struct.unpack_from("<16H", palette, base))
    shades = tile_shades(b2_normal, moves["Normal"], moves["Mystery"])
    for i, colour in zip(B2_SHADES, shades):
        struct.pack_into("<H", palette, base + i * 2, colour & 0x7FFF)
    # the sets' files that equal the originals keep sharing their data
    return lower_screen_sets.save_shared(data, narc.files + [pack(palette, compressed)])
