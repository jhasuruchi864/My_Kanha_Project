"""
Retriever
Semantic search logic for finding relevant verses.
"""

from typing import List, Dict, Any, Optional

from app.config import settings
from app.logger import logger
from app.rag.vectorstore import get_vector_store
from app.rag.embeddings import get_embedding_function
from app.models.verse_models import VerseSource


async def retrieve_relevant_verses(
    query: str,
    top_k: int = 5,
    similarity_threshold: float = None,
) -> List[VerseSource]:
    """
    Retrieve relevant verses from vector store based on query.

    Args:
        query: User's question/message
        top_k: Number of results to return
        similarity_threshold: Minimum similarity score (optional)

    Returns:
        List of relevant verses with metadata
    """
    if similarity_threshold is None:
        similarity_threshold = settings.RAG_SIMILARITY_THRESHOLD

    vs = get_vector_store()
    if vs is None:
        logger.warning("Vector store not initialized")
        return []

    embedding_fn = get_embedding_function()

    try:
        # Generate query embedding
        query_embedding = embedding_fn([query])[0]

        # Query vector store
        results = vs.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        # Process results
        verses = []
        if results and results.get("ids") and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                # Convert distance to similarity (ChromaDB uses L2 distance)
                distance = results["distances"][0][i] if results.get("distances") else 0
                similarity = 1 / (1 + distance)  # Convert to similarity score

                if similarity < similarity_threshold:
                    continue

                metadata = results["metadatas"][0][i] if results.get("metadatas") else {}

                verse = VerseSource(
                    chapter=metadata.get("chapter", 0),
                    verse=metadata.get("verse", 0),
                    sanskrit=metadata.get("sanskrit", ""),
                    english=metadata.get("english", ""),
                    hindi=metadata.get("hindi", ""),
                    transliteration=metadata.get("transliteration", ""),
                    similarity_score=similarity,
                )

                verses.append(verse)

        logger.debug(f"Retrieved {len(verses)} verses for query: {query[:50]}...")
        return verses

    except Exception as e:
        logger.error(f"Error retrieving verses: {e}")
        return []


async def retrieve_by_reference(
    chapter: int,
    verse: int,
) -> Optional[VerseSource]:
    """
    Retrieve a specific verse by chapter and verse number.

    Args:
        chapter: Chapter number
        verse: Verse number

    Returns:
        Verse data if found, None otherwise
    """
    vs = get_vector_store()
    if vs is None:
        return None

    doc_id = f"ch{chapter}_v{verse}"

    try:
        result = vs.get(
            ids=[doc_id],
            include=["documents", "metadatas"],
        )

        if result and result.get("ids") and result["ids"]:
            metadata = result["metadatas"][0] if result.get("metadatas") else {}

            return VerseSource(
                chapter=metadata.get("chapter", chapter),
                verse=metadata.get("verse", verse),
                sanskrit=metadata.get("sanskrit", ""),
                english=metadata.get("english", ""),
                hindi=metadata.get("hindi", ""),
                transliteration=metadata.get("transliteration", ""),
                similarity_score=1.0,
            )

    except Exception as e:
        logger.error(f"Error retrieving verse {chapter}:{verse}: {e}")

    return None


async def search_by_keyword(
    keyword: str,
    top_k: int = 10,
) -> List[VerseSource]:
    """
    Search verses by keyword in metadata.

    Args:
        keyword: Keyword to search for
        top_k: Maximum results to return

    Returns:
        List of matching verses
    """
    vs = get_vector_store()
    if vs is None:
        return []

    try:
        # Use metadata filtering
        results = vs.get(
            where={"$contains": keyword.lower()},
            limit=top_k,
            include=["documents", "metadatas"],
        )

        verses = []
        if results and results.get("ids"):
            for i, doc_id in enumerate(results["ids"]):
                metadata = results["metadatas"][i] if results.get("metadatas") else {}

                verse = VerseSource(
                    chapter=metadata.get("chapter", 0),
                    verse=metadata.get("verse", 0),
                    sanskrit=metadata.get("sanskrit", ""),
                    english=metadata.get("english", ""),
                    hindi=metadata.get("hindi", ""),
                    transliteration=metadata.get("transliteration", ""),
                    similarity_score=1.0,
                )
                verses.append(verse)

        return verses

    except Exception as e:
        logger.error(f"Error searching by keyword: {e}")
        return []
