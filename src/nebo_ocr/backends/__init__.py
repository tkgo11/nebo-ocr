"""Recognition backend registry."""
from __future__ import annotations

from .azure_vision import AzureVisionRecognizer
from .base import BackendUnavailable, RecognitionResult, Recognizer
from .easyocr import EasyOcrRecognizer
from .embedded import EmbeddedRecognizer
from .google_vision import GoogleVisionRecognizer
from .mathpix import MathpixRecognizer
from .myscript import MyScriptCloudRecognizer
from .paddleocr import PaddleOcrRecognizer
from .surya import SuryaRecognizer
from .trocr import TrOcrRecognizer

__all__ = [
    "BackendUnavailable",
    "RecognitionResult",
    "Recognizer",
    "available_backends",
    "get_backend",
    "registry",
]

_RECOGNIZERS: list[Recognizer] = [
    EmbeddedRecognizer(),
    MyScriptCloudRecognizer(),
    GoogleVisionRecognizer(),
    AzureVisionRecognizer(),
    MathpixRecognizer(),
    SuryaRecognizer(),
    EasyOcrRecognizer(),
    PaddleOcrRecognizer(),
    TrOcrRecognizer(),
]
_INSTANCES: dict[str, Recognizer] = {r.name: r for r in _RECOGNIZERS}


def registry() -> dict[str, Recognizer]:
    """All backends, keyed by name."""
    return dict(_INSTANCES)


def get_backend(name: str) -> Recognizer:
    try:
        return _INSTANCES[name]
    except KeyError:
        raise BackendUnavailable(
            f"unknown backend {name!r}; choices: {', '.join(sorted(_INSTANCES))}"
        ) from None


def available_backends() -> list[tuple[str, bool, str]]:
    """(name, ready, reason-if-not) for every registered backend."""
    return [(r.name, *r.available()) for r in _INSTANCES.values()]
