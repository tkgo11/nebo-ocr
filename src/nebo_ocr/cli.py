"""``nebo-ocr`` command line interface."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .backends import available_backends, get_backend, registry
from .backends.base import BackendUnavailable
from .languages import (
    backends_for_language,
    language_name,
    normalize_locale,
    supported_languages,
)
from .nebo import load_nebo
from .recognize import recognize
from .render import RenderOptions, page_to_svg, render_page


def _cmd_info(args: argparse.Namespace) -> int:
    nb = load_nebo(args.file)
    print(f"file:      {nb.path}")
    print(f"title:     {nb.title}")
    print(f"pages:     {len(nb.pages)}")
    print(f"strokes:   {nb.stroke_count}")
    print(f"language:  {language_name(nb.language)} ({nb.language or '?'})")
    print(f"versions:  doc={nb.document_version} app={nb.application_version}")
    for i, p in enumerate(nb.pages):
        labels = p.diagram_labels()
        print(
            f"  page {i} ({p.page_id}): {len(p.strokes)} strokes, "
            f"{len(p.tags)} tags, {len(labels)} embedded labels"
        )
    return 0


def _cmd_extract(args: argparse.Namespace) -> int:
    nb = load_nebo(args.file)
    res = get_backend("embedded").recognize(nb, args.lang)
    if args.json:
        print(json.dumps({"backend": res.backend, "language": res.language,
                          "pages": [{"page_id": p.page_id, "text": p.text}
                                    for p in res.pages]}, ensure_ascii=False, indent=2))
    else:
        for i, p in enumerate(res.pages):
            if len(res.pages) > 1:
                print(f"--- page {i} ({p.page_id}) ---")
            print(p.text or "(no embedded text)")
    return 0


def _cmd_recognize(args: argparse.Namespace) -> int:
    try:
        res = recognize(args.file, backend=args.backend, language=args.lang)
    except BackendUnavailable as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(
            {
                "backend": res.backend,
                "language": res.language,
                "pages": [
                    {
                        "page_id": p.page_id,
                        "text": p.text,
                        "lines": [
                            {"text": ln.text, "confidence": ln.confidence,
                             "bounds_mm": ln.bounds_mm}
                            for ln in p.lines
                        ],
                    }
                    for p in res.pages
                ],
            },
            ensure_ascii=False,
            indent=2,
        ))
    else:
        for i, p in enumerate(res.pages):
            if len(res.pages) > 1:
                print(f"--- page {i} ({p.page_id}) ---")
            print(p.text or "(no text)")
    return 0


def _cmd_render(args: argparse.Namespace) -> int:
    nb = load_nebo(args.file)
    out = Path(args.out)
    opts = RenderOptions(dpi=args.dpi, crop_to_content=not args.full_page)
    out.mkdir(parents=True, exist_ok=True)
    for i, page in enumerate(nb.pages):
        target = out / f"{nb.title}-p{i}.png" if len(nb.pages) > 1 else out / f"{nb.title}.png"
        if args.svg:
            target = target.with_suffix(".svg")
            target.write_text(page_to_svg(page))
        else:
            render_page(page, opts).save(target)
        print(target)
    return 0


def _cmd_languages(args: argparse.Namespace) -> int:
    backends = [args.backend] if args.backend else sorted(registry())
    for name in backends:
        langs = supported_languages(name)
        print(f"{name} ({len(langs)} languages):")
        print("  " + ", ".join(langs))
    return 0


def _cmd_backends(args: argparse.Namespace) -> int:
    for name, ok, why in available_backends():
        mark = "ready " if ok else "missing"
        print(f"{mark} {name:10s} {why}")
    if args.lang:
        canon = normalize_locale(args.lang)
        usable = backends_for_language(args.lang)
        print(f"\n{language_name(canon)} ({canon}): usable backends -> "
              + (", ".join(usable) if usable else "none"))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="nebo-ocr",
        description="Handwriting recognition for MyScript Nebo .nebo files "
                    "(embedded labels, cloud APIs, local OCR) in 100+ locales.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("info", help="inspect a .nebo file")
    sp.add_argument("file")
    sp.set_defaults(func=_cmd_info)

    sp = sub.add_parser("extract", help="print text already embedded by Nebo")
    sp.add_argument("file")
    sp.add_argument("-l", "--lang", default=None)
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=_cmd_extract)

    sp = sub.add_parser("recognize", help="run an OCR backend on the strokes")
    sp.add_argument("file")
    sp.add_argument("-b", "--backend", default="embedded")
    sp.add_argument("-l", "--lang", default=None,
                    help="language, e.g. it_IT, ko_KR, zh_CN (default: file's own)")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=_cmd_recognize)

    sp = sub.add_parser("render", help="render pages to PNG (or SVG)")
    sp.add_argument("file")
    sp.add_argument("-o", "--out", default=".")
    sp.add_argument("--dpi", type=float, default=200.0)
    sp.add_argument("--svg", action="store_true")
    sp.add_argument("--full-page", action="store_true",
                    help="keep the page extent instead of cropping to ink")
    sp.set_defaults(func=_cmd_render)

    sp = sub.add_parser("languages", help="list supported languages per backend")
    sp.add_argument("-b", "--backend", default=None)
    sp.set_defaults(func=_cmd_languages)

    sp = sub.add_parser("backends", help="list backends and their readiness")
    sp.add_argument("-l", "--lang", default=None,
                    help="also show which backends handle this language")
    sp.set_defaults(func=_cmd_backends)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except BackendUnavailable as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
