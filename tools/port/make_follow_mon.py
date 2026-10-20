#!/usr/bin/env python3
"""HeartGold's or SoulSilver's assets for the following Pokémon (GAME-29), as one archive the Gen V build adds to the
ROM as gen5/follow_mon.narc: the follower sprites, their frame sequence and shape table, the Poké Ball and emote
bubble models, the rules, scripts and movements of talking to it, its texts, and its Fly and Sweet Scent effects. The game reads them by the indices
of game/include/overlay005/follow_mon_archive.h, which check() compares with this file's.

Anvil runs it too, on the player's own HeartGold or SoulSilver (USA), so the download carries none of HGSS's art or
text: it reads through nitro.py only (no ndspy, which is GPL). Without that ROM, archive(None) is an archive with no
members, and the game leaves the feature out.

Everything is taken as HGSS has it, except the talk rules of Platinum's locations, which HGSS doesn't have: each
location borrows a Johto or Kanto location's table of the same kind, less the rules tied to HGSS's maps, story and
people (location_rules).

Usage (from extract_assets.py): make_follow_mon.write(hgss_file, platinum_dir), hgss_file(path) giving a file of the
ROM by its path in the file system (a/0/8/1).
"""
import re
import struct
from pathlib import Path

import nitro

SPRITE_COUNT = 566
# HGSS's archives: overworld models, the followers' shapes, field effects, talk rules, scripts, movements and species
# attributes, and the texts
MMODEL, TP_PARAM, FIELD_EFFECTS, FIELD_MOVE_EFFECTS = "a/0/8/1", "a/1/4/1", "a/1/0/3", "a/1/3/4"
RULES, SCRIPTS, MOVEMENTS, SPECIES_ATTR, MSGDATA = "a/2/2/0", "a/2/2/1", "a/2/2/2", "a/2/3/1", "a/0/2/7"
FIRST_SPRITE, SEQUENCE = 297, 292
BALL_MODEL, BURST_MODEL, BURST_ANIM = 0x81, 0x68, 0xA4
EMOTE_MODEL, EMOTE_SEQUENCE, EMOTE_TEXTURE = 0x82, 0x8C, 0x1C
EMOTE_KINDS, EMOTE_TEXTURES, EMOTE_SEQUENCES = 14, 0x2, 0x96
# Fly by the follower: its leap (hiden_jump) and the leap's material and joint animations, in FIELD_EFFECTS; Sweet
# Scent by it: the scent (e_kaori) and its material, texture pattern and joint animations, in FIELD_MOVE_EFFECTS
FLY_JUMP = (0x83, 0xA7, 0xA5)
SWEET_SCENT = (23, 21, 22, 20)
TEXT_BANK, GIFT_TEXT_BANK = 265, 40
LOCATIONS, RULE_SIZE, LOCATION_RULES = 126, 20, 30
SCRIPT_SIZE, SCRIPT_COUNT, MOVEMENT_SIZE, MOVEMENT_COUNT = 52, 1023, 80, 108

# The archive's members, in order, as follow_mon_archive.h numbers them
LAYOUT = [
    ("SPRITES", SPRITE_COUNT),
    ("TP_PARAM", 1),
    ("SEQUENCE", 1),
    ("BALL_MODEL", 1),
    ("BURST_MODEL", 1),
    ("BURST_ANIM", 1),
    ("EMOTE_MODEL", 1),
    ("EMOTE_SEQUENCE", 1),
    ("EMOTE_TEXTURE", 1),
    ("EMOTE_TEXTURES", EMOTE_KINDS),
    ("EMOTE_SEQUENCES", EMOTE_KINDS),
    ("RULES_GLOBAL", 1),
    ("RULES_LOCATION", LOCATIONS),
    ("SCRIPTS", 1),
    ("MOVEMENTS", 1),
    ("SPECIES_ATTR", 1),
    ("TEXT", 1),
    ("GIFT_TEXT", 1),
    ("FLY_JUMP_MODEL", 1),
    ("FLY_JUMP_MATERIAL_ANIM", 1),
    ("FLY_JUMP_JOINT_ANIM", 1),
    ("SWEET_SCENT_MODEL", 1),
    ("SWEET_SCENT_MATERIAL_ANIM", 1),
    ("SWEET_SCENT_TEXTURE_ANIM", 1),
    ("SWEET_SCENT_JOINT_ANIM", 1),
]
HEADER = "include/overlay005/follow_mon_archive.h"
PATH = "gen5/follow_mon.narc"


