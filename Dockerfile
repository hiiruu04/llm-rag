FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install only essential runtime dependencies (no Git, no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PATH="/app/.venv/bin:$PATH" \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Install dependencies in one layer
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Copy application files
COPY app ./app
COPY scripts ./scripts

# Convert line endings and make executable
RUN sed -i 's/\r//' scripts/docker_init_qdrant.sh && \
    chmod +x scripts/docker_init_qdrant.sh

EXPOSE 8000

CMD ["/app/scripts/docker_init_qdrant.sh"]
