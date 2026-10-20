#!/usr/bin/env python3
"""Black 2's archive 84 (the town map's art, which the Pokédex's area page and habitat list draw) with Sinnoh's map
(GAME-137, docs/pokedex-port.md section 7 and "Milestone 3: the plan"), made from the player's Platinum ROM: the build
runs it through gen5_archives.convert on the Platinum dump or the vanilla build, Anvil on the player's ROM. It reads
Platinum's art only through platinum_rom.py, and imports nothing GPL.

The lower screen is the owner's picture (dex_map_background.py, the land around the map: their pixels, none of
Platinum's) with Platinum's map showing through it at 1:1 where the picture is transparent: Platinum's area map's panel
is (80, 56)-(248, 184) on its screen, its detail pages' look (zukan.narc member 33's tiles, 64's screen, member 6's
palette, rows 1, 3 and 6), put at PANEL_X, PANEL_Y; the picture's transparent pixels lie in that panel, and its own
pixels there (the owner's frameless picture, 2026-10-19, paints over Platinum's blue frame: its 2-pixel ring and four
7x7 corners) stay the picture's. That one constant places the art here and the places in make_dex_area_data.py.

What the page loads (pokebw2 zukan_detail_map.c ZukanDetailMap_LoadMapBG; ov303 zukan_habitat_graphic.c LoadBG for
the habitat list's upper screen, BG6 and BG7):
- 0, the palette: 16 extended palettes of 256 colours, loaded into BG2's and BG3's slots; palette 0 holds the picture's
  colours from index 1 and Platinum's highlight row (member 6's row 8) at HIGHLIGHT_BASE + 0-15. Index 0 is
  transparent (8-bit BGs). The rest are zero, as Black 2's.
- 7 and 16, BG3: the picture as 8-bit characters (flipped copies shared) and its 256x256 screen; the rows under the
  touch bar (21 on) and below are character 0, blank.
- 5 and 17, BG2: the highlight's window. Character 0 is blank and transparent, 1 to N blank too, one for each 8x8 cell
  of the screen that some field's highlight can touch (the fields' cells and their neighbours, which carry the
  outline: pokedex_field_map.c), in raster order; the screen maps them there and character 0 everywhere else. The
  port's renderer draws the fields' cells into these characters, finding a pixel's character through member 17. The
  file has 256 blank characters, Black 2's count: the page loads 0x4000 bytes of it, whatever its size.
Black 2's members 2, 8, 12 and 19 (the cursor and the markers) and the others stay. After Black 2's last (20), for the
renderer, in Black 2's formats (the same NitroSystem files):
- 21, 22: Platinum's highlight strips (zukan.narc 30 normal, 31 special: 48 cell pieces of 5x5 in a 256x8 strip), as
  8-bit characters indexing palette 0 (Platinum's pixel v as HIGHLIGHT_BASE + v, 0 transparent).
- 23-26: Platinum's dungeon sprites as Platinum has them, decompressed: the palette (member 14), characters (108),
  cells (106) and animations (107): 2 normal, 3 special, 0 and 1 Mt. Coronet's, 4 and 5 Feebas's.
- 27-41: BG3's screen with a set of the hidden places shown (Platinum's members 65-68 at their places,
  ov21_021DC9BC.c), member 26 + the set's mask (bit 0 Newmoon Island, 1 Seabreak Path, 2 Fullmoon Island, 3 Spring
  Path; map_screen_member()), in place of 16. Whole screens, not pieces: on Black 2's 8x8 grid (the panel 4 pixels off
  Platinum's) Newmoon Island's and Fullmoon Island's pieces share characters.

With OWN_LAYOUT (GAME-153, the owner's choice of 2026-10-19), the page is Bulbapedia's map of Sinnoh
(dex_map_bulbapedia.py) with the owner's routes over it (dex_map_layout.py), none of Platinum's pixels; the hidden
places are the layout's pieces dex_map_layout.HIDDEN names, shown by the mask as Platinum's are. The layout isn't on
Platinum's 5-pixel grid, so the page lights its own fields, two more members after the hidden screens:
- 42: the fields' masks, the pixels the highlight lights: u16 offsets for fields 0-50 (0 for none), each mask u8 x, y,
  width, height, then its rows of (width + 7) / 8 bytes, bit n of byte k the pixel (x + 8k + n, y + row). A field's
  mask is its pieces' fill pixels and FIELD_GROW around them, as Platinum's cells and the strips' 2 pixels around them
  cover a field's fill and its outline;
- 43: the dungeons' spots: 4 bytes each, the first a dummy, as zukan_enc_platinum member 0 but x and y the sprite's
  anchor on the page (dex_map_layout.DUNGEONS), Mt. Coronet's flag Platinum's.
BG2's window is then the characters the masks touch. Without OWN_LAYOUT, the page as before (GAME-137).

The limits (section 7): BG3 at most MAP_TILE_LIMIT characters (768: from BG3's base, 0x14000, to the end of VRAM A on
the page, as Black 2's LoadMapBG loads at most 0xC000 bytes of member 7; and on the habitat list's upper screen BG6's,
0x10000, to BG7's base, 0x1C000); BG2's window at most WINDOW_TILE_LIMIT (256: what Black 2's page loads for BG2,
0x4000 bytes, and what the habitat list's BG7 has from 0x1C000 to the end of VRAM C); at most 239 colours,
HIGHLIGHT_BASE's below.

  dex_map_art.py pack PICTURE.png      the owner's picture (256x168 RGBA, at most 239 colours, transparent where
                                       Platinum's map shows, only in the panel) into dex_map_background.py
  dex_map_art.py unpack OUT.png        that picture back (RGBA, transparent where Platinum's map shows)
  dex_map_art.py render ARCHIVE OUT.png [HIDDEN]   the lower screen drawn from an archive 84 (HIDDEN: a mask of the
                                       hidden places shown, bit 0 Newmoon Island to bit 3 Spring Path)
  dex_map_art.py pack-map PICTURE.png  the map (256x168, opaque, at most MAP_COLOURS colours) into dex_map_bulbapedia.py
  dex_map_art.py pack-layout PICTURE.png   the routes (256x168 RGBA, transparent where the map shows) into
                                       dex_map_layout.py
"""
import struct
import sys

import nitro
from nitro import unlz
from platinum_rom import POKEDEX_ART, ncgr_chars, nclr_colours, nscr_screen

import dex_map_background
import dex_map_bulbapedia
import dex_map_layout

