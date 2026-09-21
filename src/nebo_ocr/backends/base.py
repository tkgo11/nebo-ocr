"""Recognition backend interface."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from ..model import Notebook


@dataclass
class RecognizedLine:
    text: str
    confidence: float | None = None
    bounds_mm: tuple[float, float, float, float] | None = None


@dataclass
class RecognizedPage:
    page_id: str
    text: str
    lines: list[RecognizedLine] = field(default_factory=list)


@dataclass
class RecognitionResult:
    backend: str
    language: str | None
    pages: list[RecognizedPage]

    @property
    def text(self) -> str:
        return "\n\n".join(p.text for p in self.pages if p.text)


class BackendUnavailable(RuntimeError):
    """Raised when a backend can't run (missing keys, packages, network)."""


class Recognizer(Protocol):
    """A handwriting-recognition backend.

    ``recognize`` takes a parsed Notebook and returns per-page text.
    Implementations must be importable without optional third-party
    packages installed — import them lazily inside ``recognize``.
    """

    name: str
    description: str
    needs_api_key: bool
    local: bool

    def available(self) -> tuple[bool, str]:
        """(ready, human-readable reason if not)."""
        ...

    def recognize(self, notebook: Notebook, language: str | None = None) -> RecognitionResult:
        ...
