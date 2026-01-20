"""
Data Ingestion
Loads Gita data from JSON and ingests into vector store.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.config import settings
from app.logger import logger
from app.rag.vectorstore import get_vector_store, initialize_chroma
from app.rag.embeddings import get_embedding_function
from app.core.constants import CHROMA_COLLECTION_NAME


# Ingestion status tracking
_ingestion_status = {
    "last_ingested": None,
    "total_documents": 0,
    "status": "not_started",
}


async def initialize_vector_store():
    """Initialize the vector store on application startup."""
    global _ingestion_status

    try:
        _ingestion_status["status"] = "initializing"

        # Initialize ChromaDB
        initialize_chroma()

        # Check if data needs to be ingested
        vs = get_vector_store()
        if vs is not None:
            count = vs.count()
            if count > 0:
                _ingestion_status["total_documents"] = count
                _ingestion_status["status"] = "ready"
                logger.info(f"Vector store ready with {count} documents")
                return

        # Ingest data if store is empty
        await ingest_gita_data()

    except Exception as e:
        _ingestion_status["status"] = "error"
        logger.error(f"Failed to initialize vector store: {e}")
        raise


async def ingest_gita_data():
    """Ingest Gita master data into vector store."""
    global _ingestion_status

    _ingestion_status["status"] = "ingesting"

    data_path = Path(settings.DATA_PATH) / "gita_master.json"

    if not data_path.exists():
        logger.warning(f"Data file not found: {data_path}")
        _ingestion_status["status"] = "no_data"
        return

    logger.info(f"Loading data from {data_path}")

    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    documents = prepare_documents(data)
    logger.info(f"Prepared {len(documents)} documents for ingestion")

    if not documents:
        _ingestion_status["status"] = "no_documents"
        return

    # Get vector store and add documents
    vs = get_vector_store()
    embedding_fn = get_embedding_function()

    # Prepare data for ChromaDB
    ids = [doc["id"] for doc in documents]
    texts = [doc["text"] for doc in documents]
    metadatas = [doc["metadata"] for doc in documents]

    # Generate embeddings and add to store
    embeddings = embedding_fn(texts)

    vs.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )

    _ingestion_status["total_documents"] = len(documents)
    _ingestion_status["last_ingested"] = datetime.utcnow().isoformat()
    _ingestion_status["status"] = "ready"

    logger.info(f"Successfully ingested {len(documents)} documents")


def prepare_documents(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Prepare documents from Gita data for vector storage.

    Each verse becomes a document with combined text for embedding.
    """
    documents = []

    for chapter in data.get("chapters", []):
        chapter_num = chapter.get("chapter_number", 0)
        chapter_name = chapter.get("chapter_name", {})

        for verse in chapter.get("verses", []):
            verse_num = verse.get("verse_number", 0)

            # Combine text for embedding (prioritize English for semantic search)
            combined_text = create_combined_text(verse, chapter_name)

            if not combined_text.strip():
                continue

            doc_id = f"ch{chapter_num}_v{verse_num}"

            document = {
                "id": doc_id,
                "text": combined_text,
                "metadata": {
                    "chapter": chapter_num,
                    "verse": verse_num,
                    "chapter_name_en": chapter_name.get("english", ""),
                    "chapter_name_hi": chapter_name.get("hindi", ""),
                    "sanskrit": verse.get("sanskrit", ""),
                    "english": verse.get("english", ""),
                    "hindi": verse.get("hindi", ""),
                    "transliteration": verse.get("transliteration", ""),
                    "speaker": verse.get("speaker", ""),
                    "keywords": ",".join(verse.get("keywords", [])),
                },
            }

            documents.append(document)

    return documents


def create_combined_text(verse: Dict, chapter_name: Dict) -> str:
    """Create combined text for embedding from verse data."""
    parts = []

    # Add chapter context
    if chapter_name.get("english"):
        parts.append(f"Chapter: {chapter_name['english']}")

    # Add English translation (primary for semantic search)
    if verse.get("english"):
        parts.append(verse["english"])

    # Add Hindi translation
    if verse.get("hindi"):
        parts.append(verse["hindi"])

    # Add transliteration for searchability
    if verse.get("transliteration"):
        parts.append(verse["transliteration"])

    # Add keywords
    if verse.get("keywords"):
        parts.append(f"Keywords: {', '.join(verse['keywords'])}")

    # Add commentary summary if available
    commentary = verse.get("commentary", {})
    if isinstance(commentary, dict) and commentary.get("general"):
        # Truncate commentary for embedding
        general = commentary["general"][:500]
        parts.append(f"Commentary: {general}")

    return " | ".join(parts)


async def reingest_data() -> Dict[str, Any]:
    """Re-ingest data (for admin endpoint)."""
    global _ingestion_status

    # Clear existing data
    vs = get_vector_store()
    if vs is not None:
        # Delete all documents
        vs.delete(where={})

    _ingestion_status = {
        "last_ingested": None,
        "total_documents": 0,
        "status": "not_started",
    }

    # Re-ingest
    await ingest_gita_data()

    return _ingestion_status


async def get_ingestion_status() -> Dict[str, Any]:
    """Get current ingestion status."""
    return _ingestion_status.copy()
