#!/usr/bin/env python3
"""Packages Anvil for players: single-file programs with the bundle inside them, and an archive with README.txt.
PyInstaller doesn't cross-build, so each platform's programs are made on that platform:

  Windows: .venv/Scripts/python anvil/release/make_exe.py  ->  anvil/dist/windows/
    Platinum Reforged Anvil.exe       the desktop app (no console)
    platinum-reforged-anvil.exe       the command line (no app; the same building)
    Platinum-Reforged-Anvil-<version>-Windows.zip
  Linux: anvil/release/make_linux.sh (in a container, Ubuntu 22.04)  ->  anvil/dist/linux/
    platinum-reforged-anvil           the command line (on Linux there's no app: the owner's call, 2026-10-14)
    Platinum-Reforged-Anvil-<version>-Linux.tar.gz

Needs PyInstaller and Pillow (and pywebview for the Windows app); and reforged_anvil/data/reforged.bundle, made by
make_release.py (or, from the public source, a release's). The programs carry the game build's converters
(tools/port, which makers.py runs) and the decomp's character map. Never ndspy: it's GPL-3.0, and Anvil is under the
MIT License (EXCLUDES keeps it out; nds.py and tools/port/nitro.py do what Anvil needed of it).
"""
import argparse
import ast
import importlib.metadata
import io
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import sysconfig
import tarfile
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ANVIL = HERE.parent
PACKAGE = ANVIL / "reforged_anvil"
sys.path.insert(0, str(ANVIL))
from reforged_anvil import __version__  # noqa: E402
from reforged_anvil.makers import HIDDEN_IMPORTS, PORT  # noqa: E402
from platinum_rom import CHARMAP  # noqa: E402  (tools/port, which makers puts on the path)
try:
    from sources import check, describe  # noqa: E402  (beside this script, in the project's own repo only)
except ImportError:
    check = describe = None

APP_NAME = "Platinum Reforged Anvil"
CLI_NAME = "platinum-reforged-anvil"
LINUX = sys.platform.startswith("linux")
ENTRIES = {
    "app": "from reforged_anvil.app import main\nmain()\n",
    "cli": "import sys\nfrom reforged_anvil.cli import main\nsys.exit(main())\n",
}
# What the programs never use. The makers only draw in memory, so Pillow's AVIF and WebP, fonts, colour management,
# Tk and Qt stay out (about 10 MB). ndspy, which the game's build tools use, is GPL-3.0: never in the programs. bsdiff4
# makes the release's patches; Anvil applies them itself (bspatch.py)
EXCLUDES = ["ndspy", "bsdiff4", "tkinter", "numpy", "scipy", "PIL.AvifImagePlugin", "PIL._avif", "PIL.WebPImagePlugin",
            "PIL._webp", "PIL.ImageFont", "PIL._imagingft", "PIL.ImageCms", "PIL._imagingcms", "PIL.ImageTk",
            "PIL._imagingtk", "PIL.ImageQt", "PIL.ImageMath", "PIL._imagingmath", "PIL.ImageMorph", "PIL._imagingmorph"]

# NOTICES.txt, beside the programs in the archive: the licence of everything PyInstaller put in them, which most ask
# to go along, worked out from PyInstaller's own record of each program (PKG-00.toc, PYZ-00.toc). Anything it can't
# place stops the build, and so does a package licensed under the GPL (Anvil is under the MIT License).
NOTICES_HEAD = """PLATINUM REFORGED ANVIL: NOTICES
================================

Platinum Reforged Anvil's own code is open source, under the MIT License (below). Its source, and what the licence
doesn't cover (the game Anvil builds, which is inside these programs, and Platinum Reforged's name and art), are
at https://github.com/smoldice/platinum-reforged-anvil (LICENSE.md).

Anvil's licence comes first. After it, the software Anvil is made with, which comes with it in these programs: their
licences ask that their copyright notices and licence texts go along, so here they are.
"""
# The licences of what comes without one: Microsoft's WebView2 SDK, whose DLLs pywebview carries (its NuGet package's)
LICENCES = HERE / "notices"
WEBVIEW2 = ("Microsoft.Web.WebView2.Core.dll", "Microsoft.Web.WebView2.WinForms.dll", "WebView2Loader.dll")
# Microsoft's C runtime, which Python's Windows build carries: Microsoft's redistributable files
MS_RUNTIME = re.compile(r"^(vcruntime140(_1)?|ucrtbase|api-ms-win-[a-z0-9-]+)\.dll$", re.I)
# The Ubuntu packages whose libraries the Linux program carries, their licences reviewed (2026-10-14): none is the GPL
REVIEWED_UBUNTU = {"libpython3.10": "PSF", "libssl3": "Apache-2.0", "libffi8": "MIT", "libexpat1": "MIT",
                   "zlib1g": "Zlib", "libmpdec3": "BSD-2-Clause", "liblzma5": "public domain", "libbz2-1.0": "bzip2"}
