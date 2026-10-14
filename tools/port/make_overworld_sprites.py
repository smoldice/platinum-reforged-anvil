#!/usr/bin/env python3
"""Black 2's overworld sprites for the trainer classes both games have, as Platinum's sprite sheets: the user chose
them, as for their battle sprites (gen5_trainer.c). Beauty, Veteran and Roughneck keep Platinum's, as the user chose,
and so do the classes the user retextured Black 2's battle sprites of (CUSTOM_CLASSES), but with the CUSTOM SPRITES
option off, when they battle as Black 2's own sprites. Writes game/gen5/field_sprites/gen5_NAME.png, which
the gen5 build packs after Platinum's sprites, beside res/graphics/field_sprites/npc/NAME.png, for the TRAINERS and
CUSTOM SPRITES options to choose between (res/graphics/field_sprites/meson.build, object_event_gfx_data.c). Never
committed.

Black 2's object codes are the ones its trainers of each class use on its maps (a/1/2/6: an NPC's script 3000 or
5000 plus the trainer's ID, whose class is the first byte after the kind in a/0/9/1); a code's model in a/0/4/8 is
its record's first resource in a/0/4/7. The Maid's, which no map places, is the green-dressed one in a white bonnet
that matches her battle sprite.

A model's texture holds the frames, 32x32 at 4 bits per pixel with one palette. Black 2's walking NPCs have 12: up,
down, left and right, each standing then two steps. Most trainers have 7: up and down standing then one step, which
the game mirrors for the other, and left standing then two steps, mirrored for right. Platinum's sheet is 16 frames
of 32x32, one above the other: up, down, left, right, each standing, a step, standing, the other step.

Platinum gives Pokémon Rangers the Ace Trainers' sprites and both Psychics one; Black 2 has their own, so the gen5 build
adds ranger_m, ranger_f and psychic_f as sprites of their own (include/gen5/gen5_overworld.h, NEW).

Usage (from extract_assets.py): make_overworld_sprites.write(rom, platinum_dir)
"""
import re
import struct
from pathlib import Path

import nitro
from PIL import Image

# Platinum's sheet (npc/NAME.png) or a new one, and Black 2's object code
SPRITES = {
    "ace_trainer_f": 31,
    "ace_trainer_m": 30,
    "artist": 28,
    "black_belt": 46,
    "cyclist_f": 39,
    "cyclist_m": 38,
    "fisherman": 63,
    "gentleman": 44,
    "guitarist": 296,
    "hiker": 64,
    "lady": 17,
    "lass": 15,
    "maid": 65,
    "parasol_lady": 84,
    "pokefan_f": 26,
    "pokefan_m": 24,
    "pokemon_breeder_f": 35,
    "pokemon_breeder_m": 34,
    "psychic": 183,
    "psychic_f": 184,
    "ranger_f": 37,
    "ranger_m": 36,
    "rich_boy": 13,
    "school_kid_f": 16,
    "school_kid_m": 12,
    "socialite": 45,
    "swimmer_f": 41,
    "swimmer_m": 40,
    "twin": 9,
    "waiter": 42,
    "waitress": 43,
    "worker": 155,
    "youngster": 11,
}
# The classes whose Black 2 sheet only shows with the CUSTOM SPRITES option off (object_event_gfx_data.c)
CUSTOM_CLASSES = {"ace_trainer_f", "ace_trainer_m", "fisherman", "lass", "waitress", "worker"}

# The sprites Platinum doesn't have, which keep their names
NEW = {"psychic_f", "ranger_f", "ranger_m"}

CODES_ARCHIVE = "a/0/4/7"
MODELS_ARCHIVE = "a/0/4/8"
CODE_RECORD = 28
FRAME = 32

# Black 2's frame for each of Platinum's 16, and whether it is mirrored
FRAMES_12 = [(3 * d + f, False) for d in range(4) for f in (0, 1, 0, 2)]
FRAMES_7 = [
    (0, False), (1, False), (0, False), (1, True),
    (2, False), (3, False), (2, False), (3, True),
    (4, False), (5, False), (4, False), (6, False),
    (4, True), (5, True), (4, True), (6, True),
]


def nitro_dict(d: bytes, off: int) -> list:
    count = d[off + 1]
    entries = off + 4 + 8 + 4 * count
    entry_size = struct.unpack_from("<H", d, entries)[0]
    data = entries + 4
    names = data + entry_size * count
    return [(d[names + 16 * i:names + 16 * (i + 1)].rstrip(b"\0").decode("ascii"),
             d[data + entry_size * i:data + entry_size * (i + 1)]) for i in range(count)]


