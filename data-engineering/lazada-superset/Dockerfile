FROM apache/superset:4.1.1

# Switch to root to install packages
USER root

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Databricks SQL connector + other drivers
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy Superset config
COPY superset_config.py /app/superset_config.py

# Copy init scripts
COPY init/ /app/docker/docker-init.d/

# Make scripts executable
RUN chmod +x /app/docker/docker-init.d/*.sh || true

# Switch back to superset user
USER superset

ENV SUPERSET_CONFIG_PATH=/app/superset_config.py
