"""Embedded recognizer — extract text MyScript already stored in the file.

When Nebo runs recognition on a page it persists the result inside the
``ink.bink`` tag table: ``DIAGRAM`` records carry a JSON payload whose
``DWLabel`` field is the recognized text for that block. This backend simply
harvests those labels — fully offline, works for every language Nebo itself
supports, zero dependencies.
"""
from __future__ import annotations

from ..model import Notebook
from .base import RecognitionResult, RecognizedLine, RecognizedPage


class EmbeddedRecognizer:
    name = "embedded"
    description = (
        "Text already recognized by MyScript inside the .nebo file "
        "(DIAGRAM/DWLabel tags) — offline, language-agnostic"
    )
    needs_api_key = False
    local = True

    def available(self) -> tuple[bool, str]:
        return True, ""

    def recognize(self, notebook: Notebook, language: str | None = None) -> RecognitionResult:
        pages: list[RecognizedPage] = []
        for page in notebook.pages:
            labels = page.diagram_labels()
            lines = [RecognizedLine(text=lbl) for lbl in labels]
            pages.append(
                RecognizedPage(page_id=page.page_id, text="\n".join(labels), lines=lines)
            )
        return RecognitionResult(
            backend=self.name,
            language=language or notebook.language,
            pages=pages,
        )
