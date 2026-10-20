"""The release bundle: how Pokémon Platinum Reforged is rebuilt from the player's ROMs.

A bundle is a zip of `manifest.json` and blobs (bsdiff patches and data of our own, named by their SHA-1). The manifest
describes the output ROM region by region; each region is one of:

- `fill`: one byte repeated;
- `data`: a blob, as it is;
- for a region that comes from one of the inputs (`rom`: "platinum", "gen5" or "hgss"), an operation for each kind of
  that input (`variants`: "rev0", "rev1"; "black2", "white2"; "heartgold", "soulsilver", and "none" for the optional
  HGSS when the player has none):
  - `copy`: a part of the input, byte for byte;
  - `diff`: a bsdiff patch applied to a base made of parts of the input;
  - `made`: made from that input on the player's machine (the following Pokémon's archive from HGSS), as below;
  - `padded`: a blob followed by zeros to the region's size (the archive with nothing in it, without HGSS);
  an operation's own `sha1`, if it has one, is what it makes in place of the region's;
- `made` (`rom`: "made"): made from both inputs on the player's machine (makers.py: the art converted from
  Nintendo's), checked by SHA-1 like the rest. `cost` is how long it took when the release was made, for the
  progress bar. If what's made ever differs from the release's, `patches` has a bsdiff patch from it, by its SHA-1.
  The manifest's `makers.reads` has the SHA-1 of every part of the inputs the makers read, by kind of input: they're
  checked before anything is made.

The output's `sha1` is the whole ROM's, by whether the optional input was given ("hgss", "none").

A part of an input is named by a reference (see `resolve`). Each base is checked by SHA-1 before it's used, each
region after it's made, and the whole output at the end.
"""
import hashlib
import json
import zipfile
from dataclasses import dataclass

from .bspatch import patch as bspatch
from .nds import Rom

FORMAT = 3
# The optional input, and its kind when the player gives none
OPTIONAL = "hgss"
NONE = "none"


class InputMismatch(Exception):
    """A part of an input ROM isn't what a clean dump has (rom: "platinum", "gen5", "hgss"; or "bundle", "output" if the
    bundle's own data didn't come out right). region: the refs of the parts, " + " between them."""

    def __init__(self, rom: str, region: str):
        super().__init__(f"{rom}: {region}")
        self.rom = rom
        self.region = region


