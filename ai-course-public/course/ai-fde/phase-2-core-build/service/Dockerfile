# PacificFreight Phase 2 — service Dockerfile.
#
# Build context MUST be `course/ai-fde/` (the grandparent of this
# Dockerfile). That way `COPY service/...` and `COPY phase-1-foundations/...`
# resolve correctly.
#
# Build from `course/ai-fde/`:
#     docker build -f phase-2-core-build/service/Dockerfile \
#            -t pf-phase2 .
#
# Run:
#     docker run --rm -p 8000:8000 pf-phase2

FROM python:3.11-slim

WORKDIR /app

# Install deps first (so this layer is cached when only code changes).
COPY phase-2-core-build/service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the service source + the shared assets it needs at runtime.
COPY phase-2-core-build/service/ /app/service/
COPY phase-2-core-build/shared/ /app/shared/
COPY phase-1-foundations/shared/ /app/phase-1-foundations/shared/

WORKDIR /app/service
EXPOSE 8000

# Healthcheck uses the /health endpoint we expose.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()" || exit 1

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
