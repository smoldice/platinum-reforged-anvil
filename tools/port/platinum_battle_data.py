#!/usr/bin/env python3
"""Platinum's battle data in Black 2's records, so the Gen V battle calculates with Platinum's numbers (GAME-79, and
GAME-82's D2 and D9 and GAME-88's J4 and J5; docs/battle-rules-audit.md, "A. Move data"). Black 2's records are
rewritten field by field: only the fields named here change, every other byte stays Black 2's.

- Moves, a/0/2/1 (ARCID 21): for Platinum's moves (1 to 467), its power, accuracy, PP, priority, target and the
  Protect, Magic Coat and Snatch flags; King's Rock's flag into a spare bit; Platinum's turn ranges for the binding and
  sleep moves; Platinum's stat changes and effect ids for Growth, Tail Glow and Minimize; Platinum's rule of which
  status moves pass a Substitute where Black 2's differs (Curse and Sketch lose the bypass, Transform gains it); Curse
  takes Platinum's ??? type (Black 2's 17). Platinum's table is poketool/waza/pl_waza_tbl.narc.
- Items, a/0/2/4 (24): the Metronome item's hold parameter, the Blue, Yellow and Red Flutes' battle pockets, X Sp.
  Def's friendship, from Platinum's itemtool/itemdata/pl_item_data.narc.
- Species, a/0/1/6 (16): Rotom's five appliance forms' types, from poketool/personal/pl_personal.narc.

Black 2's move record (0x24 bytes, pokebw2 tools/data/move_data.py): 0x00 type, 0x01 quality, 0x02 category,
0x03 power, 0x04 accuracy (101: never misses), 0x05 PP, 0x06 priority (s8), 0x07 hits, 0x08 condition (u16),
0x0A its chance, 0x0B its duration kind, 0x0C/0x0D its minimum and maximum turns, 0x0E crit stage, 0x0F flinch
chance, 0x10 effect id (u16), 0x12 drain, 0x13 heal, 0x14 target, 0x15-0x17 stats changed, 0x18-0x1A their stages
(s8), 0x1B-0x1D their chances, 0x1E "SS", 0x20 flags (u32). Platinum's (16 bytes, include/move_table.h MoveTable):
0x00 effect (u16), 0x02 class, 0x03 power, 0x04 type, 0x05 accuracy (0: never misses), 0x06 PP, 0x07 effect chance,
0x08 range (u16, a mask), 0x0A priority (s8), 0x0B flags, 0x0C contest data.

Usage (gen5_archives.py): build_moves(data, platinum), build_items(data, platinum), build_personal(data, platinum),
platinum a PlatinumRom; each returns the archive's new bytes.
"""
import struct

import nitro

MOVES_ARCHIVE = 21
ITEMS_ARCHIVE = 24
PERSONAL_ARCHIVE = 16
PLATINUM_MOVES = "poketool/waza/pl_waza_tbl.narc"
PLATINUM_ITEMS = "itemtool/itemdata/pl_item_data.narc"
PLATINUM_PERSONAL = "poketool/personal/pl_personal.narc"

# --- Moves

MOVE_COUNT = 467  # Platinum's moves; Black 2's after them (Gen V's) keep their records
B2_POWER, B2_ACCURACY, B2_PP, B2_PRIORITY = 0x03, 0x04, 0x05, 0x06
B2_DURATION, B2_MIN_TURNS, B2_MAX_TURNS = 0x0B, 0x0C, 0x0D
B2_EFFECT, B2_TARGET, B2_STATS, B2_STAGES, B2_FLAGS = 0x10, 0x14, 0x15, 0x18, 0x20
B2_TYPE = 0x00
PT_EFFECT, PT_POWER, PT_ACCURACY, PT_PP, PT_RANGE, PT_PRIORITY, PT_FLAGS = 0x00, 0x03, 0x05, 0x06, 0x08, 0x0A, 0x0B
PT_TYPE = 0x04

