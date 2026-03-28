# ── Stage 1: dependency builder ───────────────────────────────────────────────
# Use a full Python image to compile any C extensions (e.g. psycopg2-binary).
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build deps (gcc needed for some C-extension wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies into a local directory so we can
# copy only the installed packages into the final stage.
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt


# ── Stage 2: runtime ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Non-root user for security best practices
RUN groupadd --gid 1001 appgroup \
    && useradd  --uid 1001 --gid appgroup --no-create-home appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY main.py     .
COPY models.py   .
COPY database.py .
COPY schemas.py  .

# Ownership
RUN chown -R appuser:appgroup /app
USER appuser

# Uvicorn listens on port 8000
EXPOSE 8000

# Health-check — calls our /health endpoint
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# ── Runtime environment defaults ───────────────────────────────────────────────
# These can all be overridden by the K8s Deployment manifest.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_VERSION=1.0.0 \
    SQL_ECHO=false \
    ALLOWED_ORIGINS="*"
# DB_SECRET_NAME and AWS_REGION are injected by the K8s Deployment via
# environment variables (not baked in here for security reasons).

CMD ["uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2", \
     "--log-level", "info"]