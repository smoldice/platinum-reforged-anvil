"""Black 2's Pokédex art (archive 157) in Black 2's own colours, solid, with a few light backgrounds the owner chose:
platinum_copy() makes the copy the game opens (ptui/a/1/5/7, gen5_runtime.c), which the registration after a catch
(gen5_pokedex.c) shows, and Black 2's whole Pokédex (gen5_dex.c, GAME-125).

History: GAME-101 (2026-10-18) restyled the registration's entry, GAME-125 (2026-10-19) every page with it, in Reforged's
colours: Platinum's battle buttons' red for Black 2's reds, the POKéDEX icon's green for its golds, then silver. The
owner put Black 2's own colours back the same day (2026-10-19), keeping what removed a pattern and a few light
backgrounds. So this file makes three kinds of change, each in a section of its own below and a table of its own in
the code:

1. Shape changes (SHAPES): grids, dotted meshes, chevrons and stripes made solid. Each is a tile change (a pattern's
   lines are an index of their own, which the tile remaps to its base's index), never a colour change, so each solid
   fill is the colour the pattern's base has in Black 2's palette.
2. Kept exceptions (the owner's, 2026-10-19): the light backgrounds and the balls listed below, the only colour
   changes left. Some are tile changes to a light index, some copy a light colour into a palette entry.
3. Colour changes: none. Every palette entry is Black 2's, but for the kept exceptions'. A later colour pass (GAME-145)
   starts here: the reds were palette 0's index 1 of files 9 (the entry), 49, 51 (the list), 75, 76 (the search), 1,
   2 (the detail pages), palette 4's index 2 and 4 (INFO's slashes) and 0x68's row 4 (the boy's cover); the golds are
   listed in the history of this file (GAME-125's GOLDS table, git log).

Code keeps its part of the entry: the description's dark letters on the light box (gen5_pokedex.c's print shim,
gen5_dex.c's Gen5Dex_EntryPrint).

## Shape changes: solid, in Black 2's colours

The registration's entry (pokebw2 ov296 zukan_info.c: palette 9, characters 0x1a, maps 0x20 behind and 0x29 in
front), which the Pokédex's info page shows too:
- The background's grid: the map behind fills the screen with tile 5, the red (index 1 of palette 0) with the grid's
  darker lines (3) along its right and bottom edges, which take the red. Index 3 also outlines the panels in front,
  so the tile changes, not the colour. The dark line where the red meets the gray band (tile 0x2b) stays.
- The grid behind the type tags: the info panel's body (4) has a grid of light squares (5) from the category down to
  the height (tiles 0x54 to 0x56, 0x5a and 0x65, and the right three columns of 0x59, 0x5d and 0x5f, whose left ones
  are the footprint box's edge), which take the body's 4. The footprint box keeps its own grid, and the name's row and
  the height's and weight's bars their 5.

The pages (GAME-125). The list (ov299 zknlist_main.c ZknListMain_LoadGraphics): the lower screen's background is
characters 58 in palette 49 (map 64, BG3), the upper screen's characters 59 in palette 51 (map 65, BG7, and the header
and count bar, map 71, BG5); the rows are characters 60 in palette 49's palette 1, the selected row's in its palettes 2
and 3 (the cursor blinks between them), and the list's sprites are in palette 53. The habitat list (ov303
zukan_habitat_graphic.c) and the area list (ov304 zukan_area_list_view.c, GAME-137) load the same characters and
palettes, so they follow: their lower screen is characters 58 in map 115 (BG3), the list's background drawn in palette
49's palette 4 (palette 0 with orange for the red); the area list's upper screen characters 59 in maps 127 (BG5, the
header) and 116 (BG7, the background, palette 51's 9: palette 0 with orange), its rows characters 60 and 61 (maps 117
to 126, no pattern); the habitat list's upper screen the header (map 129) over Sinnoh's map (dex_map_art.py), its lower
screen's message box and grid of cells (map 128, palettes 9 to 11, 50's for water and fishing) without a pattern. The
search (ov300 zknsearch_main.c): the
lower screen's background is characters 81 in palette 75 (map 97) under the rows' strips and the buttons' frame
(characters 83, map 94, palette 75's palette 5), the upper screen's characters 82 in palette 76 (map 98). The detail
pages (ov298 zukan_detail_common.c sBackgroundFiles): the upper screen's characters 12 in palette 2 (map 37, also
behind the info page's entry), the lower screen's characters 11 in palette 1 (map 42; 33, with a band, on the forms
page), each page in its own palette of them (0 the info page's red, 2 the cry page's purple, 3 the area page's orange,
4 the forms page's blue). The area page's upper screen (GAME-137) is map 37 in the orange, so its grid goes with the
others' and it's solid orange; the place panel that slides over it (ZukanDetailMap_LoadPanelBG: characters 12, map
39, palette 2's palettes 0 to 7) keeps Black 2's golds.
- The red grids (BACKGROUNDS): the grid tile of each background (the red, 1, with the lines, 3, along two edges, the
  map flipping it) and the grid's last lines where the red meets a dark line, whose line stays: 58's tile 2 and 11's
  tile 2 (the right column below it), 59's, 82's tile 3 and 12's tile 0x25 (the top row and right column above it),
  81's tile 4 (below). The tiles: 58's, 59's, 81's, 82's and 11's 1, 12's 2.
- The dark bars' tiled squares (BACKGROUNDS "dark": the lines' index takes the squares'): above the list's band (58's
  0x1b, palette 1: 1 in 2), the list's upper screen's top and bottom (59's 2: 11 in 12), the search's (81's 3: 10 in
  12; 82's 2: 11 in 12), the detail pages' (12's 0x26, palette 1: 1 in 5; 11's 0x1b: 11 in 10).
- The search's band behind its rows (81's tiles 5 to 0x1c): its dotted mesh and chevrons (4, 5, 7) take its dark
  base (8, Black 2's #383838): one flat dark colour.
- The search's choice rows' stripes (characters 83, tiles 0x4a to 0x55, maps 99 and 100, palette 75's palette 1): 7
  takes the body's 1.

## Kept exceptions (the owner's, 2026-10-19)

- The light band behind the Pokémon in the entry (GAME-101): the gray band (7) in the info panel's light gray (4): the
  band behind (tiles 0x2b and 0x2c), its sloped ends in front (0x11 to 0x18) and where it shows past the footprint box
  and the panel (0x5e, 0x66 to 0x69, 0x6e). The ends' dark edges and the shadow under the footprint box stay, as does
  the ring of the panel's dot beside the number (0x48), the one other use of 7 there.
- The light ruler ticks on that band (GAME-101, the owner's, 2026-10-19): its ticks along its top and bottom edges
  (tile 0x2b, flipped for the bottom) and its left side (0x11, 0x15, 0x1a to 0x1c, 0x2f, in front) in the footprint
  box's grid lines' light gray (5), where Black 2's are a dark gray (8). LIGHT_RULERS, on by default; off gives Black
  2's dark ticks on the light band.
- The light description box in the entry (GAME-101): tiles 0x25 to 0x2a's dark gray (10) the info panel's light gray
  (4), with its dark letters (code, above). Index 10 also shades the footprint box's tab, which keeps it.
- The entry's small Poké Ball beside the number (zukan_info.c ZukanInfo_InitLabelWindows) in the list rows' balls' red,
  Black 2's own list-ball red (GAME-125, the owner's): its red (palette 0's 2) and shade (13) take palette 49's palette
  1's 12 and 13. Only the ball uses 2 and 13 in palette 0, so the indices change, not the tiles.
- The light bands where Black 2 has gray chevrons, in the entry's band's light gray (palette 9's 4, copied): behind
  the selected Pokémon on the list (58's tiles 3 to 0x1a: the chevrons and meshes, 4, 7 and 8, become 5, palette 49's
  palette 0, which takes the light gray) and the forms page's band (11's tiles 3 to 0x1a: 5, 6 and 8 become 7, palette
  1's palette 4, which takes it). The area list's band behind the selected area, and the same band beside the habitat
  list's grid of cells, are the list's tiles in palette 49's palette 4 (map 115), whose 5 takes the light gray too
  (LIGHT_BAND_PALETTES, GAME-137; only those tiles use 5 there).
- The white bottom of the list's Poké Ball icons (characters 60, tiles 1, 2, 0xb, 0xc): the gray (11) white and its
  shade (10) as much lighter, in palette 49's palettes 1 to 3 (the rows' and the selected row's). Only the ball's tiles
  use 10 and 11 there.
- Untouched, as before: the cry plot's dotted rows, columns and centre line (characters 11, map 43), the cover's
  ringed screen and both covers (ov301 zukan_open.c, palettes 0x68 and 0x69), the registration's cover (palette 7).

Gen5_archives.platinum_copy runs it, and Anvil on the player's ROM (MIT: no ndspy).
"""
import struct

