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
| `/health` | GET | Health check |
| `/admin/reindex` | POST | Trigger re-indexing |

## Environment Variables

Copy `.env.example` to `.env` and configure:
- `LLM_MODEL`: Model name for inference
- `CHROMA_PERSIST_DIR`: Vector DB storage path
- `EMBEDDING_MODEL`: Sentence transformer model

## License

This project is for educational and spiritual purposes.

---

*"Whenever dharma declines and adharma prevails, I manifest myself."* - Bhagavad Gita 4.7