B2_NEVER_MISSES = 101  # Platinum's accuracy 0
# Black 2's targets (pokebw2 include/constants/battle.h MOVE_TARGET_*)
SELECTED, USER_OR_ALLY, ALLY, FOE, ALL_ADJACENT, ADJACENT_FOES, USER_PARTY, USER, ALL, RANDOM_FOE, FIELD, \
    FOE_SIDE, USER_SIDE, DEPENDS = range(14)
# Platinum's ranges (generated/move_ranges.txt, a mask) as Black 2's targets
PT_TARGETS = {
    0x0000: SELECTED,  # RANGE_SINGLE_TARGET
    0x0002: RANDOM_FOE,  # RANGE_RANDOM_OPPONENT
    0x0004: ADJACENT_FOES,  # RANGE_ADJACENT_OPPONENTS
    0x0008: ALL_ADJACENT,  # RANGE_ALL_ADJACENT
    0x0010: USER,  # RANGE_USER
    0x0040: FIELD,  # RANGE_FIELD
    0x0080: FOE_SIDE,  # RANGE_OPPONENT_SIDE
    0x0100: ALLY,  # RANGE_ALLY
    0x0200: USER_OR_ALLY,  # RANGE_USER_OR_ALLY
    0x0400: FOE,  # RANGE_SINGLE_TARGET_ME_FIRST
}
# Platinum's ranges Black 2 says in more than one way: Black 2's target stays when it's one of these.
# RANGE_SINGLE_TARGET_SPECIAL (no target chosen, the move decides: Metronome, Counter...) is USER or DEPENDS in
# Black 2; RANGE_USER_SIDE is USER_SIDE, or USER_PARTY for the moves that reach the bench (Heal Bell, Aromatherapy)
PT_TARGETS_EITHER = {0x0001: {USER, DEPENDS}, 0x0020: {USER_PARTY, USER_SIDE}}
# Mirror Move (119): Platinum's RANGE_SINGLE_TARGET_SPECIAL (no target chosen; the copied move picks its own) as
# Black 2's USER, the target its other move-calling moves have (Metronome, Sleep Talk, Assist, Copycat): the port's
# handler reads Platinum's record of the moves aimed at the user, and aims the copied move itself (game/src/gen5/
# gen5_moves.c, GAME-80 B12). Conversion 2 (176) takes Platinum's RANGE_USER the same way, its handler the port's.
MOVE_MIRROR_MOVE = 119
TARGET_OVERRIDES = {MOVE_MIRROR_MOVE: USER}
# Moves whose target stays Black 2's although Platinum's differs, because Black 2's code needs its own:
# - Curse (174): Black 2 decides Curse's target in code by its move ID wherever the target matters (btl_calc.c
#   func_ov167_021bd8d0: the user, or a selected foe for a Ghost type; btl_server_flow_sub.c func_ov167_021ae55c: a
#   foe when a Ghost's Curse is aimed at itself; btlv_scd.c, the target choice; btl_client.c, the animation), which is
#   Platinum's behaviour (battle_lib.c turns a non-Ghost's Curse onto the user, and aims a Ghost's at a random foe
#   when it's aimed at itself). Black 2's DEPENDS is the value its code expects there.
# - Perish Song (195): Black 2 inflicts its condition on each target (ALL), which Soundproof blocks one by one, as
#   Platinum's BtlCmd_TryPerishSong does; Platinum's FIELD would leave Black 2's no target to inflict it on.
KEEP_TARGET = {174, 195}

