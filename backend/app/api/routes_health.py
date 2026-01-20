"""
Health Check Routes
Endpoints for monitoring service health.
"""

from fastapi import APIRouter
from datetime import datetime

from app.config import settings
from app.logger import logger

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    Returns the current status of the API service.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
    }


@router.get("/health/detailed")
async def detailed_health_check():
    """
    Detailed health check with component status.
    """
    components = {
        "api": "healthy",
        "vector_store": "unknown",
        "llm": "unknown",
    }

    # Check vector store
    try:
        from app.rag.vectorstore import get_vector_store
        vs = get_vector_store()
        if vs is not None:
            components["vector_store"] = "healthy"
        else:
            components["vector_store"] = "not_initialized"
    except Exception as e:
        logger.error(f"Vector store health check failed: {e}")
        components["vector_store"] = "unhealthy"

    # Check LLM connection
    try:
        from app.llm.local_llm import check_llm_health
        if await check_llm_health():
            components["llm"] = "healthy"
        else:
            components["llm"] = "unhealthy"
    except Exception as e:
        logger.error(f"LLM health check failed: {e}")
        components["llm"] = "unhealthy"

    # Overall status
    overall_status = "healthy" if all(
        v == "healthy" for v in components.values()
    ) else "degraded"

    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "components": components,
    }
