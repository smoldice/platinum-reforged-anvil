<div align="center">

<img src="assets/wordmark.png" alt="Platinum Reforged" width="560">

**Pokémon Platinum with BW2's battle engine.**<br>
As much of Gen V as you want, and as much of Platinum as you want to keep.

[**Download**](../../releases/latest) · [Setup](#setup) · [Options](#in-game-options) · [Troubleshooting](#troubleshooting) · [Report a problem](../../issues)

</div>

---

## What it is

Platinum Reforged is a ROM hack of Pokémon Platinum (USA) that brings in Black 2 and White 2's (BW2) battle engine, and
more of Gen V along with it. I have plenty more ideas on the way, but the goal will always be the same: to let
everyone forge their own Gen IV experience (yes, I did the thing). That's why Platinum Reforged will always have
a configuration-first approach when implementing new features.

This repository hosts the downloads for **Platinum Reforged Anvil**, the tool that builds southe game.
Anvil takes your own Platinum and Black 2 or White 2 and writes a new ROM,
*Pokemon Platinum Reforged.nds*.

## What's new

**Gen V battles everywhere.** Wild Pokémon, trainers, double and tag battles, legendaries, the catching tutorial,
the Safari Zone, Pal Park and the Battle Frontier.

**BW2's battle backgrounds.** Routes use BW2's open-field look and dynamic backgrounds 
depending on where you are standing: lawn, dirt path, tall grass, mountain, caves, snowfields etc.

**Trainers.**
- The Sinnoh Gym Leaders and Cynthia battle with the animated sprites BW2 gave them for the Pokémon World
  Tournament.
- Trainer classes both games share, like Hiker, Youngster, Psychic, Black Belt, Lady and Swimmer, can be switched out to use BW2's
  sprites. *Togglable in the options menu.*
- **Custom sprites.** This is my attempt at keeping Platinum's aesthetic while still getting the animated battle sprites.
  I think it turned out decent if not good. For Ace Trainer, Fisherman, Worker, Lass and Waitress trainers I recolored and/or retextured BW2's
  sprites and animations to look like their Platinum counterparts. For Roughneck, Clown and Aroma Lady I animated their already existing battle sprites.
  I'll try to add more as I go.
  *Togglable in the options menu.*

**More of Gen V.** BW2's transitions into battle, its evolution and egg-hatching scenes, and its 
Critical Health! Low HP Theme. *All togglable in the options menu.*

**Platinum's battle menus, recreated.** Since game now uses BW2's battle engine, it came bundled with its battle UI in the bottom screen as well.
I retextured it to look as much as possible to Platinum's Battle UI, but if you notice some differences, that is why. Still if you prefer having BW2's UI,
you can conffigure this in the options menu.




## In-game options

The OPTIONS menu has seven new settings. Each one picks between Gen V and Platinum, so you can play with as much
or as little of Gen V as you like.

| Option | What it changes | Starts at |
| --- | --- | --- |
| TRAINERS | How trainers look in battle and on the overworld | PLATINUM |
| BATTLE MENUS | The look of the battle menus on the Touch Screen | PLATINUM |
| CUSTOM SPRITES | The custom sprites and animations for Gen IV trainers | ON |
| TRANSITIONS | How battles start from the overworld | GEN V |
| EVOLUTION | The evolution scene | GEN V |
| EGG HATCHING | The egg-hatching scene | GEN V |
| LOW HP | BW2's pinch music, or Platinum's beep, when your Pokémon's HP is low | GEN V |

## What you need

1. **Pokémon Platinum (USA)**, Rev 0 or Rev 1, as an `.nds` file (game code `CPUE`).
2. **Pokémon Black Version 2** or **Pokémon White Version 2** (USA, Europe), as an `.nds` file (game codes `IREO` and
   `IRDO`). "NDSi Enhanced" dumps are fine.
3. **Windows 10 or 11**, or **Linux**.

Both ROMs must be clean, unmodified dumps of your own cartridges. Trimmed dumps work.

> **Why two games?** Every Gen V piece of Platinum Reforged (the engine, sprites, backgrounds, music) comes from
> Black 2 or White 2.

## Setup

### Windows

1. Download **`Platinum Reforged Anvil.exe`** from the [latest release](../../releases/latest).
2. Open it.
3. Choose your Platinum ROM and your Black 2 or White 2 ROM: click **Choose...**, or drop both files onto the
   window and Anvil puts each one in its slot.
4. Click **Build Platinum Reforged**.

> Windows may say *"Windows protected your PC"* the first time, because Anvil isn't signed. Click **More info**,
> then **Run anyway**.

### Linux

On Linux, Anvil is a command-line program. Download **`platinum-reforged-anvil`** from the
[latest release](../../releases/latest), then in a terminal, in the folder you saved it to:

```sh
chmod +x platinum-reforged-anvil
./platinum-reforged-anvil --platinum "Platinum.nds" --black2 "Black 2.nds"
```

### Command line (both)

The same build without the window. On Windows, download **`platinum-reforged-anvil.exe`**. On Linux, it's the
program above.

```sh
platinum-reforged-anvil --platinum "Platinum.nds" --black2 "Black 2.nds" --out "Platinum Reforged.nds"
```

- `--white2` works the same way as `--black2`.
- `--out` is optional. Without it, the new ROM goes next to your Platinum ROM.
- `platinum-reforged-anvil --identify "some rom.nds"` tells you what a ROM is and whether Anvil accepts it.

## Troubleshooting

**"... doesn't match a clean copy of the game"**<br>
That ROM has been changed (patched, or saved over by a tool) or is a bad dump. Dump the cartridge again, or use
another clean copy.

**Your antivirus removes or blocks Anvil**<br>
Programs packaged the way Anvil is are sometimes flagged by mistake. If you downloaded it from this repository's
releases, restore it and allow it.

**The window doesn't open (Windows)**<br>
The app needs the Microsoft Edge WebView2 Runtime, which Windows 10 and 11 usually have already. Install it from
Microsoft, or use the command-line program, which doesn't need it.

**"Permission denied" when starting it (Linux)**<br>
Make it runnable with `chmod +x platinum-reforged-anvil`.

Still stuck, or found a bug in the game? [Open an issue](../../issues). Say which version of Anvil you used, which
ROMs you gave it (the output of `--identify` helps), and what happened.

## FAQ

**Can I download the finished ROM instead?**<br>
No. Platinum Reforged is only available through Anvil, built from games you own.

## Credits

Platinum Reforged is built on the work of the Pokémon decompilation community:

- [pret/pokeplatinum](https://github.com/pret/pokeplatinum), the Pokémon Platinum decompilation.
- [pokebw2](https://github.com/fuddlesworth/pokebw2), the Pokémon Black 2 and White 2 decompilation.

Anvil is made with [pywebview](https://pywebview.flowrl.com/), [bsdiff4](https://github.com/ilanschnell/bsdiff4),
[ndspy](https://github.com/RoadrunnerWMC/ndspy) and [PyInstaller](https://pyinstaller.org/).

## Disclaimer

Platinum Reforged is a free, unofficial fan project. It is not affiliated with, endorsed by or sponsored by Nintendo,
Game Freak, Creatures Inc. or The Pokémon Company. Pokémon and all related names are trademarks of their respective
owners. This repository contains no ROMs and no copyrighted game data. Use only games you own.
