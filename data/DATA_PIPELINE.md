# Data Pipeline Documentation

## Overview

The data pipeline for My_Kanha_Project consists of multiple stages that transform raw Bhagavad Gita data into a production-ready, searchable knowledge base.

## Data Flow

```
Raw Data (JSON files)
    ↓
[1] Data Merging & Cleaning (merge_datasets.py)
    ↓
gita_master.json
    ↓
[2] Schema Validation (validate_schema.py)
    ↓
Validated Dataset
    ↓
[3] Embedding & Indexing (embed_and_index.py)
    ↓
ChromaDB Vector Store
    ↓
[4] RAG Retrieval (retriever.py)
    ↓
LLM System Prompt + Response
```

## Pipeline Stages

### Stage 1: Data Merging & Cleaning

**Script:** `data/scripts/merge_datasets.py`

**Purpose:**
- Merges raw JSON files from `data/raw/` directory
- Applies text cleaning (HTML removal, whitespace normalization)
- Filters verses by author/translator
- Validates output against `schema.json`

**Input Files:**
- `verse.json` - Core verse data
- `translation.json` - Multiple translations
- `commentary.json` - Verse explanations
- `chapters.json` - Chapter metadata
- `authors.json` - Author/translator information

**Output:**
- `data/cleaned/gita_master.json` - Merged dataset with all verses, translations, and commentary

**Process:**
1. Loads all raw JSON files
2. Extracts English translation (author_id: 16 - Swami Sivananda)
3. Extracts Hindi translation (author_id: 1 - Swami Ramsukhdas)
4. Extracts commentary (author_id: 1)
5. Cleans text: removes HTML tags, extra whitespace, normalizes content
6. Detects verse speaker (Krishna, Arjuna, etc.)
7. Validates against schema
8. Exports to `gita_master.json`

**Example JSON Structure:**
```json
{
  "metadata": {
    "title": "Bhagavad Gita - Master Dataset",
    "version": "1.0.0",
    "total_chapters": 18,
    "total_verses": 701
  },
  "chapters": [
    {
      "chapter_number": 1,
      "chapter_name": {
        "english": "Arjuna Visada Yoga",
        "sanskrit": "अर्जुनविषादयोग",
        "hindi": "अर्जुनविषादयोग",
        "meaning": "Arjuna's Dilemma"
      },
      "verses": [
        {
          "verse_number": 1,
          "verse_id": "1.1",
          "sanskrit_text": "धृतराष्ट्र उवाच...",
          "english_translation": "Dhritarashtra said: ...",
          "hindi_translation": "धृतराष्ट्र बोले: ...",
          "commentary": "Detailed explanation of the verse...",
          "speaker": "Dhritarashtra"
        }
      ]
    }
  ]
}
```

### Stage 2: Schema Validation

**Script:** `data/scripts/validate_schema.py`

**Purpose:**
- Validates `gita_master.json` structure against `schema.json`
- Checks data types, required fields, and constraints
- Performs integrity checks
- Generates validation report

**Schema Requirements:**
- All verses must have English translation
- All verses must have Sanskrit text
- Commentary is optional but recommended
- Verse IDs must be unique (chapter.verse)
- Chapter numbers must be 1-18

**Output:**
- `data/cleaned/validation_report.json` - Detailed validation results

### Stage 3: Embedding & Indexing

**Script:** `data/scripts/embed_and_index.py`

**Purpose:**
- Generates semantic embeddings for each verse
- Stores embeddings in ChromaDB for vector similarity search
- Enables semantic search capabilities

**Process:**
1. Loads `gita_master.json`
2. Combines English translation + commentary for embedding
3. Uses `sentence-transformers` model (default: `all-MiniLM-L6-v2`)
4. Generates 384-dimensional embeddings
5. Stores in ChromaDB with metadata:
   - Verse ID and number
   - Chapter name and number
   - Speaker
   - All translations
   - Commentary

**Embedding Model:**
- **Default:** `sentence-transformers/all-MiniLM-L6-v2`
  - Dimensions: 384
  - Speed: Fast
  - Use case: General semantic search
- **Alternative:** `sentence-transformers/all-mpnet-base-v2`
  - Dimensions: 768
  - Speed: Slower but higher quality
  - Use case: When accuracy is critical

