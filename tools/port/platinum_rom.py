#!/usr/bin/env python3
"""Platinum's own art for the port's converters, read from a Platinum ROM: a dump or the vanilla build's in the game's
build (extract_assets.py), the player's in Anvil, which makes the converted art on the player's machine so its download
carries none of Nintendo's. Each reader gives what the decomp's file has, byte for byte, as the converters used to
read it from there; `platinum_rom.py ROM GAME_DIR` checks every one against the decomp.

- trainer(cls, side): a trainer class's picture (front or back) as its front.png: the 256-colour palette, the frames
  stacked a row of 255 apart, each in its cell's box, the way nitrogfx's 8-bit path draws them (a horizontal flip
  lands one pixel right of a mirror, and the decomp's PNGs are made to match). With it, each cell's first OAM's
  place (front_cell.json) and the animations (front_anim.json, a frame's resultId numbering the distinct results in
  the order they first appear).
- file(path): a file as it is, like the decomp's res/prebuilt archives.
- font(member): a font of pl_font.narc as its PNG (16 glyphs a row, 2 bits a pixel) and its glyphs' widths.
- palette(archive, member): an NCLR's colours (15-bit), as the decomp's JASC palettes have them shifted down.
- cursor(): the battle's key cursor, as res/graphics/battle/interface/cursor.png.
- type_icon(member): a type icon of the battle's sprites, as res/graphics/battle/type_icons/<type>.png (32x16, its
  colours a row of type_icons/shared.pal: palette(BATTLE_SPRITES, TYPE_ICON_PALETTE)).
- move_palettes(): the move buttons' palettes by type, as src/overlay011/move_palettes.c has them.
- screen(archive, member): an NSCR's width, height and entries (nscr_screen), as the decomp's .NSCR has them: the
  Pokédex's area map for dex_map_art.py.
- charmap(): the decomp's character map (game/tools/msgenc/charmap.txt), which isn't the ROM's but a table of its
  text encoding; Anvil carries it.

The pictures and the font are laid out as the decomp's nitrogfx lays them out (game/tools/nitrogfx: MIT licence,
Copyright (c) 2015 YamaArashi, 2021-2026 red031000), whose notice goes with Anvil.
"""
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

import nitro
from nitro import unlz

ROOT = Path(__file__).resolve().parents[2]

# Platinum's trainer classes, by number (game/generated/trainer_classes.txt; extract_assets.py checks they agree),
# as the decomp's res/trainers/classes directories
TRAINER_CLASSES = [
    "player_male", "player_female", "youngster", "lass", "camper", "picnicker", "bug_catcher", "aroma_lady", "twins",
    "hiker", "battle_girl", "fisherman", "cyclist_male", "cyclist_female", "black_belt", "artist", "breeder_male",
    "breeder_female", "cowgirl", "jogger", "pokefan_male", "pokefan_female", "poke_kid", "young_couple",
    "ace_trainer_male", "ace_trainer_female", "waitress", "veteran", "ninja_boy", "dragon_tamer", "bird_keeper",
    "double_team", "rich_boy", "lady", "gentleman", "socialite", "beauty", "collector", "policeman", "ranger_male",
    "ranger_female", "scientist", "swimmer_male", "swimmer_female", "tuber_male", "tuber_female", "sailor",
    "sis_and_bro", "ruin_maniac", "psychic_male", "psychic_female", "pi", "guitarist", "ace_trainer_snow_male",
    "ace_trainer_snow_female", "skier_male", "skier_female", "roughneck", "clown", "worker", "school_kid_male",
    "school_kid_female", "leader_roark", "rival", "leader_byron", "elite_four_aaron", "elite_four_bertha",
    "elite_four_flint", "elite_four_lucian", "champion_cynthia", "belle_and_pa", "rancher", "commander_mars",
    "galactic_grunt_male", "leader_gardenia", "leader_wake", "leader_maylene", "leader_fantina", "leader_candice",
    "leader_volkner", "parasol_lady", "waiter", "interviewers", "cameraman", "reporter", "idol", "galactic_boss",
    "commander_jupiter", "commander_saturn", "galactic_grunt_female", "trainer_cheryl", "trainer_riley",
    "trainer_marley", "trainer_buck", "trainer_mira", "dp_player_male", "dp_player_female", "tower_tycoon", "maid",
    "hall_matron", "factory_head", "arcade_star", "castle_valet", "dp_player_male_2", "dp_player_female_2",
]
# The back pictures' order in trbgra.narc: the classes with one, then Diamond and Pearl's rival
# (game/tools/ordergen/trainer_graphics.py)
BACK_CLASSES = ["player_male", "player_female", "rival", "trainer_cheryl", "trainer_riley", "trainer_marley",
                "trainer_buck", "trainer_mira", "dp_player_male", "dp_player_female", "dp_rival"]
