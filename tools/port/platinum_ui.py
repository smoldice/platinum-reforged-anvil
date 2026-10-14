#!/usr/bin/env python3
"""Black 2's battle interface made to feel like the rest of Platinum's, one change at a time on the user's say
(2026-10-11). Black 2's layout and animations stay; colours and a few of its tiles change.

- HP plates (archive 11, palettes 0x1af and 0x1b1 when dimmed): Platinum's solid olive-slate plate with a dark outline
  and white text, in place of Black 2's light gray checkered plate. The HP bar keeps its colours, as Platinum's does.
  The user kept these from a first try that also recoloured the message box, the lower screen and its status bar, and
  dropped the rest.
- EXP bar: a solid line, as Platinum's, where Black 2 draws it in columns of two alternating colours: its fill pieces
  (0x1b2) and its empty bar (0x1c5). The "EXP" label on the player's plate (0x1b6) is gone too, as in Platinum.
- Buttons without Black 2's checkered grid, in their fill colour: BAG, RUN and POKéMON (0x168), the move buttons
  (their type palettes, 464 to 482), the bag's (archive 98) and the party list's (archive 99).
- The lower screen's status bar (InfoWin, archive 49) without its IR, ONLINE and WIRELESS lights, which Platinum
  doesn't use: its clock and battery stay.

Which index draws what came from probe builds (each colour encoding its file, palette and index); the comments say
what each is. Colours are Platinum's, sampled from its own battle in the emulator.

Usage (from extract_assets.py, after the White 2 palettes): apply(arc, narc) changes the files of an archive in
ARCHIVES in place.
"""
import struct

import make_trainer_sprites as mts


def rgb(h: str) -> int:
    """A 15-bit colour from #rrggbb."""
    r, g, b = (int(h[i:i + 2], 16) >> 3 for i in (1, 3, 5))
    return r | g << 5 | b << 10


# Platinum's battle colours
PT_WHITE = "#f8f8f8"
PT_OUTLINE = "#283028"
PT_PLATE = "#697159"

