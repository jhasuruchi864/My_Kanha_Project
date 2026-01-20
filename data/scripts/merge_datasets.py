"""
Merge Datasets Script
Joins verses, translations, and commentary into a unified master dataset.

Features:
- Filters translations by author_id (English: 16 Swami Sivananda, Hindi: 1 Swami Ramsukhdas)
- Filters commentary by author_id (Hindi: 1 Swami Ramsukhdas)
- Cleans text (removes \\n, \\r, HTML tags)
- Validates against schema.json
- Robust error handling
"""

import json
import re
import html
import csv
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
from jsonschema.exceptions import ValidationError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
RAW_DIR = Path(__file__).parent.parent / "raw"
CLEANED_DIR = Path(__file__).parent.parent / "cleaned"
OUTPUT_FILE = CLEANED_DIR / "gita_master.json"
CSV_OUTPUT = CLEANED_DIR / "gita_master.csv"
SCHEMA_FILE = CLEANED_DIR / "schema.json"

# Author IDs for filtering
ENGLISH_AUTHOR_ID = 16  # Swami Sivananda
HINDI_AUTHOR_ID = 1     # Swami Ramsukhdas


# ============ Text Cleaning Utilities ============

def clean_text(text: str) -> str:
    """
    Clean text by removing newlines, carriage returns, and HTML tags.

    Args:
        text: Raw text to clean

    Returns:
        Cleaned text
    """
    if not text:
        return ""

    # Decode HTML entities
    text = html.unescape(text)

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Replace \n and \r with spaces
    text = text.replace('\n', ' ').replace('\r', ' ')

    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


def clean_sanskrit_text(text: str) -> str:
    """
    Clean Sanskrit text while preserving Devanagari formatting.

    Args:
        text: Raw Sanskrit text

    Returns:
        Cleaned Sanskrit text
    """
    if not text:
        return ""

    # Remove verse number markers like ||1.1||
    text = re.sub(r'\|\|\d+\.\d+\|\|', '', text)
    text = re.sub(r'।।\d+\.\d+।।', '', text)

    # Replace \n with space but preserve verse structure
    text = text.replace('\n\n', ' | ').replace('\n', ' ')

    # Clean up extra spaces
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


# ============ Data Loading ============

def load_json(filepath: Path) -> Any:
    """
    Load a JSON file with error handling.

    Args:
        filepath: Path to JSON file

    Returns:
        Parsed JSON data or empty list/dict on error
    """
    if not filepath.exists():
        logger.warning(f"File not found: {filepath}")
        return []

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.info(f"Loaded {filepath.name}: {len(data) if isinstance(data, list) else 'object'} items")
            return data
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in {filepath}: {e}")
        return []
    except Exception as e:
        logger.error(f"Error loading {filepath}: {e}")
        return []


# ============ Data Processing ============

def build_translation_index(translations: List[Dict]) -> Dict[int, Dict[str, str]]:
    """
    Build an index of translations by verse_id, filtered by author.

    Args:
        translations: List of translation objects

    Returns:
        Dict mapping verse_id to {english: str, hindi: str}
    """
    index: Dict[int, Dict[str, str]] = {}

    for trans in translations:
        verse_id = trans.get('verse_id')
        author_id = trans.get('author_id')
        description = trans.get('description', '')
        lang = trans.get('lang', '').lower()

        if not verse_id:
            continue

        if verse_id not in index:
            index[verse_id] = {'english': '', 'hindi': ''}

        # Filter by author_id
        if lang == 'english' and author_id == ENGLISH_AUTHOR_ID:
            index[verse_id]['english'] = clean_text(description)
            logger.debug(f"Verse {verse_id}: Added English translation (Swami Sivananda)")
        elif lang == 'hindi' and author_id == HINDI_AUTHOR_ID:
            index[verse_id]['hindi'] = clean_text(description)
            logger.debug(f"Verse {verse_id}: Added Hindi translation (Swami Ramsukhdas)")

    return index


def build_commentary_index(commentaries: List[Dict]) -> Dict[int, Dict[str, str]]:
    """
    Build an index of commentary by verse_id, filtered by author.

    Args:
        commentaries: List of commentary objects

    Returns:
        Dict mapping verse_id to {hindi: str, english: str}
    """
    index: Dict[int, Dict[str, str]] = {}

    for comm in commentaries:
        verse_id = comm.get('verse_id')
        author_id = comm.get('author_id')
        description = comm.get('description', '')
        lang = comm.get('lang', '').lower()

        if not verse_id:
            continue

        if verse_id not in index:
            index[verse_id] = {'hindi': '', 'english': ''}

        # Filter commentary by author_id (primarily Swami Ramsukhdas for Hindi)
        if lang == 'hindi' and author_id == HINDI_AUTHOR_ID:
            index[verse_id]['hindi'] = clean_text(description)
        elif lang == 'english' and author_id == ENGLISH_AUTHOR_ID:
            index[verse_id]['english'] = clean_text(description)

    return index


