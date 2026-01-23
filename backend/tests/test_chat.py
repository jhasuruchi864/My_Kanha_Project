"""
Tests for chat endpoint and related functionality.
"""

import pytest
from unittest.mock import patch, AsyncMock, Mock

from app.models.chat_models import ChatRequest, ChatResponse, ConversationHistory
from app.models.verse_models import VerseSource
from app.core.safety_rules import check_safety, SafetyResult


@pytest.fixture
def mock_verses():
    """Create mock verse sources."""
    return [
        VerseSource(
            chapter=2,
            verse=47,
            sanskrit="कर्मण्येवाधिकारस्ते...",
            english="You have the right to work only, but never to its fruits.",
            hindi="कर्म करने में ही तुम्हारा अधिकार है...",
            similarity_score=0.85,
        ),
    ]


class TestChatRequestModels:
    """Tests for chat request/response models."""

    def test_chat_request_validation(self):
        """Test chat request Pydantic validation."""
        # Valid request
        request = ChatRequest(
            message="How can I find peace?",
            language="english",
        )
        assert request.message == "How can I find peace?"

        # Invalid - empty message
        with pytest.raises(ValueError):
            ChatRequest(message="")

        # Invalid - message too long
        with pytest.raises(ValueError):
            ChatRequest(message="x" * 3000)

    def test_chat_response_model(self, mock_verses):
        """Test ChatResponse model."""
        response = ChatResponse(
            response="Dear seeker, peace comes from within...",
            sources=mock_verses,
            language="english",
        )

        assert "Dear seeker" in response.response
        assert len(response.sources) == 1
        assert response.sources[0].chapter == 2

    def test_conversation_history(self):
        """Test conversation history in request."""
        history = [
            ConversationHistory(role="user", content="Hello"),
            ConversationHistory(role="assistant", content="Namaste, dear seeker."),
        ]

        request = ChatRequest(
            message="Tell me about karma",
            conversation_history=history,
        )

        assert len(request.conversation_history) == 2
        assert request.conversation_history[0].role == "user"

    def test_optional_parameters(self):
        """Test optional parameters have defaults."""
        request = ChatRequest(message="Test message")

        assert request.language is None
        assert request.top_k == 5
        assert request.conversation_history is None
        assert request.session_id is None


class TestSafetyRules:
    """Tests for safety guardrails."""

    def test_safe_message_passes(self):
        """Test that normal spiritual questions pass safety check."""
        result = check_safety("How can I find inner peace?")

        assert result.is_safe is True
        assert result.reason == ""

    def test_harmful_content_blocked(self):
        """Test that harmful content is blocked."""
        result = check_safety("How to harm someone?")

        assert result.is_safe is False
        assert result.reason == "harmful_content"
        assert len(result.safe_response) > 0

    def test_off_topic_redirected(self):
        """Test that off-topic content is redirected."""
        result = check_safety("What's the best stock to invest in?")

        assert result.is_safe is False
        assert result.reason == "off_topic"

    def test_other_religion_handled_respectfully(self):
        """Test that other religion queries are handled respectfully."""
        result = check_safety("What does the Bible say about this?")

        assert result.is_safe is False
        assert result.reason == "other_religion"
        assert "respect" in result.safe_response.lower()

    def test_technical_questions_redirected(self):
        """Test that technical questions are redirected."""
        result = check_safety("Can you write Python code for me?")

        assert result.is_safe is False
        assert result.reason == "technical"

    def test_safety_result_dataclass(self):
        """Test SafetyResult dataclass."""
        result = SafetyResult(is_safe=True)
        assert result.is_safe is True
        assert result.reason == ""
        assert result.safe_response == ""

        result = SafetyResult(
            is_safe=False,
            reason="harmful_content",
            safe_response="Please reconsider."
        )
        assert result.is_safe is False
        assert result.reason == "harmful_content"


class TestLanguageDetection:
    """Tests for language detection."""

    def test_detects_english(self):
        """Test English detection."""
        from app.utils.language_detect import detect_language

        result = detect_language("How can I find peace of mind?")
        assert result == "english"

    def test_detects_hindi(self):
        """Test Hindi detection."""
        from app.utils.language_detect import detect_language

        result = detect_language("मुझे शांति कैसे मिलेगी?")
        assert result == "hindi"

    def test_detects_mixed_as_hindi(self):
        """Test that mixed text with significant Hindi is detected as Hindi."""
        from app.utils.language_detect import detect_language

        # More than 30% Devanagari should be Hindi
        result = detect_language("कृपया help me find शांति")
        assert result == "hindi"

    def test_empty_string_defaults_to_english(self):
        """Test empty string defaults to English."""
        from app.utils.language_detect import detect_language

        result = detect_language("")
        assert result == "english"


