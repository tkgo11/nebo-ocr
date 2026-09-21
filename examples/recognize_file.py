"""Minimal example: load a .nebo file and recognize it.

Usage: python examples/recognize_file.py notes.nebo [backend] [lang]
"""
import sys

from nebo_ocr import available_backends, load_nebo, recognize

path = sys.argv[1] if len(sys.argv) > 1 else "notes.nebo"
backend = sys.argv[2] if len(sys.argv) > 2 else "embedded"
lang = sys.argv[3] if len(sys.argv) > 3 else None

nb = load_nebo(path)
print(f"{len(nb.pages)} page(s), language hint: {nb.language}")

result = recognize(nb, backend=backend, language=lang)
for page in result.pages:
    print(f"--- {page.page_id} ---")
    print(page.text)

ready = [n for n, ok, _ in available_backends() if ok]
print(f"\nready backends: {', '.join(ready)}")
