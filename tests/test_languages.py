"""Locale normalization and per-backend mapping tests."""
from __future__ import annotations

import pytest

from nebo_ocr.languages import (
    backends_for_language,
    language_name,
    normalize_locale,
    supported_languages,
    to_backend_code,
)


@pytest.mark.parametrize(
    "given,expected",
    [
        ("it_IT", "it_IT"),
        ("it-IT", "it_IT"),
        ("it", "it_IT"),
        ("ita", "it_IT"),
        ("italian", "it_IT"),
        ("en", "en_US"),
        ("en-US", "en_US"),
        ("en_GB", "en_GB"),
        ("ko", "ko_KR"),
        ("korean", "ko_KR"),
        ("ja", "ja_JP"),
        ("zh", "zh_CN"),
        ("zh-TW", "zh_TW"),
        ("ch_sim", "zh_CN"),      # EasyOCR spelling
        ("chinese_cht", "zh_TW"),  # PaddleOCR spelling
        ("japan", "ja_JP"),        # PaddleOCR spelling
        ("mul_Latn", "mul_Latn"),
        ("nb", "nb_NO"),
        ("no", "nb_NO"),
    ],
)
def test_normalize(given, expected):
    assert normalize_locale(given) == expected


def test_normalize_bad():
    with pytest.raises(ValueError):
        normalize_locale("xx_99_nonsense")
    assert normalize_locale(None) is None
    assert normalize_locale("") is None


def test_language_name():
    assert language_name("it_IT") == "Italian"
    assert language_name("ko_KR") == "Korean"


def test_backend_code_myscript():
    assert to_backend_code("it_IT", "myscript") == "it_IT"
    assert to_backend_code("zh_CN", "myscript") == "zh_CN"
    assert to_backend_code("km_KH", "myscript") is None  # Khmer unsupported


def test_backend_code_easyocr():
    assert to_backend_code("it_IT", "easyocr") == "it"
    assert to_backend_code("zh_CN", "easyocr") == "ch_sim"
    assert to_backend_code("zh_TW", "easyocr") == "ch_tra"
    assert to_backend_code("ja_JP", "easyocr") == "ja"
    assert to_backend_code("km_KH", "easyocr") is None


def test_backend_code_paddle():
    assert to_backend_code("ja_JP", "paddleocr") == "japan"
    assert to_backend_code("ko_KR", "paddleocr") == "korean"
    assert to_backend_code("zh_TW", "paddleocr") == "chinese_cht"
    assert to_backend_code("hi_IN", "paddleocr") == "hi"


def test_backend_code_surya():
    assert to_backend_code("ko_KR", "surya") == "ko"
    assert to_backend_code("zh_CN", "surya") == "zh"


def test_backend_code_trocr():
    assert to_backend_code("en_US", "trocr") == "en"
    assert to_backend_code("fr_FR", "trocr") is None


def test_backend_code_clouds():
    assert to_backend_code("zh_TW", "google") == "zh-TW"
    assert to_backend_code("it_IT", "azure") == "it_IT"
    assert to_backend_code("it_IT", "mathpix") == "it"


def test_supported_languages_counts():
    assert len(supported_languages("myscript")) >= 65
    assert len(supported_languages("easyocr")) >= 60
    assert len(supported_languages("surya")) >= 70
    assert len(supported_languages("paddleocr")) >= 60
    assert len(supported_languages("embedded")) >= 90


def test_backends_for_language():
    assert "myscript" in backends_for_language("ja_JP")
    assert "surya" in backends_for_language("ja_JP")
    assert "trocr" not in backends_for_language("ja_JP")
    assert "trocr" in backends_for_language("en_US")
