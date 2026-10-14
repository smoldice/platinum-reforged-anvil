#!/usr/bin/env python3
"""Black 2's lower screen with Platinum's buttons for the battles that have other ones, for gen5_battle.c.

The command screen's labels (FIGHT!, BAG, POKéMON, RUN) are drawn into its BG tiles (archive 11: characters 0x166,
maps 0x169-0x17c, on the sub screen's BG0 and BG1). Black 2 picks the lower screen's files through one function,
BtlvInput_FileId, which adds 0x86 for Pokéstar Studios' set. This appends more sets of every file it picks
(0x166-0x23b, the target screen's maps among them), copies with Platinum's buttons (SETS, in order from file 572):

- the Safari Zone's: BALL, BAIT, MUD and RUN;
- Pal Park's: BALL and RUN, without the BAG and POKéMON buttons;
- the Battle Frontier's: without the BAG button, as Platinum's Frontier has none.

gen5_battle.c makes BtlvInput_FileId add a set's offset for these battles (set_offset). The letters are the labels'
own, cut out of the files at extraction (B, A, M, U, I and T, the large ones stretched from the small ones), except D
and L, which Black 2's labels don't have and which LETTERS draws in their style. A file a set doesn't change shares the
original's data in the archive.

The game data stays in the user's ROM: nothing this makes is committed.
"""
import struct

import nitro

ARCHIVE = 11
# The files BtlvInput_FileId gives an offset to: the command and move screens' 0x166-0x17e, the target screen's maps
# (384-419) and 0x23b. A set must hold them all, since the offset applies to each
FIRST, LAST = 0x166, 0x23B
CHARS = 0x166
# The archive's length in Black 2, after which the sets go
ARCHIVE_FILES = 572
SET_SIZE = LAST - FIRST + 1

# The maps on BG0 and BG1, which use CHARS, and those showing the labels as the single battle's command screen does:
# BG0's (BAG, RUN, POKéMON) and BG1's (FIGHT!)
BG0_MAPS = range(0x169, 0x174)
BG1_MAPS = range(0x174, 0x17D)
MAP_BUTTONS = 0x169
MAP_FIGHT = 0x174
BACKGROUND = 1  # the color behind the letters

# Each label: its map, the rows of its letters, the columns of its old word, the colors of a letter and of its
# shading. Small labels have letters of 8 rows, FIGHT! of 10
SMALL = ("small", 0xF, 0xE)
LARGE = ("large", 0x9, 0x8)
LABELS = {
    "FIGHT!": (MAP_FIGHT, 91, 102, 157, LARGE),
    "BAG": (MAP_BUTTONS, 164, 24, 53, SMALL),
    "POKéMON": (MAP_BUTTONS, 164, 191, 245, SMALL),
    "RUN": (MAP_BUTTONS, 176, 113, 142, SMALL),
}
# POKéMON's accent cuts the button's border above it, which goes back without it
ACCENT = ("POKéMON", 160, 216, 219)
# The buttons a set can leave out, by their palette row on BG0
BUTTON_ROWS = {"BAG": 2, "POKéMON": 3}
# Each set: its words for the labels, and the buttons it leaves out
SETS = [
    ({"FIGHT!": "BALL", "BAG": "BAIT", "POKéMON": "MUD", "RUN": "RUN"}, ()),
    ({"FIGHT!": "BALL", "BAG": "BAG", "POKéMON": "POKéMON", "RUN": "RUN"}, ("BAG", "POKéMON")),
    ({"FIGHT!": "FIGHT!", "BAG": "BAG", "POKéMON": "POKéMON", "RUN": "RUN"}, ("BAG",)),
]


def set_offset(index):
    """What BtlvInput_FileId adds for set `index` (gen5_battle.c's G5_LOWER_SCREEN_*)."""
    return ARCHIVE_FILES + index * SET_SIZE - FIRST

# Letters the labels don't have, in their style: X a letter, + its shading
LETTERS = {
    "D": ["XXXXX+.",
          "XXXXXX+",
          "XX..+XX",
          "XX...XX",
          "XX...XX",
          "XX..+XX",
          "XXXXXX+",
          "XXXXX+."],
    "L": ["XX....",
          "XX....",
          "XX....",
          "XX....",
          "XX....",
          "XX....",
          "XXXXXX",
          "XXXXXX"],
}
# A large letter is a small one with its third and sixth rows doubled, and the other way round
STRETCH = [0, 1, 2, 2, 3, 4, 5, 5, 6, 7]
SHRINK = [0, 1, 2, 4, 5, 6, 8, 9]


def block(data, magic):
    off = 16
    while off + 8 <= len(data):
        size = struct.unpack_from("<I", data, off + 4)[0]
        if data[off:off + 4] == magic:
            return off
        if size == 0:
            break
        off += size
    raise KeyError(magic)


