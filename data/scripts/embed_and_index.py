"""
Embed and Index Script
Generates embeddings for Gita verses and stores them in ChromaDB for RAG retrieval.

Features:
- Reads gita_master.json
- Generates embeddings using sentence-transformers
- Stores embeddings + metadata in ChromaDB
- Creates searchable index for semantic search
- Verification with test query

Usage:
    python embed_and_index.py [--reset] [--model MODEL] [--device DEVICE] [--batch-size SIZE]

Options:
    --reset         Clear existing index before indexing
    --model         Embedding model name (default: sentence-transformers/all-MiniLM-L6-v2)
    --device        Device to use: cpu or cuda (default: cpu)
    --batch-size    Batch size for embedding generation (default: 32)
"""

# Disable TensorFlow to avoid compatibility issues
import os
os.environ['USE_TF'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import json
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import shutil

try:
    from sentence_transformers import SentenceTransformer
    import chromadb
    from chromadb.config import Settings
except ImportError:
    logger = logging.getLogger(__name__)
    logger.error("Required packages not installed. Please run:")
    logger.error("pip install sentence-transformers chromadb")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).parent.parent.parent  # My_Kanha_Project
DATA_DIR = BASE_DIR / "data" / "cleaned"
VECTOR_DB_DIR = BASE_DIR / "vector_db" / "chroma"
MASTER_FILE = DATA_DIR / "gita_master.json"

# Ensure directories exist
VECTOR_DB_DIR.parent.mkdir(parents=True, exist_ok=True)
VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)

# Default Configuration
DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_DEVICE = "cpu"
DEFAULT_BATCH_SIZE = 32
COLLECTION_NAME = "gita_verses"

# Embedding dimensions for known models
EMBEDDING_DIMENSIONS = {
    "sentence-transformers/all-MiniLM-L6-v2": 384,
    "sentence-transformers/all-mpnet-base-v2": 768,
    "BAAI/bge-small-en-v1.5": 384,
    "BAAI/bge-base-en-v1.5": 768,
}


# ============ Data Loading ============

def load_master_data(filepath: Path) -> Dict[str, Any]:
    """
    Load the master Gita dataset.

    Args:
        filepath: Path to gita_master.json

    Returns:
        Parsed JSON data

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Master file not found: {filepath}")

    logger.info(f"Loading data from {filepath}...")

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total_chapters = len(data.get('chapters', []))
    total_verses = data.get('metadata', {}).get('total_verses', 0)
    logger.info(f"Loaded: {total_chapters} chapters, {total_verses} verses")

    return data


# ============ Document Preparation ============

def create_embedding_text(verse: Dict, chapter_info: Dict) -> str:
    """
    Create combined text for embedding from verse data.

    Combines: chapter name + translations + transliteration + commentary + keywords

    Args:
        verse: Verse data dictionary
        chapter_info: Chapter metadata

    Returns:
        Combined text string for embedding
    """
    parts = []

    # Add chapter context
    chapter_name = chapter_info.get('chapter_name', {})
    if chapter_name.get('english'):
        parts.append(f"Chapter: {chapter_name['english']}")

    # Add English translation (primary for semantic search)
    if verse.get('english'):
        parts.append(verse['english'])

    # Add Hindi translation
    if verse.get('hindi'):
        parts.append(verse['hindi'])

    # Add transliteration
    if verse.get('transliteration'):
        parts.append(verse['transliteration'])

    # Add word meanings (helpful for concept search)
    if verse.get('word_meanings'):
        # Truncate if too long
        meanings = verse['word_meanings'][:300]
        parts.append(f"Meanings: {meanings}")

    # Add commentary (truncated)
    commentary = verse.get('commentary', {})
    if commentary.get('english'):
        comm = commentary['english'][:400]
        parts.append(f"Commentary: {comm}")
    elif commentary.get('hindi'):
        comm = commentary['hindi'][:400]
        parts.append(f"Commentary: {comm}")

    # Add keywords
    keywords = verse.get('keywords', [])
    if keywords:
        parts.append(f"Keywords: {', '.join(keywords)}")

    return " | ".join(parts)


def prepare_documents(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Prepare documents from Gita data for vector storage.

    Args:
        data: Full gita_master.json data

    Returns:
        List of document dictionaries with id, text, and metadata
    """
    documents = []

    for chapter in data.get('chapters', []):
        chapter_num = chapter.get('chapter_number', 0)
        chapter_name = chapter.get('chapter_name', {})

        for verse in chapter.get('verses', []):
            verse_num = verse.get('verse_number', 0)

            # Create document ID
            doc_id = f"ch{chapter_num}_v{verse_num}"

            # Create combined text for embedding
            text = create_embedding_text(verse, chapter)

            if not text.strip():
                logger.warning(f"Empty text for {doc_id}, skipping...")
                continue

            # Extract metadata
            metadata = {
                "chapter": chapter_num,
                "verse": verse_num,
                "chapter_name_en": chapter_name.get('english', ''),
                "chapter_name_hi": chapter_name.get('hindi', '') or chapter_name.get('sanskrit', ''),
                "sanskrit": verse.get('sanskrit', ''),
                "english": verse.get('english', ''),
                "hindi": verse.get('hindi', ''),
                "transliteration": verse.get('transliteration', ''),
                "word_meanings": verse.get('word_meanings', '')[:500],  # Truncate
                "speaker": verse.get('speaker', 'Unknown'),
                "keywords": ','.join(verse.get('keywords', [])),
            }

            documents.append({
                "id": doc_id,
                "text": text,
                "metadata": metadata
            })

    logger.info(f"Prepared {len(documents)} documents")
    return documents