**Usage:**
```bash
# Standard embedding
python data/scripts/embed_and_index.py

# Custom model
python data/scripts/embed_and_index.py --model sentence-transformers/all-mpnet-base-v2

# Reset and re-embed
python data/scripts/embed_and_index.py --reset

# Specify batch size
python data/scripts/embed_and_index.py --batch-size 64
```

**Output:**
- `vector_db/chroma/` - ChromaDB persistent storage with indexed verses

### Stage 4: Data Quality Validation

**Script:** `data/scripts/validate_data_quality.py`

**Purpose:**
- Comprehensive quality checks on final dataset
- Verifies completeness of translations and commentary
- Checks for missing fields and duplicates
- Generates coverage report

**Validation Checks:**
1. Structure validation (required keys, metadata)
2. Chapter validation (18 chapters, correct structure)
3. Verse completeness:
   - English translation coverage
   - Commentary coverage
   - Sanskrit text presence
   - Speaker assignment
4. Uniqueness checks (no duplicate verse IDs)
5. Field content validation (no empty strings, reasonable lengths)

**Output:**
- `data/cleaned/data_quality_report.json` - Detailed quality report

**Example Report:**
```json
{
  "statistics": {
    "total_verses": 701,
    "verses_with_english_translation": 701,
    "translation_coverage": "100%",
    "verses_with_commentary": 701,
    "commentary_coverage": "100%"
  },
  "coverage": {
    "speakers": {
      "Krishna": 500,
      "Arjuna": 100,
      "Others": 101
    }
  }
}
```

## RAG Retrieval Pipeline

### Retriever Module

**File:** `backend/app/rag/retriever.py`

**Class:** `GitaRetriever`

**Main Methods:**
1. `retrieve(query, n_results=5)` - Semantic search
2. `retrieve_by_chapter(chapter_number, query=None)` - Chapter-based retrieval
3. `retrieve_by_speaker(speaker)` - Filter by speaker
4. `health_check()` - Verify ChromaDB connection

**Example Usage:**
```python
from app.rag.retriever import retrieve

# Semantic search
verses = retrieve("Why should I work if I fail?", n_results=5)

# Returns:
[
  {
    'verse_id': '2.47',
    'chapter_name': 'Sankhya Yoga',
    'english_translation': '...',
    'commentary': '...',
    'similarity_score': 0.8542,
    'speaker': 'Krishna'
  },
  ...
]
```

### Formatter Module

**File:** `backend/app/rag/formatter.py`

**Class:** `VerseFormatter`

**Main Methods:**
1. `format_for_system_prompt(verses)` - Format for LLM system prompt
2. `format_for_chat_response(verses)` - Format for chat display
3. `format_full_verse(verse)` - Complete verse with all fields
4. `create_rag_context(verses, max_tokens)` - RAG context with token limit

**Example Output:**
```
## Relevant Bhagavad Gita References:

**Verse 1: 2.47** (Chapter 2, Verse 47)
*Sankhya Yoga*

**Sanskrit:** कर्मण्येवाधिकारस्ते मा फलेषु कदाचन...

**Translation:** You have a right to perform your prescribed work, but you are not entitled to the fruits of your actions...

**Commentary:** The Lord emphasizes that our duty is to act properly...

**Spoken by: Krishna**
```

## ChromaDB Initialization

**File:** `backend/app/rag/init_chromadb.py`

**Features:**
- Auto-initializes ChromaDB on application startup
- Checks for existing index (prevents re-embedding)
- Lazy loading of embedding model
- Health check functionality

**Integration with FastAPI:**
```python
from fastapi import FastAPI
from app.rag.init_chromadb import startup_event, health_check

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    startup_event()

@app.get("/health")
async def get_health():
    return health_check()
```

## Regenerating Embeddings

### When to Regenerate:
- After adding new verses to dataset
- When switching embedding models
- After major dataset updates
- To update similarity thresholds

### Process:
1. Update `gita_master.json` with new data
2. Run validation:
   ```bash
   python data/scripts/validate_data_quality.py
   ```
3. Clear old embeddings (optional):
   ```bash
   rm -rf vector_db/chroma/
   ```
4. Re-embed:
   ```bash
   python data/scripts/embed_and_index.py --reset
   ```
5. Verify:
   ```bash
   python -c "from app.rag.retriever import get_retriever; print(get_retriever().health_check())"
   ```

## Performance Metrics

