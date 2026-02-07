# LLM-RAG: Retrieval-Augmented Generation with Qdrant

A Python-based RAG system that ingests documents, performs semantic search using Qdrant vector database, and generates answers using OpenAI's LLMs.

## Features

- **Multi-format Document Ingestion**: PDF, DOCX, TXT, MD
- **OCR Support**: Extract text from scanned PDFs using Tesseract
- **Dynamic Chunking**: Adaptive text segmentation based on document length
- **Semantic Search**: Vector similarity search with Qdrant
- **Intelligent Q&A**: Context-aware responses using OpenAI GPT models
- **Docker Support**: Containerized deployment with Docker Compose
- **FastAPI**: High-performance async API with automatic docs

## Architecture

```
User Query -> FastAPI -> Embedding Generation -> Qdrant Search -> Context Retrieval -> LLM Generation -> Answer
                |
Document Upload -> Text Extraction -> Dynamic Chunking -> Embedding Generation -> Qdrant Storage
```

## Tech Stack

- **Framework**: FastAPI
- **Vector Database**: Qdrant
- **Embeddings**: OpenAI `text-embedding-3-small` / `text-embedding-3-large`
- **LLM**: OpenAI `gpt-4o-mini`
- **Document Processing**: LlamaIndex, pypdf, pytesseract, pdf2image
- **Package Manager**: uv

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | **Required** |
| `OPENAI_EMBEDDING_MODEL` | Embedding model to use | `text-embedding-3-small` |
| `OPENAI_LLM_MODEL` | LLM for generating answers | `gpt-4o-mini` |
| `QDRANT_URL` | Qdrant instance URL | `http://localhost:6333` |
| `QDRANT_COLLECTION_NAME` | Qdrant collection name | `documents` |
| `QDRANT_VECTOR_SIZE` | Embedding vector size | `1536` (small) / `3072` (large) |
| `CHUNK_SIZE` | Max chunk size for long docs | `512` |
| `CHUNK_OVERLAP` | Overlap between chunks | `50` |
| `SIMILARITY_THRESHOLD` | Minimum similarity score | `0.2` |

### Switching to Large Embedding Model

For better semantic understanding:

```bash
# In .env file
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
QDRANT_VECTOR_SIZE=3072
SIMILARITY_THRESHOLD=0.5

# Reset and re-index
uv run python app/utils/qdrant_setup.py reset
```

## Project Structure

```
llm-rag/
├── app/
│   ├── api/                 # FastAPI endpoints
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── router.py
│   ├── core/                # Core business logic
│   │   ├── config.py
│   │   ├── embeddings.py
│   │   ├── llm.py
│   │   └── vector_store.py
│   ├── modules/             # Feature modules
│   │   └── document_processor.py
│   ├── utils/               # Utilities
│   │   ├── logger.py
│   │   └── qdrant_setup.py
│   └── main.py              # FastAPI app entry
├── scripts/                 # Shell scripts
│   ├── init_qdrant.sh
│   └── docker_init_qdrant.sh
├── logs/                    # Application logs
├── .env                     # Environment configuration
├── docker-compose.yml       # Docker orchestration
├── Dockerfile               # Container definition
├── Makefile                 # Convenience commands (Linux/macOS)
├── pyproject.toml           # Python dependencies
└── README.md                # This file
```

## Prerequisites

- Python 3.13+
- OpenAI API Key
- Docker & Docker Compose (optional)
- Tesseract OCR

## Installation

### Option 1: Local Development

#### 1. Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-eng poppler-utils
```

**macOS:**
```bash
brew install tesseract poppler
```

**Windows:**
```bash
# Install Tesseract from https://github.com/UB-Mannheim/tesseract/wiki
# Install poppler from http://blog.alivate.com.au/poppler-windows/
```

#### 2. Install Python Dependencies

```bash
# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv sync
```

#### 3. Configure Environment

```bash
cp .env.example .env

# Edit .env and add your OpenAI API key
nano .env
```

#### 4. Start Qdrant

```bash
docker run -d --name qdrant \
  -p 6333:6333 -p 6334:6334 \
  -v $(pwd)/qdrant_data:/qdrant/storage \
  qdrant/qdrant:latest
```

#### 5. Initialize Qdrant Collection

```bash
uv run python app/utils/qdrant_setup.py
```

#### 6. Start the Application

```bash
uv run fastapi dev
```

The API will be available at `http://localhost:8000`

### Option 2: Docker (Recommended)

#### 1. Configure Environment

```bash
cp .env.example .env

# Edit .env and add your OpenAI API key
nano .env
```

#### 2. Start Services

```bash
docker-compose up -d
```

This will start:
- **Qdrant** on `http://localhost:6333`
- **FastAPI App** on `http://localhost:8000`

#### 3. View Logs

```bash
docker-compose logs -f
```

#### 4. Stop Services

```bash
docker-compose down
```

### Option 3: Using Makefile (Linux/macOS Only)

**Note**: Make commands only work on Linux/macOS. Windows users should use Docker commands directly or install WSL.

```bash
# Start all services
make up

# View logs
make logs

# Check health status
make health

# Stop services
make down

# Rebuild and restart
make rebuild
```

## Usage

### API Endpoints

#### 1. Health Check

```bash
curl http://localhost:8000/api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "qdrant_connected": true,
  "collection_info": {
    "name": "documents",
    "vector_size": 1536,
    "vectors_count": 10
  }
}
```

#### 2. Ingest Document

```bash
curl -X POST http://localhost:8000/api/v1/documents \
  -F "file=@path/to/document.pdf" \
  -F "metadata={\"author\":\"John Doe\"}"
```

**Response:**
```json
{
  "document_id": "uuid-here",
  "filename": "document.pdf",
  "chunks_created": 5,
  "message": "Document ingested successfully"
}
```

#### 3. Query the System

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the deadline for this project?"
  }'
```

**Response:**
```json
{
  "answer": "Based on the document, you are expected to complete the challenge within 3 days.",
  "sources": [
    {
      "document_id": "uuid-here",
      "filename": "quiz.pdf",
      "chunk_index": 5,
      "similarity_score": 0.75,
      "preview_text": "Timeline: You are expected to complete the challenge within 3 days..."
    }
  ],
  "model_used": "gpt-4o-mini",
  "tokens_used": 150
}
```

#### 4. List Documents

```bash
curl http://localhost:8000/api/v1/documents
```

#### 5. Delete Document

```bash
curl -X DELETE http://localhost:8000/api/v1/documents/{document_id}
```

### Interactive API Documentation

Visit `http://localhost:8000/docs` for interactive Swagger UI documentation.

## Troubleshooting

### Qdrant Connection Issues

```bash
# Check if Qdrant is running
curl http://localhost:6333/

# Check Qdrant logs
docker logs llm-rag-qdrant
```

### OCR Not Working

```bash
# Test Tesseract installation
tesseract --version

# Test on an image
tesseract image.png stdout
```

### Low Similarity Scores

- **Small model** (`text-embedding-3-small`): Expect 0.2-0.4 for related content
- **Large model** (`text-embedding-3-large`): Expect 0.4-0.7 for related content
- Adjust `SIMILARITY_THRESHOLD` in `.env` accordingly

### Docker Build Issues

```bash
# Rebuild from scratch
docker-compose down
docker-compose up -d --build

# Check container logs
docker-compose logs app
```

## Development

```bash
# Run with auto-reload
uv run fastapi dev app

# Run tests (if available)
uv run pytest

# Format code
uv run ruff format .

# Lint code
uv run ruff check .
```

## License

MIT