def build_chapter_index(chapters: List[Dict]) -> Dict[int, Dict]:
    """
    Build an index of chapters by chapter_number.

    Args:
        chapters: List of chapter objects

    Returns:
        Dict mapping chapter_number to chapter data
    """
    index = {}

    for ch in chapters:
        ch_num = ch.get('chapter_number')
        if ch_num:
            index[ch_num] = {
                'name_sanskrit': ch.get('name', ''),
                'name_english': ch.get('name_translation', ''),
                'name_transliterated': ch.get('name_transliterated', ''),
                'name_meaning': ch.get('name_meaning', ''),
                'summary_english': clean_text(ch.get('chapter_summary', '')),
                'summary_hindi': clean_text(ch.get('chapter_summary_hindi', '')),
                'verses_count': ch.get('verses_count', 0)
            }

    return index


def determine_speaker(verse_text: str) -> str:
    """
    Determine the speaker based on verse text patterns.

    Args:
        verse_text: Sanskrit verse text

    Returns:
        Speaker name
    """
    if not verse_text:
        return "Unknown"

    text_lower = verse_text.lower()

    if 'धृतराष्ट्र उवाच' in verse_text or 'dhṛitarāśhtra uvācha' in text_lower:
        return "Dhritarashtra"
    elif 'सञ्जय उवाच' in verse_text or 'sañjaya uvācha' in text_lower:
        return "Sanjaya"
    elif 'अर्जुन उवाच' in verse_text or 'arjuna uvācha' in text_lower:
        return "Arjuna"
    elif 'श्रीभगवानुवाच' in verse_text or 'śhrī bhagavān uvācha' in text_lower:
        return "Krishna"

    return "Krishna"  # Default speaker for most verses


def merge_data(
    verses: List[Dict],
    translation_index: Dict[int, Dict[str, str]],
    commentary_index: Dict[int, Dict[str, str]],
    chapter_index: Dict[int, Dict]
) -> List[Dict]:
    """
    Merge all data sources into chapter-wise structure.

    Args:
        verses: List of verse objects
        translation_index: Translations indexed by verse_id
        commentary_index: Commentary indexed by verse_id
        chapter_index: Chapters indexed by chapter_number

    Returns:
        List of merged chapter objects
    """
    # Group verses by chapter
    chapters_dict: Dict[int, List[Dict]] = {}

    for verse in verses:
        chapter_num = verse.get('chapter_number', 0)
        verse_id = verse.get('id')
        verse_num = verse.get('verse_number', 0)

        if not chapter_num or not verse_id:
            logger.warning(f"Skipping verse with missing data: {verse}")
            continue

        if chapter_num not in chapters_dict:
            chapters_dict[chapter_num] = []

        # Get translations
        translations = translation_index.get(verse_id, {})

        # Get commentary
        commentary = commentary_index.get(verse_id, {})

        # Build merged verse
        merged_verse = {
            'verse_number': verse_num,
            'sanskrit': clean_sanskrit_text(verse.get('text', '')),
            'transliteration': clean_text(verse.get('transliteration', '')),
            'word_meanings': clean_text(verse.get('word_meanings', '')),
            'english': translations.get('english', ''),
            'hindi': translations.get('hindi', ''),
            'commentary': {
                'hindi': commentary.get('hindi', ''),
                'english': commentary.get('english', '')
            },
            'speaker': determine_speaker(verse.get('text', '')),
            'keywords': []  # Can be populated later
        }

        chapters_dict[chapter_num].append(merged_verse)

    # Build final chapter list
    merged_chapters = []

    for ch_num in sorted(chapters_dict.keys()):
        ch_info = chapter_index.get(ch_num, {})

        # Sort verses by verse_number
        verses_sorted = sorted(chapters_dict[ch_num], key=lambda v: v.get('verse_number', 0))

        chapter = {
            'chapter_number': ch_num,
            'chapter_name': {
                'sanskrit': ch_info.get('name_sanskrit', ''),
                'english': ch_info.get('name_english', ''),
                'hindi': ch_info.get('name_sanskrit', ''),  # Use Sanskrit for Hindi name
                'transliterated': ch_info.get('name_transliterated', ''),
                'meaning': ch_info.get('name_meaning', '')
            },
            'chapter_summary': ch_info.get('summary_english', ''),
            'chapter_summary_hindi': ch_info.get('summary_hindi', ''),
            'verses': verses_sorted
        }

        merged_chapters.append(chapter)
        logger.info(f"Chapter {ch_num}: {len(verses_sorted)} verses merged")

    return merged_chapters


def create_master_dataset(merged_chapters: List[Dict]) -> Dict[str, Any]:
    """
    Create the final master dataset structure.

    Args:
        merged_chapters: List of merged chapter objects

    Returns:
        Complete master dataset
    """
    total_verses = sum(len(ch.get('verses', [])) for ch in merged_chapters)

    return {
        'metadata': {
            'title': 'Bhagavad Gita - Master Dataset',
            'version': '1.0.0',
            'languages': ['sanskrit', 'english', 'hindi'],
            'total_chapters': len(merged_chapters),
            'total_verses': total_verses,
            'sources': {
                'english_translation': 'Swami Sivananda (author_id: 16)',
                'hindi_translation': 'Swami Ramsukhdas (author_id: 1)',
                'commentary': 'Swami Ramsukhdas (author_id: 1)'
            },
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        },
        'chapters': merged_chapters
    }