# The decomp's nitrogfx, whose layouts of pictures and fonts tools/port/platinum_rom.py follows (MIT): its LICENSE
NITROGFX = LICENCES / "nitrogfx.txt"
# Anvil's own licence: the public repo's LICENSE.md (kept in anvil/public in the project's own repo)
LICENSE = next(p for p in (ANVIL / "public" / "LICENSE.md", ANVIL.parent / "LICENSE.md") if p.exists())
# The MIT licence's terms, for a package that names it without shipping its text
MIT = """Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE."""


VERSION_INFO = """VSVersionInfo(
  ffi=FixedFileInfo(filevers={v4}, prodvers={v4}, mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0,
                    date=(0, 0)),
  kids=[
    StringFileInfo([StringTable('040904B0', [
      StringStruct('ProductName', 'Platinum Reforged Anvil'),
      StringStruct('FileDescription', '{description}'),
      StringStruct('FileVersion', '{version}'),
      StringStruct('ProductVersion', '{version}'),
      StringStruct('InternalName', '{name}'),
      StringStruct('OriginalFilename', '{name}.exe')])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""


def program(kind: str, name: str, work: Path, dist: Path) -> Path:
    """One single-file program: "app" or "cli". On Linux it carries every library it needs but the C library, so it
    runs on any distribution with Ubuntu 22.04's glibc or newer."""
    entry = work / f"entry_{kind}.py"
    entry.write_text(ENTRIES[kind], encoding="utf-8")
    sep = os.pathsep
    args = [
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile", "--log-level", "WARN",
        "--name", name, "--distpath", str(dist), "--workpath", str(work / kind), "--specpath", str(work),
        "--paths", str(ANVIL), "--paths", str(PORT),
        "--add-data", f"{PACKAGE / 'data' / 'reforged.bundle'}{sep}reforged_anvil/data",
        "--add-data", f"{CHARMAP}{sep}.",
    ]
    args += [x for m in EXCLUDES for x in ("--exclude-module", m)]
    args += [x for m in HIDDEN_IMPORTS for x in ("--hidden-import", m)]
    if not LINUX:
        # Windows wants four numbers: a pre-release's (1.0.0-alpha) are its release's
        numbers = [int(x) for x in re.match(r"[\d.]+", __version__)[0].strip(".").split(".")] + [0] * 4
        version_file = work / f"version_{kind}.txt"
        version_file.write_text(VERSION_INFO.format(
            v4=tuple(numbers[:4]), version=__version__, name=name,
            description="Platinum Reforged Anvil" if kind == "app" else "Platinum Reforged Anvil (command line)"),
            encoding="utf-8")
        args += ["--icon", str(PACKAGE / "ui" / "icon.ico"), "--version-file", str(version_file)]
    if kind == "app":
        args += ["--windowed", "--add-data", f"{PACKAGE / 'ui'}{sep}reforged_anvil/ui"]
    else:
        args += ["--console"] + [x for m in ("webview", "clr", "pythonnet", "clr_loader", "gi")
                                 for x in ("--exclude-module", m)]
    subprocess.run(args + [str(entry)], check=True)
    return dist / (name if LINUX else f"{name}.exe")


def contents(folder: Path) -> list:
    """(name in the program, source path) of everything PyInstaller put in a program, from its work folder."""
    pkg = ast.literal_eval((folder / "PKG-00.toc").read_text(encoding="utf-8"))[2]
    pyz = ast.literal_eval((folder / "PYZ-00.toc").read_text(encoding="utf-8"))[1]
    return [(name, src) for name, src, kind in pkg + pyz if kind not in ("OPTION", "PYZ") and src]


