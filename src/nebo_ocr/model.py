"""Data model for parsed .nebo notebooks.

Coordinates are millimeters, y grows downward, page origin top-left —
the same convention the MyScript iink renderer uses inside .nebo files
(``pageExtent [0, 0, 210, 297]`` is an A4 portrait page).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Point:
    """One captured ink sample."""

    x: float  # mm, page origin top-left, y down
    y: float
    force: float = 1.0  # 0..1, 1.0 = no pressure sensor / full pressure
    t: float | None = None  # ms relative to stroke start, when known


@dataclass
class Stroke:
    """A pen trajectory between pointer-down and pointer-up."""

    points: list[Point]
    record_index: int = -1  # index in the bink record stream (counts tombstones)
    timestamp_us: int | None = None  # µs since epoch of pointer-down, if present
    pen: str | None = None  # brush class e.g. "pen-025", "ballpoint-1-0"
    color: str | None = None  # "#rrggbb" from .STYLE, if present
    width_mm: float | None = None  # resolved stroke width in mm
    highlighter: bool = False

    def bounds(self) -> tuple[float, float, float, float]:
        xs = [p.x for p in self.points]
        ys = [p.y for p in self.points]
        return min(xs), min(ys), max(xs), max(ys)


@dataclass
class Tag:
    """One record of the bink tag table.

    A tag assigns a name (brush class, style, grouping, or recognition-tree
    node like WORD/CHAR/TEXT_LINE/DIAGRAM) to a run of stroke records.
    """

    name: str
    node_id: int | None = None
    # Inclusive stroke-record ranges; spans are point offsets into the
    # first/last stroke of each range.
    groups: list[tuple[int, int, int, int]] = field(default_factory=list)
    text: str = ""

    def covers(self, record_index: int) -> bool:
        return any(first <= record_index <= last for first, last, _, _ in self.groups)


@dataclass
class TextLine:
    """A line of handwriting — either a TEXT_LINE tag group or a geometric
    cluster of strokes."""

    strokes: list[Stroke]

    def bounds(self) -> tuple[float, float, float, float]:
        x0, y0, x1, y1 = self.strokes[0].bounds()
        for s in self.strokes[1:]:
            a, b, c, d = s.bounds()
            x0, y0, x1, y1 = min(x0, a), min(y0, b), max(x1, c), max(y1, d)
        return x0, y0, x1, y1


@dataclass
class Page:
    """One notebook page: raw ink plus the recognition/styling tag table."""

    page_id: str
    strokes: list[Stroke] = field(default_factory=list)
    tags: list[Tag] = field(default_factory=list)
    extent: tuple[float, float, float, float] = (0.0, 0.0, 210.0, 297.0)
    language: str | None = None  # e.g. "it_IT" from page or document meta
    creation_date: str | None = None

    def tags_for(self, stroke: Stroke) -> list[Tag]:
        return [t for t in self.tags if t.covers(stroke.record_index)]

    def diagram_labels(self) -> list[str]:
        """Recognized text labels MyScript embedded in DIAGRAM tags."""
        out: list[str] = []
        for tag in self.tags:
            if tag.name != "DIAGRAM" or not tag.text:
                continue
            import json

            try:
                payload = json.loads(tag.text)
            except json.JSONDecodeError:
                continue
            label = payload.get("DWLabel")
            if isinstance(label, str) and label.strip():
                out.append(label)
        return out


@dataclass
class Notebook:
    """A parsed .nebo container."""

    path: str
    title: str
    pages: list[Page] = field(default_factory=list)
    language: str | None = None  # document-level languageLocaleIdentifier
    application_version: str | None = None
    document_version: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def stroke_count(self) -> int:
        return sum(len(p.strokes) for p in self.pages)
