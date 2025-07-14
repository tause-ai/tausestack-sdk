# TauseStack SDK - Multi-stage Docker Build
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY tausestack/ ./tausestack/
COPY README.md LICENSE ./

# Install the package
RUN pip install -e .

# Production stage
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app

# Copy frontend build
COPY frontend/out/ /app/frontend/

# Copy templates directory for Builder API
COPY templates/ /app/templates/

# Create non-root user
RUN useradd --create-home --shell /bin/bash tausestack

# Fix permissions for the app directory
RUN chown -R tausestack:tausestack /app

# Switch to non-root user
USER tausestack

# Environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV TAUSESTACK_ENVIRONMENT=production

# Health check - más tiempo para startup (Builder API + API Gateway)
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose all service ports
EXPOSE 8000 8001 8002 8003 8004 8005 8006 8007

# Copy service startup script
COPY start_services.py /app/

# Start command - run all services
CMD ["python", "/app/start_services.py"]
