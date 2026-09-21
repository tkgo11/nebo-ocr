"""Rendering and line-segmentation tests."""
from __future__ import annotations

from pathlib import Path

import numpy as np

from nebo_ocr import RenderOptions, load_nebo, page_to_svg, render_page, strokes_to_lines


def test_render_page_nonempty(sample_nebo: Path):
    nb = load_nebo(sample_nebo)
    img = render_page(nb.pages[0], RenderOptions(dpi=150))
    arr = np.asarray(img)
    assert img.width > 50 and img.height > 20
    # ink present: some pixels darker than the white background
    assert (arr < 128).any()


def test_render_empty_page(empty_nebo: Path):
    nb = load_nebo(empty_nebo)
    img = render_page(nb.pages[0])
    assert img.width == 64  # fallback canvas


def test_lines_from_tags(sample_nebo: Path):
    nb = load_nebo(sample_nebo)
    lines = strokes_to_lines(nb.pages[0])
    assert len(lines) == 2  # two TEXT_LINE tag groups
    y0 = sorted(ln.bounds()[1] for ln in lines)
    assert y0[0] < y0[1]


def test_lines_geometric_fallback(empty_nebo: Path, tmp_path: Path):
    from conftest import make_nebo

    # no TEXT_LINE tags -> geometric clustering on y
    strokes = [
        ([float(i) for i in range(5)], [10.0] * 5, None),
        ([float(i) for i in range(5)], [11.0] * 5, None),
        ([float(i) for i in range(5)], [50.0] * 5, None),
    ]
    p = make_nebo(tmp_path / "geo.nebo", [("page0001", strokes, None)])
    nb = load_nebo(p)
    lines = strokes_to_lines(nb.pages[0])
    assert len(lines) == 2
    counts = sorted(len(ln.strokes) for ln in lines)
    assert counts == [1, 2]


def test_svg_export(sample_nebo: Path):
    nb = load_nebo(sample_nebo)
    svg = page_to_svg(nb.pages[0])
    assert svg.startswith("<svg")
    assert svg.count("<path") == 3
    assert 'stroke="#000000"' in svg or "stroke=" in svg
