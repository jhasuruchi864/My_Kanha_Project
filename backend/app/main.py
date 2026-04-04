"""
Kanha API - FastAPI Entry Point
A spiritual chatbot powered by the Bhagavad Gita
"""

from contextlib import asynccontextmanager
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.logger import logger
from app.api.routes_chat import router as chat_router
from app.api.routes_health import router as health_router
from app.api.routes_admin import router as admin_router
from app.api.routes_history import router as history_router
from app.api.routes_auth import router as auth_router
from app.rag.init_chromadb import ChromaDBConnector


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting Kanha API...")
    logger.info(f"Debug mode: {settings.DEBUG}")

    # Pre-warm the spiritual engine: Initialize ChromaDB and Embedding model on startup
    try:
        logger.info("Initializing spiritual engine (ChromaDB & Embeddings)...")
        retriever = ChromaDBConnector.get_retriever()
        
        # Warm up the model with a dummy query to ensure it's loaded in RAM/GPU
        logger.info("Warming up embedding model...")
        retriever.retrieve("Namaste", n_results=1)
        
        logger.info("✓ Spiritual engine is warm and ready.")
    except Exception as e:
        logger.error(f"❌ Failed to pre-warm spiritual engine: {e}")
        # We don't necessarily want to crash the whole app if ChromaDB is down, 
        # but we definitely want it logged.

    yield

    # Shutdown
    logger.info("Shutting down Kanha API...")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="A spiritual chatbot powered by the Bhagavad Gita - Converse with Krishna",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router, tags=["Health"])
app.include_router(auth_router, tags=["Authentication"])
app.include_router(chat_router, prefix="/chat", tags=["Chat"])
app.include_router(history_router, prefix="/history", tags=["History"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])

# Mount static files from web_app folder
web_app_path = Path(__file__).parent.parent.parent / "web_app"
if web_app_path.exists():
    # Mount at root with html=True to serve index.html automatically
    app.mount("/", StaticFiles(directory=str(web_app_path), html=True), name="web_app")
    logger.info(f"Mounted web_app static files from {web_app_path}")
else:
    logger.warning(f"web_app directory not found at {web_app_path}")


@app.get("/health/chroma")
async def get_health():
    """Health check endpoint - verifies ChromaDB and backend status."""
    return ChromaDBConnector.check_health()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