# ============ Export Functions ============

def export_to_csv(master_data: Dict, output_path: Path):
    """
    Export master dataset to CSV format.

    Args:
        master_data: Master dataset
        output_path: Output CSV file path
    """
    try:
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'chapter_number', 'verse_number', 'sanskrit_text',
                'transliteration', 'word_meanings',
                'english_translation', 'hindi_translation',
                'commentary_english', 'commentary_hindi',
                'speaker', 'keywords'
            ])

            for chapter in master_data.get('chapters', []):
                chapter_num = chapter.get('chapter_number', 0)
                for verse in chapter.get('verses', []):
                    commentary = verse.get('commentary', {})
                    writer.writerow([
                        chapter_num,
                        verse.get('verse_number', 0),
                        verse.get('sanskrit', ''),
                        verse.get('transliteration', ''),
                        verse.get('word_meanings', ''),
                        verse.get('english', ''),
                        verse.get('hindi', ''),
                        commentary.get('english', ''),
                        commentary.get('hindi', ''),
                        verse.get('speaker', ''),
                        '|'.join(verse.get('keywords', []))
                    ])

        logger.info(f"CSV exported to {output_path}")

    except Exception as e:
        logger.error(f"Error exporting CSV: {e}")


def validate_against_schema(data: Dict, schema_path: Path) -> bool:
    """
    Validate data against JSON schema.

    Args:
        data: Data to validate
        schema_path: Path to schema file

    Returns:
        True if valid, False otherwise
    """
    try:
        from jsonschema import validate

        if not schema_path.exists():
            logger.warning(f"Schema file not found: {schema_path}")
            return True  # Skip validation if no schema

        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)

        validate(instance=data, schema=schema)
        logger.info("Schema validation passed!")
        return True

    except ImportError:
        logger.warning("jsonschema not installed. Skipping validation.")
        logger.info("Install with: pip install jsonschema")
        return True

    except ValidationError as e:
        logger.error(f"Schema validation failed: {e.message}")
        logger.error(f"Path: {' -> '.join(map(str, e.path))}")
        return False

    except Exception as e:
        logger.error(f"Validation error: {e}")
        return False


# ============ Main Entry Point ============

def main():
    """Main entry point for merging datasets."""
    logger.info("=" * 60)
    logger.info("BHAGAVAD GITA DATASET MERGER")
    logger.info("=" * 60)

    # Load raw data files
    logger.info("\nLoading raw datasets...")

    verses = load_json(RAW_DIR / "verse.json")
    translations = load_json(RAW_DIR / "translation.json")
    commentaries = load_json(RAW_DIR / "commentary.json")
    chapters = load_json(RAW_DIR / "chapters.json")

    # Validate we have data
    if not verses:
        logger.error("No verses found. Please add verse.json to data/raw/")
        sys.exit(1)

    # Build indexes
    logger.info("\nBuilding indexes...")
    logger.info(f"Filtering translations: English (author_id={ENGLISH_AUTHOR_ID}), Hindi (author_id={HINDI_AUTHOR_ID})")

    translation_index = build_translation_index(translations)
    commentary_index = build_commentary_index(commentaries)
    chapter_index = build_chapter_index(chapters)

    logger.info(f"Translation index: {len(translation_index)} verses")
    logger.info(f"Commentary index: {len(commentary_index)} verses")
    logger.info(f"Chapter index: {len(chapter_index)} chapters")

    # Merge data
    logger.info("\nMerging datasets...")
    merged_chapters = merge_data(verses, translation_index, commentary_index, chapter_index)

    # Create master dataset
    logger.info("\nCreating master dataset...")
    master_data = create_master_dataset(merged_chapters)

    # Ensure output directory exists
    CLEANED_DIR.mkdir(parents=True, exist_ok=True)

    # Validate against schema
    logger.info("\nValidating against schema...")
    is_valid = validate_against_schema(master_data, SCHEMA_FILE)

    if not is_valid:
        logger.warning("Proceeding despite validation errors...")

    # Save JSON
    logger.info("\nSaving outputs...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(master_data, f, ensure_ascii=False, indent=2)
    logger.info(f"Master JSON saved to {OUTPUT_FILE}")

    # Export CSV
    export_to_csv(master_data, CSV_OUTPUT)

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("MERGE COMPLETE!")
    logger.info("=" * 60)
    logger.info(f"Total Chapters: {master_data['metadata']['total_chapters']}")
    logger.info(f"Total Verses: {master_data['metadata']['total_verses']}")
    logger.info(f"Output JSON: {OUTPUT_FILE}")
    logger.info(f"Output CSV: {CSV_OUTPUT}")


if __name__ == "__main__":
    main()
