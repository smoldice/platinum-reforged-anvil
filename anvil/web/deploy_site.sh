#!/bin/sh
# Publishes the site to GitHub Pages: makes it (make_site.py, without dev.js) from this checkout's bundle and the
# public repo's README, and force-pushes it as the only commit of the public download repo's gh-pages branch, so old
# bundles don't pile up there (the site's history is this repo's). Only when the owner says (anvil/RELEASING.md).
#   sh anvil/web/deploy_site.sh
# GitHub Pages serves that branch once the repo's Settings > Pages has "Deploy from a branch: gh-pages, / (root)".
set -e
root=$(cd "$(dirname "$0")/../.." && pwd)
public="$root/../platinum-reforged-anvil"
remote=$(git -C "$public" remote get-url origin)
# The site's commit is made as the public repo's own commits are (its checkout's user.name and user.email)
name=$(git -C "$public" config user.name)
email=$(git -C "$public" config user.email)
python="$root/.venv/Scripts/python"
[ -x "$python" ] || python="$root/.venv/bin/python"
"$python" "$root/anvil/web/make_site.py" --public "$public"
commit=$(git -C "$root" rev-parse --short HEAD)
version=$(sed -n 's/^__version__ = "\(.*\)"/\1/p' "$root/anvil/reforged_anvil/__init__.py")
tmp=$(mktemp -d)
cp -r "$root/anvil/dist/site/." "$tmp/"
cd "$tmp"
git init -q -b gh-pages
git add -A
git -c user.name="$name" -c user.email="$email" commit -q -m "The site: Anvil $version, from platinum-reforged $commit"
git push -f "$remote" gh-pages
cd /
rm -rf "$tmp"
echo "published to $remote (gh-pages)"
