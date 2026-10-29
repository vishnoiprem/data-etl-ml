# Producer image for the real-time US stock pipeline.
# Builds a slim Python 3.11 environment with librdkafka system deps so that
# confluent-kafka can install its binary wheel (or build from sdist if needed).

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System packages: gcc/python3-dev/librdkafka-dev are required to build
# confluent-kafka from source if a compatible wheel is unavailable; they also
# cover the case of older slim base images missing zlib/brotli headers.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        python3-dev \
        librdkafka-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first for better layer caching.
COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copy only what the producer needs.
COPY producer/ ./producer/
COPY config/   ./config/

# Make `producer` importable as a package (contains __init__.py if present).
ENV PYTHONPATH=/app

# Default invocation; compose can override.
CMD ["python", "-u", "producer/stock_producer.py"]
