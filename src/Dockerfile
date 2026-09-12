FROM python:3.12-slim

WORKDIR /app

# Install dependencies first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

# Cloud Run sets $PORT at runtime (defaults to 8080) and expects the
# container to listen on it — this is why we reference $PORT rather than
# hardcoding 8080 in the CMD.
ENV PORT=8080
EXPOSE 8080

CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT}