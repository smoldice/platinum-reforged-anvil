# Anvil's Linux build: the command line program. PyInstaller can't cross-build, so it's made in Linux, on Ubuntu
# 22.04: a program built against its glibc (2.35) runs there and on any distribution with that or newer. Pillow as in
# env/Dockerfile, where the release is made: Anvil's makers must make the same bytes. No ndspy (GPL-3.0): Anvil has
# its own code for what it needed of it.
#   docker build -t platinum-reforged-anvil-linux -f anvil/release/linux.Dockerfile anvil/release
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-venv python3-pip python3-dev build-essential binutils \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/anvil && /opt/anvil/bin/pip install --no-cache-dir \
        "pyinstaller==6.22.3" "pillow==12.3.0"
ENV PATH=/opt/anvil/bin:$PATH
WORKDIR /src
