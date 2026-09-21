"""nebo-ocr — handwriting recognition for MyScript Nebo .nebo files.

Parse the BINK ink inside .nebo exports and recognize it with embedded
MyScript labels, cloud APIs (MyScript iink, Google Vision, Azure Read,
Mathpix) or local OCR (Surya, EasyOCR, PaddleOCR, TrOCR) across 100+ locales.
"""
from .backends import available_backends, get_backend, registry
from .backends.base import (
    BackendUnavailable,
    RecognitionResult,
    RecognizedLine,
    RecognizedPage,
)
from .languages import (
    backends_for_language,
    language_name,
    normalize_locale,
    supported_languages,
)
from .model import Notebook, Page, Point, Stroke, Tag, TextLine
from .nebo import is_nebo_file, load_nebo
from .recognize import recognize
from .render import RenderOptions, page_to_svg, render_lines, render_page, strokes_to_lines

__version__ = "0.1.0"

__all__ = [
    "BackendUnavailable",
    "Notebook",
    "Page",
    "Point",
    "RecognitionResult",
    "RecognizedLine",
    "RecognizedPage",
    "RenderOptions",
    "Stroke",
    "Tag",
    "TextLine",
    "available_backends",
    "backends_for_language",
    "get_backend",
    "is_nebo_file",
    "language_name",
    "load_nebo",
    "normalize_locale",
    "page_to_svg",
    "recognize",
    "registry",
    "render_lines",
    "render_page",
    "strokes_to_lines",
    "supported_languages",
]
