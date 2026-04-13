from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.routes import (
    actions,
    aggregates,
    assets,
    causes,
    competences,
    documents,
    down_events,
    faults,
    graph_admin,
    health,
    levels,
    locations,
    maintenance_schedules,
    materials,
    orders,
    query,
    roles,
    sensor_data,
    sensors,
    shifts,
    systems,
    tasks,
    workers,
)
from app.core.config import settings
from app.core.database import engine
from app.core.neo4j import close_neo4j_driver


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up application")
    yield
    logger.info("Shutting down application")
    await close_neo4j_driver()
    await engine.dispose()


app = FastAPI(
    title="LLM-RAG API",
    description="Retrieval-Augmented Generation API using Qdrant, FastAPI, and OpenAI",
    version="0.1.0",
    lifespan=lifespan,
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
app.include_router(assets.router)
app.include_router(sensors.router)
app.include_router(sensor_data.router)
app.include_router(faults.router)
app.include_router(maintenance_schedules.router)
app.include_router(graph_admin.router)
app.include_router(workers.router)
app.include_router(roles.router)
app.include_router(competences.router)
app.include_router(levels.router)
app.include_router(tasks.router)
app.include_router(actions.router)
app.include_router(causes.router)
app.include_router(materials.router)
app.include_router(shifts.router)
app.include_router(down_events.router)
app.include_router(orders.router)
app.include_router(locations.router)
app.include_router(systems.router)
app.include_router(aggregates.router)

# Mount MCP server
if settings.mcp_server_enabled:
    try:
        from app.mcp.server import create_mcp_app

        mcp_app = create_mcp_app()
        if mcp_app is not None:
            mcp_http_app = mcp_app.streamable_http_app()
            app.mount("/mcp", mcp_http_app)
            logger.info("MCP server mounted at /mcp")
    except Exception as e:
        logger.error(f"Failed to mount MCP server: {e}")


@app.get("/")
async def root():
    return {
        "message": "LLM-RAG API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