# The page: Bulbapedia's map with the owner's routes (GAME-153); False: the owner's background with Platinum's map
# (GAME-137)
OWN_LAYOUT = True

ARCHIVE = 84
# Black 2's members the page and the habitat list load
PALETTE, WINDOW_CHARS, MAP_CHARS, MAP_SCREEN, WINDOW_SCREEN = 0, 5, 7, 16, 17
BLACK2_MEMBERS = 21
# The members after Black 2's
STRIP_NORMAL, STRIP_SPECIAL = 21, 22
DUNGEON_PALETTE, DUNGEON_CHARS, DUNGEON_CELLS, DUNGEON_ANIMS = 23, 24, 25, 26
HIDDEN_SCREEN_FIRST = 27
# The hidden places, by their bit in a mask of those shown
HIDDEN_PLACES = ("Newmoon Island", "Seabreak Path", "Fullmoon Island", "Spring Path")
HIDDEN_MASKS = 1 << len(HIDDEN_PLACES)
# OWN_LAYOUT's members after the hidden screens: the fields' masks and the dungeons' spots
FIELD_MASKS = HIDDEN_SCREEN_FIRST + HIDDEN_MASKS - 1
DUNGEON_SPOTS = FIELD_MASKS + 1
# A field lit: its fill pixels and this many around them (Platinum's cell, 1 past the fill, and the strips' 2)
FIELD_GROW = 3
# The routes' outline (Platinum's brown), 2 pixels around their fills, and the map's colours at most
ROUTE_OUTLINE, OUTLINE_WIDTH = 0x2992, 2
MAP_COLOURS = 224

# Platinum's art (zukan.narc, game/res/graphics/pokedex/pokedex.order): the detail pages' palette (banner_sinnoh), the
# map's characters and screen, the hidden places' pieces and where ov21_021DC9BC.c puts them (in tiles), the strips,
# and the dungeon sprites
PL_PALETTE, PL_TILES, PL_SCREEN = 6, 33, 64
PL_HIDDEN = ((65, 13, 8), (66, 28, 7), (67, 11, 8), (68, 25, 16))
PL_STRIPS = (30, 31)
PL_HIGHLIGHT_ROW = 8
PL_DUNGEON = {DUNGEON_PALETTE: 14, DUNGEON_CHARS: 108, DUNGEON_CELLS: 106, DUNGEON_ANIMS: 107}
# The Pokédex's places (make_pokedex_enc_platinum.py): member 2, the fields: {column, row, columns, rows, cells[32]}
PL_ENCOUNTERS = "application/zukanlist/zkn_data/zukan_enc_platinum.narc"
PL_FIELDS, PL_DUNGEONS = 2, 0
FIELD_SIZE = 36

# Platinum's map panel on its screen, and where it goes on Black 2's lower screen (mockup E: centred). The owner may move
# it once their picture comes; the places follow (make_dex_area_data.py)
PL_PANEL_X, PL_PANEL_Y, PANEL_WIDTH, PANEL_HEIGHT = 80, 56, 168, 128
PANEL_X, PANEL_Y = 44, 20
OFFSET_X, OFFSET_Y = PANEL_X - PL_PANEL_X, PANEL_Y - PL_PANEL_Y
# Platinum's field grid (pokedex_field_map.c, ov21_021DC9BC.c): 30x30 cells of 5x5 pixels from (89, 30); the dungeon
# sprites' anchor, (x * 5 + 92, y * 5 + 32), Feebas's 18 higher
PL_FIELD_X, PL_FIELD_Y, CELL, GRID = 89, 30, 5, 30
PL_DUNGEON_X, PL_DUNGEON_Y, PL_FEEBAS_DY = 92, 32, -18

SCREEN_W, MAP_ROWS = 32, 21  # 8x8 cells: 256x168 above the touch bar
# The index dex_map_background.RUNS gives the picture's transparent pixels, where Platinum's map shows
TRANSPARENT = -1
HIGHLIGHT_BASE = 0xF0
# BG3's room (GAME-137, measured on both screens): the area page's BG VRAM (bank A, 128 KB) has the screens below
# 0x4000, BG0's characters at 0x4000, BG1's at 0xC000, BG2's 256 at 0x10000 and BG3's from 0x14000 to the bank's end,
# 0xC000 bytes, which Black 2's ZukanDetailMap_LoadMapBG loads of member 7 at most; the habitat list's upper screen
# (ov303, VRAM C) loads member 7 whole into BG6 at 0x10000, up to BG7's window at 0x1C000: 768 characters of 8x8 at 8
# bits on both. A 256x168 picture takes at most 1 + 672 cells and the hidden places' pieces (a picture of noise, every
# cell its own, took 616 with Platinum's panel), so any picture fits
MAP_TILE_LIMIT, WINDOW_TILE_LIMIT = 768, 256
BLANK = bytes(64)


