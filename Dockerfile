# ─────────────────────────────────────────────────────────────
# NEXUS — Enterprise GenAI Assistant
# FastAPI Backend Dockerfile
#
# Optimised for free-tier deployment:
# - Slim base image (python:3.11-slim) → smaller container
# - No GPU / no PyTorch → stays under memory limit
# - Multi-stage ready but single-stage for simplicity on free tier
# - Non-root user for security best practices
# ─────────────────────────────────────────────────────────────

FROM python:3.11-slim

# ── Labels ──────────────────────────────────────────────────
LABEL maintainer="Perarivalan"
LABEL project="nexus-enterprise-rag"
LABEL version="4.1"

# ── Environment ──────────────────────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8000

# ── System dependencies ───────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ─────────────────────────────────────────
WORKDIR /app

# ── Install Python dependencies ───────────────────────────────
# Copy requirements first (Docker layer caching — only re-installs
# when requirements.txt changes, not on every code change)
COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# ── Copy application code ─────────────────────────────────────
COPY . .

# ── Create non-root user for security ────────────────────────
RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser && \
    chown -R appuser:appgroup /app

USER appuser

# ── Health check ──────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT}/ || exit 1

# ── Expose port ───────────────────────────────────────────────
EXPOSE ${PORT}

# ── Start server ──────────────────────────────────────────────
# Workers=1 to stay within free-tier 512MB RAM
# Single worker handles concurrent requests via async FastAPI
CMD ["uvicorn", "app.api.rag_api:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--timeout-keep-alive", "30"]