import nitro

import platinum_ui

ARCHIVE = 157

# The entry: its palette and characters, palette 0's indices (the red, the grid's lines, the panel's light gray and
# its grid's squares, the band's gray, the rulers' ticks, the description box's dark gray)
PALETTE, CHARS = 9, 0x1A
RED, GRID_LINE, PANEL_LIGHT, PANEL_GRID, BAND_GRAY, RULER_TICK, DESCRIPTION_GRAY = 1, 3, 4, 5, 7, 8, 10
# The pages' palettes and characters: the list's, lower screen and upper, the search's and its choice rows', the
# detail pages'
LIST_PALETTE, LIST_CHARS, LIST_TOP_CHARS = 49, 58, 59
SEARCH_CHARS, SEARCH_TOP_CHARS, SEARCH_ROW_CHARS = 81, 82, 83
DETAIL_PALETTE, DETAIL_CHARS, DETAIL_TOP_CHARS = 1, 11, 12
# The forms page's palette in the detail pages' palette 1
FORMS = 4

# --- Shape changes: (tiles, the pattern's index, the base's index it takes) ---

# The entry: its background's grid, the grid behind the type tags (and beside the footprint box, the columns from 5)
ENTRY_GRID_TILES = (0x05,)
PANEL_GRID_TILES = (0x54, 0x55, 0x56, 0x5A, 0x65)
PANEL_GRID_EDGE_TILES, PANEL_EDGE_COLUMN = (0x59, 0x5D, 0x5F), 5
# Each page background's red grid tile, its edge tile toward a dark line (below it: the right column takes its row's
# colour, rows 1 to 7; above it: the grid's lines, rows 0 to 6) and its dark bar's tile (the lines' index, the
# squares')
BACKGROUNDS = {
    LIST_CHARS: {"grid": 0x01, "below": 0x02, "dark": (0x1B, 1, 2)},
    LIST_TOP_CHARS: {"grid": 0x01, "above": 0x03, "dark": (0x02, 11, 12)},
    SEARCH_CHARS: {"grid": 0x01, "below": 0x04, "dark": (0x03, 10, 12)},
    SEARCH_TOP_CHARS: {"grid": 0x01, "above": 0x03, "dark": (0x02, 11, 12)},
    DETAIL_CHARS: {"grid": 0x01, "below": 0x02, "dark": (0x1B, 11, 10)},
    DETAIL_TOP_CHARS: {"grid": 0x02, "above": 0x25, "dark": (0x26, 1, 5)},
}
# The search's band: its tiles, its mesh's and chevrons' grays and its dark base (Black 2's #383838)
SEARCH_BAND_TILES, SEARCH_BAND_GRAYS, SEARCH_BAND = range(0x05, 0x1D), (4, 5, 7), 8
# The search's choice rows: their tiles, their stripes' index and the body's
SEARCH_ROW_TILES, SEARCH_ROW_STRIPE, SEARCH_ROW_BODY = range(0x4A, 0x56), 7, 1

