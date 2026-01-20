"""
Validate Schema Script
Validates the master dataset against the defined JSON schema.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
import sys


# Paths
CLEANED_DIR = Path(__file__).parent.parent / "cleaned"
MASTER_FILE = CLEANED_DIR / "gita_master.json"
SCHEMA_FILE = CLEANED_DIR / "schema.json"


def load_json(filepath: Path) -> Dict[str, Any]:
    """Load a JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_type(value: Any, expected_type: str) -> bool:
    """Validate that a value matches the expected JSON schema type."""
    type_map = {
        'string': str,
        'integer': int,
        'number': (int, float),
        'boolean': bool,
        'array': list,
        'object': dict,
        'null': type(None)
    }

    if expected_type in type_map:
        return isinstance(value, type_map[expected_type])
    return True


def validate_value(
    value: Any,
    schema: Dict[str, Any],
    path: str = ""
) -> List[str]:
    """Recursively validate a value against a schema."""
    errors = []

    # Handle type validation
    schema_type = schema.get('type')
    if schema_type:
        # Handle union types (e.g., ["string", "null"])
        if isinstance(schema_type, list):
            if not any(validate_type(value, t) for t in schema_type):
                errors.append(f"{path}: Expected one of {schema_type}, got {type(value).__name__}")
        else:
            if not validate_type(value, schema_type):
                errors.append(f"{path}: Expected {schema_type}, got {type(value).__name__}")

    # Handle minimum/maximum for numbers
    if isinstance(value, (int, float)):
        if 'minimum' in schema and value < schema['minimum']:
            errors.append(f"{path}: Value {value} is less than minimum {schema['minimum']}")
        if 'maximum' in schema and value > schema['maximum']:
            errors.append(f"{path}: Value {value} is greater than maximum {schema['maximum']}")

    # Handle object properties
    if isinstance(value, dict) and 'properties' in schema:
        # Check required fields
        required = schema.get('required', [])
        for req_field in required:
            if req_field not in value:
                errors.append(f"{path}: Missing required field '{req_field}'")

        # Validate each property
        for prop_name, prop_schema in schema.get('properties', {}).items():
            if prop_name in value:
                prop_path = f"{path}.{prop_name}" if path else prop_name
                errors.extend(validate_value(value[prop_name], prop_schema, prop_path))

    # Handle array items
    if isinstance(value, list) and 'items' in schema:
        for i, item in enumerate(value):
            item_path = f"{path}[{i}]"
            errors.extend(validate_value(item, schema['items'], item_path))

    return errors


def validate_data_integrity(data: Dict[str, Any]) -> List[str]:
    """Perform additional data integrity checks."""
    errors = []

    chapters = data.get('chapters', [])

    # Check chapter numbering
    chapter_numbers = [ch.get('chapter_number') for ch in chapters]
    expected_numbers = list(range(1, len(chapters) + 1))

    if sorted(chapter_numbers) != expected_numbers and chapter_numbers:
        errors.append(f"Chapter numbering is not sequential: {chapter_numbers}")

    # Check for duplicate verses
    for chapter in chapters:
        chapter_num = chapter.get('chapter_number', '?')
        verse_numbers = [v.get('verse_number') for v in chapter.get('verses', [])]

        if len(verse_numbers) != len(set(verse_numbers)):
            errors.append(f"Chapter {chapter_num}: Duplicate verse numbers found")

    # Validate metadata counts
    metadata = data.get('metadata', {})
    actual_chapters = len(chapters)
    actual_verses = sum(len(ch.get('verses', [])) for ch in chapters)

    if metadata.get('total_chapters') != actual_chapters:
        errors.append(
            f"Metadata total_chapters ({metadata.get('total_chapters')}) "
            f"doesn't match actual ({actual_chapters})"
        )

    if metadata.get('total_verses') != actual_verses:
        errors.append(
            f"Metadata total_verses ({metadata.get('total_verses')}) "
            f"doesn't match actual ({actual_verses})"
        )

    return errors


def print_validation_report(
    schema_errors: List[str],
    integrity_errors: List[str]
):
    """Print a formatted validation report."""
    print("\n" + "=" * 60)
    print("VALIDATION REPORT")
    print("=" * 60)

    if not schema_errors and not integrity_errors:
        print("\n[PASS] All validations passed successfully!")
        return True

    if schema_errors:
        print(f"\n[SCHEMA ERRORS] Found {len(schema_errors)} schema violations:")
        for error in schema_errors[:20]:
            print(f"  - {error}")
        if len(schema_errors) > 20:
            print(f"  ... and {len(schema_errors) - 20} more errors")

    if integrity_errors:
        print(f"\n[INTEGRITY ERRORS] Found {len(integrity_errors)} data integrity issues:")
        for error in integrity_errors:
            print(f"  - {error}")

    print("\n" + "=" * 60)
    return False


def main():
    """Main entry point for schema validation."""
    print("Loading files...")

    # Check files exist
    if not MASTER_FILE.exists():
        print(f"Error: {MASTER_FILE} not found")
        sys.exit(1)

    if not SCHEMA_FILE.exists():
        print(f"Error: {SCHEMA_FILE} not found")
        sys.exit(1)

    # Load files
    data = load_json(MASTER_FILE)
    schema = load_json(SCHEMA_FILE)

    print("Validating against schema...")
    schema_errors = validate_value(data, schema)

    print("Checking data integrity...")
    integrity_errors = validate_data_integrity(data)

    # Print report
    is_valid = print_validation_report(schema_errors, integrity_errors)

    # Exit with appropriate code
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
