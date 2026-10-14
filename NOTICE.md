# Notices

Platinum Reforged Anvil's own code is under the MIT License, as `LICENSE.md` says. This is the work of others that
it uses or carries.

## In this repository

- **nitrogfx** (MIT License), the decompilations' tool for their graphics. `tools/port/platinum_rom.py` reads
  Platinum's pictures and fonts the way nitrogfx lays them out. Its licence: `anvil/release/notices/nitrogfx.txt`.
- **pret/pokeplatinum**, the Pokémon Platinum decompilation: `game/tools/msgenc/charmap.txt` is its character map,
  which Anvil reads Platinum's text with.

## In the programs

The Windows and Linux programs carry Python, Pillow, pywebview (Windows), Microsoft's WebView2 SDK (Windows) and
PyInstaller's bootloader. Their licences are in `NOTICES.txt`, in each download, made with the programs by
`anvil/release/make_exe.py`. Microsoft's licence for the WebView2 SDK: `anvil/release/notices/webview2.txt`.

## On the site

The build page runs Anvil in [Pyodide](https://pyodide.org/) (Mozilla Public License 2.0), with Python and Pillow
inside it, which the browser fetches from jsDelivr. The site's notices page lists them.

## Pokémon

Platinum Reforged is a free, unofficial fan project, not affiliated with, endorsed by or sponsored by Nintendo, Game
Freak, Creatures Inc. or The Pokémon Company. Pokémon and all related names are trademarks of their respective owners.