# The plate's indices: 1 letters, 2 outlines, 3 and 13 the checkered body, 4 the letters' outline, 14 the shading
# the HP numbers' object draws in its empty digit slots, the plate's colour, so it doesn't show, 15 the bottom edge
# (and the empty EXP bar). 5 to 12 are the HP and EXP bars
PLATE = {1: PT_WHITE, 2: PT_OUTLINE, 3: PT_PLATE, 4: PT_OUTLINE, 13: PT_PLATE, 14: PT_PLATE, 15: PT_OUTLINE}
# The dimmed plates (0x1b1) as Black 2 dims them: about a third as bright
PLATE_DIM = {i: "#%02x%02x%02x" % tuple(int(c[k:k + 2], 16) // 3 for k in (1, 3, 5)) for i, c in PLATE.items()}

# Palette edits, by archive, file, palette and index: a colour, or another index whose colour it takes. A button's
# checkered grid is two indices, made one
PALETTES = {
    11: {
        0x1af: {p: PLATE for p in (0, 1, 2)},
        0x1b1: {0: PLATE_DIM},
        # BAG, POKéMON, RUN: 1 the fill, 3 and 5 its grid. The move screen's frame shares 3 and 5, solid too. Its
        # palettes 7 to 12 are the move buttons' until each move's own is loaded over them, as below
        0x168: {**{p: {3: 1, 5: 1} for p in (2, 3, 4)}, **{p: {4: 3, 5: 3} for p in range(7, 13)}},
        # The move buttons' palettes (btlv_input.c), one a move by its type (464 to 480), and their two other looks
        # (481, 482): 3 the fill, 5 its grid (and 4)
        **{fid: {0: {4: 3, 5: 3}} for fid in range(464, 483)},
    },
    # The bag's pocket buttons: 6 the fill, 5 its grid (palette 4, and 5 and 6 for their other looks); the bottom
    # bar's: 1, and 4 its grid; its action buttons' (palette 1): 6, and 4 its grid
    98: {2: {4: {5: 6}, 5: {5: 6}, 6: {5: 6}, 3: {4: 1}, 1: {4: 6}}},
    # The party list's slots: 6 the fill, 4 its grid, in every slot's palette (the lead's, the rest's, and their
    # selected and fainted looks), and its menu buttons' (SUMMARY, CHECK MOVES: palette 10)
    99: {20: {p: {4: 6} for p in (0, 1, 2, 5, 6, 7, 8, 10)}},
}

# The EXP bar's fill pieces in 0x1b2: tiles 32 (empty) to 40 (full), filled from the left a column a tile, the bar
# their rows 2 and 3. Black 2 draws them in alternating columns, 12 and 11 filled, 14 and 1 empty: now light blue on
# the outline's dark, as Platinum's blue line on its dark track
EXP_PIECES, EXP_ROWS = range(32, 41), (2, 3)
EXP_FILL, EXP_EMPTY = 11, 15
# The player's plate (0x1b6): "EXP" is on tiles 26 to 28, its right border on 29's first column, and tile 30 is the
# plate's body beside it, with its edges
EXP_LABEL_TILES, PLATE_BODY_TILE = (26, 27, 28, 29), 30
# The status bar's lights and their labels (archive 49, file 1): IR 6 and 7, ONLINE 8 and 9, WIRELESS 10 and 11,
# which no other tile uses; 1 is the bar
INFOWIN_LIGHTS, INFOWIN_BAR = range(6, 12), 1


def blocks(d: bytes) -> dict:
    header_size, count = struct.unpack_from("<HH", d, 12)
    off, found = header_size, {}
    for _ in range(count):
        magic, size = bytes(d[off:off + 4]), struct.unpack_from("<I", d, off + 4)[0]
        found[magic] = off
        off += size
    return found


def edit(data: bytes, change) -> bytes:
    """The file with change(d) made to it, keeping its compression."""
    compressed = data[0] in (0x10, 0x11)
    d = bytearray(mts.unlz(data) if compressed else data)
    change(d)
    return mts.lz10(bytes(d)) if compressed else bytes(d)


def recolour(palettes: dict):
    def change(d):
        t = blocks(d)[b"TTLP"]
        size, off = struct.unpack_from("<II", d, t + 0x10)
        base = t + 8 + off
        for p, colours in palettes.items():
            for i, c in colours.items():
                assert p * 32 + i * 2 < size
                value = struct.unpack_from("<H", d, base + p * 32 + c * 2)[0] if isinstance(c, int) else rgb(c)
                struct.pack_into("<H", d, base + p * 32 + i * 2, value)
    return change


class Tiles:
    """A 4bpp NCGR's tiles, pixel by pixel."""

    def __init__(self, d: bytearray):
        self.d = d
        r = blocks(d)[b"RAHC"]
        self.base = r + 8 + struct.unpack_from("<I", d, r + 28)[0]

    def get(self, t, x, y):
        return self.d[self.base + t * 32 + y * 4 + x // 2] >> (4 * (x & 1)) & 15

    def set(self, t, x, y, v):
        i = self.base + t * 32 + y * 4 + x // 2
        shift = 4 * (x & 1)
        self.d[i] = self.d[i] & ~(15 << shift) & 0xff | v << shift

    def copy(self, src, dest):
        self.d[self.base + dest * 32:self.base + dest * 32 + 32] = self.d[self.base + src * 32:self.base + src * 32 + 32]


def solid_exp_pieces(d):
    tiles = Tiles(d)
    for level, t in enumerate(EXP_PIECES):
        for y in EXP_ROWS:
            for x in range(8):
                tiles.set(t, x, y, EXP_FILL if x < level else EXP_EMPTY)


def solid_exp_bar(d):
    tiles = Tiles(d)
    for t in range(len(d[tiles.base:]) // 32):
        for y in EXP_ROWS:
            for x in range(8):
                if tiles.get(t, x, y) == 1:
                    tiles.set(t, x, y, EXP_EMPTY)


def remove_exp_label(d):
    tiles = Tiles(d)
    for t in EXP_LABEL_TILES:
        tiles.copy(PLATE_BODY_TILE, t)


def remove_infowin_lights(d):
    tiles = Tiles(d)
    for t in range(len(d[tiles.base:]) // 32):
        for y in range(8):
            for x in range(8):
                if tiles.get(t, x, y) in INFOWIN_LIGHTS:
                    tiles.set(t, x, y, INFOWIN_BAR)


TILES = {
    11: {0x1b2: solid_exp_pieces, 0x1c5: solid_exp_bar, 0x1b6: remove_exp_label},
    49: {1: remove_infowin_lights},
}

ARCHIVES = set(PALETTES) | set(TILES)


def apply(arc: int, narc) -> None:
    for fid, palettes in PALETTES.get(arc, {}).items():
        narc.files[fid] = edit(narc.files[fid], recolour(palettes))
    for fid, change in TILES.get(arc, {}).items():
        narc.files[fid] = edit(narc.files[fid], change)