def frames(model: bytes):
    """The model's frames, in texture order, as rows of 4-bit pixels, and its palette as 8-bit RGB."""
    blocks = struct.unpack_from("<H", model, 14)[0]
    tex0 = next(model[o:] for o in (struct.unpack_from("<I", model, 16 + 4 * i)[0] for i in range(blocks))
                if model[o:o + 4] == b"TEX0")
    tex_info, tex_data = struct.unpack_from("<H", tex0, 0x0E)[0], struct.unpack_from("<I", tex0, 0x14)[0]
    pal_info, pal_data = struct.unpack_from("<II", tex0, 0x34)
    textures = []
    for name, entry in nitro_dict(tex0, tex_info):
        params = struct.unpack_from("<I", entry, 0)[0]
        width, height, fmt = 8 << (params >> 20 & 7), 8 << (params >> 23 & 7), params >> 26 & 7
        assert (width, height, fmt) == (FRAME, FRAME, 3), (name, width, height, fmt)
        start = tex_data + ((params & 0xFFFF) << 3)
        raw = tex0[start:start + FRAME * FRAME // 2]
        pixels = [raw[i // 2] >> (4 * (i & 1)) & 15 for i in range(FRAME * FRAME)]
        index = int(re.search(r"\.(\d+)$", name).group(1))
        textures.append((index, pixels))
    textures.sort()
    pal_off = pal_data + (struct.unpack_from("<H", nitro_dict(tex0, pal_info)[0][1], 0)[0] << 3)
    palette = []
    for i in range(16):
        c = struct.unpack_from("<H", tex0, pal_off + 2 * i)[0]
        palette += [(v << 3) | (v >> 2) for v in (c & 31, c >> 5 & 31, c >> 10 & 31)]
    return [p for _, p in textures], palette


def sheet(model: bytes) -> Image.Image:
    textures, palette = frames(model)
    layout = {12: FRAMES_12, 7: FRAMES_7}[len(textures)]
    out = Image.new("P", (FRAME, FRAME * len(layout)))
    out.putpalette(palette)
    for k, (frame, mirror) in enumerate(layout):
        im = Image.new("P", (FRAME, FRAME))
        im.putdata(textures[frame])
        if mirror:
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
        out.paste(im, (0, FRAME * k))
    return out


def sheets(gen5_file) -> dict:
    """Each sprite's sheet, by name, from Black 2's files (gen5_file(path) reads one)."""
    codes = bytes(nitro.NARC(gen5_file(CODES_ARCHIVE)).files[0])
    models = nitro.NARC(gen5_file(MODELS_ARCHIVE))
    model_of = {}
    for i in range(struct.unpack_from("<I", codes, 0)[0]):
        record = struct.unpack_from("<H11B3b5HH", codes, 4 + CODE_RECORD * i)
        model_of.setdefault(record[0], record[15])
    return {name: sheet(bytes(models.files[model_of[code]])) for name, code in SPRITES.items()}


def write(rom, platinum: Path) -> int:
    out = platinum / "gen5/field_sprites"
    out.mkdir(parents=True, exist_ok=True)
    for name, image in sheets(rom.getFileByName).items():
        image.save(out / (f"{name}.png" if name in NEW else f"gen5_{name}.png"))
    return len(SPRITES)


# Anvil makes the archive of overworld sprites as the gen5 build packs it (res/graphics/field_sprites/meson.build), so
# its download doesn't carry Black 2's converted: Platinum's (PLATINUM_ARCHIVE, from the player's ROM), then these in
# field_sprites_gen5.order's order (ARCHIVE_ORDER; check() holds them to the build's files). Each is written into
# Platinum's sprite for its class, which the build's texture tool lays out the same way (TEMPLATES: its index in
# Platinum's archive, field_sprites.order; a new one takes the sprite Platinum gives its class). A new one's names
# aren't its template's: the bundle's patch for the archive puts them, and their dictionary, right.
PLATINUM_ARCHIVE = "data/mmodel/mmodel.narc"
ARCHIVE_ORDER = ["ranger_m", "ranger_f", "psychic_f", "ace_trainer_f", "ace_trainer_m", "artist", "black_belt",
                 "cyclist_f", "cyclist_m", "fisherman", "gentleman", "guitarist", "hiker", "lady", "lass", "maid",
                 "parasol_lady", "pokefan_f", "pokefan_m", "pokemon_breeder_f", "pokemon_breeder_m", "psychic",
                 "rich_boy", "school_kid_f", "school_kid_m", "socialite", "swimmer_f", "swimmer_m", "twin", "waiter",
                 "waitress", "worker", "youngster"]
TEMPLATE_NAMES = {"ranger_m": "ace_trainer_m", "ranger_f": "ace_trainer_f", "psychic_f": "psychic"}
TEMPLATES = {"ranger_m": 10, "ranger_f": 13, "psychic_f": 68, "ace_trainer_f": 13, "ace_trainer_m": 10, "artist": 42,
             "black_belt": 49, "cyclist_f": 37, "cyclist_m": 36, "fisherman": 52, "gentleman": 34, "guitarist": 9,
             "hiker": 19, "lady": 61, "lass": 5, "maid": 154, "parasol_lady": 53, "pokefan_f": 15, "pokefan_m": 14,
             "pokemon_breeder_f": 11, "pokemon_breeder_m": 8, "psychic": 68, "rich_boy": 60, "school_kid_f": 7,
             "school_kid_m": 2, "socialite": 35, "swimmer_f": 45, "swimmer_m": 44, "twin": 1, "waiter": 57,
             "waitress": 58, "worker": 38, "youngster": 3}
# A texture's parameters: colour 0 transparent, which the texture tool leaves off for these sheets
TRANSPARENT_0 = 1 << 29


def dict_entries(d: bytes, off: int) -> list:
    """A Nitro dictionary's (name, offset of its entry in d), as nitro_dict."""
    count = d[off + 1]
    entries = off + 4 + 8 + 4 * count
    entry_size = struct.unpack_from("<H", d, entries)[0]
    names = entries + 4 + entry_size * count
    return [(bytes(d[names + 16 * i:names + 16 * (i + 1)]).rstrip(b"\0").decode("ascii"),
             entries + 4 + entry_size * i) for i in range(count)]


def texture(template: bytes, image: Image.Image) -> bytes:
    """A sheet as a sprite laid out like template: its frames NAME.1 to NAME.16 (some sharing their data) and its
    palette written in."""
    d = bytearray(template)
    tex0 = struct.unpack_from("<I", d, 0x10)[0]
    tex_info, tex_data = struct.unpack_from("<H", d, tex0 + 0x0E)[0], struct.unpack_from("<I", d, tex0 + 0x14)[0]
    pal_info, pal_data = struct.unpack_from("<II", d, tex0 + 0x34)
    pixels = image.load()
    for name, entry in dict_entries(d, tex0 + tex_info):
        frame = int(re.search(r"\.(\d+)$", name).group(1)) - 1
        params = struct.unpack_from("<I", d, entry)[0]
        struct.pack_into("<I", d, entry, params & ~TRANSPARENT_0)
        start = tex0 + tex_data + ((params & 0xFFFF) << 3)
        for i in range(FRAME * FRAME // 2):
            x, y = 2 * i % FRAME, FRAME * frame + 2 * i // FRAME
            d[start + i] = pixels[x, y] & 15 | (pixels[x + 1, y] & 15) << 4
    (_, entry), = dict_entries(d, tex0 + pal_info)
    start = tex0 + pal_data + (struct.unpack_from("<H", d, entry)[0] << 3)
    palette = image.getpalette()
    for i in range(16):
        r, g, b = (v >> 3 for v in palette[3 * i:3 * i + 3])
        struct.pack_into("<H", d, start + 2 * i, r | g << 5 | b << 10)
    return bytes(d)


def narc(files: list) -> bytes:
    """A NARC as the decomp's archive tool packs one without names: the files back to back."""
    assert all(len(f) % 4 == 0 for f in files)
    fat, at = b"", 0
    for f in files:
        fat += struct.pack("<II", at, at + len(f))
        at += len(f)
    btaf = b"BTAF" + struct.pack("<IHH", 12 + len(fat), len(files), 0) + fat
    btnf = b"BTNF" + struct.pack("<IIHH", 16, 4, 0, 1)
    gmif = b"GMIF" + struct.pack("<I", 8 + at) + b"".join(bytes(f) for f in files)
    body = btaf + btnf + gmif
    return b"NARC" + struct.pack("<HHIHH", 0xFFFE, 0x0100, 16 + len(body), 16, 3) + body


def archive(platinum, gen5_file) -> bytes:
    """The archive of overworld sprites, from Platinum's (platinum: a PlatinumRom) and Black 2's files."""
    files = list(platinum.narc(PLATINUM_ARCHIVE))
    images = sheets(gen5_file)
    return narc(files + [texture(files[TEMPLATES[name]], images[name]) for name in ARCHIVE_ORDER])


def check(game: Path):
    """ARCHIVE_ORDER and TEMPLATES against the build's order files."""
    field_sprites = game / "res/graphics/field_sprites"
    order = (field_sprites / "field_sprites.order").read_text().split()
    gen5 = [n.removesuffix(".nsbtx").removeprefix("gen5_")
            for n in (field_sprites / "field_sprites_gen5.order").read_text().split()]
    assert gen5 == ARCHIVE_ORDER, "make_overworld_sprites.ARCHIVE_ORDER differs from field_sprites_gen5.order"
    assert all(order.index(TEMPLATE_NAMES.get(n, n) + ".nsbtx") == TEMPLATES[n] for n in ARCHIVE_ORDER), \
        "make_overworld_sprites.TEMPLATES differs from field_sprites.order"