# Black 2's flags (pokebw2 MOVE_FLAG_*) and Platinum's (generated/move_flags.txt, a mask)
B2_FLAG_PROTECT, B2_FLAG_REFLECTABLE, B2_FLAG_SNATCH = 1 << 3, 1 << 4, 1 << 5
B2_FLAG_BYPASS_SUBSTITUTE = 1 << 13
PT_FLAG_PROTECT, PT_FLAG_MAGIC_COAT, PT_FLAG_SNATCH, PT_FLAG_KINGS_ROCK = 1 << 1, 1 << 2, 1 << 3, 1 << 5
# Platinum's TRIGGERS_KINGS_ROCK in a bit Black 2 doesn't use (no move has bits 14 to 31, and its code tests flags
# 0 to 13 only), for a King's Rock handler of the port's (GAME-82, D1): game/include/gen5/gen5_move_data.h
# G5_MOVE_FLAG_KINGS_ROCK says the same
B2_FLAG_KINGS_ROCK = 1 << 14
FLAGS_FROM_PLATINUM = [(PT_FLAG_PROTECT, B2_FLAG_PROTECT), (PT_FLAG_MAGIC_COAT, B2_FLAG_REFLECTABLE),
                       (PT_FLAG_SNATCH, B2_FLAG_SNATCH), (PT_FLAG_KINGS_ROCK, B2_FLAG_KINGS_ROCK)]
# The sound flag (Soundproof) stays Black 2's: it's on Platinum's sSoundMoves (battle_lib.c) and on Perish Song and
# Heal Bell, which Platinum's table doesn't mark but its code keeps from Soundproof Pokémon (BtlCmd_TryPerishSong,
# BtlCmd_TryPartyStatusRefresh), the same 14 moves Black 2 marks.

MOVE_GROWTH, MOVE_MINIMIZE, MOVE_CURSE, MOVE_BEAT_UP, MOVE_TAIL_GLOW, MOVE_ME_FIRST = 74, 107, 174, 251, 294, 382
# Black 2's power stays for Me First, which its code uses as a marker (the copied move's power is used; GAME-80, B17).
# Beat Up takes Platinum's 10: the port's handler deals Platinum's damage per party member with it (gen5_moves.c,
# GAME-80 B14), where Black 2's set each hit's power in code
KEEP_POWER = {MOVE_ME_FIRST}
# Curse's type: Platinum's ??? (its type 9), as Black 2's type 17, which Black 2 keeps for typeless moves (pokebw2
# TYPE_NULL: neutral against every type and every type against it, no same-type bonus, never a Pokémon's own), as
# Platinum's ??? is; Platinum's Conversion rule and look for it are game/src/gen5/gen5_types.c's and mystery_type.py's
B2_TYPE_MYSTERY = 17
CURSE_TYPE = B2_TYPE_MYSTERY
MOVE_TRANSFORM, MOVE_SKETCH = 144, 166
# Platinum's rule of which status moves pass a Substitute, where Black 2's flag 13 differs (GAME-130). Platinum has no
# flag: a move stops at a Substitute when its script checks one (CheckSubstitute, BtlCmd_ChangeStatStage,
# BtlCmd_TryMimic). A Ghost's Curse (subscript_curse_ghost.s, GAME-80 B17) and Sketch (subscript_sketch.s) check it, so
# Black 2's drop of a status move's targets behind a Substitute (btl_server_flow.c func_ov167_021a2c5c, the flag's only
# reader) takes them out: "But it failed!". Transform doesn't (subscript_transform_into_target.s), so it passes, and the
# port's TransformSet copies the Pokémon behind the doll (game/src/gen5/gen5_rules_moves.c). Mimic's stays Black 2's
# (set): the port's handler fails it at a Substitute (gen5_moves.c Gen5Moves_Mimic), the same line. Defog's too: its
# clearing goes on behind a Substitute in Platinum, and its evasion drop's failure is gen5_rules_moves.c's
SUBSTITUTE_BYPASS = {MOVE_CURSE: False, MOVE_SKETCH: False, MOVE_TRANSFORM: True}
# Platinum's stat changes for the moves whose Black 2 records differ (Platinum keeps them in its effect scripts:
# effect_script_0013.s Sp. Atk +1, effect_script_0053.s Sp. Atk +2, subscript_minimize.s evasion +1), as Black 2's
# stats (BATTLEMON_*_STAGE: 3 Sp. Atk, 7 evasion) and stages, with Platinum's effect ids, which Black 2 numbers the
# same (13 SP_ATK_UP, 53 SP_ATK_UP_2; Black 2's Nasty Plot is 53): the trainer AI reads them. Black 2's Growth handler
# (its boost in sunshine) is a rule of its own, GAME-80's (B17).
B2_STAT_SP_ATK, B2_STAT_EVASION = 3, 7
STAT_CHANGES = {MOVE_GROWTH: [(B2_STAT_SP_ATK, 1)], MOVE_TAIL_GLOW: [(B2_STAT_SP_ATK, 2)],
                MOVE_MINIMIZE: [(B2_STAT_EVASION, 1)]}
