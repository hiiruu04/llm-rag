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

echo "Starting FastAPI application..."
exec fastapi run --host 0.0.0.0 --port 8000
