"""Black 2's seven wings (GAME-59) under their later name, Feather (GAME-156, the owner's): "Health Feather" to
"Pretty Feather" in Black 2's system text (a/0/0/2), whose names Black 2's battle shows for a held item ("Chimchar
flung its Health Feather!"). The names are in three banks, NAME_BANK, ARTICLE_BANK ("a Health Feather") and
PLURAL_BANK, at the items' IDs; Platinum's side has them in game/res/items/data/*_wing.json. The messages are rewritten
by pokedex_text.patch.
"""
NAME_BANK = 64
ARTICLE_BANK = 481
PLURAL_BANK = 482
BANKS = (NAME_BANK, ARTICLE_BANK, PLURAL_BANK)
# ITEM_HEALTH_WING to ITEM_PRETTY_WING (Black 2's IDs)
WINGS = range(565, 572)


def words(bank: int, message: int) -> dict:
    """The words to replace in a message of the item name banks: only the wings', "Wing" ("Wings" in the plurals)."""
    return {"Wing": "Feather"} if message in WINGS else {}