def ubuntu_package(path: Path) -> str:
    """The Ubuntu package a system library is from (its path as dpkg has it: /lib and /usr/lib are one)."""
    text = str(path)
    for candidate in {text, text.replace("/usr/lib/", "/lib/", 1), text.replace("/lib/", "/usr/lib/", 1)}:
        found = subprocess.run(["dpkg", "-S", candidate], capture_output=True, text=True).stdout
        if found:
            return found.split(":")[0]
    sys.exit(f"{path}: not from an Ubuntu package; whose licence is it under?")


def licence_text(dist) -> str:
    """A package's licence files, or for one that ships none, the MIT licence its metadata names."""
    files = [f for f in dist.files or [] if re.search(r"LICEN[CS]E|COPYING|NOTICE", f.name, re.I)]
    if files:
        return "\n\n".join(f.read_text(encoding="utf-8").strip() for f in files)
    if (dist.metadata.get("License") or "").strip() == "MIT":
        return (f"MIT License (from its package's metadata; it ships no licence file)\n\n"
                f"Copyright (c) {dist.metadata['Author']}\n\n" + MIT)
    sys.exit(f"{dist.metadata['Name']}: no licence text")


def under_gpl(dist) -> bool:
    meta = dist.metadata
    words = " ".join([meta.get("License-Expression") or "", (meta.get("License") or "")[:200]]
                     + [c for c in meta.get_all("Classifier") or [] if c.startswith("License")])
    return bool(re.search(r"\bGPL|General Public License", words)) and "Lesser" not in words


