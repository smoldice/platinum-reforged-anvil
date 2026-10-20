#!/usr/bin/env python3
"""The battle's Touch Screen menus with Platinum's own art (the user's, 2026-10-11; always since GAME-141,
2026-10-18): copies of the archives Black 2's lower screen loads from (11: the command, move, target, yes/no and
message screens; 49: the status bar; 98: the bag; 99: the party list) whose maps, characters and palettes show
Platinum's art where Black 2's was. Black 2's code stays: what each button does, the touch areas, and its transitions,
which now move Platinum's pieces. gen5_runtime.c points Black 2's archive paths at these copies (ptui/a/0/1/1 …);
gen5_battle.c and gen5_runtime.c patch what data can't change (the dimming of the background, where the party balls
go, which text is dark).

How Black 2 draws its lower screen (pokebw2 src/ov168/btlv_input.c; the sub screen's BGs as GFL numbers them):
- BG 5 (sub BG1), the large area: maps 0x174-0x17b, 512x512, a screen to each quarter: top left the command screen's
  (FIGHT's octagon), the others transitions' and the move and target screens' tiles, bottom right.
- BG 4 (sub BG0), the buttons: maps 0x169-0x173 (the command screen's, by rule and mode: BAG, RUN, POKéMON, or the
  back button, SHIFT, LAUNCHER) and 0x23b, along the bottom of the top left quarter; the move screen's back button
  at the bottom right of the top right one; the target screen's highlight frames (384-419, by rule and range).
- Both on characters 0x166 (1024 tiles, 4 bits a pixel) and palettes 0x168 (rows 0 and 1 the large area's two parts,
  2, 3 and 4 BAG, POKéMON and RUN, 9 to 12 the move tiles, loaded by type from 464-480).
- BG 7 (sub BG3), the ball shown between screens and behind the messages (0x17d, 0x17e); BG 6 (sub BG2), the text
  Black 2 prints and its status bar.
The command screen at rest shows the top left quarters of 0x174 and its BG 4 map (probed in melonDS).

Platinum's lower screen (src/battle/battle_subscreen.c; res/prebuilt/battle/graphic/pl_batt_bg.narc): characters 28,
palettes 242, its row 0 from the battle location's (0xf3 onwards: 0xf5 the towns' mint), and a map a layer: the
background 0x31 (row 0; its panels, 0x30, are the key cursor's highlight), the command screen's buttons 0x2a (rows 1
to 4: FIGHT, BAG, POKéMON, RUN), the move screen's 0x2b (8 to 11 by type, 4 CANCEL), the target screen's 0x2c, the
yes/no screen's 0x2d. Its labels are text it prints, in FONT_SUBSCREEN; here they're drawn into the buttons.

The copy of 11 rebuilds the characters from the cells every lower-screen map shows: BG 5's background cells (rows 0
and 1, or empty) become Platinum's background, BG 4's command buttons Platinum's, labelled, the move, target and
yes/no screens' panels Platinum's, fitted to Black 2's; BG 7's ball the background, enlarged. Palette rows 0 to 4
become Platinum's background, FIGHT, BAG, POKéMON and RUN. The lower screen sets (lower_screen_sets.py: Safari, Pal
Park, the Frontier) get the same, with their words. The bag and the party list follow (their sections below).

Built from the archives as extraction leaves them, with Platinum's art read from its ROM (platinum_rom.py; the
paths below are the decomp's files that art is in). Never committed.

Usage (from extract_assets.py and Anvil): build(arc, data, platinum), platinum a PlatinumRom, returns the copy of an
archive in ARCHIVES.
"""
import struct
from collections import Counter

import nitro

import lower_screen_sets
import make_trainer_sprites as mts
import mystery_type
from platinum_rom import BATTLE_SPRITES, FONT_SUBSCREEN, INTERFACE_PALETTE, PlatinumRom

ARCHIVES = (11, 49, 98, 99)
# Where the copies go, in gen5/files and in the ROM
PREFIX = "ptui"

# Black 2's status bar along the top of the lower screen (system/infowin.c: the clock and battery, archive 49, which
# only it loads; its characters are member 1): Platinum's screen has none (the user's), so they're left blank
INFOWIN, INFOWIN_CHARS = 49, 1

PT_ART = "battle/graphic/pl_batt_bg.narc"  # res/prebuilt/battle/graphic/pl_batt_bg.narc
PT_CHARS, PT_PALETTES, PT_LOCATION = 28, 242, 0xF5
PT_BACKGROUND, PT_COMMAND, PT_MOVES = 0x31, 0x2A, 0x2B
# Platinum's move tiles' palettes by type, and for no move (src/overlay011/move_palettes.c)
PT_TYPES = ["Normal", "Fighting", "Flying", "Poison", "Ground", "Rock", "Bug", "Ghost", "Steel", "Fire", "Water",
            "Grass", "Electric", "Psychic", "Ice", "Dragon", "Dark"]
# The buttons' labels in Platinum's colours (battle_subscreen.c: TEXT_COLOR(1, 2, 3) on FIGHT, (4, 5, 6) on BAG,
# (7, 8, 9) on POKéMON, (10, 11, 12) on RUN and CANCEL, row 2 of res/graphics/battle/interface/shared.pal): a glyph's
# body (1) white, its inner edge (2) a light shade and its outline (3), on its top and left, a dark one of the button's
# colour. The two shades go into each button's palette row (1 to 4) at LABEL_LIGHT and LABEL_DARK, which no art of
# Platinum's uses there; the labels used to draw the inner edge in the row's dark grey (10) and no outline, thin next
# to Platinum's (the user's)
PT_LABEL_PALETTE_ROW = 2
LABEL_FIRST_COLOUR = {1: 1, 2: 4, 3: 7, 4: 10}
WHITE, LABEL_LIGHT, LABEL_DARK = 1, 11, 12

B2_CHARS, B2_PALETTES = 0x166, 0x168
BG4_COMMAND_MAPS = (0x169, 0x16A, 0x16B, 0x16C, 0x16D, 0x16F, 0x170, 0x171, 0x172, 0x173)
# The target screen's highlight frames (384-419, by rule and range) load onto BG 4, over the panels
BG4_MAPS = BG4_COMMAND_MAPS + (0x16E, 0x23B) + tuple(range(384, 420))
BG5_MAPS = tuple(range(0x174, 0x17D))
# The command buttons' places on BG 4's top left quarter: the columns of each slot, the rows of the buttons
SLOTS = {"BAG": range(0, 11), "RUN": range(11, 22), "POKéMON": range(22, 32)}
BUTTON_ROWS = range(17, 24)
FIGHT_ROWS = range(3, 17)
# Which slots hold the usual button in each command map; the others hold Black 2's back button (BACK_IN_RUN), SHIFT
# or LAUNCHER, which Platinum's battles don't have and keep their art
USUAL = {
    0x169: ("BAG", "RUN", "POKéMON"), 0x16A: ("BAG", "RUN"), 0x16B: ("RUN",), 0x16C: ("BAG", "POKéMON"),
    0x16D: ("BAG",), 0x16F: ("BAG", "RUN"), 0x170: ("BAG", "RUN", "POKéMON"), 0x171: ("RUN", "POKéMON"),
    0x172: ("POKéMON",), 0x173: (),
}
# The maps with Black 2's back button in RUN's place (a double battle's second Pokémon's, and the Wonder Launcher's):
# Platinum's RUN button there, labelled CANCEL, as Platinum has it
BACK_IN_RUN = (0x16C, 0x16D, 0x172, 0x173)
# Black 2's palette rows of the large area's two parts, and of Platinum's background, FIGHT, BAG, POKéMON and RUN,
# which take them over
B2_AREA_ROWS = (0, 1)
PT_ROWS = (0, 1, 2, 3, 4)
# Where Platinum centres each label (battle_subscreen.c: BattleSubscreen_NewFontOAM)
LABEL_CENTRES = {"FIGHT": (128, 84), "BAG": (40, 170), "POKéMON": (216, 170), "RUN": (128, 178)}

