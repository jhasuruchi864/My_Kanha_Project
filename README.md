# 🕉️ My Kanha - AI Spiritual Companion

> *"Converse with Krishna through the timeless wisdom of the Bhagavad Gita"*

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**My Kanha** is an AI-powered spiritual chatbot that brings the profound teachings of the Bhagavad Gita to life through conversational AI. Users can ask life's deepest questions and receive guidance grounded in authentic scripture, complete with verse citations.

---

## ✨ Features

### 🎯 **Currently Working**
- ✅ **Intelligent Chat Interface** - Natural conversations with AI Krishna
- ✅ **RAG-Powered Responses** - Answers grounded in 701 Bhagavad Gita verses
- ✅ **Verse Citations** - Every response includes relevant scripture references
- ✅ **Streaming Support** - Real-time SSE streaming for responsive experience
- ✅ **Multilingual** - English & Hindi language detection and responses
- ✅ **Safety Filters** - Content moderation for appropriate spiritual guidance
- ✅ **Vector Search** - Semantic search across all 18 chapters using ChromaDB
- ✅ **Local LLM** - Privacy-first with Ollama (llama3 model)
- ✅ **Admin Dashboard** - Reindexing, stats, and system monitoring
- ✅ **API Documentation** - Interactive Swagger/ReDoc at `/docs`
- ✅ **Comprehensive Testing** - 24 passing unit tests

### 📊 **Technical Highlights**
- **701 verses indexed** across 18 chapters
- **384-dimensional embeddings** using sentence-transformers
- **Cosine similarity search** for semantic retrieval
- **5 verses per query** for context-rich responses
- **100% data coverage** validated with quality reports

---

## 🏗️ Architecture

```
My_Kanha_Project/
│
├── 📁 data/                    # Data Engineering Pipeline
│   ├── raw/                    # Original JSON datasets (7 sources)
│   ├── cleaned/                # Unified gita_master.json (701 verses)
│   └── scripts/                # ETL & validation scripts
│
├── 📁 backend/                 # FastAPI REST API
│   ├── app/
│   │   ├── api/               # Route handlers (chat, health, admin)
│   │   ├── rag/               # RAG pipeline (retriever, embeddings, formatter)
│   │   ├── llm/               # LLM integration (Ollama client)
│   │   ├── models/            # Pydantic schemas
│   │   ├── core/              # Safety rules & prompt templates
│   │   └── utils/             # Language detection & text processing
│   ├── tests/                 # Pytest test suite
│   └── requirements.txt
│
├── 📁 vector_db/               # ChromaDB Persistent Storage
│   └── chroma/                # Indexed verse embeddings
│
├── 📁 web_app/                 # Frontend (HTML/CSS/JS)
└── 📁 mobile_app/              # Flutter Mobile App (Planned)
```

---

## 🚀 Quick Start

### Prerequisites
```bash
Python 3.11+
Ollama (for local LLM)
Git
```

### 1️⃣ Clone & Setup

```bash
# Clone repository
git clone <repository-url>
cd My_Kanha_Project

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
cd backend
pip install -r requirements.txt
```

### 2️⃣ Install Ollama & Pull Model

```bash
# Download Ollama from https://ollama.ai
# Then pull the llama3 model
ollama pull llama3

# Verify Ollama is running
ollama list
```

### 3️⃣ Initialize Vector Database

```bash
# Embeddings are already indexed in vector_db/
# To rebuild from scratch:
cd data/scripts
python embed_and_index.py
```

### 4️⃣ Start Backend Server

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5️⃣ Test the API

```bash
# Health check
curl http://localhost:8000/health/chroma

# Chat request
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is dharma?",
    "language": "english",
    "top_k": 5
  }'
```

### 6️⃣ Open API Docs
Navigate to: **http://localhost:8000/docs**

---

---

## 📡 API Endpoints

### **Chat Endpoints**

#### `POST /chat`
Main chat endpoint with full response

