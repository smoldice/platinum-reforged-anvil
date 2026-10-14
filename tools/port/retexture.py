"""Black 2 trainer sprites retextured to look like Platinum's: a class's Black 2 sprite keeps its own animation and
takes Platinum's colours and Platinum's hair, from the class's Platinum front sprite. A retexture is a module of
settings (retexture_ace_trainer_male.py is the first); build(cfg, b2_files, src) makes its sprite.

- The palette: Black 2's slots take Platinum's colours (cfg.PALETTE). One slot whose colour only trims used is freed
  for the darkest of Platinum's three hair greens; the pixels that had it, and the others whose role the palette
  alone can't change, are remapped part by part (cfg.REMAPS: by cell, rows and old slot -> new slot).
- The hair: Platinum's heads face the other way from Black 2's, so Platinum's hair goes on mirrored, lined up by the
  eyes: Black 2 (x, y) <- Platinum (cfg.PT_MIRROR - x, y - cfg.PT_DY - dy). Black 2's face, eyes, mouth and jaw stay
  as drawn, and so does its own hair underneath (recoloured green), so the head keeps Black 2's outline: Platinum's
  hair may reach past it only above the face (to cfg.TRIM_ROW), and is trimmed to it below. The hair's edges are
  dark, as both games draw them: Black 2's hair left poking out of Platinum's crown goes, plain green on the lower
  outline turns black. Every head drawing (cfg.HEADS) gets it.
- The still frame, which Black 2 shows when the trainer comes back after the battle, is drawn again from the
  retextured parts, in the animation's pose that matches Black 2's still frame best (the earliest such).

The animation files (cells, cell animations, multi-cells, multi-cell animations) stay Black 2's, byte for byte, and
every file keeps Black 2's compression. File 0, Black 2's 2D version of the sprite, which the battle doesn't read
(MCSS reads the texture, file 1: mcss_tool.c), takes cfg.CHARS_REMAP only.

Usage, to preview and check a retexture (in the container, from tools/port):
  retexture.py B2_ROM POKEPLATINUM_DIR MODULE OUT_DIR    e.g. MODULE = retexture_ace_trainer_male
It writes the 8 files, sha1.txt and preview.gif (Black 2's original beside the retextured one, 60 ticks a second).
"""
import hashlib
import importlib
import struct
import sys
from pathlib import Path

from PIL import Image

import make_trainer_sprites as mts
import trainer_rig


def cell_box(sprite, c):
    """A cell's texture rect: (s, t, w, h) in pixels."""
    _, _, w, h, s, t = sprite["rects"][c]
    return s // 4096, t // 4096, w // 4096, h // 4096


def recolour_cell(tex, box, remaps):
    px = tex.load()
    s, t, w, h = box
    for (y0, y1), m in remaps:
        for y in range(y0, min(y1, h - 1) + 1):
            for x in range(w):
                if px[s + x, t + y] in m:
                    px[s + x, t + y] = m[px[s + x, t + y]]


def mirrored_head(cfg, tex, box, dy, pt):
    """Black 2's head as it is, its own hair recoloured green, under Platinum's hair, mirrored and trimmed; then the
    hair's edges darkened."""
    px = tex.load()
    s, t = box[0], box[1]
    n = cfg.HEAD_SIZE
    old = [[px[s + x, t + y] for x in range(n)] for y in range(n)]

    def near(x, y, kinds):
        return any(0 <= x + a < n and 0 <= y + b < n and old[y + b][x + a] in kinds
                   for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))

    # The eyes stay over the hair: their whites and greys, and the dark pixels beside them in the eye rows
    eyes = {(x, y) for y in range(n) for x in range(n) if old[y][x] in cfg.EYE_SLOTS}
    eyes |= {(x, y) for y in range(cfg.EYE_ROWS.start + dy, cfg.EYE_ROWS.stop + dy) for x in cfg.EYE_COLS
             if old[y][x] in cfg.EYE_DARK and near(x, y, cfg.EYE_NEAR)}
    new = {}
    for y in range(n):
        for x in range(n):
            v = old[y][x]
            if v == 0:
                continue
            if v in cfg.B2_HAIR:
                v = cfg.B2_HAIR[v]
            elif v == cfg.B2_HAIR_SHADE and near(x, y, cfg.B2_HAIR) and not near(x, y, cfg.FACE):
                v = cfg.HAIR_DARK
            # Other slots that edge Black 2's hair, away from the skin (cfg.HAIR_EDGE, where set): dark green too
            elif v in getattr(cfg, "HAIR_EDGE", ()) and near(x, y, cfg.B2_HAIR) and not near(x, y, cfg.SKIN):
                v = cfg.HAIR_DARK
            new[(x, y)] = v
    pp = pt.load()
    from_platinum = set()
    for py in cfg.PT_HAIR_ROWS:
        for ptx in cfg.PT_HAIR_COLS:
            v = pp[ptx, py]
            bx, by = cfg.PT_MIRROR - ptx, py + cfg.PT_DY + dy
            if not (0 <= bx < n and 0 <= by < n) or (bx, by) in eyes:
                continue
            if by > cfg.TRIM_ROW + dy and not old[by][bx]:
                continue
            # From the eyes down, Black 2's face stays its own (cfg.FACE_KEEP_FROM_ROW, where set)
            if by >= getattr(cfg, "FACE_KEEP_FROM_ROW", n) + dy and old[by][bx] in cfg.FACE:
                continue
            if v in cfg.PT_TO_B2:
                new[(bx, by)] = cfg.PT_TO_B2[v]
            elif v == 0xF and (ptx, py) in cfg.PT_HAIR_OUTLINE:
                new[(bx, by)] = 15
            elif v in cfg.PT_SKIN_TO_B2 and py <= cfg.PT_SKIN_MAX_ROW:
                new[(bx, by)] = cfg.PT_SKIN_TO_B2[v]
            else:
                continue
            from_platinum.add((bx, by))

    def on_edge(x, y):
        return any((x + a, y + b) not in new for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))

    # Black 2's hair left poking out of Platinum's crown goes; plain green on the lower outline turns dark: black, or
    # cfg.EDGE_DARK where set
    green = (cfg.HAIR_LIGHT, cfg.HAIR_MID, cfg.HAIR_DARK)
    for q in [q for q, v in new.items() if v in green and q not in from_platinum and q[1] <= cfg.TRIM_ROW + dy]:
        if on_edge(*q):
            del new[q]
    for q in [q for q, v in new.items() if v in (cfg.HAIR_LIGHT, cfg.HAIR_MID) and q[1] > cfg.TRIM_ROW + dy]:
        if on_edge(*q):
            new[q] = getattr(cfg, "EDGE_DARK", 15)
    for y in range(n):
        for x in range(n):
            px[s + x, t + y] = new.get((x, y), 0)


