#!/bin/sh
# Builds Anvil's Linux program (anvil/dist/linux/) in a container (anvil/release/linux.Dockerfile), from Git Bash on
# Windows or any machine with Docker:
#   anvil/release/make_linux.sh
# The image is built from linux.Dockerfile first (from Docker's cache once it's made, so changes to the file apply).
set -e
image=platinum-reforged-anvil-linux
root=$(cd "$(dirname "$0")/../.." && { pwd -W 2>/dev/null || pwd; })
docker build -q -t "$image" -f "$root/anvil/release/linux.Dockerfile" "$root/anvil/release" >/dev/null
MSYS_NO_PATHCONV=1 docker run --rm -v "$root:/src" -w /src "$image" python3 anvil/release/make_exe.py "$@"