# ============ ChromaDB Operations ============

def initialize_chroma(persist_dir: Path, reset: bool = False):
    """
    Initialize ChromaDB client and collection.

    Args:
        persist_dir: Directory for persistent storage
        reset: If True, delete existing collection first

    Returns:
        ChromaDB collection object
    """
    try:
        import chromadb
        from chromadb.config import Settings
    except ImportError:
        logger.error("chromadb not installed. Install with: pip install chromadb")
        sys.exit(1)

    # Ensure directory exists
    persist_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Initializing ChromaDB at {persist_dir}...")

    # Create persistent client
    client = chromadb.PersistentClient(
        path=str(persist_dir),
        settings=Settings(
            anonymized_telemetry=False,
            allow_reset=True,
        )
    )

    # Reset if requested
    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
            logger.info(f"Deleted existing collection: {COLLECTION_NAME}")
        except Exception:
            pass  # Collection doesn't exist

    # Get or create collection with cosine similarity
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    existing_count = collection.count()
    logger.info(f"Collection '{COLLECTION_NAME}' ready. Existing documents: {existing_count}")

    return collection, client


# ============ Embedding Generation ============

def load_embedding_model(model_name: str, device: str):
    """
    Load the SentenceTransformer embedding model.

    Args:
        model_name: Model name/path
        device: Device to use (cpu/cuda)

    Returns:
        SentenceTransformer model instance
    """
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        logger.error("sentence-transformers not installed. Install with: pip install sentence-transformers")
        sys.exit(1)

    logger.info(f"Loading embedding model: {model_name}")
    logger.info(f"Device: {device}")

    model = SentenceTransformer(model_name, device=device)

    # Get embedding dimension
    dim = EMBEDDING_DIMENSIONS.get(model_name, model.get_sentence_embedding_dimension())
    logger.info(f"Embedding dimension: {dim}")

    return model


def generate_embeddings(
    texts: List[str],
    model,
    batch_size: int = 32,
    show_progress: bool = True
) -> List[List[float]]:
    """
    Generate embeddings for a list of texts.

    Args:
        texts: List of text strings
        model: SentenceTransformer model
        batch_size: Batch size for encoding
        show_progress: Whether to show progress bar

    Returns:
        List of embedding vectors
    """
    logger.info(f"Generating embeddings for {len(texts)} texts...")

    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=show_progress,
        convert_to_numpy=True
    )

    return embeddings.tolist()


# ============ Indexing ============

def index_documents(
    collection,
    documents: List[Dict],
    embeddings: List[List[float]],
    batch_size: int = 100
):
    """
    Index documents into ChromaDB.

    Args:
        collection: ChromaDB collection
        documents: List of document dicts
        embeddings: List of embedding vectors
        batch_size: Batch size for adding
    """
    logger.info(f"Indexing {len(documents)} documents to ChromaDB...")

    # Prepare data
    ids = [doc['id'] for doc in documents]
    texts = [doc['text'] for doc in documents]
    metadatas = [doc['metadata'] for doc in documents]

    # Add in batches
    total = len(documents)
    for i in range(0, total, batch_size):
        end = min(i + batch_size, total)

        collection.add(
            ids=ids[i:end],
            embeddings=embeddings[i:end],
            documents=texts[i:end],
            metadatas=metadatas[i:end]
        )

        if (i + batch_size) % 200 == 0 or end == total:
            logger.info(f"Indexed {end}/{total} documents")

    logger.info(f"Indexing complete. Total documents: {collection.count()}")


# ============ Verification ============

