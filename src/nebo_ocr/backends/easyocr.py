"""EasyOCR backend — local, ~80 languages.

Install: ``pip install nebo-ocr[easyocr]``
"""
from __future__ import annotations

import importlib.util
from typing import Any, ClassVar

from ..languages import to_backend_code
from ..model import Notebook
from ..render import RenderOptions, render_page
from .base import BackendUnavailable, RecognitionResult, RecognizedLine, RecognizedPage


class EasyOcrRecognizer:
    name = "easyocr"
    description = "EasyOCR (local, ~80 languages)"
    needs_api_key = False
    local = True
    _readers: ClassVar[dict[tuple[str, ...], Any]] = {}

    def available(self) -> tuple[bool, str]:
        if importlib.util.find_spec("easyocr") is None:
            return False, "pip install nebo-ocr[easyocr]"
        return True, ""

    def _reader(self, langs: list[str]) -> Any:
        key = tuple(sorted(langs))
        if key not in self._readers:
            import easyocr

            self._readers[key] = easyocr.Reader(list(key))
        return self._readers[key]

    def recognize(self, notebook: Notebook, language: str | None = None) -> RecognitionResult:
        ok, why = self.available()
        if not ok:
            raise BackendUnavailable(why)
        lang = language or notebook.language
        code = to_backend_code(lang, self.name)
        if lang and code is None:
            raise BackendUnavailable(f"easyocr does not support {lang!r}")
        import numpy as np

        reader = self._reader([code or "en", "en"])

        pages: list[RecognizedPage] = []
        for page in notebook.pages:
            if not page.strokes:
                pages.append(RecognizedPage(page_id=page.page_id, text=""))
                continue
            img = np.asarray(render_page(page, RenderOptions(dpi=200)))
            detections = reader.readtext(img, detail=1, paragraph=False)
            lines = [
                RecognizedLine(text=text, confidence=float(conf))
                for _box, text, conf in detections
            ]
            pages.append(
                RecognizedPage(
                    page_id=page.page_id,
                    text="\n".join(ln.text for ln in lines),
                    lines=lines,
                )
            )
        return RecognitionResult(backend=self.name, language=code, pages=pages)
