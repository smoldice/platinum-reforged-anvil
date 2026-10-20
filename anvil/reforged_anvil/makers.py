"""The parts of Platinum Reforged made on the player's machine from their own two ROMs: the art the port converts
from Nintendo's (Platinum's trainers as Black 2's sprites, the battle's Touch Screen menus in Platinum's look, its
interface in Platinum's colours), so Anvil's download carries none of it. And from their HeartGold or SoulSilver if
they give one, the following Pokémon's art and texts (tools/port/make_follow_mon.py, one archive, the same from both). The makers are the game build's own
converters (tools/port/gen5_archives.py and what it calls; the program carries them), run on the player's ROMs; the
bundle checks what they make by SHA-1, as it checks everything else.

A Maker reads parts of the ROMs, and notes each (`reads`, by the references bundle.resolve takes): the release
records their SHA-1s, and the player's are checked against them before anything is made, so a ROM that isn't clean
is named as it is for the rest of the build.
"""
import contextlib
import io
import sys
from pathlib import Path

PORT = Path(__file__).resolve().parents[2] / "tools" / "port"
if not getattr(sys, "frozen", False) and PORT.is_dir() and str(PORT) not in sys.path:
    sys.path.insert(0, str(PORT))

import gen5_archives  # noqa: E402
import make_follow_mon  # noqa: E402
import make_trainer_sprites  # noqa: E402
from platinum_rom import PlatinumRom  # noqa: E402

# The archives made here: Black 2's trainer sprites with Platinum's trainers (71, 72); the battle's interface in
# Platinum's colours (11, 49, 98, 99), which the copies in Platinum's look are made from; those copies (ptui/); the
# evolution scene's background in the egg scene's green (179); the battle's data with Platinum's numbers: the moves
# (21), a few items (24) and Rotom's forms' types (16) (platinum_battle_data.py); the type tags with Platinum's
# ??? type's, in Black 2's tag style (82) (mystery_type.py, which also adds ???'s move tile palette to 11); the
# Pokédex's search data with Platinum's Sinnoh order and Vespiquen's shape (97) (pokedex_search.py); the town map's
# art with Platinum's Sinnoh map, for the Pokédex's area page (84) (dex_map_art.py). The copies also include the
# Pokédex's art in Platinum's look (157, pokedex_art.py), made from Black 2's as it is
ARCHIVES = (11, 16, 21, 24, 49, 71, 72, 82, 84, 97, 98, 99, 179)
COPIES = (11, 49, 98, 99, 157)
COPY_PREFIX = "ptui/"
# The following Pokémon's archive, made from the optional HeartGold or SoulSilver (with nothing in it without one)
FOLLOW_MON = f"file:{make_follow_mon.PATH}"
# The settings modules make_trainer_sprites.py imports by name (its RETEXTURES and RIGS, the rigs packed from Aseprite
# among them), which PyInstaller and the site's module finder can't see
HIDDEN_IMPORTS = [*make_trainer_sprites.RETEXTURES.values(), *make_trainer_sprites.RIGS.values()]


def names() -> list:
    """The regions made from both ROMs, as the bundle names them."""
    return ([f"file:{gen5_archives.path(a)}" for a in ARCHIVES]
            + [f"file:{COPY_PREFIX}{gen5_archives.path(a)}" for a in COPIES])


def follow_mon_archive(hgss_file=None) -> bytes:
    """The following Pokémon's archive, from HeartGold's or SoulSilver's files; with nothing in it without them."""
    return make_follow_mon.archive(hgss_file)


class Maker:
    """Makes the regions from one pair of ROMs (Anvil's nds.Rom), and HeartGold or SoulSilver if given, each once."""

    def __init__(self, platinum, gen5, hgss=None):
        self.reads = {"platinum": {}, "gen5": {}, "hgss": {}}

        def reader(rom_name, kind, read):
            def read_noted(arg):
                data = read(arg)
                self.reads[rom_name].setdefault(f"{kind}:{arg}", data)
                return data
            return read_noted

        self.gen5_file = reader("gen5", "file", gen5.file_by_path)
        self.hgss_file = reader("hgss", "file", hgss.file_by_path) if hgss is not None else None
        self.platinum = PlatinumRom(reader("platinum", "file", platinum.file_by_path),
                                    reader("platinum", "overlay", platinum.overlay))
        self._made = {}

    def make(self, name: str) -> bytes:
        if name not in self._made:
            path = name[len("file:"):]
            # What the converters print is for the game's build, not the player
            with contextlib.redirect_stdout(io.StringIO()):
                if name == FOLLOW_MON:
                    data = follow_mon_archive(self.hgss_file)
                elif path.startswith(COPY_PREFIX):
                    arc = self._arc(path[len(COPY_PREFIX):])
                    data = gen5_archives.platinum_copy(arc, self.make(f"file:{gen5_archives.path(arc)}"),
                                                       self.platinum)
                else:
                    arc = self._arc(path)
                    data = gen5_archives.convert(arc, self.gen5_file(path), self.gen5_file, self.platinum)
            self._made[name] = data
        return self._made[name]

    @staticmethod
    def _arc(path: str) -> int:
        _, a, b, c = path.split("/")
        return int(a) * 100 + int(b) * 10 + int(c)
