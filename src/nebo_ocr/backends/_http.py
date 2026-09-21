"""Shared stdlib HTTP helpers for cloud backends (no third-party deps)."""
from __future__ import annotations

import json
import urllib.request
from typing import Any

from .base import BackendUnavailable

DEFAULT_TIMEOUT = 90


def post_json(
    url: str,
    payload: Any,
    headers: dict[str, str],
    timeout: int = DEFAULT_TIMEOUT,
) -> Any:
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", **headers},
    )
    return _open(req, timeout)


def post_bytes(
    url: str,
    body: bytes,
    headers: dict[str, str],
    content_type: str = "application/octet-stream",
    timeout: int = DEFAULT_TIMEOUT,
) -> Any:
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": content_type, **headers}
    )
    return _open(req, timeout)


def get_json(url: str, headers: dict[str, str], timeout: int = 30) -> Any:
    req = urllib.request.Request(url, headers=headers)
    return _open(req, timeout)


def _open(req: urllib.request.Request, timeout: int) -> Any:
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            ctype = resp.headers.get("Content-Type", "")
            if "json" in ctype:
                return json.loads(data)
            return data
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:400]
        raise BackendUnavailable(f"HTTP {exc.code}: {detail}") from exc
    except OSError as exc:
        raise BackendUnavailable(f"request failed: {exc}") from exc
