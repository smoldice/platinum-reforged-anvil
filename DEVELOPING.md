# Developing Anvil

Platinum Reforged Anvil is open source (MIT License: `LICENSE.md`, which also says what it doesn't cover). The game
it builds is not: its source isn't public, and it reaches players only as the bundle Anvil builds it from.

## What's here

| Folder | What it is |
| --- | --- |
| `anvil/reforged_anvil/` | Anvil: reading ROMs (`nds.py`, `inputs.py`), the bundle and its patches (`bundle.py`, `bspatch.py`), the build (`build.py`, `makers.py`), the command line (`cli.py`), the Windows app (`app.py`, `ui/`) and the browser's side (`web.py`) |
| `anvil/web/` | The site: the README as its home page, and Anvil in the browser (`web.js`, `worker.js`, Pyodide) |
| `anvil/release/` | Packaging the Windows and Linux programs, with `NOTICES.txt` (`make_exe.py`, `make_linux.sh`) |
| `tools/port/` | The converters Anvil runs to make the game's sprites and menus from the player's own ROMs. They're part of the game's build: only the ones Anvil runs are here |
| `game/tools/msgenc/charmap.txt` | The Platinum decompilation's character map, which the converters read text with |

The code here is copied from Platinum Reforged's own repository at each release, so the tag of a release is the code
of its programs. Comments sometimes name files that stay there, such as `make_release.py`, which makes the bundle
from the game's build. Issues are welcome. Pull requests can't be merged as they are, but a change in one can be
made there by hand and arrive here with the next release.

## Running it from source

Python 3.10 or newer:

```sh
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt     # on Linux and macOS: .venv/bin/python
```

Anvil needs the bundle of the release you're running: download `reforged.bundle` from that release and put it in
`anvil/reforged_anvil/data/`. The code and the bundle go together, so check out the release's tag too.

Then, in `anvil/`:

```sh
python -m reforged_anvil --platinum "Platinum.nds" --black2 "Black 2.nds" --out "Platinum Reforged.nds"
python -m reforged_anvil                                     # the app (Windows; needs pywebview)
```

Pillow must be the version in `requirements.txt`: Anvil makes sprites from the player's ROMs, and checks that they
come out exactly as the release's.

## Building the programs

```sh
.venv/Scripts/python anvil/release/make_exe.py     # Windows: the app, the command line, the .zip (anvil/dist/windows)
sh anvil/release/make_linux.sh                     # Linux, in a Docker container: the command line, the .tar.gz
```

`make_exe.py` also writes `NOTICES.txt`, from what PyInstaller put in each program. It stops when something has no
known licence, or is under the GPL: the programs carry none.

## The site

```sh
.venv/Scripts/python anvil/web/make_site.py     # anvil/dist/site
.venv/Scripts/python anvil/web/serve.py 8766    # http://127.0.0.1:8766/
```

The build page runs Anvil's own Python in a Web Worker with [Pyodide](https://pyodide.org/): the ROMs are read where
they are and never leave the computer.
