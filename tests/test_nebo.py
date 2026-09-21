"""Container-level tests for .nebo loading."""
from __future__ import annotations

from pathlib import Path

from nebo_ocr import is_nebo_file, load_nebo


def test_load_sample(sample_nebo: Path):
    nb = load_nebo(sample_nebo)
    assert nb.title == "sample"
    assert nb.language == "en_US"
    assert len(nb.pages) == 1
    page = nb.pages[0]
    assert page.page_id == "pageid01"
    assert len(page.strokes) == 3
    assert page.extent == (0.0, 0.0, 210.0, 297.0)
    # brush tag resolved
    assert all(s.pen == "pen-025" for s in page.strokes)
    assert all(s.width_mm == 0.25 for s in page.strokes)
    # embedded labels
    assert page.diagram_labels() == ["hello world", "second line"]


def test_load_empty(empty_nebo: Path):
    nb = load_nebo(empty_nebo)
    assert len(nb.pages) == 1
    assert nb.pages[0].strokes == []
    assert nb.pages[0].diagram_labels() == []


def test_is_nebo_file(sample_nebo: Path, tmp_path: Path):
    assert is_nebo_file(sample_nebo)
    other = tmp_path / "other.zip"
    import zipfile

    with zipfile.ZipFile(other, "w") as zf:
        zf.writestr("x.txt", "hi")
    assert not is_nebo_file(other)
    assert not is_nebo_file(tmp_path / "nonexistent.nebo")


def test_multi_page(tmp_path: Path):
    from conftest import make_nebo

    p = make_nebo(
        tmp_path / "multi.nebo",
        [
            ("aaaa0001", [([1.0, 2.0], [3.0, 4.0], None)], None),
            ("bbbb0002", [([5.0, 6.0], [7.0, 8.0], None),
                          ([9.0, 10.0], [11.0, 12.0], None)], None),
        ],
        language="ko_KR",
    )
    nb = load_nebo(p)
    assert nb.language == "ko_KR"
    assert [pg.page_id for pg in nb.pages] == ["aaaa0001", "bbbb0002"]
    assert nb.stroke_count == 3
