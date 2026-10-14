"""Applying a bsdiff 4 patch (what bsdiff4.diff makes, release/make_release.py): our own, in plain Python, so Anvil
runs where bsdiff4's C extension doesn't (a browser) and its programs carry no bsdiff code.

A patch is a 32-byte header ("BSDIFF40", then the lengths of its control and diff blocks and the new file's, each
8 bytes, little-endian, the top bit the sign), then the three blocks, bzip2-compressed. The control block is a list
of triples (x, y, z): add the next x bytes of the diff block to the old file's, byte by byte modulo 256; then copy the
next y bytes of the extra block; then move z bytes in the old file. Old bytes past either end count as zeros.
"""
import bz2

HEADER = b"BSDIFF40"


def offtin(data: bytes, at: int) -> int:
    value = int.from_bytes(data[at:at + 8], "little")
    return -(value & ~(1 << 63)) if value >> 63 else value


def add(a: bytes, b: bytes) -> bytes:
    """Two equal runs added byte by byte, modulo 256: all at once as integers, each byte's low 7 bits summed apart
    (two can't carry out of their byte) and its top bit set from both tops and that sum's carry."""
    n = len(a)
    low = int.from_bytes(b"\x7f" * n, "little")
    high = int.from_bytes(b"\x80" * n, "little")
    x, y = int.from_bytes(a, "little"), int.from_bytes(b, "little")
    return (((x & low) + (y & low)) ^ ((x ^ y) & high)).to_bytes(n, "little")


def old_run(old: bytes, start: int, n: int) -> bytes:
    """n bytes of old from start, zeros where that's past either end."""
    if 0 <= start and start + n <= len(old):
        return old[start:start + n]
    return bytes(old[i] if 0 <= i < len(old) else 0 for i in range(start, start + n))


def patch(old: bytes, data: bytes) -> bytes:
    if data[:8] != HEADER:
        raise ValueError("not a bsdiff 4 patch")
    ctrl_len, diff_len, new_size = offtin(data, 8), offtin(data, 16), offtin(data, 24)
    ctrl = bz2.decompress(data[32:32 + ctrl_len])
    diff = bz2.decompress(data[32 + ctrl_len:32 + ctrl_len + diff_len])
    extra = bz2.decompress(data[32 + ctrl_len + diff_len:])
    out, new_pos, old_pos, diff_pos, extra_pos, c = [], 0, 0, 0, 0, 0
    while new_pos < new_size:
        x, y, z = offtin(ctrl, c), offtin(ctrl, c + 8), offtin(ctrl, c + 16)
        c += 24
        if x:
            run, base = diff[diff_pos:diff_pos + x], old_run(old, old_pos, x)
            # Most of a diff run is zeros, where the old bytes stay as they are
            out.append(base if run.count(0) == x else add(base, run))
            diff_pos += x
            old_pos += x
            new_pos += x
        if y:
            out.append(extra[extra_pos:extra_pos + y])
            extra_pos += y
            new_pos += y
        old_pos += z
    result = b"".join(out)
    if len(result) != new_size:
        raise ValueError("the patch doesn't make a file of its size")
    return result
