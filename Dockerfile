FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DATA_DIR=/data
WORKDIR /app

RUN apt-get update && \
    apt-get install -y build-essential curl && \
    rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    python -m textblob.download_corpora
RUN apt-get purge -y --auto-remove build-essential curl
COPY . .
RUN mkdir -p ${DATA_DIR} /app/chroma_db && \
    chown -R 1000:1000 /app ${DATA_DIR}
RUN useradd -m -u 1000 appuser
USER appuser
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
