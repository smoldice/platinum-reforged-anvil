#!/usr/bin/env python3
"""Puts the player's name in Black 2's battle messages that say "Player": "Player defeated Youngster Tristan!", and
the ones for losing, a draw and two opponents. Both games' English text has the word itself there (Platinum's
BattleStrings_Text_PlayerDefeatedTr too); the user asked for their name.

The battle fills a message's name tags from its arguments, and the arguments it doesn't pass are 0, which is the
player's client (btl_string.c, btl_client.c). So "Player" becomes a trainer name tag, {0100:N}, on the first argument
the message leaves unused. A trainer class tag ({010e:N}) uses its trainer's argument again, which shifts the tags
after it back by one; N counts that in.

The EXPERIENCE option's MODERN has one message Black 2 doesn't, for the experience the rest of the team gets
(gen5_experience.c). It goes after the bank's own, as message REST_OF_TEAM. The LEVEL CAPS option's line for a Pokémon
the cap keeps from gaining experience follows it, as message LEVEL_CAP, with the Pokémon's name as Black 2's "… gained
… Exp. Points!" has it.

The messages are in Black 2's system text, a/0/0/2, file BANK: each one encrypted with a key that starts at
0x7c89 + 0x2983 times its index and rotates by 3 bits per character (pokebw2: tools/text/text_data.py).
"""
import struct

BANK = 19
CONTROL = 0xF000
COMPRESSED = 0xF100
LINE_END = 0xFFFF
TRAINER_NAME = 0x0100
TRAINER_CLASS = 0x010E
WORD = "Player"
LINE_BREAK = 0xFFFE
# The message the rest of the team's experience shows (G5_MSG_REST_OF_TEAM_EXP in gen5_experience.c), after Black 2's
# 201 messages
REST_OF_TEAM = 201
REST_OF_TEAM_TEXT = "The rest of your team gained\nExp. Points!"
# The level cap's line (G5_MSG_LEVEL_CAP in gen5_experience.c): the name of the Pokémon of the message's first argument
# (a party nickname tag, as Black 2's message 42 has), then the text
LEVEL_CAP = 202
POKEMON_NICKNAME = 0x010C
LEVEL_CAP_TEXT = " can't gain more\nExp. Points!"


def decrypt(chars):
    chars = list(chars)
    key = chars[-1] ^ LINE_END
    for i in reversed(range(len(chars))):
        chars[i] ^= key
        key = ((key >> 3) | (key << 13)) & 0xFFFF
    return chars


def encrypt(chars, index):
    key = (0x7C89 + 0x2983 * index) & 0xFFFF
    out = []
    for c in chars:
        out.append(c ^ key)
        key = ((key << 3) | (key >> 13)) & 0xFFFF
    return out


def text(string):
    """A message's characters, with its line breaks and its end."""
    return [LINE_BREAK if c == "\n" else ord(c) for c in string] + [LINE_END]


def tags(chars):
    """The message's control codes, as (position, kind, arguments)."""
    out = []
    i = 0
    while i < len(chars):
        if chars[i] == CONTROL:
            count = chars[i + 2]
            out.append((i, chars[i + 1], chars[i + 3:i + 3 + count]))
            i += 3 + count
        else:
            i += 1
    return out


def with_player(chars):
    """The message with its leading "Player" as the player's name, or None if it doesn't start with it."""
    word = [ord(c) for c in WORD]
    if chars[:len(word)] != word or chars[0] == COMPRESSED:
        return None
    words = [(kind, args[0]) for _, kind, args in tags(chars) if kind >> 8 in (1, 2) and args]
    if not any(kind == TRAINER_NAME for kind, _ in words):
        return None
    # One past the last tag: the class tags shift it back onto the first argument the message leaves unused
    param = max(param for _, param in words) + 1
    return [CONTROL, TRAINER_NAME, 1, param] + chars[len(word):]


def patch(data: bytes):
    """The message file with the changed messages, and how many changed."""
    sections, count = struct.unpack_from("<HH", data, 0)
    section = struct.unpack_from("<I", data, 12)[0]
    assert sections == 1 and count == REST_OF_TEAM
    messages, changed = [], 0
    for i in range(count):
        offset, length, attribute = struct.unpack_from("<IHH", data, section + 4 + 8 * i)
        chars = decrypt(struct.unpack_from(f"<{length}H", data, section + offset))
        new = with_player(chars)
        if new is not None:
            chars = new
            changed += 1
        messages.append((encrypt(chars, i) if new is not None else
                         list(struct.unpack_from(f"<{length}H", data, section + offset)), attribute))
    rest = text(REST_OF_TEAM_TEXT)
    messages.append((encrypt(rest, REST_OF_TEAM), 0))
    capped = [CONTROL, POKEMON_NICKNAME, 1, 0] + text(LEVEL_CAP_TEXT)
    messages.append((encrypt(capped, LEVEL_CAP), 0))
    count += 2
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