# The move and target screens: BG 5's right half is shown 24 rows down (scroll 256, 192). Each of their panels is
# on a palette row of its own, which Black 2 loads at run time; it takes the Platinum panel on the given row of a
# Platinum map, fitted to its cells (its body's middle rows and columns dropped or repeated). By BG 5 map: the move
# tiles (rows 9 to 12, by slot; Platinum's 0x2b, 8 to 11), the targets (7 and 8 the opponents, 9 and 10 the
# partners; Platinum's 0x2c, orange and grey). A third number is the row the panel goes on, if not Black 2's
RIGHT_HALF_ROWS = 24
# BG 5's quarters each show the background the same way up, a screen's rows apart: Black 2 scrolls it a quarter at a
# time between screens (btlv_input.c BtlvInput_StartFieldFrames), and Platinum's background stays still
SCREEN_ROWS = 24
PT_TARGETS, PT_YES_NO = 0x2C, 0x2D
MOVE_PANELS = {9: (PT_MOVES, 8), 10: (PT_MOVES, 9), 11: (PT_MOVES, 10), 12: (PT_MOVES, 11)}
PANELS = {0x174: MOVE_PANELS, 0x17B: MOVE_PANELS,
          0x175: {7: (PT_TARGETS, 5), 8: (PT_TARGETS, 12), 9: (PT_TARGETS, 6), 10: (PT_TARGETS, 13)},
          # the yes/no screen's two bars (rows 2 and 3, BAG's and POKéMON's): Platinum's red and blue (0x2d), on
          # FIGHT's and RUN's rows, which don't change
          0x177: {2: (PT_YES_NO, 1, 1), 3: (PT_YES_NO, 4, 4)}}
# The move tiles' palettes, loaded by type (Black 2's order, without Platinum's ???) from these files, and for no
# move from NO_MOVE; the target panels' (481 the opponents', 482 the partners'), Platinum's rows of them. Platinum's
# ???, the battle's type 17, has the file mystery_type.py adds after the lower screen sets (MYSTERY_TILE), which the
# move screen loads whichever set the battle has
B2_TYPE_PALETTES = (464, 470, 473, 471, 472, 476, 475, 477, 479, 465, 466, 468, 467, 469, 478, 474, 480)
MYSTERY_TILE = mystery_type.TILE_PALETTE_MEMBER
NO_MOVE_PALETTES = (463,)
TARGET_PALETTES = {481: 5, 482: 6}
# The opponents' panels' rows, which hold 0x168's own colours for the frames before Black 2 loads 481 into them
OPPONENT_PANEL_ROWS = (7, 8)
# The target highlight frames' green (palette row 6), in Platinum's cursor purple
FRAME_ROW, FRAME_COLOURS = 6, {6: 0x6829, 7: 0x7D2A, 10: 0x7D51, 11: 0x7CEB}
# Black 2 frames the Pokémon a move can target, or those it hits together, in its own shape (a double battle's maps;
# 384-408 are a triple battle's, which Platinum's battles don't have). Here the frame becomes an outline of each of
# Platinum's panels it covers, along their edge, two pixels thick (the outer ring index 6, the inner 7). BG 4 shows
# them 16 pixels lower than the map has them
DOUBLES_FRAMES = range(409, 420)
FRAME_ROWS_DOWN = 2
TARGET_MAP = 0x175
# Platinum shows an empty slot dark grey: the tile's body (14, and 13 below it) in its greys
EMPTY_BODY = {14: 0x358C, 13: 0x2D4A}
# The back button, which becomes a CANCEL button of its size from Platinum's (0x2b, row 4: columns 1 to 30, rows 19
# to 23): its two ends and its middle
BACK_COLUMNS, BACK_ROWS = range(54, 64), range(17, 24)
PT_CANCEL_ROWS, PT_CANCEL_LEFT, PT_CANCEL_MIDDLE, PT_CANCEL_RIGHT = range(19, 24), (1, 2), 8, (29, 30)
CANCEL_CENTRE = (216, 172)
# The text Black 2 prints on the lower screen (palette row 13: its letters and shadow, then the PP's when low:
# yellow, orange, red, each with its shadow), darker, for Platinum's light buttons
TEXT_ROW = 13
# The ball shown between screens and behind the messages (BG 7: characters 0x17d, 256 colours; map 0x17e, 512x512
# affine): at rest it's scaled by 3 about the map's centre, at x 128 and y 152 (btlv_input.c BtlvInput_BallScaleTask),
# so screen pixel (x, y) shows map pixel (3x - 128, 3y - 56). It becomes the command screen's background, three
# times its size there, so that at rest it's the same; Black 2's zoom between screens enlarges it
BALL_CHARS, BALL_MAP = 0x17D, 0x17E
BALL_SCALE, BALL_X, BALL_Y = 3, -128, -56
# The rows of the background it shows: not the grey bars at its top and bottom (0-15, 176-191) nor the light lines
# along them (16-19, 172-175), which the buttons hide on the command screen and it can't show whole, its map being too
# small for the screen at that scale; behind the messages the background is one colour around the ball (the user's)
BALL_ROWS = (20, 172)
# The key cursor (the four corners around the button the D-pad is on): Black 2's corner (characters 0x1a8, one 16x16
# tile; cells 0x1a9, the tile flipped for each corner; animations 0x1aa, which bob it) becomes Platinum's red L with
# its white edge (res/graphics/battle/interface/cursor.png, the battle's cursor; its colours, 14 and 15, put into the
# rows Black 2's cells use, 0 and 4, where no other sprite uses them), the L's corner on the button's corner, as
# Platinum's are: on the point a corner is drawn at, at the top and left, and a pixel before it at the right and
# bottom, where Black 2's boxes and touch rectangles end (gen5_battle.c and gen5_runtime.c make those the buttons';
# the bag's and the party list's cursor are the same files)
B2_CURSOR_CHARS, B2_CURSOR_CELLS, B2_OBJ_PALETTES = 0x1A8, 0x1A9, 0x1A5
CURSOR_ROWS, CURSOR_COLOURS = (0, 4), {14: 0x7FFF, 15: 0x001F}
# The fixed labels Black 2 prints on the bag's and the party list's buttons (the pockets, LAST USED ITEM, USE,
# SUMMARY, CHECK MOVES, SHIFT …) print in Platinum's button font (the user's): it's made into Black 2's font format
# (system/gf_font.c: Nitro's, with Black 2's own width table; its cells 12x15 as Black 2's fonts', each row's 2-bit
# pixels following the last's) and added to this archive's copy, as member LABEL_FONT_MEMBER, which gen5_runtime.c
# prints them in. Platinum's glyphs (res/fonts/font_subscreen, 16x16, glyph =
# charcode - 1) have a body (1), its shading (2) and an outline (3); Black 2 draws a glyph's 1 as the letter and 2 as
# the shadow, and 3 not at all, so the body and shading become 1 and the outline 2, closed all round (label_outlined).
# Characters by the decomp's charmap (PlatinumRom.charmap)
LABEL_FONT_MEMBER = mystery_type.TILE_PALETTE_MEMBER + 1
LABEL_CELL_WIDTH, LABEL_CELL_HEIGHT = 12, 15
LABEL_GLYPH_VALUES = {0: 0, 1: 1, 2: 1, 3: 2}
LABEL_CHAR_ALIASES = {"'": "’"}
TEXT_COLOURS = {1: 0x1CE7, 2: 0x5AD6, 3: 0x0218, 4: 0x3F7F, 5: 0x01D9, 6: 0x2EBF, 7: 0x1018, 8: 0x35BF}
# The yes/no screen's labels, which gen5_runtime.c prints in Platinum's button font (LABEL_FONT_MEMBER), as Platinum
# does (battle_subscreen.c BattleSubscreen_DrawYesNoMenu: TEXT_COLOR(1, 2, 3) on the upper button, (10, 11, 12) on the
# lower): white, outlined in the dark shade of the button's colour. At indices of the text row Black 2 leaves unused
# (gen5_runtime.c G5_YESNO_LABEL_*), from row PT_LABEL_PALETTE_ROW's: index in the text row, index in Platinum's
YESNO_LABEL_COLOURS = {11: 1, 12: 3, 13: 12}
CHARMAP = {chr(c): 0x12B + c - ord("A") for c in range(ord("A"), ord("Z") + 1)}
CHARMAP["é"] = 0x188


# --- Nitro files ---

def blocks(d: bytes) -> dict:
    header_size, count = struct.unpack_from("<HH", d, 12)
    off, found = header_size, {}
    for _ in range(count):
        magic, size = bytes(d[off:off + 4]), struct.unpack_from("<I", d, off + 4)[0]
        found[magic] = off
        off += size
    return found


