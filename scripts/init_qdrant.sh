#!/bin/bash

set -e

echo "Initializing Qdrant collection..."

uv run python app/utils/qdrant_setup.py

echo "Qdrant initialization complete"
