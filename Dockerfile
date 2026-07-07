# Use official lightweight Python image
FROM python:3.12-slim

# Set working directory inside the container
WORKDIR /app

# Set system environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies needed for FPDF2 or build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY src/ ./src/
COPY static/ ./static/
COPY .specify/ ./.specify/
COPY .agents/ ./.agents/

# Set PYTHONPATH for clean import paths
ENV PYTHONPATH=/app/src

# Expose backend API port
EXPOSE 8000

# Run uvicorn server on startup
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