**Request:**
```json
{
  "message": "How can I find peace of mind?",
  "language": "english",
  "top_k": 5,
  "conversation_history": [
    {"role": "user", "content": "Previous question"},
    {"role": "assistant", "content": "Previous answer"}
  ]
}
```

**Response:**
```json
{
  "response": "Dear seeker, peace of mind comes from...",
  "sources": [
    {
      "chapter": 2,
      "verse": 66,
      "sanskrit": "नास्ति बुद्धिरयुक्तस्य...",
      "english": "One who is not connected with the Supreme...",
      "hindi": "जो व्यक्ति भगवान से जुड़ा नहीं...",
      "similarity_score": 0.89
    }
  ],
  "language": "english",
  "metadata": {
    "model": "llama3",
    "context_verses": 5,
    "verse_references": ["2:66", "6:35", "12:13"]
  }
}
```

#### `POST /chat/stream`
Streaming chat with Server-Sent Events (SSE)

**Request:** Same as `/chat`

**Response:** (Event stream)
```
data: {"content": "Dear", "is_complete": false}
data: {"content": " seeker", "is_complete": false}
...
data: {"content": "", "is_complete": true, "sources": [...]}
```

---

### **Health Endpoints**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Welcome message & API info |
| `/health/chroma` | GET | ChromaDB status & verse count |

**Health Response:**
```json
{
  "status": "healthy",
  "total_verses_indexed": 701,
  "collections": 1,
  "database": "ChromaDB"
}
```

---

### **Admin Endpoints** 🔐

All admin endpoints require authentication via `X-API-Key` header.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/admin/stats` | GET | Collection statistics |
| `/admin/llm-status` | GET | Ollama availability & models |
| `/admin/reindex` | POST | Rebuild vector index |
| `/admin/status` | GET | System configuration |
| `/admin/clear-cache` | POST | Clear embedding cache |

**Example Usage:**
```bash
# Get statistics
curl http://localhost:8000/admin/stats \
  -H "X-API-Key: your-secret-key"

# Reindex database
curl -X POST "http://localhost:8000/admin/reindex?force=true" \
  -H "X-API-Key: your-secret-key"
```

**Stats Response:**
```json
{
  "status": "healthy",
  "total_verses_indexed": 701,
  "embedding_model": "all-MiniLM-L6-v2",
  "embedding_dimension": 384,
  "vector_store_location": "vector_db/chroma",
  "last_updated": "2026-01-23T10:30:00"
}
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Application
APP_NAME="Kanha API"
APP_VERSION="1.0.0"
DEBUG=True
LOG_LEVEL="INFO"

# Server
HOST="0.0.0.0"
PORT=8000

# LLM Configuration
LLM_PROVIDER="ollama"
OLLAMA_BASE_URL="http://localhost:11434"
LLM_MODEL="llama3"
LLM_TEMPERATURE=0.75
LLM_MAX_TOKENS=768

# Embeddings
EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2"
DEVICE="cpu"

# Vector Database
CHROMA_PERSIST_DIR="./vector_db/chroma"

# RAG Configuration
TOP_K_RESULTS=5
SIMILARITY_THRESHOLD=0.3

# Admin
API_KEY="your-super-secret-admin-key-change-this"

# CORS
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
```

### Configuration Tuning

**LLM Temperature:**
- `0.3-0.5` → Focused, consistent answers
- `0.7-0.8` → Creative spiritual responses (recommended)
- `0.9-1.0` → More varied, exploratory

**Top K Results:**
- `3` → Quick, focused responses
- `5` → Balanced context (recommended)
- `7-10` → Rich context for complex questions

---

## 🧪 Testing

```bash
# Run all tests
cd backend
pytest tests/ -v

# Run specific test file
pytest tests/test_admin.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html
```

**Current Test Coverage:**
- ✅ 24 passing tests
- ✅ Admin authentication
- ✅ Chat endpoints
- ✅ Health checks
- ✅ Model validation
- ✅ Safety rules
- ✅ Language detection

---

## 🗂️ Data Pipeline

### 1. Raw Data Sources (7 JSON files)
```
data/raw/
├── verse.json           # Sanskrit verses
├── translation.json     # English & Hindi translations
├── commentary.json      # Scholar commentaries
├── chapters.json        # Chapter metadata
├── authors.json         # Translator info
├── languages.json       # Language mappings
└── summary.md          # Documentation
```

### 2. Cleaning & Merging
```bash
cd data/scripts

