"""Shared raster helpers: notebook page/line -> PNG bytes."""
from __future__ import annotations

import io

from ..model import Page
from ..render import RenderOptions, render_lines, render_page


def page_png(page: Page, dpi: float = 200.0) -> bytes:
    img = render_page(page, RenderOptions(dpi=dpi))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def line_pngs(
    page: Page, dpi: float = 200.0
) -> list[tuple[tuple[float, float, float, float], bytes]]:
    """Per-text-line PNGs with their mm bounding boxes."""
    out = []
    for line, img in render_lines(page, RenderOptions(dpi=dpi)):
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        out.append((line.bounds(), buf.getvalue()))
    return out