### Embedding Generation:
- Time: ~30-60 seconds for 701 verses
- Model size: ~100MB (all-MiniLM-L6-v2)
- Storage: ~100MB (embeddings + metadata)

### Search Performance:
- Query time: <100ms for semantic search
- Throughput: >1000 queries/second
- Typical result count: 3-5 verses per query

### Storage:
- `gita_master.json`: ~3MB
- ChromaDB: ~100MB
- Total: ~103MB

## Troubleshooting

### Issue: Embeddings not being used
**Solution:**
```bash
# Verify ChromaDB is initialized
python -c "from app.rag.init_chromadb import ChromaDBInitializer; ChromaDBInitializer.initialize()"
```

### Issue: Low search quality
**Solution:**
- Try a better embedding model: `--model sentence-transformers/all-mpnet-base-v2`
- Re-embed with new model
- Adjust query formulation (be more specific)

### Issue: Memory issues during embedding
**Solution:**
- Reduce batch size: `--batch-size 16`
- Use CPU instead of GPU: `--device cpu`
- Split into smaller chunks

## Future Enhancements

1. **Hybrid Search:** Combine semantic + keyword search
2. **Multi-language Support:** Index all three languages separately
3. **Speaker-specific Context:** Prioritize Krishna's verses for certain queries
4. **Caching:** Cache frequent queries
5. **Fine-tuning:** Fine-tune embedding model on Gita-specific content
6. **Monitoring:** Track query performance and user feedback

## References

- ChromaDB: https://www.trychroma.com/
- Sentence Transformers: https://www.sbert.net/
- Bhagavad Gita Data: Original sources in `data/raw/`

This document describes the complete data processing pipeline for the My Kanha Project, from raw dataset files to vector-indexed content ready for RAG retrieval.

---

## Pipeline Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌──────────────────┐
│   Raw Data      │────▶│  Merge & Clean   │────▶│   Validate &    │────▶│  Vector Index    │
│   (JSON files)  │     │  (merge_datasets)│     │   Quality Check │     │  (embed_and_index)│
└─────────────────┘     └──────────────────┘     └─────────────────┘     └──────────────────┘
       │                        │                        │                        │
       ▼                        ▼                        ▼                        ▼
  verse.json              gita_master.json         Quality Report         ChromaDB Index
  translation.json        gita_master.csv          (console/JSON)         (vector_db/chroma)
  commentary.json
  chapters.json
```

---

## Directory Structure

```
data/
├── raw/                          # Raw source data (user-provided)
│   ├── verse.json                # Sanskrit verses with IDs
│   ├── translation.json          # Translations by multiple authors
│   ├── commentary.json           # Commentary by multiple authors
│   └── chapters.json             # Chapter metadata
│
├── cleaned/                      # Processed data outputs
│   ├── gita_master.json          # Merged master dataset
│   ├── gita_master.csv           # CSV export for analysis
│   └── schema.json               # JSON schema for validation
│
└── scripts/                      # Processing scripts
    ├── merge_datasets.py         # Step 1: Merge raw data
    ├── clean_text.py             # Step 2: Clean text (optional)
    ├── validate_schema.py        # Step 3: Validate against schema
    ├── validate_data_quality.py  # Step 4: Quality checks
    └── embed_and_index.py        # Step 5: Vector embedding
