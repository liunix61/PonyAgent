# PonyAgent Dockerfile
# Multi-stage build for minimal image

# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /app

COPY pyproject.toml requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ponyagent/ ponyagent/

# Stage 2: Runtime
FROM python:3.11-slim

# System dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        tzdata \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy from builder
COPY --from=builder /app/pyproject.toml /app/pyproject.toml
COPY --from=builder /app/requirements.txt /app/requirements.txt
COPY --from=builder /app/ponyagent/ /app/ponyagent/

RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -e .

# Create non-root user
RUN useradd -m -u 1000 ponyagent && \
    mkdir -p /app/data && \
    chown -R ponyagent:ponyagent /app
USER ponyagent

# Environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PONYAGENT_DATA_DIR=/app/data \
    PORT=8000

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the server
CMD ["python", "-m", "ponyagent", "serve", "--host", "0.0.0.0", "--port", "8000"]
