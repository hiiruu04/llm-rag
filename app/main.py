from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import documents, health, query

app = FastAPI(
    title="LLM-RAG API",
    description="Retrieval-Augmented Generation API using Qdrant, FastAPI, and OpenAI",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(documents.router)
app.include_router(query.router)


@app.get("/")
async def root():
    return {
        "message": "LLM-RAG API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
