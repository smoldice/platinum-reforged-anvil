"""Recognising the player's ROMs: which game, region and revision each is, and whether Anvil can use it."""
import mmap
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

from .nds import FileData, Rom

# The games Anvil takes: (input, kind, title)
SUPPORTED = {
    ("CPUE", 0): ("platinum", "rev0", "Pokémon Platinum (USA)"),
    ("CPUE", 1): ("platinum", "rev1", "Pokémon Platinum (USA, Rev 1)"),
    ("IREO", None): ("gen5", "black2", "Pokémon Black Version 2 (USA, Europe)"),
    ("IRDO", None): ("gen5", "white2", "Pokémon White Version 2 (USA, Europe)"),
    # Optional: the following Pokémon's art and texts (makers.py)
    ("IPKE", None): ("hgss", "heartgold", "Pokémon HeartGold Version (USA)"),
    ("IPGE", None): ("hgss", "soulsilver", "Pokémon SoulSilver Version (USA)"),
}
# Other games a player might pick by mistake, to say what the file is
OTHERS = {
    "CPUP": "Pokémon Platinum (Europe)", "CPUJ": "Pokémon Platinum (Japan)", "CPUK": "Pokémon Platinum (Korea)",
    "CPUD": "Pokémon Platinum (Germany)", "CPUF": "Pokémon Platinum (France)", "CPUI": "Pokémon Platinum (Italy)",
    "CPUS": "Pokémon Platinum (Spain)", "ADAE": "Pokémon Diamond (USA)", "APAE": "Pokémon Pearl (USA)",
    "IPKP": "Pokémon HeartGold (Europe)", "IPGP": "Pokémon SoulSilver (Europe)", "IPKJ": "Pokémon HeartGold (Japan)",
    "IPGJ": "Pokémon SoulSilver (Japan)", "IPKK": "Pokémon HeartGold (Korea)", "IPGK": "Pokémon SoulSilver (Korea)",
    "IPKD": "Pokémon HeartGold (Germany)", "IPGD": "Pokémon SoulSilver (Germany)",
    "IPKF": "Pokémon HeartGold (France)", "IPGF": "Pokémon SoulSilver (France)",
    "IPKI": "Pokémon HeartGold (Italy)", "IPGI": "Pokémon SoulSilver (Italy)",
    "IPKS": "Pokémon HeartGold (Spain)", "IPGS": "Pokémon SoulSilver (Spain)", "IRBO": "Pokémon Black (USA, Europe)",
    "IRAO": "Pokémon White (USA, Europe)", "IREJ": "Pokémon Black 2 (Japan)", "IRDJ": "Pokémon White 2 (Japan)",
    "IRED": "Pokémon Black 2 (Germany)", "IRDD": "Pokémon White 2 (Germany)", "IREF": "Pokémon Black 2 (France)",
    "IRDF": "Pokémon White 2 (France)", "IREI": "Pokémon Black 2 (Italy)", "IRDI": "Pokémon White 2 (Italy)",
    "IRES": "Pokémon Black 2 (Spain)", "IRDS": "Pokémon White 2 (Spain)", "IREK": "Pokémon Black 2 (Korea)",
    "IRDK": "Pokémon White 2 (Korea)",
}
INPUT_NAMES = {"platinum": "Pokémon Platinum (USA)", "gen5": "Pokémon Black 2 or White 2 (USA, Europe)",
               "hgss": "Pokémon HeartGold or SoulSilver (USA)"}
WRONG_GAME = ("Anvil needs the USA version of Platinum, Black 2 or White 2 (USA, Europe), and if you like HeartGold or "
              "SoulSilver (USA).")
# A file only Platinum Reforged has, to tell it from Platinum
REFORGED_FILE = "gen5/ground.bin"


@dataclass
class RomInfo:
    path: str
    input: str = ""     # "platinum", "gen5" or "hgss", if supported
    kind: str = ""      # "rev0", "rev1", "black2", "white2", "heartgold", "soulsilver"
    title: str = ""     # what the file is, for the player
    problem: str = ""   # why it can't be used, if it can't

    @property
    def ok(self) -> bool:
        return not self.problem


def open_rom(path) -> Rom:
    """A ROM, memory-mapped, or read from its file as it's asked for where that can't be: in a browser, where mapping
    would copy the whole file into memory."""
    f = open(path, "rb")
    if sys.platform != "emscripten":
        try:
            return Rom(mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ))
        except (OSError, ValueError):
            pass
    return Rom(FileData(f))


def identify(path) -> RomInfo:
    info = RomInfo(str(path))
    if Path(path).is_dir():
        info.title = Path(path).name
        info.problem = "This is a folder: choose the ROM file in it."
        return info
    try:
        size = Path(path).stat().st_size
        with open(path, "rb") as f:
            header = f.read(0x200)
    except OSError as e:
        info.problem = f"Can't read the file: {(e.strerror or str(e)).rstrip('.')}."
        return info
    if size < 0x8000 or len(header) < 0x200:
        info.problem = "This isn't a Nintendo DS ROM."
        return info
    code = header[0x0C:0x10].decode("ascii", "replace")
    revision = header[0x1E]
    if code == "CPUE":
        try:
            if REFORGED_FILE in open_rom(path).paths:
                info.title = "Pokémon Platinum Reforged"
                info.problem = "This is Platinum Reforged already: choose your original Platinum ROM."
                return info
        except (OSError, ValueError, IndexError, UnicodeDecodeError, struct.error):
            pass
    for (known_code, known_revision), (input_name, kind, title) in SUPPORTED.items():
        if code == known_code and known_revision in (None, revision):
            info.input, info.kind, info.title = input_name, kind, title
            return info
    if code == "CPUE":
        info.title = f"Pokémon Platinum (USA, Rev {revision})"
        info.problem = "Unknown Platinum revision."
    elif code in OTHERS:
        info.title = OTHERS[code]
        info.problem = WRONG_GAME
    else:
        title = header[0:12].decode("ascii", "replace").strip("\0 ")
        info.title = f"{title} ({code})" if title else code
        info.problem = "This isn't one of the games Anvil takes."
    return info


def describe(path, slot: str, name: str = "") -> dict:
    """What a ROM is, for a slot ("platinum", "gen5" or "hgss"), as the app's page shows it. name: the file's, if not path's
    (a browser's file is named apart from where it's read)."""
    info = identify(path)
    problem = info.problem
    if problem == WRONG_GAME or (not problem and info.input != slot):
        problem = f"This slot needs {INPUT_NAMES[slot]}."
    return {"path": info.path, "name": name or Path(info.path).name, "title": info.title or "Unknown file",
            "ok": not problem, "problem": problem}


def place(path, name: str = "") -> dict:
    """A dropped ROM, in the slot its game belongs in (Platinum's unless it's a Black 2 or White 2, or a HeartGold or
    SoulSilver)."""
    info = identify(path)
    slot = info.input or ("gen5" if info.title.startswith(("Pokémon Black", "Pokémon White"))
                          else "hgss" if info.title.startswith(("Pokémon HeartGold", "Pokémon SoulSilver"))
                          else "platinum")
    return {"slot": slot, "info": describe(path, slot, name)}
