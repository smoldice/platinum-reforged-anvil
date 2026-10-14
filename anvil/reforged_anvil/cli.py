"""The command line: platinum-reforged-anvil --platinum PLATINUM.nds --gen5 BLACK2.nds [--out OUT.nds]"""
import argparse
import sys
import time

from . import __version__
from .build import BuildError, default_output, make
from .inputs import identify

STEPS = {"read": "Reading your ROMs", "make": "Making the sprites", "build": "Building Platinum Reforged",
         "save": "Saving"}


def plain(text: str) -> str:
    """Pokémon as Pokemon, dashes as hyphens: consoles and pipes on Windows don't agree on how to show them."""
    return text.replace("Pokémon", "Pokemon").replace("—", "-")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="platinum-reforged-anvil",
        description="Makes Pokemon Platinum Reforged from your own clean copies of Pokemon Platinum (USA) and "
                    "Pokemon Black 2 or White 2 (USA, Europe).")
    ap.add_argument("--platinum", metavar="ROM", help="Pokemon Platinum (USA), revision 0 or 1")
    ap.add_argument("--gen5", "--black2", "--white2", dest="gen5", metavar="ROM",
                    help="Pokemon Black 2 or White 2 (USA, Europe)")
    ap.add_argument("--out", metavar="ROM", help="where to save it (default: beside the Platinum ROM)")
    ap.add_argument("--identify", nargs="+", metavar="ROM", help="say what these ROMs are, and stop")
    ap.add_argument("--version", action="version", version=f"Platinum Reforged Anvil {__version__}")
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        ap.print_help()
        return 0
    args = ap.parse_args(argv)

    if args.identify:
        for path in args.identify:
            info = identify(path)
            print(plain(f"{path}: {info.title or '?'}{'' if info.ok else ' - ' + info.problem}"))
        return 0
    if not args.platinum or not args.gen5:
        ap.error("--platinum and --gen5 are needed (or --identify)")
    out = args.out or default_output(args.platinum)
    state = {"step": None, "shown": -1}

    def progress(step, fraction):
        percent = int(fraction * 100)
        if step != state["step"] or percent != state["shown"]:
            state["step"], state["shown"] = step, percent
            bar = "#" * (percent // 4) + "-" * (25 - percent // 4)
            sys.stdout.write(f"\r{STEPS[step]:28s} [{bar}] {percent:3d}%")
            sys.stdout.flush()
            if fraction >= 1.0:
                sys.stdout.write("\n")

    start = time.monotonic()
    try:
        result = make(args.platinum, args.gen5, out, progress)
    except (BuildError, FileNotFoundError) as e:
        print(plain(f"\nError: {e}"), file=sys.stderr)
        return 1
    print(f"Done in {time.monotonic() - start:.0f} s: {result.path}")
    print(f"Verified: SHA-1 {result.sha1}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
