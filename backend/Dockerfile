# AI Content Studio - Backend Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for sentence-transformers
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create uploads and vectors directories
RUN mkdir -p uploads vectors

# Expose the API port
EXPOSE 8001

# Run uvicorn with production settings
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "2"]