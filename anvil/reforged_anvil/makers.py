"""The parts of Platinum Reforged made on the player's machine from their own two ROMs: the art the port converts
from Nintendo's (Platinum's trainers as Black 2's sprites, the battle's Touch Screen menus in Platinum's look, its
interface in Platinum's colours), so Anvil's download carries none of it. The makers are the game build's own
converters (tools/port/gen5_archives.py and what it calls; the program carries them), run on the player's ROMs; the
bundle checks what they make by SHA-1, as it checks everything else.

A Maker reads parts of both ROMs, and notes each (`reads`, by the references bundle.resolve takes): the release
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
import make_overworld_sprites  # noqa: E402
from platinum_rom import PlatinumRom  # noqa: E402

# The archives made here: Black 2's trainer sprites with Platinum's trainers (71, 72); the battle's interface in
# Platinum's colours (11, 49, 98, 99), which the copies in Platinum's look are made from; those copies (ptui/); and
# Platinum's overworld sprites with Black 2's after them
ARCHIVES = (11, 49, 71, 72, 98, 99)
COPIES = (11, 49, 98, 99)
COPY_PREFIX = "ptui/"
OVERWORLD = make_overworld_sprites.PLATINUM_ARCHIVE
# The settings modules make_trainer_sprites.py imports by name (its RETEXTURES and RIGS), which PyInstaller can't see
HIDDEN_IMPORTS = ["retexture_ace_trainer_male", "retexture_ace_trainer_female", "retexture_fisherman",
                  "retexture_worker", "retexture_lass", "retexture_waitress", "rig_roughneck", "rig_clown",
                  "rig_aroma_lady"]


def names() -> list:
    """The regions made, as the bundle names them."""
    return ([f"file:{gen5_archives.path(a)}" for a in ARCHIVES]
            + [f"file:{COPY_PREFIX}{gen5_archives.path(a)}" for a in COPIES] + [f"file:{OVERWORLD}"])


class Maker:
    """Makes the regions from one pair of ROMs (Anvil's nds.Rom), each once."""

    def __init__(self, platinum, gen5):
        self.reads = {"platinum": {}, "gen5": {}}

        def reader(rom_name, kind, read):
            def read_noted(arg):
                data = read(arg)
                self.reads[rom_name].setdefault(f"{kind}:{arg}", data)
                return data
            return read_noted

        self.gen5_file = reader("gen5", "file", gen5.file_by_path)
        self.platinum = PlatinumRom(reader("platinum", "file", platinum.file_by_path),
                                    reader("platinum", "overlay", platinum.overlay))
        self._made = {}

    def make(self, name: str) -> bytes:
        if name not in self._made:
            path = name[len("file:"):]
            # What the converters print is for the game's build, not the player
            with contextlib.redirect_stdout(io.StringIO()):
                if path == OVERWORLD:
                    data = make_overworld_sprites.archive(self.platinum, self.gen5_file)
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
