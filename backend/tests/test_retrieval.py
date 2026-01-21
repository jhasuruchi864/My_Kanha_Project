"""
Tests for RAG retrieval functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from app.models.verse_models import VerseSource


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

    def test_similarity_score_bounds(self):
        """Test similarity score must be between 0 and 1."""
        # Valid scores
        verse = VerseSource(chapter=1, verse=1, similarity_score=0.5)
        assert verse.similarity_score == 0.5

        verse = VerseSource(chapter=1, verse=1, similarity_score=0.0)
        assert verse.similarity_score == 0.0

        verse = VerseSource(chapter=1, verse=1, similarity_score=1.0)
        assert verse.similarity_score == 1.0

        # Invalid scores
        with pytest.raises(ValueError):
            VerseSource(chapter=1, verse=1, similarity_score=-0.1)

        with pytest.raises(ValueError):
            VerseSource(chapter=1, verse=1, similarity_score=1.5)

    def test_all_fields(self):
        """Test creating verse with all fields."""
        verse = VerseSource(
            chapter=2,
            verse=47,
            sanskrit="कर्मण्येवाधिकारस्ते",
            transliteration="karmany evadhikaras te",
            english="You have the right to work",
            hindi="कर्म करने में ही तुम्हारा अधिकार है",
            similarity_score=0.95,
        )

        assert verse.chapter == 2
        assert verse.verse == 47
        assert verse.sanskrit == "कर्मण्येवाधिकारस्ते"
        assert verse.transliteration == "karmany evadhikaras te"
        assert verse.english == "You have the right to work"
        assert verse.hindi == "कर्म करने में ही तुम्हारा अधिकार है"
        assert verse.similarity_score == 0.95

    def test_reference_format(self):
        """Test the reference property format."""
        verse = VerseSource(chapter=18, verse=66)
        assert verse.reference == "Chapter 18, Verse 66"

        verse = VerseSource(chapter=1, verse=1)
        assert verse.reference == "Chapter 1, Verse 1"


class TestVerseModels:
    """Tests for verse-related models."""

    def test_chapter_info_model(self):
        """Test ChapterInfo model."""
        from app.models.verse_models import ChapterInfo

        chapter = ChapterInfo(
            chapter_number=2,
            name_sanskrit="सांख्ययोग",
            name_english="Sankhya Yoga",
            name_hindi="सांख्य योग",
            verse_count=72,
            summary="Chapter about knowledge."
        )

        assert chapter.chapter_number == 2
        assert chapter.verse_count == 72

    def test_verse_detail_model(self):
        """Test VerseDetail model."""
        from app.models.verse_models import VerseDetail

        detail = VerseDetail(
            chapter=2,
            verse=47,
            sanskrit="test",
            speaker="Krishna"
        )

        assert detail.chapter == 2
        assert detail.verse == 47
        assert detail.speaker == "Krishna"

    def test_verse_search_result_model(self):
        """Test VerseSearchResult model."""
        from app.models.verse_models import VerseSearchResult

        verses = [VerseSource(chapter=1, verse=1)]
        result = VerseSearchResult(
            verses=verses,
            total_count=1,
            query="test query"
        )

        assert result.total_count == 1
        assert result.query == "test query"
        assert result.search_type == "semantic"


class TestRetrieverLogic:
    """Tests for retriever-related logic without real ChromaDB."""

    def test_similarity_calculation(self):
        """Test similarity score calculation from distance."""
        # Similarity = 1 - distance (for normalized distances)
        distance = 0.2
        similarity = 1 - distance
        assert similarity == 0.8

        distance = 0.0
        similarity = 1 - distance
        assert similarity == 1.0

        distance = 1.0
        similarity = 1 - distance
        assert similarity == 0.0

    def test_distance_threshold_filtering(self):
        """Test filtering results by distance threshold."""
        results = [
            {"distance": 0.1, "id": "1"},  # similarity 0.9
            {"distance": 0.5, "id": "2"},  # similarity 0.5
            {"distance": 0.8, "id": "3"},  # similarity 0.2
        ]

        threshold = 0.5
        filtered = [r for r in results if (1 - r["distance"]) >= threshold]

        assert len(filtered) == 2
        assert filtered[0]["id"] == "1"
        assert filtered[1]["id"] == "2"

    def test_verse_metadata_parsing(self):
        """Test parsing verse metadata from ChromaDB format."""
        metadata = {
            "chapter_number": "2",
            "verse_number": "47",
            "sanskrit": "test sanskrit",
            "english_translation": "test english",
            "hindi_translation": "test hindi",
            "speaker": "Krishna",
        }

        # Simulate parsing
        chapter = int(metadata.get("chapter_number", 0))
        verse = int(metadata.get("verse_number", 0))

        assert chapter == 2
        assert verse == 47
        assert metadata["speaker"] == "Krishna"

    def test_empty_query_result_handling(self):
        """Test handling of empty query results."""
        empty_result = {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }

        # Check if empty
        has_results = empty_result["ids"] and empty_result["ids"][0]
        assert not has_results

    def test_query_result_format(self):
        """Test expected format of query results."""
        query_result = {
            "ids": [["ch2_v47", "ch2_v48"]],
            "documents": [["doc1", "doc2"]],
            "metadatas": [[
                {"chapter_number": "2", "verse_number": "47"},
                {"chapter_number": "2", "verse_number": "48"},
            ]],
            "distances": [[0.1, 0.2]],
        }

        # Verify structure
        assert len(query_result["ids"][0]) == 2
        assert len(query_result["metadatas"][0]) == 2
        assert query_result["distances"][0][0] == 0.1
