"""Nintendo DS file formats for the port's converters, which Anvil also runs on the player's machine: NARC archives,
read and written in the layout the converters always wrote them in (ndspy's), and LZ77 decompression. Our own, so
Anvil carries no GPL code: ndspy is GPL-3.0 (the game's build tools may still use it; they aren't distributed).
`nitro.py ROM...` checks every archive in the ROMs reads and saves as ndspy does, where ndspy is installed.

A NARC: its header, then the file allocation table (BTAF: each file's start and end in the data), the name table
(BTNF) and the data (GMIF). Files start 4-byte aligned, zeros between and after the last; an archive is written
without names (a name table of one empty folder), as the port's all are. An archive with names reads (its names left
out) but doesn't write. The header's byte order mark and version are written as read; a new archive's are ndspy's
own (NEW_HEADER).
"""
import struct
import sys

# The name table of an archive without names: the root folder's entry (its names at 8, its first file 0, one
# folder), then its names: none, the end, padded to 4 bytes
EMPTY_NAMES = struct.pack("<IHH", 8, 0, 1) + b"\x00\xff\xff\xff"
# The byte order mark and version of a NARC read from a ROM, and of a new one
READ_HEADER, NEW_HEADER = b"\xfe\xff\x00\x01", b"\xff\xfe\x01\x00"


class NARC:
    """An archive's files, in order (`files`, each bytes or bytearray), as read from data or set."""

    def __init__(self, data=None):
        self.files = []
        self.named = False
        self.header = NEW_HEADER
        if data is not None:
            self._read(data)

    def _read(self, data):
        if bytes(data[:4]) != b"NARC":
            raise ValueError("not a NARC")
        self.header = bytes(data[4:8])
        blocks, offset = {}, struct.unpack_from("<H", data, 0xC)[0]
        for _ in range(struct.unpack_from("<H", data, 0xE)[0]):
            magic, size = bytes(data[offset:offset + 4]), struct.unpack_from("<I", data, offset + 4)[0]
            blocks[magic] = offset
            offset += size
        fat, names, gmif = blocks[b"BTAF"], blocks[b"BTNF"], blocks[b"GMIF"] + 8
        count = struct.unpack_from("<H", data, fat + 8)[0]
        for i in range(count):
            start, end = struct.unpack_from("<II", data, fat + 12 + 8 * i)
            self.files.append(data[gmif + start:gmif + end])
        # Names: more than the root folder, or anything in its list (an empty one may have no list at all)
        size = struct.unpack_from("<I", data, names + 4)[0]
        listed, _, folders = struct.unpack_from("<IHH", data, names + 8)
        self.named = folders > 1 or (listed < size - 8 and data[names + 8 + listed] != 0)

    def save(self) -> bytes:
        if self.named:
            raise ValueError("an archive with file names can't be written here")
        fat, data = b"", bytearray()
        for f in self.files:
            data += bytes(-len(data) % 4)
            fat += struct.pack("<II", len(data), len(data) + len(f))
            data += f
        data += bytes(-len(data) % 4)
        btaf = b"BTAF" + struct.pack("<IHH", 12 + len(fat), len(self.files), 0) + fat
        btnf = b"BTNF" + struct.pack("<I", 8 + len(EMPTY_NAMES)) + EMPTY_NAMES
        gmif = b"GMIF" + struct.pack("<I", 8 + len(data)) + data
        body = btaf + btnf + gmif
        return b"NARC" + self.header + struct.pack("<IHH", 16 + len(body), 16, 3) + body


def unlz(data: bytes) -> bytes:
    """An LZ77 stream (type 0x10 or 0x11) decompressed; anything else as it is."""
    if data[0] not in (0x10, 0x11):
        return data
    size = int.from_bytes(data[1:4], "little")
    out, i = bytearray(), 4
    while len(out) < size:
        flags = data[i]
        i += 1
        for b in range(8):
            if len(out) >= size:
                break
            if not flags & (0x80 >> b):
                out.append(data[i])
                i += 1
                continue
            if data[0] == 0x10:
                n, d = (data[i] >> 4) + 3, ((data[i] & 15) << 8 | data[i + 1]) + 1
                i += 2
            else:
                ind = data[i] >> 4
                if ind == 0:
                    n = ((data[i] & 15) << 4 | data[i + 1] >> 4) + 0x11
                    d = ((data[i + 1] & 15) << 8 | data[i + 2]) + 1
                    i += 3
                elif ind == 1:
                    n = ((data[i] & 15) << 12 | data[i + 1] << 4 | data[i + 2] >> 4) + 0x111
                    d = ((data[i + 2] & 15) << 8 | data[i + 3]) + 1
                    i += 4
                else:
                    n, d = ind + 1, ((data[i] & 15) << 8 | data[i + 1]) + 1
                    i += 2
            for _ in range(n):
                out.append(out[-d])
    return bytes(out)


def check(paths) -> int:
    """Every archive in each ROM read and saved here and by ndspy; the number that differ."""
    import ndspy.narc
    import ndspy.rom
    bad = archives = 0
    for path in paths:
        rom = ndspy.rom.NintendoDSRom.fromFile(path)
        for fid, data in enumerate(rom.files):
            if bytes(data[:4]) != b"NARC":
                continue
            archives += 1
            ours, theirs = NARC(data), ndspy.narc.NARC(data)
            same = [bytes(f) for f in ours.files] == [bytes(f) for f in theirs.files]
            if same and not ours.named:
                same = ours.save() == theirs.save()
            if not same:
                bad += 1
                print(f"{path}: file {fid} ({rom.filenames.filenameOf(fid)}) differs")
    print(f"{archives} archives checked")
    return bad


if __name__ == "__main__":
    sys.exit(1 if check(sys.argv[1:]) else 0)
