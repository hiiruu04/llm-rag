import time
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, Query, UploadFile
from loguru import logger
from pydantic import BaseModel
from qdrant_client import QdrantClient

from app.api.models import Pagination, SuccessResponse
from app.core.config import settings
from app.core.vector_store import get_vector_store
from app.modules.document_processor import DocumentProcessor

router = APIRouter(prefix="/api/v1", tags=["documents"])


class Metadata(BaseModel):
    title: Optional[str] = None
    tags: Optional[list[str]] = None
    author: Optional[str] = None


class IngestData(BaseModel):
    document_id: str
    filename: str
    chunks_processed: int
    embedding_model: str
    processing_time_ms: int
    graph_ingestion_triggered: bool = False


class DocumentInfo(BaseModel):
    document_id: str
    filename: str
    title: Optional[str]
    chunks_count: int


class DocumentListData(BaseModel):
    documents: List[DocumentInfo]


class DeleteData(BaseModel):
    document_id: str


async def _run_graph_ingestion(document_id: str, chunks: list[dict], file_name: str):
    """Background task to ingest document graph data into Neo4j."""
    try:
        from app.services.graph_ingestion_service import get_graph_ingestion_service

        service = get_graph_ingestion_service()
        result = await service.ingest_document_graph(document_id, chunks, file_name)
        logger.info(f"Background graph ingestion result: {result}")
    except Exception as e:
        logger.error(f"Background graph ingestion failed for {document_id}: {e}")


@router.post("/documents", status_code=201)
async def ingest_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    author: Optional[str] = Form(None),
    enable_graph: bool = Form(True),
):
    document_id = str(uuid.uuid4())
    start_time = time.time()

    logger.info(f"Starting ingestion for document {document_id}")

    try:
        processor = DocumentProcessor()

        file_size = 0
        content = await file.read()
        file_size = len(content)

        processor.validate_file_size(file_size)

        file_path = Path(f"/tmp/{document_id}_{file.filename}")
        with open(file_path, "wb") as f:
            f.write(content)

        metadata = {
            "file_name": file.filename,
            "title": title or file.filename,
            "author": author,
            "tags": tags.split(",") if tags else [],
        }

        chunks = processor.process_file(file_path, metadata)

        logger.info(f"Processed {len(chunks)} chunks from file")
        for i, chunk in enumerate(chunks):
            logger.debug(f"Chunk {i}: {len(chunk['text'])} chars - '{chunk['text'][:100]}'")

        vector_store = get_vector_store()
        vector_store.add_documents(chunks, document_id)

        file_path.unlink()

        # Trigger background graph ingestion if enabled
        graph_triggered = False
        if enable_graph and settings.graphrag_enabled:
            background_tasks.add_task(
                _run_graph_ingestion,
                document_id,
                chunks,
                file.filename,
            )
            graph_triggered = True

        processing_time = int((time.time() - start_time) * 1000)

        logger.info(
            f"Document {document_id} ingested successfully: {len(chunks)} chunks processed"
        )

        data = IngestData(
            document_id=document_id,
            filename=file.filename,
            chunks_processed=len(chunks),
            embedding_model=settings.openai_embedding_model,
            processing_time_ms=processing_time,
            graph_ingestion_triggered=graph_triggered,
        )

        return SuccessResponse.create(
            data=data,
            status_code=201,
            details="Document ingested successfully",
        )

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail={
                "data": None,
                "meta": {"status_code": 400, "details": str(e), "errors": [str(e)]},
            },
        )
    except Exception as e:
        logger.error(f"Error ingesting document: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "data": None,
                "meta": {
                    "status_code": 500,
                    "details": "Internal server error",
                    "errors": [str(e)],
                },
            },
        )


@router.get("/documents")
async def list_documents(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
):
    logger.info(f"Listing documents (page={page}, per_page={per_page})")

    try:
        client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key if settings.qdrant_api_key else None,
        )

        limit = 1000
        results = client.scroll(
            collection_name=settings.qdrant_collection_name,
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )

        documents_map = {}
        for point in results[0]:
            doc_id = point.payload.get("document_id")
            if doc_id and doc_id not in documents_map:
                documents_map[doc_id] = {
                    "document_id": doc_id,
                    "filename": point.payload.get("file_name", "Unknown"),
                    "title": point.payload.get("title"),
                    "chunks_count": 1,
                }
            elif doc_id:
                documents_map[doc_id]["chunks_count"] += 1

        all_documents = list(documents_map.values())
        total = len(all_documents)
        total_pages = (total + per_page - 1) // per_page

        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_documents = all_documents[start_idx:end_idx]

        data = DocumentListData(documents=paginated_documents)

        pagination = Pagination(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=total_pages,
        )

        return SuccessResponse.create(
            data=data,
            status_code=200,
            details=f"Retrieved {len(paginated_documents)} documents",
            pagination=pagination,
        )

    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "data": None,
                "meta": {
                    "status_code": 500,
                    "details": "Internal server error",
                    "errors": [str(e)],
                },
            },
        )


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    logger.info(f"Deleting document {document_id}")

    try:
        vector_store = get_vector_store()
        success = vector_store.delete_document(document_id)

        if not success:
            raise HTTPException(
                status_code=404,
                detail={
                    "data": None,
                    "meta": {
                        "status_code": 404,
                        "details": f"Document {document_id} not found",
                        "errors": [f"Document {document_id} not found"],
                    },
                },
            )

        # Also clean up graph data
        if settings.graphrag_enabled:
            try:
                from app.services.graph_ingestion_service import (
                    get_graph_ingestion_service,
                )

                graph_service = get_graph_ingestion_service()
                await graph_service.delete_document_graph(document_id)
            except Exception as e:
                logger.warning(f"Graph cleanup failed for {document_id}: {e}")

        data = DeleteData(document_id=document_id)

        return SuccessResponse.create(
            data=data,
            status_code=200,
            details="Document deleted successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "data": None,
                "meta": {
                    "status_code": 500,
                    "details": "Internal server error",
                    "errors": [str(e)],
                },
            },
        )
