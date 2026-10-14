#!/usr/bin/env python3
"""Makes the Platinum Reforged site, which GitHub Pages serves from the public download repo
(smoldice/platinum-reforged-anvil, its gh-pages branch: deploy_site.sh):

  index.html      the home page: the players' README (the public repo's README.md), in Anvil's look
  build/          Anvil in the browser: the app's own page (reforged_anvil/ui) with web.js, which runs Anvil's
                  Python in a worker (worker.js, Pyodide); anvil.zip holds that Python, the converters it runs, the
                  bundle and the decomp's character map, laid out as in this repo
  notices/        what the build page runs on, and Anvil's terms

  .venv/Scripts/python anvil/web/make_site.py [--public PATH] [--dev]   ->   anvil/dist/site/

--public: the public repo's checkout, for its README and wordmark (default: this repo, when it's the public one;
else platinum-reforged-anvil beside it). --dev adds dev.js, which on localhost loads ROMs from serve.py's /dev-roms/
to test a build (never deployed). Needs the bundle (make_release.py, or a release's).
"""
import argparse
import html
import modulefinder
import re
import shutil
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ANVIL = HERE.parent
ROOT = ANVIL.parent
PACKAGE = ANVIL / "reforged_anvil"
sys.path[:0] = [str(HERE), str(ANVIL)]
import markdown  # noqa: E402  (beside this script)
from reforged_anvil import __version__  # noqa: E402
from reforged_anvil.makers import HIDDEN_IMPORTS, PORT  # noqa: E402
from platinum_rom import CHARMAP  # noqa: E402  (tools/port, which makers puts on the path)

REPO = "https://github.com/smoldice/platinum-reforged-anvil"
SITE = "https://smoldice.github.io/platinum-reforged-anvil/"
# A badge in the README's opening block: [![alt](picture)](link)
BADGE = re.compile(r"\[!\[([^\]]*)\]\([^)]*\)\]\(([^)]+)\)")
NITROGFX = ANVIL / "release" / "notices" / "nitrogfx.txt"
# Anvil's licence, which goes with its code in anvil.zip: the public repo's LICENSE.md (anvil/public in the project's)
LICENSE = next(p for p in (ANVIL / "public" / "LICENSE.md", ROOT / "LICENSE.md") if p.exists())
PYODIDE = re.search(r'PYODIDE = "https://cdn\.jsdelivr\.net/pyodide/v([^/]+)/', (HERE / "worker.js").read_text())[1]


def python_files() -> list:
    """Anvil's modules the browser runs: what web.py imports, and the settings modules makers.py loads by name."""
    # Only this repo's folders: the standard library and Pillow are Pyodide's
    finder = modulefinder.ModuleFinder(path=[str(ANVIL), str(PORT)])
    script = HERE.parent / "build" / "web_imports.py"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text("import reforged_anvil.web\n" + "".join(f"import {m}\n" for m in HIDDEN_IMPORTS))
    finder.run_script(str(script))
    files = {Path(m.__file__).resolve() for m in finder.modules.values() if m.__file__}
    files |= {PACKAGE / "__init__.py"}
    return sorted(f for f in files if f.is_relative_to(PACKAGE) or f.is_relative_to(PORT))


def make_zip(path: Path):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f in python_files():
            z.write(f, f.relative_to(ROOT).as_posix())
        z.write(PACKAGE / "data" / "reforged.bundle", "anvil/reforged_anvil/data/reforged.bundle")
        z.write(CHARMAP, CHARMAP.relative_to(ROOT).as_posix())
        z.write(LICENSE, "LICENSE.md")


def link(url: str) -> str:
    """Where a README link points on the site: its links into the repo (../../releases, ../../issues) go there, and
    its links to the site (the build page, the notices) stay on it, from the home page."""
    if url.startswith("../../"):
        return f"{REPO}/{url[len('../../'):]}"
    return url[len(SITE):] or "./" if url.startswith(SITE) else url


def page(title: str, body: str, up: str = "", description: str = "") -> str:
    """A page of the site; up: the way back to its root ("" or "../")."""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
<link rel="icon" href="{up}assets/icon.png">
<link rel="stylesheet" href="{up}assets/site.css">
</head>
<body>
<header class="top">
  <a class="brand" href="{up or './'}">Platinum Reforged</a>
  <nav>
    <a href="{up}build/">Build in your browser</a>
    <a href="{REPO}/releases/latest">Download</a>
    <a href="{REPO}/issues">Report a problem</a>
  </nav>
</header>
{body}
<footer>
  Anvil is <a href="{REPO}">open source</a> (MIT License) · <a href="{up}notices/">Notices</a> ·
  Not affiliated with Nintendo, Game Freak, Creatures Inc. or The Pokémon Company.
</footer>
</body>
</html>
"""


def home(readme: str) -> str:
    # The README opens with its own block (the wordmark, the tagline, links): the tagline goes in the page's
    m = re.match(r'\s*<div align="center">(.*?)</div>\s*(?:---\s*\n)?', readme, re.S)
    head, body = (m[1], readme[m.end():]) if m else ("", readme)
    tagline = " ".join(line.strip() for line in head.splitlines()
                       if line.strip() and not line.strip().startswith(("<img", "[")))
    # Its badges (shields.io's pictures, which the site doesn't load) are buttons here, by their alt text; the web
    # builder's is the first button already
    badges = "".join(f'\n    <a class="button" href="{html.escape(link(href))}">{html.escape(alt)}</a>'
                     for alt, href in BADGE.findall(head) if link(href) != "build/")
    hero = f"""<section class="hero">
  <img class="wordmark" src="assets/wordmark.png" alt="Platinum Reforged">
  <p class="tagline">{markdown.inline(tagline, link)}</p>
  <div class="cta">
    <a class="button primary" href="build/">Build it in your browser</a>
    <a class="button" href="{REPO}/releases/latest">Download Anvil for Windows or Linux</a>{badges}
  </div>
  <p class="cta-note">Both build the game from your own Pokémon Platinum and Black 2 or White 2. In the browser,
    your ROMs never leave your computer: the page builds the game there.</p>
