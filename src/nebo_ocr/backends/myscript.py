"""MyScript iink Cloud backend — recognize the raw strokes with the same
engine Nebo uses, in ~72 languages.

Credentials (register at https://developer.myscript.com/):
    MYSCRIPT_APPLICATION_KEY   - sent in the `applicationKey` header
    MYSCRIPT_HMAC_KEY          - HMAC-SHA512(request body, appKey + hmacKey)
    MYSCRIPT_HOST              - optional, default https://cloud.myscript.com
    MYSCRIPT_ENDPOINT          - "recognize" (default) or "batch"

Strokes are sent as mm coordinates (``scaleX/scaleY = 1``); timestamps are
rebuilt from each stroke's capture time when present.
"""
from __future__ import annotations

import hashlib
import hmac as hmac_mod
import json
import os
import urllib.request
from typing import Any

from ..languages import to_backend_code
from ..model import Notebook, Page, Stroke
from .base import BackendUnavailable, RecognitionResult, RecognizedLine, RecognizedPage

DEFAULT_HOST = "https://cloud.myscript.com"


def _stroke_to_api(stroke: Stroke, idx: int) -> dict[str, Any]:
    d: dict[str, Any] = {
        "id": f"s{idx}",
        "x": [round(p.x, 4) for p in stroke.points],
        "y": [round(p.y, 4) for p in stroke.points],
    }
    if any(p.t is not None for p in stroke.points):
        d["t"] = [int(p.t or 0) for p in stroke.points]
    if any(p.force < 1.0 for p in stroke.points):
        d["p"] = [max(0.01, min(0.99, p.force)) for p in stroke.points]
    return d


def _recognize_body(page: Page, lang: str | None) -> dict[str, Any]:
    strokes = [
        _stroke_to_api(s, i) for i, s in enumerate(page.strokes) if len(s.points) > 1
    ]
    config: dict[str, Any] = {}
    if lang:
        config["lang"] = lang
    config["export"] = {"jiix": {"strokes": False, "bounding-box": False,
                                 "text": {"chars": False, "words": True}}}
    return {
        "scaleX": 1.0,
        "scaleY": 1.0,
        "contentType": "Text",
        "configuration": config,
        "strokes": strokes,
    }


def _batch_body(page: Page, lang: str | None, dpi: int = 96) -> dict[str, Any]:
    k = dpi / 25.4
    strokes = [
        {
            "x": [round(p.x * k, 2) for p in s.points],
            "y": [round(p.y * k, 2) for p in s.points],
        }
        for s in page.strokes
        if len(s.points) > 1
    ]
    x0, y0, x1, y1 = page.extent
    body: dict[str, Any] = {
        "xDPI": dpi,
        "yDPI": dpi,
        "width": round((x1 - x0) * k),
        "height": round((y1 - y0) * k),
        "contentType": "Text",
        "strokeGroups": [{"strokes": strokes}],
    }
    if lang:
        body["configuration"] = {"lang": lang}
    return body


def _jiix_text(node: Any) -> str:
    """Pull plain text out of a JIIX export tree."""
    out: list[str] = []
    if isinstance(node, dict):
        label = node.get("label")
        if isinstance(label, str) and node.get("type") in (
            "Text", "TextLine", "Word", "Paragraph", "Text Document",
        ):
            out.append(label)
        for key in ("children", "elements", "words", "items", "candidates"):
            for child in node.get(key, []) or []:
                out.append(_jiix_text(child))
    elif isinstance(node, list):
        for item in node:
            out.append(_jiix_text(item))
    return "\n".join(t for t in out if t)


class MyScriptCloudRecognizer:
    name = "myscript"
    description = "MyScript iink Cloud REST API — ~72 languages, the same engine as Nebo"
    needs_api_key = True
    local = False

    def _keys(self) -> tuple[str, str]:
        app = os.environ.get("MYSCRIPT_APPLICATION_KEY", "")
        hmac_key = os.environ.get("MYSCRIPT_HMAC_KEY", "")
        return app, hmac_key

    def available(self) -> tuple[bool, str]:
        app, hmac_key = self._keys()
        if not app or not hmac_key:
            return False, "set MYSCRIPT_APPLICATION_KEY and MYSCRIPT_HMAC_KEY"
        return True, ""

    def _post(self, body: bytes, endpoint: str, accept: str) -> bytes:
        app, hmac_key = self._keys()
        host = os.environ.get("MYSCRIPT_HOST", DEFAULT_HOST).rstrip("/")
        sig = hmac_mod.new(
            (app + hmac_key).encode(), body, hashlib.sha512
        ).hexdigest()
        req = urllib.request.Request(
            f"{host}/api/v4.0/iink/{endpoint}/",
            data=body,
            headers={
                "applicationKey": app,
                "hmac": sig,
                "Content-Type": "application/json",
                "Accept": f"{accept}, application.json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data: bytes = resp.read()
                return data
        except urllib.error.HTTPError as exc:  # pragma: no cover - network
            detail = exc.read().decode("utf-8", "replace")[:500]
            raise BackendUnavailable(
                f"MyScript API error {exc.code}: {detail}"
            ) from exc
        except OSError as exc:  # pragma: no cover - network
            raise BackendUnavailable(f"MyScript API unreachable: {exc}") from exc

    def _recognize_page(self, page: Page, lang: str | None, endpoint: str) -> RecognizedPage:
        body = (
            _batch_body(page, lang) if endpoint == "batch" else _recognize_body(page, lang)
        )
        raw = self._post(
            json.dumps(body).encode(), endpoint, "application/vnd.myscript.jiix"
        )
        try:
            jiix = json.loads(raw)
        except json.JSONDecodeError:
            return RecognizedPage(page_id=page.page_id, text=raw.decode("utf-8", "replace"))
        text = _jiix_text(jiix)
        lines = [RecognizedLine(text=t) for t in text.splitlines() if t.strip()]
        return RecognizedPage(page_id=page.page_id, text=text, lines=lines)

    def recognize(self, notebook: Notebook, language: str | None = None) -> RecognitionResult:
        ok, why = self.available()
        if not ok:
            raise BackendUnavailable(why)
        lang = language or notebook.language
        code = to_backend_code(lang, self.name)
        if lang and code is None:
            raise BackendUnavailable(f"myscript does not support {lang!r}")
        endpoint = os.environ.get("MYSCRIPT_ENDPOINT", "recognize")
        pages = [self._recognize_page(p, code, endpoint) for p in notebook.pages]
        return RecognitionResult(backend=self.name, language=code, pages=pages)
