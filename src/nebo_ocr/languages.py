"""Language/locale registry shared by all recognition backends.

Canonical form is ``<iso-639-1>_<iso-3166-1>`` (``en_US``, ``zh_TW``), the same
shape Nebo stores in ``languageLocaleIdentifier`` and MyScript's iink engine
expects in ``configuration.lang``. Helpers normalize the many ways users and
backends spell a locale (``en-US``, ``en``, ``eng``, EasyOCR's ``ch_sim``,
PaddleOCR's ``japan`` ...) and map a canonical locale onto each backend's own
code — so a single ``--lang it_IT`` works everywhere.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Canonical locale catalog: code -> English name
# (locales recognised across the supported backends; not all backends cover
# all of them — see to_backend_code / supported_languages)
# ---------------------------------------------------------------------------
LANGUAGE_NAMES: dict[str, str] = {
    "af_ZA": "Afrikaans",
    "sq_AL": "Albanian",
    "am_ET": "Amharic",
    "ar_SA": "Arabic",
    "hy_AM": "Armenian",
    "as_IN": "Assamese",
    "az_AZ": "Azerbaijani",
    "ba_RU": "Bashkir",
    "eu_ES": "Basque",
    "be_BY": "Belarusian",
    "bn_BD": "Bengali",
    "bho_IN": "Bhojpuri",
    "bs_BA": "Bosnian",
    "bg_BG": "Bulgarian",
    "my_MM": "Burmese",
    "ca_ES": "Catalan",
    "ceb_PH": "Cebuano",
    "zh_CN": "Chinese (Simplified)",
    "zh_HK": "Chinese (Traditional, Hong Kong)",
    "zh_TW": "Chinese (Traditional, Taiwan)",
    "co_FR": "Corsican",
    "hr_HR": "Croatian",
    "cs_CZ": "Czech",
    "da_DK": "Danish",
    "nl_BE": "Dutch (Belgium)",
    "nl_NL": "Dutch",
    "en_AU": "English (Australia)",
    "en_CA": "English (Canada)",
    "en_PH": "English (Philippines)",
    "en_ZA": "English (South Africa)",
    "en_GB": "English (United Kingdom)",
    "en_US": "English (United States)",
    "eo": "Esperanto",
    "et_EE": "Estonian",
    "fa_IR": "Farsi (Persian)",
    "fil_PH": "Filipino",
    "fi_FI": "Finnish",
    "fr_CA": "French (Canada)",
    "fr_FR": "French",
    "fy_NL": "Frisian",
    "gl_ES": "Galician",
    "ka_GE": "Georgian",
    "de_AT": "German (Austria)",
    "de_DE": "German",
    "el_GR": "Greek",
    "gu_IN": "Gujarati",
    "haw_US": "Hawaiian",
    "he_IL": "Hebrew",
    "hi_IN": "Hindi",
    "hmn_US": "Hmong",
    "hu_HU": "Hungarian",
    "is_IS": "Icelandic",
    "id_ID": "Indonesian",
    "ga_IE": "Irish",
    "it_IT": "Italian",
    "ja_JP": "Japanese",
    "jv_ID": "Javanese",
    "kn_IN": "Kannada",
    "kk_KZ": "Kazakh",
    "km_KH": "Khmer",
    "ko_KR": "Korean",
    "ku_TR": "Kurdish",
    "ky_KG": "Kyrgyz",
    "lo_LA": "Lao",
    "la_VA": "Latin",
    "lv_LV": "Latvian",
    "lt_LT": "Lithuanian",
    "lb_LU": "Luxembourgish",
    "mk_MK": "Macedonian",
    "mg_MG": "Malagasy",
    "ms_MY": "Malay",
    "ml_IN": "Malayalam",
    "mt_MT": "Maltese",
    "mr_IN": "Marathi",
    "mn_MN": "Mongolian",
    "ne_NP": "Nepali",
    "nb_NO": "Norwegian",
    "oc_FR": "Occitan",
    "or_IN": "Odia",
    "ps_AF": "Pashto",
    "pa_IN": "Punjabi",
    "pl_PL": "Polish",
    "pt_BR": "Portuguese (Brazil)",
    "pt_PT": "Portuguese",
    "ro_RO": "Romanian",
    "ru_RU": "Russian",
    "sa_IN": "Sanskrit",
    "sr_RS": "Serbian (Latin)",
    "sr_Cyrl_RS": "Serbian (Cyrillic)",
    "sd_PK": "Sindhi",
    "si_LK": "Sinhala",
    "sk_SK": "Slovak",
    "sl_SI": "Slovenian",
    "es_CO": "Spanish (Colombia)",
    "es_MX": "Spanish (Mexico)",
    "es_ES": "Spanish",
    "sw_TZ": "Swahili",
    "sv_SE": "Swedish",
    "tg_TJ": "Tajik",
    "tl_PH": "Tagalog",
    "ta_IN": "Tamil",
    "tt_RU": "Tatar",
    "te_IN": "Telugu",
    "th_TH": "Thai",
    "tr_TR": "Turkish",
    "tk_TM": "Turkmen",
    "uk_UA": "Ukrainian",
    "ur_PK": "Urdu",
    "ug_CN": "Uyghur",
    "uz_UZ": "Uzbek",
    "vi_VN": "Vietnamese",
    "cy_GB": "Welsh",
    "yi_IL": "Yiddish",
    "zu_ZA": "Zulu",
    "mul_Latn": "Multiple Latin languages (MyScript Raw Content)",
}

# ---------------------------------------------------------------------------
# Per-backend language support, expressed as sets of *backend-native* codes.
# ---------------------------------------------------------------------------

#: MyScript iink text languages (≈72 locales + mul_Latn for Raw Content).
MYSCRIPT_LOCALES: set[str] = {
    "af_ZA", "sq_AL", "ar_SA", "hy_AM", "az_AZ", "eu_ES", "be_BY", "bs_BA",
    "bg_BG", "ca_ES", "ceb_PH", "zh_CN", "zh_HK", "zh_TW", "hr_HR", "cs_CZ",
    "da_DK", "nl_BE", "nl_NL", "en_CA", "en_PH", "en_ZA", "en_GB", "en_US",
    "et_EE", "fa_IR", "fil_PH", "fi_FI", "fr_CA", "fr_FR", "ga_IE", "gl_ES",
    "ka_GE", "de_AT", "de_DE", "el_GR", "he_IL", "hi_IN", "hu_HU", "is_IS",
    "id_ID", "it_IT", "ja_JP", "kk_KZ", "ko_KR", "lv_LV", "lt_LT", "mk_MK",
    "mg_MG", "ms_MY", "mn_MN", "nb_NO", "pl_PL", "pt_BR", "pt_PT", "ro_RO",
    "ru_RU", "sr_RS", "sr_Cyrl_RS", "sk_SK", "sl_SI", "es_CO", "es_MX",
    "es_ES", "sw_TZ", "sv_SE", "tt_RU", "th_TH", "tr_TR", "uk_UA", "ur_PK",
    "vi_VN", "mul_Latn",
}

#: EasyOCR language codes.
EASYOCR_CODES: set[str] = {
    "abq", "ady", "af", "ang", "ar", "as", "ava", "az", "be", "bg", "bh",
    "bho", "bn", "bs", "ch_sim", "ch_tra", "che", "cs", "cy", "da", "dar",
    "de", "en", "es", "et", "fa", "fr", "ga", "gom", "hi", "hr", "hu", "id",
    "inh", "is", "it", "ja", "kbd", "kn", "ko", "ku", "la", "lbe", "lez",
    "lt", "lv", "mah", "mai", "mi", "mn", "mr", "ms", "mt", "ne", "new",
    "nl", "no", "oc", "pi", "pl", "pt", "ro", "rs_cyrillic", "rs_latin",
    "ru", "sck", "sk", "sl", "sq", "sv", "sw", "ta", "tab", "te", "th",
    "tjk", "tl", "tr", "ug", "uk", "ur", "uz", "vi",
}

#: Surya OCR languages (ISO codes it accepts in `langs`).
SURYA_CODES: set[str] = {
    "af", "am", "ar", "as", "az", "ba", "be", "bg", "bn", "bho", "br", "bs",
    "ca", "ceb", "co", "cs", "cy", "da", "de", "el", "en", "eo", "es", "et",
    "eu", "fa", "fi", "fil", "fj", "fo", "fr", "fy", "ga", "gd", "gl", "gom",
    "gu", "ha", "haw", "he", "hi", "hmn", "hr", "ht", "hu", "hy", "id", "ig",
    "is", "it", "iu", "ja", "jv", "ka", "kk", "km", "kn", "ko", "ku", "ky",
    "la", "lb", "lo", "lt", "lv", "mg", "mi", "mk", "ml", "mn", "mr", "ms",
    "mt", "my", "nb", "ne", "nl", "nn", "no", "ny", "oc", "or", "otq", "pa",
    "pl", "ps", "pt", "qu", "ro", "ru", "sa", "sd", "si", "sk", "sl", "sm",
    "sn", "sq", "sr", "st", "su", "sv", "sw", "ta", "te", "tg", "th", "tk",
    "tl", "to", "tr", "tt", "ty", "ug", "uk", "ur", "uz", "vi", "yi", "yo",
    "yua", "zh", "zu",
}

#: PaddleOCR `lang` values (script-family names + specific codes).
PADDLEOCR_CODES: set[str] = {
    "ch", "chinese_cht", "en", "japan", "korean", "latin", "arabic",
    "cyrillic", "devanagari", "ta", "te", "kn", "ka", "hy",
    # latin alphabet languages
    "af", "az", "bs", "cs", "cy", "da", "de", "es", "et", "fr", "ga", "hr",
    "hu", "id", "is", "it", "ku", "la", "lt", "lv", "mi", "ms", "mt", "nl",
    "no", "oc", "pi", "pl", "pt", "ro", "rs_latin", "sk", "sl", "sq", "sv",
    "sw", "tl", "tr", "ug", "uk", "ur", "uz", "vi",
    # cyrillic
    "abq", "ady", "ava", "be", "bg", "dar", "inh", "kbd", "kk", "ky", "lbe",
    "lez", "mn", "rs_cyrillic", "ru", "sck", "tab", "tg", "tjk", "tt",
    # arabic script
    "ar", "fa",
    # devanagari + indic
    "as", "bh", "bho", "bn", "gom", "hi", "mai", "ml", "mr", "ne", "new",
    "or", "pa", "sa",
}

#: TrOCR handwritten models are English-only.
TROCR_CODES: set[str] = {"en"}

# Google/Azure take BCP-47 hints and cover a wide set; we accept any canonical
# locale whose language is in this (broad) set and pass it through as a hint.
CLOUD_HINT_LANGS: set[str] = {
    "af", "am", "ar", "as", "az", "be", "bg", "bn", "bs", "ca", "ceb", "co",
    "cs", "cy", "da", "de", "el", "en", "eo", "es", "et", "eu", "fa", "fi",
    "fil", "fr", "fy", "ga", "gd", "gl", "gu", "haw", "he", "hi", "hmn",
    "hr", "hu", "hy", "id", "is", "it", "ja", "jv", "ka", "kk", "km", "kn",
    "ko", "ku", "ky", "la", "lb", "lo", "lt", "lv", "mg", "mi", "mk", "ml",
    "mn", "mr", "ms", "mt", "my", "ne", "nl", "no", "ny", "oc", "or", "pa",
    "pl", "ps", "pt", "ro", "ru", "sa", "sd", "si", "sk", "sl", "sm", "sn",
    "sq", "sr", "st", "su", "sv", "sw", "ta", "te", "tg", "th", "tk", "tl",
    "tr", "tt", "ug", "uk", "ur", "uz", "vi", "yi", "zh", "zu",
}

#: Mathpix `languages` option codes it understands.
MATHPIX_CODES: set[str] = {
    "en", "es", "fr", "de", "hi", "ja", "ko", "zh_s", "zh_t", "th", "ru",
    "it", "pt", "nl", "sv", "da", "pl", "tr", "vi", "id", "ms", "cs", "uk",
    "ar", "he", "fa", "ur", "bn", "ta", "te", "kn", "ml", "mr", "ne", "pa",
    "gu", "or", "as", "my", "km", "lo", "si", "ro", "hu", "el", "bg", "sr",
    "hr", "sk", "sl", "lt", "lv", "et", "fi", "is", "ga", "sq", "mk", "bs",
    "az", "kk", "ky", "mn", "uz", "tk", "tg", "hy", "ka", "sw", "zu", "af",
}

#: Aliases mapping arbitrary spellings to canonical locales.
_ALIASES: dict[str, str] = {
    "en": "en_US", "eng": "en_US", "english": "en_US",
    "fr": "fr_FR", "fre": "fr_FR", "fra": "fr_FR", "french": "fr_FR",
    "de": "de_DE", "ger": "de_DE", "deu": "de_DE", "german": "de_DE",
    "it": "it_IT", "ita": "it_IT", "italian": "it_IT",
    "es": "es_ES", "spa": "es_ES", "spanish": "es_ES",
    "pt": "pt_PT", "por": "pt_PT", "portuguese": "pt_PT",
    "nl": "nl_NL", "dut": "nl_NL", "nld": "nl_NL", "dutch": "nl_NL",
    "ru": "ru_RU", "rus": "ru_RU", "russian": "ru_RU",
    "uk": "uk_UA", "ukr": "uk_UA", "ukrainian": "uk_UA",
    "ja": "ja_JP", "jpn": "ja_JP", "japanese": "ja_JP", "japan": "ja_JP",
    "ko": "ko_KR", "kor": "ko_KR", "korean": "ko_KR",
    "zh": "zh_CN", "zho": "zh_CN", "chi": "zh_CN", "chinese": "zh_CN",
    "ch": "zh_CN", "ch_sim": "zh_CN", "chinese_cht": "zh_TW", "ch_tra": "zh_TW",
    "pl": "pl_PL", "pol": "pl_PL", "polish": "pl_PL",
    "sv": "sv_SE", "swe": "sv_SE", "swedish": "sv_SE",
    "no": "nb_NO", "nor": "nb_NO", "nb": "nb_NO", "norwegian": "nb_NO",
    "da": "da_DK", "dan": "da_DK", "danish": "da_DK",
    "fi": "fi_FI", "fin": "fi_FI", "finnish": "fi_FI",
    "tr": "tr_TR", "tur": "tr_TR", "turkish": "tr_TR",
    "el": "el_GR", "gre": "el_GR", "ell": "el_GR", "greek": "el_GR",
    "cs": "cs_CZ", "cze": "cs_CZ", "ces": "cs_CZ", "czech": "cs_CZ",
    "sk": "sk_SK", "slo": "sk_SK", "slk": "sk_SK", "slovak": "sk_SK",
    "sl": "sl_SI", "slv": "sl_SI", "slovenian": "sl_SI",
    "hr": "hr_HR", "hrv": "hr_HR", "croatian": "hr_HR",
    "sr": "sr_RS", "srp": "sr_RS", "serbian": "sr_RS",
    "bg": "bg_BG", "bul": "bg_BG", "bulgarian": "bg_BG",
    "ro": "ro_RO", "rum": "ro_RO", "ron": "ro_RO", "romanian": "ro_RO",
    "hu": "hu_HU", "hun": "hu_HU", "hungarian": "hu_HU",
    "et": "et_EE", "est": "et_EE", "estonian": "et_EE",
    "lv": "lv_LV", "lav": "lv_LV", "latvian": "lv_LV",
    "lt": "lt_LT", "lit": "lt_LT", "lithuanian": "lt_LT",
    "ga": "ga_IE", "gle": "ga_IE", "irish": "ga_IE",
    "cy": "cy_GB", "wel": "cy_GB", "cym": "cy_GB", "welsh": "cy_GB",
    "is": "is_IS", "ice": "is_IS", "isl": "is_IS", "icelandic": "is_IS",
    "mt": "mt_MT", "mlt": "mt_MT", "maltese": "mt_MT",
    "ca": "ca_ES", "cat": "ca_ES", "catalan": "ca_ES",
    "eu": "eu_ES", "baq": "eu_ES", "eus": "eu_ES", "basque": "eu_ES",
    "gl": "gl_ES", "glg": "gl_ES", "galician": "gl_ES",
    "oc": "oc_FR", "oci": "oc_FR", "occitan": "oc_FR",
    "ar": "ar_SA", "ara": "ar_SA", "arabic": "ar_SA",
    "he": "he_IL", "heb": "he_IL", "hebrew": "he_IL",
    "fa": "fa_IR", "per": "fa_IR", "fas": "fa_IR", "persian": "fa_IR", "farsi": "fa_IR",
    "ur": "ur_PK", "urd": "ur_PK",
    "hi": "hi_IN", "hin": "hi_IN", "hindi": "hi_IN",
    "bn": "bn_BD", "ben": "bn_BD", "bengali": "bn_BD",
    "ta": "ta_IN", "tam": "ta_IN", "tamil": "ta_IN",
    "te": "te_IN", "tel": "te_IN", "telugu": "te_IN",
    "kn": "kn_IN", "kan": "kn_IN", "kannada": "kn_IN",
    "ml": "ml_IN", "mal": "ml_IN", "malayalam": "ml_IN",
    "mr": "mr_IN", "mar": "mr_IN", "marathi": "mr_IN",
    "gu": "gu_IN", "guj": "gu_IN", "gujarati": "gu_IN",
    "pa": "pa_IN", "pan": "pa_IN", "punjabi": "pa_IN",
    "or": "or_IN", "ori": "or_IN", "odia": "or_IN",
    "as": "as_IN", "asm": "as_IN", "assamese": "as_IN",
    "ne": "ne_NP", "nep": "ne_NP", "nepali": "ne_NP",
    "sa": "sa_IN", "san": "sa_IN", "sanskrit": "sa_IN",
    "si": "si_LK", "sin": "si_LK", "sinhala": "si_LK",
    "th": "th_TH", "tha": "th_TH", "thai": "th_TH",
    "vi": "vi_VN", "vie": "vi_VN", "vietnamese": "vi_VN",
    "id": "id_ID", "ind": "id_ID", "indonesian": "id_ID",
    "ms": "ms_MY", "may": "ms_MY", "msa": "ms_MY", "malay": "ms_MY",
    "tl": "tl_PH", "tgl": "tl_PH", "tagalog": "tl_PH",
    "fil": "fil_PH", "filipino": "fil_PH",
    "sw": "sw_TZ", "swa": "sw_TZ", "swahili": "sw_TZ",
    "zu": "zu_ZA", "zul": "zu_ZA", "zulu": "zu_ZA",
    "af": "af_ZA", "afr": "af_ZA", "afrikaans": "af_ZA",
    "sq": "sq_AL", "alb": "sq_AL", "sqi": "sq_AL", "albanian": "sq_AL",
    "hy": "hy_AM", "arm": "hy_AM", "hye": "hy_AM", "armenian": "hy_AM",
    "az": "az_AZ", "aze": "az_AZ", "azerbaijani": "az_AZ", "azeri": "az_AZ",
    "be": "be_BY", "bel": "be_BY", "belarusian": "be_BY",
    "bs": "bs_BA", "bos": "bs_BA", "bosnian": "bs_BA",
    "my": "my_MM", "bur": "my_MM", "mya": "my_MM", "burmese": "my_MM",
    "ka": "ka_GE", "geo": "ka_GE", "kat": "ka_GE", "georgian": "ka_GE",
    "kk": "kk_KZ", "kaz": "kk_KZ", "kazakh": "kk_KZ",
    "km": "km_KH", "khm": "km_KH", "khmer": "km_KH",
    "ku": "ku_TR", "kur": "ku_TR", "kurdish": "ku_TR",
    "ky": "ky_KG", "kir": "ky_KG", "kyrgyz": "ky_KG",
    "lo": "lo_LA", "lao": "lo_LA",
    "la": "la_VA", "lat": "la_VA", "latin": "la_VA",
    "lb": "lb_LU", "ltz": "lb_LU", "luxembourgish": "lb_LU",
    "mk": "mk_MK", "mac": "mk_MK", "mkd": "mk_MK", "macedonian": "mk_MK",
    "mg": "mg_MG", "mlg": "mg_MG", "malagasy": "mg_MG",
    "mn": "mn_MN", "mon": "mn_MN", "mongolian": "mn_MN",
    "ps": "ps_AF", "pus": "ps_AF", "pashto": "ps_AF",
    "sd": "sd_PK", "snd": "sd_PK", "sindhi": "sd_PK",
    "tg": "tg_TJ", "tgk": "tg_TJ", "tajik": "tg_TJ", "tjk": "tg_TJ",
    "tt": "tt_RU", "tat": "tt_RU", "tatar": "tt_RU",
    "tk": "tk_TM", "tuk": "tk_TM", "turkmen": "tk_TM",
    "ug": "ug_CN", "uig": "ug_CN", "uyghur": "ug_CN",
    "uz": "uz_UZ", "uzb": "uz_UZ", "uzbek": "uz_UZ",
    "yi": "yi_IL", "yid": "yi_IL", "yiddish": "yi_IL",
    "am": "am_ET", "amh": "am_ET", "amharic": "am_ET",
    "ceb": "ceb_PH", "cebuano": "ceb_PH",
    "haw": "haw_US", "hawaiian": "haw_US",
    "hmn": "hmn_US", "hmong": "hmn_US",
    "jv": "jv_ID", "jav": "jv_ID", "javanese": "jv_ID",
    "eo": "eo", "epo": "eo", "esperanto": "eo",
    "fy": "fy_NL", "fry": "fy_NL", "frisian": "fy_NL",
    "co": "co_FR", "cos": "co_FR", "corsican": "co_FR",
    "mul_latn": "mul_Latn", "mul": "mul_Latn",
}


def normalize_locale(lang: str | None) -> str | None:
    """Normalize a user/file locale to canonical ``xx_YY`` form.

    Accepts ``it_IT``, ``it-IT``, ``it``, ``ita``, ``italian``, EasyOCR's
    ``ch_sim``, PaddleOCR's ``japan``/``korean``/``chinese_cht`` ... Returns
    ``None`` for None/empty input; raises ``ValueError`` for garbage.
    """
    if lang is None:
        return None
    s = lang.strip()
    if not s:
        return None
    key = s.lower().replace("-", "_").replace(" ", "_")
    if key in _ALIASES:
        return _ALIASES[key]
    if s in LANGUAGE_NAMES:
        return s
    # xx_YY / xx_YY_ZZ / xx-Script_YY forms
    parts = key.split("_")
    if len(parts) >= 2:
        guess = f"{parts[0]}_{parts[-1].upper()}"
        if guess in LANGUAGE_NAMES:
            return guess
        guess2 = f"{parts[0]}_{parts[1].upper()}"
        if guess2 in LANGUAGE_NAMES:
            return guess2
    raise ValueError(f"unrecognized language/locale: {lang!r}")


def language_name(lang: str | None) -> str:
    if lang is None:
        return "(unspecified)"
    try:
        canon = normalize_locale(lang) or lang
    except ValueError:
        return lang
    return LANGUAGE_NAMES.get(canon, canon)


def to_backend_code(lang: str | None, backend: str) -> str | None:
    """Map a canonical (or loose) locale to a backend-native language code.

    Returns ``None`` when the backend doesn't support the language.
    """
    canon = normalize_locale(lang) if lang else None
    if canon is None:
        canon = "en_US"
    if backend == "embedded":
        return canon  # uses whatever the notebook recorded; no constraint
    if backend == "myscript":
        return canon if canon in MYSCRIPT_LOCALES else None
    if backend == "trocr":
        return "en" if canon.startswith("en") else None
    if backend in ("google", "azure"):
        iso = canon.split("_")[0]
        if iso not in CLOUD_HINT_LANGS and canon not in ("zh_CN", "zh_TW", "zh_HK"):
            return None
        return canon.replace("_", "-") if backend == "google" else canon
    if backend == "mathpix":
        iso = canon.split("_")[0]
        if canon == "zh_CN":
            return "zh_s"
        if canon in ("zh_TW", "zh_HK"):
            return "zh_t"
        return iso if iso in MATHPIX_CODES else None
    if backend == "easyocr":
        mapping = {
            "zh_CN": "ch_sim", "zh_TW": "ch_tra", "zh_HK": "ch_tra",
            "sr_RS": "rs_latin", "sr_Cyrl_RS": "rs_cyrillic",
            "nb_NO": "no", "fil_PH": "tl", "tl_PH": "tl", "la_VA": "la",
            "ug_CN": "ug", "tg_TJ": "tjk", "ku_TR": "ku", "as_IN": "as",
            "bho_IN": "bho", "hi_IN": "hi", "ne_NP": "ne", "mr_IN": "mr",
            "sa_IN": "sa", "te_IN": "te", "kn_IN": "kn", "ta_IN": "ta",
            "oc_FR": "oc", "mt_MT": "mt", "mi": "mi",
        }
        if canon in mapping:
            return mapping[canon]
        iso = canon.split("_")[0]
        return iso if iso in EASYOCR_CODES else None
    if backend == "surya":
        if canon == "zh_CN":
            return "zh"
        if canon in ("zh_TW", "zh_HK"):
            return "zh"
        iso = canon.split("_")[0]
        if iso == "nb":
            return "no"
        return iso if iso in SURYA_CODES else None
    if backend == "paddleocr":
        mapping = {
            "zh_CN": "ch", "zh_TW": "chinese_cht", "zh_HK": "chinese_cht",
            "ja_JP": "japan", "ko_KR": "korean",
            "sr_RS": "rs_latin", "sr_Cyrl_RS": "rs_cyrillic",
            "nb_NO": "no", "tl_PH": "tl", "fil_PH": "tl",
            "ug_CN": "ug", "tg_TJ": "tjk", "tt_RU": "tt", "mn_MN": "mn",
            "kk_KZ": "kk", "ky_KG": "ky", "la_VA": "la", "mi": "mi",
            "pi": "pi", "oc_FR": "oc", "hi_IN": "hi", "mr_IN": "mr",
            "ne_NP": "ne", "bho_IN": "bho", "as_IN": "as", "bn_BD": "bn",
            "or_IN": "or", "pa_IN": "pa", "sa_IN": "sa", "ml_IN": "ml",
            "ta_IN": "ta", "te_IN": "te", "kn_IN": "kn", "ka_GE": "ka",
            "hy_AM": "hy", "ur_PK": "ur", "fa_IR": "fa", "ar_SA": "ar",
        }
        if canon in mapping:
            return mapping[canon]
        iso = canon.split("_")[0]
        return iso if iso in PADDLEOCR_CODES else None
    return canon


def supported_languages(backend: str) -> list[str]:
    """Canonical locales the given backend claims to support."""
    out: list[str] = []
    for canon in LANGUAGE_NAMES:
        try:
            if to_backend_code(canon, backend) is not None:
                out.append(canon)
        except ValueError:
            continue
    return out


def backends_for_language(lang: str) -> list[str]:
    """Which backends can handle this locale."""
    from .backends import registry  # local import to avoid a cycle

    canon = normalize_locale(lang) or lang
    return [
        name
        for name in registry()
        if name == "embedded" or to_backend_code(canon, name) is not None
    ]
