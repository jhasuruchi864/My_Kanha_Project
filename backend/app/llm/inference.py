"""
Inference
Context assembly and response generation.
"""

from typing import List, Optional
from dataclasses import dataclass, field

from app.logger import logger
from app.llm.local_llm import get_llm_client
from app.core.prompt_templates import (
    KRISHNA_SYSTEM_PROMPT,
    RESPONSE_TEMPLATE,
    VERSE_CONTEXT_TEMPLATE,
    LANGUAGE_INSTRUCTION,
)
from app.models.verse_models import VerseSource
from app.models.chat_models import ConversationHistory
from app.rag.formatter import format_verses_for_prompt, format_verse_citation


@dataclass
class LLMResponse:
    """Response from LLM inference."""
    text: str
    sources: List[VerseSource] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


async def generate_response(
    user_message: str,
    retrieved_verses: List[VerseSource],
    conversation_history: Optional[List[ConversationHistory]] = None,
    response_language: str = "english",
) -> LLMResponse:
    """
    Generate Krishna's response using retrieved context and LLM.

    Args:
        user_message: The user's question/message
        retrieved_verses: Relevant verses from RAG retrieval
        conversation_history: Previous messages in conversation
        response_language: Desired response language

    Returns:
        LLMResponse with generated text and sources
    """
    # Build rich context from retrieved verses
    context = build_context(retrieved_verses, language=response_language)

    # Build conversation history string
    history = build_history(conversation_history)

    # Build the full prompt with verse grounding
    prompt = RESPONSE_TEMPLATE.format(
        context=context,
        question=user_message,
        history=history if history else "No previous conversation.",
    )
    
    # Append grounding reminder
    prompt += "\n\n[Remember: Ground your response in the verses above. Cite specific verses when relevant.]"

    # Add language instruction
    language_instruction = LANGUAGE_INSTRUCTION.get(
        response_language.lower(),
        LANGUAGE_INSTRUCTION["english"]
    )

    system_prompt = f"{KRISHNA_SYSTEM_PROMPT}\n\n{language_instruction}"

    logger.debug(f"Generating response for: {user_message[:50]}...")

    try:
        client = get_llm_client()

        response_text = await client.generate(
            prompt=prompt,
            system=system_prompt,
        )

        # Clean up response
        response_text = clean_response(response_text)

        # Add verse references to metadata
        verse_refs = [format_verse_citation(v) for v in retrieved_verses[:3]]  # Top 3

        return LLMResponse(
            text=response_text,
            sources=retrieved_verses,
            metadata={
                "model": client.model,
                "context_verses": len(retrieved_verses),
                "language": response_language,
                "verse_references": verse_refs,
            },
        )

    except Exception as e:
        logger.error(f"Error generating response: {e}")

        # Return a graceful fallback
        return LLMResponse(
            text=(
                "Dear seeker, I am momentarily unable to respond. "
                "Please try again, and I shall share the wisdom of the Gita with you."
            ),
            sources=[],
            metadata={"error": str(e)},
        )


def build_context(verses: List[VerseSource], language: str = "english") -> str:
    """Build rich context string from retrieved verses with full formatting."""
    if not verses:
        return "No specific verses found for this query."

    # Use the rich formatter for better grounding
    formatted = format_verses_for_prompt(
        verses,
        max_verses=5,
        include_sanskrit=True,
        include_transliteration=False,
        language=language
    )

    # Add instruction to cite verses
    citation_guide = "\n\n**Citation Instructions:**\n"
    citation_guide += "When referencing these verses, use format: 'As I taught in Chapter X, Verse Y...'"
    
    return formatted.context_text + citation_guide


def build_history(history: Optional[List[ConversationHistory]]) -> str:
    """Build conversation history string."""
    if not history:
        return ""

    history_parts = []

    for msg in history[-5:]:  # Last 5 messages only
        role = "Seeker" if msg.role == "user" else "Krishna"
        history_parts.append(f"{role}: {msg.content}")

    return "\n".join(history_parts)


def clean_response(response: str) -> str:
    """Clean up the LLM response."""
    # Remove any accidental prompt leakage
    response = response.strip()

    # Remove common artifacts
    prefixes_to_remove = [
        "Response:",
        "Krishna:",
        "As Krishna,",
        "Here is my response:",
    ]

    for prefix in prefixes_to_remove:
        if response.startswith(prefix):
            response = response[len(prefix):].strip()

    return response


async def generate_response_stream(
    user_message: str,
    retrieved_verses: List[VerseSource],
    conversation_history: Optional[List[ConversationHistory]] = None,
    response_language: str = "english",
):
    """
    Generate Krishna's response as a stream of text chunks.

    Args:
        user_message: The user's question/message
        retrieved_verses: Relevant verses from RAG retrieval
        conversation_history: Previous messages in conversation
        response_language: Desired response language

    Yields:
        Text chunks as they are generated
    """
    # Build rich context from retrieved verses
    context = build_context(retrieved_verses, language=response_language)

    # Build conversation history string
    history = build_history(conversation_history)

    # Build the full prompt with verse grounding
    prompt = RESPONSE_TEMPLATE.format(
        context=context,
        question=user_message,
        history=history if history else "No previous conversation.",
    )
    
    # Append grounding reminder
    prompt += "\n\n[Remember: Ground your response in the verses above. Cite specific verses when relevant.]"

    # Add language instruction
    language_instruction = LANGUAGE_INSTRUCTION.get(
        response_language.lower(),
        LANGUAGE_INSTRUCTION["english"]
    )

    system_prompt = f"{KRISHNA_SYSTEM_PROMPT}\n\n{language_instruction}"

    logger.debug(f"Generating streaming response for: {user_message[:50]}...")

    try:
        client = get_llm_client()

        async for chunk in client.generate_stream(
            prompt=prompt,
            system=system_prompt,
        ):
            yield chunk

    except Exception as e:
        logger.error(f"Error generating streaming response: {e}")
        yield "Dear seeker, I am momentarily unable to respond. Please try again."


async def generate_verse_explanation(
    verse: VerseSource,
    context_question: Optional[str] = None,
    language: str = "english",
) -> str:
    """
    Generate a detailed explanation of a specific verse.

    Args:
        verse: The verse to explain
        context_question: Optional question to focus the explanation
        language: Response language

    Returns:
        Detailed explanation text
    """
    prompt = f"""Explain this verse from the Bhagavad Gita:

Chapter {verse.chapter}, Verse {verse.verse}

Sanskrit: {verse.sanskrit}
Translation: {verse.english or verse.hindi}

{f"The seeker specifically asks: {context_question}" if context_question else ""}

Provide a clear, accessible explanation that:
1. Explains the core teaching
2. Relates it to practical life
3. Connects it to the broader context of the Gita
"""

    language_instruction = LANGUAGE_INSTRUCTION.get(language.lower(), LANGUAGE_INSTRUCTION["english"])
    system_prompt = f"{KRISHNA_SYSTEM_PROMPT}\n\n{language_instruction}"

    try:
        client = get_llm_client()
        response = await client.generate(prompt=prompt, system=system_prompt)
        return clean_response(response)

    except Exception as e:
        logger.error(f"Error generating verse explanation: {e}")
        return "I am unable to provide an explanation at this moment."