def sha1(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()


# The Black 2 and White 2 overlays the Gen V overlays come from, after the main binary, in the Gen V code base: the
# battle's, the evolution's and the egg's, the registration's (296, 297) and the Pokédex's (139, 144, 296, 298-304)
GEN5_CODE_OVERLAYS = (139, 144, 167, 168, 169, 170, 284, 285, 286, 287, 296, 297, 298, 299, 300, 301, 302, 303, 304,
                      307)


def resolve(rom: Rom, ref: str) -> bytes:
    """A part of an input ROM:

    - `file:PATH`, or `file:PATH@START:END` for a slice of it;
    - `arm9` (as stored), `arm9code` (as it runs), `arm7`, `overlay:ID` (as it runs);
    - `header`, `fnt`, `fat`, `ovt9`, `banner`;
    - `gen5code`: the Gen V overlays' base, the main binary as it runs and the overlays they come from.
    """
    kind, _, arg = ref.partition(":")
    if kind == "file":
        path, _, span = arg.partition("@")
        if span:
            # Only the slice is read: a base can be a thousand slices of one large file (Gen V's sound data, of
            # Black 2's 85 MB), and in a browser every read of the whole file goes through the player's file
            start, end = (int(x) for x in span.split(":"))
            return rom.file_part(path, start, end)
        return rom.file_by_path(path)
    if kind == "overlay":
        return rom.overlay(int(arg))
    if kind == "gen5code":
        return rom.arm9_decompressed() + b"".join(rom.overlay(i) for i in GEN5_CODE_OVERLAYS)
    return {
        "arm9": rom.arm9, "arm9code": rom.arm9_decompressed, "arm7": rom.arm7, "header": rom.header, "fnt": rom.fnt,
        "fat": rom.fat_bytes, "ovt9": rom.ovt9, "banner": rom.banner,
    }[kind]()


@dataclass
class Inputs:
    """The player's ROMs, and which kind each is: HeartGold or SoulSilver if they have one."""
    platinum: Rom
    platinum_variant: str
    gen5: Rom
    gen5_variant: str
    hgss: Rom = None
    hgss_variant: str = NONE

    def rom(self, name: str) -> Rom:
        return {"platinum": self.platinum, "gen5": self.gen5, OPTIONAL: self.hgss}[name]

    def variant(self, name: str) -> str:
        return {"platinum": self.platinum_variant, "gen5": self.gen5_variant, OPTIONAL: self.hgss_variant}[name]

    def output_key(self) -> str:
        """The output's SHA-1 to check against: with the optional input or without."""
        return NONE if self.hgss is None else OPTIONAL


class Bundle:
    def __init__(self, path):
        self.zip = zipfile.ZipFile(path)
        self.manifest = json.loads(self.zip.read("manifest.json"))
        if self.manifest["format"] != FORMAT:
            raise ValueError(f"bundle format {self.manifest['format']}, this version of Anvil reads {FORMAT}")

    def blob(self, name: str) -> bytes:
        return self.zip.read("blobs/" + name)

    def made_regions(self, inputs: Inputs) -> list:
        """The regions made on the player's machine: from both inputs, and from the optional one if it's given."""
        return [r for r in self.manifest["regions"] if r.get("rom") == "made"
                or (r.get("rom") == OPTIONAL and r["variants"][inputs.variant(OPTIONAL)]["kind"] == "made")]

    def make(self, inputs: Inputs, progress=None) -> dict:
        """The made regions' data, by name, once the parts of the inputs the makers read are checked. progress(done,
        total) is called as each is made, in the seconds each took for the release."""
        regions = self.made_regions(inputs)
        if not regions:
            return {}
        for rom_name, by_variant in self.manifest["makers"]["reads"].items():
            if inputs.variant(rom_name) not in by_variant:
                continue
            for ref, expected in by_variant[inputs.variant(rom_name)].items():
                try:
                    data = resolve(inputs.rom(rom_name), ref)
                except (KeyError, IndexError, ValueError):
                    raise InputMismatch(rom_name, ref)
                if sha1(data) != expected:
                    raise InputMismatch(rom_name, ref)
        # The converters load only when there's something to make
        from .makers import Maker
        maker = Maker(inputs.platinum, inputs.gen5, inputs.hgss)
        total, done, made = sum(r["cost"] for r in regions), 0.0, {}
        if progress:
            progress(done, total)
        for region in regions:
            made[region["name"]] = maker.make(region["name"])
            done += region["cost"]
            if progress:
                progress(done, total)
        return made

    def build(self, inputs: Inputs, write=None, progress=None, making=None) -> str:
        """Makes the output ROM from its start, region by region: write(data) gets each in turn, so the whole ROM is
        never in memory. making(done, total) is called as the made regions are made (Bundle.make), then
        progress(done, total) as the regions are put together, in bytes. Returns the ROM's SHA-1, checked."""
        made = self.make(inputs, making)
        out_info = self.manifest["output"]
        whole = hashlib.sha1()
        total, done = out_info["size"], 0
        cache = {}

        def part(rom_name, ref):
            key = (rom_name, ref)
            if key not in cache:
                try:
                    cache[key] = resolve(inputs.rom(rom_name), ref)
                except (KeyError, IndexError, ValueError):
                    raise InputMismatch(rom_name, ref)
            return cache[key]

        for region in self.manifest["regions"]:
            op = region
            rom_name = region.get("rom")
            if rom_name == "made":
                op = {"kind": "made"}
            elif rom_name:
                op = region["variants"][inputs.variant(rom_name)]
            kind = op["kind"]
            if kind == "made":
                data = made[region["name"]]
                patch = region.get("patches", {}).get(sha1(data))
                if patch and sha1(data) != region["sha1"]:
                    data = bspatch(data, self.blob(patch))
            elif kind == "fill":
                data = bytes([op["byte"]]) * region["size"]
            elif kind == "data":
                data = self.blob(op["blob"])
            elif kind == "padded":
                data = self.blob(op["blob"])
                data += bytes(region["size"] - len(data))
            elif kind == "copy":
                data = part(rom_name, op["ref"])
            else:
                base = b"".join(part(rom_name, ref) for ref in op["base"])
                if sha1(base) != op["base_sha1"]:
                    raise InputMismatch(rom_name, " + ".join(op["base"]))
                data = bspatch(base, self.blob(op["patch"]))
            if len(data) != region["size"] or sha1(data) != op.get("sha1", region["sha1"]):
                if kind == "copy":
                    raise InputMismatch(rom_name, op["ref"])
                raise InputMismatch("bundle", region["name"])
            # The regions run end to end from the ROM's start (make_release.py regions)
            if region["offset"] != done:
                raise InputMismatch("bundle", region["name"])
            whole.update(data)
            if write:
                write(data)
            done += region["size"]
            if progress:
                progress(done, total)
            # Parts used once are let go: the inputs are large
            if kind in ("copy", "diff") and len(cache) > 64:
                cache.clear()
        if done != total or whole.hexdigest() != out_info["sha1"][inputs.output_key()]:
            raise InputMismatch("output", "the whole ROM")
        return whole.hexdigest()
