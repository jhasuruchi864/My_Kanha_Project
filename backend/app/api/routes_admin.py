"""
Admin Routes
Administrative endpoints for managing the system.
"""

from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from datetime import datetime, timedelta
from collections import defaultdict

from app.config import settings
from app.logger import logger
from app.rag.ingest import reingest_data, get_ingestion_status
from app.rag.embeddings import get_cached_embedding

router = APIRouter()

# Performance metrics tracking
class MetricsTracker:
    """Track retrieval and LLM performance metrics."""
    
    def __init__(self):
        self.retrieval_times = []
        self.llm_response_times = []
        self.retrieval_by_query = defaultdict(list)
        self.llm_by_model = defaultdict(list)
        self.error_log = []
        self.request_count = 0
    
    def record_retrieval(self, query: str, duration: float, results_count: int):
        """Record retrieval performance."""
        self.retrieval_times.append(duration)
        self.retrieval_by_query[query].append({
            "duration": duration,
            "results": results_count,
            "timestamp": datetime.now().isoformat()
        })
    
    def record_llm_response(self, model: str, duration: float, tokens: int = 0):
        """Record LLM response performance."""
        self.llm_response_times.append(duration)
        self.llm_by_model[model].append({
            "duration": duration,
            "tokens": tokens,
            "timestamp": datetime.now().isoformat()
        })
    
    def record_error(self, error_type: str, message: str):
        """Record errors."""
        self.error_log.append({
            "type": error_type,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_stats(self) -> dict:
        """Get aggregated statistics."""
        if not self.retrieval_times:
            avg_retrieval = 0
        else:
            avg_retrieval = sum(self.retrieval_times) / len(self.retrieval_times)
        
        if not self.llm_response_times:
            avg_llm = 0
        else:
            avg_llm = sum(self.llm_response_times) / len(self.llm_response_times)
        
        return {
            "retrieval": {
                "total_queries": len(self.retrieval_times),
                "avg_time": round(avg_retrieval, 3),
                "min_time": round(min(self.retrieval_times), 3) if self.retrieval_times else 0,
                "max_time": round(max(self.retrieval_times), 3) if self.retrieval_times else 0,
            },
            "llm": {
                "total_requests": len(self.llm_response_times),
                "avg_time": round(avg_llm, 3),
                "min_time": round(min(self.llm_response_times), 3) if self.llm_response_times else 0,
                "max_time": round(max(self.llm_response_times), 3) if self.llm_response_times else 0,
            },
            "errors": {
                "total": len(self.error_log),
                "recent": self.error_log[-10:],
            }
        }

# Global metrics instance
metrics_tracker = MetricsTracker()


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
    Clear any cached data including embedding caches.
    """
    verify_admin_key(x_api_key)

    logger.info("Admin triggered cache clear")

    caches_cleared = []

    try:
        # Clear embedding cache
        cache_info_before = get_cached_embedding.cache_info()
        get_cached_embedding.cache_clear()
        cache_info_after = get_cached_embedding.cache_info()
        caches_cleared.append({
            "cache": "embedding_cache",
            "entries_cleared": cache_info_before.currsize,
        })
        logger.info(f"Cleared embedding cache: {cache_info_before.currsize} entries")

    except Exception as e:
        logger.error(f"Error clearing embedding cache: {e}")
        caches_cleared.append({
            "cache": "embedding_cache",
            "error": str(e),
        })

    return {
        "status": "success",
        "message": "Cache cleared",
        "details": caches_cleared,
    }

@router.get("/stats/retrieval")
async def get_retrieval_stats(x_api_key: Optional[str] = Header(None)):
    """
    Get retrieval performance statistics.
    Shows metrics on vector database queries and retrieval times.
    """
    verify_admin_key(x_api_key)
    
    logger.info("Admin requested retrieval stats")
    
    stats = metrics_tracker.get_stats()
    
    return {
        "status": "success",
        "retrieval_stats": stats["retrieval"],
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/stats/llm")
async def get_llm_stats(x_api_key: Optional[str] = Header(None)):
    """
    Get LLM performance statistics.
    Shows metrics on response generation times and model performance.
    """
    verify_admin_key(x_api_key)
    
    logger.info("Admin requested LLM stats")
    
    stats = metrics_tracker.get_stats()
    
    return {
        "status": "success",
        "llm_stats": stats["llm"],
        "model": settings.LLM_MODEL,
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/stats/combined")
async def get_combined_stats(x_api_key: Optional[str] = Header(None)):
    """
    Get comprehensive performance statistics for both retrieval and LLM.
    """
    verify_admin_key(x_api_key)
    
    logger.info("Admin requested combined stats")
    
    stats = metrics_tracker.get_stats()
    
    return {
        "status": "success",
        "stats": stats,
        "models": {
            "llm": settings.LLM_MODEL,
            "embedding": settings.EMBEDDING_MODEL,
        },
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/stats/reset")
async def reset_stats(x_api_key: Optional[str] = Header(None)):
    """
    Reset all performance statistics.
    """
    verify_admin_key(x_api_key)
    
    logger.warning("Admin triggered stats reset")
    
    metrics_tracker.retrieval_times.clear()
    metrics_tracker.llm_response_times.clear()
    metrics_tracker.retrieval_by_query.clear()
    metrics_tracker.llm_by_model.clear()
    metrics_tracker.error_log.clear()
    
    return {
        "status": "success",
        "message": "Statistics reset successfully",
    }


@router.get("/health/detailed")
async def get_detailed_health(x_api_key: Optional[str] = Header(None)):
    """
    Get detailed health check including performance metrics and system info.
    """
    verify_admin_key(x_api_key)
    
    stats = metrics_tracker.get_stats()
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "system": {
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "debug": settings.DEBUG,
        },
        "models": {
            "llm": settings.LLM_MODEL,
            "embedding": settings.EMBEDDING_MODEL,
        },
        "performance": stats,
    }