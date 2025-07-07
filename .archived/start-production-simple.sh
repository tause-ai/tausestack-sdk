#!/bin/bash

# TauseStack Production Startup Script - SIMPLE VERSION
# Evita rate limiting y problemas de configuración
set -euo pipefail

echo "🚀 Starting TauseStack Production v0.9.0 (Simple Mode)..."

# Load environment configuration
if [[ -f "config/local.env" ]]; then
    echo "📋 Loading local environment configuration..."
    set -a
    source config/local.env
    set +a
else
    echo "⚠️  No local environment configuration found"
    exit 1
fi

# Set defaults
export PORT=${PORT:-8000}
export ENVIRONMENT=development

echo "📋 Environment:"
echo "  PORT: $PORT"
echo "  ENVIRONMENT: $ENVIRONMENT"

# Cleanup function
cleanup() {
    echo "🧹 Cleaning up services..."
    pkill -f "uvicorn.*services" || true
    pkill -f "production_health" || true
}

# Set up signal handlers
trap cleanup EXIT INT TERM

# Find available ports
find_available_port() {
    local port=$1
    while lsof -i :$port >/dev/null 2>&1; do
        ((port++))
        if [[ $port -gt 9999 ]]; then
            echo "No available ports found"
            exit 1
        fi
    done
    echo $port
}

# Start API Gateway on available port
API_GATEWAY_PORT=$(find_available_port 9001)
echo "🌐 Starting API Gateway on port $API_GATEWAY_PORT..."
python -m uvicorn services.api_gateway:app \
    --host 0.0.0.0 \
    --port $API_GATEWAY_PORT \
    --log-level info &

API_GATEWAY_PID=$!
echo "📝 API Gateway started with PID: $API_GATEWAY_PID"

# Start MCP Server on available port
MCP_SERVER_PORT=$(find_available_port 9000)
echo "🤖 Starting MCP Server on port $MCP_SERVER_PORT..."
python -m uvicorn services.mcp_server_api:app \
    --host 0.0.0.0 \
    --port $MCP_SERVER_PORT \
    --log-level info &

MCP_SERVER_PID=$!
echo "📝 MCP Server started with PID: $MCP_SERVER_PID"

# Wait for services to start
echo "⏳ Waiting for services to initialize..."
sleep 10

# Simple health checks
echo "🔍 Checking API Gateway health..."
if curl -sf "http://localhost:$API_GATEWAY_PORT/" >/dev/null 2>&1; then
    echo "✅ API Gateway is responding"
else
    echo "❌ API Gateway is not responding"
fi

echo "🔍 Checking MCP Server health..."
if curl -sf "http://localhost:$MCP_SERVER_PORT/health" >/dev/null 2>&1; then
    echo "✅ MCP Server is responding"
else
    echo "❌ MCP Server is not responding"
fi

# Create simple health check server
echo "🏥 Starting health check server on port $PORT..."

cat > /tmp/simple_health.py << EOF
from fastapi import FastAPI
import uvicorn
import os

app = FastAPI(title="TauseStack Health", version="0.9.0")

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "0.9.0"}

@app.get("/")
async def root():
    return {"service": "TauseStack", "version": "0.9.0", "status": "running"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
EOF

echo "✅ TauseStack Production is ready!"
echo "📊 Health Check: http://localhost:$PORT/health"
echo "🌐 API Gateway: http://localhost:$API_GATEWAY_PORT"
echo "🤖 MCP Server: http://localhost:$MCP_SERVER_PORT"

# Start health server (foreground)
python /tmp/simple_health.py 