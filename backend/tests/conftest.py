"""
Pytest configuration and shared fixtures.
"""

import sys
from pathlib import Path
import os
import pytest

# Add backend to Python path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Setup test database before running tests."""
    # Use a separate test database
    os.environ["DB_PATH"] = "./data/users/test_users.db"
    from app.core.auth_service import init_db
    import sqlite3
    
    # Remove old test database if exists
    db_path = Path("./data/users/test_users.db")
    if db_path.exists():
        db_path.unlink()
    
    # Initialize fresh database
    init_db()
    
    yield
    
    # Cleanup after all tests
    if db_path.exists():
        db_path.unlink()


@pytest.fixture(scope="function", autouse=True)
def cleanup_test_db():
    """Cleanup database between tests to avoid locks."""
    yield
    # Give time for connections to close
    import time
    time.sleep(0.1)


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
