# AI Content Studio - Backend Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for sentence-transformers
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy the app directory (contains all source code)
COPY app/ /app/app/

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create uploads and vectors directories
RUN mkdir -p uploads vectors

# Expose the API port
EXPOSE 8001

# Run uvicorn with production settings
# Note: Imports use from app. prefix (not backend.app.) for Render compatibility
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "2"]