```

---

## Pipeline Steps

### Step 1: Merge Datasets (`merge_datasets.py`)

**Purpose:** Combines raw JSON files into a unified master dataset with filtered translations.

**Input Files:**
- `raw/verse.json` - Sanskrit verses with IDs, text, transliteration
- `raw/translation.json` - Translations in multiple languages by various authors
- `raw/commentary.json` - Commentary texts
- `raw/chapters.json` - Chapter metadata and summaries

**Key Filtering Rules:**
| Content Type | Author ID | Author Name |
|--------------|-----------|-------------|
| English Translation | 16 | Swami Sivananda |
| Hindi Translation | 1 | Swami Ramsukhdas |
| Hindi Commentary | 1 | Swami Ramsukhdas |
| English Commentary | 16 | Swami Sivananda |

**Text Cleaning Applied:**
- HTML tags removed (`<p>`, `<br>`, etc.)
- Newline characters (`\n`, `\r`) replaced with spaces
- Multiple whitespace normalized
- HTML entities decoded

**Output:** `cleaned/gita_master.json`, `cleaned/gita_master.csv`

**Usage:**
```bash
cd data/scripts
python merge_datasets.py
```

---

### Step 2: Text Cleaning (`clean_text.py`)

**Purpose:** Additional text cleaning pass if needed after merge.

**Cleaning Operations:**
- HTML tag removal (including self-closing tags)
- Newline and carriage return removal
- Whitespace normalization
- Devanagari text preservation
- Sanskrit text structure preservation (verse separators)

**Usage:**
```bash
python clean_text.py
```

---

### Step 3: Schema Validation (`validate_schema.py`)

**Purpose:** Validates master dataset against JSON schema and checks data integrity.

**Validation Checks:**
- JSON Schema compliance (Draft 7)
- Required field presence
- Chapter numbering sequence (1-18)
- Verse numbering within chapters
- No duplicate verse numbers
- Metadata count consistency

**Usage:**
```bash
python validate_schema.py
```

---

### Step 4: Data Quality Validation (`validate_data_quality.py`)

**Purpose:** Comprehensive quality checks for production readiness.

**Quality Checks:**

| Category | Check |
|----------|-------|
| **Coverage** | All 701 verses present |
| **Translations** | English (author_id=16) coverage |
| **Translations** | Hindi (author_id=1) coverage |
| **Commentary** | Hindi commentary coverage |
| **Text Quality** | No HTML remnants |
| **Text Quality** | No newline artifacts |
| **Text Quality** | No encoding issues |
| **Text Quality** | Minimum length validation |

**Expected Verse Counts per Chapter:**
```
Ch 1: 47   Ch 7: 30   Ch 13: 35
Ch 2: 72   Ch 8: 28   Ch 14: 27
Ch 3: 43   Ch 9: 34   Ch 15: 20
Ch 4: 42   Ch 10: 42  Ch 16: 24
Ch 5: 29   Ch 11: 55  Ch 17: 28
Ch 6: 47   Ch 12: 20  Ch 18: 78
                      ─────────
                      Total: 701
```

**Usage:**
```bash
# Full validation
python validate_data_quality.py

# Verbose output
python validate_data_quality.py --verbose

# Save report to JSON
python validate_data_quality.py --output quality_report.json

# Check only raw data
python validate_data_quality.py --raw-only
```

---

### Step 5: Vector Embedding & Indexing (`embed_and_index.py`)

**Purpose:** Generates embeddings and creates ChromaDB vector index for RAG retrieval.

**Configuration:**
| Setting | Default | Description |
|---------|---------|-------------|
| Model | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model |
| Dimension | 384 | Vector dimension |
| Device | `cpu` | Compute device (cpu/cuda) |
| Batch Size | 32 | Embedding batch size |
| Collection | `gita_verses` | ChromaDB collection name |
| Similarity | Cosine | Distance metric |

**Embedding Text Composition:**
For each verse, the following fields are combined:
```
{chapter_name} | {english_translation} | {hindi_translation} |
{transliteration} | Meanings: {word_meanings} |
Commentary: {commentary} | Keywords: {keywords}
```

**Document ID Format:** `ch{chapter}_v{verse}` (e.g., `ch2_v47`)

**Metadata Stored:**
```json
{
    "chapter": 2,
    "verse": 47,
    "chapter_name_en": "Sankhya Yoga",
    "chapter_name_hi": "सांख्ययोग",
    "sanskrit": "कर्मण्येवाधिकारस्ते...",
    "english": "You have the right to work only...",
    "hindi": "कर्म करने में ही तुम्हारा अधिकार है...",
    "transliteration": "karmaṇy evādhikāras te...",
    "word_meanings": "karmaṇi—in work; eva—only...",
    "speaker": "Krishna",
    "keywords": "karma,duty,action,attachment"
}
```

**Output:** ChromaDB index at `vector_db/chroma/`

**Usage:**
```bash
# Basic indexing
python embed_and_index.py

# Reset existing index
python embed_and_index.py --reset

# Use GPU
python embed_and_index.py --device cuda

# Custom model
python embed_and_index.py --model BAAI/bge-small-en-v1.5