EFFECTS = {MOVE_GROWTH: 13, MOVE_TAIL_GLOW: 53}

# Turn ranges. Black 2 draws a condition's turns as min + BattleRandom(max - min + 1) (btl_calc.c
# func_ov167_021bd3a0, from func_ov167_021bd484 with the record's duration kind) and counts them the way Platinum
# counts its own counter:
# - Binding (duration kind 4): the end of each turn adds one to the Pokémon's counter and frees it when the counter
#   reaches the turns (btl_pokeparam.c func_ov167_021bb864), so N turns are N - 1 turns of damage, as Platinum's
#   counter of N (subscript_bind_start.s: Random 3, 3, a counter of 3 to 6, 2 to 5 turns of damage). Black 2's 5-6
#   becomes Platinum's 3-6.
# - Sleep (duration kind 2): each move attempt adds one (two with Early Bird) and the Pokémon wakes when the counter
#   reaches the turns (func_ov167_021bb930), so N turns are N - 1 turns asleep, as Platinum's counter of N
#   (subscript_fall_asleep.s: Random 3, 2, 2 to 5, asleep 1 to 4 turns). Black 2's 2-4 becomes Platinum's 2-5.
# Disable's (4) is another ticket's; sleep and binding from other sources (Yawn, Grip Claw...) too (GAME-80, B2, D4).
BIND_DURATION, SLEEP_DURATION = 4, 2
TURN_RANGES = {
    BIND_DURATION: ((3, 6), [20, 35, 83, 128, 250, 328, 463]),  # Bind, Wrap, Fire Spin, Clamp, Whirlpool, Sand Tomb,
    # Magma Storm
    SLEEP_DURATION: ((2, 5), [47, 79, 95, 142, 147, 320, 464]),  # Sing, Sleep Powder, Hypnosis, Lovely Kiss, Spore,
    # GrassWhistle, Dark Void
}


def b2_target(move: int, b2: int, pt_range: int) -> int:
    if move in TARGET_OVERRIDES:
        return TARGET_OVERRIDES[move]
    if move in KEEP_TARGET or b2 in PT_TARGETS_EITHER.get(pt_range, ()):
        return b2
    return PT_TARGETS[pt_range]


