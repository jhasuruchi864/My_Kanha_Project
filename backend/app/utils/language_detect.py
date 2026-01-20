"""
Language Detection
Detects whether input is Hindi or English.
"""

import re
from typing import Literal

from app.logger import logger


# Devanagari Unicode range
DEVANAGARI_PATTERN = re.compile(r'[\u0900-\u097F]')

# Common Hindi words for additional detection
HINDI_MARKERS = {
    'क्या', 'कैसे', 'क्यों', 'कहाँ', 'कब', 'कौन',
    'मैं', 'हम', 'तुम', 'आप', 'वह', 'यह',
    'है', 'हैं', 'था', 'थे', 'होगा',
    'में', 'से', 'को', 'के', 'का', 'की',
    'और', 'या', 'लेकिन', 'परन्तु',
    'कृपया', 'धन्यवाद', 'नमस्ते',
}


def detect_language(text: str) -> Literal["hindi", "english"]:
    """
    Detect whether text is primarily Hindi or English.

    Uses Devanagari character detection as the primary method.

    Args:
        text: Input text to analyze

    Returns:
        "hindi" or "english"
    """
    if not text:
        return "english"

    text = text.strip()

    # Count Devanagari characters
    devanagari_chars = len(DEVANAGARI_PATTERN.findall(text))
    total_chars = len(re.findall(r'\S', text))  # Non-whitespace characters

    if total_chars == 0:
        return "english"

    # Calculate ratio
    devanagari_ratio = devanagari_chars / total_chars

    # If more than 30% Devanagari, consider it Hindi
    if devanagari_ratio > 0.3:
        logger.debug(f"Detected Hindi (ratio: {devanagari_ratio:.2f})")
        return "hindi"

    # Check for common Hindi words (for transliterated Hindi)
    words = set(text.lower().split())
    if words.intersection(HINDI_MARKERS):
        logger.debug("Detected Hindi (marker words)")
        return "hindi"

    logger.debug("Detected English")
    return "english"


def detect_language_advanced(text: str) -> dict:
    """
    Advanced language detection with confidence scores.

    Args:
        text: Input text

    Returns:
        Dict with language and confidence
    """
    if not text:
        return {"language": "english", "confidence": 1.0}

    try:
        from langdetect import detect_langs, LangDetectException

        detections = detect_langs(text)

        # Map langdetect codes to our language names
        lang_map = {
            'hi': 'hindi',
            'en': 'english',
            'sa': 'sanskrit',  # Sanskrit sometimes detected
        }

        for detection in detections:
            lang_code = detection.lang
            confidence = detection.prob

            if lang_code in lang_map:
                return {
                    "language": lang_map[lang_code],
                    "confidence": confidence,
                }

        # Default to English if no match
        return {"language": "english", "confidence": 0.5}

    except (ImportError, LangDetectException) as e:
        logger.warning(f"Advanced language detection failed: {e}")

        # Fall back to basic detection
        return {
            "language": detect_language(text),
            "confidence": 0.7,
        }


def contains_devanagari(text: str) -> bool:
    """Check if text contains any Devanagari characters."""
    return bool(DEVANAGARI_PATTERN.search(text))


def get_script_type(text: str) -> str:
    """
    Determine the primary script type of the text.

    Returns:
        "devanagari", "latin", or "mixed"
    """
    if not text:
        return "latin"

    devanagari_count = len(DEVANAGARI_PATTERN.findall(text))
    latin_count = len(re.findall(r'[a-zA-Z]', text))

    if devanagari_count == 0 and latin_count > 0:
        return "latin"
    elif latin_count == 0 and devanagari_count > 0:
        return "devanagari"
    elif devanagari_count > latin_count:
        return "devanagari"
    elif latin_count > devanagari_count:
        return "latin"
    else:
        return "mixed"
