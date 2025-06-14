# Vigia Celery Beat Scheduler - Medical Task Scheduling
# Hospital-grade task scheduler for medical compliance

FROM python:3.11-slim-bullseye AS base

# Medical compliance metadata
LABEL maintainer="Vigia Medical Team"
LABEL version="1.3.1"
LABEL description="Celery beat scheduler for medical task automation"
LABEL compliance="HIPAA,ISO13485,SOC2"

# Security hardening
RUN groupadd -r vigia && useradd -r -g vigia -u 1000 vigia

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir celery[redis]==5.3.6 kombu==5.3.5

# Copy application code
COPY vigia_detect/ ./vigia_detect/
COPY scripts/ ./scripts/
COPY config/ ./config/

# Create directories
RUN mkdir -p /app/beat /app/logs && \
    chown -R vigia:vigia /app

# Copy beat configuration
COPY docker/celery/celeryconfig.py ./celeryconfig.py
COPY docker/celery/beat-schedule.py ./beat-schedule.py
COPY docker/celery/beat-entrypoint.sh ./beat-entrypoint.sh
RUN chmod +x ./beat-entrypoint.sh

# Security: Drop privileges
USER vigia:vigia

# Environment variables
ENV PYTHONPATH=/app
ENV CELERY_APP=vigia_detect.tasks
ENV CELERY_LOGLEVEL=INFO
ENV CELERY_BEAT_SCHEDULE_FILENAME=/app/beat/celerybeat-schedule

# Health check
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD celery -A vigia_detect.tasks inspect ping -d celery@beat || exit 1

# Entry point
ENTRYPOINT ["./beat-entrypoint.sh"]
CMD ["celery", "-A", "vigia_detect.tasks", "beat", \
     "--loglevel=INFO", \
     "--schedule=/app/beat/celerybeat-schedule", \
     "--pidfile=/app/beat/celerybeat.pid"]