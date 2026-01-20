"""
Clean Text Script
Removes HTML tags, formatting artifacts, and normalizes text in the dataset.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any
import html


# Paths
CLEANED_DIR = Path(__file__).parent.parent / "cleaned"
MASTER_FILE = CLEANED_DIR / "gita_master.json"


def remove_html_tags(text: str) -> str:
    """Remove HTML tags from text."""
    if not text:
        return ""

    # Decode HTML entities
    text = html.unescape(text)

    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', text)

    return clean


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in text."""
    if not text:
        return ""

    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


def remove_special_characters(text: str, preserve_devanagari: bool = True) -> str:
    """Remove unwanted special characters while preserving language-specific chars."""
    if not text:
        return ""

    if preserve_devanagari:
        # Keep Devanagari (Hindi/Sanskrit), English letters, numbers, basic punctuation
        pattern = r'[^\u0900-\u097F\u0A00-\u0A7Fa-zA-Z0-9\s.,;:!?\'"()-]'
    else:
        # Keep only English letters, numbers, basic punctuation
        pattern = r'[^a-zA-Z0-9\s.,;:!?\'"()-]'

    clean = re.sub(pattern, '', text)
    return clean


def clean_verse(verse: Dict[str, Any]) -> Dict[str, Any]:
    """Clean all text fields in a verse."""
    cleaned = verse.copy()

    # Clean text fields
    text_fields = ['sanskrit', 'transliteration', 'english', 'hindi']
    for field in text_fields:
        if field in cleaned and cleaned[field]:
            text = cleaned[field]
            text = remove_html_tags(text)
            text = normalize_whitespace(text)
            # Preserve Devanagari for Sanskrit and Hindi
            if field in ['sanskrit', 'hindi']:
                text = remove_special_characters(text, preserve_devanagari=True)
            cleaned[field] = text

    # Clean commentary
    if 'commentary' in cleaned and isinstance(cleaned['commentary'], dict):
        for key, value in cleaned['commentary'].items():
            if value:
                value = remove_html_tags(value)
                value = normalize_whitespace(value)
                cleaned['commentary'][key] = value

    return cleaned


def clean_chapter(chapter: Dict[str, Any]) -> Dict[str, Any]:
    """Clean all verses in a chapter."""
    cleaned = chapter.copy()

    # Clean chapter names
    if 'chapter_name' in cleaned and isinstance(cleaned['chapter_name'], dict):
        for lang, name in cleaned['chapter_name'].items():
            if name:
                cleaned['chapter_name'][lang] = normalize_whitespace(remove_html_tags(name))

    # Clean verses
    if 'verses' in cleaned:
        cleaned['verses'] = [clean_verse(v) for v in cleaned['verses']]

    return cleaned


def clean_master_dataset(data: Dict[str, Any]) -> Dict[str, Any]:
    """Clean the entire master dataset."""
    cleaned = data.copy()

    if 'chapters' in cleaned:
        cleaned['chapters'] = [clean_chapter(ch) for ch in cleaned['chapters']]

    return cleaned


def validate_cleaned_data(data: Dict[str, Any]) -> bool:
    """Validate that cleaned data meets quality standards."""
    issues = []

    for chapter in data.get('chapters', []):
        chapter_num = chapter.get('chapter_number', '?')

        for verse in chapter.get('verses', []):
            verse_num = verse.get('verse_number', '?')

            # Check for empty required fields
            if not verse.get('sanskrit') and not verse.get('english'):
                issues.append(f"Chapter {chapter_num}, Verse {verse_num}: Missing both Sanskrit and English text")

            # Check for remaining HTML
            for field in ['sanskrit', 'english', 'hindi']:
                text = verse.get(field, '')
                if '<' in text or '>' in text:
                    issues.append(f"Chapter {chapter_num}, Verse {verse_num}: Possible HTML in {field}")

    if issues:
        print("Validation issues found:")
        for issue in issues[:10]:  # Show first 10
            print(f"  - {issue}")
        if len(issues) > 10:
            print(f"  ... and {len(issues) - 10} more issues")
        return False

    return True


def main():
    """Main entry point for cleaning text."""
    print("Loading master dataset...")

    if not MASTER_FILE.exists():
        print(f"Error: {MASTER_FILE} not found. Run merge_datasets.py first.")
        return

    with open(MASTER_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("Cleaning text...")
    cleaned_data = clean_master_dataset(data)

    print("Validating cleaned data...")
    is_valid = validate_cleaned_data(cleaned_data)

    # Save cleaned data
    with open(MASTER_FILE, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, ensure_ascii=False, indent=2)

    print(f"Cleaned data saved to {MASTER_FILE}")

    if is_valid:
        print("All validation checks passed!")
    else:
        print("Warning: Some validation issues were found. Please review.")


if __name__ == "__main__":
    main()
