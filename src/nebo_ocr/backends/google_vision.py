"""Google Cloud Vision backend — DOCUMENT_TEXT_DETECTION on rendered pages.

Auth (either):
    GOOGLE_VISION_API_KEY     - API key appended as ?key=
    GOOGLE_ACCESS_TOKEN       - OAuth2 Bearer token
    GOOGLE_APPLICATION_CREDENTIALS is honored indirectly if you mint a token
    yourself; this client deliberately avoids the heavy google-cloud SDK.

Language hints are BCP-47 (``en-US``, ``zh-TW``).
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

URL = "https://vision.googleapis.com/v1/images:annotate"


class GoogleVisionRecognizer:
    name = "google"
    description = "Google Cloud Vision DOCUMENT_TEXT_DETECTION — broad language coverage"
    needs_api_key = True
    local = False

    def available(self) -> tuple[bool, str]:
        if not (
            os.environ.get("GOOGLE_VISION_API_KEY")
            or os.environ.get("GOOGLE_ACCESS_TOKEN")
        ):
            return False, "set GOOGLE_VISION_API_KEY or GOOGLE_ACCESS_TOKEN"
        return True, ""

    def _annotate(self, png: bytes, hint: str | None) -> dict[str, Any]:
        image_context = {"languageHints": [hint]} if hint else {}
        payload = {
            "requests": [
                {
                    "image": {"content": base64.b64encode(png).decode()},
                    "features": [{"type": "DOCUMENT_TEXT_DETECTION"}],
                    "imageContext": image_context,
                }
            ]
        }
        headers: dict[str, str] = {}
        url = URL
        if key := os.environ.get("GOOGLE_VISION_API_KEY"):
            url = f"{URL}?key={key}"
        else:
            headers["Authorization"] = f"Bearer {os.environ['GOOGLE_ACCESS_TOKEN']}"
        data = post_json(url, payload, headers)
        result: dict[str, Any] = data["responses"][0]
        return result

    def recognize(self, notebook: Notebook, language: str | None = None) -> RecognitionResult:
        ok, why = self.available()
        if not ok:
            raise BackendUnavailable(why)
        lang = language or notebook.language
        hint = to_backend_code(lang, self.name)
        if lang and hint is None:
            raise BackendUnavailable(f"google vision does not support {lang!r}")
        pages: list[RecognizedPage] = []
        for page in notebook.pages:
            if not page.strokes:
                pages.append(RecognizedPage(page_id=page.page_id, text=""))
                continue
            resp = self._annotate(page_png(page), hint)
            if "error" in resp:
                raise BackendUnavailable(f"google vision: {resp['error']}")
            fta = resp.get("fullTextAnnotation", {})
            lines = [
                RecognizedLine(text=t)
                for t in fta.get("text", "").splitlines()
                if t.strip()
            ]
            pages.append(
                RecognizedPage(page_id=page.page_id, text=fta.get("text", ""), lines=lines)
            )
        return RecognitionResult(backend=self.name, language=hint, pages=pages)
