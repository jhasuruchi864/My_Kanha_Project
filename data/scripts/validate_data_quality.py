"""
Data Quality Validation Script
Validates the gita_master.json dataset for completeness and consistency
"""

import json
import logging
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_CLEANED_PATH = PROJECT_ROOT / 'data' / 'cleaned' / 'gita_master.json'
REPORT_PATH = PROJECT_ROOT / 'data' / 'cleaned' / 'data_quality_report.json'

# Expected verse counts per chapter (Bhagavad Gita standard)
EXPECTED_VERSES = {
    1: 47, 2: 72, 3: 43, 4: 42, 5: 29, 6: 47,
    7: 30, 8: 28, 9: 34, 10: 42, 11: 55, 12: 20,
    13: 35, 14: 27, 15: 20, 16: 24, 17: 28, 18: 78
}
EXPECTED_TOTAL_VERSES = 701


class DataQualityValidator:
    """Validate data quality of Bhagavad Gita dataset"""

    def __init__(self):
        self.data = None
        self.report = {
            'timestamp': datetime.now().isoformat(),
            'total_chapters': 0,
            'total_verses': 0,
            'validation_results': {},
            'issues': [],
            'coverage': {},
            'statistics': {}
        }

    def load_data(self) -> bool:
        """Load gita_master.json"""
        try:
            logger.info(f"Loading data from {DATA_CLEANED_PATH}")
            with open(DATA_CLEANED_PATH, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            logger.info("Data loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load data: {str(e)}")
            return False

    def validate_structure(self) -> bool:
        """Validate basic structure of the dataset"""
        logger.info("Validating structure...")
        is_valid = True

        # Check top-level keys
        required_keys = ['metadata', 'chapters']
        for key in required_keys:
            if key not in self.data:
                logger.error(f"Missing required key: {key}")
                self.report['issues'].append(f"Missing required key: {key}")
                is_valid = False

        # Check metadata
        metadata = self.data.get('metadata', {})
        required_meta_keys = ['title', 'total_chapters', 'total_verses']
        for key in required_meta_keys:
            if key not in metadata:
                logger.warning(f"Missing metadata key: {key}")
                self.report['issues'].append(f"Missing metadata key: {key}")

        self.report['validation_results']['structure'] = is_valid
        return is_valid

    def validate_verses(self) -> None:
        """Validate all verses for completeness"""
        logger.info("Validating verses...")

        total_verses = 0
        verses_with_english = 0
        verses_with_commentary = 0
        verses_with_sanskrit = 0
        verses_with_hindi = 0
        verses_with_speaker = 0

        missing_fields = defaultdict(list)
        duplicate_verses = []
        verse_ids = set()

        for chapter in self.data.get('chapters', []):
            chapter_num = chapter.get('chapter_number')

            for verse in chapter.get('verses', []):
                total_verses += 1
                verse_num = verse.get('verse_number')
                verse_id = f"{chapter_num}.{verse_num}"

                # Check for duplicates
                if verse_id in verse_ids:
                    duplicate_verses.append(verse_id)
                verse_ids.add(verse_id)

                # Check English translation
                english = verse.get('english', '')
                if english and english.strip():
                    verses_with_english += 1
                else:
                    missing_fields['english'].append(verse_id)

                # Check commentary
                commentary = verse.get('commentary', {})
                if isinstance(commentary, dict):
                    if commentary.get('hindi', '').strip() or commentary.get('english', '').strip():
                        verses_with_commentary += 1
                    else:
                        missing_fields['commentary'].append(verse_id)
                else:
                    missing_fields['commentary'].append(verse_id)

                # Check Sanskrit
                if verse.get('sanskrit', '').strip():
                    verses_with_sanskrit += 1
                else:
                    missing_fields['sanskrit'].append(verse_id)

                # Check Hindi
                if verse.get('hindi', '').strip():
                    verses_with_hindi += 1
                else:
                    missing_fields['hindi'].append(verse_id)

                # Check speaker
                speaker = verse.get('speaker', '')
                if speaker and speaker.strip() and speaker != 'Unknown':
                    verses_with_speaker += 1
                else:
                    missing_fields['speaker'].append(verse_id)

        # Report results
        self.report['total_verses'] = total_verses
        self.report['statistics'] = {
            'total_verses': total_verses,
            'expected_verses': EXPECTED_TOTAL_VERSES,
            'verses_with_english': verses_with_english,
            'english_coverage': f"{(verses_with_english/total_verses)*100:.1f}%" if total_verses > 0 else "0%",
            'verses_with_hindi': verses_with_hindi,
            'hindi_coverage': f"{(verses_with_hindi/total_verses)*100:.1f}%" if total_verses > 0 else "0%",
            'verses_with_sanskrit': verses_with_sanskrit,
            'sanskrit_coverage': f"{(verses_with_sanskrit/total_verses)*100:.1f}%" if total_verses > 0 else "0%",
            'verses_with_commentary': verses_with_commentary,
            'commentary_coverage': f"{(verses_with_commentary/total_verses)*100:.1f}%" if total_verses > 0 else "0%",
            'verses_with_speaker': verses_with_speaker,
            'duplicate_verses': duplicate_verses if duplicate_verses else None
        }

        # Log issues
        if missing_fields['english']:
            count = len(missing_fields['english'])
            logger.warning(f"Missing English translation in {count} verses")
            self.report['issues'].append(f"Missing English translation: {count} verses")

        if missing_fields['commentary']:
            count = len(missing_fields['commentary'])
            logger.warning(f"Missing commentary in {count} verses")
            self.report['issues'].append(f"Missing commentary: {count} verses")

        if duplicate_verses:
            logger.error(f"Found {len(duplicate_verses)} duplicate verses")
            self.report['issues'].append(f"Duplicate verses found: {duplicate_verses}")

        self.report['validation_results']['verses'] = len(missing_fields['english']) == 0

    def validate_chapters(self) -> None:
        """Validate chapter structure"""
        logger.info("Validating chapters...")

        chapters = self.data.get('chapters', [])
        self.report['total_chapters'] = len(chapters)

        expected_chapters = 18

        if len(chapters) != expected_chapters:
            logger.warning(f"Expected {expected_chapters} chapters, found {len(chapters)}")
            self.report['issues'].append(f"Chapter count mismatch: {len(chapters)} vs {expected_chapters}")

        # Check verses per chapter
        chapter_verse_counts = {}
        for chapter in chapters:
            chapter_num = chapter.get('chapter_number')
            verses = chapter.get('verses', [])
            chapter_verse_counts[chapter_num] = len(verses)

            expected = EXPECTED_VERSES.get(chapter_num, 0)
            if len(verses) != expected:
                logger.warning(f"Chapter {chapter_num}: Expected {expected} verses, found {len(verses)}")
                self.report['issues'].append(f"Chapter {chapter_num}: {len(verses)} vs {expected} verses")

        self.report['coverage']['verses_per_chapter'] = chapter_verse_counts
        self.report['validation_results']['chapters'] = len(chapters) == expected_chapters

    def generate_coverage_report(self) -> None:
        """Generate coverage statistics"""
        logger.info("Generating coverage report...")

        speaker_coverage = defaultdict(int)

        for chapter in self.data.get('chapters', []):
            for verse in chapter.get('verses', []):
                speaker = verse.get('speaker', 'Unknown')
                speaker_coverage[speaker] += 1

        self.report['coverage']['speakers'] = dict(speaker_coverage)

    def run(self) -> bool:
        """Execute the validation pipeline"""
        try:
            logger.info("=" * 60)
            logger.info("BHAGAVAD GITA DATA QUALITY VALIDATOR")
            logger.info("=" * 60)

            # Load and validate
            if not self.load_data():
                return False

            self.validate_structure()
            self.validate_chapters()
            self.validate_verses()
            self.generate_coverage_report()

            # Summary
            all_valid = all(self.report['validation_results'].values())
            stats = self.report['statistics']

            logger.info("")
            logger.info("=" * 60)
            logger.info("VALIDATION SUMMARY")
            logger.info("=" * 60)
            logger.info(f"  Total Chapters: {self.report['total_chapters']}")
            logger.info(f"  Total Verses: {stats.get('total_verses', 0)} (Expected: {EXPECTED_TOTAL_VERSES})")
            logger.info(f"  English Coverage: {stats.get('english_coverage', 'N/A')}")
            logger.info(f"  Hindi Coverage: {stats.get('hindi_coverage', 'N/A')}")
            logger.info(f"  Sanskrit Coverage: {stats.get('sanskrit_coverage', 'N/A')}")
            logger.info(f"  Commentary Coverage: {stats.get('commentary_coverage', 'N/A')}")
            logger.info(f"  Issues Found: {len(self.report['issues'])}")

            logger.info("")
            if not all_valid or self.report['issues']:
                logger.warning("Issues detected:")
                for issue in self.report['issues'][:10]:
                    logger.warning(f"  - {issue}")
                if len(self.report['issues']) > 10:
                    logger.warning(f"  ... and {len(self.report['issues']) - 10} more issues")
            else:
                logger.info("[PASS] All validations passed!")

            logger.info("=" * 60)

            # Save report
            self.save_report()
            return all_valid and len(self.report['issues']) == 0

        except Exception as e:
            logger.error(f"Error during validation: {str(e)}", exc_info=True)
            return False

    def save_report(self) -> None:
        """Save validation report to JSON"""
        try:
            REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(REPORT_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.report, f, indent=2, ensure_ascii=False)
            logger.info(f"Report saved to {REPORT_PATH}")
        except Exception as e:
            logger.error(f"Failed to save report: {str(e)}")


if __name__ == "__main__":
    validator = DataQualityValidator()
    success = validator.run()
    exit(0 if success else 1)
