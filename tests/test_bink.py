"""BINK codec round-trip tests."""
from __future__ import annotations

import pytest

from nebo_ocr.bink import BinkError, BinkTag, encode_bink, parse_bink


def test_roundtrip_strokes():
    xs = [10.0, 10.5, 11.0, 12.25]
    ys = [20.0, 21.0, 20.5, 22.0]
    fs = [10, 128, 255, 90]
    doc = parse_bink(encode_bink([(xs, ys, fs)]))
    assert doc.version == 5
    assert [n for n, _ in doc.channels] == ["X", "Y", "F", "T"]
    assert len(doc.strokes) == 1
    s = doc.strokes[0]
    assert s.record_index == 0
    assert s.timestamp_us is None
    assert s.x == pytest.approx(xs, abs=0.005)
    assert s.y == pytest.approx(ys, abs=0.005)
    assert s.f == fs


def test_roundtrip_multiple_and_delta_precision():
    strokes = [
        ([0.0, 0.001, 0.002], [5.0, 5.001, 5.002], None),
        ([100.5, 99.5, 50.25], [1.0, 2.0, 3.0], [255, 0, 128]),
    ]
    doc = parse_bink(encode_bink(strokes))
    assert len(doc.strokes) == 2
    assert doc.strokes[0].x == pytest.approx(strokes[0][0], abs=0.003)
    assert doc.strokes[1].y == pytest.approx(strokes[1][1], abs=0.003)


def test_roundtrip_tags():
    tags = [
        BinkTag(name="pen-025", node_id=None, groups=[(0, 1, 0, 0)], text=""),
        BinkTag(name="DIAGRAM", node_id=42, groups=[(0, 0, 0, 50)],
                text='{"DWLabel":"ciao"}'),
    ]
    doc = parse_bink(encode_bink([([1.0, 2.0], [3.0, 4.0], None)] * 2, tags))
    names = [t.name for t in doc.tags]
    assert "pen-025" in names
    assert "DIAGRAM" in names
    diagram = next(t for t in doc.tags if t.name == "DIAGRAM")
    assert diagram.node_id == 42
    assert diagram.text == '{"DWLabel":"ciao"}'
    assert diagram.groups == [(0, 0, 0, 50)]


def test_bad_magic():
    with pytest.raises(BinkError):
        parse_bink(b"NOPE" + b"\x00" * 50)


def test_truncated():
    blob = encode_bink([([1.0, 2.0], [3.0, 4.0], None)])
    with pytest.raises(BinkError):
        parse_bink(blob[:100])


def test_empty():
    doc = parse_bink(encode_bink([]))
    assert doc.strokes == []
    assert doc.tags == []