# --- Kept exceptions (the owner's, 2026-10-19) ---

# The entry's light band behind the Pokémon and its light description box: tiles whose gray takes the panel's light 4
ENTRY_BAND_TILES = (0x11, 0x12, 0x13, 0x15, 0x16, 0x17, 0x18, 0x2B, 0x2C, 0x5E, 0x66, 0x67, 0x68, 0x69, 0x6E)
DESCRIPTION_TILES = (0x25, 0x26, 0x27, 0x28, 0x29, 0x2A)
# The band's light ruler ticks (GAME-101, kept 2026-10-19): 8 in the footprint grid's light 5 (False: Black 2's dark
# ticks)
LIGHT_RULERS = True
RULER_TILES = (0x11, 0x15, 0x1A, 0x1B, 0x1C, 0x2B, 0x2F)
# The entry's small Poké Ball's red and shade, and the list rows' balls' (palette 49) they take
ENTRY_BALL = {(0, 2): (1, 12), (0, 13): (1, 13)}
# The light bands where Black 2 has gray chevrons: (file, palette, index) that takes the entry's band's colour (palette
# 9's light gray), and the characters, tiles and grays that become that index
ENTRY_BAND_COLOUR = (PALETTE, 0, PANEL_LIGHT)
LIGHT_BANDS = {
    LIST_CHARS: ((LIST_PALETTE, 0, 5), range(0x03, 0x1B), (4, 7, 8)),
    DETAIL_CHARS: ((DETAIL_PALETTE, FORMS, 7), range(0x03, 0x1B), (5, 6, 8)),
}
# The same bands drawn in other palettes of their file, which take the light gray at the same index: the area list's
# and the habitat list's lower screen (map 115) draw the list's band in palette 49's palette 4 (GAME-137)
AREA_LIST = 4
LIGHT_BAND_PALETTES = {LIST_CHARS: (AREA_LIST,)}
# The list rows' Poké Ball: its gray bottom and its shade, white and as much lighter, in the rows' palettes
BALL_GRAY, BALL_SHADE, BALL_PALETTES, WHITE = 11, 10, (1, 2, 3), 0xF8