def still_cell(sprite):
    """The cell the still frame (multi-cell 1's one node) draws, and its node."""
    node = sprite["nmcr"][1][0]
    return sprite["nanr"][node[0]][1][0][0], node


STILL_SIZE, STILL_ORIGIN = (120, 120), (60, 110)


def set_nodes(nmcr, multicells):
    """Writes the multi-cells' nodes (seq, x, y, attr) over the file's, in place: the same nodes, maybe reordered."""
    off = 16
    while nmcr[off:off + 4] != b"KBCM":
        off += struct.unpack_from("<I", nmcr, off + 4)[0]
    base = off + 8
    _, _, mc_off, hier_off = struct.unpack_from("<HHII", nmcr, base)
    for m, nodes in enumerate(multicells):
        count, _, hoff = struct.unpack_from("<HHI", nmcr, base + mc_off + m * 8)
        assert count == len(nodes)
        for k, node in enumerate(nodes):
            struct.pack_into("<HhhH", nmcr, base + hier_off + hoff + k * 8, *node)


def node_at(sprite, seq, tick):
    """Where the node playing a cell animation is at a tick (x right, y down, from the sprite's origin), and the
    cell it draws."""
    x, y = next((n[1], n[2]) for n in sprite["nmcr"][0] if n[0] == seq)
    c, px, py = trainer_rig._at(sprite["nanr"][seq], tick)[:3]
    return x + px, y + py, c


def cell_origin(sprite, seq, tick):
    """Where the top left of the cell a node draws is on screen at a tick (from the sprite's origin), and the cell."""
    x, y, c = node_at(sprite, seq, tick)
    rx, ry = sprite["rects"][c][:2]
    return x + rx // 256, y - ry // 256, c


def clear_cell(tex, box):
    s, t, w, h = box
    tex.paste(0, (s, t, s + w, t + h))


def still_pose(sprite):
    """The earliest tick of the animation whose pose matches the still frame best."""
    still = trainer_rig.frame(sprite, 0, seq=1, size=STILL_SIZE, origin=STILL_ORIGIN).tobytes()
    ticks = sum(f[3] for f in sprite["nmar"][0][1])
    return min(range(ticks), key=lambda t: sum(
        1 for a, b in zip(trainer_rig.frame(sprite, t, size=STILL_SIZE, origin=STILL_ORIGIN).tobytes(), still)
        if a != b))


