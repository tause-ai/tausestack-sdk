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

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Start command
CMD ["uvicorn", "tausestack.services.api_gateway:app", "--host", "0.0.0.0", "--port", "8000"]