def to_rgb(colour: int) -> tuple:
    return tuple((colour >> shift & 31) * 255 // 31 for shift in (0, 5, 10))


def _tiles_4bpp(chars: bytes) -> list:
    tiles = []
    for t in range(len(chars) // 32):
        tile = bytearray(64)
        for i, byte in enumerate(chars[t * 32:t * 32 + 32]):
            tile[i * 2], tile[i * 2 + 1] = byte & 15, byte >> 4
        tiles.append(bytes(tile))
    return tiles


def background() -> list:
    """The owner's picture as rows of 15-bit colours, None where it is transparent (where Platinum's map shows)."""
    pixels = [None if i == TRANSPARENT else dex_map_background.PALETTE[i]
              for i, n in dex_map_background.RUNS for _ in range(n)]
    w, h = dex_map_background.WIDTH, dex_map_background.HEIGHT
    assert (w, h) == (256, MAP_ROWS * 8) and len(pixels) == w * h, "dex_map_background: not 256x168"
    rows = [pixels[y * w:(y + 1) * w] for y in range(h)]
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            if c is None and not in_panel(x, y):
                raise ValueError(f"dex_map_background: transparent at {x},{y}, outside the map panel")
    return rows


def platinum_map(platinum, hidden: int = 0) -> list:
    """Platinum's area map as its upper screen shows it: rows of 15-bit colours, with the hidden places in the mask."""
    palette = platinum.palette(POKEDEX_ART, PL_PALETTE)
    tiles = _tiles_4bpp(ncgr_chars(unlz(platinum.narc(POKEDEX_ART)[PL_TILES])))
    width, height, entries = platinum.screen(POKEDEX_ART, PL_SCREEN)
    cols = width // 8
    entries = list(entries)
    for k, (member, x0, y0) in enumerate(PL_HIDDEN):
        if hidden >> k & 1:
            w, h, piece = platinum.screen(POKEDEX_ART, member)
            for y in range(h // 8):
                for x in range(w // 8):
                    entries[(y0 + y) * cols + x0 + x] = piece[y * (w // 8) + x]
    rows = [[0] * width for _ in range(height)]
    for i, e in enumerate(entries[:cols * (height // 8)]):
        tile, hf, vf, row = tiles[e & 0x3FF], e >> 10 & 1, e >> 11 & 1, e >> 12
        ox, oy = i % cols * 8, i // cols * 8
        for y in range(8):
            for x in range(8):
                v = tile[(7 - y if vf else y) * 8 + (7 - x if hf else x)]
                # Pixel 0 is the backdrop, palette 0's colour 0 (the panel has none)
                rows[oy + y][ox + x] = palette[row * 16 + v] if v else palette[0]
    return rows


def page(platinum, hidden: int = 0) -> list:
    """The lower screen's 256x168: the owner's picture, and where it is transparent Platinum's map (with the hidden
    places in the mask) from its panel, at PANEL_X, PANEL_Y. Only there: the picture's own pixels in the panel (where
    it paints over Platinum's frame) stay. With OWN_LAYOUT, layout_page's."""
    if OWN_LAYOUT:
        return layout_page(hidden)
    rows = background()
    pl = platinum_map(platinum, hidden)
    for y in range(MAP_ROWS * 8):
        for x in range(256):
            if rows[y][x] is None:
                rows[y][x] = pl[PL_PANEL_Y - PANEL_Y + y][PL_PANEL_X - PANEL_X + x]
    return rows


# --- OWN_LAYOUT: Bulbapedia's map with the owner's routes (GAME-153) ---

def _picture(module) -> list:
    """A packed picture's rows of 15-bit colours, None where it is transparent."""
    pixels = [None if i == TRANSPARENT else module.PALETTE[i] for i, n in module.RUNS for _ in range(n)]
    assert (module.WIDTH, module.HEIGHT) == (256, MAP_ROWS * 8) and len(pixels) == 256 * MAP_ROWS * 8, \
        f"{module.__name__}: not 256x{MAP_ROWS * 8}"
    return [pixels[y * 256:(y + 1) * 256] for y in range(MAP_ROWS * 8)]


def _piece(rows, x: int, y: int) -> set:
    """The layout's piece at (x, y): the pixels of its fill colour joined side by side to it."""
    colour = rows[y][x]
    if colour is None or colour == ROUTE_OUTLINE:
        raise ValueError(f"dex_map_layout: no piece at {x},{y}")
    piece, todo = {(x, y)}, [(x, y)]
    while todo:
        px, py = todo.pop()
        for nx, ny in ((px + 1, py), (px - 1, py), (px, py + 1), (px, py - 1)):
            if 0 <= nx < 256 and 0 <= ny < len(rows) and (nx, ny) not in piece and rows[ny][nx] == colour:
                piece.add((nx, ny))
                todo.append((nx, ny))
    return piece


def _grow(pixels: set, by: int) -> set:
    return {(x + dx, y + dy) for x, y in pixels for dx in range(-by, by + 1) for dy in range(-by, by + 1)
            if 0 <= x + dx < 256 and 0 <= y + dy < MAP_ROWS * 8}


def layout_fields() -> dict:
    """{field: its fill pixels}: dex_map_layout.FIELDS' pieces, each between its rows."""
    rows = _picture(dex_map_layout)
    out = {}
    for n, pieces in dex_map_layout.FIELDS.items():
        out[n] = set()
        for x, y, first, last in pieces:
            out[n] |= {(px, py) for px, py in _piece(rows, x, y) if first <= py <= last}
    return out


def field_masks() -> dict:
    """{field: the pixels it lights}: its fill pixels and FIELD_GROW around them."""
    return {n: _grow(pixels, FIELD_GROW) for n, pixels in layout_fields().items()}


def layout_page(hidden: int = 0) -> list:
    """The lower screen's 256x168 with OWN_LAYOUT: the map, and the routes over it but the hidden places not in the
    mask: their pieces' fills, and the outline only they had (within OUTLINE_WIDTH of their fills and no other's)."""
    rows = [list(row) for row in _picture(dex_map_bulbapedia)]
    routes = _picture(dex_map_layout)
    if any(c is None for row in rows for c in row):
        raise ValueError("dex_map_bulbapedia: the map has transparent pixels")
    gone = set()
    for bit, seeds in dex_map_layout.HIDDEN.items():
        if not hidden >> bit & 1:
            for x, y in seeds:
                gone |= _piece(routes, x, y)
    if gone:
        fills = {(x, y) for y, row in enumerate(routes) for x, c in enumerate(row)
                 if c is not None and c != ROUTE_OUTLINE and (x, y) not in gone}
        gone |= _grow(gone, OUTLINE_WIDTH) - _grow(fills, OUTLINE_WIDTH)
    for y, row in enumerate(routes):
        for x, c in enumerate(row):
            if c is not None and (x, y) not in gone:
                rows[y][x] = c
    return rows


def mask_bytes(masks: dict) -> bytes:
    """Member FIELD_MASKS: the masks of fields 1 to the last (see the module's notes)."""
    count = max(masks)
    head, body = [0] * (count + 1), b""
    base = 2 * (count + 1)
    for n in range(1, count + 1):
        pixels = masks[n]
        xs, ys = [x for x, _ in pixels], [y for _, y in pixels]
        x0, y0, w, h = min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
        if w > 255 or h > 255:
            raise ValueError(f"field {n}'s mask is {w}x{h}")
        stride = (w + 7) // 8
        bits = bytearray(stride * h)
        for x, y in pixels:
            bits[(y - y0) * stride + (x - x0) // 8] |= 1 << ((x - x0) % 8)
        head[n] = base + len(body)
        body += bytes((x0, y0, w, h)) + bytes(bits)
        body += bytes(len(body) % 2)
    if base + len(body) > 0xFFFF:
        raise ValueError("the fields' masks are over 64 KB")
    return struct.pack(f"<{count + 1}H", *head) + body


def dungeon_bytes(platinum) -> bytes:
    """Member DUNGEON_SPOTS: Platinum's dungeons (zukan_enc_platinum member 0) at dex_map_layout.DUNGEONS' spots."""
    data = platinum.narc(PL_ENCOUNTERS)[PL_DUNGEONS]
    count = len(data) // 4 - 1
    if count != len(dex_map_layout.DUNGEONS):
        raise ValueError(f"Platinum has {count} dungeons, dex_map_layout {len(dex_map_layout.DUNGEONS)}")
    out = bytearray(4)
    for n, (x, y) in enumerate(dex_map_layout.DUNGEONS, 1):
        out += bytes((x, y, data[n * 4 + 2], 0))
    return bytes(out)


# --- OWN_LAYOUT: the time selector in the bottom right (GAME-153, the owner's choice of 2026-10-19) ---
#
# Black 2's selector (zukan_detail_map.c: ACTOR_SEASON's box, cell 1 of archive 157's NCER 30, and its arrows, cells
# 2-3 and 4-5, idle and pressed, all at (128, 96); the time's name in WINDOW_SEASON) covers the map's top left, where
# the owner's layout has places. Here it sits in the bottom right, 96 wide (one of Black 2's three middle pieces),
# mirrored both ways so its edge runs along its top and left and its other sides meet the screen's edges, as Black 2's
# meet the top left: x 160-255, y 144-167, clear of the routes and their highlights (Route 213's sea lights down to
# row 144, the box's top row, which is transparent). Without Black 2's yellow border (the owner's, 2026-10-19: its
# colours 13-15 made transparent in the box's characters, the arrows keeping theirs), its body shows from row 147, and
# the arrows sit 1 pixel and the time's name 2 pixels higher than Black 2's to centre in it (the owner's). The page
# loads its own copies of NCER 30 (SELECTOR_CELLS) and NCGR 16 (SELECTOR_CHARS), since the form page and the touch bar
# use them too, and the box is baked translucent (selector_bake); gen5_dex_map.c moves the window, the name and the
# arrows' touches to match.
SELECTOR_CELLS, SELECTOR_CHARS, SELECTOR_PALETTE = 131, 132, 133
# The box baked translucent over the map (selector_bake): its opacity, and its palette's row: 2 past the season
# palettes' first (OBJ palette 5), so OBJ palette 7, where Black 2's page loads its area sprites' palette, which the
# port's renderer doesn't use (it replaces those sprites); gen5_dex_map.c has that load take SELECTOR_PALETTE. Every
# other OBJ palette the page has is in use (0-4 the cursor and markers, 5-6 the selector, 8-13 the touch bar, 14-15
# the dungeons)
SELECTOR_OPACITY = 0.7
SELECTOR_PALETTE_ROW, SELECTOR_OBJ_PALETTE = 2, 7
SELECTOR_X, SELECTOR_Y, SELECTOR_WIDTH = 160, 144, 96
SELECTOR_PREV_X, SELECTOR_NEXT_X, SELECTOR_ARROW_Y = 166, 236, 151
# The window for the time's name (tiles): between the arrows, over the box; and the name's row in it (Black 2's 1)
SELECTOR_WINDOW = (23, 18, 6, 3)
SELECTOR_TEXT_Y = 7
# The box's border's colours (yellow, and its dark gold at the corner), and the box's characters (names 16-21)
_BORDER_COLOURS = (13, 14, 15)
_BOX_NAMES = range(16, 22)
# Black 2's: the actors' place, the box's cell, the arrows' cells
_SEASON_POS = (128, 96)
_BOX_CELL, _NEXT_CELLS, _PREV_CELLS = 1, (2, 3), (4, 5)
# The box's pieces' characters: the body and its border strip, plain and with the corner
_BODY, _STRIP, _CORNER_BODY, _CORNER_STRIP = 16, 18, 19, 21


def _oam_set(block: bytearray, at: int, x: int, y: int, char: int = None, hflip: bool = None, vflip: bool = None):
    a0, a1, a2 = struct.unpack_from("<HHH", block, at)
    a0 = a0 & 0xFF00 | y & 0xFF
    a1 = a1 & ~0x1FF | x & 0x1FF
    if hflip is not None:
        a1 = a1 & ~0x1000 | (0x1000 if hflip else 0)
    if vflip is not None:
        a1 = a1 & ~0x2000 | (0x2000 if vflip else 0)
    if char is not None:
        a2 = a2 & ~0x3FF | char
    struct.pack_into("<HHH", block, at, a0, a1, a2)


def selector_cells(ncer: bytes) -> bytes:
    """NCER 30 with the selector's box and arrows in the bottom right (see above); its other cells as they are."""
    data = bytearray(ncer)
    start = struct.unpack_from("<H", data, 0xC)[0]
    if bytes(data[start:start + 4]) != b"KBEC":
        raise ValueError("NCER 30: no cell bank where expected")
    base = start + 8
    count, attr, cell_offset = struct.unpack_from("<HHI", data, base)
    if not attr & 1:
        raise ValueError("NCER 30: cells without boxes")
    oams = base + cell_offset + count * 16

    def cell(i):
        n, cell_attr, oam_offset = struct.unpack_from("<HHI", data, base + cell_offset + i * 16)
        return base + cell_offset + i * 16, n, oams + oam_offset

    px, py = _SEASON_POS
    # The box: its corner piece on the left, two plain ones, each body under its strip, all flipped both ways;
    # Black 2's other four OAMs repeat the middle piece
    at, n, first = cell(_BOX_CELL)
    if n != 10:
        raise ValueError(f"NCER 30's box has {n} OAMs, Black 2's 10")
    x0, y0 = SELECTOR_X - px, SELECTOR_Y - py
    pieces = [(x0, _CORNER_STRIP, _CORNER_BODY), (x0 + 32, _STRIP, _BODY), (x0 + 64, _STRIP, _BODY)]
    pieces += [(x0 + 32, _STRIP, _BODY)] * 2
    for k, (x, strip, body) in enumerate(pieces):
        _oam_set(data, first + (2 * k) * 6, x, y0, strip, False, True)
        _oam_set(data, first + (2 * k + 1) * 6, x, y0 + 8, body, False, True)
    # sizes: the strips 32x8 (shape 1, size 1), the bodies 32x16 (shape 1, size 2), as Black 2's
    for k in range(5):
        for j, size in ((0, 1), (1, 2)):
            o = first + (2 * k + j) * 6
            a0, a1 = struct.unpack_from("<HH", data, o)
            struct.pack_into("<HH", data, o, a0 & 0x3FFF | 1 << 14, a1 & 0x3FFF | size << 14)
    cell_attr = struct.unpack_from("<H", data, at + 2)[0]
    struct.pack_into("<H", data, at + 2, cell_attr | 0x300)
    struct.pack_into("<hhhh", data, at + 8, x0 + SELECTOR_WIDTH - 1, y0 + 23, x0, y0)
    # The arrows: their frames moved, as they are
    for cells, x in ((_NEXT_CELLS, SELECTOR_NEXT_X), (_PREV_CELLS, SELECTOR_PREV_X)):
        for i in cells:
            at, n, first = cell(i)
            if n != 1:
                raise ValueError(f"NCER 30's arrow cell {i} has {n} OAMs")
            _oam_set(data, first, x - px, SELECTOR_ARROW_Y - py)
            struct.pack_into("<hhhh", data, at + 8, x - px + 15, SELECTOR_ARROW_Y - py + 15, x - px,
                             SELECTOR_ARROW_Y - py)
    return bytes(data)


def selector_chars(ncgr: bytes) -> bytes:
    """NCGR 16 with the box's border gone: its colours transparent in the box's characters, the rest as it is."""
    data = bytearray(ncgr)
    start = struct.unpack_from("<H", data, 0xC)[0]
    if bytes(data[start:start + 4]) != b"RAHC":
        raise ValueError("NCGR 16: no characters where expected")
    size, offset = struct.unpack_from("<II", data, start + 8 + 0x10)
    first = start + 8 + offset
    for name in _BOX_NAMES:
        for i in range(first + name * 128, first + (name + 1) * 128):
            low, high = data[i] & 15, data[i] >> 4
            low = 0 if low in _BORDER_COLOURS else low
            high = 0 if high in _BORDER_COLOURS else high
            data[i] = high << 4 | low
    return bytes(data)


def _box_pixels(ncer: bytes, ncgr: bytes) -> dict:
    """The box (cell 1 of an NCER) as drawn at its actor's place: {(x, y): palette index}, transparent left out."""
    from platinum_rom import ncer_cells, ncgr_chars
    cells, unit, _ = ncer_cells(ncer)
    chars = ncgr_chars(ncgr)
    out = {}
    for o in cells[_BOX_CELL].oams:
        for y in range(o.height):
            for x in range(o.width):
                tile = o.char * unit + (y // 8 * (o.width // 8) + x // 8) * 32
                b = chars[tile + y % 8 * 4 + x % 8 // 2]
                v = b >> 4 if x & 1 else b & 15
                if v:
                    px = o.width - 1 - x if o.hflip else x
                    py = o.height - 1 - y if o.vflip else y
                    out[(_SEASON_POS[0] + o.x + px, _SEASON_POS[1] + o.y + py)] = v
    return out


def selector_bake(ncer: bytes, ncgr: bytes, nclr: bytes) -> tuple:
    """The box baked translucent (the owner's choice, 2026-10-19): each of its pixels SELECTOR_OPACITY its own colour and
    the rest the map's under it, which never moves (no highlight reaches it), cut to 15 colours. Returns the NCER with
    the box's six pieces on their own characters, unflipped, on palette SELECTOR_PALETTE_ROW; the NCGR with those
    characters added; and an NCLR whose first row is the baked colours."""
    import dex_area_picture
    box = _box_pixels(ncer, ncgr)
    colours = nclr_colours(nclr)
    page_rows = layout_page(0)
    baked = {}
    for (x, y), v in box.items():
        c, m = colours[v], page_rows[y][x]
        baked[(x, y)] = sum(round(SELECTOR_OPACITY * (c >> s & 31) + (1 - SELECTOR_OPACITY) * (m >> s & 31)) << s
                            for s in (0, 5, 10))
    palette = dex_area_picture.median_cut(list(baked.values()), 15)
    own = dict(enumerate(palette, 1))
    index = {p: dex_area_picture.nearest(c, own) for p, c in baked.items()}
    # The characters: per column a strip (32x8, 1 name) then a body (32x16, 2 names), after NCGR 16's last
    data = bytearray(ncgr)
    start = struct.unpack_from("<H", data, 0xC)[0]
    size, offset = struct.unpack_from("<II", data, start + 8 + 0x10)
    first_name = size // 128
    extra = bytearray()
    for k in range(SELECTOR_WIDTH // 32):
        for top, rows in ((SELECTOR_Y, 8), (SELECTOR_Y + 8, 16)):
            for ty in range(rows // 8):
                for tx in range(4):
                    for y in range(8):
                        for x in range(0, 8, 2):
                            px, py = SELECTOR_X + 32 * k + tx * 8 + x, top + ty * 8 + y
                            extra.append(index.get((px, py), 0) | index.get((px + 1, py), 0) << 4)
    data += extra
    struct.pack_into("<I", data, start + 8 + 0x10, size + len(extra))
    struct.pack_into("<I", data, start + 4, struct.unpack_from("<I", data, start + 4)[0] + len(extra))
    struct.pack_into("<I", data, 8, len(data))
    # The box's pieces on them: column k's strip at name first + 3k, its body at first + 3k + 1; the other four OAMs
    # repeat the middle column
    cells = bytearray(ncer)
    cstart = struct.unpack_from("<H", cells, 0xC)[0] + 8
    count, _, cell_offset = struct.unpack_from("<HHI", cells, cstart)
    n, _, oam_offset = struct.unpack_from("<HHI", cells, cstart + cell_offset + _BOX_CELL * 16)
    oams = cstart + cell_offset + count * 16 + oam_offset
    px0, py0 = SELECTOR_X - _SEASON_POS[0], SELECTOR_Y - _SEASON_POS[1]
    for slot, k in enumerate((0, 1, 2, 1, 1)):
        for j, (dy, name) in enumerate(((0, first_name + 3 * k), (8, first_name + 3 * k + 1))):
            at = oams + (2 * slot + j) * 6
            _oam_set(cells, at, px0 + 32 * k, py0 + dy, name, False, False)
            a2 = struct.unpack_from("<H", cells, at + 4)[0]
            struct.pack_into("<H", cells, at + 4, a2 & 0x0FFF | SELECTOR_PALETTE_ROW << 12)
    # The palette: the baked colours as the first row
    pal = bytearray(nclr)
    pstart = struct.unpack_from("<H", pal, 0xC)[0] + 8
    poffset = struct.unpack_from("<I", pal, pstart + 0xC)[0]
    struct.pack_into("<16H", pal, pstart + poffset, 0, *(palette + [0] * (15 - len(palette))))
    return bytes(cells), bytes(data), bytes(pal)


def add_selector(narc) -> None:
    """Archive 157's copy (a nitro.NARC) with the page's own NCER 30, NCGR 16 and the baked box's palette:
    SELECTOR_CELLS, SELECTOR_CHARS and SELECTOR_PALETTE."""
    if len(narc.files) != SELECTOR_CELLS:
        raise ValueError(f"archive 157 has {len(narc.files)} members, the selector's cells go at {SELECTOR_CELLS}")
    ncer, ncgr, nclr = selector_bake(selector_cells(narc.files[30]), selector_chars(narc.files[16]), narc.files[6])
    narc.files += [ncer, ncgr, nclr]


def in_panel(x: int, y: int) -> bool:
    return PANEL_X <= x < PANEL_X + PANEL_WIDTH and PANEL_Y <= y < PANEL_Y + PANEL_HEIGHT


def hidden_pieces_covered(platinum) -> list:
    """The hidden places' pixels (where Platinum's map with one shown differs from it without) that the picture covers
    with its own: none, when the pieces show whole through its transparent pixels."""
    rows = background()
    base = platinum_map(platinum)
    out = []
    for k, name in enumerate(HIDDEN_PLACES):
        shown = platinum_map(platinum, 1 << k)
        covered = [(x, y) for y in range(MAP_ROWS * 8) for x in range(256) if in_panel(x, y) and rows[y][x] is not None
                   and shown[PL_PANEL_Y - PANEL_Y + y][PL_PANEL_X - PANEL_X + x]
                   != base[PL_PANEL_Y - PANEL_Y + y][PL_PANEL_X - PANEL_X + x]]
        out.append((name, covered))
    return out


def fields(platinum) -> list:
    """Platinum's fields (zukan_enc_platinum member 2, the first a dummy): (column, row, columns, rows, cells)."""
    data = platinum.narc(PL_ENCOUNTERS)[PL_FIELDS]
    out = []
    for i in range(len(data) // FIELD_SIZE):
        f = data[i * FIELD_SIZE:(i + 1) * FIELD_SIZE]
        out.append((f[0], f[1], f[2], f[3], bytes(f[4:4 + f[2] * f[3]])))
    return out


def highlight_cells(field_list) -> set:
    """The grid's cells (column, row) a field's highlight can draw in: its own and their eight neighbours."""
    own = set()
    for column, row, columns, rows, cells in field_list[1:]:
        for r in range(rows):
            for c in range(columns):
                if cells[r * columns + c]:
                    own.add((column + c, row + r))
    return {(c + dc, r + dr) for c, r in own for dc in (-1, 0, 1) for dr in (-1, 0, 1)
            if 0 <= c + dc < GRID and 0 <= r + dr < GRID}


def window_cells(field_list) -> list:
    """The 8x8 cells of Black 2's screen the highlight can touch, in raster order: BG2's window."""
    out = set()
    for c, r in highlight_cells(field_list):
        x0, y0 = PL_FIELD_X + OFFSET_X + c * CELL, PL_FIELD_Y + OFFSET_Y + r * CELL
        for y in range(max(0, y0), y0 + CELL):
            for x in range(x0, x0 + CELL):
                if y < MAP_ROWS * 8:
                    out.add((x // 8, y // 8))
    return sorted(out, key=lambda t: (t[1], t[0]))


class TilePool:
    """8-bit characters, each kept once with its flipped copies: add() gives a screen entry."""

    def __init__(self):
        self.tiles = [BLANK]
        self.index = {BLANK: 0}

    @staticmethod
    def flip(tile: bytes, hf: int, vf: int) -> bytes:
        rows = [tile[y * 8:y * 8 + 8] for y in range(8)]
        if vf:
            rows.reverse()
        return b"".join(r[::-1] if hf else r for r in rows)

    def add(self, tile: bytes) -> int:
        if tile in self.index:
            return self.index[tile]
        n = len(self.tiles)
        self.tiles.append(tile)
        for hf in (0, 1):
            for vf in (0, 1):
                self.index.setdefault(self.flip(tile, hf, vf), n | hf << 10 | vf << 11)
        return n


def _cut(rows: list, colours: dict, pool: TilePool) -> list:
    """A 32x32 screen of the picture's tiles (rows under it blank)."""
    screen = [0] * (SCREEN_W * 32)
    for ty in range(MAP_ROWS):
        for tx in range(SCREEN_W):
            tile = bytes(colours[rows[ty * 8 + y][tx * 8 + x]] for y in range(8) for x in range(8))
            screen[ty * SCREEN_W + tx] = pool.add(tile)
    return screen


def _ncgr(template: bytes, tiles: bytes, width: int = 32) -> bytes:
    """An 8-bit NCGR in the template's layout (Black 2's member 7): `width` characters a row, padded to whole rows."""
    count = len(tiles) // 64
    height = -(-count // width)
    tiles += bytes(64 * (height * width - count))
    head = bytearray(template[:0x10])
    rahc = bytearray(template[0x10:0x30])
    struct.pack_into("<HH", rahc, 8, height, width)
    struct.pack_into("<I", rahc, 4, 0x20 + len(tiles))
    struct.pack_into("<I", rahc, 0x18, len(tiles))
    sopc_at = 0x10 + struct.unpack_from("<I", template, 0x14)[0]
    sopc = bytearray(template[sopc_at:sopc_at + 0x10])
    struct.pack_into("<HH", sopc, 12, width, height)
    body = bytes(rahc) + tiles + bytes(sopc)
    struct.pack_into("<I", head, 8, 0x10 + len(body))
    return bytes(head) + body


def _nscr(template: bytes, entries: list) -> bytes:
    """A 256x256 screen in the template's layout (Black 2's member 16)."""
    data = bytearray(template)
    struct.pack_into(f"<{len(entries)}H", data, 0x24, *entries)
    return bytes(data)


def _nclr(template: bytes, colours: list) -> bytes:
    """Black 2's member 0 with palette 0's colours; the other 15 palettes zero."""
    data = bytearray(template)
    raw = bytearray(0x2000)
    struct.pack_into(f"<{len(colours)}H", raw, 0, *colours)
    data[0x28:0x28 + 0x2000] = raw
    return bytes(data)


def build(data: bytes, platinum) -> bytes:
    """Black 2's archive 84 (its bytes) with Sinnoh's map (see the module's notes)."""
    narc = nitro.NARC(data)
    files = narc.files
    assert len(files) == BLACK2_MEMBERS, f"archive 84 has {len(files)} members, Black 2's {BLACK2_MEMBERS}"
    pictures = [page(platinum, mask) for mask in range(HIDDEN_MASKS)]
    # The colours: the pictures', in the order they come, from index 1; then Platinum's highlight row
    order = []
    for rows in pictures:
        for row in rows:
            for c in row:
                if c not in order:
                    order.append(c)
    if len(order) > HIGHLIGHT_BASE - 1:
        raise ValueError(f"the map has {len(order)} colours; at most {HIGHLIGHT_BASE - 1}")
    colours = {c: i + 1 for i, c in enumerate(order)}
    pl_palette = platinum.palette(POKEDEX_ART, PL_PALETTE)
    palette = [0] + order + [0] * (HIGHLIGHT_BASE - 1 - len(order))
    palette += pl_palette[PL_HIGHLIGHT_ROW * 16:PL_HIGHLIGHT_ROW * 16 + 16]
    # BG3: the picture, with each set of the hidden places shown
    pool = TilePool()
    base = _cut(pictures[0], colours, pool)
    hidden = [_cut(rows, colours, pool) for rows in pictures[1:]]
    if len(pool.tiles) > MAP_TILE_LIMIT:
        raise ValueError(f"the map takes {len(pool.tiles)} characters; BG3 has room for {MAP_TILE_LIMIT}")
    # BG2: the highlight's window
    if OWN_LAYOUT:
        masks = field_masks()
        if len(masks) != len(fields(platinum)) - 1:
            raise ValueError(f"dex_map_layout has {len(masks)} fields, Platinum {len(fields(platinum)) - 1}")
        window = sorted({(x // 8, y // 8) for pixels in masks.values() for x, y in pixels}, key=lambda t: (t[1], t[0]))
    else:
        window = window_cells(fields(platinum))
    if len(window) + 1 > WINDOW_TILE_LIMIT:
        raise ValueError(f"the highlight's window takes {len(window) + 1} characters; at most {WINDOW_TILE_LIMIT}")
    window_screen = [0] * (SCREEN_W * 32)
    for n, (tx, ty) in enumerate(window, 1):
        window_screen[ty * SCREEN_W + tx] = n
    files[PALETTE] = _nclr(files[PALETTE], palette)
    files[MAP_CHARS] = _ncgr(files[MAP_CHARS], b"".join(pool.tiles))
    files[MAP_SCREEN] = _nscr(files[MAP_SCREEN], base)
    # all blank, as many as Black 2's (the page loads 0x4000 bytes of them whatever the file has)
    files[WINDOW_CHARS] = _ncgr(files[WINDOW_CHARS], BLANK * WINDOW_TILE_LIMIT)
    files[WINDOW_SCREEN] = _nscr(files[WINDOW_SCREEN], window_screen)
    # The extras
    zukan = platinum.narc(POKEDEX_ART)
    for member in PL_STRIPS:
        strip = _tiles_4bpp(ncgr_chars(unlz(zukan[member])))
        tiles = b"".join(bytes(HIGHLIGHT_BASE + v if v else 0 for v in t) for t in strip)
        files.append(_ncgr(files[MAP_CHARS], tiles))
    for member in (DUNGEON_PALETTE, DUNGEON_CHARS, DUNGEON_CELLS, DUNGEON_ANIMS):
        files.append(bytes(unlz(zukan[PL_DUNGEON[member]])))
    for s in hidden:
        files.append(_nscr(files[MAP_SCREEN], s))
    assert len(files) == HIDDEN_SCREEN_FIRST + HIDDEN_MASKS - 1
    if OWN_LAYOUT:
        files.append(mask_bytes(masks))
        files.append(dungeon_bytes(platinum))
        assert len(files) == DUNGEON_SPOTS + 1
    return narc.save()


def map_screen_member(hidden: int) -> int:
    """The member of BG3's screen with the hidden places in the mask shown."""
    return HIDDEN_SCREEN_FIRST + hidden - 1 if hidden else MAP_SCREEN


# --- reading it back ---

def _8bpp(data: bytes) -> list:
    chars = ncgr_chars(data)
    return [chars[i:i + 64] for i in range(0, len(chars), 64)]


def _draw(rows, tiles, entries, palette, transparent=True):
    for i, e in enumerate(entries):
        tile, hf, vf = tiles[e & 0x3FF], e >> 10 & 1, e >> 11 & 1
        ox, oy = i % SCREEN_W * 8, i // SCREEN_W * 8
        if oy >= len(rows):
            break
        for y in range(8):
            for x in range(8):
                v = tile[(7 - y if vf else y) * 8 + (7 - x if hf else x)]
                if v or not transparent:
                    rows[oy + y][ox + x] = palette[(e >> 12) * 256 + v]


def screens(data: bytes, hidden: int = 0) -> tuple:
    """(BG3's entries with the hidden places in the mask, BG2's), as the game would show them."""
    files = nitro.NARC(data).files
    return nscr_screen(files[map_screen_member(hidden)])[2], nscr_screen(files[WINDOW_SCREEN])[2]


def render(data: bytes, hidden: int = 0, window_pixels=None) -> list:
    """The lower screen (256x192 rows of 15-bit colours, None where nothing is drawn) from an archive 84: BG3, then BG2
    over it. window_pixels, if given, {(x, y): palette index} drawn into BG2's window characters first (as the
    renderer would)."""
    files = nitro.NARC(data).files
    palette = nclr_colours(files[PALETTE])
    rows = [[None] * 256 for _ in range(192)]
    bg3, bg2 = screens(data, hidden)
    _draw(rows, _8bpp(files[MAP_CHARS]), bg3, palette)
    window = [bytearray(t) for t in _8bpp(files[WINDOW_CHARS])]
    for (x, y), v in (window_pixels or {}).items():
        e = bg2[(y // 8) * SCREEN_W + x // 8]
        if e & 0x3FF:
            window[e & 0x3FF][(y % 8) * 8 + x % 8] = v
    _draw(rows, [bytes(t) for t in window], bg2, palette)
    return rows


def to_image(rows, backdrop=0):
    from PIL import Image
    img = Image.new("RGB", (256, len(rows)))
    img.putdata([to_rgb(backdrop if c is None else c) for row in rows for c in row])
    return img


# --- the owner's picture ---

def picture_pixels(path: str) -> list:
    """A picture's pixels in raster order as 15-bit colours, None where it is transparent (alpha 0): only inside the
    map panel, where Platinum's map shows through. Its other pixels must be opaque: no partial alpha."""
    from PIL import Image
    img = Image.open(path)
    if img.size != (256, MAP_ROWS * 8):
        sys.exit(f"{path}: {img.size[0]}x{img.size[1]}, the map is 256x{MAP_ROWS * 8}")
    pixels = []
    for i, (r, g, b, a) in enumerate(img.convert("RGBA").get_flattened_data()):
        x, y = i % 256, i // 256
        if 0 < a < 255:
            sys.exit(f"{path}: a partly transparent pixel at {x},{y}: transparent (alpha 0) or opaque only")
        if a == 0 and not in_panel(x, y):
            sys.exit(f"{path}: a transparent pixel at {x},{y}, outside the map panel")
        pixels.append(None if a == 0 else (r >> 3) | (g >> 3) << 5 | (b >> 3) << 10)
    if None not in pixels:
        sys.exit(f"{path}: no transparent pixel, so no window onto Platinum's map")
    return pixels


def pack(path: str, out: str):
    """The owner's picture into dex_map_background.py: its colours and, as runs, its pixels, the transparent ones as
    TRANSPARENT. Nothing of Platinum's is kept: the transparent pixels hold no colour."""
    pixels = picture_pixels(path)
    palette = []
    for c in pixels:
        if c is not None and c not in palette:
            palette.append(c)
    runs = []
    for c in pixels:
        i = TRANSPARENT if c is None else palette.index(c)
        if runs and runs[-1][0] == i:
            runs[-1][1] += 1
        else:
            runs.append([i, 1])
    # The module's notes kept, read before it's rewritten (out is usually the module itself)
    text = open(dex_map_background.__file__, encoding="utf-8").read()
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(text[:text.index("# The visible map area")])
        f.write("# The visible map area above the touch bar\nWIDTH, HEIGHT = 256, %d\n" % (MAP_ROWS * 8))
        f.write("# Its colours, 15-bit (BGR555, as the DS's palettes)\nPALETTE = [%s]\n"
                % ", ".join("0x%04X" % c for c in palette))
        f.write("# Its pixels in raster order, as runs of (index into PALETTE, length); index %d is transparent, where\n"
                "# Platinum's map shows (dex_map_art.page)\nRUNS = [\n" % TRANSPARENT)
        for k in range(0, len(runs), 8):
            f.write("    " + " ".join("(%d, %d)," % tuple(r) for r in runs[k:k + 8]) + "\n")
        f.write("]\n")
    print(f"{len(palette)} colours, {len(runs)} runs, {pixels.count(None)} pixels transparent")


def _write_picture(module, pixels: list, note: str):
    """A module's picture rewritten (its colours in the order they come, its pixels as runs), the module's text up to
    its picture kept."""
    palette = []
    for c in pixels:
        if c is not None and c not in palette:
            palette.append(c)
    runs = []
    for c in pixels:
        i = TRANSPARENT if c is None else palette.index(c)
        if runs and runs[-1][0] == i:
            runs[-1][1] += 1
        else:
            runs.append([i, 1])
    text = open(module.__file__, encoding="utf-8").read()
    with open(module.__file__, "w", encoding="utf-8", newline="\n") as f:
        f.write(text[:text.index("# The picture's size")])
        f.write("# The picture's size\nWIDTH, HEIGHT = 256, %d\n" % (MAP_ROWS * 8))
        f.write("# Its colours, 15-bit (BGR555, as the DS's palettes)\nPALETTE = [\n")
        for k in range(0, len(palette), 12):
            f.write("    " + " ".join("0x%04X," % c for c in palette[k:k + 12]) + "\n")
        f.write("]\n# Its pixels in raster order, as runs of (index into PALETTE, length)%s\nRUNS = [\n" % note)
        for k in range(0, len(runs), 8):
            f.write("    " + " ".join("(%d, %d)," % tuple(r) for r in runs[k:k + 8]) + "\n")
        f.write("]\n")
    print(f"{module.__name__}: {len(palette)} colours, {len(runs)} runs")


def _picture_file(path: str, transparent: bool) -> list:
    """A 256x168 picture's pixels as 15-bit colours, None where transparent (alpha under 128) if allowed."""
    from PIL import Image
    img = Image.open(path).convert("RGBA")
    if img.size != (256, MAP_ROWS * 8):
        sys.exit(f"{path}: {img.size[0]}x{img.size[1]}, the map is 256x{MAP_ROWS * 8}")
    pixels = []
    for i, (r, g, b, a) in enumerate(img.get_flattened_data()):
        if a < 128:
            if not transparent:
                sys.exit(f"{path}: a transparent pixel at {i % 256},{i // 256}: the map is opaque")
            pixels.append(None)
        else:
            pixels.append((r >> 3) | (g >> 3) << 5 | (b >> 3) << 10)
    return pixels


def pack_map(path: str):
    pixels = _picture_file(path, False)
    if len(set(pixels)) > MAP_COLOURS:
        sys.exit(f"{path}: {len(set(pixels))} colours, at most {MAP_COLOURS}")
    _write_picture(dex_map_bulbapedia, pixels, "")


def pack_layout(path: str):
    _write_picture(dex_map_layout, _picture_file(path, True), "; index %d is transparent (the map shows)"
                   % TRANSPARENT)


def unpack(out: str):
    """The picture back, RGBA, transparent where Platinum's map shows."""
    from PIL import Image
    img = Image.new("RGBA", (dex_map_background.WIDTH, dex_map_background.HEIGHT))
    img.putdata([(0, 0, 0, 0) if c is None else to_rgb(c) + (255,) for row in background() for c in row])
    img.save(out)


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "pack":
        pack(sys.argv[2], dex_map_background.__file__)
    elif len(sys.argv) >= 3 and sys.argv[1] == "unpack":
        unpack(sys.argv[2])
    elif len(sys.argv) >= 3 and sys.argv[1] == "pack-map":
        pack_map(sys.argv[2])
    elif len(sys.argv) >= 3 and sys.argv[1] == "pack-layout":
        pack_layout(sys.argv[2])
    elif len(sys.argv) >= 4 and sys.argv[1] == "render":
        hidden = int(sys.argv[4], 0) if len(sys.argv) > 4 else 0
        to_image(render(open(sys.argv[2], "rb").read(), hidden)).save(sys.argv[3])
    else:
        sys.exit(__doc__)