# Larger batches (for GPU)
python embed_and_index.py --device cuda --batch-size 64
```

---

## Master Dataset Schema

### Top-Level Structure
```json
{
    "metadata": {
        "title": "Bhagavad Gita - Master Dataset",
        "version": "1.0.0",
        "languages": ["sanskrit", "english", "hindi"],
        "total_chapters": 18,
        "total_verses": 701,
        "sources": {...},
        "created_at": "ISO timestamp",
        "last_updated": "ISO timestamp"
    },
    "chapters": [...]
}
```

### Chapter Structure
```json
{
    "chapter_number": 2,
    "chapter_name": {
        "sanskrit": "सांख्ययोग",
        "english": "Sankhya Yoga",
        "hindi": "सांख्ययोग",
        "transliterated": "Sāṅkhya Yoga",
        "meaning": "Yoga of Knowledge"
    },
    "chapter_summary": "English summary...",
    "chapter_summary_hindi": "Hindi summary...",
    "verses": [...]
}
```

### Verse Structure
```json
{
    "verse_number": 47,
    "sanskrit": "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन।...",
    "transliteration": "karmaṇy evādhikāras te mā phaleṣu kadācana...",
    "word_meanings": "karmaṇi—in work; eva—only...",
    "english": "You have the right to work only...",
    "hindi": "कर्म करने में ही तुम्हारा अधिकार है...",
    "commentary": {
        "hindi": "Commentary in Hindi...",
        "english": "Commentary in English..."
    },
    "speaker": "Krishna",
    "keywords": ["karma", "duty", "action"]
}
```

---

## Running the Complete Pipeline

### Quick Start
```bash
# Navigate to scripts directory
cd data/scripts

# Step 1: Merge raw data
python merge_datasets.py

# Step 2: (Optional) Additional cleaning
python clean_text.py

# Step 3: Validate schema
python validate_schema.py

# Step 4: Quality check
python validate_data_quality.py

# Step 5: Create vector index
python embed_and_index.py
```

### Full Pipeline with Options
```bash
# Merge and create master dataset
python merge_datasets.py

# Validate with detailed output
python validate_schema.py
python validate_data_quality.py --verbose --output quality_report.json

# Create vector index with GPU
python embed_and_index.py --device cuda --batch-size 64

# Verify index
python embed_and_index.py  # Will run verification queries
```

---

## Integration with Backend

The processed data integrates with the FastAPI backend:

### Data Flow
```
ChromaDB Index (vector_db/chroma)
        │
        ▼
┌───────────────────────────────┐
│ backend/app/rag/retriever.py  │
│   - retrieve_relevant_verses() │
│   - semantic search            │
└───────────────────────────────┘
        │
        ▼
┌───────────────────────────────┐
│ backend/app/rag/formatter.py  │
│   - format_for_krishna_response()│
│   - prepare LLM context        │
└───────────────────────────────┘
        │
        ▼
┌───────────────────────────────┐
│ backend/app/llm/client.py     │
│   - generate response          │
│   - Krishna persona            │
└───────────────────────────────┘
```

### Backend Initialization
When the FastAPI backend starts, it:
1. Loads ChromaDB from `vector_db/chroma/`
2. Initializes the embedding model
3. Makes the retriever available to API endpoints

---

## Troubleshooting

### Common Issues

**1. Missing raw data files**
```
Error: File not found: data/raw/verse.json
Solution: Ensure all raw JSON files are in data/raw/
```

**2. Translation coverage warnings**
```
Warning: English translations missing for X verses
Solution: Check if author_id=16 exists for all verses in translation.json
```

**3. ChromaDB initialization failure**
```
Error: Could not initialize ChromaDB
Solution: Ensure vector_db/chroma directory is writable
```

**4. Embedding model download issues**
```
Error: Could not load model
Solution: Check internet connection, or pre-download model
```

### Resetting the Pipeline

To completely reset and rebuild:
```bash
# Remove processed files
rm data/cleaned/gita_master.json
rm data/cleaned/gita_master.csv
rm -rf vector_db/chroma/*

# Re-run pipeline
python merge_datasets.py
python validate_data_quality.py
python embed_and_index.py --reset
```

---

## Dependencies

### Python Packages
```
# Core
json (builtin)
pathlib (builtin)
logging (builtin)

# Data Processing
jsonschema>=4.17.0

# Vector Database
chromadb>=0.4.22

# Embeddings
sentence-transformers>=2.2.2
torch>=2.0.0
```

### Installation
```bash
pip install jsonschema chromadb sentence-transformers torch
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | Initial | Complete pipeline implementation |

---

## References

- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Sentence Transformers](https://www.sbert.net/)
- [JSON Schema](https://json-schema.org/)
- Bhagavad Gita API Dataset
