"""
Chat Routes
Main endpoint for conversing with Krishna.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from app.logger import logger
from app.models.chat_models import ChatRequest, ChatResponse, ConversationHistory
from app.rag.retriever import retrieve
from app.rag.formatter import format_system_prompt
from app.llm.inference import generate_response
from app.core.safety_rules import check_safety
from app.utils.language_detect import detect_language

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint - Converse with Krishna.

    Receives a user message and returns Krishna's response
    along with relevant verse citations.
    """
    try:
        logger.info(f"Received chat request: {request.message[:50]}...")

        # Detect input language
        detected_language = detect_language(request.message)
        logger.debug(f"Detected language: {detected_language}")

        # Safety check
        safety_result = check_safety(request.message)
        if not safety_result.is_safe:
            logger.warning(f"Safety check failed: {safety_result.reason}")
            return ChatResponse(
                response=safety_result.safe_response,
                sources=[],
                language=detected_language,
            )

        # Retrieve relevant verses from ChromaDB
        retrieved_verses = retrieve(
            query=request.message,
            n_results=request.top_k or 5,
        )

        logger.debug(f"Retrieved {len(retrieved_verses)} relevant verses")

        # Prepare RAG context for the LLM
        verse_context = format_system_prompt(retrieved_verses)

        # Generate response using LLM
        response = await generate_response(
            user_message=request.message,
            retrieved_verses=retrieved_verses,
            conversation_history=request.conversation_history,
            response_language=request.language or detected_language,
        )

        return ChatResponse(
            response=response.text,
            sources=response.sources,
            language=detected_language,
            metadata=response.metadata,
        )

    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while processing your request")


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint for real-time responses.
    Returns Server-Sent Events (SSE) stream.
    """
    # TODO: Implement streaming response
    raise HTTPException(status_code=501, detail="Streaming not yet implemented")
