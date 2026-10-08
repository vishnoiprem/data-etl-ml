FROM python:3.11-slim

WORKDIR /app

# System deps for clickhouse-connect (none strictly required, but keep pip fresh)
RUN pip install --no-cache-dir --upgrade pip

# Install Python deps
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt && \
    pip install --no-cache-dir fastapi 'uvicorn[standard]' clickhouse-connect pydantic-settings

# Copy source
COPY src /app/src
COPY api /app/api
COPY scripts /app/scripts
COPY sample_data /app/sample_data

ENV PYTHONPATH=/app
EXPOSE 8000

CMD ["uvicorn", "api.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
