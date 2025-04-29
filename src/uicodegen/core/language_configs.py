"""
Language configuration for translation module
"""

# Available languages for translation
LANGUAGES = [
    {
        "code": "en",
        "name": "English",
        "native_name": "English"
    },
    {
        "code": "en-sa",
        "name": "English (South Asia)",
        "native_name": "English (South Asia)"
    },
    {
        "code": "zh-hant",
        "name": "Traditional Chinese",
        "native_name": "繁體中文"
    },
    {
        "code": "vi",
        "name": "Vietnamese",
        "native_name": "Tiếng Việt"
    },
    {
        "code": "ru",
        "name": "Russian",
        "native_name": "Русский"
    },
    {
        "code": "ja",
        "name": "Japanese",
        "native_name": "日本語"
    },
    {
        "code": "es",
        "name": "Spanish",
        "native_name": "Español"
    },
    {
        "code": "es-co",
        "name": "Spanish (Colombia)",
        "native_name": "Español (Colombia)"
    },
    {
        "code": "es-ar",
        "name": "Spanish (Argentina)",
        "native_name": "Español (Argentina)"
    },
    {
        "code": "id",
        "name": "Indonesian",
        "native_name": "Bahasa"
    },
    {
        "code": "pt",
        "name": "Portuguese",
        "native_name": "Português"
    },
    {
        "code": "de",
        "name": "German",
        "native_name": "Deutsch"
    },
    {
        "code": "th",
        "name": "Thai",
        "native_name": "ภาษาไทย"
    },
    {
        "code": "ar",
        "name": "Arabic",
        "native_name": "العربية"
    },
    {
        "code": "fr",
        "name": "French",
        "native_name": "Français"
    },
    {
        "code": "it",
        "name": "Italian",
        "native_name": "Italiano"
    },
    {
        "code": "uk",
        "name": "Ukrainian",
        "native_name": "Українська"
    },
    {
        "code": "pl",
        "name": "Polish",
        "native_name": "Polski"
    },
    {
        "code": "zh-hans",
        "name": "Simplified Chinese",
        "native_name": "简体中文"
    }
]

# Default source and target languages
DEFAULT_SOURCE_LANGUAGE = "en"
DEFAULT_TARGET_LANGUAGE = "zh-hans"

def get_all_languages():
    """
    Get all available languages
    
    Returns:
        list: List of language dictionaries
    """
    return LANGUAGES

def get_language_by_code(code):
    """
    Get language by code
    
    Args:
        code: Language code
        
    Returns:
        dict: Language dictionary or None if not found
    """
    for lang in LANGUAGES:
        if lang["code"] == code:
            return lang
    return None

def get_language_name(code, use_native=False):
    """
    Get language name by code
    
    Args:
        code: Language code
        use_native: Whether to use native name
        
    Returns:
        str: Language name or code if not found
    """
    lang = get_language_by_code(code)
    if lang:
        return lang["native_name"] if use_native else lang["name"]
    return code
