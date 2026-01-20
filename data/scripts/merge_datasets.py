"""
Merge Datasets Script
Joins verses from Sanskrit, English, and Hindi raw files into a unified master dataset.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


# Paths
RAW_DIR = Path(__file__).parent.parent / "raw"
CLEANED_DIR = Path(__file__).parent.parent / "cleaned"
OUTPUT_FILE = CLEANED_DIR / "gita_master.json"
CSV_OUTPUT = CLEANED_DIR / "gita_master.csv"


def load_json(filepath: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    if not filepath.exists():
        print(f"Warning: {filepath} not found")
        return {}

    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def merge_verses(
    sanskrit_data: Dict,
    english_data: Dict,
    hindi_data: Dict
) -> List[Dict[str, Any]]:
    """Merge verses from all three language sources."""
    merged_chapters = []

    # Get chapters from Sanskrit as base (or any available source)
    base_chapters = (
        sanskrit_data.get('chapters', []) or
        english_data.get('chapters', []) or
        hindi_data.get('chapters', [])
    )

    for chapter in base_chapters:
        chapter_num = chapter.get('chapter_number', 0)

        merged_chapter = {
            'chapter_number': chapter_num,
            'chapter_name': {
                'sanskrit': get_chapter_name(sanskrit_data, chapter_num),
                'english': get_chapter_name(english_data, chapter_num),
                'hindi': get_chapter_name(hindi_data, chapter_num)
            },
            'verses': []
        }

        # Merge verses
        verses = chapter.get('verses', [])
        for verse in verses:
            verse_num = verse.get('verse_number', 0)

            merged_verse = {
                'verse_number': verse_num,
                'sanskrit': get_verse_text(sanskrit_data, chapter_num, verse_num),
                'transliteration': get_verse_field(sanskrit_data, chapter_num, verse_num, 'transliteration'),
                'english': get_verse_text(english_data, chapter_num, verse_num),
                'hindi': get_verse_text(hindi_data, chapter_num, verse_num),
                'commentary': {
                    'general': get_verse_field(english_data, chapter_num, verse_num, 'commentary')
                },
                'keywords': extract_keywords(verse),
                'speaker': determine_speaker(verse)
            }

            merged_chapter['verses'].append(merged_verse)

        merged_chapters.append(merged_chapter)

    return merged_chapters


def get_chapter_name(data: Dict, chapter_num: int) -> str:
    """Extract chapter name from data."""
    chapters = data.get('chapters', [])
    for chapter in chapters:
        if chapter.get('chapter_number') == chapter_num:
            return chapter.get('chapter_name', '') or chapter.get('chapter_name_transliterated', '')
    return ''


def get_verse_text(data: Dict, chapter_num: int, verse_num: int) -> str:
    """Extract verse text from data."""
    return get_verse_field(data, chapter_num, verse_num, 'text')


def get_verse_field(data: Dict, chapter_num: int, verse_num: int, field: str) -> str:
    """Extract a specific field from a verse."""
    chapters = data.get('chapters', [])
    for chapter in chapters:
        if chapter.get('chapter_number') == chapter_num:
            verses = chapter.get('verses', [])
            for verse in verses:
                if verse.get('verse_number') == verse_num:
                    return verse.get(field, '')
    return ''


def extract_keywords(verse: Dict) -> List[str]:
    """Extract keywords from verse metadata."""
    return verse.get('keywords', [])


def determine_speaker(verse: Dict) -> str:
    """Determine the speaker of the verse."""
    return verse.get('speaker', 'Unknown')


def create_master_dataset(merged_chapters: List[Dict]) -> Dict[str, Any]:
    """Create the final master dataset structure."""
    total_verses = sum(len(ch.get('verses', [])) for ch in merged_chapters)

    return {
        'metadata': {
            'title': 'Bhagavad Gita - Master Dataset',
            'version': '1.0.0',
            'languages': ['sanskrit', 'english', 'hindi'],
            'total_chapters': len(merged_chapters),
            'total_verses': total_verses,
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        },
        'chapters': merged_chapters
    }


def export_to_csv(master_data: Dict, output_path: Path):
    """Export master dataset to CSV format."""
    import csv

    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'chapter_number', 'verse_number', 'sanskrit_text',
            'english_translation', 'hindi_translation', 'transliteration',
            'commentary', 'keywords'
        ])

        for chapter in master_data.get('chapters', []):
            chapter_num = chapter.get('chapter_number', 0)
            for verse in chapter.get('verses', []):
                writer.writerow([
                    chapter_num,
                    verse.get('verse_number', 0),
                    verse.get('sanskrit', ''),
                    verse.get('english', ''),
                    verse.get('hindi', ''),
                    verse.get('transliteration', ''),
                    verse.get('commentary', {}).get('general', ''),
                    '|'.join(verse.get('keywords', []))
                ])

    print(f"CSV exported to {output_path}")


def main():
    """Main entry point for merging datasets."""
    print("Loading raw datasets...")

    # Load raw data files
    sanskrit_data = load_json(RAW_DIR / "gita_sanskrit_raw.json")
    english_data = load_json(RAW_DIR / "gita_english_raw.json")
    hindi_data = load_json(RAW_DIR / "gita_hindi_raw.json")

    if not any([sanskrit_data, english_data, hindi_data]):
        print("Error: No raw data files found. Please add JSON files to data/raw/")
        return

    print("Merging datasets...")
    merged_chapters = merge_verses(sanskrit_data, english_data, hindi_data)

    print("Creating master dataset...")
    master_data = create_master_dataset(merged_chapters)

    # Ensure output directory exists
    CLEANED_DIR.mkdir(parents=True, exist_ok=True)

    # Save JSON
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(master_data, f, ensure_ascii=False, indent=2)
    print(f"Master JSON saved to {OUTPUT_FILE}")

    # Export CSV
    export_to_csv(master_data, CSV_OUTPUT)

    print(f"Merge complete! {master_data['metadata']['total_verses']} verses processed.")


if __name__ == "__main__":
    main()