class TestTextUtils:
    """Tests for text utility functions."""

    def test_normalize_text(self):
        """Test text normalization."""
        from app.utils.text_utils import normalize_text

        result = normalize_text("  Multiple   spaces   here  ")
        assert result == "Multiple spaces here"

    def test_truncate_text(self):
        """Test text truncation."""
        from app.utils.text_utils import truncate_text

        long_text = "This is a very long text that needs to be truncated."
        result = truncate_text(long_text, max_length=20)

        assert len(result) <= 20
        assert result.endswith("...")

    def test_extract_verse_reference(self):
        """Test verse reference extraction."""
        from app.utils.text_utils import extract_verse_reference

        assert extract_verse_reference("Chapter 2, Verse 47") == (2, 47)
        assert extract_verse_reference("2:47") == (2, 47)
        assert extract_verse_reference("BG 2.47") == (2, 47)
        assert extract_verse_reference("No verse here") is None


class TestVerseSourceModel:
    """Tests for VerseSource model."""

    def test_creates_valid_verse(self):
        """Test creating a valid verse."""
        verse = VerseSource(
            chapter=2,
            verse=47,
            english="Test translation"
        )
        assert verse.chapter == 2
        assert verse.verse == 47

    def test_reference_property(self):
        """Test the reference property."""
        verse = VerseSource(chapter=5, verse=10)
        assert verse.reference == "Chapter 5, Verse 10"

    def test_chapter_bounds(self):
        """Test chapter number bounds."""
        # Valid chapters
        VerseSource(chapter=1, verse=1)
        VerseSource(chapter=18, verse=1)

        # Invalid chapters
        with pytest.raises(ValueError):
            VerseSource(chapter=0, verse=1)

        with pytest.raises(ValueError):
            VerseSource(chapter=19, verse=1)


class TestInferenceHelpers:
    """Tests for inference helper functions."""

    def test_build_context(self):
        """Test building context from verses."""
        from app.llm.inference import build_context

        verses = [
            VerseSource(
                chapter=2,
                verse=47,
                sanskrit="test sanskrit",
                english="test translation"
            )
        ]

        context = build_context(verses)
        assert "Chapter 2" in context
        assert "Verse 47" in context

    def test_build_context_empty(self):
        """Test building context with no verses."""
        from app.llm.inference import build_context

        context = build_context([])
        assert context == ""

    def test_build_history(self):
        """Test building conversation history."""
        from app.llm.inference import build_history

        history = [
            ConversationHistory(role="user", content="Hello"),
            ConversationHistory(role="assistant", content="Namaste"),
        ]

        result = build_history(history)
        assert "Seeker: Hello" in result
        assert "Krishna: Namaste" in result

    def test_build_history_empty(self):
        """Test building history with no messages."""
        from app.llm.inference import build_history

        result = build_history(None)
        assert result == ""

        result = build_history([])
        assert result == ""

    def test_clean_response(self):
        """Test response cleanup."""
        from app.llm.inference import clean_response

        # Test prefix removal
        assert clean_response("Krishna: Hello") == "Hello"
        assert clean_response("Response: Test") == "Test"
        assert clean_response("  Whitespace  ") == "Whitespace"


class TestStreamChunk:
    """Tests for StreamChunk model."""

    def test_stream_chunk_creation(self):
        """Test creating a stream chunk."""
        from app.models.chat_models import StreamChunk

        chunk = StreamChunk(content="Hello", is_complete=False)
        assert chunk.content == "Hello"
        assert chunk.is_complete is False
        assert chunk.sources is None

    def test_stream_chunk_with_sources(self, mock_verses):
        """Test stream chunk with sources."""
        from app.models.chat_models import StreamChunk

        chunk = StreamChunk(
            content="",
            is_complete=True,
            sources=mock_verses
        )
        assert chunk.is_complete is True
        assert len(chunk.sources) == 1
