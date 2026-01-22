"""
Tests for admin endpoints.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def api_key():
    """Return configured API key or test key."""
    return settings.API_KEY or "test-api-key"


@pytest.fixture
def auth_headers(api_key):
    """Return headers with API key."""
    return {"X-API-Key": api_key}


class TestAdminAuth:
    """Test admin endpoint authentication."""

    def test_stats_without_key_returns_401(self, client):
        """Stats endpoint requires API key when not in debug mode."""
        with patch.object(settings, "DEBUG", False):
            with patch.object(settings, "API_KEY", "test-key"):
                response = client.get("/admin/stats")
                assert response.status_code == 401

    def test_stats_with_wrong_key_returns_401(self, client):
        """Stats endpoint rejects wrong API key."""
        with patch.object(settings, "API_KEY", "correct-key"):
            response = client.get(
                "/admin/stats",
                headers={"X-API-Key": "wrong-key"}
            )
            assert response.status_code == 401

    def test_stats_with_correct_key_succeeds(self, client):
        """Stats endpoint accepts correct API key."""
        with patch.object(settings, "API_KEY", "test-key"):
            with patch("app.api.routes_admin.get_collection_stats") as mock_stats:
                mock_stats.return_value = {
                    "status": "healthy",
                    "total_verses_indexed": 701,
                    "vector_db_path": "/path/to/db",
                    "collection_name": "gita_verses",
                    "last_index_time": "2024-01-01T00:00:00",
                    "embedding_model": "test-model",
                    "ollama_model": "llama3",
                    "error": None,
                }
                response = client.get(
                    "/admin/stats",
                    headers={"X-API-Key": "test-key"}
                )
                assert response.status_code == 200


class TestStatsEndpoint:
    """Test /admin/stats endpoint."""

    def test_stats_returns_collection_info(self, client, auth_headers):
        """Stats endpoint returns collection information."""
        with patch.object(settings, "API_KEY", auth_headers.get("X-API-Key", "")):
            with patch.object(settings, "DEBUG", True):
                with patch("app.api.routes_admin.get_collection_stats") as mock_stats:
                    mock_stats.return_value = {
                        "status": "healthy",
                        "total_verses_indexed": 701,
                        "vector_db_path": "/test/path",
                        "collection_name": "gita_verses",
                        "last_index_time": "2024-01-15T12:00:00",
                        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                        "ollama_model": "llama3",
                        "error": None,
                    }

                    response = client.get("/admin/stats", headers=auth_headers)

                    assert response.status_code == 200
                    data = response.json()
                    assert data["status"] == "healthy"
                    assert data["total_verses_indexed"] == 701
                    assert data["collection_name"] == "gita_verses"


class TestLLMStatusEndpoint:
    """Test /admin/llm-status endpoint."""

    def test_llm_status_when_ollama_reachable(self, client, auth_headers):
        """LLM status returns info when Ollama is reachable."""
        with patch.object(settings, "API_KEY", auth_headers.get("X-API-Key", "")):
            with patch.object(settings, "DEBUG", True):
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "models": [
                        {"name": "llama3:latest"},
                        {"name": "mistral:latest"},
                    ]
                }

                with patch("httpx.AsyncClient") as mock_client:
                    mock_instance = AsyncMock()
                    mock_instance.get.return_value = mock_response
                    mock_instance.__aenter__.return_value = mock_instance
                    mock_instance.__aexit__.return_value = None
                    mock_client.return_value = mock_instance

                    response = client.get("/admin/llm-status", headers=auth_headers)

                    assert response.status_code == 200
                    data = response.json()
                    assert data["reachable"] is True
                    assert "llama3:latest" in data["available_models"]

    def test_llm_status_when_ollama_unreachable(self, client, auth_headers):
        """LLM status handles unreachable Ollama."""
        import httpx

        with patch.object(settings, "API_KEY", auth_headers.get("X-API-Key", "")):
            with patch.object(settings, "DEBUG", True):
                with patch("httpx.AsyncClient") as mock_client:
                    mock_instance = AsyncMock()
                    mock_instance.get.side_effect = httpx.ConnectError("Connection refused")
                    mock_instance.__aenter__.return_value = mock_instance
                    mock_instance.__aexit__.return_value = None
                    mock_client.return_value = mock_instance

                    response = client.get("/admin/llm-status", headers=auth_headers)

                    assert response.status_code == 200
                    data = response.json()
                    assert data["reachable"] is False
                    assert "error" in data


class TestReindexEndpoint:
    """Test /admin/reindex endpoint."""

    def test_reindex_success(self, client, auth_headers):
        """Reindex endpoint triggers indexing."""
        with patch.object(settings, "API_KEY", auth_headers.get("X-API-Key", "")):
            with patch.object(settings, "DEBUG", True):
                with patch("app.api.routes_admin.reindex") as mock_reindex:
                    mock_reindex.return_value = {
                        "success": True,
                        "docs_indexed": 701,
                        "duration_seconds": 45.5,
                        "embedding_model": "test-model",
                        "persist_dir": "/test/path",
                        "last_index_time": "2024-01-15T12:00:00",
                        "error": None,
                    }

                    response = client.post("/admin/reindex", headers=auth_headers)

                    assert response.status_code == 200
                    data = response.json()
                    assert data["status"] == "success"
                    assert data["docs_indexed"] == 701

    def test_reindex_failure(self, client, auth_headers):
        """Reindex endpoint handles failures."""
        with patch.object(settings, "API_KEY", auth_headers.get("X-API-Key", "")):
            with patch.object(settings, "DEBUG", True):
                with patch("app.api.routes_admin.reindex") as mock_reindex:
                    mock_reindex.return_value = {
                        "success": False,
                        "docs_indexed": 0,
                        "duration_seconds": 1.0,
                        "embedding_model": "test-model",
                        "persist_dir": "/test/path",
                        "last_index_time": None,
                        "error": "Data file not found",
                    }

                    response = client.post("/admin/reindex", headers=auth_headers)

                    assert response.status_code == 500


class TestClearCacheEndpoint:
    """Test /admin/clear-cache endpoint."""

    def test_clear_cache_success(self, client, auth_headers):
        """Clear cache endpoint works."""
        with patch.object(settings, "API_KEY", auth_headers.get("X-API-Key", "")):
            with patch.object(settings, "DEBUG", True):
                response = client.post("/admin/clear-cache", headers=auth_headers)

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "success"


class TestStatusEndpoint:
    """Test /admin/status endpoint."""

    def test_status_returns_system_info(self, client, auth_headers):
        """Status endpoint returns system information."""
        with patch.object(settings, "API_KEY", auth_headers.get("X-API-Key", "")):
            with patch.object(settings, "DEBUG", True):
                with patch("app.api.routes_admin.get_ingestion_status") as mock_status:
                    mock_status.return_value = {"status": "idle"}

                    response = client.get("/admin/status", headers=auth_headers)

                    assert response.status_code == 200
                    data = response.json()
                    assert "system" in data
                    assert data["system"]["app_name"] == settings.APP_NAME
