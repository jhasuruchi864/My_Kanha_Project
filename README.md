# My Kanha Project 🙏

A spiritual chatbot powered by the Bhagavad Gita, designed to provide wisdom from Lord Krishna using modern AI techniques.

## Architecture Overview

```
My_Kanha_Project/
├── data/           # Data Engineering - The Brain
├── backend/        # FastAPI + LLM Engine - The Bridge
├── vector_db/      # Persistent Vector Storage
└── mobile_app/     # Flutter Mobile App - The Body
```

## Components

### 1. Data Layer (`data/`)
- Raw Gita texts in Sanskrit, English, and Hindi
- Data cleaning and merging scripts
- Schema validation utilities

### 2. Backend (`backend/`)
- FastAPI REST API
- RAG (Retrieval Augmented Generation) pipeline
- Local LLM integration (Llama 3 / Mistral via Ollama)
- ChromaDB for vector storage

### 3. Mobile App (`mobile_app/`)
- Flutter cross-platform application
- Chat interface with Krishna
- Verse citations and history

## Getting Started

### Prerequisites
- Python 3.10+
- Docker & Docker Compose
- Flutter SDK
- Ollama (for local LLM)

### Quick Start

```bash
# Start all services
docker-compose up -d

# Run data pipeline
cd data/scripts
python merge_datasets.py
python clean_text.py
python validate_schema.py

# Start backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Run mobile app
cd mobile_app
flutter pub get
flutter run
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat` | POST | Main chat endpoint |
| `/chat/stream` | POST | Streaming chat endpoint (SSE) |
| `/health` | GET | Basic health check |
| `/health/detailed` | GET | Detailed health with components |

### Admin Endpoints

Admin endpoints require authentication via the `X-API-Key` header. Set `API_KEY` in your `.env` file.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/admin/stats` | GET | ChromaDB collection stats (count, last index time) |
| `/admin/llm-status` | GET | Ollama availability and latency |
| `/admin/reindex` | POST | Trigger ChromaDB rebuild from gita_master.json |
| `/admin/status` | GET | System status and configuration |
| `/admin/clear-cache` | POST | Clear embedding caches |

#### Example Requests

```bash
# Get collection stats
curl http://localhost:8000/admin/stats -H "X-API-Key: your-key"

# Check LLM status
curl http://localhost:8000/admin/llm-status -H "X-API-Key: your-key"

# Trigger reindex (with reset)
curl -X POST "http://localhost:8000/admin/reindex?allow_reset=true" -H "X-API-Key: your-key"

# Get system status
curl http://localhost:8000/admin/status -H "X-API-Key: your-key"
```

#### Stats Response Example

```json
{
  "status": "healthy",
  "total_verses_indexed": 701,
  "vector_db_path": "./vector_db/chroma",
  "collection_name": "gita_verses",
  "last_index_time": "2024-01-15T12:30:00",
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
  "ollama_model": "llama3"
}
```

#### LLM Status Response Example

```json
{
  "reachable": true,
  "model": "llama3",
  "ollama_url": "http://localhost:11434",
  "latency_ms": 45.2,
  "available_models": ["llama3:latest", "mistral:latest"]
}
```

## Environment Variables

Copy `.env.example` to `.env` and configure:
- `LLM_MODEL`: Model name for inference
- `CHROMA_PERSIST_DIR`: Vector DB storage path
- `EMBEDDING_MODEL`: Sentence transformer model

## License

This project is for educational and spiritual purposes.

---

*"Whenever dharma declines and adharma prevails, I manifest myself."* - Bhagavad Gita 4.7
