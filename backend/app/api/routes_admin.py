"""
Admin Routes
Administrative endpoints for managing the system.
"""

from fastapi import APIRouter, HTTPException, Header
from typing import Optional

from app.config import settings
from app.logger import logger
from app.rag.ingest import reingest_data, get_ingestion_status

router = APIRouter()


def verify_admin_key(x_api_key: Optional[str] = Header(None)):
    """Verify admin API key."""
    if not settings.API_KEY:
        return True  # No key configured, allow access
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return True


@router.post("/reindex")
async def trigger_reindex(x_api_key: Optional[str] = Header(None)):
    """
    Trigger re-indexing of the Gita data into the vector store.
    Requires admin API key.
    """
    verify_admin_key(x_api_key)

    logger.info("Admin triggered re-indexing")

    try:
        result = await reingest_data()
        return {
            "status": "success",
            "message": "Re-indexing completed",
            "details": result,
        }
    except Exception as e:
        logger.error(f"Re-indexing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Re-indexing failed: {str(e)}")


@router.get("/status")
async def get_status(x_api_key: Optional[str] = Header(None)):
    """
    Get current system status including ingestion status.
    """
    verify_admin_key(x_api_key)

    status = await get_ingestion_status()

    return {
        "system": {
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "debug": settings.DEBUG,
            "llm_model": settings.LLM_MODEL,
            "embedding_model": settings.EMBEDDING_MODEL,
        },
        "ingestion": status,
    }


@router.post("/clear-cache")
async def clear_cache(x_api_key: Optional[str] = Header(None)):
    """
    Clear any cached data.
    """
    verify_admin_key(x_api_key)

    # TODO: Implement cache clearing logic
    logger.info("Admin triggered cache clear")

    return {
        "status": "success",
        "message": "Cache cleared",
    }
