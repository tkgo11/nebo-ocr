# Verification — nebo-ocr

- Date (UTC): 2026-09-21
- Commit: e47c99e (master), tree clean
- Repo: https://github.com/tkgo11/nebo-ocr

## Gate results

| Gate | Command | Result | Evidence |
|------|---------|--------|----------|
| Lint | `ruff check .` | PASS | `All checks passed!` (exit 0) |
| Typecheck | `mypy src` | PASS | `Success: no issues found in 21 source files` (strict mode, exit 0) |
| Tests | `pytest` | PASS | `64 passed in 0.35s` (exit 0) |
| Build | `python3 -m build` | PASS | `Successfully built nebo_ocr-0.1.0.tar.gz and nebo_ocr-0.1.0-py3-none-any.whl` (exit 0) |

## Raw output

```text
=== ruff ===
All checks passed!
ruff_exit=0
=== mypy ===
Success: no issues found in 21 source files
mypy_exit=0
=== pytest ===
................................................................         [100%]
64 passed in 0.35s
pytest_exit=0
=== build ===
Successfully built nebo_ocr-0.1.0.tar.gz and nebo_ocr-0.1.0-py3-none-any.whl
build_exit=0
```

## Functional spot-check (real .nebo fixture)

```text
$ nebo-ocr info Write.nebo
pages: 2, strokes: 45, language: Italian (it_IT)
  page 0: 45 strokes, 125 tags, 3 embedded labels

$ nebo-ocr extract Write.nebo
1st
AL', i, a test
try ti
- ad delete
↳ write after
delete
```

Verdict: **ALL GATES PASS**
