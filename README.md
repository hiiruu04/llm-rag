# LLM-RAG: Retrieval-Augmented Generation with Qdrant & Neo4j

A Python-based RAG system that ingests documents, performs semantic search using Qdrant vector database, enriches queries with a knowledge graph in Neo4j, and generates answers using OpenAI's LLMs.

## Features

- **Multi-format Document Ingestion**: PDF, DOCX, TXT, MD
- **OCR Support**: Extract text from scanned PDFs using Tesseract
- **Dynamic Chunking**: Adaptive text segmentation based on document length
- **Semantic Search**: Vector similarity search with Qdrant
- **Knowledge Graph**: Neo4j-powered graph for CMMS entity relationships
- **GraphRAG Pipeline**: Vector search enriched with graph context and CMMS references
- **Intelligent Q&A**: Context-aware responses using OpenAI GPT models
- **Docker Support**: Containerized deployment with Docker Compose
- **FastAPI**: High-performance async API with automatic docs

## Architecture

```
INGESTION:
  Document -> Text Extraction -> Chunks
    -> Embedding -> Store in Qdrant (vector search)
    -> LLM Entity/Rel Extraction -> Store in Neo4j (knowledge graph)
    -> Link extracted entities to CMMS nodes

RETRIEVAL:
  Query -> Embed -> Semantic Search (Qdrant) -> Extract Chunk IDs
    -> Query Neo4j graph around those IDs -> Graph Context
    -> Graph Context + Doc Passages + Query -> LLM -> Answer
```

### Query Modes

| Mode | Description |
|------|-------------|
| `vector` | Traditional RAG: Qdrant semantic search only |
| `graph` | Knowledge graph queries via Cypher generation |
| `graphrag` | **Vector + Graph**: Semantic search enriched with graph context and CMMS references |
| `hybrid` | Parallel vector + graph search with synthesized answer |
| `auto` | Intent classification selects the best mode automatically |

## Tech Stack

- **Framework**: FastAPI
- **Vector Database**: Qdrant
- **Graph Database**: Neo4j
- **Relational Database**: PostgreSQL
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
| `NEO4J_URI` | Neo4j bolt URI | `bolt://localhost:7687` |
| `NEO4J_USER` | Neo4j username | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j password | `password123` |

### GraphRAG Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `GRAPHRAG_ENABLED` | Enable GraphRAG pipeline | `true` |
| `GRAPHRAG_MAX_ENTITIES_PER_CHUNK` | Max entities to extract per chunk | `20` |
| `GRAPHRAG_NEIGHBORHOOD_HOPS` | Graph traversal depth for context | `2` |

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
│   │   ├── models.py        # Response models
│   │   └── routes/          # API route handlers
│   │       ├── documents.py # Document ingestion/deletion
│   │       ├── query.py     # Query endpoints (vector, graph, graphrag, hybrid)
│   │       └── ...          # CMMS CRUD routes
│   ├── core/                # Core business logic
│   │   ├── config.py        # Settings management
│   │   ├── embeddings.py    # OpenAI embeddings
│   │   ├── graphrag_pipeline.py  # GraphRAG retrieval pipeline
│   │   ├── graph_rag_pipeline.py # Cypher-based graph pipeline
│   │   ├── hybrid_pipeline.py    # Combined vector + graph
│   │   ├── llm.py           # LLM service
│   │   ├── neo4j.py         # Neo4j driver
│   │   ├── rag_pipeline.py  # Vector-only RAG
│   │   └── vector_store.py  # Qdrant operations
│   ├── services/            # Service layer
│   │   ├── document_entity_extractor.py  # LLM entity extraction
│   │   ├── entity_linking_service.py     # Link entities to CMMS nodes
│   │   ├── graph_ingestion_service.py    # Graph data ingestion
│   │   ├── intent_classifier.py          # Query intent classification
│   │   └── ...
│   ├── models/              # SQLAlchemy data models
│   ├── modules/             # Feature modules
│   │   └── document_processor.py
│   ├── utils/               # Utilities
│   │   ├── neo4j_setup.py   # Neo4j schema setup
│   │   ├── qdrant_setup.py  # Qdrant collection setup
│   │   └── logger.py
│   └── main.py              # FastAPI app entry
├── scripts/
├── logs/
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── README.md
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