# Merge all sources into unified JSON
python merge_datasets.py

# Clean and normalize text
python clean_text.py

# Validate schema and quality
python validate_schema.py
python validate_data_quality.py
```

### 3. Output
```
data/cleaned/
├── gita_master.json         # 701 verses, all fields
├── data_quality_report.json # Validation metrics
└── schema.json              # JSON schema definition
```

### 4. Embedding & Indexing
```bash
# Generate embeddings and populate ChromaDB
python embed_and_index.py

# Output: vector_db/chroma/ (persistent storage)
```

---

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern async web framework
- **Pydantic** - Data validation & settings
- **Uvicorn** - ASGI server
- **ChromaDB** - Vector database
- **Sentence Transformers** - Embedding generation
- **Ollama** - Local LLM inference
- **Loguru** - Structured logging

### Data Science
- **PyTorch** - Deep learning backend
- **Transformers** - NLP models
- **NumPy/Pandas** - Data manipulation

### Testing
- **pytest** - Testing framework
- **httpx** - Async HTTP client for tests
- **pytest-cov** - Coverage reporting

### Frontend (Planned)
- **Flutter** - Mobile app (iOS/Android)
- **Vanilla JS** - Web interface

---

## 📊 Dataset Statistics

| Metric | Value |
|--------|-------|
| **Total Verses** | 701 |
| **Chapters** | 18 |
| **Languages** | 3 (Sanskrit, English, Hindi) |
| **Translators** | 2 (Primary: author_id=16, 1) |
| **Embeddings** | 701 × 384 dimensions |
| **Vector Store** | ChromaDB (cosine similarity) |
| **Data Coverage** | 100% validated |

---

## 🔒 Safety & Moderation

The chatbot includes built-in safety filters:

- ✅ **Harmful content detection** - Blocks violence, hate speech
- ✅ **Off-topic redirection** - Guides to spiritual context
- ✅ **Respectful interfaith** - Handles other religions gracefully
- ✅ **Spiritual focus** - Redirects technical/mundane questions

All safety rules defined in `backend/app/core/safety_rules.py`

---

## 📈 Roadmap

### ✅ Completed
- [x] Data pipeline (ETL, cleaning, validation)
- [x] Vector database setup (ChromaDB)
- [x] RAG retrieval system
- [x] LLM integration (Ollama)
- [x] FastAPI backend
- [x] Streaming chat support
- [x] Admin endpoints
- [x] Test suite
- [x] API documentation

### 🚧 In Progress
- [ ] Frontend web app completion
- [ ] Flutter mobile app
- [ ] Conversation history persistence
- [ ] User authentication

### 🎯 Future
- [ ] Docker deployment
- [ ] Rate limiting enforcement
- [ ] Caching layer (Redis)
- [ ] Advanced analytics
- [ ] Multi-model LLM support
- [ ] Voice interface
- [ ] Personalized recommendations

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

### Development Setup
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is for educational and spiritual purposes. 

---

## 🙏 Acknowledgments

- **Bhagavad Gita As It Is** - A.C. Bhaktivedanta Swami Prabhupada
- **GitaGPT Dataset** - For raw data sources
- **Ollama** - Local LLM infrastructure
- **FastAPI** - Modern Python web framework
- **ChromaDB** - Vector database solution

---

## 📞 Contact & Support

For questions, suggestions, or spiritual guidance:
- Open an issue on GitHub
- Reach out to the development team

---

<div align="center">

**🕉️ May this project bring peace and wisdom to all seekers 🕉️**

*"You have the right to work only, but never to its fruits."*  
— Bhagavad Gita 2:47

**Built with 💙 for spiritual seekers everywhere**

</div>
