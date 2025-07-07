#!/bin/bash

# TauseStack Production Startup Script
# Following production best practices
set -euo pipefail

echo "🚀 Starting TauseStack Production v0.9.0..."

# Load environment configuration
if [[ -f "config/local.env" ]]; then
    echo "📋 Loading local environment configuration..."
    set -a  # automatically export all variables
    source config/local.env
    set +a
elif [[ -f "config/production.env" ]]; then
    echo "📋 Loading production environment configuration..."
    set -a
    source config/production.env
    set +a
else
    echo "⚠️  No environment configuration found, using defaults"
fi

# Set default values with validation
export PORT=${PORT:-8000}
export WORKERS=${WORKERS:-2}
export LOG_LEVEL=${LOG_LEVEL:-info}
export NODE_ENV=production

# Validate environment
if [[ ! "$PORT" =~ ^[0-9]+$ ]] || [[ "$PORT" -lt 1000 ]] || [[ "$PORT" -gt 65535 ]]; then
    echo "❌ Invalid PORT: $PORT. Must be between 1000-65535"
    exit 1
fi

echo "📋 Environment:"
echo "  PORT: $PORT"
echo "  WORKERS: $WORKERS"
echo "  LOG_LEVEL: $LOG_LEVEL"
echo "  NODE_ENV: $NODE_ENV"

# Health check function
health_check() {
    local service=$1
    local port=$2
    local endpoint=${3:-"/health"}
    local max_attempts=30
    local attempt=0
    
    echo "🔍 Checking $service health on port $port..."
    
    while [[ $attempt -lt $max_attempts ]]; do
        if curl -sf "http://localhost:$port$endpoint" >/dev/null 2>&1; then
            echo "✅ $service is healthy"
            return 0
        fi
        ((attempt++))
        echo "⏳ Waiting for $service... ($attempt/$max_attempts)"
        sleep 2
    done
    
    echo "❌ $service failed to start after $max_attempts attempts"
    return 1
}

# Start services with proper error handling
start_service() {
    local name=$1
    local module=$2
    local port=$3
    
    echo "🌐 Starting $name on port $port..."
    python -m uvicorn "$module" \
        --host 0.0.0.0 \
        --port "$port" \
        --workers 1 \
        --log-level "$LOG_LEVEL" \
        --access-log \
        --loop uvloop \
        --no-server-header &
    
    local pid=$!
    echo "📝 $name started with PID: $pid"
    
    # Store PID for cleanup
    echo "$pid" >> /tmp/service_pids.txt
}

# Cleanup function
cleanup() {
    echo "🧹 Cleaning up services..."
    if [[ -f /tmp/service_pids.txt ]]; then
        while read -r pid; do
            if kill -0 "$pid" 2>/dev/null; then
                echo "🛑 Stopping process $pid"
                kill -TERM "$pid" 2>/dev/null || true
            fi
        done < /tmp/service_pids.txt
        rm -f /tmp/service_pids.txt
    fi
}

# Set up signal handlers
trap cleanup EXIT INT TERM

# Initialize PID tracking
> /tmp/service_pids.txt

# Set working directory (Docker: /app, Development: current directory)
if [[ -d "/app" ]]; then
    cd /app
    echo "📁 Working directory: /app (Docker)"
else
    echo "📁 Working directory: $(pwd) (Development)"
fi

# Start core services
start_service "API Gateway" "services.api_gateway:app" 9001
start_service "MCP Server" "services.mcp_server_api:app" 9000

# Wait for services to be ready
echo "⏳ Waiting for services to initialize..."
sleep 5

# Health checks for core services
if ! health_check "API Gateway" 9001; then
    echo "❌ API Gateway failed to start properly"
    exit 1
fi

if ! health_check "MCP Server" 9000; then
    echo "❌ MCP Server failed to start properly"
    exit 1
fi

# Start main health check server
echo "🏥 Starting main health check server on port $PORT..."

# Create production health check server
cat > /tmp/production_health.py << 'EOF'
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import httpx
import asyncio
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="TauseStack Production Health",
    description="Production health check and status endpoint",
    version="0.9.0",
    docs_url=None,  # Disable docs in production
    redoc_url=None  # Disable redoc in production
)

# Minimal CORS for health checks
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Only for health checks
    allow_methods=["GET"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Secure health check endpoint for load balancer"""
    try:
        # Check core services
        services_status = {}
        
        async with httpx.AsyncClient(timeout=2.0) as client:
            # Check API Gateway
            try:
                response = await client.get("http://localhost:9001/health")
                services_status["api_gateway"] = "healthy" if response.status_code == 200 else "unhealthy"
            except:
                services_status["api_gateway"] = "unhealthy"
            
            # Check MCP Server
            try:
                response = await client.get("http://localhost:9000/health")
                services_status["mcp_server"] = "healthy" if response.status_code == 200 else "unhealthy"
            except:
                services_status["mcp_server"] = "unhealthy"
        
        # Determine overall health
        all_healthy = all(status == "healthy" for status in services_status.values())
        
        if all_healthy:
            return {"status": "healthy", "services": services_status}
        else:
            raise HTTPException(status_code=503, detail={"status": "unhealthy", "services": services_status})
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail={"status": "error", "message": str(e)})

@app.get("/")
async def root():
    """Minimal public endpoint"""
    return {
        "service": "TauseStack",
        "version": "0.9.0",
        "status": "running"
    }

@app.get("/metrics")
async def metrics():
    """Basic metrics endpoint"""
    return {
        "uptime": "running",
        "version": "0.9.0",
        "services": ["api_gateway", "mcp_server"]
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info",
        access_log=True,
        server_header=False
    )
EOF

# Start main health server (foreground process)
echo "✅ TauseStack Production is ready!"
echo "📊 Health Check: http://localhost:$PORT/health"
echo "🌐 API Gateway: http://localhost:9001"
echo "🤖 MCP Server: http://localhost:9000"
echo "📈 Metrics: http://localhost:$PORT/metrics"

python /tmp/production_health.py 