def build(cfg, b2_files, src):
    """The 8 files of the retextured sprite, from the Black 2 sprite's files and Platinum's front.png."""
    # the bin (file 6) is always raw: its first byte, the cell count, can look like LZ's
    lz = [k != 6 and f[0] in (0x10, 0x11) for k, f in enumerate(b2_files)]
    files = [bytearray(f if k == 6 else mts.unlz(f)) for k, f in enumerate(b2_files)]
    sprite = trainer_rig.read(b2_files)
    pose_tick = still_pose(sprite)
    tex = sprite["tex"]
    pal = tex.getpalette()[:48]
    for i, c in cfg.PALETTE.items():
        pal[i * 3:i * 3 + 3] = c
    tex.putpalette(pal + [0] * (768 - len(pal)))
    for c, remaps in cfg.REMAPS.items():
        recolour_cell(tex, cell_box(sprite, c), remaps)
    for c, dy in cfg.HEADS.items():
        mirrored_head(cfg, tex, cell_box(sprite, c), dy, src)
    # A retexture may also replace parts with pieces of Platinum's art: it changes the texture, the cells' rects
    # (sprite["rects"]) and the order nodes are drawn in (sprite["nmcr"]), in the still frame's pose
    rects, nodes = list(sprite["rects"]), [list(mc) for mc in sprite["nmcr"]]
    if hasattr(cfg, "customize"):
        cfg.customize(sprite, src, pose_tick)

    # The still frame, from the parts in its pose
    still, (_, node_x, node_y, _) = still_cell(sprite)
    s, t, w, h = cell_box(sprite, still)
    origin = STILL_ORIGIN
    pose = trainer_rig.frame(sprite, pose_tick, size=STILL_SIZE, origin=origin)
    box = pose.point(lambda v: 255 if v else 0).getbbox()
    assert box[2] - box[0] <= w and box[3] - box[1] <= h, "the first pose doesn't fit the still frame's room"
    tex.paste(0, (s, t, s + w, t + h))
    tex.paste(pose.crop(box), (s, t))
    struct.pack_into("<6i", files[6], 12 + still * 48, (box[0] - origin[0] - node_x) * 256,
                     (origin[1] + node_y - box[1]) * 256, (box[2] - box[0]) * 4096, (box[3] - box[1]) * 4096,
                     s * 4096, t * 4096)

    for c, r in enumerate(sprite["rects"]):
        if c != still and r != rects[c]:
            struct.pack_into("<6i", files[6], 12 + c * 48, *r)
    changed = set()
    if [list(mc) for mc in sprite["nmcr"]] != nodes:
        set_nodes(files[4], sprite["nmcr"])
        changed.add(4)

    # The texture, palette and 2D characters into Black 2's files
    tp = tex.load()
    texture = bytearray(mts.TEX_W * mts.TEX_H // 2)
    for i in range(mts.TEX_W * mts.TEX_H):
        texture[i // 2] |= (tp[i % mts.TEX_W, i // mts.TEX_W] & 15) << (4 * (i & 1))
    assert struct.unpack_from("<HH", files[1], 0x18) == (mts.TEX_H // 8, mts.TEX_W // 8)
    files[1][0x30:0x30 + len(texture)] = texture
    data = struct.unpack_from("<I", files[7], 0x10 + 0x14)[0]
    for c in range(16):
        r, g, b = pal[c * 3:c * 3 + 3]
        struct.pack_into("<H", files[7], 0x10 + 0x08 + data + c * 2, (r >> 3) | (g >> 3) << 5 | (b >> 3) << 10)
    size = struct.unpack_from("<I", files[0], 0x28)[0]
    for i in range(0x30, 0x30 + size):
        lo, hi = files[0][i] & 15, files[0][i] >> 4
        files[0][i] = cfg.CHARS_REMAP.get(lo, lo) | cfg.CHARS_REMAP.get(hi, hi) << 4

    return [bytes(b2_files[k]) if k in (2, 3, 4, 5) and k not in changed else
            mts.lz10(bytes(f)) if compressed else bytes(f)
            for k, (f, compressed) in enumerate(zip(files, lz))]


def main():
    import ndspy.narc
    import ndspy.rom
    rom, platinum = ndspy.rom.NintendoDSRom.fromFile(sys.argv[1]), Path(sys.argv[2])
    cfg = importlib.import_module(sys.argv[3])
    out = Path(sys.argv[4])
    out.mkdir(parents=True, exist_ok=True)
    narc = ndspy.narc.NARC(rom.getFileByName("a/0/7/1"))
    b2_files = narc.files[cfg.B2_SPRITE * 8:(cfg.B2_SPRITE + 1) * 8]
    src = Image.open(platinum / "res/trainers/classes" / cfg.PLATINUM_CLASS / "front.png")
    files = build(cfg, b2_files, src)
    sums = []
    for k, f in enumerate(files):
        (out / f"file{k}.bin").write_bytes(f)
        sums.append(f"{hashlib.sha1(f).hexdigest()}  file{k}.bin")
    (out / "sha1.txt").write_text("\n".join(sums) + "\n")
    print("\n".join(sums))
    kept = [k for k in (2, 3, 4, 5) if files[k] == b2_files[k]]
    print("Black 2's animation files kept as they are:", kept, "changed:", [k for k in (2, 3, 4, 5) if k not in kept])

    original, new = trainer_rig.read(b2_files), trainer_rig.read(files)
    length = sum(f[3] for f in original["nmar"][0][1])
    frames = []
    for t in range(0, length + 60, 2):
        img = Image.new("RGB", (220, 124))
        for i, sp in enumerate((original, new)):
            f = trainer_rig.frame(sp, min(t, length - 1), size=(110, 124), origin=(55, 118))
            bg = Image.new("RGB", f.size, (232, 236, 240))
            bg.paste(f.convert("RGB"), (0, 0), trainer_rig.opaque(f))
            img.paste(bg, (i * 110, 0))
        frames.append(img.resize((660, 372), Image.NEAREST))
    frames[0].save(out / "preview.gif", save_all=True, append_images=frames[1:], duration=33, loop=0)


if __name__ == "__main__":
    main()