#### 4. Start Infrastructure

```bash
# Start Qdrant, PostgreSQL, and Neo4j
docker-compose up -d qdrant postgres neo4j
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
- **PostgreSQL** on `localhost:5432`
- **Neo4j** on `bolt://localhost:7687` (browser: `http://localhost:7474`)
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

#### 2. Ingest Document

```bash
curl -X POST http://localhost:8000/api/v1/documents \
  -F "file=@path/to/document.pdf" \
  -F "enable_graph=true"
```

**Response:**
```json
{
  "data": {
    "document_id": "uuid-here",
    "filename": "document.pdf",
    "chunks_processed": 5,
    "embedding_model": "text-embedding-3-small",
    "processing_time_ms": 1234,
    "graph_ingestion_triggered": true
  },
  "meta": {"status_code": 201, "details": "Document ingested successfully"}
}
```

Graph ingestion runs as a background task. Entities and relationships are extracted via LLM and stored in Neo4j, then linked to existing CMMS nodes.

#### 3. Query with GraphRAG

```bash
curl -X POST http://localhost:8000/api/v1/query/graphrag \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What equipment is mentioned in the maintenance manual and what faults are associated with it?"
  }'
```

**Response:**
```json
{
  "data": {
    "answer": "Based on the maintenance manual...",
    "sources": [
      {
        "document_id": "uuid",
        "filename": "maintenance_manual.pdf",
        "chunk_index": 3,
        "similarity_score": 0.82,
        "preview_text": "The hydraulic pump requires..."
      }
    ],
    "graph_entities": [
      {"name": "Hydraulic Pump", "entity_type": "Equipment", "description": "Main hydraulic pump unit"},
      {"name": "Pressure Loss", "entity_type": "FailureMode", "description": "Loss of system pressure"}
    ],
    "cmms_references": [
      {"entity_name": "Hydraulic Pump", "cmms_label": "Asset", "cmms_name": "HP-2000", "cmms_pg_id": 42}
    ],
    "mode_used": "graphrag"
  },
  "meta": {"status_code": 200, "details": "GraphRAG query processed successfully"}
}
```

#### 4. Query with Auto Mode

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the maintenance schedule for pump HP-2000?",
    "mode": "auto"
  }'
```

The `mode` parameter accepts: `auto`, `vector`, `graph`, `graphrag`, `hybrid`.

#### 5. List Documents

```bash
curl http://localhost:8000/api/v1/documents
```

#### 6. Delete Document

```bash
curl -X DELETE http://localhost:8000/api/v1/documents/{document_id}
```

This removes the document from both Qdrant and Neo4j (DocumentChunk nodes, DocEntity nodes, and all relationships).

### Interactive API Documentation

Visit `http://localhost:8000/docs` for interactive Swagger UI documentation.

## GraphRAG Neo4j Schema

### Node Labels

| Label | Key Properties | Purpose |
|-------|---------------|---------|
| `DocumentChunk` | `chunk_id`, `document_id`, `chunk_index`, `text`, `file_name` | Bridge between Qdrant vectors and Neo4j graph |
| `DocEntity` | `entity_id`, `name`, `entity_type`, `description`, `source_document_id` | Entities extracted from documents |

### Relationships

| Type | From -> To | Description |
|------|-----------|-------------|
| `MENTIONED_IN` | DocEntity -> DocumentChunk | Entity found in this chunk |
| `RELATED_TO` | DocEntity -> DocEntity | Extracted relationships between entities |
| `NEXT_CHUNK` | DocumentChunk -> DocumentChunk | Sequential ordering within a document |
| `REFERS_TO` | DocEntity -> Asset/Fault/Sensor/... | Links to existing CMMS entities |

## Troubleshooting

### Qdrant Connection Issues

```bash
# Check if Qdrant is running
curl http://localhost:6333/

# Check Qdrant logs
docker logs llm-rag-qdrant
```

### Neo4j Connection Issues

```bash
# Check if Neo4j is running
curl http://localhost:7474/

# Check Neo4j logs
docker logs llm-rag-neo4j
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
