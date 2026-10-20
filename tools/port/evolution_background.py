"""Black 2's evolution scene (pokebw2 ov284 shinka_demo) in the green of its egg-hatching scene (ov307 egg_demo), the
owner's choice (GAME-32): it matches Platinum's own evolution background better than Black 2's orange.

Both scenes' backgrounds are the same 3D model, file 8 of their archives (179 and 186), shaded by the colours of its
vertices; its textures and palettes are white in both. The evolution's model keeps its geometry and animations, which
time the scene, and takes the egg's shades in place of its own: recolour() rewrites the colour commands in the
model's display lists. The reveal's flash, the evolution's particles (file 10, SPL's format: pokebw2 lib/spl spl.h),
is white tinted with oranges and golds, which turn the background's teal greens (the egg's particles are its own,
with nothing to take). Gen5_archives.convert runs it, and Anvil on the player's ROM (MIT: no ndspy).
"""
import struct

import nitro

ARCHIVE = 179
MODEL = 8
PARTICLES = 10


def rgb(r: int, g: int, b: int) -> int:
    """GX_RGB: a BGR555 colour."""
    return r | g << 5 | b << 10


# The evolution model's bands, darkest first, and the egg model's in their place. The two layers of arcs have slightly
# different oranges; the egg's share one ramp. Black and the whites at the ends of the bands are the same in both
GREEN = {
    rgb(9, 5, 0): rgb(0, 5, 4),
    rgb(22, 13, 0): rgb(0, 12, 10),
    rgb(20, 12, 0): rgb(0, 12, 10),
    rgb(31, 23, 0): rgb(15, 31, 28),
    rgb(31, 18, 0): rgb(15, 31, 28),
}

COLOR = 0x20
# The geometry commands' parameter counts, in words, for walking a packed display list
PARAMS = {0x00: 0, 0x10: 1, 0x11: 0, 0x12: 1, 0x13: 1, 0x14: 1, 0x15: 0, 0x16: 16, 0x17: 12, 0x18: 16, 0x19: 12,
          0x1A: 9, 0x1B: 3, 0x1C: 3, 0x20: 1, 0x21: 1, 0x22: 1, 0x23: 2, 0x24: 1, 0x25: 1, 0x26: 1, 0x27: 1,
          0x28: 1, 0x29: 1, 0x2A: 1, 0x2B: 1, 0x30: 1, 0x31: 1, 0x32: 1, 0x33: 1, 0x34: 32, 0x40: 1, 0x41: 0,
          0x50: 1, 0x60: 1, 0x70: 3, 0x71: 2, 0x72: 1}


def _entries(data, off: int) -> list:
    """The offsets of a NitroSystem dictionary's entries' data, in order."""
    entries = off + struct.unpack_from("<H", data, off + 6)[0]
    unit = struct.unpack_from("<H", data, entries)[0]
    return [entries + 4 + i * unit for i in range(data[off + 1])]


def _block(data, magic: bytes) -> int:
    count = struct.unpack_from("<H", data, 0xE)[0]
    for i in range(count):
        off = struct.unpack_from("<I", data, 0x10 + 4 * i)[0]
        if data[off:off + 4] == magic:
            return off
    raise ValueError(f"no {magic.decode()} block")


def _colour_params(data) -> list:
    """The offsets of every colour command's parameter in a BMD0's display lists."""
    found = []
    mdl0 = _block(data, b"MDL0")
    for entry in _entries(data, mdl0 + 8):
        model = mdl0 + struct.unpack_from("<I", data, entry)[0]
        shapes = model + struct.unpack_from("<I", data, model + 0xC)[0]
        for shape_entry in _entries(data, shapes):
            shape = shapes + struct.unpack_from("<I", data, shape_entry)[0]
            ofs, size = struct.unpack_from("<II", data, shape + 8)
            p, end = shape + ofs, shape + ofs + size
            while p < end:
                commands = data[p:p + 4]
                p += 4
                for c in commands:
                    if c not in PARAMS:
                        raise ValueError(f"unknown geometry command {c:#x}")
                    if c == COLOR:
                        found.append(p)
                    p += 4 * PARAMS[c]
    return found


def teal(colour: int) -> int:
    """A colour's hue a third of the way round, red to green to blue: the flash's oranges and golds (hues 30 to 60
    degrees) become teal greens (150 to 180) about the background's (169), as bright; white stays white."""
    r, g, b = colour & 31, colour >> 5 & 31, colour >> 10 & 31
    return colour & ~0x7FFF | rgb(b, r, g)


# SPL's resource: its header's size and the offset of its colour; then, as its flags say, its animations of scale,
# colour (the colours it starts and ends at first), alpha and texture, its children (their colour at 0xA) and its
# behaviors, by flag bit
RESOURCE_SIZE = 0x58
RESOURCE_COLOR = 0x22
SCALE_ANIM, COLOR_ANIM, ALPHA_ANIM, TEXTURE_ANIM, CHILDREN = 8, 9, 10, 11, 16
SIZES = {SCALE_ANIM: 12, COLOR_ANIM: 12, ALPHA_ANIM: 8, TEXTURE_ANIM: 12, CHILDREN: 20,
         24: 8, 25: 8, 26: 16, 27: 4, 28: 8, 29: 16}


def _particle_colours(data) -> list:
    """The offsets of every colour of an SPA file's particle resources (its textures are white)."""
    count = struct.unpack_from("<H", data, 8)[0]
    found = []
    p = 0x20
    for _ in range(count):
        flags = struct.unpack_from("<I", data, p)[0]
        found.append(p + RESOURCE_COLOR)
        p += RESOURCE_SIZE
        for bit, size in SIZES.items():
            if flags >> bit & 1:
                if bit == COLOR_ANIM:
                    found += [p, p + 2]
                elif bit == CHILDREN:
                    found.append(p + 0xA)
                p += size
    if p != 0x20 + struct.unpack_from("<I", data, 0x10)[0]:
        raise ValueError("the particle resources don't add up")
    return found


def recolour(data: bytes) -> bytes:
    """The evolution scene's archive with its background in the egg's green, and its flash in teal."""
    narc = nitro.NARC(data)
    model = bytearray(narc.files[MODEL])
    for p in _colour_params(model):
        colour = struct.unpack_from("<I", model, p)[0]
        if colour & 0x7FFF in GREEN:
            struct.pack_into("<I", model, p, colour & ~0x7FFF | GREEN[colour & 0x7FFF])
    narc.files[MODEL] = bytes(model)
    particles = bytearray(narc.files[PARTICLES])
    for p in _particle_colours(particles):
        struct.pack_into("<H", particles, p, teal(struct.unpack_from("<H", particles, p)[0]))
    narc.files[PARTICLES] = bytes(particles)
    return narc.save()
