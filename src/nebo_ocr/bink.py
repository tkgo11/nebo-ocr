"""MyScript ``ink.bink`` (BINK v5) codec.

BINK is MyScript iink's byte-packed binary ink format. A ``.nebo`` file stores
one ``pages/<id>/ink.bink`` per page. Layout (all little-endian)::

    "BINK" u8 u8                      # magic + version-ish (observed 00 05)
    u32 version (=5)  u32 1
    u32 nchannels                     # 4 observed: X, Y, F, T
      per channel: str name, 4B type tag, u32 has_unit, [str unit]
    u32 layout_len + layout table     # per-channel point layout (skipped)
    u32 precision_x (=1000) u32 precision_y (=1000)
    u32 unk (=3) u8 0
    u32 nstrokes
      per stroke:
        u32 flags                     # 0x80000000 normal, 0xffffffff tombstone
        u64 t0                        # µs since epoch (0xffffffffffffffff = none)
        f32 x0 f32 y0                 # first point, mm
        u32 unk u16 0 u32 npoints
        i16 dx[n] i16 dy[n]           # first differences; mm = cumsum / 500
        u8  f[n]                      # force, 255 = full (no pressure sensor)
    tag table: u32 0, u32 count, u8 0
      per record: [u32 kind u32 id u32 0  -- on all but the first record]
        str name
        u32 ngroups
          per group: u16 u16 span_start u32 first_stroke
                     u8 u8 u16 span_end u32 last_stroke
        str text                      # e.g. CSS for ".STYLE", JSON for "DIAGRAM"
    44-byte trailer

This implementation was written against the public byte-level description of
the format (the same one reverse-engineered and documented by the MIT-licensed
``inkterop`` project) and validated on real .nebo exports.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass
from itertools import accumulate

#: mm per stored coordinate-delta unit (empirical: 1 unit = 2 µm).
DELTA_UNITS_PER_MM = 500.0

FLAG_NORMAL = 0x80000000
FLAG_TOMBSTONE = 0xFFFFFFFF


class BinkError(ValueError):
    """Raised when an ink.bink blob cannot be decoded."""


class _Cursor:
    def __init__(self, buf: bytes) -> None:
        self.buf = buf
        self.pos = 0

    def _unpack(self, fmt: str) -> int | float:
        try:
            (val,) = struct.unpack_from(fmt, self.buf, self.pos)
        except struct.error as exc:
            raise BinkError(f"truncated at 0x{self.pos:x}") from exc
        self.pos += struct.calcsize(fmt)
        if isinstance(val, (int, float)):
            return val
        raise BinkError(f"unexpected unpacked value at 0x{self.pos:x}")

    def u8(self) -> int:
        return int(self._unpack("<B"))

    def u16(self) -> int:
        return int(self._unpack("<H"))

    def u32(self) -> int:
        return int(self._unpack("<I"))

    def u64(self) -> int:
        return int(self._unpack("<Q"))

    def f32(self) -> float:
        return float(self._unpack("<f"))

    def raw(self, n: int) -> bytes:
        if n < 0 or self.pos + n > len(self.buf):
            raise BinkError(f"truncated at 0x{self.pos:x}")
        out = self.buf[self.pos : self.pos + n]
        self.pos += n
        return out

    def string(self, limit: int = 1 << 20) -> str:
        n = self.u32()
        if n > limit:
            raise BinkError(f"implausible string length {n} at 0x{self.pos - 4:x}")
        return self.raw(n).decode("utf-8", "replace")


@dataclass
class BinkStroke:
    """Raw decoded stroke: points as parallel channel arrays (mm, 0..255)."""

    record_index: int
    timestamp_us: int | None
    x: list[float]
    y: list[float]
    f: list[int]


@dataclass
class BinkTag:
    """Raw decoded tag-table record."""

    name: str
    node_id: int | None
    groups: list[tuple[int, int, int, int]]  # (first, last, span_start, span_end)
    text: str


@dataclass
class BinkDocument:
    version: int
    channels: list[tuple[str, str | None]]
    strokes: list[BinkStroke]
    tags: list[BinkTag]


def parse_bink(data: bytes) -> BinkDocument:
    """Decode one ink.bink blob.

    Tolerant of the trailing recognition-tree trailer: if the tag table
    cannot be fully walked, strokes (already decoded) are kept and parsing
    of tags stops silently at the first malformed record.
    """
    if data[:4] != b"BINK":
        raise BinkError("bad magic")
    c = _Cursor(data)
    c.pos = 4
    c.u8()
    c.u8()
    version = c.u32()
    c.u32()
    channels: list[tuple[str, str | None]] = []
    for _ in range(c.u32()):
        name = c.string(64)
        c.raw(4)  # type tag
        unit = c.string(64) if c.u32() else None
        channels.append((name, unit))
    c.raw(c.u32())  # per-channel layout table
    c.u32()  # precision x
    c.u32()  # precision y
    c.u32()
    c.u8()
    nstrokes = c.u32()
    if nstrokes > 1_000_000:
        raise BinkError(f"implausible stroke count {nstrokes}")

    strokes: list[BinkStroke] = []
    for rec in range(nstrokes):
        flags = c.u32()
        if flags == FLAG_TOMBSTONE:
            continue  # erased stroke: single -1 word, still counted
        t0 = c.u64()
        x0, y0 = c.f32(), c.f32()
        c.u32()
        c.u16()
        n = c.u32()
        if not 0 < n < 1_000_000:
            raise BinkError(f"implausible point count {n} at 0x{c.pos - 4:x}")
        dx = struct.unpack_from(f"<{n}h", c.raw(2 * n))
        dy = struct.unpack_from(f"<{n}h", c.raw(2 * n))
        f = list(c.raw(n))
        strokes.append(
            BinkStroke(
                record_index=rec,
                timestamp_us=None if t0 == 0xFFFFFFFFFFFFFFFF else t0,
                x=[x0 + d / DELTA_UNITS_PER_MM for d in accumulate(dx)],
                y=[y0 + d / DELTA_UNITS_PER_MM for d in accumulate(dy)],
                f=f,
            )
        )

    tags: list[BinkTag] = []
    try:
        c.u32()
        count = c.u32()
        c.u8()
        for i in range(count):
            node_id: int | None = None
            if i > 0:
                c.u32()  # kind
                node_id = c.u32()
                c.u32()
            name = c.string(4096)
            groups: list[tuple[int, int, int, int]] = []
            for _ in range(c.u32()):
                c.u16()
                span_start = c.u16()
                first = c.u32()
                c.raw(2)  # usually 05 ff
                span_end = c.u16()
                last = c.u32()
                groups.append((min(first, last), max(first, last), span_start, span_end))
            text = c.string(1 << 20)
            tags.append(BinkTag(name=name, node_id=node_id, groups=groups, text=text))
    except BinkError:
        pass  # keep strokes; the 44-byte trailer isn't part of the tag table

    return BinkDocument(version=version, channels=channels, strokes=strokes, tags=tags)


def encode_bink(
    strokes: list[tuple[list[float], list[float], list[int] | None]],
    tags: list[BinkTag] | None = None,
) -> bytes:
    """Encode strokes + tags into a BINK v5 blob.

    ``strokes`` items are ``(xs_mm, ys_mm, force_0_255 | None)``. Used to build
    synthetic .nebo fixtures; also handy for round-trip testing.
    """
    out = bytearray()
    out += b"BINK\x00\x05"
    out += struct.pack("<II", 5, 1)
    channel_decls = [
        (b"X", b"\x20\x04\x01\x00", b"mm"),
        (b"Y", b"\x20\x04\x01\x00", b"mm"),
        (b"F", b"\x20\x04\x01\x00", None),
        (b"T", b"\x20\x02\x01\x00", b"ms"),
    ]
    out += struct.pack("<I", len(channel_decls))
    for name, type_tag, unit in channel_decls:
        out += struct.pack("<I", len(name)) + name
        out += type_tag
        if unit is None:
            out += struct.pack("<I", 0)
        else:
            out += struct.pack("<II", 1, len(unit)) + unit
    layout = struct.pack("<I", 4) + b"".join(
        struct.pack("<III", off, stride, size) + type_tag
        for (off, stride, size), (_, type_tag, _) in zip(
            [(0, 0, 8), (4, 0, 8), (0, 8, 4), (0, 12, 4)], channel_decls, strict=True
        )
    )
    out += struct.pack("<I", len(layout)) + layout
    out += struct.pack("<IIIB", 1000, 1000, 3, 0)
    out += struct.pack("<I", len(strokes))
    for xs, ys, fs in strokes:
        n = len(xs)
        dxs = [0] + [round((xs[i] - xs[i - 1]) * DELTA_UNITS_PER_MM) for i in range(1, n)]
        dys = [0] + [round((ys[i] - ys[i - 1]) * DELTA_UNITS_PER_MM) for i in range(1, n)]
        out += struct.pack("<I", FLAG_NORMAL)
        out += struct.pack("<Q", 0xFFFFFFFFFFFFFFFF)
        out += struct.pack("<ff", xs[0], ys[0])
        out += struct.pack("<IHI", 0, 0, n)  # unk + u16 pad + point count
        out += struct.pack(f"<{n}h", *dxs)
        out += struct.pack(f"<{n}h", *dys)
        out += bytes(fs if fs is not None else [255] * n)
    tags = tags or []
    out += struct.pack("<II", 0, len(tags)) + b"\x00"
    for i, tag in enumerate(tags):
        if i > 0:
            out += struct.pack("<III", 0, tag.node_id or 0, 0)
        name = tag.name.encode()
        out += struct.pack("<I", len(name)) + name
        out += struct.pack("<I", len(tag.groups))
        for first, last, ss, se in tag.groups:
            out += struct.pack("<HHI", 3, ss, first)
            out += b"\x05\xff"
            out += struct.pack("<HI", se, last)
        text = tag.text.encode()
        out += struct.pack("<I", len(text)) + text
    out += b"\x12" + b"\x00" * 43  # terminator record
    return bytes(out)
