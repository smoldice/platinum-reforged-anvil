#!/usr/bin/env python3
"""Black 2's battle draws trainers as MCSS sprites. This makes them out of Platinum's own trainer sprites, so every
trainer in the battle looks as in Platinum:

- The front sprites (a/0/7/1): one for each of Platinum's trainer classes, at FRONT_BASE plus the class's number,
  which the port's battle uses as the sprite (gen5_trainer.c). They come after the Black 2 sprites the battle still
  shows: its World Tournament's Sinnoh Gym Leaders (129 to 136) and Cynthia (91), which have more animation than
  Platinum's, so the user chose them for those characters. Thirteen classes' are Black 2's own sprite and animation of
  the class, retextured to Platinum's look (retexture.py, RETEXTURES): the user's, reviewed in
  docs/retextured-trainers.md.
  The Roughneck's, the Clown's and the Aroma Lady's are Platinum's own frame, animated by a rig (trainer_rig.py, RIGS):
  the user's, in docs/roughneck-animation.md, docs/clown-animation.md and docs/aroma-lady-animation.md. A rig can
  also be made in Aseprite and packed into anim_<class>.py (aseprite_rig.py, docs/aseprite-animations.md): the
  Picnicker's (docs/picnicker-animation.md) and the Bug Catcher's (docs/bug-catcher-animation.md). The
  classes with a retexture or a rig also get Platinum's own sprite after the last class's (PLATINUM_ORIGINALS),
  which the battle shows with the CUSTOM SPRITES option off (gen5_trainer.c).
- The back sprites (a/0/7/2): Lucas and Dawn in place of Nate and Rosa, which Black 2's trainer class table gives
  the player classes 0 and 1, and the partners' (Cheryl, Riley…) in place of Black 2's partners (BACKS).

An MCSS sprite is eight files (pokebw2: src/system/pokegra.c, TRGRA_FILE_*): a 2D character set, the texture, cells,
cell animations, multi-cells, multi-cell animations, the rectangles each cell draws from the texture (the "bin"), and
the palette. Platinum's sprites are 80x80 frames (as the decomp's res/trainers/classes/*/front.png or back.png has
them, one pixel apart, read from Platinum's ROM by platinum_rom.py) that its cells draw at slightly different places.

Each distinct frame is trimmed to what it shows and packed into the 256x128 4bpp texture, Black 2's size for these. A
frame that doesn't fit whole is drawn in two parts, through the bin's second rectangle. Each of Platinum's cells
becomes a cell, a cell animation and a multi-cell, and its animations become the multi-cell animations. A back
sprite keeps Platinum's order, where the throw is the second, as in Black 2. A front sprite's first is the one Black
2 plays as the trainer appears: Platinum's intro (a Gym Leader's, Cynthia's…), which Platinum plays then too, or the
still frame; its second, which Black 2 shows when the trainer comes back after the battle, is the still frame.

Used by extract_assets.py and Anvil: update_fronts(narc_bytes, platinum) and update_backs(narc_bytes, platinum),
platinum a PlatinumRom, return the archives with them.
"""
import importlib
import struct

import nitro
from nitro import unlz  # noqa: F401  (other modules use it as mts.unlz)
from platinum_rom import TRAINER_CLASSES, PlatinumRom

TEX_W, TEX_H = 256, 128
# Black 2's player is drawn about 104 pixels tall, Platinum's 67: back sprites are scaled to take Black 2's place
BACK_SCALE = 1.5
FRONT_SCALE = 1.0
FRAME = 80
FILE_COUNT = 8
# Black 2's back sprite index, and Platinum's trainer class directory. gen5_trainer.c gives the partners' classes
# these indices
BACKS = {0: "player_male", 1: "player_female", 2: "trainer_cheryl", 3: "trainer_riley", 4: "trainer_marley",
         5: "trainer_buck", 6: "trainer_mira", 7: "rival", 8: "dp_player_male", 9: "dp_player_female"}
