"""
Validate Schema Script
Validates the master dataset against the defined JSON schema using jsonschema library.

Features:
- Full JSON Schema validation using jsonschema library
- Detailed error reporting with path information
- Data integrity checks (verse counts, chapter numbering, etc.)
- Statistics and summary report
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple
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
SCHEMA_FILE = CLEANED_DIR / "schema.json"


# ============ JSON Schema Validation ============

def validate_with_jsonschema(data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate data against JSON schema using jsonschema library.

    Args:
        data: Data to validate
        schema: JSON schema

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []

    try:
        from jsonschema import validate, ValidationError, Draft7Validator

        # Create validator
        validator = Draft7Validator(schema)

        # Collect all errors
        for error in validator.iter_errors(data):
            path = " -> ".join(str(p) for p in error.path) if error.path else "root"
            errors.append(f"[{path}] {error.message}")

        return len(errors) == 0, errors

    except ImportError:
        logger.warning("jsonschema library not installed.")
        logger.info("Install with: pip install jsonschema")
        logger.info("Falling back to basic validation...")
        return basic_validate(data)

    except Exception as e:
        errors.append(f"Validation error: {str(e)}")
        return False, errors


def basic_validate(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Basic validation without jsonschema library.

    Args:
        data: Data to validate

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []

    # Check required top-level fields
    if 'metadata' not in data:
        errors.append("Missing required field: metadata")

    if 'chapters' not in data:
        errors.append("Missing required field: chapters")

    # Validate metadata
    metadata = data.get('metadata', {})
    required_metadata = ['title', 'version', 'languages', 'total_chapters', 'total_verses']
    for field in required_metadata:
        if field not in metadata:
            errors.append(f"Missing metadata field: {field}")

    # Validate chapters
    chapters = data.get('chapters', [])
    if not isinstance(chapters, list):
        errors.append("chapters must be an array")
    else:
        for i, chapter in enumerate(chapters):
            ch_errors = validate_chapter(chapter, i)
            errors.extend(ch_errors)

    return len(errors) == 0, errors


def validate_chapter(chapter: Dict[str, Any], index: int) -> List[str]:
    """
    Validate a single chapter.

    Args:
        chapter: Chapter object
        index: Chapter index in array

    Returns:
        List of error messages
    """
    errors = []
    ch_num = chapter.get('chapter_number', f'index_{index}')

    # Check required fields
    if 'chapter_number' not in chapter:
        errors.append(f"Chapter {index}: Missing chapter_number")

    if 'verses' not in chapter:
        errors.append(f"Chapter {ch_num}: Missing verses array")
    elif not isinstance(chapter['verses'], list):
        errors.append(f"Chapter {ch_num}: verses must be an array")
    else:
        # Validate each verse
        for j, verse in enumerate(chapter['verses']):
            v_errors = validate_verse(verse, ch_num, j)
            errors.extend(v_errors)

    return errors


def validate_verse(verse: Dict[str, Any], chapter_num: Any, index: int) -> List[str]:
    """
    Validate a single verse.

    Args:
        verse: Verse object
        chapter_num: Parent chapter number
        index: Verse index in array

    Returns:
        List of error messages
    """
    errors = []
    v_num = verse.get('verse_number', f'index_{index}')
    ref = f"Chapter {chapter_num}, Verse {v_num}"

    # Check required fields
    if 'verse_number' not in verse:
        errors.append(f"{ref}: Missing verse_number")

    # Check that at least one text field exists
    has_text = any([
        verse.get('sanskrit'),
        verse.get('english'),
        verse.get('hindi')
    ])
    if not has_text:
        errors.append(f"{ref}: No text content (sanskrit, english, or hindi)")

    return errors


# ============ Data Integrity Checks ============

def check_data_integrity(data: Dict[str, Any]) -> List[str]:
    """
    Perform data integrity checks beyond schema validation.

    Args:
        data: Dataset to check

    Returns:
        List of integrity issues
    """
    issues = []
    chapters = data.get('chapters', [])
    metadata = data.get('metadata', {})

    # Check chapter count matches metadata
    actual_chapters = len(chapters)
    declared_chapters = metadata.get('total_chapters', 0)
    if actual_chapters != declared_chapters:
        issues.append(
            f"Chapter count mismatch: metadata says {declared_chapters}, "
            f"actual is {actual_chapters}"
        )

    # Check verse count matches metadata
    actual_verses = sum(len(ch.get('verses', [])) for ch in chapters)
    declared_verses = metadata.get('total_verses', 0)
    if actual_verses != declared_verses:
        issues.append(
            f"Verse count mismatch: metadata says {declared_verses}, "
            f"actual is {actual_verses}"
        )

    # Check chapter numbering is sequential
    chapter_numbers = [ch.get('chapter_number', 0) for ch in chapters]
    expected_numbers = list(range(1, len(chapters) + 1))
    if sorted(chapter_numbers) != expected_numbers:
        issues.append(f"Non-sequential chapter numbering: {chapter_numbers}")

    # Check for duplicate verses within chapters
    for chapter in chapters:
        ch_num = chapter.get('chapter_number', '?')
        verse_numbers = [v.get('verse_number', 0) for v in chapter.get('verses', [])]

        if len(verse_numbers) != len(set(verse_numbers)):
            duplicates = [n for n in verse_numbers if verse_numbers.count(n) > 1]
            issues.append(f"Chapter {ch_num}: Duplicate verse numbers: {set(duplicates)}")

    # Check for empty translations
    empty_english = 0
    empty_hindi = 0
    empty_sanskrit = 0

    for chapter in chapters:
        for verse in chapter.get('verses', []):
            if not verse.get('english'):
                empty_english += 1
            if not verse.get('hindi'):
                empty_hindi += 1
            if not verse.get('sanskrit'):
                empty_sanskrit += 1

    if empty_english > 0:
        issues.append(f"Warning: {empty_english} verses missing English translation")
    if empty_hindi > 0:
        issues.append(f"Warning: {empty_hindi} verses missing Hindi translation")
    if empty_sanskrit > 0:
        issues.append(f"Warning: {empty_sanskrit} verses missing Sanskrit text")

    return issues


# ============ Statistics ============

def calculate_statistics(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate statistics about the dataset.

    Args:
        data: Dataset

    Returns:
        Statistics dictionary
    """
    chapters = data.get('chapters', [])

    stats = {
        'total_chapters': len(chapters),
        'total_verses': 0,
        'verses_per_chapter': {},
        'with_english': 0,
        'with_hindi': 0,
        'with_sanskrit': 0,
        'with_commentary': 0,
        'speakers': {}
    }

    for chapter in chapters:
        ch_num = chapter.get('chapter_number', 0)
        verses = chapter.get('verses', [])
        stats['total_verses'] += len(verses)
        stats['verses_per_chapter'][ch_num] = len(verses)

        for verse in verses:
            if verse.get('english'):
                stats['with_english'] += 1
            if verse.get('hindi'):
                stats['with_hindi'] += 1
            if verse.get('sanskrit'):
                stats['with_sanskrit'] += 1

            commentary = verse.get('commentary', {})
            if commentary.get('hindi') or commentary.get('english'):
                stats['with_commentary'] += 1

            speaker = verse.get('speaker', 'Unknown')
            stats['speakers'][speaker] = stats['speakers'].get(speaker, 0) + 1

    return stats


