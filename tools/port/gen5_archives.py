"""What the port does to Black 2's archives, one at a time: extract_assets.py writes them into the game's build, and
Anvil makes the same on the player's machine from their own two ROMs, so its download doesn't carry the art made
from Nintendo's (make_trainer_sprites.py, platinum_battle_menus.py, …).

- convert(arc, data, gen5_file, platinum): Black 2's archive `arc` (its bytes, data) as the port's ROM has it.
  gen5_file(path) reads another of Black 2's files; platinum is a PlatinumRom (platinum_rom.py).
- platinum_copy(arc, converted, platinum): the copy in Platinum's look an archive in COPIES gets, at ptui/ + its
  path, which the game opens in its place.
"""
import nitro

import battle_text
import dex_area_picture
import dex_map_art
import evolution_background
import item_text
import lower_screen_sets
import make_trainer_sprites
import mystery_type
import platinum_battle_data
import platinum_battle_menus
import platinum_learnsets
import platinum_ui
import pokedex_art
import pokedex_search
import pokedex_text

# By archive, Black 2's file and White 2's that the code loads instead (pokebw2: btlv_gauge.c, btlv_input.c,
# b_bag_main.c, b_plist_main.c): the battle's lower screen, gauges, bag and party list take White 2's palettes, the
# user's choice, since white suits Platinum's own interface better. Both games ship both palettes and pick one with
# `#ifdef BLACK2`
W2_UI = {
    11: {0x1AF: 0x1AE, 0x1B1: 0x1B0, 0x168: 0x167},
    98: {2: 1},
    99: {20: 19},
}
# Black 2's system text, whose battle messages say the player's name (battle_text.py), whose Pokédex titles say
# Sinnoh (pokedex_text.py) and whose item names call the wings feathers (item_text.py)
SYSTEM_TEXT = 2
# Black 2's trainer sprites, which become Platinum's (make_trainer_sprites.py)
TRAINER_FRONTS = 71
TRAINER_BACKS = 72
# The archives with a copy in Platinum's look (platinum_copy): the battle's menus', and
# the Pokédex's art (pokedex_art.py: the registration after a catch)
COPIES = platinum_battle_menus.ARCHIVES + (pokedex_art.ARCHIVE,)


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
    # Platinum's ??? type's look, Curse's (mystery_type.py): its move tile's palette, after the lower screen sets, and
    # its type icon
    if arc == mystery_type.TILE_ARCHIVE:
        data = mystery_type.add_tile_palette(data, platinum)
    if arc == mystery_type.ICON_ARCHIVE:
        data = mystery_type.add_icon(data, platinum)
    if arc == SYSTEM_TEXT:
        narc = nitro.NARC(data)
        narc.files[battle_text.BANK], changed = battle_text.patch(narc.files[battle_text.BANK])
        log(changed, "battle messages with the player's name")
        # Sinnoh in the Pokédex's titles and the habitat list's times of day (pokedex_text.py)
        for bank in pokedex_text.BANKS:
            narc.files[bank], renamed = pokedex_text.patch(narc.files[bank], bank)
            log(len(renamed), f"Pokédex texts with Sinnoh (and the times of day) in bank {bank}")
        # Black 2's wings as feathers in the item names the battle shows (item_text.py)
        for bank in item_text.BANKS:
            narc.files[bank], renamed = pokedex_text.patch(narc.files[bank], bank, item_text.words)
            log(len(renamed), f"wings named feathers in bank {bank}")
        data = narc.save()
    if arc == TRAINER_FRONTS:
        data = make_trainer_sprites.update_fronts(data, platinum)
    if arc == TRAINER_BACKS:
        data = make_trainer_sprites.update_backs(data, platinum)
    if arc == platinum_learnsets.ARCHIVE:
        data = platinum_learnsets.build(data, gen5_file(platinum_learnsets.PERSONAL), platinum)
    # Platinum's numbers for the battle: its move data, a few items, Rotom's forms' types (platinum_battle_data.py)
    if arc == platinum_battle_data.MOVES_ARCHIVE:
        data = platinum_battle_data.build_moves(data, platinum)
    if arc == platinum_battle_data.ITEMS_ARCHIVE:
        data = platinum_battle_data.build_items(data, platinum)
    if arc == platinum_battle_data.PERSONAL_ARCHIVE:
        data = platinum_battle_data.build_personal(data, platinum)
    if arc == evolution_background.ARCHIVE:
        data = evolution_background.recolour(data)
    # The Pokédex's regional order in Sinnoh's, and Vespiquen's shape as Platinum's (pokedex_search.py)
    if arc == pokedex_search.ARCHIVE:
        data = pokedex_search.build(data, platinum)
    # The town map's art with Sinnoh's map, for the Pokédex's area page and habitat list (dex_map_art.py)
    if arc == dex_map_art.ARCHIVE:
        data = dex_map_art.build(data, platinum)
    return data


def platinum_copy(arc: int, converted: bytes, platinum) -> bytes:
    if arc == pokedex_art.ARCHIVE:
        # Black 2's colours, solid, the area list's picture of Sinnoh (dex_area_picture.py), and the area page's time
        # selector in the bottom right with the owner's layout (dex_map_art.py)
        narc = nitro.NARC(pokedex_art.platinum_copy(converted))
        dex_area_picture.apply(narc, platinum)
        if dex_map_art.OWN_LAYOUT:
            dex_map_art.add_selector(narc)
        return narc.save()
    return platinum_battle_menus.build(arc, converted, platinum)
