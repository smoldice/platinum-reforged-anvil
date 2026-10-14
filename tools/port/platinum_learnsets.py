#!/usr/bin/env python3
"""Platinum's level-up learnsets in Black 2's format, for Black 2's learnset archive (a/0/1/8, ARCID_LEARNSETS): the
battle's level-ups and the evolution scene teach moves from it, and Black 2's own teach moves Platinum doesn't have
(its Pikachu learns Electro Ball, 486, at 18), which a party member then keeps in Platinum's save. Each of Platinum's
species (1 to 493) and forms with their own learnset get Platinum's; the rest, Gen V's, keep Black 2's.

Black 2's entry is (u16 move, u16 level) pairs ending with 0xFFFF twice; Platinum's (poketool/personal/wotbl.narc,
read from its ROM) is u16 move | level << 9 entries ending with 0xFFFF. Black 2 finds a form's entry from its personal data's form table
(a/0/1/6: the first form's index at 0x1C); Platinum's forms are after its species, from 496 (pokemon.c
Pokemon_GetFormNarcIndex).

Usage (gen5_archives.py): platinum_learnsets.build(black2_archive, black2_personal, platinum), platinum a PlatinumRom
"""
import struct

import nitro

ARCHIVE = 18
PERSONAL = "a/0/1/6"
PLATINUM_LEARNSETS = "poketool/personal/wotbl.narc"
SPECIES_COUNT = 493
PERSONAL_FORM_START = 0x1C
# Platinum's forms with their own learnset: species, first form, count, Platinum's index of the first
PLATINUM_FORMS = [(386, 1, 3, 496), (413, 1, 2, 499), (487, 1, 1, 501), (492, 1, 1, 502), (479, 1, 5, 503)]
# Black 2's forms Platinum gives no learnset of their own: Castform's
SHARED_FORMS = [351]
END = 0xFFFF


def convert(platinum_entry: bytes) -> bytes:
    pairs = []
    for (value,) in struct.iter_unpack("<H", platinum_entry[:len(platinum_entry) // 2 * 2]):
        if value == END:
            break
        pairs.append((value & 0x1FF, value >> 9))
    return b"".join(struct.pack("<HH", move, level) for move, level in pairs) + struct.pack("<HH", END, END)


def build(data: bytes, personal: bytes, platinum) -> bytes:
    narc = nitro.NARC(data)
    learnsets = platinum.narc(PLATINUM_LEARNSETS)
    forms = nitro.NARC(personal).files
    for species in range(1, SPECIES_COUNT + 1):
        narc.files[species] = convert(learnsets[species])
    for species, first, count, index in PLATINUM_FORMS:
        start = struct.unpack_from("<H", forms[species], PERSONAL_FORM_START)[0]
        for k in range(count):
            narc.files[start + first - 1 + k] = convert(learnsets[index + k])
    for species in SHARED_FORMS:
        start = struct.unpack_from("<H", forms[species], PERSONAL_FORM_START)[0]
        count = forms[species][0x20]
        for k in range(count - 1):
            narc.files[start + k] = convert(learnsets[species])
    return narc.save()
