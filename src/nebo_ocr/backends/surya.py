"""Surya OCR backend — local transformer OCR covering ~90 languages.

Install: ``pip install nebo-ocr[surya]``
"""
from __future__ import annotations

import importlib.util
from typing import Any

from ..languages import to_backend_code
from ..model import Notebook
from ..render import RenderOptions, render_page
from .base import BackendUnavailable, RecognitionResult, RecognizedLine, RecognizedPage


class SuryaRecognizer:
    name = "surya"
    description = "Surya OCR (local, ~90 languages, transformer-based)"
    needs_api_key = False
    local = True
    _predictor = None

    def available(self) -> tuple[bool, str]:
        if importlib.util.find_spec("surya") is None:
            return False, "pip install nebo-ocr[surya]"
        return True, ""

    def _load(self) -> Any:
        if self._predictor is None:
            from surya.recognition import RecognitionPredictor

            SuryaRecognizer._predictor = RecognitionPredictor()
        return self._predictor

    def recognize(self, notebook: Notebook, language: str | None = None) -> RecognitionResult:
        ok, why = self.available()
        if not ok:
            raise BackendUnavailable(why)
        lang = language or notebook.language
        code = to_backend_code(lang, self.name)
        if lang and code is None:
            raise BackendUnavailable(f"surya does not support {lang!r}")
        predictor = self._load()

        images = [render_page(p, RenderOptions(dpi=200)) for p in notebook.pages]
        langs = [[code] if code else None for _ in images]
        try:
            results = predictor(images, langs)
        except TypeError:  # older surya API without per-image langs
            results = predictor(images)

        pages: list[RecognizedPage] = []
        for page, res in zip(notebook.pages, results, strict=True):
            lines = [
                RecognizedLine(
                    text=getattr(tl, "text", ""),
                    confidence=getattr(tl, "confidence", None),
                )
                for tl in getattr(res, "text_lines", [])
            ]
            pages.append(
                RecognizedPage(
                    page_id=page.page_id,
                    text="\n".join(ln.text for ln in lines if ln.text),
                    lines=lines,
                )
            )
        return RecognitionResult(backend=self.name, language=code, pages=pages)