def swap(tiles, numbers, old, new, columns=range(8), rows=range(8)):
    for t in numbers:
        for y in rows:
            for x in columns:
                if tiles.get(t, x, y) == old:
                    tiles.set(t, x, y, new)


def entry_background(d):
    """The entry's characters: its grids solid (shape), its band and description box light (kept)."""
    tiles = platinum_ui.Tiles(d)
    swap(tiles, ENTRY_GRID_TILES, GRID_LINE, RED)
    swap(tiles, PANEL_GRID_TILES, PANEL_GRID, PANEL_LIGHT)
    swap(tiles, PANEL_GRID_EDGE_TILES, PANEL_GRID, PANEL_LIGHT, range(PANEL_EDGE_COLUMN, 8))
    if LIGHT_RULERS:
        swap(tiles, RULER_TILES, RULER_TICK, PANEL_GRID)
    swap(tiles, ENTRY_BAND_TILES, BAND_GRAY, PANEL_LIGHT)
    swap(tiles, DESCRIPTION_TILES, DESCRIPTION_GRAY, PANEL_LIGHT)


def page_background(chars):
    """A page's background: its red grid and dark bar solid, the search's band flat (shape); the list's and the forms
    page's bands one light index (kept)."""
    def change(d):
        tiles = platinum_ui.Tiles(d)
        background = BACKGROUNDS[chars]
        swap(tiles, (background["grid"],), GRID_LINE, RED)
        if "below" in background:
            for y in range(1, 8):
                tiles.set(background["below"], 7, y, tiles.get(background["below"], 6, y))
        if "above" in background:
            swap(tiles, (background["above"],), GRID_LINE, RED, rows=range(0, 7))
        tile, line, square = background["dark"]
        swap(tiles, (tile,), line, square)
        if chars == SEARCH_CHARS:
            for gray in SEARCH_BAND_GRAYS:
                swap(tiles, SEARCH_BAND_TILES, gray, SEARCH_BAND)
        if chars in LIGHT_BANDS:
            (_, _, band), band_tiles, grays = LIGHT_BANDS[chars]
            for gray in grays:
                swap(tiles, band_tiles, gray, band)
    return change