def verify_index(collection, model) -> Dict[str, Any]:
    """
    Verify the index with a test query.

    Args:
        collection: ChromaDB collection
        model: Embedding model for query

    Returns:
        Verification results
    """
    logger.info("\nVerifying index with test queries...")

    test_queries = [
        "How to find peace of mind?",
        "What is the meaning of duty and action?",
        "How to overcome fear and anxiety?",
    ]

    results = {
        "total_documents": collection.count(),
        "test_results": []
    }

    for query in test_queries:
        # Generate query embedding
        query_embedding = model.encode([query])[0].tolist()

        # Query collection
        response = collection.query(
            query_embeddings=[query_embedding],
            n_results=3,
            include=["documents", "metadatas", "distances"]
        )

        if response['ids'] and response['ids'][0]:
            top_result = {
                "query": query,
                "top_match": {
                    "id": response['ids'][0][0],
                    "chapter": response['metadatas'][0][0].get('chapter'),
                    "verse": response['metadatas'][0][0].get('verse'),
                    "distance": response['distances'][0][0],
                    "similarity": 1 / (1 + response['distances'][0][0])  # Convert L2 to similarity
                }
            }
            results["test_results"].append(top_result)

            logger.info(f"\nQuery: \"{query}\"")
            logger.info(f"  Top Result: Chapter {top_result['top_match']['chapter']}, "
                       f"Verse {top_result['top_match']['verse']} "
                       f"(similarity: {top_result['top_match']['similarity']:.3f})")

    return results


# ============ Main ============

def main():
    """Main entry point."""
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Generate embeddings and index Gita verses to ChromaDB"
    )
    parser.add_argument(
        '--reset', action='store_true',
        help='Clear existing index before indexing'
    )
    parser.add_argument(
        '--model', type=str, default=DEFAULT_MODEL,
        help=f'Embedding model name (default: {DEFAULT_MODEL})'
    )
    parser.add_argument(
        '--device', type=str, default=DEFAULT_DEVICE,
        choices=['cpu', 'cuda'],
        help=f'Device to use (default: {DEFAULT_DEVICE})'
    )
    parser.add_argument(
        '--batch-size', type=int, default=DEFAULT_BATCH_SIZE,
        help=f'Batch size for embedding (default: {DEFAULT_BATCH_SIZE})'
    )

    args = parser.parse_args()

    # Print header
    logger.info("=" * 60)
    logger.info("BHAGAVAD GITA VECTOR INDEXER")
    logger.info("=" * 60)

    start_time = datetime.now()

    try:
        # Step 1: Load data
        data = load_master_data(MASTER_FILE)

        # Step 2: Initialize ChromaDB
        collection, client = initialize_chroma(VECTOR_DB_DIR, reset=args.reset)

        # Check if already indexed
        existing_count = collection.count()
        expected_count = data.get('metadata', {}).get('total_verses', 0)

        if existing_count > 0 and not args.reset:
            logger.info(f"\nCollection already has {existing_count} documents.")
            logger.info("Use --reset flag to re-index from scratch.")

            # Still run verification
            model = load_embedding_model(args.model, args.device)
            verify_index(collection, model)

            logger.info("\n" + "=" * 60)
            logger.info("INDEX VERIFICATION COMPLETE")
            logger.info("=" * 60)
            return

        # Step 3: Load embedding model
        model = load_embedding_model(args.model, args.device)

        # Step 4: Prepare documents
        documents = prepare_documents(data)

        if not documents:
            logger.error("No documents to index!")
            sys.exit(1)

        # Step 5: Generate embeddings
        texts = [doc['text'] for doc in documents]
        embeddings = generate_embeddings(texts, model, batch_size=args.batch_size)

        # Step 6: Index to ChromaDB
        index_documents(collection, documents, embeddings)

        # Step 7: Verify
        verification = verify_index(collection, model)

        # Print summary
        elapsed = (datetime.now() - start_time).total_seconds()

        logger.info("\n" + "=" * 60)
        logger.info("INDEXING COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Collection: {COLLECTION_NAME}")
        logger.info(f"Total Documents: {verification['total_documents']}")
        logger.info(f"Embedding Model: {args.model}")
        logger.info(f"Embedding Dimension: {EMBEDDING_DIMENSIONS.get(args.model, 'unknown')}")
        logger.info(f"Persist Directory: {VECTOR_DB_DIR}")
        logger.info(f"Time Elapsed: {elapsed:.1f} seconds")
        logger.info("=" * 60)

    except FileNotFoundError as e:
        logger.error(str(e))
        logger.info("Run merge_datasets.py first to create the master dataset.")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
