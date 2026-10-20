"""Reading Nintendo DS ROM images: the header's fields, the file allocation table, the file names, the ARM9 overlays,
and the main binaries.

The secure area (the first 2 KB of the ARM9 binary) is left out of everything read here: clean dumps keep it
encrypted, some tools decrypt it, and Platinum Reforged doesn't need it (the Gen V build makes its own), so the two
forms of the same game read the same.
"""
import struct
from dataclasses import dataclass

HEADER_SIZE = 0x4000
SECURE_AREA_SIZE = 0x800
# The 12 bytes after the ARM9 binary that point at its module parameters (NitroSDK's NITROCODE)
NITROCODE = 0xDEC00621


def decompress_code(data: bytes) -> bytes:
    """Code compressed the NitroSDK way, expanded: LZ77 read backwards from its end. Its last 8 bytes are a footer:
    the compressed part's length (bits 0-23) and the footer's own, with its padding (bits 24-31), then how many
    bytes longer the code is expanded. The compressed part is the code's end; what's before it is stored as it is.
    Each flag byte, read backwards, says for its next eight items, highest bit first, whether one is a byte as it is
    or a copy: two bytes, the length less 3 (high 4 bits) and the distance back less 3 (12 bits). ValueError if data
    doesn't end in such a footer."""
    if len(data) < 8:
        raise ValueError("too short to be compressed code")
    info, extra = struct.unpack_from("<II", data, len(data) - 8)
    footer, compressed = info >> 24, info & 0xFFFFFF
    if not extra or not 8 <= footer <= 11 or not footer <= compressed <= len(data):
        raise ValueError("not compressed code")
    out = bytearray(data) + bytes(extra)
    src, dst, start = len(data) - footer, len(out), len(data) - compressed
    while src > start:
        src -= 1
        flags = data[src]
        for _ in range(8):
            if src <= start:
                break
            if flags & 0x80:
                hi, lo = data[src - 1], data[src - 2]
                src -= 2
                distance, length = ((hi & 0x0F) << 8 | lo) + 3, (hi >> 4) + 3
                for _ in range(length):
                    dst -= 1
                    out[dst] = out[dst + distance]
            else:
                src -= 1
                dst -= 1
                out[dst] = data[src]
            flags <<= 1
    return bytes(out)


@dataclass
class Overlay:
    id: int
    ram_address: int
    ram_size: int
    bss_size: int
    sinit_start: int
    sinit_end: int
    file_id: int
    flags: int

    @property
    def compressed(self) -> bool:
        return bool(self.flags & 0x01000000)


class FileData:
    """A ROM file read as it's asked for, for where it can't be memory-mapped (Anvil in a browser reads the player's
    files this way): slices, single bytes and its length, as bytes have them."""

    def __init__(self, f):
        self.f = f
        self.size = f.seek(0, 2)

    def __len__(self) -> int:
        return self.size

    def __getitem__(self, key):
        if isinstance(key, slice):
            start, stop, step = key.indices(self.size)
            assert step == 1
            self.f.seek(start)
            return self.f.read(max(0, stop - start))
        self.f.seek(key % self.size)
        return self.f.read(1)[0]