class Chars:
    """An NCGR's 4bpp tiles, as bytearrays of 64 indices."""

    def __init__(self, data):
        self.data = bytearray(data)
        b = block(self.data, b"RAHC")
        size, off = struct.unpack_from("<II", self.data, b + 0x18)
        self.start = b + 8 + off
        self.count = size // 32

    def tile(self, i):
        raw = self.data[self.start + i * 32:self.start + i * 32 + 32]
        return bytearray(raw[p // 2] >> (4 * (p & 1)) & 15 for p in range(64))

    def set_tile(self, i, pixels):
        for p in range(0, 64, 2):
            self.data[self.start + i * 32 + p // 2] = pixels[p] | pixels[p + 1] << 4


class Screen:
    """An NSCR's 512x512 map, in 32x32 blocks."""

    def __init__(self, data):
        self.data = bytearray(data)
        b = block(self.data, b"NRCS")
        self.width, self.height = struct.unpack_from("<HH", self.data, b + 8)
        self.start = b + 0x14

    def offset(self, tx, ty):
        blk = tx // 32 + ty // 32 * (self.width // 256)
        return self.start + blk * 0x800 + (ty % 32 * 32 + tx % 32) * 2

    def cells(self):
        return [(tx, ty) for ty in range(self.height // 8) for tx in range(self.width // 8)]

    def get(self, tx, ty):
        return struct.unpack_from("<H", self.data, self.offset(tx, ty))[0]

    def set(self, tx, ty, entry):
        struct.pack_into("<H", self.data, self.offset(tx, ty), entry)


def cell_pixels(chars, entry):
    t = chars.tile(entry & 0x3FF)
    hf, vf = entry >> 10 & 1, entry >> 11 & 1
    return bytearray(t[(7 - y if vf else y) * 8 + (7 - x if hf else x)] for y in range(8) for x in range(8))


class Canvas:
    """A map's pixels as palette indices, for the cells a label covers."""

    def __init__(self, chars, screen):
        self.chars, self.screen, self.cells = chars, screen, {}

    def cell(self, tx, ty):
        if (tx, ty) not in self.cells:
            self.cells[(tx, ty)] = cell_pixels(self.chars, self.screen.get(tx, ty))
        return self.cells[(tx, ty)]

    def get(self, x, y):
        return self.cell(x // 8, y // 8)[y % 8 * 8 + x % 8]

    def put(self, x, y, color):
        self.cell(x // 8, y // 8)[y % 8 * 8 + x % 8] = color


def cut_letters(canvas, word, top, x0, x1, height, letter, shade):
    """The label's letters, split at its empty columns: {letter: rows of 'X', '+' and '.'}."""
    columns = [x for x in range(x0, x1 + 1) if any(canvas.get(x, y) != BACKGROUND for y in range(top, top + height))]
    runs = []
    for x in columns:
        if runs and x == runs[-1][-1] + 1:
            runs[-1].append(x)
        else:
            runs.append([x])
    names = [c for c in word.replace("é", "E")]
    assert len(runs) == len(names), (word, len(runs))
    out = {}
    for name, run in zip(names, runs):
        rows = []
        for y in range(top, top + height):
            rows.append("".join({letter: "X", shade: "+"}.get(canvas.get(x, y), ".") for x in run))
        out[name] = rows
    gaps = sorted(b[0] - a[-1] - 1 for a, b in zip(runs, runs[1:]))
    return out, gaps[len(gaps) // 2]


def draw_word(canvas, word, letters, top, x0, x1, gap, letter, shade):
    """Clears the old word's columns and writes the new one, centered on them."""
    height = len(next(iter(letters.values())))
    for y in range(top, top + height):
        for x in range(x0, x1 + 1):
            canvas.put(x, y, BACKGROUND)
    width = sum(len(letters[c][0]) for c in word) + gap * (len(word) - 1)
    x = (x0 + x1 + 1 - width) // 2
    for c in word:
        for dy, row in enumerate(letters[c]):
            for dx, p in enumerate(row):
                if p != ".":
                    canvas.put(x + dx, top + dy, letter if p == "X" else shade)
        x += len(letters[c][0]) + gap


class Tiles:
    """New tiles, in the character file's empty tiles that no map uses, from the last one down."""

    def __init__(self, chars, screens):
        used = {s.get(tx, ty) & 0x3FF for s in screens for tx, ty in s.cells()}
        self.chars = chars
        self.free = [i for i in range(chars.count - 1, 0, -1) if i not in used and not any(chars.tile(i))]
        self.made = {}

    def get(self, pixels):
        key = bytes(pixels)
        if key not in self.made:
            i = self.free.pop(0)
            self.chars.set_tile(i, pixels)
            self.made[key] = i
        return self.made[key]


def button_pattern(screen, row):
    """A button of the command screen as the reference map shows it: its cells on screen, by palette row."""
    cells = [(tx, ty, screen.get(tx, ty)) for ty in range(24) for tx in range(32)
             if screen.get(tx, ty) >> 12 == row and screen.get(tx, ty) & 0x3FF]
    ox, oy = min(c[0] for c in cells), min(c[1] for c in cells)
    return [(tx - ox, ty - oy, entry) for tx, ty, entry in cells]


def find(screen, pattern):
    """Where a pattern of cells (tiles and flips, of any palette row) appears in a map."""
    cols, rows = screen.width // 8, screen.height // 8
    for ty in range(rows):
        for tx in range(cols):
            if all(tx + dx < cols and ty + dy < rows and screen.get(tx + dx, ty + dy) & 0xFFF == entry & 0xFFF
                   for dx, dy, entry in pattern):
                yield tx, ty


def relabel(chars, screens, words, hide):
    """Rewrites the labels LABELS names to words[...] in every map that shows them, and takes out the buttons `hide`
    names; returns how many maps changed."""
    tiles = Tiles(chars, screens.values())
    hidden = [button_pattern(screens[MAP_BUTTONS], BUTTON_ROWS[name]) for name in hide]
    small, large = {}, {}
    gaps = {}
    canvases = {MAP_BUTTONS: Canvas(chars, screens[MAP_BUTTONS]), MAP_FIGHT: Canvas(chars, screens[MAP_FIGHT])}
    for word, (map_id, top, x0, x1, (style, letter, shade)) in LABELS.items():
        found, gaps[word] = cut_letters(canvases[map_id], word, top, x0, x1, 10 if style == "large" else 8, letter,
                                        shade)
        (large if style == "large" else small).update(found)
    small.update(LETTERS)
    for c in "IT":
        small.setdefault(c, [large[c][r] for r in SHRINK])
    for c in set("BALDMU"):
        large.setdefault(c, [small[c][r] for r in STRETCH])

    # The new words on the reference maps
    for word, new in words.items():
        map_id, top, x0, x1, (style, letter, shade) = LABELS[word]
        canvas = canvases[map_id]
        if new != word:
            draw_word(canvas, new, large if style == "large" else small, top, x0, x1, gaps[word], letter, shade)
        if word == ACCENT[0] and new != word:
            for x in range(ACCENT[2], ACCENT[3] + 1):
                canvas.put(x, ACCENT[1], letter)
                for y in range(ACCENT[1] + 1, top):
                    canvas.put(x, y, BACKGROUND)

    # Each changed cell of a reference map, as a pattern to find in every map: (dx, dy, old entry, new tile)
    patterns = []
    for map_id, canvas in canvases.items():
        screen = screens[map_id]
        changed = [(tx, ty, px) for (tx, ty), px in canvas.cells.items() if px != cell_pixels(chars, screen.get(tx, ty))]
        if not changed:
            continue
        ox, oy = min(c[0] for c in changed), min(c[1] for c in changed)
        patterns.append([(tx - ox, ty - oy, screen.get(tx, ty), tiles.get(px)) for tx, ty, px in changed])

    count = 0
    for screen in screens.values():
        before = bytes(screen.data)
        # A button goes before its label changes, which would change its pattern
        for pattern in hidden:
            for tx, ty in list(find(screen, pattern)):
                for dx, dy, _ in pattern:
                    screen.set(tx + dx, ty + dy, 0)
        for pattern in patterns:
            for tx, ty in list(find(screen, [(dx, dy, old) for dx, dy, old, _ in pattern])):
                for dx, dy, old, new in pattern:
                    screen.set(tx + dx, ty + dy, screen.get(tx + dx, ty + dy) & 0xF000 | new)
        count += bytes(screen.data) != before
    return count


def save_shared(narc, files):
    """The archive with files appended, a file equal to an earlier one sharing its data, as NARCs allow."""
    fnt = bytes(narc_fnt(narc))
    image, entries, seen = bytearray(), [], {}
    for f in files:
        key = bytes(f)
        if key not in seen:
            while len(image) % 4:
                image.append(0xFF)
            seen[key] = (len(image), len(image) + len(f))
            image += f
        entries.append(seen[key])
    while len(image) % 4:
        image.append(0xFF)
    fat = struct.pack("<4sIHH", b"BTAF", 12 + 8 * len(entries), len(entries), 0)
    fat += b"".join(struct.pack("<II", s, e) for s, e in entries)
    img = struct.pack("<4sI", b"GMIF", 8 + len(image)) + image
    size = 16 + len(fat) + len(fnt) + len(img)
    return struct.pack("<4sHHIHH", b"NARC", 0xFFFE, 0x0100, size, 16, 3) + fat + fnt + img


def narc_fnt(data):
    off = block(data, b"BTNF")
    size = struct.unpack_from("<I", data, off + 4)[0]
    return data[off:off + size]


def build(data: bytes) -> bytes:
    """Archive 11 with the sets of SETS appended."""
    narc = nitro.NARC(data)
    assert len(narc.files) == ARCHIVE_FILES, len(narc.files)
    files = list(narc.files)
    for index, (words, hide) in enumerate(SETS):
        chars = Chars(files[CHARS])
        screens = {i: Screen(files[i]) for i in (*BG0_MAPS, *BG1_MAPS)}
        changed = relabel(chars, screens, words, hide)
        print(f"lower screen set {index} (offset {set_offset(index):#x}): {changed} maps changed")
        for i in range(FIRST, LAST + 1):
            files.append(bytes(chars.data) if i == CHARS else bytes(screens[i].data) if i in screens else files[i])
    return save_shared(data, files)
