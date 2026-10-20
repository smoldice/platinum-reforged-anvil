PLATINUM REFORGED ANVIL
=======================

Builds Pokemon Platinum Reforged from your own copies of two games, or three. Your ROMs are only read, never
changed: Anvil writes a new ROM, "Pokemon Platinum Reforged.nds".


WHAT YOU NEED
-------------

  1. Pokemon Platinum (USA), Rev 0 or Rev 1, as an .nds file.
  2. Pokemon Black Version 2 or Pokemon White Version 2 (USA, Europe), as an .nds file.
     The "NDSi Enhanced" dumps are fine.
  3. If you like, Pokemon HeartGold Version or Pokemon SoulSilver Version (USA), as an .nds file: with it, your
     first Pokemon follows you around, as in HeartGold and SoulSilver. Without it, the game is the same but for that.

All must be clean, unmodified dumps of your own cartridges. Dumps with the secure area encrypted or decrypted
both work, and so do trimmed dumps. Other regions and other games aren't supported (Anvil says so if you
pick one).

Anvil runs on Windows 10 and 11, and on Linux (any distribution from 2022 on: Ubuntu 22.04, Debian 12, Fedora 36
or newer), where it's a command line program: see COMMAND LINE.


HOW TO BUILD
------------

  1. Open "Platinum Reforged Anvil.exe" (on Linux, see COMMAND LINE).
  2. Choose your Platinum ROM, and your Black 2 or White 2 ROM: click Choose..., or drop both files onto the
     window (it puts each one where it belongs). If you like, choose your HeartGold or SoulSilver ROM too.
  3. Click "Reforge Platinum".

Or build it in your browser, with nothing to install: https://smoldice.github.io/platinum-reforged-anvil/build/
(about a minute; your ROMs stay on your computer).

It takes about 30 seconds: Anvil makes the game's sprites from your own ROMs, then builds the ROM. The new ROM is
saved beside your Platinum ROM unless you pick another place with Change... When it's done, Anvil checks that the ROM
came out exactly as released ("Verified" on the last screen), so you know it isn't damaged.

Play it in melonDS or DeSmuME.


COMMAND LINE
------------

The same build without the window: "platinum-reforged-anvil.exe" on Windows, "platinum-reforged-anvil" on Linux.
In a terminal, in Anvil's folder:

  platinum-reforged-anvil --platinum "Platinum.nds" --black2 "Black 2.nds" --out "Platinum Reforged.nds"

(--white2 works the same as --black2. --out is optional: the new ROM goes beside your Platinum ROM. Add
--heartgold "HeartGold.nds", or --soulsilver, for the following Pokemon. On Linux, start it as
./platinum-reforged-anvil.)

  platinum-reforged-anvil --identify "some rom.nds"     says what a ROM is, and whether Anvil takes it


IF SOMETHING GOES WRONG
-----------------------

"... doesn't match a clean copy of the game"
    That ROM was changed (patched, saved over by a tool) or is a bad dump. Dump the cartridge again, or use
    another clean copy.

"Windows protected your PC" when you open Anvil
    The program isn't signed. Click "More info", then "Run anyway".

Your antivirus removes or blocks Anvil
    Programs packed the way this one is are sometimes flagged by mistake. If you got it from the official
    download, restore it and allow it.

The window doesn't open
    The app needs Microsoft Edge WebView2 Runtime, which Windows 10 and 11 normally have. Install it from
    Microsoft, or use the command line program, which doesn't need it.

"Permission denied" when starting it on Linux
    Make it runnable: chmod +x platinum-reforged-anvil


LICENCE
-------

Platinum Reforged Anvil is open source, under the MIT License. Its source, and what the licence doesn't cover (the
game it builds, and Platinum Reforged's name and art), are at https://github.com/smoldice/platinum-reforged-anvil.
It's made with other software, whose licences and notices are in NOTICES.txt, with Anvil's own.