# Where Platinum's front sprites start: after the last Black 2 sprite the battle shows, Volkner's. Black 2 has 188.
# GetTrSpriteBaseDatID returns a u8, but its callers don't cut the value to a byte, so the port's (gen5_trainer.c)
# returns slots past 255
FRONT_BASE = 137
# Front sprites that are Black 2's, retextured to Platinum's look (retexture.py), by Platinum class: each settings
# module's B2_SPRITE is its Black 2 sprite, still Black 2's own when replace() reads it
RETEXTURES = {
    "ace_trainer_male": "retexture_ace_trainer_male",
    "ace_trainer_female": "retexture_ace_trainer_female",
    "fisherman": "retexture_fisherman",
    "worker": "retexture_worker",
    "lass": "retexture_lass",
    "waitress": "retexture_waitress",
    "black_belt": "retexture_black_belt",
    "hiker": "retexture_hiker",
    "psychic_male": "retexture_psychic_male",
    "psychic_female": "retexture_psychic_female",
    "rich_boy": "retexture_rich_boy",
    "gentleman": "retexture_gentleman",
    "youngster": "retexture_youngster",
}
# Front sprites animated from Platinum's own frame by a rig (trainer_rig.py), by Platinum class: written by hand
# (rig_<class>), or made in Aseprite and packed (anim_<class>, aseprite_rig.py)
RIGS = {"roughneck": "rig_roughneck", "clown": "rig_clown", "aroma_lady": "rig_aroma_lady",
        "picnicker": "anim_picnicker", "bug_catcher": "anim_bug_catcher"}
# The classes whose slot has the user's sprite, also as Platinum's own after the last class's slot, in this order, for
# the CUSTOM SPRITES option off (gen5_trainer.c: sGen5CustomClasses, which must list them in the same order): a new
# one goes at the end, so the others keep their slots
PLATINUM_ORIGINALS = ["ace_trainer_male", "ace_trainer_female", "fisherman", "worker", "roughneck", "lass",
                      "waitress", "clown", "aroma_lady", "picnicker", "black_belt", "hiker", "psychic_male",
                      "psychic_female", "rich_boy", "gentleman", "bug_catcher", "youngster"]
# The Black 2 sprites whose files the new ones take their headers from: Nate's back, the Youngster's front
BACK_TEMPLATE = 0
FRONT_TEMPLATE = 2
SIZES = {(0, 0): (8, 8), (0, 1): (16, 16), (0, 2): (32, 32), (0, 3): (64, 64), (1, 0): (16, 8), (1, 1): (32, 8),
         (1, 2): (32, 16), (1, 3): (64, 32), (2, 0): (8, 16), (2, 1): (8, 32), (2, 2): (16, 32), (2, 3): (32, 64)}


def lz10(data: bytes) -> bytes:
    """An LZ77 (type 0x10) stream of literals only, which GFL's archive reads decompress."""
    out = bytearray([0x10]) + len(data).to_bytes(3, "little")
    for i in range(0, len(data), 8):
        out.append(0)
        out += data[i:i + 8]
    while len(out) % 4:
        out.append(0)
    return bytes(out)


def nitro_file(magic: bytes, version: int, blocks: list) -> bytes:
    body = b"".join(blocks)
    return magic + struct.pack("<HHIHH", 0xFEFF, version, 16 + len(body), 16, len(blocks)) + body


def block(magic: bytes, content: bytes) -> bytes:
    while len(content) % 4:
        content += b"\0"
    return magic + struct.pack("<I", 8 + len(content)) + content


def anim_block(sequences) -> bytes:
    """A KNBA block: sequences of (element type, anim type, play mode, [(duration, result bytes)])."""
    seq_data, frame_data, results = b"", b"", b""
    frame_count = 0
    for element, anim_type, mode, frames in sequences:
        seq_data += struct.pack("<HHHHII", len(frames), 0, element, anim_type, mode, len(frame_data))
        for duration, result in frames:
            frame_data += struct.pack("<IHH", len(results), duration, 0xBEEF)
            results += result
            while len(results) % 4:
                results += b"\0"
        frame_count += len(frames)
    head = 0x18
    content = struct.pack("<HHIII8x", len(sequences), frame_count, head, head + len(seq_data),
                          head + len(seq_data) + len(frame_data))
    return block(b"KNBA", content + seq_data + frame_data + results)


def load_frames(picture):
    image = picture.image
    frames = [image.crop((0, f * (FRAME + 1), FRAME, f * (FRAME + 1) + FRAME)) for f in range(len(picture.shifts))]
    # Each cell draws its own frame (Platinum swaps the frame's characters in), shifted by its first OAM's place
    # (a cell with nothing to show has no OAM)
    shifts = [(s[0] + 40, s[1] + 40) if s else (0, 0) for s in picture.shifts]
    return image.getpalette()[:48], frames, shifts, picture.sequences


