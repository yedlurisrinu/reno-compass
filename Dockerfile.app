# Inherit from the pre-built base image containing system and python dependencies
FROM reno-compass-base:latest

# Set working directory inside the container
WORKDIR /app

# Copy application source code
COPY src/ ./src/
COPY static/ ./static/
COPY .specify/ ./.specify/
COPY .agents/ ./.agents/

# Set PYTHONPATH for clean import paths
ENV PYTHONPATH=/app/src

# Expose backend API port
EXPOSE 8020

# Run uvicorn server on startup
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8020"]
