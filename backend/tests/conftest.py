"""
Pytest configuration and shared fixtures.
"""

import sys
from pathlib import Path

import pytest

# Add backend to Python path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))


@pytest.fixture(scope="session")
def test_data_dir():
    """Return path to test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture
def sample_query():
    """Sample query for testing."""
    return "How can I find peace of mind?"


@pytest.fixture
def sample_hindi_query():
    """Sample Hindi query for testing."""
    return "मुझे शांति कैसे मिलेगी?"
