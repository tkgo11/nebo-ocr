"""CLI smoke tests."""
from __future__ import annotations

from pathlib import Path

from nebo_ocr.cli import main


def test_info(sample_nebo: Path, capsys):
    assert main(["info", str(sample_nebo)]) == 0
    out = capsys.readouterr().out
    assert "pages:     1" in out
    assert "strokes:   3" in out
    assert "English (United States)" in out


def test_extract(sample_nebo: Path, capsys):
    assert main(["extract", str(sample_nebo)]) == 0
    out = capsys.readouterr().out
    assert "hello world" in out
    assert "second line" in out


def test_extract_json(sample_nebo: Path, capsys):
    import json

    assert main(["extract", str(sample_nebo), "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["language"] == "en_US"
    assert data["pages"][0]["text"] == "hello world\nsecond line"


def test_recognize_bad_backend(sample_nebo: Path, capsys):
    assert main(["recognize", str(sample_nebo), "-b", "nope"]) == 2
    assert "unknown backend" in capsys.readouterr().err


def test_render(sample_nebo: Path, tmp_path: Path, capsys):
    outdir = tmp_path / "out"
    assert main(["render", str(sample_nebo), "-o", str(outdir)]) == 0
    pngs = list(outdir.glob("*.png"))
    assert len(pngs) == 1
    assert pngs[0].stat().st_size > 100


def test_render_svg(sample_nebo: Path, tmp_path: Path):
    outdir = tmp_path / "svg"
    assert main(["render", str(sample_nebo), "-o", str(outdir), "--svg"]) == 0
    svgs = list(outdir.glob("*.svg"))
    assert len(svgs) == 1
    assert "<svg" in svgs[0].read_text()


def test_languages(capsys):
    assert main(["languages", "-b", "myscript"]) == 0
    out = capsys.readouterr().out
    assert "myscript" in out and "it_IT" in out and "ja_JP" in out


def test_backends(capsys):
    assert main(["backends"]) == 0
    out = capsys.readouterr().out
    assert "embedded" in out and "myscript" in out
    assert main(["backends", "-l", "ja_JP"]) == 0
    out = capsys.readouterr().out
    assert "Japanese" in out
