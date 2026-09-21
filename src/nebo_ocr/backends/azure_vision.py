"""Azure AI Vision Read backend — strong handwriting OCR across many languages.

Auth:
    AZURE_VISION_ENDPOINT   - e.g. https://<resource>.cognitiveservices.azure.com
    AZURE_VISION_KEY        - Ocp-Apim-Subscription-Key

Uses the Read API: POST /vision/v3.2/read/analyze then poll the
Operation-Location URL until the analysis succeeds.
"""
from __future__ import annotations

import os
import time
import urllib.request
from typing import Any

from ..languages import to_backend_code
from ..model import Notebook
from ._http import get_json
from ._images import page_png
from .base import BackendUnavailable, RecognitionResult, RecognizedLine, RecognizedPage


class AzureVisionRecognizer:
    name = "azure"
    description = "Azure AI Vision Read API — 30+ handwriting languages"
    needs_api_key = True
    local = False

    def available(self) -> tuple[bool, str]:
        if not (
            os.environ.get("AZURE_VISION_ENDPOINT") and os.environ.get("AZURE_VISION_KEY")
        ):
            return False, "set AZURE_VISION_ENDPOINT and AZURE_VISION_KEY"
        return True, ""

    def _analyze(self, png: bytes, lang: str | None) -> dict[str, Any]:
        endpoint = os.environ["AZURE_VISION_ENDPOINT"].rstrip("/")
        headers = {"Ocp-Apim-Subscription-Key": os.environ["AZURE_VISION_KEY"]}
        url = f"{endpoint}/vision/v3.2/read/analyze"
        if lang:
            url += f"?language={lang}"
        req = urllib.request.Request(
            url, data=png, headers={"Content-Type": "application/octet-stream", **headers}
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                op = resp.headers["Operation-Location"]
        except urllib.error.HTTPError as exc:  # pragma: no cover - network
            raise BackendUnavailable(
                f"azure vision {exc.code}: {exc.read().decode('utf-8', 'replace')[:300]}"
            ) from exc
        except OSError as exc:  # pragma: no cover - network
            raise BackendUnavailable(f"azure vision unreachable: {exc}") from exc

        for _ in range(30):
            time.sleep(1)
            data: dict[str, Any] = get_json(op, headers)
            status = data.get("status")
            if status == "succeeded":
                return data
            if status == "failed":
                raise BackendUnavailable(f"azure vision analysis failed: {data}")
        raise BackendUnavailable("azure vision analysis timed out")

    def recognize(self, notebook: Notebook, language: str | None = None) -> RecognitionResult:
        ok, why = self.available()
        if not ok:
            raise BackendUnavailable(why)
        lang = language or notebook.language
        code = to_backend_code(lang, self.name)
        if lang and code is None:
            raise BackendUnavailable(f"azure vision does not support {lang!r}")
        pages: list[RecognizedPage] = []
        for page in notebook.pages:
            if not page.strokes:
                pages.append(RecognizedPage(page_id=page.page_id, text=""))
                continue
            data = self._analyze(page_png(page), code)
            lines: list[RecognizedLine] = []
            texts: list[str] = []
            for result in data.get("analyzeResult", {}).get("readResults", []):
                for ln in result.get("lines", []):
                    lines.append(RecognizedLine(text=ln.get("text", "")))
                    texts.append(ln.get("text", ""))
            pages.append(
                RecognizedPage(page_id=page.page_id, text="\n".join(texts), lines=lines)
            )
        return RecognitionResult(backend=self.name, language=code, pages=pages)