def convert_move(move: int, record: bytes, platinum: bytes) -> bytes:
    out = bytearray(record)
    pt_flags = platinum[PT_FLAGS]
    if move not in KEEP_POWER:
        out[B2_POWER] = platinum[PT_POWER]
    out[B2_ACCURACY] = platinum[PT_ACCURACY] or B2_NEVER_MISSES
    out[B2_PP] = platinum[PT_PP]
    out[B2_PRIORITY] = platinum[PT_PRIORITY]
    out[B2_TARGET] = b2_target(move, record[B2_TARGET], struct.unpack_from("<H", platinum, PT_RANGE)[0])
    flags = struct.unpack_from("<I", record, B2_FLAGS)[0]
    for pt_bit, b2_bit in FLAGS_FROM_PLATINUM:
        flags = flags | b2_bit if pt_flags & pt_bit else flags & ~b2_bit
    if move in SUBSTITUTE_BYPASS:
        flags = flags | B2_FLAG_BYPASS_SUBSTITUTE if SUBSTITUTE_BYPASS[move] else flags & ~B2_FLAG_BYPASS_SUBSTITUTE
    if move == MOVE_CURSE:
        if platinum[PT_TYPE] != PT_TYPE_MYSTERY:
            raise ValueError(f"Platinum's Curse has type {platinum[PT_TYPE]}, not ???")
        out[B2_TYPE] = CURSE_TYPE
    struct.pack_into("<I", out, B2_FLAGS, flags)
    if move in STAT_CHANGES:
        changes = STAT_CHANGES[move] + [(0, 0)] * (3 - len(STAT_CHANGES[move]))
        for i, (stat, stages) in enumerate(changes):
            out[B2_STATS + i] = stat
            struct.pack_into("<b", out, B2_STAGES + i, stages)
    if move in EFFECTS:
        struct.pack_into("<H", out, B2_EFFECT, EFFECTS[move])
    for duration, ((low, high), moves) in TURN_RANGES.items():
        if move in moves:
            if record[B2_DURATION] != duration:
                raise ValueError(f"move {move}: Black 2's record has duration kind {record[B2_DURATION]}")
            out[B2_MIN_TURNS], out[B2_MAX_TURNS] = low, high
    return bytes(out)


def build_moves(data: bytes, platinum) -> bytes:
    narc = nitro.NARC(data)
    table = platinum.narc(PLATINUM_MOVES)
    for move in range(1, MOVE_COUNT + 1):
        narc.files[move] = convert_move(move, narc.files[move], table[move])
    return narc.save()


# --- Items

# Black 2's item record (0x24 bytes, pokebw2 tools/data/item_data.py) and Platinum's (0x22 in the archive,
# include/item.h ItemData) share their start: 0x03 the hold effect's parameter, 0x08 a u16 whose bits 11-15 are the
# battle pockets (the same pockets in both). The party-use fields follow at 0x10 in Black 2's and 0x0E in Platinum's:
# their byte 6 has the friendship flags (bits 1-3), their bytes 15-17 the three friendship changes
ITEM_HOLD_PARAM, ITEM_POCKET_BITS = 0x03, 0x08
BATTLE_POCKET_MASK = 0x1F << 11
B2_ITEM_PARTY, PT_ITEM_PARTY = 0x10, 0x0E
FRIENDSHIP_FLAGS, FRIENDSHIP_CHANGES = 6, 15
FRIENDSHIP_FLAG_MASK = 0x0E
ITEM_X_SP_DEF, ITEM_BLUE_FLUTE, ITEM_YELLOW_FLUTE, ITEM_RED_FLUTE, ITEM_METRONOME = 62, 65, 66, 67, 277
# Platinum's items have no data for IDs 113 to 134, which don't exist: its archive skips them (item_id_map.h)
PT_ITEM_GAP_START, PT_ITEM_GAP = 113, 22


def platinum_item(item: int) -> int:
    """An item's member in Platinum's item data."""
    return item if item < PT_ITEM_GAP_START else item - PT_ITEM_GAP


