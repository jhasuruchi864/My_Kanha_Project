"""
Chat Routes
Main endpoint for conversing with Krishna.
"""

import json
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from typing import Optional, AsyncGenerator
from uuid import uuid4

from app.logger import logger
from app.models.chat_models import ChatRequest, ChatResponse, ConversationHistory, StreamChunk
from app.models.verse_models import VerseSource
from app.rag.retriever import retrieve
from app.rag.formatter import format_system_prompt
from app.llm.inference import generate_response, generate_response_stream
from app.core.safety_rules import check_safety
from app.core.auth_service import verify_token
from app.utils.language_detect import detect_language
from app.persistence.conversation_store import (
    load_conversation,
    save_conversation,
    create_conversation,
)

router = APIRouter()
security = HTTPBearer(auto_error=False)


async def get_optional_user(credentials: Optional[HTTPAuthCredentials] = Depends(security)) -> Optional[str]:
    """Extract user_id from JWT token if provided (optional)."""
    if not credentials:
        return None
    
    token_data = verify_token(credentials.credentials)
    return token_data.user_id if token_data else None


def _to_verse_source(verse: dict) -> VerseSource:
    """Normalize retrieval dicts into VerseSource model."""
    chapter_raw = verse.get("chapter_number", verse.get("chapter"))
    verse_raw = verse.get("verse_number", verse.get("verse"))

    # Guard against missing/zero values to satisfy validation (>=1)
    if not chapter_raw or not verse_raw:
        raise ValueError("Verse data missing chapter or verse number")

    return VerseSource(
        chapter=int(chapter_raw),
        verse=int(verse_raw),
        sanskrit=verse.get("sanskrit", ""),
        english=verse.get("english_translation") or verse.get("english", ""),
        hindi=verse.get("hindi_translation") or verse.get("hindi", ""),
        similarity_score=verse.get("similarity_score"),
    )


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest, user_id: Optional[str] = Depends(get_optional_user)):
    """
    Main chat endpoint - Converse with Krishna.

    Receives a user message and returns Krishna's response
    along with relevant verse citations.
    
    Persists conversation to JSON storage and links to authenticated user if provided.
    """
    try:
        logger.info(f"Received chat request: {request.message[:50]}...")

        # Get or create user session
        final_user_id = user_id or request.user_id or str(uuid4())
        session_id = request.session_id
        
        # Load or create conversation
        if session_id:
            session = load_conversation(final_user_id, session_id)
        else:
            session = create_conversation(final_user_id, request.language or "english")
            session_id = session.session_id
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Detect input language
        detected_language = detect_language(request.message)
        logger.debug(f"Detected language: {detected_language}")

        # Safety check
        safety_result = check_safety(request.message)
        if not safety_result.is_safe:
            logger.warning(f"Safety check failed: {safety_result.reason}")
            
            # Store the user message and safety redirect
            session.add_message("user", request.message)
            session.add_message("assistant", safety_result.safe_response)
            save_conversation(session)
            
            return ChatResponse(
                response=safety_result.safe_response,
                sources=[],
                language=detected_language,
                session_id=session_id,
                user_id=final_user_id,
            )

        # Retrieve relevant verses from ChromaDB
        retrieved_verses = retrieve(
            query=request.message,
            n_results=request.top_k or 5,
        )

        logger.debug(f"Retrieved {len(retrieved_verses)} relevant verses")

        normalized_sources = []
        for v in retrieved_verses:
            try:
                normalized_sources.append(_to_verse_source(v))
            except Exception as norm_err:
                logger.warning(f"Skipping verse with missing identifiers: {norm_err} | data={v}")

        # Prepare RAG context for the LLM
        format_system_prompt(retrieved_verses)

        # Generate response using LLM
        response = await generate_response(
            user_message=request.message,
            retrieved_verses=normalized_sources,
            conversation_history=session.get_messages_for_context(),
            response_language=request.language or detected_language,
        )

        # Store messages in session
        session.add_message("user", request.message, sources=[s.model_dump() if hasattr(s, 'model_dump') else s.__dict__ for s in normalized_sources])
        session.add_message("assistant", response.text, sources=[s.model_dump() if hasattr(s, 'model_dump') else s.__dict__ for s in normalized_sources])
        
        # Save conversation to persistent storage
        save_conversation(session)

        return ChatResponse(
            response=response.text,
            sources=normalized_sources,
            language=detected_language,
            metadata=response.metadata,
            session_id=session_id,
            user_id=final_user_id,
        )

    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while processing your request")


@router.post("/stream")
async def chat_stream(request: ChatRequest, user_id: Optional[str] = Depends(get_optional_user)):
    """
    Streaming chat endpoint for real-time responses.
    Returns Server-Sent Events (SSE) stream.
    
    Optional JWT authentication to link chat history to user.
    """
    try:
        logger.info(f"Received streaming chat request: {request.message[:50]}...")

        # Get or create user session
        final_user_id = user_id or request.user_id or str(uuid4())
        session_id = request.session_id
        
        # Load or create conversation
        if session_id:
            session = load_conversation(final_user_id, session_id)
        else:
            session = create_conversation(final_user_id, request.language or "english")
            session_id = session.session_id
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

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

        normalized_sources = []
        for v in retrieved_verses:
            try:
                normalized_sources.append(_to_verse_source(v))
            except Exception as norm_err:
                logger.warning(f"Skipping verse with missing identifiers: {norm_err} | data={v}")

        logger.debug(f"Retrieved {len(retrieved_verses)} relevant verses")

        async def generate_stream() -> AsyncGenerator[str, None]:
            """Generate SSE stream with response chunks."""
            try:
                full_response = ""
                async for chunk_text in generate_response_stream(
                    user_message=request.message,
                    retrieved_verses=normalized_sources,
                    conversation_history=request.conversation_history,
                    response_language=request.language or detected_language,
                ):
                    full_response += chunk_text
                    chunk = StreamChunk(content=chunk_text, is_complete=False)
                    yield f"data: {chunk.model_dump_json()}\n\n"

                # Store messages in session
                session.add_message("user", request.message, sources=[s.model_dump() if hasattr(s, 'model_dump') else s.__dict__ for s in normalized_sources])
                session.add_message("assistant", full_response, sources=[s.model_dump() if hasattr(s, 'model_dump') else s.__dict__ for s in normalized_sources])
                
                # Save conversation to persistent storage
                save_conversation(session)

                # Send final chunk with sources
                final_chunk = StreamChunk(
                    content="",
                    is_complete=True,
                    sources=normalized_sources,
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
