FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY dashboard ./dashboard
COPY db ./db

ENV PYTHONUNBUFFERED=1
EXPOSE 8501

CMD ["streamlit", "run", "dashboard/app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