def print_statistics(stats: Dict[str, Any]):
    """Print statistics report."""
    logger.info("\n" + "=" * 60)
    logger.info("DATASET STATISTICS")
    logger.info("=" * 60)

    logger.info(f"\nTotal Chapters: {stats['total_chapters']}")
    logger.info(f"Total Verses: {stats['total_verses']}")

    logger.info(f"\nContent Coverage:")
    logger.info(f"  - With Sanskrit: {stats['with_sanskrit']} ({100*stats['with_sanskrit']/max(stats['total_verses'],1):.1f}%)")
    logger.info(f"  - With English: {stats['with_english']} ({100*stats['with_english']/max(stats['total_verses'],1):.1f}%)")
    logger.info(f"  - With Hindi: {stats['with_hindi']} ({100*stats['with_hindi']/max(stats['total_verses'],1):.1f}%)")
    logger.info(f"  - With Commentary: {stats['with_commentary']} ({100*stats['with_commentary']/max(stats['total_verses'],1):.1f}%)")

    logger.info(f"\nSpeakers Distribution:")
    for speaker, count in sorted(stats['speakers'].items(), key=lambda x: -x[1]):
        logger.info(f"  - {speaker}: {count} verses")

    logger.info(f"\nVerses per Chapter:")
    for ch_num, count in sorted(stats['verses_per_chapter'].items()):
        logger.info(f"  - Chapter {ch_num}: {count} verses")


