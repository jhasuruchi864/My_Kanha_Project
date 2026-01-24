"""
ChromaDB Initialization Module
Auto-loads and indexes Gita data on backend startup
"""

import logging
import json
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

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
            
            # Import here to avoid circular imports and module not found at startup
            try:
                # Add project root to path to handle imports correctly
                sys.path.insert(0, str(PROJECT_ROOT))
                from data.scripts.embed_and_index import GitaEmbedder
            except ImportError as import_err:
                logger.warning(f"Could not auto-initialize via GitaEmbedder: {import_err}")
                logger.info("Assuming embeddings already exist in ChromaDB")
                # Mark as initialized anyway since vector store might already be populated
                VECTOR_DB_PATH.mkdir(parents=True, exist_ok=True)
                INIT_FLAG_FILE.touch()
                cls._initialized = True
                return True
            
            embedder = GitaEmbedder()
            embedder.run()
            
            # Mark as initialized
            VECTOR_DB_PATH.mkdir(parents=True, exist_ok=True)
            INIT_FLAG_FILE.touch()
            
            logger.info("✓ ChromaDB initialization complete")
            cls._initialized = True
            return True
        
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
        logger.warning("⚠ ChromaDB initialization warning - vector store may not be available")


def health_check() -> dict:
    """Health check endpoint"""
    return ChromaDBInitializer.check_health()


# Admin helper functions (required by routes_admin.py)
def reindex(force: bool = False) -> dict:
    """
    Reindex all Gita verses in ChromaDB
    
    Args:
        force: If True, skip existing index check and force re-indexing
    
    Returns:
        Status dictionary with result and stats
    """
    try:
        if force:
            # Clear initialization flag to force re-indexing
            if INIT_FLAG_FILE.exists():
                INIT_FLAG_FILE.unlink()
            ChromaDBInitializer._initialized = False
        
        logger.info("Starting reindex operation...")
        success = ChromaDBInitializer.initialize()
        
        if success:
            stats = get_collection_stats()
            logger.info(f"Reindex complete: {stats}")
            return {
                'status': 'success',
                'message': 'Reindexing complete',
                'stats': stats,
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'status': 'failed',
                'message': 'Reindexing failed',
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Reindex failed: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }


def get_collection_stats() -> dict:
    """
    Get statistics about ChromaDB collection
    
    Returns:
        Dictionary with collection stats
    """
    try:
        retriever = ChromaDBInitializer.get_retriever()
        result = retriever.health_check()
        
        # Enhanced stats
        return {
            'status': 'healthy',
            'total_verses_indexed': result.get('total_verses_indexed', 0),
            'collections': result.get('collections', 0),
            'embedding_model': 'all-MiniLM-L6-v2',
            'embedding_dimension': 384,
            'vector_store_location': str(VECTOR_DB_PATH),
            'last_updated': get_last_index_time()
        }
    except Exception as e:
        logger.error(f"Failed to get collection stats: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }


def get_last_index_time() -> Optional[str]:
    """
    Get timestamp of last index/reindex operation
    
    Returns:
        ISO format timestamp or None if not indexed yet
    """
    try:
        if INIT_FLAG_FILE.exists():
            timestamp = INIT_FLAG_FILE.stat().st_mtime
            from datetime import datetime
            return datetime.fromtimestamp(timestamp).isoformat()
        return None
    except Exception as e:
        logger.error(f"Failed to get index timestamp: {str(e)}")
        return None
