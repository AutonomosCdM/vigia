# ===============================================
# PHI Tokenization Service Dockerfile
# Secure API bridge for Hospital PHI ↔ Processing Database
# ===============================================

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r tokenization && useradd -r -g tokenization -u 1001 tokenization

# Copy requirements first (for Docker layer caching)
COPY tokenization/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy tokenization service code
COPY tokenization/ ./tokenization/
COPY vigia_detect/utils/ ./vigia_detect/utils/

# Set PYTHONPATH
ENV PYTHONPATH="/app:${PYTHONPATH}"

# Create directories for logs and temp files
RUN mkdir -p /app/logs /app/tmp \
    && chown -R tokenization:tokenization /app

# Switch to non-root user
USER tokenization

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose port
EXPOSE 8080

# Run the tokenization service
CMD ["python", "-m", "tokenization.phi_tokenization_service"]