def search_rows(d):
    """The search's choice rows without their stripes."""
    swap(platinum_ui.Tiles(d), SEARCH_ROW_TILES, SEARCH_ROW_STRIPE, SEARCH_ROW_BODY)


def palette_base(d) -> int:
    t = platinum_ui.blocks(d)[b"TTLP"]
    return t + 8 + struct.unpack_from("<I", d, t + 0x14)[0]


def read_colour(data: bytes, palette: int, index: int) -> int:
    """A 15-bit colour of a palette file."""
    d = platinum_ui.mts.unlz(data) if data[0] in (0x10, 0x11) else data
    return struct.unpack_from("<H", d, palette_base(d) + palette * 32 + index * 2)[0]


def channels(colour: int):
    return tuple((colour >> shift & 31) << 3 for shift in (0, 5, 10))


def pack(r, g, b) -> int:
    return min(round(r) >> 3, 31) | min(round(g) >> 3, 31) << 5 | min(round(b) >> 3, 31) << 10


def white_of(colour: int, gray: int) -> int:
    """White for a gray, and a shade of it as much lighter."""
    factor = WHITE / max(channels(gray))
    return pack(*(min(WHITE, c * factor) for c in channels(colour)))


def set_colours(colours: dict):
    """A change that writes 15-bit colours: {(palette, index): colour}."""
    def change(d):
        base = palette_base(d)
        for (palette, index), colour in colours.items():
            struct.pack_into("<H", d, base + palette * 32 + index * 2, colour)
    return change


def kept_colours(original: list) -> dict:
    """The kept exceptions' colours, {file: {(palette, index): colour}}, read from Black 2's own: the entry's ball in
    the list balls' red, the list balls' white bottom, the light bands in the entry's band's light gray."""
    kept = {}
    for (palette, index), (lpalette, lindex) in ENTRY_BALL.items():
        kept.setdefault(PALETTE, {})[palette, index] = read_colour(original[LIST_PALETTE], lpalette, lindex)
    for palette in BALL_PALETTES:
        gray = read_colour(original[LIST_PALETTE], palette, BALL_GRAY)
        for index in (BALL_GRAY, BALL_SHADE):
            kept.setdefault(LIST_PALETTE, {})[palette, index] = white_of(
                read_colour(original[LIST_PALETTE], palette, index), gray)
    light = read_colour(original[ENTRY_BAND_COLOUR[0]], *ENTRY_BAND_COLOUR[1:])
    for chars, ((fid, palette, index), _, _) in LIGHT_BANDS.items():
        for band_palette in (palette, *LIGHT_BAND_PALETTES.get(chars, ())):
            kept.setdefault(fid, {})[band_palette, index] = light
    return kept


def platinum_copy(data: bytes) -> bytes:
    """The copy of Black 2's archive 157 the game opens: Black 2's colours, solid, with the kept exceptions."""
    narc = nitro.NARC(data)
    original = list(narc.files)
    for fid, colours in kept_colours(original).items():
        narc.files[fid] = platinum_ui.edit(narc.files[fid], set_colours(colours))
    narc.files[CHARS] = platinum_ui.edit(narc.files[CHARS], entry_background)
    for fid in BACKGROUNDS:
        narc.files[fid] = platinum_ui.edit(narc.files[fid], page_background(fid))
    narc.files[SEARCH_ROW_CHARS] = platinum_ui.edit(narc.files[SEARCH_ROW_CHARS], search_rows)
    return narc.save()
