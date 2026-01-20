"""
Clean Text Script
Removes HTML tags, formatting artifacts, and normalizes text in the dataset.

Features:
- Removes HTML tags using regex
- Removes \\n and \\r characters
- Normalizes whitespace
- Preserves Devanagari (Sanskrit/Hindi) text
- Validates cleaned data quality
"""

import json
import re
import html
from pathlib import Path
from typing import Dict, Any, List
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
CLEANED_DIR = Path(__file__).parent.parent / "cleaned"
MASTER_FILE = CLEANED_DIR / "gita_master.json"


# ============ Text Cleaning Functions ============

def remove_html_tags(text: str) -> str:
    """
    Remove HTML tags from text.

    Args:
        text: Text with potential HTML tags

    Returns:
        Text without HTML tags
    """
    if not text:
        return ""

    # Decode HTML entities first
    text = html.unescape(text)

    # Remove HTML tags (including self-closing tags)
    text = re.sub(r'<[^>]+/?>', '', text)

    # Remove any remaining HTML-like artifacts
    text = re.sub(r'&[a-zA-Z]+;', '', text)  # Named entities
    text = re.sub(r'&#\d+;', '', text)       # Numeric entities

    return text


def remove_newlines(text: str) -> str:
    """
    Remove newline and carriage return characters.

    Args:
        text: Text with newlines

    Returns:
        Text without newlines
    """
    if not text:
        return ""

    # Replace \n and \r with spaces
    text = text.replace('\n', ' ').replace('\r', ' ')

    return text


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text.

    Args:
        text: Text with irregular whitespace

    Returns:
        Text with normalized whitespace
    """
    if not text:
        return ""

    # Replace multiple spaces/tabs with single space
    text = re.sub(r'[ \t]+', ' ', text)

    # Replace multiple newlines with single newline (if we want to preserve structure)
    text = re.sub(r'\n+', '\n', text)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


def remove_special_characters(text: str, preserve_devanagari: bool = True) -> str:
    """
    Remove unwanted special characters while preserving language-specific chars.

    Args:
        text: Input text with possible special characters
        preserve_devanagari: Whether to keep Devanagari (Hindi/Sanskrit) characters

    Returns:
        Cleaned text
    """
    if not text:
        return ""

    if preserve_devanagari:
        # Keep:
        # - Devanagari (U+0900 to U+097F)
        # - Extended Devanagari (U+A8E0 to U+A8FF)
        # - Vedic Extensions (U+1CD0 to U+1CFF)
        # - English letters, numbers, basic punctuation
        pattern = r'[^\u0900-\u097F\uA8E0-\uA8FF\u1CD0-\u1CFFs\u0000-\u007Fa-zA-Z0-9\s.,;:!?\'"()\-–—।॥]'
    else:
        # Keep only English letters, numbers, basic punctuation
        pattern = r'[^a-zA-Z0-9\s.,;:!?\'"()\-]'

    clean = re.sub(pattern, '', text)
    return clean


def clean_text_full(text: str, preserve_devanagari: bool = True) -> str:
    """
    Apply full cleaning pipeline to text.

    Args:
        text: Raw text to clean
        preserve_devanagari: Whether to preserve Devanagari characters

    Returns:
        Fully cleaned text
    """
    if not text:
        return ""

    # 1. Remove HTML tags
    text = remove_html_tags(text)

    # 2. Remove newlines
    text = remove_newlines(text)

    # 3. Normalize whitespace
    text = normalize_whitespace(text)

    return text


def clean_sanskrit_text(text: str) -> str:
    """
    Clean Sanskrit text while preserving verse structure.

    Args:
        text: Sanskrit text

    Returns:
        Cleaned Sanskrit text
    """
    if not text:
        return ""

    # Remove verse numbers in various formats
    text = re.sub(r'॥\s*\d+\s*॥', '', text)          # ॥1॥
    text = re.sub(r'॥\s*\d+\.\d+\s*॥', '', text)     # ॥1.1॥
    text = re.sub(r'\|\|\s*\d+\s*\|\|', '', text)     # ||1||
    text = re.sub(r'\|\|\s*\d+\.\d+\s*\|\|', '', text) # ||1.1||

    # Clean HTML
    text = remove_html_tags(text)

    # Replace double newlines with pipe (verse separator)
    text = re.sub(r'\n\s*\n', ' | ', text)

    # Replace single newlines with space
    text = text.replace('\n', ' ')

    # Normalize whitespace
    text = normalize_whitespace(text)

    return text


# ============ Data Processing ============

def clean_verse(verse: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean all text fields in a verse.

    Args:
        verse: Verse object with text fields

    Returns:
        Cleaned verse object
    """
    cleaned = verse.copy()

    # Text fields to clean
    text_fields = ['transliteration', 'word_meanings', 'english', 'hindi']

    for field in text_fields:
        if field in cleaned and cleaned[field]:
            cleaned[field] = clean_text_full(cleaned[field])

    # Clean Sanskrit separately (preserve structure)
    if 'sanskrit' in cleaned and cleaned['sanskrit']:
        cleaned['sanskrit'] = clean_sanskrit_text(cleaned['sanskrit'])

    # Clean commentary
    if 'commentary' in cleaned and isinstance(cleaned['commentary'], dict):
        for key, value in cleaned['commentary'].items():
            if value:
                cleaned['commentary'][key] = clean_text_full(value)

    return cleaned


