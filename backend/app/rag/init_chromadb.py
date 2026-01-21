"""
ChromaDB Initialization Module
Auto-loads and indexes Gita data on backend startup
"""

import logging
import json
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_CLEANED_PATH = PROJECT_ROOT / 'data' / 'cleaned' / 'gita_master.json'
VECTOR_DB_PATH = PROJECT_ROOT / 'vector_db' / 'chroma'
INIT_FLAG_FILE = VECTOR_DB_PATH / '.initialized'


class ChromaDBInitializer:
    """Initialize and manage ChromaDB on application startup"""
    
    _initialized = False
    _retriever = None
    
    @classmethod
    def initialize(cls) -> bool:
        """
        Initialize ChromaDB on first startup
        
        Returns:
            True if successfully initialized or already initialized
        """
        if cls._initialized:
            logger.debug("ChromaDB already initialized")
            return True
        
        try:
            # Check if index already exists
            if INIT_FLAG_FILE.exists():
                logger.info("ChromaDB index already exists, skipping initialization")
                cls._initialized = True
                return True
            
            # Check if raw data exists
            if not DATA_CLEANED_PATH.exists():
                logger.error(f"Data file not found: {DATA_CLEANED_PATH}")
                logger.error("Please run 'python data/scripts/embed_and_index.py' first")
                return False
            
            # Create embeddings and index
            logger.info("Starting ChromaDB initialization...")
            from data.scripts.embed_and_index import GitaEmbedder
            
            embedder = GitaEmbedder()
            embedder.run()
            
            # Mark as initialized
            VECTOR_DB_PATH.mkdir(parents=True, exist_ok=True)
            INIT_FLAG_FILE.touch()
            
            logger.info("✓ ChromaDB initialization complete")
            cls._initialized = True
            return True
        
        except ImportError as e:
            logger.error(f"Missing dependency: {str(e)}")
            logger.error("Please install required packages: pip install sentence-transformers chromadb")
            return False
        except Exception as e:
            logger.error(f"ChromaDB initialization failed: {str(e)}", exc_info=True)
            return False
    
    @classmethod
    def get_retriever(cls):
        """Get initialized retriever instance"""
        if not cls._initialized:
            cls.initialize()
        
        if cls._retriever is None:
            from app.rag.retriever import GitaRetriever
            cls._retriever = GitaRetriever()
        
        return cls._retriever
    
    @classmethod
    def check_health(cls) -> dict:
        """Check ChromaDB health status"""
        try:
            retriever = cls.get_retriever()
            return retriever.health_check()
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }


def startup_event() -> None:
    """FastAPI startup event handler"""
    logger.info("Running FastAPI startup tasks...")
    
    # Initialize ChromaDB
    if ChromaDBInitializer.initialize():
        logger.info("✓ Backend initialized successfully")
    else:
        logger.warning("⚠ ChromaDB initialization failed - some features may not work")


def health_check() -> dict:
    """Health check endpoint"""
    return ChromaDBInitializer.check_health()