TRAINER_FILES = {"front": "poketool/trgra/trfgra.narc", "back": "poketool/trgra/trbgra.narc"}
# The Castle Valet's pixels are laid out by a cell file of their own (castle_valet/front_cell_key.json), not by
# the cells the game draws with: every frame, its OAMs as (x, y, shape, size, character)
CASTLE_VALET_KEY = [(-8, -40, 2, 2, 0), (-8, -8, 2, 2, 4), (8, -40, 2, 3, 8), (8, 24, 1, 2, 24), (-40, -40, 2, 3, 28),
                    (-40, 24, 1, 2, 44), (-8, 24, 0, 1, 48)]
OAM_SIZES = {(0, 0): (8, 8), (0, 1): (16, 16), (0, 2): (32, 32), (0, 3): (64, 64), (1, 0): (16, 8), (1, 1): (32, 8),
             (1, 2): (32, 16), (1, 3): (64, 32), (2, 0): (8, 16), (2, 1): (8, 32), (2, 2): (16, 32), (2, 3): (32, 64)}
# The battle's sprites (game/res/graphics/battle/sprites.order): the interface's palette (interface/shared.pal),
# and the key cursor's picture, then its cells (interface/cursor.png, cursor_cell.json)
BATTLE_SPRITES = "battle/graphic/pl_batt_obj.narc"
INTERFACE_PALETTE, CURSOR = 72, 250
# and the type icons' palette, whose ??? colour mystery_type.py takes, and the ??? icon (type_icons/shared.pal,
# type_icons/mystery.png)
TYPE_ICON_PALETTE, MYSTERY_ICON = 74, 236
TYPE_ICON_SIZE = (32, 16)
# The fonts (game/res/fonts/pl_font.order)
FONTS = "graphic/pl_font.narc"
FONT_SUBSCREEN = 2
# The move buttons' palettes in overlay 11, one after another in the order the linker placed them (the same in
# both revisions)
MOVE_PALETTES_OVERLAY, MOVE_PALETTES_AT = 11, 0x14C
MOVE_PALETTE_NAMES = ["Normal", "None", "Dark", "Dragon", "Ice", "Psychic", "Electric", "Grass", "Water", "Fire",
                      "Mystery", "Steel", "Ghost", "Bug", "Rock", "Ground", "Poison", "Flying", "Fighting"]
# The Pokédex's art (game/res/graphics/pokedex/pokedex.order), whose area map dex_map_art.py converts
POKEDEX_ART = "resource/eng/zukan/zukan.narc"
# The decomp's character map, beside this file's repo or in Anvil's
CHARMAP = ROOT / "game/tools/msgenc/charmap.txt"


@dataclass
class Oam:
    x: int
    y: int
    width: int
    height: int
    char: int
    hflip: bool = False
    vflip: bool = False


@dataclass
class Cell:
    box: tuple  # (min x, min y, max x, max y)
    oams: list


@dataclass
class Picture:
    """A trainer's picture: as front.png, each cell's first OAM's place (or None), and the animations as lists of
    (frameDelay, resultId)."""
    image: Image.Image
    shifts: list
    sequences: list


