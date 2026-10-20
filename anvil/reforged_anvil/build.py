"""Making Pokémon Platinum Reforged: the steps the CLI and the app share."""
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from .bundle import Bundle, Inputs, InputMismatch
from .inputs import INPUT_NAMES, identify, open_rom

OUTPUT_NAME = "Pokemon Platinum Reforged.nds"


def bundle_path() -> Path:
    """The bundle that came with Anvil (beside the package, or in PyInstaller's folder)."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    for candidate in (base / "data" / "reforged.bundle", base / "reforged_anvil" / "data" / "reforged.bundle"):
        if candidate.exists():
            return candidate
    raise FileNotFoundError("Anvil's data (reforged.bundle) is missing.")


def default_output(platinum_path) -> str:
    return str(Path(platinum_path).with_name(OUTPUT_NAME))


class BuildError(Exception):
    """Why the ROM couldn't be made, for the player."""


@dataclass
class Result:
    path: str
    sha1: str
    size: int


def make_into(platinum_path, gen5_path, write, progress=None, bundle=None, hgss_path=None) -> str:
    """Makes the ROM into write(data), from its start (Bundle.build), after checking the inputs; returns its SHA-1.
    hgss_path: HeartGold or SoulSilver, optional, for the following Pokémon. progress(step, fraction) is called as it
    goes; steps: "read", "make" (the sprites, made from the ROMs), "build". The desktop programs write it to a file
    (make); Anvil in a browser to the download it offers."""
    def report(step, fraction):
        if progress:
            progress(step, fraction)

    report("read", 0.0)
    infos = {}
    given = [("platinum", platinum_path), ("gen5", gen5_path)] + ([("hgss", hgss_path)] if hgss_path else [])
    for expected, path in given:
        info = identify(path)
        if not info.ok:
            raise BuildError(f"{Path(path).name}: {info.title + ' — ' if info.title else ''}{info.problem}")
        if info.input != expected:
            raise BuildError(f"{Path(path).name} is {info.title}; this slot needs {INPUT_NAMES[expected]}.")
        infos[expected] = info
    bundle = bundle or Bundle(bundle_path())
    for name, info in infos.items():
        # A kind of game this release wasn't made for (one made without SoulSilver, say)
        if info.kind not in bundle.manifest["inputs"].get(name, {}):
            raise BuildError(f"{Path(info.path).name} is {info.title}, which this version of Anvil can't use.")
    inputs = Inputs(open_rom(platinum_path), infos["platinum"].kind, open_rom(gen5_path), infos["gen5"].kind)
    if hgss_path:
        inputs.hgss, inputs.hgss_variant = open_rom(hgss_path), infos["hgss"].kind
    report("read", 1.0)
    try:
        return bundle.build(inputs, write, lambda done, total: report("build", done / total),
                            lambda done, total: report("make", done / total))
    except InputMismatch as e:
        which = {name: info.title for name, info in infos.items()}.get(e.rom)
        if not which:  # the bundle's own data: make_release.py checks every input with it, so not in a release
            raise
        raise BuildError(f"{which} doesn't match a clean copy of the game (it may be modified, or a bad dump).")


def make(platinum_path, gen5_path, out_path, progress=None, bundle=None, hgss_path=None) -> Result:
    """Makes the ROM at out_path, as make_into, then "save": it's written beside out_path as it's made, and moved
    there once it's checked."""
    out_path = Path(out_path)
    for path in filter(None, (platinum_path, gen5_path, hgss_path)):
        if _same_file(out_path, path):
            raise BuildError("You can't save over one of your ROMs. Choose another name.")
    tmp = out_path.with_suffix(out_path.suffix + ".part")

    def discard():
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass

    def cant_save(e):
        discard()
        return BuildError(f"Couldn't save {out_path.name} in {out_path.parent}: {e.strerror or e}. "
                          "Choose another folder to save in.")

    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        f = open(tmp, "wb")
    except OSError as e:
        raise cant_save(e)
    try:
        with f:
            sha = make_into(platinum_path, gen5_path, f.write, progress, bundle, hgss_path)
    except OSError as e:
        raise cant_save(e)
    except BaseException:
        discard()
        raise
    if progress:
        progress("save", 0.0)
    try:
        os.replace(tmp, out_path)
    except OSError as e:
        raise cant_save(e)
    if progress:
        progress("save", 1.0)
    return Result(str(out_path), sha, out_path.stat().st_size)


def _same_file(a: Path, b) -> bool:
    try:
        return a.exists() and os.path.samefile(a, b)
    except OSError:
        return False
