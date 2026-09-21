# nebo-ocr

Handwriting recognition for **MyScript Nebo** `.nebo` files.

`.nebo` exports are ZIP containers holding vector ink in MyScript's binary
`ink.bink` format. nebo-ocr decodes those strokes (millimetre-accurate, with
pressure) and runs them through pluggable recognition engines — from the
text Nebo itself embeds in the file, to cloud APIs, to fully local OCR —
across **100+ languages/locales**.

```sh
pip install -e .            # base: Pillow only
pip install -e .[easyocr]   # + a local OCR engine
pip install -e .[all]       # all optional engines
```

## Quick start

```sh
nebo-ocr info notes.nebo                 # pages, strokes, declared language
nebo-ocr extract notes.nebo              # text Nebo already embedded (offline!)
nebo-ocr recognize notes.nebo -b myscript -l ko_KR
nebo-ocr render notes.nebo -o page.png   # or .svg
nebo-ocr languages                       # language catalogue per backend
nebo-ocr backends                        # which engines are ready to use
```

```python
from nebo_ocr import load_nebo, recognize

nb = load_nebo("notes.nebo")          # Notebook → Pages → Strokes → Points (mm)
res = recognize(nb, backend="embedded")
print(res.pages[0].text)
```

## Recognition backends

| Backend    | Type    | Languages | Notes |
|------------|---------|-----------|-------|
| `embedded` | offline | whatever Nebo used | `DWLabel` text already inside the file — no deps, no network |
| `myscript` | cloud   | 73 locales | Sends raw strokes (no rasterization) to the iink REST API |
| `google`   | cloud   | 111 | Cloud Vision `DOCUMENT_TEXT_DETECTION` on rendered ink |
| `azure`    | cloud   | 111 | Azure AI Vision Read on rendered ink |
| `mathpix`  | cloud   | 84 | Good for mixed text + math |
| `surya`    | local   | 114 | `pip install nebo-ocr[surya]` |
| `easyocr`  | local   | 78 | `pip install nebo-ocr[easyocr]` |
| `paddleocr`| local   | 85 | `pip install nebo-ocr[paddleocr]` |
| `trocr`    | local   | 6 | Microsoft's handwriting transformer |

Language resolution: `--lang` (any spelling — `it_IT`, `it-IT`, `it`,
`italian`) → normalized → mapped to each backend's own code. Without
`--lang`, the document's `languageLocaleIdentifier` is used.

### Cloud credentials

```sh
# MyScript iink (developer.myscript.com)
export MYSCRIPT_APPLICATION_KEY=... MYSCRIPT_HMAC_KEY=...
# Google
export GOOGLE_VISION_API_KEY=...        # or GOOGLE_APPLICATION_CREDENTIALS
# Azure
export AZURE_VISION_ENDPOINT=... AZURE_VISION_KEY=...
# Mathpix
export MATHPIX_APP_ID=... MATHPIX_APP_KEY=...
```

## The `.nebo` format

```
notes.nebo (zip)
├── meta.json                  # languageLocaleIdentifier, app/doc versions
├── rel.json
├── index.bdom
└── pages/<id>/
    ├── ink.bink               # BINK v5: strokes as mm coords, i16 deltas, pressure
    ├── page.bdom              # tag tree: TOOL/STYLE + CHAR/WORD/TEXT_LINE/DIAGRAM
    ├── meta.json              # page extent (e.g. [0,0,210,297] mm)
    └── style.css
```

`page.bdom` recognition tags carry Nebo's own text in `DIAGRAM` payloads
(`{"DWShape":"text","DWLabel":"..."}`) — the `embedded` backend surfaces it
for free. `TEXT_LINE` tags also give exact line regions for cropping.

The BINK decoder is an independent implementation of the reverse-engineered
v5 format (no MyScript SDK code).

## Development

```sh
pip install -e .[dev]
pytest            # 64 tests incl. synthetic .nebo fixtures
mypy src          # strict
ruff check .
python -m build
```

## License

MIT
