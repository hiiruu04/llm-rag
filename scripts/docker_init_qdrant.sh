#!/bin/bash

set -e

echo "Waiting for Qdrant to be ready..."
until curl -f http://qdrant:6333/ > /dev/null 2>&1; do
    echo "Qdrant is unavailable - sleeping"
    sleep 2
done

echo "Qdrant is ready - initializing collection..."

python app/utils/qdrant_setup.py

echo "Qdrant initialization complete"

echo "Waiting for Neo4j to be ready..."
until python -c "import asyncio; from neo4j import AsyncGraphDatabase; asyncio.run(AsyncGraphDatabase.driver('bolt://neo4j:7687', auth=('neo4j', '${NEO4J_PASSWORD:-password123}')).verify_connectivity())" 2>/dev/null; do
    echo "Neo4j is unavailable - sleeping"
    sleep 2
done
echo "Neo4j is ready"

echo "Running database migrations..."
alembic upgrade head
echo "Database migrations complete"

echo "Starting FastAPI application..."
exec fastapi run --host 0.0.0.0 --port 8000