def notices(folders: list) -> str:
    """NOTICES.txt for the programs PyInstaller built in these work folders."""
    owners = {}
    for dist in importlib.metadata.distributions():
        for f in dist.files or []:
            owners[os.path.normcase(str(Path(dist.locate_file(f)).resolve()))] = dist
    root, stdlib = ANVIL.parent.resolve(), Path(sysconfig.get_paths()["stdlib"]).resolve()
    # Python: its standard library, and on Windows its whole folder (its DLLs); on Linux the prefix is /usr, whose
    # libraries are the system's
    python = {stdlib, Path(sysconfig.get_paths()["platstdlib"]).resolve()}
    if not LINUX:
        python.add(Path(sys.base_prefix).resolve())
    dists, ubuntu, runtime, webview2 = {}, set(), set(), set()
    for folder in folders:
        for name, src in contents(folder):
            path = Path(src).resolve()
            if Path(name).name in WEBVIEW2:
                webview2.add(Path(name).name)
            dist = owners.get(os.path.normcase(str(path)))
            if dist:
                dists[dist.metadata["Name"].lower()] = dist
            elif path.is_relative_to(root) and not path.is_relative_to(root / ".venv"):
                continue  # ours: Anvil, the converters, the bundle, the decomp's character map
            elif path.is_relative_to(folder.parents[1]) or any(path.is_relative_to(p) for p in python):
                continue  # Python and its standard library, and the work folder's (the entry script, PyInstaller's
                # copies of the standard library)
            elif MS_RUNTIME.match(path.name):
                runtime.add(path.name)
            elif LINUX and (path.is_relative_to("/usr/lib") or path.is_relative_to("/lib")):
                ubuntu.add(ubuntu_package(path))
            else:
                sys.exit(f"{name} ({src}): whose licence is it under?")
    out = [NOTICES_HEAD]

    def section(title, text):
        out.append(f"\n\n{title}\n{'-' * len(title)}\n\n{text.strip()}\n")

    mit = LICENSE.read_text(encoding="utf-8").split("## MIT License", 1)[1]
    section(f"Platinum Reforged Anvil {__version__}", "MIT License\n\n" + mit.strip())
    licence = next(p for p in (Path(sys.base_prefix) / "LICENSE.txt", stdlib / "LICENSE.txt") if p.exists())
    section(f"Python {platform.python_version()}", licence.read_text(encoding="utf-8"))
    if runtime:
        section("Microsoft Visual C++ and Universal C runtimes",
                f"{', '.join(sorted(runtime))}: Microsoft's, redistributed with Python's Windows build as Microsoft's "
                "terms for them allow.")
    for key, dist in sorted(dists.items()):
        if key == "pyinstaller":
            continue
        if under_gpl(dist):
            sys.exit(f"{dist.metadata['Name']} is licensed under the GPL and would be in the programs")
        section(f"{dist.metadata['Name']} {dist.version}", licence_text(dist))
    if webview2:
        section("Microsoft WebView2 SDK", f"{', '.join(sorted(webview2))}, which pywebview carries.\n\n"
                + (LICENCES / "webview2.txt").read_text(encoding="utf-8"))
    for package in sorted(ubuntu):
        if package not in REVIEWED_UBUNTU:
            sys.exit(f"{package}: its licence hasn't been reviewed (make_exe.py REVIEWED_UBUNTU)")
        section(f"{package} (Ubuntu 22.04)", Path(f"/usr/share/doc/{package}/copyright").read_text(encoding="utf-8"))
    pyinstaller = importlib.metadata.distribution("pyinstaller")
    lines = next(f for f in pyinstaller.files if f.name == "COPYING.txt").read_text(encoding="utf-8").splitlines()
    end = next(i for i in range(30, len(lines) - 1) if lines[i + 1].startswith("---"))
    section(f"PyInstaller {pyinstaller.version}: its bootloader, and the files it embeds with it",
            "Under the GNU GPL with the exception below, which lets them go with programs under any licence "
            "(PyInstaller's COPYING.txt, its beginning):\n\n" + "\n".join(lines[:end]))
    section("nitrogfx", "The decomp's tool for its graphics. Anvil reads Platinum's pictures and fonts the way "
            "nitrogfx lays them out (tools/port/platinum_rom.py).\n\n" + NITROGFX.read_text(encoding="utf-8"))
    return "".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", help="where the programs and the archive go (default: anvil/dist/windows or linux)")
    args = ap.parse_args()
    bundle = PACKAGE / "data" / "reforged.bundle"
    if not bundle.exists():
        sys.exit(f"No bundle at {bundle}: make it first (release/make_release.py), or put a release's there.")
    # Which commits the bundle comes from, and whether the repo still matches them (the Linux build runs in a
    # container, where git can't check the Windows checkout: run make_exe.py's check on Windows for that)
    recorded = json.loads(zipfile.ZipFile(bundle).read("manifest.json")).get("sources")
    print(f"bundle from: {describe(recorded) if recorded and describe else recorded or '?'}")
    if not LINUX and check:
        for warning in check(recorded):
            print(f"warning: {warning}")
    platform = "linux" if LINUX else "windows"
    dist = Path(args.out) if args.out else ANVIL / "dist" / platform
    # Linux builds in the container's own disk: the checkout is a slow Windows mount there
    work = Path(tempfile.gettempdir()) / "anvil-build" if LINUX else ANVIL / "build"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    dist.mkdir(parents=True, exist_ok=True)

    folder = f"{APP_NAME} {__version__}"
    # The archives' names have no spaces or brackets: GitHub turns those into dots in a release's file names
    stem = f"{APP_NAME.replace(' ', '-')}-{__version__}"
    kinds = [("cli", CLI_NAME)] if LINUX else [("app", APP_NAME), ("cli", CLI_NAME)]
    programs = [program(kind, name, work, dist) for kind, name in kinds]
    texts = {"README.txt": (ANVIL / "README.txt").read_bytes(),
             "NOTICES.txt": notices([work / kind / name for kind, name in kinds]).encode("utf-8")}
    (dist / "NOTICES.txt").write_bytes(texts["NOTICES.txt"])
    if LINUX:
        archive = dist / f"{stem}-Linux.tar.gz"
        with tarfile.open(archive, "w:gz") as tar:
            for path in programs:
                info = tar.gettarinfo(path, f"{folder}/{path.name}")
                info.mode, info.uid, info.gid, info.uname, info.gname = 0o755, 0, 0, "", ""
                with open(path, "rb") as f:
                    tar.addfile(info, f)
            for name, data in texts.items():
                info = tarfile.TarInfo(f"{folder}/{name}")
                info.size, info.mode = len(data), 0o644
                tar.addfile(info, io.BytesIO(data))
    else:
        archive = dist / f"{stem}-Windows.zip"
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for exe in programs:
                z.write(exe, f"{folder}/{exe.name}")
            for name, data in texts.items():
                z.writestr(f"{folder}/{name}", data)
    for path in programs + [dist / "NOTICES.txt", archive]:
        print(f"{path.stat().st_size:>12,}  {path}")


if __name__ == "__main__":
    main()
