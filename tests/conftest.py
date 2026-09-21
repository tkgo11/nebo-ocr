"""Synthetic .nebo fixtures built with the BINK encoder — no copyrighted
sample files needed."""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from nebo_ocr.bink import BinkTag, encode_bink


def make_nebo(
    path: Path,
    pages: list[tuple[str, list[tuple[list[float], list[float], list[int] | None]],
                     list[BinkTag] | None]],
    language: str = "en_US",
) -> Path:
    """Write a minimal-but-real .nebo container."""
    rel = {"pages": {pid: {"version": 5} for pid, _, _ in pages}, "objects": {}}
    meta = {
        "format-version": "4.0",
        "Document_Version": "1.11",
        "Application": "iink",
        "Application_Version": "2.0.6",
        "languageLocaleIdentifier": language,
    }
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("rel.json", json.dumps(rel))
        zf.writestr("meta.json", json.dumps(meta))
        zf.writestr("index.bdom", b"BDOM\x00\x00")
        for pid, strokes, tags in pages:
            zf.writestr(f"pages/{pid}/ink.bink", encode_bink(strokes, tags))
            zf.writestr(f"pages/{pid}/meta.json", json.dumps(
                {"creationDate": "2026-01-01 10:00:00.000000",
                 "pageHasContent": bool(strokes),
                 "languageLocaleIdentifier": language,
                 "pageExtent": [0, 0, 210, 297]}
            ))
            zf.writestr(f"pages/{pid}/page.bdom", b"BDOM\x00\x00")
            zf.writestr(f"pages/{pid}/style.css", ".pen-025 { -myscript-pen-width: 0.625; }")
    return path


@pytest.fixture
def sample_strokes() -> list[tuple[list[float], list[float], list[int] | None]]:
    # three strokes forming two "lines"
    return [
        ([10.0 + i * 0.4 for i in range(20)], [20.0] * 20, None),
        ([10.0 + i * 0.4 for i in range(20)], [22.0 + (i % 3) * 0.1 for i in range(20)], None),
        ([15.0 + i * 0.5 for i in range(15)], [40.0] * 15, None),
    ]


@pytest.fixture
def sample_nebo(tmp_path: Path, sample_strokes) -> Path:
    tags = [
        BinkTag(name="pen-025", node_id=1, groups=[(0, 2, 0, 0)], text=""),
        BinkTag(name="TEXT_LINE", node_id=2, groups=[(0, 1, 0, 0)], text=""),
        BinkTag(name="TEXT_LINE", node_id=3, groups=[(2, 2, 0, 0)], text=""),
        BinkTag(
            name="DIAGRAM",
            node_id=4,
            groups=[(0, 1, 0, 0)],
            text=json.dumps({"DWShape": "text", "DWTagId": 4,
                             "DWLabel": "hello world"}),
        ),
        BinkTag(
            name="DIAGRAM",
            node_id=5,
            groups=[(2, 2, 0, 0)],
            text=json.dumps({"DWShape": "text", "DWTagId": 5,
                             "DWLabel": "second line"}),
        ),
    ]
    return make_nebo(tmp_path / "sample.nebo", [("pageid01", sample_strokes, tags)])


@pytest.fixture
def empty_nebo(tmp_path: Path) -> Path:
    return make_nebo(tmp_path / "empty.nebo", [("blank001", [], None)])
