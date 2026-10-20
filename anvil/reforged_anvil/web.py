"""Anvil in a browser (anvil/web): what its worker calls, in Pyodide, with the player's files mounted read-only where
it reads them as it needs them (Emscripten's WORKERFS). The same steps and messages as the desktop programs; the ROM
goes to write(data), region by region, which the page turns into the download."""
from . import __version__
from .build import OUTPUT_NAME, BuildError, bundle_path, make_into
from .bundle import Bundle
from .inputs import describe, place


def info() -> dict:
    manifest = Bundle(bundle_path()).manifest
    return {"version": __version__, "label": manifest.get("label", ""), "output": OUTPUT_NAME,
            "size": manifest["output"]["size"], "sha1": manifest["output"]["sha1"]}


def describe_file(path: str, slot: str, name: str) -> dict:
    return describe(path, slot, name)


def place_file(path: str, name: str) -> dict:
    return place(path, name)


def build(platinum: str, gen5: str, write, progress, hgss: str = "") -> dict:
    """{"sha1": ...} once the ROM is made and checked, or {"error": the message the app would show}. hgss: HeartGold
    or SoulSilver, or "" for none."""
    try:
        return {"sha1": make_into(platinum, gen5, write, progress, hgss_path=hgss or None)}
    except BuildError as e:
        return {"error": str(e)}
    except Exception as e:  # anything unexpected, shown rather than lost, as the app does
        return {"error": f"Something went wrong: {e}"}
