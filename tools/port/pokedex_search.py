"""Black 2's Pokédex search data (archive 97, ARCID_ZUKAN_SEARCH) for Platinum's Sinnoh Pokédex (docs/pokedex-port.md,
section 4). Black 2's Pokédex shows the regional list in the order of the archive's file 4 (FILE_NATIONAL_ORDER):
ZukanSearchEngine_LoadList(1) (pokebw2 zukan_search_engine.c) takes from it, in its order, the species the regional
table has (the port's: Platinum's Sinnoh numbers, gen5_pokedex.c), and the search's regional order is the same file.
Black 2's file has all 649 species, those outside Unova's Pokédex first in national order, then Unova's in its order.
The port's: Platinum's 210 in Sinnoh's order (Platinum's zukan_data.narc, member 12), then the other species to 649 in
national order, which the regional table leaves out.

And the shapes (file 2, a byte per species and then the forms'): Black 2's are Platinum's, numbered differently, but
for Vespiquen (Black 2 multi-winged, Platinum winged), which takes Platinum's.

From the player's Platinum ROM, through platinum_rom.py: made on the player's machine (anvil makers.ARCHIVES).
"""
import collections
import struct

import nitro

ARCHIVE = 97
FILE_SHAPES = 2
FILE_REGIONAL_ORDER = 4
NATIONAL_COUNT = 649
# Platinum's Pokédex data (pokeplatinum: tools/dataproc/src/speciesproc.c pack_dexdata): member 2 the shapes, a byte
# per species, member 12 the Sinnoh Pokédex's species in its order. The Altered Forme's archive, as Black 2's
# Giratina (its Origin Forme is a form of its own there)
PLATINUM_DEX_DATA = "application/zukanlist/zkn_data/zukan_data.narc"
PLATINUM_DEX_DATA_ALTERED = "application/zukanlist/zkn_data/zukan_data_gira.narc"
PT_SHAPES = 2
PT_SINNOH_ORDER = 12
SINNOH_COUNT = 210
PLATINUM_SPECIES = 493
SPECIES_VESPIQUEN = 416


def u16s(data: bytes) -> list:
    return list(struct.unpack(f"<{len(data) // 2}H", data))


def regional_order(sinnoh: list) -> bytes:
    """File 4: Sinnoh's species in Sinnoh's order, then the others in national order."""
    assert len(sinnoh) == SINNOH_COUNT and len(set(sinnoh)) == SINNOH_COUNT
    assert all(1 <= s <= PLATINUM_SPECIES for s in sinnoh)
    order = sinnoh + [s for s in range(1, NATIONAL_COUNT + 1) if s not in set(sinnoh)]
    return struct.pack(f"<{len(order)}H", *order)


def shapes(black2: bytes, platinum: bytes) -> bytes:
    """File 2 with Vespiquen's shape as Platinum's, in Black 2's numbering (the one the other species of Platinum's
    shape have in Black 2's file)."""
    pairs = collections.Counter((platinum[s], black2[s]) for s in range(1, PLATINUM_SPECIES + 1))
    numbering = {}
    for (pt, b2), n in pairs.most_common():
        numbering.setdefault(pt, b2)
    differ = [s for s in range(1, PLATINUM_SPECIES + 1) if numbering[platinum[s]] != black2[s]]
    assert differ == [SPECIES_VESPIQUEN], differ
    out = bytearray(black2)
    out[SPECIES_VESPIQUEN] = numbering[platinum[SPECIES_VESPIQUEN]]
    return bytes(out)


def build(data: bytes, platinum) -> bytes:
    narc = nitro.NARC(data)
    assert len(narc.files[FILE_REGIONAL_ORDER]) == 2 * NATIONAL_COUNT
    narc.files[FILE_REGIONAL_ORDER] = regional_order(u16s(platinum.narc(PLATINUM_DEX_DATA)[PT_SINNOH_ORDER]))
    narc.files[FILE_SHAPES] = shapes(narc.files[FILE_SHAPES], platinum.narc(PLATINUM_DEX_DATA_ALTERED)[PT_SHAPES])
    return narc.save()