def pack(pieces):
    """Shelf packing of (key, w, h) pieces into the texture, tallest first. Returns {key: (x, y)} or None."""
    placed, x, y, shelf = {}, 0, 0, 0
    for key, w, h in sorted(pieces, key=lambda p: -p[2]):
        if x + w > TEX_W:
            x, y, shelf = 0, y + shelf, 0
        if y + h > TEX_H or w > TEX_W:
            return None
        placed[key] = (x, y)
        x += w
        shelf = max(shelf, h)
    return placed


def layout(frames):
    """The texture pieces of the distinct frames: (frame, top row, rows, left, width), with at most two per frame."""
    distinct = []
    for i, f in enumerate(frames):
        if not any(frames[j].tobytes() == f.tobytes() for j in distinct):
            distinct.append(i)
    boxes = {i: frames[i].point(lambda p: 255 if p else 0).getbbox() for i in distinct}
    # A frame that shows nothing (some intros start with one) draws no rectangle
    shown = [i for i in distinct if boxes[i] is not None]
    split = set()
    while True:
        pieces = []
        for i in shown:
            left, top, right, bottom = boxes[i]
            if i in split:
                middle = (top + bottom) // 2
                pieces += [((i, 0), right - left, middle - top), ((i, 1), right - left, bottom - middle)]
            else:
                pieces.append(((i, 0), right - left, bottom - top))
        placed = pack(pieces)
        if placed is not None:
            break
        # Split the tallest whole frame next
        whole = [i for i in shown if i not in split]
        if not whole:
            raise SystemExit("the sprite's frames don't fit the texture")
        split.add(max(whole, key=lambda i: boxes[i][3] - boxes[i][1]))
    parts = {i: [] for i in distinct}
    for i in shown:
        left, top, right, bottom = boxes[i]
        rows = [(top, bottom)] if i not in split else [(top, (top + bottom) // 2), ((top + bottom) // 2, bottom)]
        parts[i] = [(r0, r1 - r0, left, right - left, placed[(i, k)]) for k, (r0, r1) in enumerate(rows)]
    owner = [next(j for j in distinct if frames[j].tobytes() == f.tobytes()) for f in frames]
    return parts, owner


def make_sprite(picture, side: str, template: list) -> list:
    palette, frames, shifts, anim = load_frames(picture)
    scale = BACK_SCALE if side == "back" else FRONT_SCALE
    if side == "front":
        anim = [anim[1] if len(anim) > 1 else anim[0], anim[0]]
    parts, owner = layout(frames)

    texture = bytearray(TEX_W * TEX_H // 2)
    for i, pieces in parts.items():
        px = frames[i].load()
        for top, rows, left, width, (tx, ty) in pieces:
            for y in range(rows):
                for x in range(width):
                    v = px[left + x, top + y] & 15
                    p = (ty + y) * TEX_W + tx + x
                    texture[p // 2] |= v << (4 * (p & 1))

    # The bin: per cell, the main rectangle and maybe a second one. Positions are from the sprite's origin, the
    # frame's bottom middle, up and right, in units of 16 pixels as fx32 (pixels * 256); sizes and texture
    # coordinates in pixels as fx32
    rects = b""
    for cell, frame in enumerate(owner):
        dx, dy = shifts[cell]
        entries = []
        for top, rows, left, width, (tx, ty) in parts[frame]:
            x = left + dx - FRAME // 2
            y = FRAME - (top + dy)
            entries.append(struct.pack("<6i", x * 256, y * 256, width * 4096, rows * 4096, tx * 4096, ty * 4096))
        while len(entries) < 2:
            entries.append(bytes(24))
        rects += entries[0] + entries[1]
    bin_file = struct.pack("<I4H", len(owner), 0, 0, 0, 0) + rects

    # The palette, in the template's NCLR
    nclr = bytearray(unlz(template[7]))
    data = struct.unpack_from("<I", nclr, 0x10 + 0x14)[0]
    for c in range(16):
        r, g, b = palette[c * 3:c * 3 + 3]
        struct.pack_into("<H", nclr, 0x10 + 0x08 + data + c * 2, (r >> 3) | (g >> 3) << 5 | (b >> 3) << 10)

    # The texture, in the template's NCGR (256x128, 4bpp, linear)
    ncgr = bytearray(unlz(template[1]))
    assert struct.unpack_from("<HH", ncgr, 0x18) == (TEX_H // 8, TEX_W // 8)
    assert struct.unpack_from("<I", ncgr, 0x2c)[0] == 0x18, "unexpected NCGR data offset"
    ncgr[0x30:0x30 + len(texture)] = texture

    # The 2D characters: the first frame, 10x10 tiles
    chars = bytearray(unlz(template[0]))
    assert struct.unpack_from("<HH", chars, 0x18) == (FRAME // 8, FRAME // 8)
    tiles = bytearray()
    first = frames[0].load()
    for ty in range(FRAME // 8):
        for tx in range(FRAME // 8):
            for y in range(8):
                for x in range(0, 8, 2):
                    a = first[tx * 8 + x, ty * 8 + y] & 15
                    b = first[tx * 8 + x + 1, ty * 8 + y] & 15
                    tiles.append(a | b << 4)
    chars[0x30:0x30 + len(tiles)] = tiles

    # One cell animation and one multi-cell per cell
    nanr = nitro_file(b"RNAN", 0x0100, [anim_block([(0, 1, 2, [(1, struct.pack("<H", c))]) for c in range(len(owner))])])
    hier = b"".join(struct.pack("<HhhH", c, 0, 0, 0x21) for c in range(len(owner)))
    mcs = b"".join(struct.pack("<HHI", 1, 1, c * 8) for c in range(len(owner)))
    nmcr = nitro_file(b"RCMN", 0x0100, [block(b"KBCM", struct.pack("<HHII8x", len(owner), 0xBEEF, 0x14, 0x14 + len(mcs))
                                              + mcs + hier)])
    sequences = []
    for s, seq in enumerate(anim):
        frames_ = [(delay, struct.pack("<HHiihh", result, 0, int(4096 * scale), int(4096 * scale), 0, 0))
                   for delay, result in seq]
        sequences.append((1, 2, 1 if s == 0 else 2, frames_))
    nmar = nitro_file(b"RAMN", 0x0100, [anim_block(sequences)])

    return [lz10(bytes(chars)), lz10(bytes(ncgr)), template[2], lz10(nanr), nmcr, nmar, bin_file, bytes(nclr)]


def replace(narc_data: bytes, sprites: dict, side: str, template: int, platinum: PlatinumRom, plain=()) -> bytes:
    """The archive with each sprite index's files made from that Platinum class's picture: the user's retexture or
    rig for the classes that have one, unless the index is in plain."""
    narc = nitro.NARC(narc_data)
    base = template * FILE_COUNT
    template_files = narc.files[base:base + FILE_COUNT]
    for index, cls in sorted(sprites.items()):
        base = index * FILE_COUNT
        # past the archive's end, the sprites are added in order
        assert base <= len(narc.files)
        picture = platinum.trainer(cls, side)
        if index in plain:
            files = make_sprite(picture, side, template_files)
        elif side == "front" and cls in RETEXTURES:
            # retexture.py imports this module, so its settings modules load here
            module = importlib.import_module(RETEXTURES[cls])
            b2 = module.B2_SPRITE
            files = module.build(narc.files[b2 * FILE_COUNT:(b2 + 1) * FILE_COUNT], picture.image)
        elif side == "front" and cls in RIGS:
            # trainer_rig.py imports this module, so it and the rigs load here
            import trainer_rig
            rig = importlib.import_module(RIGS[cls])
            files = trainer_rig.build(rig, picture.image, template_files)
        else:
            files = make_sprite(picture, side, template_files)
        narc.files[base:base + FILE_COUNT] = files
    return narc.save()


def update_fronts(narc_data: bytes, platinum: PlatinumRom) -> bytes:
    classes = TRAINER_CLASSES
    assert sorted(PLATINUM_ORIGINALS) == sorted({*RETEXTURES, *RIGS}), \
        "PLATINUM_ORIGINALS (and gen5_trainer.c's sGen5CustomClasses) must list every class with a retexture or a rig"
    sprites = {FRONT_BASE + i: cls for i, cls in enumerate(classes)}
    originals = {FRONT_BASE + len(classes) + i: cls for i, cls in enumerate(PLATINUM_ORIGINALS)}
    return replace(narc_data, {**sprites, **originals}, "front", FRONT_TEMPLATE, platinum, plain=originals)


def update_backs(narc_data: bytes, platinum: PlatinumRom) -> bytes:
    return replace(narc_data, BACKS, "back", BACK_TEMPLATE, platinum)