def nitro_blocks(data: bytes) -> dict:
    """A Nitro file's blocks, by magic, without their headers."""
    count = struct.unpack_from("<H", data, 0xE)[0]
    offset, blocks = struct.unpack_from("<H", data, 0xC)[0], {}
    for _ in range(count):
        magic, size = bytes(data[offset:offset + 4]), struct.unpack_from("<I", data, offset + 4)[0]
        blocks[magic] = bytes(data[offset + 8:offset + size])
        offset += size
    return blocks


def ncgr_chars(data: bytes) -> bytes:
    block = nitro_blocks(data)[b"RAHC"]
    size, offset = struct.unpack_from("<II", block, 0x10)
    return block[offset:offset + size]


def nclr_colours(data: bytes) -> list:
    block = nitro_blocks(data)[b"TTLP"]
    size, offset = struct.unpack_from("<II", block, 0x8)
    raw = block[offset:offset + size]
    return [struct.unpack_from("<H", raw, i * 2)[0] for i in range(len(raw) // 2)]


def nscr_screen(data: bytes):
    """An NSCR's screen: (width, height in pixels, its entries: each a u16 of tile, flips and palette row)."""
    block = nitro_blocks(data)[b"NRCS"]
    width, height, _, _, size = struct.unpack_from("<HHHHI", block, 0)
    return width, height, list(struct.unpack_from(f"<{size // 2}H", block, 12))


def rgb(colour: int) -> tuple:
    """A 15-bit colour as the decomp's PNGs and palettes have it."""
    return tuple((colour >> shift & 31) * 255 // 31 for shift in (0, 5, 10))


def ncer_cells(data: bytes):
    """The cells, the mapping's bytes per character name, and each cell's VRAM transfer offset (or None)."""
    block = nitro_blocks(data)[b"KBEC"]
    count, attr, cell_offset, mapping, vram_offset = struct.unpack_from("<HHIII", block, 0)
    entry = 16 if attr & 1 else 8
    oam_base = cell_offset + count * entry
    cells = []
    for i in range(count):
        n, cell_attr, oam_offset = struct.unpack_from("<HHI", block, cell_offset + i * entry)
        assert attr & 1, "cells without boxes"
        max_x, max_y, min_x, min_y = struct.unpack_from("<hhhh", block, cell_offset + i * entry + 8)
        oams = []
        for k in range(n):
            a0, a1, a2 = struct.unpack_from("<HHH", block, oam_base + oam_offset + k * 6)
            w, h = OAM_SIZES[(a0 >> 14, a1 >> 14)]
            rs = a1 >> 9 & 31
            oams.append(Oam(x=(a1 & 0x1FF) - (512 if a1 & 0x100 else 0), y=(a0 & 0xFF) - (256 if a0 & 0x80 else 0),
                            width=w, height=h, char=a2 & 0x3FF, hflip=bool(cell_attr >> 8 & 1 and rs & 8),
                            vflip=bool(cell_attr >> 9 & 1 and rs & 16)))
        cells.append(Cell((min_x, min_y, max_x, max_y), oams))
    transfers = [None] * count
    if vram_offset:
        array = struct.unpack_from("<I", block, vram_offset + 4)[0]
        transfers = [struct.unpack_from("<I", block, vram_offset + array + i * 8)[0] for i in range(count)]
    return cells, 32 << mapping, transfers


def nanr_sequences(data: bytes) -> list:
    block = nitro_blocks(data)[b"KNBA"]
    count, _, seq_offset, frame_offset = struct.unpack_from("<HHII", block, 0)
    sequences, results = [], []
    for s in range(count):
        frames_, _, _, _, _, first = struct.unpack_from("<HHHHII", block, seq_offset + s * 16)
        frames = []
        for f in range(frames_):
            result, delay = struct.unpack_from("<IH", block, frame_offset + first + f * 8)
            if result not in results:
                results.append(result)
            frames.append((delay, results.index(result)))
        sequences.append(frames)
    return sequences


def snap(v: int) -> int:
    """nitrogfx's SnapToTile: to the nearest multiple of 8."""
    d = v % 8
    return v - d if d < 4 else v + 8 - d


def draw_cells(chars: bytes, cells: list, char_bytes: int, transfers: list) -> bytes:
    """nitrogfx's ApplyCellsToImage to a PNG, on its 8-bit path: (width, height, pixels)."""
    shown = [i for i, c in enumerate(cells) if c.oams]
    width = max(snap(cells[i].box[2] - cells[i].box[0]) for i in shown)
    height = sum(snap(cells[i].box[3] - cells[i].box[1]) + 1 for i in shown) - 1
    pixels = bytearray([255]) * (width * height)
    scan, drawn = -1, set()
    for i in shown:
        cell = cells[i]
        scan += 1
        min_x, min_y = cell.box[:2]
        cell_height = snap(cell.box[3] - min_y)
        unique = len(cell.oams)
        for oam in cell.oams:
            x, y = snap(oam.x - min_x), snap(oam.y - min_y) + scan
            offset = oam.char * char_bytes + (transfers[i] or 0)
            if offset in drawn:
                unique -= 1
                continue
            drawn.add(offset)
            tiles_wide, tiles_high = oam.width // 8, oam.height // 8
            for t in range(tiles_wide * tiles_high):
                tx, ty = t % tiles_wide, t // tiles_wide
                tile = chars[offset + t * 32:offset + t * 32 + 32]
                for row in range(8):
                    py = y + (8 * (tiles_high - ty) - row - 1 if oam.vflip else 8 * ty + row)
                    for col in range(8):
                        px = x + (8 * (tiles_wide - tx) - col if oam.hflip else 8 * tx + col)
                        index = py * width + px
                        if 0 <= index < len(pixels):
                            pixels[index] = tile[row * 4 + col // 2] >> 4 * (col & 1) & 15
        if unique == 0:
            height -= cell_height + 1
            scan -= 1
        else:
            scan += cell_height
    return width, height, bytes(pixels[:width * height])


class PlatinumRom:
    """Platinum's art from its ROM: read_file(path) gives a file's bytes, read_overlay(id) an ARM9 overlay as it runs
    (ndspy's, or Anvil's Rom's file_by_path and overlay)."""

    def __init__(self, read_file, read_overlay):
        self.file = read_file
        self.overlay = read_overlay
        self._narcs = {}

    @classmethod
    def open(cls, path):
        import ndspy.rom
        rom = ndspy.rom.NintendoDSRom.fromFile(path)
        return cls(rom.getFileByName, lambda i: rom.loadArm9Overlays([i])[i].data)

    def narc(self, path: str) -> list:
        if path not in self._narcs:
            self._narcs[path] = nitro.NARC(self.file(path)).files
        return self._narcs[path]

    def trainer(self, cls: str, side: str) -> Picture:
        files = self.narc(TRAINER_FILES[side])
        base = 5 * (TRAINER_CLASSES if side == "front" else BACK_CLASSES).index(cls)
        cells, char_bytes, transfers = ncer_cells(files[base + 2])
        layout = cells
        if cls == "castle_valet":
            layout = [Cell((-40, -40, 39, 39), [Oam(x, y, *OAM_SIZES[(shape, size)], char)
                                                for x, y, shape, size, char in CASTLE_VALET_KEY]) if c.oams else c
                      for c in cells]
        width, height, pixels = draw_cells(ncgr_chars(files[base]), layout, char_bytes, transfers)
        image = Image.frombytes("P", (width, height), pixels)
        palette = [v for c in nclr_colours(files[base + 1]) for v in rgb(c)]
        image.putpalette((palette + [0] * 768)[:768])
        shifts = [(c.oams[0].x, c.oams[0].y) if c.oams else None for c in cells]
        return Picture(image, shifts, nanr_sequences(files[base + 3]))

    def palette(self, archive: str, member: int) -> list:
        return nclr_colours(unlz(self.narc(archive)[member]))

    def screen(self, archive: str, member: int):
        """An NSCR of an archive: (width, height, entries), nscr_screen's."""
        return nscr_screen(unlz(self.narc(archive)[member]))

    def cursor(self) -> Image.Image:
        files = self.narc(BATTLE_SPRITES)
        cells, char_bytes, transfers = ncer_cells(unlz(files[CURSOR + 1]))
        width, height, pixels = draw_cells(ncgr_chars(unlz(files[CURSOR])), cells, char_bytes, transfers)
        return Image.frombytes("P", (width, height), pixels)

    def type_icon(self, member: int) -> Image.Image:
        width, height = TYPE_ICON_SIZE
        chars = ncgr_chars(unlz(self.narc(BATTLE_SPRITES)[member]))
        pixels = bytearray(width * height)
        for i, byte in enumerate(chars[:width * height // 2]):
            tile, at = divmod(i * 2, 64)
            x, y = tile % (width // 8) * 8 + at % 8, tile // (width // 8) * 8 + at // 8
            pixels[y * width + x], pixels[y * width + x + 1] = byte & 15, byte >> 4
        return Image.frombytes("P", TYPE_ICON_SIZE, bytes(pixels))

    def font(self, member: int):
        """(the font's PNG, its glyphs' widths), as nitrogfx reads an NFGR: each glyph 16x16, four 8x8 tiles of 2
        bits a pixel, each tile row's two bytes swapped, the first pixel highest."""
        data = self.narc(FONTS)[member]
        header, widths_at, count = struct.unpack_from("<III", data, 0)
        rows = (count + 15) // 16
        pixels = bytearray(256 * rows * 16)
        at = header
        for glyph in range(count):
            gx, gy = glyph % 16 * 16, glyph // 16 * 16
            for tile in range(4):
                for y in range(8):
                    bits = data[at + 1] << 8 | data[at]
                    at += 2
                    for x in range(8):
                        pixels[(gy + tile // 2 * 8 + y) * 256 + gx + tile % 2 * 8 + x] = bits >> (14 - 2 * x) & 3
        return Image.frombytes("P", (256, rows * 16), bytes(pixels)), list(data[widths_at:widths_at + count])

    def move_palettes(self) -> dict:
        code = self.overlay(MOVE_PALETTES_OVERLAY)
        return {name: list(struct.unpack_from("<16H", code, MOVE_PALETTES_AT + 32 * i))
                for i, name in enumerate(MOVE_PALETTE_NAMES)}

    @staticmethod
    def charmap() -> str:
        base = Path(getattr(sys, "_MEIPASS", ""))
        path = base / "charmap.txt" if hasattr(sys, "_MEIPASS") else CHARMAP
        return path.read_text(encoding="utf-8")


def check(rom: PlatinumRom, game: Path) -> int:
    """Every reader against the decomp's files; the number that differ."""
    import json
    bad = 0
    classes = game / "res/trainers/classes"
    names = [n.removeprefix("TRAINER_CLASS_").lower()
             for n in (game / "generated/trainer_classes.txt").read_text().split()]
    if names != TRAINER_CLASSES:
        print("TRAINER_CLASSES differs from generated/trainer_classes.txt")
        bad += 1
    backs = [n for n in names if (classes / n / "back.png").exists()] + ["dp_rival"]
    if backs != BACK_CLASSES:
        print("BACK_CLASSES differs from the classes with a back.png")
        bad += 1
    for side, order in (("front", TRAINER_CLASSES), ("back", BACK_CLASSES)):
        for cls in order:
            picture = rom.trainer(cls, side)
            png = Image.open(classes / cls / f"{side}.png")
            cells = json.loads((classes / cls / f"{side}_cell.json").read_text())["cells"]
            anim = json.loads((classes / cls / f"{side}_anim.json").read_text())["sequences"]
            problems = []
            if (png.size, png.tobytes()) != (picture.image.size, picture.image.tobytes()):
                problems.append("pixels")
            if png.getpalette() != picture.image.getpalette():
                problems.append("palette")
            if [(c["OAM"][0]["Attr1"]["XCoordinate"], c["OAM"][0]["Attr0"]["YCoordinate"]) if c["OAM"] else None
                    for c in cells] != picture.shifts:
                problems.append("cells")
            if [[(f["frameDelay"], f["resultId"]) for f in s["frameData"]] for s in anim] != picture.sequences:
                problems.append("animations")
            if problems:
                print(f"{side} {cls}: {', '.join(problems)} differ")
                bad += 1
    print(f"trainer pictures: {len(TRAINER_CLASSES) + len(BACK_CLASSES)} checked")

    def differs(what, ok):
        nonlocal bad
        if not ok:
            print(f"{what} differs")
            bad += 1

    for name in ("pl_batt_bg", "b_bag_gra", "pl_b_plist_gra"):
        differs(name, rom.file(f"battle/graphic/{name}.narc")
                == (game / f"res/prebuilt/battle/graphic/{name}.narc").read_bytes())
    image, widths = rom.font(FONT_SUBSCREEN)
    png = Image.open(game / "res/fonts/font_subscreen.png")
    differs("font_subscreen.png", (png.size, png.tobytes()) == (image.size, image.tobytes()))
    metadata = json.loads((game / "res/fonts/font_subscreen.json").read_text())
    differs("font_subscreen.json", metadata["glyphWidths"] == widths)
    jasc = (game / "res/graphics/battle/interface/shared.pal").read_text().splitlines()[3:]
    colours = rom.palette(BATTLE_SPRITES, INTERFACE_PALETTE)
    differs("shared.pal", [tuple(int(v) >> 3 for v in line.split()) for line in jasc[:len(colours)]]
            == [(c & 31, c >> 5 & 31, c >> 10 & 31) for c in colours])
    png = Image.open(game / "res/graphics/battle/interface/cursor.png")
    differs("cursor.png", (png.size, png.tobytes()) == (rom.cursor().size, rom.cursor().tobytes()))
    png = Image.open(game / "res/graphics/battle/type_icons/mystery.png")
    icon = rom.type_icon(MYSTERY_ICON)
    differs("type_icons/mystery.png", (png.size, png.tobytes()) == (icon.size, icon.tobytes()))
    jasc = (game / "res/graphics/battle/type_icons/shared.pal").read_text().splitlines()[3:]
    colours = rom.palette(BATTLE_SPRITES, TYPE_ICON_PALETTE)
    differs("type_icons/shared.pal", [tuple(int(v) >> 3 for v in line.split()) for line in jasc[:len(colours)]]
            == [(c & 31, c >> 5 & 31, c >> 10 & 31) for c in colours])
    import re
    text = (game / "src/overlay011/move_palettes.c").read_text(encoding="utf-8")
    source = {m[1]: [int(r) | int(g) << 5 | int(b) << 10
                     for r, g, b in re.findall(r"RGB\((\d+), (\d+), (\d+)\)", m[2])][:16]
              for m in re.finditer(r"sMovePalette(\w+)\[\] = \{(.*?)\};", text, re.S) if m[1] != "Table"}
    differs("move_palettes.c", source == rom.move_palettes())
    # The Pokédex's area map and its hidden places' pieces (dex_map_art.py), as the decomp has the screens
    for member, name in ((64, "area_map"), (65, "map_newmoon_island"), (66, "map_seabreak_path"),
                         (67, "map_fullmoon_island"), (68, "map_spring_path")):
        differs(f"{name}.NSCR", rom.screen(POKEDEX_ART, member)
                == nscr_screen((game / f"res/graphics/pokedex/{name}.NSCR").read_bytes()))
    return bad


if __name__ == "__main__":
    differ = check(PlatinumRom.open(sys.argv[1]), Path(sys.argv[2]))
    print("all match" if not differ else f"{differ} differ")
    sys.exit(1 if differ else 0)