def build_items(data: bytes, platinum) -> bytes:
    narc = nitro.NARC(data)
    table = platinum.narc(PLATINUM_ITEMS)
    records = {item: bytearray(narc.files[item]) for item in
               (ITEM_X_SP_DEF, ITEM_BLUE_FLUTE, ITEM_YELLOW_FLUTE, ITEM_RED_FLUTE, ITEM_METRONOME)}
    pt = {item: table[platinum_item(item)] for item in records}
    for item in records:
        # The same item in both: its Fling and Natural Gift data (bytes 4 to 7) agree
        if records[item][4:8] != pt[item][4:8]:
            raise ValueError(f"item {item}: Platinum's item data isn't that item's")
    # The Metronome (D2): +10% a repeat up to ×2 after 10, Platinum's, where Black 2's 20 gives +20% to ×2 after 5
    records[ITEM_METRONOME][ITEM_HOLD_PARAM] = pt[ITEM_METRONOME][ITEM_HOLD_PARAM]
    # The flutes (D9): Platinum's battle pocket (status restore), where Black 2 gives none
    for item in (ITEM_BLUE_FLUTE, ITEM_YELLOW_FLUTE, ITEM_RED_FLUTE):
        bits = struct.unpack_from("<H", records[item], ITEM_POCKET_BITS)[0] & ~BATTLE_POCKET_MASK
        bits |= struct.unpack_from("<H", pt[item], ITEM_POCKET_BITS)[0] & BATTLE_POCKET_MASK
        struct.pack_into("<H", records[item], ITEM_POCKET_BITS, bits)
    # X Sp. Def's friendship (J5): Platinum's changes none, where Black 2's +1/+1/0 is the other X items'. Black 2 marks
    # the changes with other flag bits than Platinum (bits 2-3 where Platinum's other X items have 1-2), so its flags
    # are cleared only when Platinum's are
    b2_party, pt_party = B2_ITEM_PARTY, PT_ITEM_PARTY
    x = records[ITEM_X_SP_DEF]
    pt_x = pt[ITEM_X_SP_DEF]
    if pt_x[pt_party + FRIENDSHIP_FLAGS] & FRIENDSHIP_FLAG_MASK:
        raise ValueError("Platinum's X Sp. Def changes friendship: write its flags in Black 2's order")
    x[b2_party + FRIENDSHIP_FLAGS] &= ~FRIENDSHIP_FLAG_MASK
    x[b2_party + FRIENDSHIP_CHANGES:b2_party + FRIENDSHIP_CHANGES + 3] = \
        pt_x[pt_party + FRIENDSHIP_CHANGES:pt_party + FRIENDSHIP_CHANGES + 3]
    for item, record in records.items():
        narc.files[item] = bytes(record)
    return narc.save()


# --- Species

PERSONAL_TYPES = 6  # two types, the same place in both games' personal records
PERSONAL_FORM_START, PERSONAL_FORM_COUNT = 0x1C, 0x20  # Black 2's form table (as platinum_learnsets.py reads it)
SPECIES_ROTOM = 479
PT_ROTOM_FORMS, ROTOM_APPLIANCES = 503, 5  # Platinum's Heat, Wash, Frost, Fan and Mow Rotom, in Black 2's order
PT_TYPE_MYSTERY = 9  # Platinum's ??? type: Black 2's types are Platinum's without it


def b2_type(pt_type: int) -> int:
    if pt_type == PT_TYPE_MYSTERY:
        raise ValueError("Black 2 has no ??? type")
    return pt_type if pt_type < PT_TYPE_MYSTERY else pt_type - 1


def build_personal(data: bytes, platinum) -> bytes:
    narc = nitro.NARC(data)
    table = platinum.narc(PLATINUM_PERSONAL)
    rotom = narc.files[SPECIES_ROTOM]
    start = struct.unpack_from("<H", rotom, PERSONAL_FORM_START)[0]
    if rotom[PERSONAL_FORM_COUNT] != ROTOM_APPLIANCES + 1:
        raise ValueError("Black 2's Rotom hasn't six forms")
    # Black 2's form table lists the forms after the first, Heat Rotom first, as Platinum's archive does from 503
    for k in range(ROTOM_APPLIANCES):
        record = bytearray(narc.files[start + k])
        pt = table[PT_ROTOM_FORMS + k]
        record[PERSONAL_TYPES:PERSONAL_TYPES + 2] = bytes(b2_type(t) for t in pt[PERSONAL_TYPES:PERSONAL_TYPES + 2])
        narc.files[start + k] = bytes(record)
    return narc.save()