</section>
<main class="content">
{markdown.to_html(body, link)}
</main>"""
    plain = re.sub(r"<[^>]+>|\*", "", tagline)
    return page("Pokémon Platinum Reforged", hero, description=plain)


def build_page(dev: bool) -> str:
    """The app's own page, in the browser: the site's bar above it, web.css and web.js with it."""
    text = (PACKAGE / "ui" / "index.html").read_text(encoding="utf-8")
    bar = f"""<header class="site-bar">
  <a class="home" href="../">Platinum Reforged</a>
  <span class="quiet">Anvil, in your browser</span>
  <span class="spacer"></span>
  <a href="{REPO}/releases/latest">Download for Windows or Linux</a>
  <a href="../notices/">Notices</a>
</header>
"""
    scripts = '<script src="web.js"></script>\n' + ('<script src="dev.js"></script>\n' if dev else "")
    for old, new in [
        ('<meta charset="utf-8">\n', '<meta charset="utf-8">\n<meta name="viewport" content="width=device-width">\n'
                                     '<link rel="icon" href="../assets/icon.png">\n'),
        ('<link rel="stylesheet" href="style.css">\n', '<link rel="stylesheet" href="style.css">\n'
                                                       '<link rel="stylesheet" href="web.css">\n'),
        ("<body>\n", "<body>\n" + bar),
        ('<script src="app.js"></script>', scripts + '<script src="app.js"></script>'),
    ]:
        assert text.count(old) == 1, old
        text = text.replace(old, new)
    return text


def notices() -> str:
    body = f"""<main class="content">
<h1>Notices</h1>
<p><strong>Platinum Reforged Anvil</strong> is open source, under the MIT License. Its source is on
<a href="{REPO}">GitHub</a>, where its <a href="{REPO}/blob/main/LICENSE.md">LICENSE.md</a> says what the licence
doesn't cover: the game Anvil builds, and Platinum Reforged's name and art.</p>
<h2>What the build page runs on</h2>
<p>Your browser fetches these from <a href="https://www.jsdelivr.com/">jsDelivr</a>, as their makers publish them,
when you open the build page:</p>
<ul>
<li><a href="https://pyodide.org/">Pyodide</a> {PYODIDE}: Python in the browser. Mozilla Public License 2.0.</li>
<li><a href="https://www.python.org/">Python</a> 3.14, within Pyodide. Python Software Foundation License.</li>
<li><a href="https://python-pillow.org/">Pillow</a>, within Pyodide. MIT-CMU License.</li>
</ul>
<p>The Windows and Linux programs carry their own notices, in <em>NOTICES.txt</em> in each download.</p>
<h2>nitrogfx</h2>
<p>The decomp's tool for its graphics. Anvil reads Platinum's pictures and fonts the way nitrogfx lays them out.</p>
<pre class="notice-text">{html.escape(NITROGFX.read_text(encoding="utf-8").strip())}</pre>
</main>"""
    return page("Notices · Platinum Reforged", body, up="../")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--public", type=Path,
                    default=ROOT.parent / "platinum-reforged-anvil" if (ANVIL / "public").is_dir() else ROOT)
    ap.add_argument("--dev", action="store_true")
    ap.add_argument("--out", type=Path, default=ANVIL / "dist" / "site")
    args = ap.parse_args()
    if not (PACKAGE / "data" / "reforged.bundle").exists():
        sys.exit("No bundle: make it first (release/make_release.py).")
    out = args.out
    shutil.rmtree(out, ignore_errors=True)
    # The README's pictures (the wordmark, the examples), where its links put them
    shutil.copytree(args.public / "assets", out / "assets")
    (out / "build").mkdir()
    (out / "notices").mkdir()
    (out / ".nojekyll").write_bytes(b"")  # the files as they are: no Jekyll on GitHub Pages
    shutil.copy(ANVIL / "assets" / "icon.png", out / "assets" / "icon.png")
    shutil.copy(HERE / "site.css", out / "assets" / "site.css")
    (out / "index.html").write_text(home((args.public / "README.md").read_text(encoding="utf-8")),
                                    encoding="utf-8")
    (out / "notices" / "index.html").write_text(notices(), encoding="utf-8")
    (out / "build" / "index.html").write_text(build_page(args.dev), encoding="utf-8")
    for name in ("app.js", "style.css", "logo.png", "cart.png"):
        shutil.copy(PACKAGE / "ui" / name, out / "build" / name)
    for name in ("web.js", "worker.js", "web.css") + (("dev.js",) if args.dev else ()):
        shutil.copy(HERE / name, out / "build" / name)
    make_zip(out / "build" / "anvil.zip")
    total = sum(f.stat().st_size for f in out.rglob("*") if f.is_file())
    print(f"site: {out} ({total / 1e6:.1f} MB; anvil.zip {(out / 'build' / 'anvil.zip').stat().st_size / 1e6:.2f} MB,"
          f" Anvil {__version__}, Pyodide {PYODIDE}){' with dev.js' if args.dev else ''}")


if __name__ == "__main__":
    main()
