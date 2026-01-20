"""
Tests for RAG retrieval functionality.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from app.rag.retriever import retrieve_relevant_verses, retrieve_by_reference
from app.models.verse_models import VerseSource


@pytest.fixture
def mock_vector_store():
    """Create a mock vector store."""
    mock_vs = Mock()
    mock_vs.query.return_value = {
        "ids": [["ch2_v47", "ch2_v48"]],
        "documents": [["doc1", "doc2"]],
        "metadatas": [[
            {
                "chapter": 2,
                "verse": 47,
                "sanskrit": "कर्मण्येवाधिकारस्ते...",
                "english": "You have the right to work only...",
                "hindi": "कर्म करने में ही तुम्हारा अधिकार है...",
            },
            {
                "chapter": 2,
                "verse": 48,
                "sanskrit": "योगस्थः कुरु कर्माणि...",
                "english": "Perform action being steadfast in Yoga...",
                "hindi": "योग में स्थित होकर कर्म करो...",
            },
        ]],
        "distances": [[0.2, 0.3]],
    }
    return mock_vs


@pytest.fixture
def mock_embedding_fn():
    """Create a mock embedding function."""
    def embedding_fn(texts):
        return [[0.1] * 384 for _ in texts]
    return embedding_fn


class TestRetrieveRelevantVerses:
    """Tests for retrieve_relevant_verses function."""

    @pytest.mark.asyncio
    async def test_retrieves_verses_successfully(
        self, mock_vector_store, mock_embedding_fn
    ):
        """Test successful verse retrieval."""
        with patch("app.rag.retriever.get_vector_store", return_value=mock_vector_store):
            with patch("app.rag.retriever.get_embedding_function", return_value=mock_embedding_fn):
                verses = await retrieve_relevant_verses(
                    query="How to do my duty?",
                    top_k=2,
                )

                assert len(verses) == 2
                assert verses[0].chapter == 2
                assert verses[0].verse == 47

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_vector_store(self):
        """Test returns empty list when vector store not initialized."""
        with patch("app.rag.retriever.get_vector_store", return_value=None):
            verses = await retrieve_relevant_verses(query="test")

            assert verses == []

    @pytest.mark.asyncio
    async def test_filters_by_similarity_threshold(
        self, mock_vector_store, mock_embedding_fn
    ):
        """Test that results are filtered by similarity threshold."""
        # Set high distances (low similarity)
        mock_vector_store.query.return_value["distances"] = [[0.9, 0.95]]

        with patch("app.rag.retriever.get_vector_store", return_value=mock_vector_store):
            with patch("app.rag.retriever.get_embedding_function", return_value=mock_embedding_fn):
                verses = await retrieve_relevant_verses(
                    query="test",
                    similarity_threshold=0.6,
                )

                # High distance = low similarity, should be filtered
                assert len(verses) < 2


class TestRetrieveByReference:
    """Tests for retrieve_by_reference function."""

    @pytest.mark.asyncio
    async def test_retrieves_specific_verse(self, mock_vector_store):
        """Test retrieving a specific verse by reference."""
        mock_vector_store.get.return_value = {
            "ids": ["ch2_v47"],
            "documents": ["test doc"],
            "metadatas": [{
                "chapter": 2,
                "verse": 47,
                "sanskrit": "test",
                "english": "test translation",
            }],
        }

        with patch("app.rag.retriever.get_vector_store", return_value=mock_vector_store):
            verse = await retrieve_by_reference(chapter=2, verse=47)

            assert verse is not None
            assert verse.chapter == 2
            assert verse.verse == 47

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self, mock_vector_store):
        """Test returns None when verse not found."""
        mock_vector_store.get.return_value = {"ids": [], "metadatas": []}

        with patch("app.rag.retriever.get_vector_store", return_value=mock_vector_store):
            verse = await retrieve_by_reference(chapter=99, verse=99)

            assert verse is None


class TestVerseSourceModel:
    """Tests for VerseSource Pydantic model."""

    def test_creates_valid_verse_source(self):
        """Test creating a valid VerseSource."""
        verse = VerseSource(
            chapter=2,
            verse=47,
            sanskrit="test",
            english="test translation",
        )

        assert verse.chapter == 2
        assert verse.verse == 47
        assert verse.reference == "Chapter 2, Verse 47"

    def test_chapter_validation(self):
        """Test chapter number validation."""
        with pytest.raises(ValueError):
            VerseSource(chapter=0, verse=1)

        with pytest.raises(ValueError):
            VerseSource(chapter=19, verse=1)

    def test_optional_fields(self):
        """Test optional fields have defaults."""
        verse = VerseSource(chapter=1, verse=1)

        assert verse.sanskrit == ""
        assert verse.english == ""
        assert verse.similarity_score is None