def clean_chapter(chapter: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean all verses and text in a chapter.

    Args:
        chapter: Chapter object

    Returns:
        Cleaned chapter object
    """
    cleaned = chapter.copy()

    # Clean chapter names
    if 'chapter_name' in cleaned and isinstance(cleaned['chapter_name'], dict):
        for lang, name in cleaned['chapter_name'].items():
            if name:
                cleaned['chapter_name'][lang] = normalize_whitespace(remove_html_tags(name))

    # Clean chapter summary
    if 'chapter_summary' in cleaned:
        cleaned['chapter_summary'] = clean_text_full(cleaned['chapter_summary'])

    if 'chapter_summary_hindi' in cleaned:
        cleaned['chapter_summary_hindi'] = clean_text_full(cleaned['chapter_summary_hindi'])

    # Clean verses
    if 'verses' in cleaned:
        cleaned['verses'] = [clean_verse(v) for v in cleaned['verses']]

    return cleaned


def clean_master_dataset(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean the entire master dataset.

    Args:
        data: Full master dataset

    Returns:
        Cleaned dataset
    """
    cleaned = data.copy()

    if 'chapters' in cleaned:
        cleaned['chapters'] = [clean_chapter(ch) for ch in cleaned['chapters']]

    # Update metadata
    if 'metadata' in cleaned:
        from datetime import datetime
        cleaned['metadata']['last_updated'] = datetime.now().isoformat()
        cleaned['metadata']['cleaning_applied'] = True

    return cleaned


# ============ Validation ============

def validate_cleaned_data(data: Dict[str, Any]) -> List[str]:
    """
    Validate that cleaned data meets quality standards.

    Args:
        data: Cleaned dataset

    Returns:
        List of validation issues found
    """
    issues = []

    for chapter in data.get('chapters', []):
        chapter_num = chapter.get('chapter_number', '?')

        for verse in chapter.get('verses', []):
            verse_num = verse.get('verse_number', '?')
            ref = f"Chapter {chapter_num}, Verse {verse_num}"

            # Check for empty required fields
            if not verse.get('sanskrit') and not verse.get('english'):
                issues.append(f"{ref}: Missing both Sanskrit and English text")

            # Check for remaining HTML tags
            for field in ['sanskrit', 'english', 'hindi', 'transliteration']:
                text = verse.get(field, '')
                if '<' in text and '>' in text:
                    issues.append(f"{ref}: Possible remaining HTML in '{field}'")

            # Check for remaining newlines
            for field in ['english', 'hindi']:
                text = verse.get(field, '')
                if '\n' in text or '\r' in text:
                    issues.append(f"{ref}: Remaining newlines in '{field}'")

            # Check commentary
            commentary = verse.get('commentary', {})
            for comm_lang, comm_text in commentary.items():
                if comm_text:
                    if '<' in comm_text and '>' in comm_text:
                        issues.append(f"{ref}: Possible HTML in commentary ({comm_lang})")
                    if '\n' in comm_text:
                        issues.append(f"{ref}: Remaining newlines in commentary ({comm_lang})")

    return issues


def print_validation_report(issues: List[str]):
    """Print validation report."""
    logger.info("\n" + "=" * 60)
    logger.info("VALIDATION REPORT")
    logger.info("=" * 60)

    if not issues:
        logger.info("\n[PASS] All validation checks passed!")
        return True

    logger.warning(f"\n[ISSUES] Found {len(issues)} issues:")
    for issue in issues[:20]:
        logger.warning(f"  - {issue}")

    if len(issues) > 20:
        logger.warning(f"  ... and {len(issues) - 20} more issues")

    return False


# ============ Main ============

def main():
    """Main entry point for cleaning text."""
    logger.info("=" * 60)
    logger.info("BHAGAVAD GITA TEXT CLEANER")
    logger.info("=" * 60)

    # Check if master file exists
    if not MASTER_FILE.exists():
        logger.error(f"Master file not found: {MASTER_FILE}")
        logger.info("Run merge_datasets.py first to create the master dataset.")
        return

    # Load data
    logger.info(f"\nLoading {MASTER_FILE}...")
    with open(MASTER_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total_verses = data.get('metadata', {}).get('total_verses', 0)
    logger.info(f"Loaded {total_verses} verses")

    # Clean data
    logger.info("\nCleaning text...")
    cleaned_data = clean_master_dataset(data)

    # Validate
    logger.info("\nValidating cleaned data...")
    issues = validate_cleaned_data(cleaned_data)
    is_valid = print_validation_report(issues)

    # Save cleaned data
    logger.info("\nSaving cleaned data...")
    with open(MASTER_FILE, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, ensure_ascii=False, indent=2)

    logger.info(f"Cleaned data saved to {MASTER_FILE}")

    if is_valid:
        logger.info("\n[SUCCESS] Text cleaning complete with no issues!")
    else:
        logger.warning("\n[WARNING] Text cleaning complete but some issues remain.")
        logger.info("Review the issues above and consider manual fixes if needed.")


if __name__ == "__main__":
    main()