class Rom:
    """A ROM's parts. data is the whole file: bytes, an mmap or a FileData, read through slices."""

    def __init__(self, data):
        self.data = data
        f = self.word
        self.game_code = bytes(data[0x0C:0x10]).decode("ascii", "replace")
        self.revision = data[0x1E]
        self.unit_code = data[0x12]
        self.arm9_offset, self.arm9_ram, self.arm9_size = f(0x20), f(0x28), f(0x2C)
        self.arm7_offset, self.arm7_size = f(0x30), f(0x3C)
        self.fnt_offset, self.fnt_size = f(0x40), f(0x44)
        self.fat_offset, self.fat_size = f(0x48), f(0x4C)
        self.ovt9_offset, self.ovt9_size = f(0x50), f(0x54)
        self.banner_offset = f(0x68)
        self.used_size = f(0x80)
        fat = self.fat_bytes()
        self.fat = [struct.unpack_from("<II", fat, i * 8) for i in range(self.fat_size // 8)]
        self.overlays = {}
        ovt9 = self.ovt9()
        for i in range(self.ovt9_size // 32):
            ov = Overlay(*struct.unpack_from("<8I", ovt9, i * 32))
            self.overlays[ov.id] = ov
        self.paths = self._file_names()

    def word(self, offset: int) -> int:
        return struct.unpack("<I", self.data[offset:offset + 4])[0]

    def file(self, file_id: int) -> bytes:
        start, end = self.fat[file_id]
        return bytes(self.data[start:end])

    def file_by_path(self, path: str) -> bytes:
        return self.file(self.paths[path])

    def file_part(self, path: str, start: int, end: int) -> bytes:
        """file_by_path(path)[start:end], reading only that part of the ROM."""
        file_start, file_end = self.fat[self.paths[path]]
        start, end, _ = slice(start, end).indices(file_end - file_start)
        return bytes(self.data[file_start + start:file_start + max(start, end)])

    def _file_names(self) -> dict:
        """{path: file id} from the file name table."""
        fnt = self.fnt()
        out = {}

        def walk(dir_id, prefix):
            sub_offset, first_file = struct.unpack_from("<IH", fnt, (dir_id & 0xFFF) * 8)
            pos, file_id = sub_offset, first_file
            while True:
                length = fnt[pos]
                pos += 1
                if length == 0:
                    break
                name = bytes(fnt[pos:pos + (length & 0x7F)]).decode("ascii")
                pos += length & 0x7F
                if length & 0x80:
                    sub_id = struct.unpack_from("<H", fnt, pos)[0]
                    pos += 2
                    walk(sub_id, prefix + name + "/")
                else:
                    out[prefix + name] = file_id
                    file_id += 1

        walk(0xF000, "")
        return out

    def header(self) -> bytes:
        return bytes(self.data[:HEADER_SIZE])

    def arm9(self) -> bytes:
        """The ARM9 binary as stored, with its NITROCODE footer if it has one, the secure area zeroed."""
        end = self.arm9_offset + self.arm9_size
        if self.word(end) == NITROCODE:
            end += 12
        data = bytearray(self.data[self.arm9_offset:end])
        data[:SECURE_AREA_SIZE] = bytes(SECURE_AREA_SIZE)
        return bytes(data)

    def arm9_decompressed(self) -> bytes:
        """The ARM9 binary as it runs, its compressed part (if any) expanded, the secure area zeroed."""
        data = bytearray(self.data[self.arm9_offset:self.arm9_offset + self.arm9_size])
        data[:SECURE_AREA_SIZE] = bytes(SECURE_AREA_SIZE)
        footer = self.arm9_offset + self.arm9_size
        if self.word(footer) == NITROCODE:
            params = self.word(footer + 4)
            compressed_end = struct.unpack_from("<I", data, params + 0x14)[0]
            if compressed_end:
                head = bytes(data[:compressed_end - self.arm9_ram])
                return decompress_code(head) + bytes(data[compressed_end - self.arm9_ram:])
            return bytes(data)
        # A DSi-enhanced game (Black 2, White 2) has no footer: its binary is compressed to its end, if at all
        try:
            expanded = decompress_code(bytes(data))
        except (ValueError, IndexError):
            return bytes(data)
        return expanded if len(expanded) > len(data) else bytes(data)

    def arm7(self) -> bytes:
        return bytes(self.data[self.arm7_offset:self.arm7_offset + self.arm7_size])

    def overlay(self, overlay_id: int) -> bytes:
        """An ARM9 overlay as it runs, expanded if it's stored compressed."""
        ov = self.overlays[overlay_id]
        data = self.file(ov.file_id)
        return decompress_code(data) if ov.compressed else data

    def fnt(self) -> bytes:
        return bytes(self.data[self.fnt_offset:self.fnt_offset + self.fnt_size])

    def fat_bytes(self) -> bytes:
        return bytes(self.data[self.fat_offset:self.fat_offset + self.fat_size])

    def ovt9(self) -> bytes:
        return bytes(self.data[self.ovt9_offset:self.ovt9_offset + self.ovt9_size])

    def banner(self) -> bytes:
        version = struct.unpack("<H", self.data[self.banner_offset:self.banner_offset + 2])[0]
        size = {1: 0x840, 2: 0x940, 3: 0xA40, 0x103: 0x23C0}.get(version, 0x840)
        return bytes(self.data[self.banner_offset:self.banner_offset + size])
