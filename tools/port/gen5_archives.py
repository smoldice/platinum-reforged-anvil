"""What the port does to Black 2's archives, one at a time: extract_assets.py writes them into the game's build, and
Anvil makes the same on the player's machine from their own two ROMs, so its download doesn't carry the art made
from Nintendo's (make_trainer_sprites.py, platinum_battle_menus.py, …).

- convert(arc, data, gen5_file, platinum): Black 2's archive `arc` (its bytes, data) as the port's ROM has it.
  gen5_file(path) reads another of Black 2's files; platinum is a PlatinumRom (platinum_rom.py).
- platinum_copy(arc, converted, platinum): the copy in Platinum's look an archive in platinum_battle_menus.ARCHIVES
  gets, for the BATTLE MENUS option, at ptui/ + its path.
"""
import nitro

import battle_text
import lower_screen_sets
import make_trainer_sprites
import platinum_battle_menus
import platinum_learnsets
import platinum_ui

# By archive, Black 2's file and White 2's that the code loads instead (pokebw2: btlv_gauge.c, btlv_input.c,
# b_bag_main.c, b_plist_main.c): the battle's lower screen, gauges, bag and party list take White 2's palettes, the
# user's choice, since white suits Platinum's own interface better. Both games ship both palettes and pick one with
# `#ifdef BLACK2`
W2_UI = {
    11: {0x1AF: 0x1AE, 0x1B1: 0x1B0, 0x168: 0x167},
    98: {2: 1},
    99: {20: 19},
}
# Black 2's system text, whose battle messages say the player's name (battle_text.py)
SYSTEM_TEXT = 2
# Black 2's trainer sprites, which become Platinum's (make_trainer_sprites.py)
TRAINER_FRONTS = 71
TRAINER_BACKS = 72


def path(arc: int) -> str:
    """A Gen V archive's path in the ROM: a/0/7/1 for 71."""
    return f"a/{arc // 100}/{arc // 10 % 10}/{arc % 10}"


def use_white2_ui(arc: int, data: bytes) -> bytes:
    if arc not in W2_UI:
        return data
    narc = nitro.NARC(data)
    for black2, white2 in W2_UI[arc].items():
        narc.files[black2] = narc.files[white2]
    return narc.save()


def convert(arc: int, data: bytes, gen5_file, platinum, log=lambda *args: None) -> bytes:
    data = use_white2_ui(arc, data)
    if arc in platinum_ui.ARCHIVES:
        # Platinum's colours for the interface, before the lower screen's copies are made
        narc = nitro.NARC(data)
        platinum_ui.apply(arc, narc)
        data = narc.save()
    if arc == lower_screen_sets.ARCHIVE:
        data = lower_screen_sets.build(data)
    if arc == SYSTEM_TEXT:
        narc = nitro.NARC(data)
        narc.files[battle_text.BANK], changed = battle_text.patch(narc.files[battle_text.BANK])
        log(changed, "battle messages with the player's name")
        data = narc.save()
    if arc == TRAINER_FRONTS:
        data = make_trainer_sprites.update_fronts(data, platinum)
    if arc == TRAINER_BACKS:
        data = make_trainer_sprites.update_backs(data, platinum)
    if arc == platinum_learnsets.ARCHIVE:
        data = platinum_learnsets.build(data, gen5_file(platinum_learnsets.PERSONAL), platinum)
    return data


def platinum_copy(arc: int, converted: bytes, platinum) -> bytes:
    return platinum_battle_menus.build(arc, converted, platinum)
