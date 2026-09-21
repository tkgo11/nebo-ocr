"""Backend tests: embedded end-to-end; cloud backends via mocked HTTP."""
from __future__ import annotations

import hashlib
import hmac as hmac_mod
import json
from pathlib import Path

import pytest

from nebo_ocr import load_nebo, recognize
from nebo_ocr.backends import available_backends, registry
from nebo_ocr.backends.base import BackendUnavailable
from nebo_ocr.backends.myscript import (
    MyScriptCloudRecognizer,
    _batch_body,
    _jiix_text,
    _recognize_body,
)


def test_registry_complete():
    names = set(registry())
    assert names == {
        "embedded", "myscript", "google", "azure", "mathpix",
        "surya", "easyocr", "paddleocr", "trocr",
    }


def test_embedded_end_to_end(sample_nebo: Path):
    res = recognize(sample_nebo, backend="embedded")
    assert res.backend == "embedded"
    assert res.language == "en_US"
    assert res.pages[0].text == "hello world\nsecond line"
    assert [ln.text for ln in res.pages[0].lines] == ["hello world", "second line"]


def test_embedded_empty(empty_nebo: Path):
    res = recognize(empty_nebo, backend="embedded")
    assert res.pages[0].text == ""


def test_unknown_backend(sample_nebo: Path):
    with pytest.raises(BackendUnavailable, match="unknown backend"):
        recognize(sample_nebo, backend="nonexistent")


def test_myscript_unavailable_without_keys(sample_nebo: Path, monkeypatch):
    monkeypatch.delenv("MYSCRIPT_APPLICATION_KEY", raising=False)
    monkeypatch.delenv("MYSCRIPT_HMAC_KEY", raising=False)
    ok, why = MyScriptCloudRecognizer().available()
    assert not ok and "MYSCRIPT" in why
    with pytest.raises(BackendUnavailable):
        recognize(sample_nebo, backend="myscript")


def test_myscript_body_shapes(sample_nebo: Path):
    nb = load_nebo(sample_nebo)
    page = nb.pages[0]
    body = _recognize_body(page, "it_IT")
    assert body["contentType"] == "Text"
    assert body["scaleX"] == 1.0 and body["scaleY"] == 1.0
    assert body["configuration"]["lang"] == "it_IT"
    assert len(body["strokes"]) == 3
    assert body["strokes"][0]["x"][0] == pytest.approx(10.0)

    batch = _batch_body(page, "ko_KR")
    assert batch["contentType"] == "Text"
    assert batch["configuration"]["lang"] == "ko_KR"
    assert batch["width"] == round(210 * 96 / 25.4)
    first = batch["strokeGroups"][0]["strokes"][0]
    assert first["x"][0] == pytest.approx(10.0 * 96 / 25.4, abs=0.01)


def test_myscript_post_hmac(monkeypatch):
    """The HMAC header must be sha512(body, appKey+hmacKey)."""
    monkeypatch.setenv("MYSCRIPT_APPLICATION_KEY", "APP")
    monkeypatch.setenv("MYSCRIPT_HMAC_KEY", "SECRET")
    rec = MyScriptCloudRecognizer()
    captured = {}

    class FakeResp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return json.dumps({"type": "Text", "children": [
                {"type": "TextLine", "label": "ciao"},
            ]}).encode()

    def fake_urlopen(req, timeout=0):
        captured["url"] = req.full_url
        captured["app"] = (
            req.headers["Applicationkey"]
            if "Applicationkey" in req.headers
            else req.headers.get("applicationKey")
        )
        captured["hmac"] = req.headers.get("Hmac") or req.headers.get("hmac")
        captured["body"] = req.data
        return FakeResp()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    import tempfile

    from conftest import make_nebo

    with tempfile.TemporaryDirectory() as td:
        p = make_nebo(
            Path(td) / "x.nebo",
            [("pg000001", [([1.0, 2.0], [3.0, 4.0], None)], None)],
        )
        res = rec.recognize(load_nebo(p), "en_US")
    expected = hmac_mod.new(b"APPSECRET", captured["body"], hashlib.sha512).hexdigest()
    assert captured["hmac"] == expected
    assert "/api/v4.0/iink/recognize/" in captured["url"]
    assert res.pages[0].text == "ciao"


def test_jiix_text_extraction():
    jiix = {
        "type": "Text",
        "children": [
            {"type": "TextLine", "label": "line one",
             "words": [{"label": "line"}, {"label": "one"}]},
            {"type": "TextLine", "label": "line two"},
        ],
    }
    text = _jiix_text(jiix)
    assert "line one" in text and "line two" in text


def test_google_body(monkeypatch, sample_nebo: Path):
    monkeypatch.setenv("GOOGLE_VISION_API_KEY", "KEY123")
    from nebo_ocr.backends.google_vision import GoogleVisionRecognizer

    captured = {}

    def fake_post(url, payload, headers, timeout=0):
        captured["url"] = url
        captured["payload"] = payload
        return {"responses": [{"fullTextAnnotation": {"text": "hi there"}}]}

    monkeypatch.setattr(
        "nebo_ocr.backends.google_vision.post_json", fake_post
    )
    res = GoogleVisionRecognizer().recognize(load_nebo(sample_nebo), "en_US")
    assert captured["url"].endswith("key=KEY123")
    req = captured["payload"]["requests"][0]
    assert req["features"] == [{"type": "DOCUMENT_TEXT_DETECTION"}]
    assert req["imageContext"]["languageHints"] == ["en-US"]
    assert res.pages[0].text == "hi there"


def test_mathpix_payload(monkeypatch, sample_nebo: Path):
    monkeypatch.setenv("MATHPIX_APP_ID", "ID")
    monkeypatch.setenv("MATHPIX_APP_KEY", "KEY")
    from nebo_ocr.backends.mathpix import MathpixRecognizer

    captured = {}

    def fake_post(url, payload, headers, timeout=0):
        captured.update(payload=payload, headers=headers)
        return {"text": "recognized"}

    monkeypatch.setattr("nebo_ocr.backends.mathpix.post_json", fake_post)
    res = MathpixRecognizer().recognize(load_nebo(sample_nebo), "it_IT")
    assert captured["headers"]["app_id"] == "ID"
    assert captured["payload"]["languages"] == ["it"]
    assert res.pages[0].text == "recognized"


def test_available_backends_shape():
    report = available_backends()
    assert len(report) == 9
    by_name = {n: (ok, why) for n, ok, why in report}
    assert by_name["embedded"][0] is True
    for name in ("surya", "easyocr", "paddleocr", "trocr"):
        _ok, why = by_name[name]
        assert isinstance(why, str)


def test_language_fallback_to_document(sample_nebo: Path):
    # file declares en_US; passing no lang -> embedded reports en_US
    res = recognize(sample_nebo, backend="embedded")
    assert res.language == "en_US"
    # explicit override wins
    res = recognize(sample_nebo, backend="embedded", language="it")
    assert res.language == "it_IT"
