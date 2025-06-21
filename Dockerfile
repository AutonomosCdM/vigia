# Vigia Medical System - Cloud Run Deployment
# ===========================================
# Multi-stage Docker build for production ADK medical system

FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements-cloudrun.txt .
RUN pip install --no-cache-dir -r requirements-cloudrun.txt

# Copy application code
COPY vigia_detect/ ./vigia_detect/
COPY scripts/ ./scripts/
COPY config/ ./config/
COPY deploy/cloud-run/entrypoints/workflow_orchestration_agent.py ./app.py

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Run the workflow orchestration agent (main entry point)
CMD ["python", "app.py"]