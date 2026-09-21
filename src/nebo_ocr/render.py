"""Render parsed ink to raster images (for image-based OCR backends) or SVG.

Coordinates are mm; rendering scales them to pixels via a DPI factor and
draws each stroke as a jointed polyline with round caps — a deliberately
plain "digital pen" look that OCR engines handle well.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from PIL import Image, ImageDraw

from .model import Page, Point, Stroke, TextLine

MM_PER_INCH = 25.4


def strokes_to_lines(page: Page) -> list[TextLine]:
    """Group a page's strokes into text lines.

    Prefers the engine's own TEXT_LINE tag spans; falls back to geometric
    clustering (sort strokes by vertical midpoint, break when the y-gap
    exceeds a fraction of the median stroke height).
    """
    line_groups: list[list[int]] = []
    seen: set[int] = set()
    for tag in page.tags:
        if tag.name != "TEXT_LINE":
            continue
        for first, last, _, _ in tag.groups:
            recs = [
                s.record_index
                for s in page.strokes
                if first <= s.record_index <= last
            ]
            recs = [r for r in recs if r not in seen]
            if recs:
                seen.update(recs)
                line_groups.append(recs)
    leftover = [s for s in page.strokes if s.record_index not in seen]

    lines: list[TextLine] = []
    for recs in line_groups:
        strokes = [s for s in page.strokes if s.record_index in recs]
        if strokes:
            lines.append(TextLine(strokes=strokes))
    if leftover:
        lines.extend(_geometric_lines(leftover))
    lines.sort(key=lambda ln: ln.bounds()[1])
    return lines


def _geometric_lines(strokes: list[Stroke]) -> list[TextLine]:
    if not strokes:
        return []
    ordered = sorted(strokes, key=lambda s: (s.bounds()[1] + s.bounds()[3]) / 2)
    heights = sorted(s.bounds()[3] - s.bounds()[1] for s in ordered)
    median_h = heights[len(heights) // 2] or 5.0
    gap = max(median_h * 0.8, 3.0)

    lines: list[TextLine] = []
    current: list[Stroke] = []
    current_bottom = -math.inf
    for s in ordered:
        top = s.bounds()[1]
        if current and top - current_bottom > gap:
            lines.append(TextLine(strokes=current))
            current = []
        current.append(s)
        current_bottom = max(current_bottom, s.bounds()[3])
    if current:
        lines.append(TextLine(strokes=current))
    return lines


@dataclass
class RenderOptions:
    dpi: float = 150.0
    margin_mm: float = 8.0
    pen_width_mm: float = 0.35  # default when the brush class is unknown
    foreground: str = "#000000"
    background: str = "#ffffff"
    crop_to_content: bool = True


def _stroke_color(stroke: Stroke, default: str) -> str:
    return stroke.color or default


def render_strokes(
    strokes: list[Stroke],
    options: RenderOptions | None = None,
    canvas_mm: tuple[float, float] | None = None,
) -> Image.Image:
    """Rasterize strokes into a PIL image sized to their bounding box."""
    opts = options or RenderOptions()
    px_per_mm = opts.dpi / MM_PER_INCH
    if not strokes:
        return Image.new("RGB", (64, 64), opts.background)

    x0 = min(s.bounds()[0] for s in strokes)
    y0 = min(s.bounds()[1] for s in strokes)
    x1 = max(s.bounds()[2] for s in strokes)
    y1 = max(s.bounds()[3] for s in strokes)
    if canvas_mm is not None:
        w_mm, h_mm = canvas_mm
    elif opts.crop_to_content:
        w_mm, h_mm = x1 - x0, y1 - y0
    else:
        w_mm, h_mm = x1, y1

    m = opts.margin_mm
    width_px = max(1, round((w_mm + 2 * m) * px_per_mm))
    height_px = max(1, round((h_mm + 2 * m) * px_per_mm))
    img = Image.new("RGB", (width_px, height_px), opts.background)
    draw = ImageDraw.Draw(img, "RGBA")

    origin_x = x0 if opts.crop_to_content or canvas_mm is None else 0.0
    origin_y = y0 if opts.crop_to_content or canvas_mm is None else 0.0
    for s in strokes:
        pts = [
            ((p.x - origin_x + m) * px_per_mm, (p.y - origin_y + m) * px_per_mm)
            for p in s.points
        ]
        if len(pts) < 2:
            continue
        w = max(1, round((s.width_mm or opts.pen_width_mm) * px_per_mm))
        color = _stroke_color(s, opts.foreground)
        if s.highlighter:
            draw.line(pts, fill=color + "66" if len(color) == 7 else color,
                      width=max(w, round(4 * px_per_mm)), joint="curve")
        else:
            draw.line(pts, fill=color, width=w, joint="curve")
            r = w / 2
            for px, py in pts:
                draw.ellipse((px - r, py - r, px + r, py + r), fill=color)
    return img


def render_page(page: Page, options: RenderOptions | None = None) -> Image.Image:
    """Render a full page at its declared extent."""
    opts = options or RenderOptions()
    if opts.crop_to_content:
        return render_strokes(page.strokes, opts)
    x0, y0, x1, y1 = page.extent
    canvas_mm = (x1 - x0, y1 - y0)
    # keep absolute page coordinates: offset by extent origin
    shifted = [
        Stroke(
            points=[Point(p.x - x0, p.y - y0, p.force, p.t) for p in s.points],
            record_index=s.record_index,
            pen=s.pen,
            color=s.color,
            width_mm=s.width_mm,
            highlighter=s.highlighter,
        )
        for s in page.strokes
    ]
    return render_strokes(shifted, opts, canvas_mm=canvas_mm)


def render_lines(
    page: Page, options: RenderOptions | None = None
) -> list[tuple[TextLine, Image.Image]]:
    """Render each detected text line separately — useful for line-level OCR."""
    return [(ln, render_strokes(ln.strokes, options)) for ln in strokes_to_lines(page)]


def page_to_svg(page: Page, pen_width_mm: float = 0.35) -> str:
    """Export the page's ink as a standalone SVG (mm units, y down)."""
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{page.extent[0]} {page.extent[1]} '
        f'{page.extent[2] - page.extent[0]} {page.extent[3] - page.extent[1]}" '
        'stroke-linecap="round" stroke-linejoin="round" fill="none">'
    ]
    for s in page.strokes:
        if len(s.points) < 2:
            continue
        color = s.color or "#000000"
        w = s.width_mm or pen_width_mm
        d = "M " + " L ".join(f"{p.x:.3f} {p.y:.3f}" for p in s.points)
        opacity = ' stroke-opacity="0.4"' if s.highlighter else ""
        parts.append(
            f'<path d="{d}" stroke="{color}" stroke-width="{w:.3f}"{opacity}/>'
        )
    parts.append("</svg>")
    return "\n".join(parts)
