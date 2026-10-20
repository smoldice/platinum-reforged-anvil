"""The desktop app: Anvil behind an HTML interface (ui/) in a native window, through pywebview (WebView2 on
Windows; WebKit on macOS and Linux)."""
import json
import os
import subprocess
import sys
import threading
from pathlib import Path

import webview

from . import __version__
from .build import OUTPUT_NAME, BuildError, bundle_path, default_output, make
from .bundle import Bundle
from .inputs import INPUT_NAMES, describe, place

ROM_TYPES = ("Nintendo DS ROMs (*.nds)", "All files (*.*)")


def ui_dir() -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    for candidate in (base / "ui", base / "reforged_anvil" / "ui"):
        if candidate.exists():
            return candidate
    raise FileNotFoundError("ui")


class Api:
    """What the page calls (window.pywebview.api)."""

    def __init__(self):
        self._window = None
        self._busy = False
        self._last_folder = ""  # where the last ROM was chosen or dropped: the next Choose... starts there

    def info(self):
        manifest = Bundle(bundle_path()).manifest
        return {"version": __version__, "label": manifest.get("label", ""), "made": manifest.get("made", ""),
                "inputs": INPUT_NAMES}

    def describe(self, path, slot):
        """What a ROM is, for a slot ("platinum", "gen5" or "hgss")."""
        if not path:
            return None
        self._last_folder = str(Path(path).parent)
        return describe(path, slot)

    def place(self, path):
        """A dropped ROM, in the slot its game belongs in (inputs.place)."""
        self._last_folder = str(Path(path).parent)
        return place(path)

    def pick_rom(self, slot):
        # The folder of the last ROM; at first, Windows' own choice (where its dialogs were last)
        result = self._window.create_file_dialog(webview.FileDialog.OPEN, directory=self._last_folder,
                                                 file_types=ROM_TYPES)
        return self.describe(result[0], slot) if result else None

    def default_output(self, platinum_path):
        return default_output(platinum_path) if platinum_path else ""

    def pick_output(self, current):
        folder = str(Path(current).parent) if current else ""
        result = self._window.create_file_dialog(webview.FileDialog.SAVE, directory=folder,
                                                save_filename=Path(current).name if current else OUTPUT_NAME,
                                                file_types=ROM_TYPES)
        if not result:
            return None
        path = result if isinstance(result, str) else result[0]
        return path if path.lower().endswith(".nds") else path + ".nds"

    def build(self, platinum, gen5, out, hgss=""):
        """hgss: HeartGold or SoulSilver, or "" for none."""
        if self._busy:
            return False
        self._busy = True
        threading.Thread(target=self._build, args=(platinum, gen5, out, hgss), daemon=True).start()
        return True

    def _build(self, platinum, gen5, out, hgss):
        shown = {"key": None}

        def progress(step, fraction):
            key = (step, int(fraction * 200))
            if key != shown["key"]:
                shown["key"] = key
                self._js("onProgress", step, fraction)

        try:
            result = make(platinum, gen5, out, progress, hgss_path=hgss or None)
            self._js("onDone", {"path": result.path, "name": Path(result.path).name, "sha1": result.sha1})
        except BuildError as e:
            self._js("onError", str(e))
        except Exception as e:  # anything unexpected, shown rather than lost
            self._js("onError", f"Something went wrong: {e}")
        finally:
            self._busy = False

    def _js(self, function, *args):
        self._window.evaluate_js(f"window.{function}({', '.join(json.dumps(a) for a in args)})")

    def show_in_folder(self, path):
        if sys.platform == "win32":
            subprocess.Popen(["explorer", "/select,", os.path.normpath(path)])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-R", path])
        else:
            subprocess.Popen(["xdg-open", str(Path(path).parent)])


def _bind_drop(api):
    """Dropped files' paths, which only the window's own handler sees (pywebview's pywebviewFullPath)."""
    from webview.dom import DOMEventHandler

    def on_drop(event):
        for f in (event.get("dataTransfer") or {}).get("files") or []:
            path = f.get("pywebviewFullPath")
            if path:
                api._js("onDropped", path)

    api._window.dom.document.events.drop += DOMEventHandler(on_drop, True, True)


def main():
    api = Api()
    api._window = webview.create_window(
        "Platinum Reforged Anvil", str(ui_dir() / "index.html"), js_api=api,
        width=1060, height=740, min_size=(920, 680), background_color="#eef0f4")
    webview.start(_bind_drop, api, icon=str(ui_dir() / "icon.ico"), debug=bool(os.environ.get("REFORGED_DEBUG")))


if __name__ == "__main__":
    main()
