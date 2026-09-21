"""High-level recognition orchestration."""
from __future__ import annotations

from pathlib import Path

from .backends import get_backend
from .backends.base import RecognitionResult
from .languages import normalize_locale
from .model import Notebook
from .nebo import load_nebo


def recognize(
    source: Notebook | str | Path,
    backend: str = "embedded",
    language: str | None = None,
) -> RecognitionResult:
    """Recognize a .nebo notebook with the chosen backend.

    ``language`` accepts any spelling (``it_IT``, ``it-IT``, ``it``,
    ``italian``); it is normalized and mapped onto the backend's own code.
    When omitted, the document's ``languageLocaleIdentifier`` is used.
    """
    notebook = load_nebo(source) if not isinstance(source, Notebook) else source
    lang = normalize_locale(language) if language else None
    return get_backend(backend).recognize(notebook, lang)
