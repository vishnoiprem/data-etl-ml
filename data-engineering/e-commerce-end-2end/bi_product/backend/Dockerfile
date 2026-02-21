FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir fastapi uvicorn[standard] websockets clickhouse-driver pandas

COPY api/ ./api/
COPY services/ ./services/
COPY models/ ./models/

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
