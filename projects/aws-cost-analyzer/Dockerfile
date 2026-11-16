# Dockerfile for aws-cost-analyzer
#
# The image packages the FastAPI app that serves the cost-analysis
# findings over HTTP. The app is **read-only**: it analyses a snapshot
# or the synthetic corpus and serves the result. It never calls a
# mutating AWS API, and it never fetches from AWS at request time —
# pulling live data is the separate `scripts/fetch_aws.py` job.
#
# Build:   docker build -t aws-cost-analyzer .
# Run:     docker run --rm -p 8000:8000 aws-cost-analyzer
#
# Python version matches the CI workflow (3.11); the runtime image
# uses 3.12 because it's the latest stable and a superset of the CI
# test matrix.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app/src

WORKDIR /app

# Install OS-level deps first (rare, but cheap to layer). Keep this
# before the pip install so changes to requirements.txt don't bust
# the apt cache layer.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps as a separate layer for build cache reuse.
COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# Copy the package and the app entrypoint.
COPY src/ /app/src/
COPY app.py /app/app.py

# Stamp the version into the image.
ARG VERSION=0.0.0+unknown
LABEL org.opencontainers.image.version=${VERSION} \
      org.opencontainers.image.title=aws-cost-analyzer \
      org.opencontainers.image.description="Deterministic S3 cost root-cause analysis (read-only)" \
      org.opencontainers.image.source=https://github.com/vishnoiprem/data-etl-ml \
      org.opencontainers.image.licenses=MIT

# Non-root user. UID 1001 is conventional for K8s runAsUser.
RUN groupadd --system --gid 1001 analyzer \
    && useradd  --system --uid 1001 --gid analyzer \
                --home-dir /home/analyzer --shell /usr/sbin/nologin \
                analyzer \
    && mkdir -p /home/analyzer \
    && chown -R analyzer:analyzer /app /home/analyzer

# Healthcheck: install + chmod BEFORE the USER switch so we
# don't have to be root to mark the script executable.
COPY docker-healthcheck.sh /usr/local/bin/docker-healthcheck.sh
RUN chmod 0755 /usr/local/bin/docker-healthcheck.sh \
    && chown analyzer:analyzer /usr/local/bin/docker-healthcheck.sh

USER analyzer
WORKDIR /app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD /usr/local/bin/docker-healthcheck.sh || exit 1

# Serve the read-only API. `--workers 1` because the analysis is
# computed in-process on each request against an on-disk snapshot;
# multiple workers would each do the same work. Override CMD to run
# the CLI instead (e.g. `docker run --rm aws-cost-analyzer
# python -m aws_cost_analyzer.cli analyze --demo`).
ENTRYPOINT ["uvicorn"]
CMD ["app:app", "--host", "0.0.0.0", "--port", "8000"]