def members(hgss_file) -> list:
    """The archive's files, in LAYOUT's order."""
    mmodel = nitro.NARC(hgss_file(MMODEL)).files
    effects = nitro.NARC(hgss_file(FIELD_EFFECTS)).files
    move_effects = nitro.NARC(hgss_file(FIELD_MOVE_EFFECTS)).files
    rules = nitro.NARC(hgss_file(RULES)).files
    msgdata = nitro.NARC(hgss_file(MSGDATA)).files
    sprites = [bytes(f) for f in mmodel[FIRST_SPRITE:FIRST_SPRITE + SPRITE_COUNT]]
    tp_param = b"".join(bytes(f) for f in nitro.NARC(hgss_file(TP_PARAM)).files)
    scripts = b"".join(bytes(f) for f in nitro.NARC(hgss_file(SCRIPTS)).files)
    movements = b"".join(bytes(f) for f in nitro.NARC(hgss_file(MOVEMENTS)).files)
    attrs = bytes(nitro.NARC(hgss_file(SPECIES_ATTR)).files[0])
    assert all(s[:4] == b"BTX0" for s in sprites), "the follower sprites aren't where HGSS has them"
    assert len(tp_param) == 4 * SPRITE_COUNT
    assert len(scripts) == SCRIPT_SIZE * SCRIPT_COUNT and len(movements) == MOVEMENT_SIZE * MOVEMENT_COUNT
    return (sprites + [tp_param, bytes(mmodel[SEQUENCE])]
            + [bytes(effects[i]) for i in (BALL_MODEL, BURST_MODEL, BURST_ANIM)]
            + [bytes(effects[i]) for i in (EMOTE_MODEL, EMOTE_SEQUENCE, EMOTE_TEXTURE)]
            + [bytes(effects[EMOTE_TEXTURES + k]) for k in range(EMOTE_KINDS)]
            + [bytes(effects[EMOTE_SEQUENCES + k]) for k in range(EMOTE_KINDS)]
            + [bytes(rules[0])] + location_rules(rules, scripts)
            + [scripts, movements, attrs, bytes(msgdata[TEXT_BANK]), bytes(msgdata[GIFT_TEXT_BANK])]
            + [bytes(effects[i]) for i in FLY_JUMP]
            + [bytes(move_effects[i]) for i in SWEET_SCENT])


# The talk rules of Platinum's locations (HGSS's mapsecs 0-125, which HGSS has none for, but the Pokémon League's):
# each borrows the table of a Johto or Kanto location of the same kind, HGSS's mapsec here (the owner's choice, "borrow
# by kind"). A town borrows a town's, a route a route of its terrain's (sea, mountain, cycling road), a cave, forest,
# lake, marsh, ruins, mansion or factory one of their own kind. The ones not listed (most buildings, and where the
# follower can't go) borrow none: the 70 global rules apply everywhere.
DONORS = {
    1: 138, 2: 126, 3: 127, 4: 134, 5: 142, 6: 128, 7: 143, 8: 134, 9: 128, 10: 128, 11: 145, 12: 143,
    13: 130, 14: 134, 15: 15,
    16: 177, 17: 178, 18: 179, 19: 180, 20: 182, 21: 165, 22: 157, 23: 181, 24: 185, 25: 160, 26: 193, 27: 186,
    28: 188, 29: 174, 30: 190, 31: 137, 32: 137, 33: 189, 34: 168, 35: 169, 36: 170, 37: 167, 38: 189, 39: 173,
    40: 176, 41: 175, 42: 171, 43: 152, 44: 150, 45: 167,
    46: 210, 47: 201, 48: 214, 49: 201, 50: 216, 51: 209, 52: 202, 53: 209, 54: 221, 57: 220, 58: 183, 59: 210,
    60: 224, 61: 135, 62: 222, 63: 183, 64: 217, 65: 220, 66: 210, 67: 210, 68: 149, 69: 200, 70: 206, 71: 213,
    72: 191, 73: 191, 74: 191, 75: 195, 76: 135, 77: 135, 78: 135, 79: 224, 81: 130, 82: 134, 83: 146, 84: 219,
    85: 189, 86: 209, 87: 203, 88: 203, 89: 203, 104: 212, 109: 146, 112: 229, 122: 213, 123: 209, 124: 209,
    125: 209,
}
# HGSS's flag 332, which its rules of the follower finding accessories ask for, is Platinum's
# FLAG_RECEIVED_FASHION_CASE; the rules that ask for any other flag (HGSS's story) are dropped
FLAG_FASHION_CASE = (332, 242)
# Messages naming HGSS's people and places, or what only the donor location has: the rules whose scripts print one are
# dropped (Team Rocket, Kimono Girls, the S.S. Aqua's boat, towers and their pillars, the straw hat, souvenir and
# weather vanes, "the two" and "everyone")
EXCLUDED_MESSAGES = {
    143, 229, 275, 290, 291, 292, 305, 307, 319, 346, 347, 417, 418, 430, 479, 483, 492, 516, 578, 582, 608, 688,
    689, 726, 740,
}


