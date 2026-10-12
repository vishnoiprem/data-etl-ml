# Dockerfile for leads-pipeline/draft-cron
#
# The image packages the Python autopilot that scrapes AI/data job
# postings, runs email outreach, and tracks results in Postgres.
# Entrypoint is `python`; default CMD runs one autopilot pass and
# exits, so an orchestrator (cron, K8s CronJob, a wrapper container)
# can schedule the next run.
#
# Build:   docker build -t leads-pipeline .
# Run:     docker run --rm -e AVILX_DB_HOST=... leads-pipeline
#   or:    docker run --rm leads-pipeline dashboard.py --help
#
# Python version matches leads-ci workflow (3.10/3.11); we use 3.12
# for the runtime image because it's the latest stable and a
# superset of the CI test matrix.
FROM python:3.12-slim

# Sensible Python defaults for containers
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app/draft-cron

WORKDIR /app

# Install OS-level deps first (rare, but cheap to layer). Keep this
# before the pip install so changes to requirements.txt don't bust
# the apt cache layer.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps as a separate layer for build cache reuse.
COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# Copy the rest of the package
COPY . /app/draft-cron

# Stamp the version into the image. Updated by release-please on
# every release. /app/draft-cron/VERSION is a one-line semver that
# `python -c "open('/app/draft-cron/VERSION').read().strip()"` can
# read at runtime for telemetry / health endpoints.
ARG VERSION=0.0.0+unknown
LABEL org.opencontainers.image.version=${VERSION}

# Non-root user. UID 1001 is conventional for K8s runAsUser.
RUN groupadd --system --gid 1001 avilx \
    && useradd  --system --uid 1001 --gid avilx \
                --home-dir /home/avilx --shell /usr/sbin/nologin \
                avilx \
    && mkdir -p /home/avilx \
    && chown -R avilx:avilx /app /home/avilx

# Healthcheck: install + chmod BEFORE the USER switch so we
# don't have to be root to mark the script executable.
COPY docker-healthcheck.sh /usr/local/bin/docker-healthcheck.sh
RUN chmod 0755 /usr/local/bin/docker-healthcheck.sh \
    && chown avilx:avilx /usr/local/bin/docker-healthcheck.sh

USER avilx
WORKDIR /app/draft-cron

HEALTHCHECK --interval=5m --timeout=10s --start-period=30s --retries=3 \
    CMD /usr/local/bin/docker-healthcheck.sh || exit 1

# Run one autopilot pass by default. Override CMD to run other
# entrypoints (dashboard.py, daily_report.py, db_cli.py, etc.).
ENTRYPOINT ["python"]
CMD ["autopilot.py"]
