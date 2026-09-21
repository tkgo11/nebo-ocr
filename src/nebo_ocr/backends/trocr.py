"""TrOCR backend — Microsoft's transformer OCR running locally.

English-only handwritten model (``microsoft/trocr-base-handwritten``); works
line-by-line on the detected text lines. Install:
``pip install nebo-ocr[trocr]``
"""
from __future__ import annotations

import importlib.util
from typing import Any

from ..languages import to_backend_code
from ..model import Notebook
from ..render import RenderOptions, render_lines
from .base import BackendUnavailable, RecognitionResult, RecognizedLine, RecognizedPage

MODEL_ID = "microsoft/trocr-base-handwritten"


class TrOcrRecognizer:
    name = "trocr"
    description = "TrOCR handwritten (local, English only, line-level)"
    needs_api_key = False
    local = True
    _pipe = None

    def available(self) -> tuple[bool, str]:
        if importlib.util.find_spec("transformers") is None:
            return False, "pip install nebo-ocr[trocr]"
        return True, ""

    def _load(self) -> Any:
        if self._pipe is None:
            from transformers import TrOCRProcessor, VisionEncoderDecoderModel

            processor = TrOCRProcessor.from_pretrained(MODEL_ID)
            model = VisionEncoderDecoderModel.from_pretrained(MODEL_ID)
            TrOcrRecognizer._pipe = (processor, model)
        return self._pipe

    def recognize(self, notebook: Notebook, language: str | None = None) -> RecognitionResult:
        ok, why = self.available()
        if not ok:
            raise BackendUnavailable(why)
        lang = language or notebook.language
        code = to_backend_code(lang, self.name)
        if lang and code is None:
            raise BackendUnavailable(f"trocr does not support {lang!r}")
        processor, model = self._load()

        pages: list[RecognizedPage] = []
        for page in notebook.pages:
            lines: list[RecognizedLine] = []
            for ln, img in render_lines(page, RenderOptions(dpi=200)):
                pixel = processor(images=img, return_tensors="pt").pixel_values
                ids = model.generate(pixel)
                text = processor.batch_decode(ids, skip_special_tokens=True)[0]
                lines.append(
                    RecognizedLine(text=text.strip(), bounds_mm=ln.bounds())
                )
            pages.append(
                RecognizedPage(
                    page_id=page.page_id,
                    text="\n".join(ln.text for ln in lines if ln.text),
                    lines=lines,
                )
            )
        return RecognitionResult(backend=self.name, language=code, pages=pages)