# ============ Report ============

def print_validation_report(
    schema_valid: bool,
    schema_errors: List[str],
    integrity_issues: List[str]
) -> bool:
    """
    Print comprehensive validation report.

    Args:
        schema_valid: Whether schema validation passed
        schema_errors: List of schema validation errors
        integrity_issues: List of data integrity issues

    Returns:
        True if all validations passed
    """
    logger.info("\n" + "=" * 60)
    logger.info("VALIDATION REPORT")
    logger.info("=" * 60)

    all_passed = True

    # Schema validation results
    if schema_valid:
        logger.info("\n[PASS] Schema Validation: All checks passed")
    else:
        all_passed = False
        logger.error(f"\n[FAIL] Schema Validation: {len(schema_errors)} errors found")
        for error in schema_errors[:15]:
            logger.error(f"  - {error}")
        if len(schema_errors) > 15:
            logger.error(f"  ... and {len(schema_errors) - 15} more errors")

    # Integrity check results
    warnings = [i for i in integrity_issues if i.startswith('Warning:')]
    errors = [i for i in integrity_issues if not i.startswith('Warning:')]

    if not errors:
        logger.info("\n[PASS] Data Integrity: All checks passed")
    else:
        all_passed = False
        logger.error(f"\n[FAIL] Data Integrity: {len(errors)} issues found")
        for issue in errors:
            logger.error(f"  - {issue}")

    if warnings:
        logger.warning(f"\n[WARN] Warnings: {len(warnings)}")
        for warning in warnings:
            logger.warning(f"  - {warning}")

    # Summary
    logger.info("\n" + "=" * 60)
    if all_passed:
        logger.info("[SUCCESS] All validations passed!")
    else:
        logger.error("[FAILED] Some validations failed. Please review the errors above.")
    logger.info("=" * 60)

    return all_passed


# ============ Main ============

def main():
    """Main entry point for schema validation."""
    logger.info("=" * 60)
    logger.info("BHAGAVAD GITA SCHEMA VALIDATOR")
    logger.info("=" * 60)

    # Check files exist
    if not MASTER_FILE.exists():
        logger.error(f"Master file not found: {MASTER_FILE}")
        logger.info("Run merge_datasets.py first to create the master dataset.")
        sys.exit(1)

    # Load master data
    logger.info(f"\nLoading {MASTER_FILE}...")
    with open(MASTER_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Load schema if available
    schema = None
    if SCHEMA_FILE.exists():
        logger.info(f"Loading schema from {SCHEMA_FILE}...")
        with open(SCHEMA_FILE, 'r', encoding='utf-8') as f:
            schema = json.load(f)
    else:
        logger.warning(f"Schema file not found: {SCHEMA_FILE}")
        logger.info("Will perform basic validation only.")

    # Perform validations
    logger.info("\nValidating against schema...")
    if schema:
        schema_valid, schema_errors = validate_with_jsonschema(data, schema)
    else:
        schema_valid, schema_errors = basic_validate(data)

    logger.info("\nChecking data integrity...")
    integrity_issues = check_data_integrity(data)

    # Calculate and print statistics
    stats = calculate_statistics(data)
    print_statistics(stats)

    # Print validation report
    all_passed = print_validation_report(schema_valid, schema_errors, integrity_issues)

    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