def unpack(data: bytes):
    compressed = data[0] in (0x10, 0x11)
    return bytearray(mts.unlz(data) if compressed else data), compressed


def pack(d: bytearray, compressed: bool) -> bytes:
    return mts.lz10(bytes(d)) if compressed else bytes(d)


def chars_base(d) -> int:
    r = blocks(d)[b"RAHC"]
    assert struct.unpack_from("<I", d, r + 12)[0] == 3, "4 bits a pixel"
    return r + 8 + struct.unpack_from("<I", d, r + 28)[0]


def read_tiles(d) -> list:
    base, size = chars_base(d), struct.unpack_from("<I", d, blocks(d)[b"RAHC"] + 24)[0]
    return [tuple(d[base + t * 32 + i // 2] >> (4 * (i & 1)) & 15 for i in range(64)) for t in range(size // 32)]


def write_tiles(d, tiles: list):
    base, size = chars_base(d), struct.unpack_from("<I", d, blocks(d)[b"RAHC"] + 24)[0]
    assert len(tiles) * 32 <= size, f"{len(tiles)} tiles"
    for t in range(size // 32):
        px = tiles[t] if t < len(tiles) else (0,) * 64
        for i in range(0, 64, 2):
            d[base + t * 32 + i // 2] = px[i] | px[i + 1] << 4


def read_map(d):
    """The map's entries in rows: wider or taller than 32 tiles, it's stored as 32x32 screen blocks."""
    n = blocks(d)[b"NRCS"]
    w, h, _, size = struct.unpack_from("<HHII", d, n + 8)
    tw, th = w // 8, h // 8
    stored = struct.unpack_from(f"<{size // 2}H", d, n + 20)
    return tw, th, [stored[stored_index(tw, th, i)] for i in range(tw * th)]


def stored_index(tw, th, i):
    r, c = divmod(i, tw)
    if tw <= 32 and th <= 32:
        return i
    return ((r // 32) * (tw // 32) + c // 32) * 1024 + (r % 32) * 32 + c % 32


def write_map(d, tw, th, entries):
    n = blocks(d)[b"NRCS"]
    for i, e in enumerate(entries):
        struct.pack_into("<H", d, n + 20 + 2 * stored_index(tw, th, i), e)


def palette_base(d) -> int:
    t = blocks(d)[b"TTLP"]
    return t + 8 + struct.unpack_from("<I", d, t + 20)[0]


def read_colours(d) -> list:
    t = blocks(d)[b"TTLP"]
    size = struct.unpack_from("<I", d, t + 16)[0]
    return list(struct.unpack_from(f"<{size // 2}H", d, palette_base(d)))


# --- Cells: an 8x8 tile's 64 colour indices and its palette row; None is an empty cell ---

def flip(px, h, v):
    return tuple(px[(7 - y if v else y) * 8 + (7 - x if h else x)] for y in range(8) for x in range(8))


def cell_of(tiles, e):
    px = tiles[e & 0x3FF]
    if not any(px):
        return None
    return flip(px, e >> 10 & 1, e >> 11 & 1), e >> 12


class Encoder:
    """New characters for the cells, each kept once with its flips found."""

    def __init__(self):
        self.tiles = [(0,) * 64]
        self.index = {(0,) * 64: (0, 0, 0)}

    def entry(self, cell) -> int:
        if cell is None:
            return 0
        px, row = cell
        if px not in self.index:
            t = len(self.tiles)
            self.tiles.append(px)
            for h in (0, 1):
                for v in (0, 1):
                    self.index.setdefault(flip(px, h, v), (t, h, v))
        t, h, v = self.index[px]
        return t | h << 10 | v << 11 | row << 12


# --- Platinum's art ---

class Platinum:
    def __init__(self, platinum: PlatinumRom):
        art = nitro.NARC(platinum.file(PT_ART))
        self.files = art.files
        self.tiles = read_tiles(unpack(art.files[PT_CHARS])[0])
        colours = read_colours(unpack(art.files[PT_PALETTES])[0])
        location = read_colours(unpack(art.files[PT_LOCATION])[0])
        self.rows = {r: colours[r * 16:r * 16 + 16] for r in range(16)}
        self.rows[0] = location[:16]
        # The labels' shades (as the decomp's JASC palette has them, shifted down)
        interface = platinum.palette(BATTLE_SPRITES, INTERFACE_PALETTE)
        label = [interface[PT_LABEL_PALETTE_ROW * 16 + i] & 0x7FFF for i in range(16)]
        for r, first in LABEL_FIRST_COLOUR.items():
            for index, i in ((LABEL_LIGHT, first + 1), (LABEL_DARK, first + 2)):
                self.rows[r][index] = label[i]
        self.yesno_colours = {index: label[i] for index, i in YESNO_LABEL_COLOURS.items()}
        font, self.widths = platinum.font(FONT_SUBSCREEN)
        self.font = font.load()
        # Platinum's move tiles' palettes, by name (Normal …, None)
        self.move_palette = platinum.move_palettes()

    def cells(self, map_id) -> list:
        """A 32x32 map's cells, by row and column."""
        tw, th, entries = read_map(unpack(self.files[map_id])[0])
        return [[cell_of(self.tiles, entries[r * tw + c]) for c in range(tw)] for r in range(th)]

    def background(self) -> list:
        """The background, on row 0, its empty cells (below the screen) filled with its colour. Its panels (0x30) are
        the key cursor's highlight, which pulses, not shown when the screen is touched"""
        cells = self.cells(PT_BACKGROUND)
        solid = Counter(cell for row in cells for cell in row if cell and len(set(cell[0])) == 1)
        fill = solid.most_common(1)[0][0]
        self.background_colour = self.rows[0][fill[0][0]]
        return [[cell or fill for cell in row] for row in cells]

    def label(self, cells, text, centre):
        """Draws text into the buttons' cells, centred, in each cell's row's label colours."""
        codes = [CHARMAP[ch] for ch in text]
        width = sum(self.widths[c - 1] for c in codes)
        x0, y0 = centre[0] - width // 2, centre[1] - 8
        x = x0
        for c in codes:
            g = c - 1
            gx, gy = (g % 16) * 16, (g // 16) * 16
            for y in range(16):
                for dx in range(self.widths[g]):
                    v = self.font[gx + dx, gy + y]
                    if v:
                        put(cells, x + dx, y0 + y, (WHITE, LABEL_LIGHT, LABEL_DARK)[v - 1])
            x += self.widths[g]


def put(cells, x, y, colour):
    r, c = y // 8, x // 8
    cell = cells[r][c]
    if cell is None:
        return
    px = list(cell[0])
    px[(y % 8) * 8 + x % 8] = colour
    cells[r][c] = (tuple(px), cell[1])


def middle(n, count):
    """count indices into n, the middle ones dropped or the middle one repeated."""
    if count <= n:
        return list(range((count + 1) // 2)) + list(range(n - count // 2, n))
    return list(range(n // 2)) + [n // 2] * (count - n) + list(range(n // 2, n))


def panel(pt: Platinum, map_id, pt_row, height, width, row) -> list:
    """The Platinum panel on pt_row of a map, fitted to height x width cells, on Black 2's row."""
    cells = pt.cells(map_id)
    where = [(r, c) for r in range(len(cells)) for c in range(32) if cells[r][c] and cells[r][c][1] == pt_row]
    top, left = min(r for r, _ in where), min(c for _, c in where)
    bottom, right = max(r for r, _ in where), max(c for _, c in where)
    rows, cols = middle(bottom - top + 1, height), middle(right - left + 1, width)
    return [[(cells[top + r][left + c][0], row) if cells[top + r][left + c] else None for c in cols] for r in rows]


def cancel_button(pt: Platinum) -> list:
    """A CANCEL button the size of Black 2's back button: Platinum's ends and middle, labelled."""
    cells = pt.cells(PT_MOVES)
    columns = list(PT_CANCEL_LEFT) + [PT_CANCEL_MIDDLE] * (len(BACK_COLUMNS) - 4) + list(PT_CANCEL_RIGHT)
    rows = [[None] * 32 for _ in range(24)]
    for r in PT_CANCEL_ROWS:
        for k, c in enumerate(columns):
            rows[r][22 + k] = cells[r][c]
    pt.label(rows, "CANCEL", CANCEL_CENTRE)
    return rows


def command_buttons(pt: Platinum, words: dict, removed=()) -> list:
    """Platinum's command screen buttons, labelled with a set's words (lower_screen_sets: FIGHT!, BAG, POKéMON,
    RUN)."""
    cells = pt.cells(PT_COMMAND)
    for slot in removed:
        for r in BUTTON_ROWS:
            for c in SLOTS[slot]:
                cells[r][c] = None
    for key, text in (("FIGHT", words.get("FIGHT!", "FIGHT!")), ("BAG", words.get("BAG", "BAG")),
                      ("POKéMON", words.get("POKéMON", "POKéMON")), ("RUN", words.get("RUN", "RUN"))):
        if key in removed:
            continue
        pt.label(cells, text.rstrip("!"), LABEL_CENTRES[key])
    return cells


# --- Black 2's lower screen, redrawn ---

def panel_boxes(tiles, tw, entries, rows):
    """Where each panel of a BG 5 map's right half is: [top, left, bottom, right] in cells, by palette row."""
    boxes = {}
    for i, e in enumerate(entries):
        r, c = divmod(i, tw)
        row = e >> 12
        if c >= 32 and row in rows and any(tiles[e & 0x3FF]):
            b = boxes.setdefault(row, [r, c, r, c])
            b[0], b[1], b[2], b[3] = min(b[0], r), min(b[1], c), max(b[2], r), max(b[3], c)
    return boxes


def ball(files: list, offset: int, background: list):
    """BG 7's characters and map: the background, enlarged."""
    # The background's colour indices (row 0, so the same in 256 colours), by screen pixel
    def index(x, y):
        cell = background[y // 8][x // 8]
        return cell[0][(y % 8) * 8 + x % 8] if cell else 0

    fill = Counter(index(x, 96) for x in range(256)).most_common(1)[0][0]
    tiles, entries, seen = [(0,) * 64], [], {(0,) * 64: 0}
    for ty in range(64):
        for tx in range(64):
            px = []
            for y in range(8):
                for x in range(8):
                    sx = (tx * 8 + x - BALL_X) // BALL_SCALE
                    sy = (ty * 8 + y - BALL_Y) // BALL_SCALE
                    px.append(index(sx, sy) if 0 <= sx < 256 and BALL_ROWS[0] <= sy < BALL_ROWS[1] else fill)
            px = tuple(px)
            if px not in seen:
                seen[px] = len(tiles)
                tiles.append(px)
            entries.append(seen[px])
    assert len(tiles) <= 1024, len(tiles)

    d, lz = unpack(files[BALL_CHARS + offset])
    r = blocks(d)[b"RAHC"]
    assert struct.unpack_from("<I", d, r + 12)[0] == 4, "256 colours"
    base, size = r + 8 + struct.unpack_from("<I", d, r + 28)[0], struct.unpack_from("<I", d, r + 24)[0]
    flat = bytes(v for t in tiles for v in t)
    d[base:base + size] = flat + bytes(size - len(flat))
    files[BALL_CHARS + offset] = pack(d, lz)

    d, lz = unpack(files[BALL_MAP + offset])
    n = blocks(d)[b"NRCS"]
    for i, t in enumerate(entries):
        struct.pack_into("<H", d, n + 20 + 2 * i, t)
    files[BALL_MAP + offset] = pack(d, lz)


def target_outlines(files: list, offset: int, pt: Platinum, tiles: list):
    """A function from a frame map's entries to its cells: outlines of the target panels its frame goes around."""
    d, _ = unpack(files[TARGET_MAP + offset])
    tw, _, entries = read_map(d)
    sources = PANELS[TARGET_MAP]
    # Each panel's place in cells and its pixels on the screen: Black 2's boxes are in the right half, 24 rows down
    shapes = []
    for row, box in panel_boxes(tiles, tw, entries, sources).items():
        cells = panel(pt, sources[row][0], sources[row][1], box[2] - box[0] + 1, box[3] - box[1] + 1, row)
        top, left = box[0] - RIGHT_HALF_ROWS, box[1] - 32
        pixels = {((left + c) * 8 + i % 8, (top + r) * 8 + i // 8)
                  for r, line in enumerate(cells) for c, cell in enumerate(line) if cell
                  for i, v in enumerate(cell[0]) if v}
        edge = {(r, c) for r in range(top, top + box[2] - box[0] + 1) for c in range(left, left + box[3] - box[1] + 1)
                if r in (top, top + box[2] - box[0]) or c in (left, left + box[3] - box[1])}
        shapes.append((edge, pixels))

    def ring(pixels):
        sides = ((1, 0), (-1, 0), (0, 1), (0, -1))
        edge = {p for p in pixels if any((p[0] + dx, p[1] + dy) not in pixels for dx, dy in sides)}
        inner = {p for p in pixels - edge if any((p[0] + dx, p[1] + dy) in edge for dx, dy in sides)}
        return edge, inner

    def outlines(fw, fh, frame_entries):
        framed = {(i // fw + FRAME_ROWS_DOWN, i % fw) for i, e in enumerate(frame_entries) if any(tiles[e & 0x3FF])}
        drawn = {}
        for edge_cells, pixels in shapes:
            # a panel is framed when the frames run along most of its edge (they lie on their panels' edges)
            if len(edge_cells & framed) * 4 < len(edge_cells) * 3:
                continue
            edge, inner = ring(pixels)
            for p in edge:
                drawn[p] = 6
            for p in inner:
                drawn.setdefault(p, 7)
        cells = []
        for r in range(fh):
            for c in range(fw):
                px = tuple(drawn.get((c * 8 + i % 8, (r + FRAME_ROWS_DOWN) * 8 + i // 8), 0) for i in range(64))
                cells.append((px, FRAME_ROW) if any(px) else None)
        return cells
    return outlines


def skin_set(files: list, offset: int, pt: Platinum, background: list, buttons: list, removed=(), cancel=None,
             back=None):
    """One set of the lower screen's files, from offset: its maps and characters, redrawn."""
    chars_data, chars_lz = unpack(files[B2_CHARS + offset])
    tiles = read_tiles(chars_data)
    encoder = Encoder()
    maps = {}
    outlines = target_outlines(files, offset, pt, tiles)
    for m in BG4_MAPS + BG5_MAPS:
        d, lz = unpack(files[m + offset])
        if b"NRCS" not in blocks(d):
            continue
        tw, th, entries = read_map(d)
        sources = PANELS.get(m, {})
        boxes = panel_boxes(tiles, tw, entries, sources)
        panels = {row: (box, panel(pt, sources[row][0], sources[row][1], box[2] - box[0] + 1, box[3] - box[1] + 1,
                                   sources[row][2] if len(sources[row]) > 2 else row))
                  for row, box in boxes.items()}
        has_back = any(cell_of(tiles, entries[r * tw + c]) and entries[r * tw + c] >> 12 == 4
                       for r in BACK_ROWS for c in BACK_COLUMNS if r < th and c < tw)
        if m in DOUBLES_FRAMES:
            maps[m] = (d, lz, tw, th, outlines(tw, th, entries))
            continue
        cells = []
        for i, e in enumerate(entries):
            r, c = divmod(i, tw)
            cell = cell_of(tiles, e)
            if m in BG5_MAPS:
                inside = next(((box, cells_) for box, cells_ in panels.values()
                               if box[0] <= r <= box[2] and box[1] <= c <= box[3]), None)
                if inside:
                    box, cells_ = inside
                    cell = cells_[r - box[0]][c - box[1]]
                    if cell is None:
                        cell = background[r % SCREEN_ROWS][c % 32]
                elif cell is None or cell[1] in B2_AREA_ROWS:
                    cell = background[r % SCREEN_ROWS][c % 32]
            elif cancel and has_back and r in BACK_ROWS and c in BACK_COLUMNS and (cell is None or cell[1] == 4):
                cell = cancel[r][c - 32]
            elif m in BG4_COMMAND_MAPS and r < 32 and c < 32:
                if r in FIGHT_ROWS:
                    cell = buttons[r][c]
                elif r in BUTTON_ROWS:
                    for slot in USUAL[m]:
                        if c in SLOTS[slot]:
                            cell = None if slot in removed else buttons[r][c]
                    if back and m in BACK_IN_RUN and c in SLOTS["RUN"] and "RUN" not in removed:
                        cell = back[r][c]
            cells.append(cell)
        maps[m] = (d, lz, tw, th, cells)
    for m, (d, lz, tw, th, cells) in maps.items():
        write_map(d, tw, th, [encoder.entry(cell) for cell in cells])
        files[m + offset] = pack(d, lz)
    write_tiles(chars_data, encoder.tiles)
    files[B2_CHARS + offset] = pack(chars_data, chars_lz)
    ball(files, offset, background)

    pal_data, pal_lz = unpack(files[B2_PALETTES + offset])
    base = palette_base(pal_data)
    for r in PT_ROWS:
        for i, colour in enumerate(pt.rows[r]):
            struct.pack_into("<H", pal_data, base + (r * 16 + i) * 2, colour)
    for i, colour in (TEXT_COLOURS | pt.yesno_colours).items():
        struct.pack_into("<H", pal_data, base + (TEXT_ROW * 16 + i) * 2, colour)
    for i, colour in FRAME_COLOURS.items():
        struct.pack_into("<H", pal_data, base + (FRAME_ROW * 16 + i) * 2, colour)
    for r in OPPONENT_PANEL_ROWS:
        for i, colour in enumerate(pt.rows[TARGET_PALETTES[481]]):
            struct.pack_into("<H", pal_data, base + (r * 16 + i) * 2, colour)
    # The backdrop, which shows through the edges of the buttons on BG 5, in the background's colour
    struct.pack_into("<H", pal_data, base, pt.background_colour)
    files[B2_PALETTES + offset] = pack(pal_data, pal_lz)

    # The move tiles' palettes by type, and for no move
    for fid, colours in [(f, pt.move_palette[t]) for f, t in zip(B2_TYPE_PALETTES, PT_TYPES)] + \
                        [(f, [EMPTY_BODY.get(i, c) for i, c in enumerate(pt.move_palette["None"])])
                         for f in NO_MOVE_PALETTES] + \
                        [(f, pt.rows[r]) for f, r in TARGET_PALETTES.items()]:
        write_palette(files, fid + offset, colours)
    return len(encoder.tiles)


def write_palette(files: list, fid: int, colours: list):
    """A palette file's first 16 colours."""
    d, lz = unpack(files[fid])
    b = palette_base(d)
    assert len(colours) == 16, (fid, len(colours))
    for i, colour in enumerate(colours):
        struct.pack_into("<H", d, b + i * 2, colour)
    files[fid] = pack(d, lz)


# --- The bag (archive 98) ---
#
# Black 2's battle bag (pokebw2 src/ov286: b_bag_main.c, b_bag_anm.c) draws on BG 6 and 7, both on characters 0 and
# rows 0 to 6 of palette 2: BG 7 the background (map 3), BG 6 the pages (map 4, 512x512, scrolled to the one shown: the
# pockets top left, a pocket's items top right, an item bottom left) and over them its buttons, each a frame from a
# member of its own (5-13) that it recolours by palette row: normal, pressed and disabled are rows 1, 2 and 3 for the
# small buttons (back, the page arrows, the wide bar: LAST USED ITEM and USE), 4, 5 and 6 for the pockets and items.
# Platinum's (src/battle_sub_menus/battle_bag*.c; b_bag_gra.narc) lays its pages out the same way, in one map (0), and
# draws its buttons by palette row too, from another (1) with each state's art (battle_bag_buttons.c). Its normal art
# becomes Black 2's frames, its pressed and disabled looks the colours of the rows that recolour them, its pages the
# pages. Platinum colours a pocket's items, and USE, by pocket; here they're its pockets' orange, and the wide bar is
# LAST USED ITEM's red for USE too.
PT_BAG = "battle/graphic/b_bag_gra.narc"  # res/prebuilt/battle/graphic/b_bag_gra.narc
PT_BAG_PAGES, PT_BAG_BUTTONS, PT_BAG_CHARS, PT_BAG_PALETTES = 0, 1, 2, 3
B2_BAG_CHARS, B2_BAG_PALETTES, B2_BAG_BACKGROUND, B2_BAG_PAGES = 0, 2, 3, 4
# By Black 2's frame member: Platinum's normal art (map 1: column, row, width, height), the palette row Platinum draws
# it in, the pocket icon it carries (map 1: column, row; 4x4, centred at its top), and the row group it's recoloured in
BAG_FRAMES = {
    5: ((0, 0, 16, 9), 0, (20, 47), "big"),     # HP/PP RESTORE
    6: ((0, 0, 16, 9), 0, (20, 51), "big"),     # STATUS RESTORE
    7: ((0, 0, 16, 9), 0, (20, 55), "big"),     # POKé BALLS
    8: ((0, 0, 16, 9), 0, (20, 59), "big"),     # BATTLE ITEMS
    9: ((16, 0, 16, 6), 1, None, "big"),        # an item
    10: ((0, 47, 5, 5), 2, None, "small"),      # the previous page: Platinum's up
    11: ((0, 52, 5, 5), 2, None, "small"),      # the next page: down
    12: ((0, 57, 5, 5), 2, None, "small"),      # back
    13: ((0, 27, 26, 5), 3, None, "small"),     # the wide bar
}
# Black 2's palette rows of each group, normal, pressed and disabled; the pages' row
BAG_GROUPS = {"big": (4, 5, 6), "small": (1, 2, 3)}
BAG_PAGE_ROW = 0
# Platinum's pressed and disabled looks, as recolourings of its normal art: pressed, its body in the colour of the
# pressed art's (Platinum's pressed buttons are drawn pushed down, so only their body's colour carries over: the
# normal art's and the pressed art's in map 1, column, row, width, height); disabled, in the row Platinum draws a
# disabled button in
BAG_PRESSED = {"big": ((16, 0, 16, 6), (16, 6, 16, 6)), "small": ((0, 57, 5, 5), (5, 57, 5, 5))}
PT_DISABLED_ROW = 5
# The quantiser keeps the pocket icons' colours before the buttons' shading, each icon pixel counted this many times.
# The pockets' and the items' buttons have 19 colours for 15 places: at full size (GAME-90), 8 merges the shades of
# HP/PP RESTORE's, STATUS RESTORE's and BATTLE ITEMS' icons into one, as when the two-line pockets' icons were smaller;
# 16 would keep HP/PP RESTORE's and give the pockets' top edge the items' yellow
ICON_WEIGHT = 8
# The pocket icons at full size, between the button's inside top and the name, in the middle (the user's). Black 2
# prints a pocket's name higher than Platinum (from its 4th row of cells; gen5_runtime.c brings it down 3 pixels for two
# lines, 4 for one) and its buttons are a row of cells shorter (the middle row left out), so Platinum's icon stays where
# its art has it above a name of one line, and above a name of two lines, which starts at the button's pixel row 30,
# goes up by these pixels, by member: to rows 9 to 26, two rows of the inside (from row 7) above it, three below
# (GAME-90)
ICON_RAISE = {5: 1, 6: 1}
# The pocket icons' palette row; its colours that are also the pocket's are the pocket's, which brighten when pressed
PT_ICON_ROW = 6
# Platinum's buttons on its pages (battle_bag_buttons.c sButtonDimensions: column, row, width, height), which Black 2's
# frames cover; the page box's columns on Black 2's (where it prints the pocket's name and the page) and on Platinum's
PT_BAG_BUTTONS_AT = [(0, 1, 16, 9), (0, 10, 16, 9), (16, 1, 16, 9), (16, 10, 16, 9), (0, 19, 26, 5), (27, 19, 5, 5),
                     (32, 1, 32, 18), (32, 19, 10, 5), (59, 19, 5, 5), (0, 51, 26, 5), (27, 51, 5, 5)]
BAG_BOX_ROWS, B2_BOX_COLUMNS, PT_BOX_COLUMNS = range(19, 24), range(42, 59), range(42, 59)


class PlatinumBag:
    def __init__(self, platinum: PlatinumRom):
        art = nitro.NARC(platinum.file(PT_BAG))
        tiles = read_tiles(unpack(art.files[PT_BAG_CHARS])[0])
        colours = read_colours(unpack(art.files[PT_BAG_PALETTES])[0])
        self.rows = {r: colours[r * 16:r * 16 + 16] for r in range(len(colours) // 16)}
        self.maps = {}
        for m in (PT_BAG_PAGES, PT_BAG_BUTTONS):
            tw, th, entries = read_map(unpack(art.files[m])[0])
            self.maps[m] = [[(flip(tiles[e & 0x3FF], e >> 10 & 1, e >> 11 & 1), e >> 12)
                             for e in entries[r * tw:r * tw + tw]] for r in range(th)]

    def piece(self, m, x, y, w, h) -> list:
        return [row[x:x + w] for row in self.maps[m][y:y + h]]

    def body(self, x, y, w, h) -> int:
        """The colour index most of a piece of map 1 is."""
        counts = Counter(i for line in self.piece(PT_BAG_BUTTONS, x, y, w, h) for px, _ in line for i in px if i)
        return counts.most_common(1)[0][0]


def quantise(counts: Counter, size=15) -> dict:
    """At most size colour tuples for those counted: the rarest merged into the nearest, by pixels times distance."""
    def distance(a, b):
        return sum(((p >> s & 31) - (q >> s & 31)) ** 2 for p, q in zip(a, b) for s in (0, 5, 10))

    keep = dict(counts)
    merged = {t: t for t in counts}
    while len(keep) > size:
        t, n = min(keep.items(), key=lambda kv: kv[1] * min(distance(kv[0], u) for u in keep if u != kv[0]))
        into = min((u for u in keep if u != t), key=lambda u: distance(t, u))
        keep[into] += keep.pop(t)
        for k, v in merged.items():
            if v == t:
                merged[k] = into
    order = sorted(keep, key=lambda t: -keep[t])
    return {t: order.index(merged[t]) + 1 for t in counts}


def skin_bag(files: list, bag: PlatinumBag):
    """The bag's characters, maps and palette rows 0 to 6, redrawn with Platinum's."""
    rows = bag.rows
    pressed = {g: {bag.body(*a): bag.body(*b)} for g, (a, b) in BAG_PRESSED.items()}

    # Each pixel's colours, normal, pressed and disabled, by its Platinum row and index; 0 stays transparent
    def colours(group, row, i):
        if group == "page":
            return (rows[row][i],)
        if row == PT_ICON_ROW and rows[PT_ICON_ROW][i] != rows[0][i]:
            return (rows[row][i],) * 3
        if row == PT_ICON_ROW:
            row = 0
        return rows[row][i], rows[row][pressed[group].get(i, i)], rows[PT_DISABLED_ROW][i]

    # A cell's pixels as (Platinum row, index) each
    def lift(cell_):
        px, row = cell_
        return tuple((row, i) for i in px)

    def raise_icon(art, body, by):
        """The icon (its cells' pixels that aren't the button's body) moved up by pixels; the body where it was."""
        grid = [[art[y // 8][x // 8][(y % 8) * 8 + x % 8] for x in range(len(art[0]) * 8)] for y in range(len(art) * 8)]
        icon = {(y, x): pixel for y, line in enumerate(grid) for x, pixel in enumerate(line)
                if pixel[0] == PT_ICON_ROW and pixel[1] not in (0, body)}
        for y, x in icon:
            grid[y][x] = (0, body)
        for (y, x), pixel in icon.items():
            grid[y - by][x] = pixel
        return [[tuple(grid[r * 8 + k // 8][c * 8 + k % 8] for k in range(64)) for c in range(len(art[0]))]
                for r in range(len(art))]

    # The frames' art and the pages', as cells of pixels, and the group each is in
    frames = {}
    for member, ((x, y, w, h), row, icon, group) in BAG_FRAMES.items():
        d, lz = unpack(files[member])
        tw, th, _ = read_map(d)
        art = bag.piece(PT_BAG_BUTTONS, x, y, w, h)
        art = [[(px, row) for px, _ in r] for r in art]
        if icon:
            for r, line in enumerate(bag.piece(PT_BAG_BUTTONS, icon[0], icon[1], 4, 4)):
                for c, cell_ in enumerate(line):
                    art[r][(w - 4) // 2 + c] = cell_
        art = [[lift(art[r][c]) for c in middle(w, tw)] for r in middle(h, th)]
        if member in ICON_RAISE:
            art = raise_icon(art, bag.body(x, y, w, h), ICON_RAISE[member])
        frames[member] = (d, lz, tw, th, art, group)

    page = [row[:] for row in bag.maps[PT_BAG_PAGES]]
    # The background: the commonest plain cell of the disabled grey's row
    fill = Counter(cell for line in page for cell in line
                   if cell[1] == PT_DISABLED_ROW and len(set(cell[0])) == 1).most_common(1)[0][0]
    for x, y, w, h in PT_BAG_BUTTONS_AT:
        for r in range(y, y + h):
            for c in range(x, x + w):
                page[r][c] = fill
    # The page box, stretched to Black 2's
    box = [page[r][PT_BOX_COLUMNS.start:PT_BOX_COLUMNS.stop] for r in BAG_BOX_ROWS]
    edges = [c for c in range(len(PT_BOX_COLUMNS)) if any(box[k][c] != fill for k in range(len(box)))]
    span = [line[edges[0]:edges[-1] + 1] for line in box]
    for k, r in enumerate(BAG_BOX_ROWS):
        for c in B2_BOX_COLUMNS:
            page[r][c] = fill
        for n, c in enumerate(middle(len(span[k]), len(B2_BOX_COLUMNS))):
            page[r][B2_BOX_COLUMNS.start + n] = span[k][c]
    for r in range(32, 64):
        for c in range(32, 64):
            page[r][c] = fill

    # The colour tuples of each group, and Black 2's palette indices for them
    counts = {"page": Counter(), "big": Counter(), "small": Counter()}
    counts["page"][colours("page", fill[1], fill[0][0])] += 1
    for line in page:
        for px, row in line:
            for i in px:
                if i:
                    counts["page"][colours("page", row, i)] += 1
    for _, _, _, _, art, group in frames.values():
        for line in art:
            for px in line:
                for row, i in px:
                    if i:
                        counts[group][colours(group, row, i)] += ICON_WEIGHT if row == PT_ICON_ROW else 1
    index = {g: quantise(c) for g, c in counts.items()}

    def cell(px, group, b2_row):
        return tuple(index[group][colours(group, row, i)] if i else 0 for row, i in px), b2_row

    encoder = Encoder()
    page_cells = [cell(lift(c), "page", BAG_PAGE_ROW) for line in page for c in line]
    fill_cell = cell(lift(fill), "page", BAG_PAGE_ROW)
    d, lz = unpack(files[B2_BAG_PAGES])
    tw, th, _ = read_map(d)
    write_map(d, tw, th, [encoder.entry(c) for c in page_cells])
    files[B2_BAG_PAGES] = pack(d, lz)
    d, lz = unpack(files[B2_BAG_BACKGROUND])
    tw, th, _ = read_map(d)
    write_map(d, tw, th, [encoder.entry(fill_cell)] * (tw * th))
    files[B2_BAG_BACKGROUND] = pack(d, lz)
    for member, (d, lz, tw, th, art, group) in frames.items():
        write_map(d, tw, th, [encoder.entry(cell(c, group, BAG_GROUPS[group][0])) for line in art for c in line])
        files[member] = pack(d, lz)
    chars_data, chars_lz = unpack(files[B2_BAG_CHARS])
    write_tiles(chars_data, encoder.tiles)
    files[B2_BAG_CHARS] = pack(chars_data, chars_lz)

    pal_data, pal_lz = unpack(files[B2_BAG_PALETTES])
    base = palette_base(pal_data)
    groups = {"page": (BAG_PAGE_ROW,), **BAG_GROUPS}
    for g, b2_rows in groups.items():
        for t, k in index[g].items():
            for state, b2_row in enumerate(b2_rows):
                struct.pack_into("<H", pal_data, base + (b2_row * 16 + k) * 2, t[state])
    # The backdrop, behind BG 7, in the background's colour
    struct.pack_into("<H", pal_data, base, colours("page", fill[1], fill[0][0])[0])
    files[B2_BAG_PALETTES] = pack(pal_data, pal_lz)
    return len(encoder.tiles), {g: len(c) for g, c in counts.items()}


# --- The party list (archive 99) ---
#
# Black 2's battle party list (pokebw2 src/ov287: b_plist_main.c, b_plist_anm.c) is Platinum's
# (src/battle_sub_menus/battle_party*.c; pl_b_plist_gra.narc) under another skin: the same pages, each a background
# on BG 7 and buttons on BG 6 (Black 2's maps by page, b_plist_main.c data_ov287_021fb50c; Platinum's
# ScreenBackgroundDataMemberIndexes), its buttons' states cut from two maps at the same places (Black 2's 16 and 17,
# Platinum's 20 and 21), the experience bar drawn from the same characters (0x16 to 0x1e, 8 at x 10, y 8), the text
# in the same windows. So Platinum's maps replace Black 2's, by page: Black 2's map, Platinum's
PLIST_MAPS = {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9, 10: 10, 11: 11,
              12: 14, 13: 15,  # confirming a move to learn
              14: 18, 15: 19,  # a Pokémon's choices (SHIFT, SUMMARY, CHECK MOVES)
              16: 20, 17: 21}  # the buttons' states
PT_PLIST = "battle/graphic/pl_b_plist_gra.narc"  # res/prebuilt/battle/graphic/pl_b_plist_gra.narc
PT_PLIST_CHARS, PT_PLIST_PALETTES = 22, 23
B2_PLIST_CHARS, B2_PLIST_PALETTES = 18, 20
# The experience bar's characters, which both draw by number
EXP_BAR_TILES = range(0x16, 0x1F)
# Palette rows. Black 2 recolours a fainted Pokémon's plate to row 7 (8 pressed) and a partner's to 5 (6), where
# Platinum has 2 and 1; its plates keep their row, 0 in both. Its text windows print in row 9 (its own colours kept),
# the font and message box load over 13 and 14, and 15 isn't loaded. Platinum's other rows share the rest, merged
# where their colours fit together
PLIST_FIXED_ROWS = {0: (0,), 1: (5, 6), 2: (7, 8)}
PLIST_FREE_ROWS = (1, 2, 3, 4, 10, 11, 12)
# Black 2 prints all its text in white (row 9: letters 15 and shadow 14, a stat's 8 and 9), where Platinum prints the
# values in its pale boxes in black: gen5_runtime.c gives those windows this row instead, which has dark letters at
# those indices, with the fewest of Platinum's colours in the others
PLIST_DARK_TEXT_ROW = 12
PLIST_DARK_TEXT = {15: 0x1CE7, 14: 0x5AD6, 8: 0x1CE7, 9: 0x5AD6}
# The labels' outline in Platinum's font (gen5_runtime.c G5_PLIST_LABEL_OUTLINE): an index of the text row Black 2
# prints nothing in
PLIST_TEXT_ROW, PLIST_LABEL_OUTLINE = 9, {7: 0x2108}


def skin_party_list(files: list, platinum: PlatinumRom):
    """The party list's characters, maps and palette, Platinum's."""
    art = nitro.NARC(platinum.file(PT_PLIST))
    tiles = read_tiles(unpack(art.files[PT_PLIST_CHARS])[0])
    colours = read_colours(unpack(art.files[PT_PLIST_PALETTES])[0])
    rows = [colours[r * 16:r * 16 + 16] for r in range(16)]
    maps = {}
    for b2, pt in PLIST_MAPS.items():
        tw, th, entries = read_map(unpack(art.files[pt])[0])
        maps[b2] = (tw, th, [cell_of(tiles, e) for e in entries])

    # The colours each of Platinum's other rows uses (by pixels), packed into Black 2's free rows, most first; when
    # they don't fit, the rarest colour becomes the nearest its row has, until they do
    used = {}
    for _, _, cells in maps.values():
        for cell in cells:
            if cell and cell[1] not in PLIST_FIXED_ROWS:
                for i in cell[0]:
                    if i:
                        used.setdefault(cell[1], Counter())[rows[cell[1]][i]] += 1
    # and the experience bar's characters, in its cells' row, the full ones too
    exp_row = maps[4][2][8 * 32 + 10][1]
    for t in EXP_BAR_TILES:
        for i in tiles[t]:
            if i:
                used[exp_row][rows[exp_row][i]] += 1
    remap = {r: {} for r in used}

    def pack_rows():
        packed = []
        for r in sorted(used, key=lambda r: -len(used[r])):
            cs = set(used[r])
            fits = [k for k, (_, ks) in enumerate(packed) if len(ks | cs) <= 15]
            if fits:
                k = max(fits, key=lambda k: len(packed[k][1] & cs))
                packed[k][0].append(r)
                packed[k][1].update(cs)
            else:
                packed.append(([r], cs))
        return packed

    def distance(a, b):
        return sum(((a >> s & 31) - (b >> s & 31)) ** 2 for s in (0, 5, 10))

    while len(packed := pack_rows()) > len(PLIST_FREE_ROWS):
        r, colour = min(((r, c) for r in used for c in used[r]), key=lambda rc: used[rc[0]][rc[1]])
        into = min((c for c in used[r] if c != colour), key=lambda c: distance(c, colour))
        used[r][into] += used[r].pop(colour)
        remap[r] = {k: (into if v == colour else v) for k, v in remap[r].items()}
        remap[r][colour] = into
    target, palette = {}, {}
    packed.sort(key=lambda p: len(p[1]))
    free = [PLIST_DARK_TEXT_ROW] + [r for r in PLIST_FREE_ROWS if r != PLIST_DARK_TEXT_ROW]
    for (pt_rows, cs), b2_row in zip(packed, free):
        slots = [i for i in range(1, 16) if b2_row != PLIST_DARK_TEXT_ROW or i not in PLIST_DARK_TEXT]
        assert len(cs) <= len(slots), (b2_row, len(cs))
        at = dict(zip(sorted(cs), slots))
        palette[b2_row] = [0] * 16
        for colour, i in at.items():
            palette[b2_row][i] = colour
        for r in pt_rows:
            colour = [remap[r].get(c, c) for c in rows[r]]
            target[r] = (b2_row, {i: at[colour[i]] for i in range(1, 16) if colour[i] in cs})
    for i, colour in PLIST_DARK_TEXT.items():
        palette[PLIST_DARK_TEXT_ROW][i] = colour
    for r, b2_rows in PLIST_FIXED_ROWS.items():
        target[r] = (b2_rows[0], {i: i for i in range(16)})
        for b2_row in b2_rows:
            palette[b2_row] = rows[r]

    def recoloured(cell):
        if cell is None:
            return None
        px, r = cell
        b2_row, index = target[r]
        return tuple(index[i] if i else 0 for i in px), b2_row

    # The experience bar's characters first, in its cells' colours, at their numbers; before them, placeholders
    encoder = Encoder()
    for t in range(1, EXP_BAR_TILES.stop):
        px = recoloured((tiles[t], exp_row))[0] if t in EXP_BAR_TILES else (1,) * t + (2,) * (64 - t)
        encoder.tiles.append(px)
        encoder.index.setdefault(px, (t, 0, 0))
    for b2, (tw, th, cells) in maps.items():
        d, lz = unpack(files[b2])
        assert read_map(d)[:2] == (tw, th), b2
        write_map(d, tw, th, [encoder.entry(recoloured(c)) for c in cells])
        files[b2] = pack(d, lz)
    chars_data, chars_lz = unpack(files[B2_PLIST_CHARS])
    write_tiles(chars_data, encoder.tiles)
    files[B2_PLIST_CHARS] = pack(chars_data, chars_lz)

    pal_data, pal_lz = unpack(files[B2_PLIST_PALETTES])
    base = palette_base(pal_data)
    for b2_row, cs in palette.items():
        for i, colour in enumerate(cs):
            struct.pack_into("<H", pal_data, base + (b2_row * 16 + i) * 2, colour)
    for i, colour in PLIST_LABEL_OUTLINE.items():
        struct.pack_into("<H", pal_data, base + (PLIST_TEXT_ROW * 16 + i) * 2, colour)
    files[B2_PLIST_PALETTES] = pack(pal_data, pal_lz)
    return len(encoder.tiles), {r: t[0] for r, t in target.items()}


def platinum_cursor(files: list, platinum: PlatinumRom):
    """Black 2's key cursor in Platinum's look: its tile, its colours and its corners' places."""
    image = platinum.cursor()
    px = image.load()
    # A 16x16 sprite's four tiles, one after another
    tiles = [tuple(px[tx * 8 + i % 8, ty * 8 + i // 8] for i in range(64)) for ty in (0, 1) for tx in (0, 1)]
    d, lz = unpack(files[B2_CURSOR_CHARS])
    old = read_tiles(d)
    write_tiles(d, tiles + old[len(tiles):])
    files[B2_CURSOR_CHARS] = pack(d, lz)

    # Each corner's OAM: the L's corner on the point, or a pixel before it where the tile is flipped across
    d, lz = unpack(files[B2_CURSOR_CELLS])
    k = blocks(d)[b"KBEC"]
    count, attr_type = struct.unpack_from("<HH", d, k + 8)
    offset = struct.unpack_from("<I", d, k + 12)[0]
    size = 16 if attr_type == 1 else 8
    oams = k + 8 + offset + count * size
    for c in range(count):
        n, _, o = struct.unpack_from("<HHI", d, k + 8 + offset + c * size)
        for j in range(n):
            a0, a1 = struct.unpack_from("<HH", d, oams + o + 6 * j)
            x = -16 if a1 & 0x1000 else 0
            y = -16 if a1 & 0x2000 else 0
            struct.pack_into("<HH", d, oams + o + 6 * j, (a0 & 0xFF00) | (y & 0xFF), (a1 & 0xFE00) | (x & 0x1FF))
    files[B2_CURSOR_CELLS] = pack(d, lz)

    d, lz = unpack(files[B2_OBJ_PALETTES])
    base = palette_base(d)
    for row in CURSOR_ROWS:
        for i, colour in CURSOR_COLOURS.items():
            struct.pack_into("<H", d, base + (row * 16 + i) * 2, colour)
    files[B2_OBJ_PALETTES] = pack(d, lz)


def label_outlined(px, gx, gy) -> list:
    """A glyph's 16x16 pixels, its outline closed. Platinum's has it only on the letter's top and left (the next
    letter's left edge being the last's right one), which on Black 2's buttons reads as cut off below (the user's):
    it's added below and right of the letter too, wherever that's the glyph's outside (not into a letter's holes)."""
    grid = [[px[gx + x, gy + y] for x in range(16)] for y in range(16)]
    outside = set()
    todo = [(x, y) for x in range(16) for y in (0, 15)] + [(x, y) for x in (0, 15) for y in range(16)]
    while todo:
        x, y = todo.pop()
        if 0 <= x < 16 and 0 <= y < 16 and (x, y) not in outside and not grid[y][x]:
            outside.add((x, y))
            todo += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]

    def letter(x, y):
        return x >= 0 and y >= 0 and grid[y][x] in (1, 2)

    return [[3 if (x, y) in outside and (letter(x - 1, y) or letter(x, y - 1) or letter(x - 1, y - 1)) else grid[y][x]
             for x in range(16)] for y in range(16)]


def label_font(platinum: PlatinumRom) -> bytes:
    """Platinum's button font in Black 2's font format."""
    image, advances = platinum.font(FONT_SUBSCREEN)
    px = image.load()
    count = len(advances)
    chars = {}
    for line in platinum.charmap().splitlines():
        code, _, char = line.partition("=")
        if len(char) == 1 and 0 < int(code, 16) <= count:
            chars.setdefault(char, int(code, 16) - 1)
    for char, alias in LABEL_CHAR_ALIASES.items():
        if char not in chars and alias in chars:
            chars[char] = chars[alias]

    # The glyphs: each its left edge, width (as far as its outline reaches, which can be past its advance) and advance,
    # then its rows of pixels, 2 bits each, the first highest
    pixel_bytes = (LABEL_CELL_WIDTH * LABEL_CELL_HEIGHT * 2 + 7) // 8
    cells = b""
    for g in range(count):
        grid = label_outlined(px, (g % 16) * 16, (g // 16) * 16)
        bits = 0
        for y in range(LABEL_CELL_HEIGHT):
            for x in range(LABEL_CELL_WIDTH):
                bits = bits << 2 | LABEL_GLYPH_VALUES[grid[y][x]]
        bits <<= pixel_bytes * 8 - LABEL_CELL_WIDTH * LABEL_CELL_HEIGHT * 2
        width = max([advances[g]] + [x + 1 for row in grid for x in range(LABEL_CELL_WIDTH) if row[x]])
        cells += bytes((0, width, advances[g])) + bits.to_bytes(pixel_bytes, "big")
    glyph_info = struct.pack("<BBHbBBB", LABEL_CELL_WIDTH, LABEL_CELL_HEIGHT, 3 + pixel_bytes, 13, max(advances), 2, 0)

    # The widths: three common ones, then a class of 2 bits for each glyph (3 for any other), a table of 512 widths
    # by a hash of the glyph, and buckets for the hashes widths share
    common = [w for w, _ in Counter(advances).most_common(3)]
    common += [0] * (3 - len(common))
    classes = bytearray((count * 2 + 7) // 8)
    by_hash = {}
    for g, w in enumerate(advances):
        k = common.index(w) if w in common else 3
        classes[g * 2 // 8] |= k << (6 - g * 2 % 8)
        if k == 3:
            parity = ((g >> 12) ^ (g >> 11) ^ (g >> 10) ^ (g >> 9)) & 1
            by_hash.setdefault(((g & 0x1FF) ^ (parity << 3)) & 0x1FF, []).append((g, w))
    table, buckets, n = bytearray(512), b"", 0
    for h, entries in sorted(by_hash.items()):
        if len({w for _, w in entries}) == 1:
            table[h] = entries[0][1]
        else:
            n += 1
            table[h] = -n & 0xFF
            buckets += bytes((len(entries),)) + b"".join(bytes((g >> 8, g & 0xFF, w)) for g, w in entries)
    head = 16
    widths = (bytes(common) + b"\0" + struct.pack("<III", head, head + len(classes), head + len(classes) + 512)
              + bytes(classes) + bytes(table) + buckets)

    # The character map: every character, sorted, scanned
    pairs = sorted((ord(c), g) for c, g in chars.items() if ord(c) < 0x10000)
    cmap = (struct.pack("<HHHHI", pairs[0][0], pairs[-1][0], 2, 0, 0) + struct.pack("<H", len(pairs))
            + b"".join(struct.pack("<HH", c, g) for c, g in pairs))

    def block(magic, body):
        body += bytes(-(len(body)) % 4)
        return magic + struct.pack("<I", 8 + len(body)) + body

    cglp = block(b"PLGC", glyph_info + cells)
    cwdh = block(b"HDWC", widths)
    glyph_offset = 0x10 + 0x1C + 8
    width_offset = 0x10 + 0x1C + len(cglp) + 8
    map_offset = width_offset - 8 + len(cwdh) + 8
    question = chars.get("?", 0)
    # The line's height, as many rows as Black 2 draws of a glyph: its cell's, not the 16 its drawing reads
    finf = block(b"FNIF", struct.pack("<BBHBBBBIII", 0, LABEL_CELL_HEIGHT, question, 0, LABEL_CELL_WIDTH, 8, 1,
                                      glyph_offset, width_offset, map_offset))
    assert len(finf) == 0x1C
    cmap_block = block(b"PAMC", cmap)
    body = finf + cglp + cwdh + cmap_block
    return b"RTFN" + struct.pack("<HHIHH", 0xFEFF, 0x0101, 0x10 + len(body), 0x10, 4) + body


def build(arc: int, data: bytes, platinum: PlatinumRom) -> bytes:
    narc = nitro.NARC(data)
    if arc == 99:
        skin_party_list(narc.files, platinum)
    if arc == INFOWIN:
        d, lz = unpack(narc.files[INFOWIN_CHARS])
        write_tiles(d, [])
        narc.files[INFOWIN_CHARS] = pack(d, lz)
    if arc == 98:
        skin_bag(narc.files, PlatinumBag(platinum))
    if arc == 11:
        pt = Platinum(platinum)
        background = pt.background()
        cancel = cancel_button(pt)
        platinum_cursor(narc.files, platinum)
        assert len(narc.files) == LABEL_FONT_MEMBER, len(narc.files)
        narc.files.append(label_font(platinum))
        skin_set(narc.files, 0, pt, background, command_buttons(pt, {}), cancel=cancel,
                 back=command_buttons(pt, {"RUN": "CANCEL"}))
        for k, (words, removed) in enumerate(lower_screen_sets.SETS):
            skin_set(narc.files, lower_screen_sets.set_offset(k), pt, background,
                     command_buttons(pt, words, removed), removed, cancel=cancel,
                     back=command_buttons(pt, {**words, "RUN": "CANCEL"}, removed))
        write_palette(narc.files, MYSTERY_TILE, pt.move_palette["Mystery"])
    return narc.save()