def script_messages(scripts: bytes, script: int, seen=None) -> set:
    """The messages a script prints, and its yes and no scripts' (HGSS's FollowMonInteractionStep and the rest)."""
    seen = set() if seen is None else seen
    if script == 0 or script in seen or script > SCRIPT_COUNT:
        return set()
    seen.add(script)
    data = scripts[(script - 1) * SCRIPT_SIZE:script * SCRIPT_SIZE]
    messages = set()
    for i in range(5):
        movement, message = struct.unpack_from("<HH", data, i * 8)
        if movement == 0xFFFF:
            break
        if message:
            messages.add(message - 1)
    yes, no = struct.unpack_from("<HH", data, 44)
    return messages | script_messages(scripts, yes, seen) | script_messages(scripts, no, seen)


def borrowed_rule(rule: bytes, scripts: bytes):
    """A donor's rule as a Platinum location's, or None to drop it: not one for an HGSS map (its map id), story flag
    or Pokéathlon stat, nor one whose script names HGSS's people or places."""
    script = struct.unpack_from("<H", rule, 10)[0] >> 6
    map_id, flag = struct.unpack_from("<H", rule, 12)[0], struct.unpack_from("<H", rule, 18)[0]
    pokeathlon = rule[4] >> 5
    if script == 0 or map_id or pokeathlon or (flag and flag != FLAG_FASHION_CASE[0]):
        return None
    if script_messages(scripts, script) & EXCLUDED_MESSAGES:
        return None
    if flag:
        rule = rule[:18] + struct.pack("<H", FLAG_FASHION_CASE[1])
    return rule


def location_rules(rules: list, scripts: bytes) -> list:
    """Each Platinum location's talk rules, 30 of 20 bytes, borrowed from its donor (DONORS), the rest empty."""
    tables = []
    for location in range(LOCATIONS):
        kept = []
        if location in DONORS:
            donor = bytes(rules[DONORS[location] + 1])
            for i in range(0, len(donor), RULE_SIZE):
                rule = borrowed_rule(donor[i:i + RULE_SIZE], scripts)
                if rule is not None:
                    kept.append(rule)
        tables.append(b"".join(kept[:LOCATION_RULES]).ljust(RULE_SIZE * LOCATION_RULES, b"\0"))
    return tables


def archive(hgss_file) -> bytes:
    """The archive made from a HeartGold or SoulSilver ROM, or, with none, an archive with no members."""
    narc = nitro.NARC()
    if hgss_file is not None:
        narc.files = members(hgss_file)
        assert len(narc.files) == sum(n for _, n in LAYOUT)
    return narc.save()


def write(hgss_file, platinum: Path) -> int:
    """Writes the archive into game/gen5/files; returns its size."""
    data = archive(hgss_file)
    dest = platinum / "gen5/files" / PATH
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return len(data)


def check(game: Path):
    """The archive's layout must be the game's (follow_mon_archive.h)."""
    defines = dict(re.findall(r"#define FOLLOW_MON_MEMBER_(\w+)\s+(\d+)", (game / HEADER).read_text()))
    first = 0
    for name, count in LAYOUT:
        assert int(defines[name]) == first, f"{HEADER}: FOLLOW_MON_MEMBER_{name} is {defines[name]}, not {first}"
        first += count
    assert int(defines["COUNT"]) == first, f"{HEADER}: FOLLOW_MON_MEMBER_COUNT is {defines['COUNT']}, not {first}"
