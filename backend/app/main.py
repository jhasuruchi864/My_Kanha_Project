"""
Kanha API - FastAPI Entry Point
A spiritual chatbot powered by the Bhagavad Gita
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.logger import logger
from app.api.routes_chat import router as chat_router
from app.api.routes_health import router as health_router
from app.api.routes_admin import router as admin_router
from app.rag.init_chromadb import startup_event, health_check


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting Kanha API...")
    logger.info(f"Debug mode: {settings.DEBUG}")

    # Initialize ChromaDB (persisted embeddings)
    try:
        startup_event()
        logger.info("ChromaDB initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB: {e}")

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
app.include_router(chat_router, prefix="/chat", tags=["Chat"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Kanha API",
        "description": "Converse with Krishna through the wisdom of Bhagavad Gita",
        "docs": "/docs" if settings.DEBUG else "Disabled in production",
    }


@app.get("/health")
async def get_health():
    """Health check endpoint - verifies ChromaDB and backend status."""
    return health_check()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
