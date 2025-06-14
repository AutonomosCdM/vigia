# Vigia Celery Worker - Medical Tasks Processing
# Hospital-grade async worker for medical pipeline

FROM python:3.11-slim-bullseye AS base

# Medical compliance metadata
LABEL maintainer="Vigia Medical Team"
LABEL version="1.3.1"
LABEL description="Celery worker for medical LPP detection pipeline"
LABEL compliance="HIPAA,ISO13485,SOC2"

# Security hardening
RUN groupadd -r vigia && useradd -r -g vigia -u 1000 vigia

# System dependencies for medical processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    g++ \
    libc6-dev \
    libffi-dev \
    libssl-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (layer caching)
COPY requirements.txt .
COPY requirements-medical.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-medical.txt && \
    pip install --no-cache-dir celery[redis]==5.3.6 kombu==5.3.5

# Copy application code
COPY vigia_detect/ ./vigia_detect/
COPY scripts/ ./scripts/
COPY models/ ./models/
COPY config/ ./config/

# Create necessary directories
RUN mkdir -p /app/data/images /app/logs /app/tmp && \
    chown -R vigia:vigia /app

# Copy Celery configuration
COPY docker/celery/celeryconfig.py ./celeryconfig.py
COPY docker/celery/worker-entrypoint.sh ./worker-entrypoint.sh
RUN chmod +x ./worker-entrypoint.sh

# Health check script
COPY docker/celery/health-check.py ./health-check.py

# Security: Drop privileges
USER vigia:vigia

# Environment variables
ENV PYTHONPATH=/app
ENV CELERY_APP=vigia_detect.tasks
ENV CELERY_LOGLEVEL=INFO
ENV MEDICAL_COMPLIANCE_LEVEL=hipaa
ENV PHI_PROTECTION_ENABLED=true
ENV WORKER_TYPE=medical

# Health check
HEALTHCHECK --interval=60s --timeout=30s --start-period=120s --retries=3 \
    CMD python health-check.py || exit 1

# Expose metrics port
EXPOSE 9540

# Entry point
ENTRYPOINT ["./worker-entrypoint.sh"]
CMD ["celery", "-A", "vigia_detect.tasks", "worker", \
     "--loglevel=INFO", \
     "--queues=medical_priority,image_processing,notifications,audit_logging", \
     "--concurrency=4", \
     "--max-tasks-per-child=100", \
     "--task-acks-late", \
     "--worker-prefetch-multiplier=1"]