"""Mathpix backend — excellent on handwriting mixed with math.

Auth:
    MATHPIX_APP_ID
    MATHPIX_APP_KEY
"""
from __future__ import annotations

import base64
import os
from typing import Any

from ..languages import to_backend_code
from ..model import Notebook
from ._http import post_json
from ._images import page_png
from .base import BackendUnavailable, RecognitionResult, RecognizedLine, RecognizedPage

URL = "https://api.mathpix.com/v3/text"


class MathpixRecognizer:
    name = "mathpix"
    description = "Mathpix OCR — handwriting + math, 60+ languages"
    needs_api_key = True
    local = False

    def available(self) -> tuple[bool, str]:
        if not (os.environ.get("MATHPIX_APP_ID") and os.environ.get("MATHPIX_APP_KEY")):
            return False, "set MATHPIX_APP_ID and MATHPIX_APP_KEY"
        return True, ""

    def recognize(self, notebook: Notebook, language: str | None = None) -> RecognitionResult:
        ok, why = self.available()
        if not ok:
            raise BackendUnavailable(why)
        lang = language or notebook.language
        code = to_backend_code(lang, self.name)
        if lang and code is None:
            raise BackendUnavailable(f"mathpix does not support {lang!r}")
        headers = {
            "app_id": os.environ["MATHPIX_APP_ID"],
            "app_key": os.environ["MATHPIX_APP_KEY"],
        }
        pages: list[RecognizedPage] = []
        for page in notebook.pages:
            if not page.strokes:
                pages.append(RecognizedPage(page_id=page.page_id, text=""))
                continue
            payload: dict[str, Any] = {
                "src": "data:image/png;base64," + base64.b64encode(page_png(page)).decode(),
                "formats": ["text"],
            }
            if code:
                payload["languages"] = [code]
            data = post_json(URL, payload, headers)
            if data.get("error"):
                raise BackendUnavailable(f"mathpix: {data['error']}")
            text = data.get("text", "")
            lines = [RecognizedLine(text=t) for t in text.splitlines() if t.strip()]
            pages.append(RecognizedPage(page_id=page.page_id, text=text, lines=lines))
        return RecognitionResult(backend=self.name, language=code, pages=pages)
