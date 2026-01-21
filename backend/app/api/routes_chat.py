"""
Chat Routes
Main endpoint for conversing with Krishna.
"""

import json
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import Optional, AsyncGenerator

from app.logger import logger
from app.models.chat_models import ChatRequest, ChatResponse, ConversationHistory, StreamChunk
from app.rag.retriever import retrieve
from app.rag.formatter import format_system_prompt
from app.llm.inference import generate_response, generate_response_stream
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
    try:
        logger.info(f"Received streaming chat request: {request.message[:50]}...")

        # Detect input language
        detected_language = detect_language(request.message)

        # Safety check
        safety_result = check_safety(request.message)
        if not safety_result.is_safe:
            logger.warning(f"Safety check failed: {safety_result.reason}")

            async def safety_response():
                chunk = StreamChunk(
                    content=safety_result.safe_response,
                    is_complete=True,
                    sources=[],
                )
                yield f"data: {chunk.model_dump_json()}\n\n"

            return StreamingResponse(
                safety_response(),
                media_type="text/event-stream",
            )

        # Retrieve relevant verses from ChromaDB
        retrieved_verses = retrieve(
            query=request.message,
            n_results=request.top_k or 5,
        )

        logger.debug(f"Retrieved {len(retrieved_verses)} relevant verses")

        async def generate_stream() -> AsyncGenerator[str, None]:
            """Generate SSE stream with response chunks."""
            try:
                async for chunk_text in generate_response_stream(
                    user_message=request.message,
                    retrieved_verses=retrieved_verses,
                    conversation_history=request.conversation_history,
                    response_language=request.language or detected_language,
                ):
                    chunk = StreamChunk(content=chunk_text, is_complete=False)
                    yield f"data: {chunk.model_dump_json()}\n\n"

                # Send final chunk with sources
                final_chunk = StreamChunk(
                    content="",
                    is_complete=True,
                    sources=retrieved_verses,
                )
                yield f"data: {final_chunk.model_dump_json()}\n\n"

            except Exception as e:
                logger.error(f"Error in stream generation: {e}")
                error_chunk = StreamChunk(
                    content="Dear seeker, I encountered an issue. Please try again.",
                    is_complete=True,
                    sources=[],
                )
                yield f"data: {error_chunk.model_dump_json()}\n\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )

    except Exception as e:
        logger.error(f"Error processing streaming chat request: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while processing your request")
