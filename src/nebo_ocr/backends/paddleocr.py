"""PaddleOCR backend — local, ~80 languages via script-family models.

Install: ``pip install nebo-ocr[paddleocr]``
"""
from __future__ import annotations

import importlib.util
from typing import Any, ClassVar

from ..languages import to_backend_code
from ..model import Notebook
from ..render import RenderOptions, render_page
from .base import BackendUnavailable, RecognitionResult, RecognizedLine, RecognizedPage


class PaddleOcrRecognizer:
    name = "paddleocr"
    description = "PaddleOCR (local, ~80 languages incl. CJK, Cyrillic, Arabic, Indic)"
    needs_api_key = False
    local = True
    _engines: ClassVar[dict[str, Any]] = {}

    def available(self) -> tuple[bool, str]:
        if importlib.util.find_spec("paddleocr") is None:
            return False, "pip install nebo-ocr[paddleocr]"
        return True, ""

    def _engine(self, lang: str) -> Any:
        if lang not in self._engines:
            from paddleocr import PaddleOCR

            self._engines[lang] = PaddleOCR(lang=lang, use_angle_cls=False,
                                          show_log=False)
        return self._engines[lang]

    def recognize(self, notebook: Notebook, language: str | None = None) -> RecognitionResult:
        ok, why = self.available()
        if not ok:
            raise BackendUnavailable(why)
        lang = language or notebook.language
        code = to_backend_code(lang, self.name)
        if lang and code is None:
            raise BackendUnavailable(f"paddleocr does not support {lang!r}")
        import numpy as np

        engine = self._engine(code or "en")

        pages: list[RecognizedPage] = []
        for page in notebook.pages:
            if not page.strokes:
                pages.append(RecognizedPage(page_id=page.page_id, text=""))
                continue
            img = np.asarray(render_page(page, RenderOptions(dpi=200)))
            result = engine.ocr(img, cls=False)
            lines: list[RecognizedLine] = []
            for block in result or []:
                for entry in block or []:
                    try:
                        text, conf = entry[1]
                        lines.append(
                            RecognizedLine(text=str(text), confidence=float(conf))
                        )
                    except (TypeError, ValueError, IndexError):
                        continue
            pages.append(
                RecognizedPage(
                    page_id=page.page_id,
                    text="\n".join(ln.text for ln in lines),
                    lines=lines,
                )
            )
        return RecognitionResult(backend=self.name, language=code, pages=pages)
