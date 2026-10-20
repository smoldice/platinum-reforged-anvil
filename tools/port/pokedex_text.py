"""Sinnoh in Black 2's Pokédex's texts: the list's and the search's banks of Black 2's system text (a/0/0/2, banks
LIST_BANK and SEARCH_BANK: "UNOVA POKéDEX", "Unova Pokédex: Search Mode" and the like) and the habitat list's
(HABITAT_BANK: the area list's "UNOVA" button, "Explore all of the Unova region!") say Sinnoh where they say Unova, in
each string's own capitals ("UNOVA" to "SINNOH", "Unova" to "Sinnoh"), as the port's Pokédex shows Platinum's Sinnoh
Pokédex (docs/pokedex-port.md, section 4). The habitat list's message names the time of day where an area's land
differs by it, as Black 2's names the season (zukan_habitat.c PrintHabitat: the kind's message + the season + 1): its
first three seasons become Platinum's times of day in Black 2's capitals, "(Morning)", "(Day)", "(Night)" (the owner's,
GAME-137), and Black 2's swamp messages for summer to winter, which say "sand", say "swamp" (the Great Marsh's land
differs by time). The messages are encrypted as battle_text.py reads them.
"""
import struct

import battle_text

LIST_BANK = 478
SEARCH_BANK = 479
HABITAT_BANK = 362
BANKS = (LIST_BANK, SEARCH_BANK, HABITAT_BANK)
WORDS = {"UNOVA": "SINNOH", "Unova": "Sinnoh"}
# The habitat list's seasons as times of day, in every message of its bank
BANK_WORDS = {HABITAT_BANK: {"(Spring)": "(Morning)", "(Summer)": "(Day)", "(Autumn)": "(Night)"}}
# Black 2's swamp messages for summer, autumn and winter (Bank0362_Text_SummerPokemonLivingSand_2 and the two after
# it), which say sand
SWAMP_MESSAGES = (12, 13, 14)
MESSAGE_WORDS = {(HABITAT_BANK, m): {"sand": "swamp"} for m in SWAMP_MESSAGES}


def replaced(chars: list, words=WORDS):
    """The message with the words replaced, or None if it has none. Only text: a control code's arguments are left as
    they are."""
    out, i, changed = [], 0, False
    while i < len(chars):
        if chars[i] == battle_text.CONTROL:
            end = i + 3 + chars[i + 2]
            out += chars[i:end]
            i = end
            continue
        for old, new in words.items():
            if chars[i:i + len(old)] == [ord(c) for c in old]:
                out += [ord(c) for c in new]
                i += len(old)
                changed = True
                break
        else:
            out.append(chars[i])
            i += 1
    return out if changed else None


def pokedex_words(bank: int, message: int) -> dict:
    """The words to replace in a message of the Pokédex's banks."""
    return dict(WORDS, **BANK_WORDS.get(bank, {}), **MESSAGE_WORDS.get((bank, message), {}))


def patch(data: bytes, bank: int = None, words_for=pokedex_words):
    """The bank with its messages renamed (words_for(bank, message): the words to replace in one), and the (index,
    before, after) of each changed message."""
    sections, count = struct.unpack_from("<HH", data, 0)
    section = struct.unpack_from("<I", data, 12)[0]
    assert sections == 1
    messages, changed = [], []
    for i in range(count):
        offset, length, attribute = struct.unpack_from("<IHH", data, section + 4 + 8 * i)
        raw = list(struct.unpack_from(f"<{length}H", data, section + offset))
        chars = battle_text.decrypt(raw)
        new = None if chars[0] == battle_text.COMPRESSED else replaced(chars, words_for(bank, i))
        if new is not None:
            changed.append((i, chars, new))
            raw = battle_text.encrypt(new, i)
        messages.append((raw, attribute))
    if not changed:
        return data, changed
    table = b""
    body = b""
    offset = 4 + 8 * count
    for chars, attribute in messages:
        table += struct.pack("<IHH", offset, len(chars), attribute)
        body += struct.pack(f"<{len(chars)}H", *chars)
        offset += 2 * len(chars)
    size = (4 + len(table) + len(body) + 3) & ~3
    out = struct.pack("<I", size) + table + body
    out += bytes(size - len(out))
    return struct.pack("<HHIII", 1, count, size, 0, 16) + out, changed
