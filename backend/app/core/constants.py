"""
Constants
Application-wide constants and configuration values.
"""

# Gita metadata
TOTAL_CHAPTERS = 18
TOTAL_VERSES = 700

CHAPTER_NAMES = {
    1: ("Arjuna Vishaada Yoga", "अर्जुनविषादयोग", "The Yoga of Arjuna's Dejection"),
    2: ("Sankhya Yoga", "सांख्ययोग", "The Yoga of Knowledge"),
    3: ("Karma Yoga", "कर्मयोग", "The Yoga of Action"),
    4: ("Jnana Karma Sanyasa Yoga", "ज्ञानकर्मसंन्यासयोग", "The Yoga of Knowledge and Renunciation of Action"),
    5: ("Karma Sanyasa Yoga", "कर्मसंन्यासयोग", "The Yoga of Renunciation of Action"),
    6: ("Dhyana Yoga", "ध्यानयोग", "The Yoga of Meditation"),
    7: ("Jnana Vijnana Yoga", "ज्ञानविज्ञानयोग", "The Yoga of Knowledge and Wisdom"),
    8: ("Aksara Brahma Yoga", "अक्षरब्रह्मयोग", "The Yoga of the Imperishable Brahman"),
    9: ("Raja Vidya Raja Guhya Yoga", "राजविद्याराजगुह्ययोग", "The Yoga of Royal Knowledge and Royal Secret"),
    10: ("Vibhuti Yoga", "विभूतियोग", "The Yoga of Divine Manifestations"),
    11: ("Viswarupa Darsana Yoga", "विश्वरूपदर्शनयोग", "The Yoga of the Vision of the Universal Form"),
    12: ("Bhakti Yoga", "भक्तियोग", "The Yoga of Devotion"),
    13: ("Kshetra Kshetrajna Vibhaga Yoga", "क्षेत्रक्षेत्रज्ञविभागयोग", "The Yoga of the Field and the Knower of the Field"),
    14: ("Gunatraya Vibhaga Yoga", "गुणत्रयविभागयोग", "The Yoga of the Division of the Three Gunas"),
    15: ("Purushottama Yoga", "पुरुषोत्तमयोग", "The Yoga of the Supreme Person"),
    16: ("Daivasura Sampad Vibhaga Yoga", "दैवासुरसम्पद्विभागयोग", "The Yoga of the Division between Divine and Demonic Qualities"),
    17: ("Sraddhatraya Vibhaga Yoga", "श्रद्धात्रयविभागयोग", "The Yoga of the Division of Threefold Faith"),
    18: ("Moksha Sanyasa Yoga", "मोक्षसंन्यासयोग", "The Yoga of Liberation through Renunciation"),
}

# Key themes for semantic search enhancement
GITA_THEMES = [
    "dharma",
    "karma",
    "yoga",
    "bhakti",
    "jnana",
    "moksha",
    "atman",
    "brahman",
    "gunas",
    "sattva",
    "rajas",
    "tamas",
    "detachment",
    "duty",
    "action",
    "knowledge",
    "devotion",
    "meditation",
    "self-realization",
    "liberation",
]

# Speakers in the Gita
SPEAKERS = {
    "krishna": "Lord Krishna",
    "arjuna": "Arjuna",
    "sanjaya": "Sanjaya",
    "dhritarashtra": "Dhritarashtra",
}

# Embedding dimensions (depends on model)
EMBEDDING_DIMENSIONS = {
    "sentence-transformers/all-MiniLM-L6-v2": 384,
    "sentence-transformers/all-mpnet-base-v2": 768,
    "BAAI/bge-small-en-v1.5": 384,
}

# Collection name for ChromaDB
CHROMA_COLLECTION_NAME = "gita_verses"

# Maximum context length for LLM
MAX_CONTEXT_LENGTH = 4096

# Response generation settings
DEFAULT_TOP_K = 5
DEFAULT_TEMPERATURE = 0.7
MAX_RESPONSE_TOKENS = 1024
