"""
Text Utilities
Helper functions for text processing.
"""

import re
from typing import List, Optional


def normalize_text(text: str) -> str:
    """
    Normalize text for consistent processing.

    Args:
        text: Input text

    Returns:
        Normalized text
    """
    if not text:
        return ""

    # Normalize whitespace
    text = " ".join(text.split())

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


def truncate_text(text: str, max_length: int = 500, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.

    Args:
        text: Input text
        max_length: Maximum characters
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text

    # Try to break at word boundary
    truncated = text[:max_length - len(suffix)]
    last_space = truncated.rfind(" ")

    if last_space > max_length * 0.7:  # If space is reasonably close to end
        truncated = truncated[:last_space]

    return truncated + suffix


def extract_verse_reference(text: str) -> Optional[tuple]:
    """
    Extract chapter and verse numbers from text.

    Handles formats like:
    - "Chapter 2, Verse 47"
    - "2:47"
    - "2.47"
    - "BG 2.47"

    Args:
        text: Input text

    Returns:
        Tuple of (chapter, verse) or None if not found
    """
    patterns = [
        r"chapter\s*(\d+)[,\s]*verse\s*(\d+)",
        r"ch(?:apter)?\.?\s*(\d+)[\s,.:]+v(?:erse)?\.?\s*(\d+)",
        r"bg\s*(\d+)[.:](\d+)",
        r"(\d+)[.:](\d+)",
    ]

    text_lower = text.lower()

    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            chapter = int(match.group(1))
            verse = int(match.group(2))

            # Validate range
            if 1 <= chapter <= 18 and 1 <= verse <= 78:  # Max verse in any chapter
                return (chapter, verse)

    return None


def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences.

    Args:
        text: Input text

    Returns:
        List of sentences
    """
    if not text:
        return []

    # Split on sentence boundaries
    sentences = re.split(r'(?<=[.!?])\s+', text)

    return [s.strip() for s in sentences if s.strip()]


def remove_diacritics(text: str) -> str:
    """
    Remove diacritical marks from text (for search normalization).

    Args:
        text: Input text with possible diacritics

    Returns:
        Text without diacritics
    """
    import unicodedata

    # Normalize to decomposed form
    normalized = unicodedata.normalize("NFD", text)

    # Remove combining characters (diacritics)
    without_diacritics = "".join(
        char for char in normalized
        if unicodedata.category(char) != "Mn"
    )

    return without_diacritics


def highlight_terms(text: str, terms: List[str], tag: str = "**") -> str:
    """
    Highlight search terms in text.

    Args:
        text: Input text
        terms: Terms to highlight
        tag: Markdown tag for highlighting

    Returns:
        Text with highlighted terms
    """
    if not text or not terms:
        return text

    for term in terms:
        if not term:
            continue

        # Case-insensitive replacement
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        text = pattern.sub(f"{tag}{term}{tag}", text)

    return text


def clean_sanskrit_text(text: str) -> str:
    """
    Clean Sanskrit text by removing common artifacts.

    Args:
        text: Sanskrit text

    Returns:
        Cleaned text
    """
    if not text:
        return ""

    # Remove verse numbers in Devanagari
    text = re.sub(r'॥\d+॥', '', text)
    text = re.sub(r'\|\|\d+\|\|', '', text)

    # Normalize Devanagari punctuation
    text = text.replace('।', '|')

    return normalize_text(text)


def format_verse_for_display(
    chapter: int,
    verse: int,
    sanskrit: str,
    translation: str,
    transliteration: Optional[str] = None,
) -> str:
    """
    Format a verse for display.

    Args:
        chapter: Chapter number
        verse: Verse number
        sanskrit: Sanskrit text
        translation: English/Hindi translation
        transliteration: Optional transliteration

    Returns:
        Formatted string
    """
    parts = [f"**Chapter {chapter}, Verse {verse}**", ""]

    if sanskrit:
        parts.append(f"*{sanskrit}*")
        parts.append("")

    if transliteration:
        parts.append(f"_{transliteration}_")
        parts.append("")

    if translation:
        parts.append(translation)

    return "\n".join(parts)
