"""``.nebo`` container reader.

A .nebo file (MyScript Nebo / "MyScript Notes" notebook export, also used by
Kobo's MyScript-based notebooks) is a plain zip::

    rel.json                        # {"pages": {"<id>": {...}}, "objects": ...}
    meta.json                       # format-version, languageLocaleIdentifier, ...
    index.bdom                      # document skeleton (unused here)
    pages/<id>/meta.json            # creationDate, Type, pageExtent, locale
    pages/<id>/ink.bink             # BINK v5 ink + recognition/style tag table
    pages/<id>/page.bdom            # recognition lattice (not decoded)
    pages/<id>/style.css            # named style classes
"""
from __future__ import annotations

import json
import logging
import re
import zipfile
from pathlib import Path
from typing import Any

from .bink import BinkDocument, BinkError, parse_bink
from .model import Notebook, Page, Point, Stroke, Tag

_logger = logging.getLogger(__name__)

_BRUSH_RE = re.compile(r"^(?:pen|brush)-(\d{3,4})$")
_COLOR_RE = re.compile(r"color:\s*#([0-9a-fA-F]{6,8})")
_WIDTH_RE = re.compile(r"-myscript-pen-width:\s*([\d.]+)")


def is_nebo_file(path: str | Path) -> bool:
    """Cheap sniff: zip containing rel.json and a bdom/bink member."""
    try:
        if not zipfile.is_zipfile(path):
            return False
        with zipfile.ZipFile(path) as zf:
            names = zf.namelist()
        return "rel.json" in names and any(
            n.endswith("/ink.bink") or n.endswith(".bdom") for n in names
        )
    except OSError:
        return False


def _read_json(zf: zipfile.ZipFile, name: str) -> dict[str, Any]:
    try:
        data = json.loads(zf.read(name))
        return data if isinstance(data, dict) else {}
    except (KeyError, json.JSONDecodeError):
        return {}


def _style_of(css: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    m = _COLOR_RE.search(css)
    if m:
        out["color"] = "#" + m.group(1).lower()
    m = _WIDTH_RE.search(css)
    if m:
        out["width_mm"] = float(m.group(1))
    return out


def _strokes_from_bink(doc: BinkDocument) -> tuple[list[Stroke], list[Tag]]:
    tags = [Tag(name=t.name, node_id=t.node_id, groups=t.groups, text=t.text) for t in doc.tags]
    by_record: dict[int, list[Tag]] = {}
    for tag in tags:
        for first, last, _, _ in tag.groups:
            for rec in range(first, last + 1):
                by_record.setdefault(rec, []).append(tag)

    strokes: list[Stroke] = []
    for raw in doc.strokes:
        mine = by_record.get(raw.record_index, [])
        style: dict[str, Any] = {}
        pen: str | None = None
        highlight = False
        for tag in mine:
            if tag.name == ".STYLE" and tag.text:
                style.update(_style_of(tag.text.strip('"')))
            elif _BRUSH_RE.match(tag.name):
                pen = tag.name
            elif tag.name == "HIGHLIGHT_STROKES":
                highlight = True
        width_mm = style.get("width_mm")
        if width_mm is None and pen:
            m = _BRUSH_RE.match(pen)
            if m:
                width_mm = int(m.group(1)) / 100.0
        strokes.append(
            Stroke(
                points=[
                    Point(x=x, y=y, force=f / 255.0)
                    for x, y, f in zip(raw.x, raw.y, raw.f, strict=True)
                ],
                record_index=raw.record_index,
                timestamp_us=raw.timestamp_us,
                pen=pen,
                color=style.get("color"),
                width_mm=width_mm,
                highlighter=highlight,
            )
        )
    return strokes, tags


def load_nebo(path: str | Path) -> Notebook:
    """Parse a .nebo file into a Notebook (pages of Strokes + Tags)."""
    path = Path(path)
    with zipfile.ZipFile(path) as zf:
        rel = _read_json(zf, "rel.json")
        meta = _read_json(zf, "meta.json")
        page_ids = list(rel.get("pages", {}))
        if not page_ids:
            page_ids = sorted(
                {n.split("/")[1] for n in zf.namelist() if n.startswith("pages/")}
            )
        doc_lang = meta.get("languageLocaleIdentifier")

        pages: list[Page] = []
        for pid in page_ids:
            page_meta = _read_json(zf, f"pages/{pid}/meta.json")
            extent = page_meta.get("pageExtent") or [0, 0, 210, 297]
            strokes: list[Stroke] = []
            tags: list[Tag] = []
            try:
                doc = parse_bink(zf.read(f"pages/{pid}/ink.bink"))
            except KeyError:
                doc = None
            except BinkError as exc:
                _logger.warning("page %s: unreadable ink.bink (%s)", pid, exc)
                doc = None
            if doc is not None:
                strokes, tags = _strokes_from_bink(doc)
            try:
                ex = [float(v) for v in extent[:4]]
            except (TypeError, ValueError):
                ex = []
            ex = [*ex, 0.0, 0.0, 210.0, 297.0][:4]
            pages.append(
                Page(
                    page_id=pid,
                    strokes=strokes,
                    tags=tags,
                    extent=(ex[0], ex[1], ex[2], ex[3]),
                    language=page_meta.get("languageLocaleIdentifier") or doc_lang,
                    creation_date=page_meta.get("creationDate"),
                )
            )

    return Notebook(
        path=str(path),
        title=str(meta.get("pageTitle") or path.stem),
        pages=pages,
        language=doc_lang,
        application_version=meta.get("Application_Version"),
        document_version=meta.get("Document_Version"),
        meta=meta,
    )
