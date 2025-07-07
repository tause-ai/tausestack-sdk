#!/bin/bash

# TauseStack SDK - Development Startup Script
# Este script inicia todos los servicios para desarrollo local

set -e

echo "🚀 Iniciando TauseStack SDK en modo desarrollo..."

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Verificar que estamos en el directorio correcto
if [[ ! -f "pyproject.toml" ]]; then
    error "No se encontró pyproject.toml. Ejecuta este script desde el directorio raíz del proyecto."
    exit 1
fi

# Verificar Python
if ! command -v python &> /dev/null; then
    error "Python no está instalado o no está en el PATH"
    exit 1
fi

# Verificar dependencias
log "Verificando dependencias..."
if ! python -c "import tausestack" 2>/dev/null; then
    warn "El SDK no está instalado. Instalando en modo desarrollo..."
    pip install -e .
fi

# Configurar variables de entorno para desarrollo
export TAUSESTACK_ENVIRONMENT=development
export TAUSESTACK_TENANT_ID=default
export TAUSESTACK_STORAGE_BACKEND=local
export TAUSESTACK_CACHE_BACKEND=memory
export TAUSESTACK_NOTIFY_BACKEND=console
export TAUSESTACK_LOG_LEVEL=DEBUG

# Crear directorio de datos local
mkdir -p data/storage data/cache data/logs

# Función para iniciar un servicio
start_service() {
    local service_name=$1
    local port=$2
    local module_path=$3
    
    log "Iniciando $service_name en puerto $port..."
    
    # Verificar si el puerto está disponible
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        warn "Puerto $port ya está en uso. Saltando $service_name..."
        return
    fi
    
    # Iniciar el servicio en background
    python -m $module_path --port $port --host 0.0.0.0 > data/logs/${service_name}.log 2>&1 &
    local pid=$!
    
    # Guardar PID
    echo $pid > data/logs/${service_name}.pid
    
    # Esperar un momento para verificar que el servicio inició
    sleep 2
    
    if kill -0 $pid 2>/dev/null; then
        log "$service_name iniciado correctamente (PID: $pid)"
    else
        error "Error al iniciar $service_name"
        cat data/logs/${service_name}.log
    fi
}

# Función para verificar que un servicio esté funcionando
check_service() {
    local service_name=$1
    local port=$2
    
    log "Verificando $service_name..."
    
    if curl -s -f http://localhost:$port/health >/dev/null 2>&1; then
        log "$service_name está funcionando correctamente"
        return 0
    else
        warn "$service_name no responde en el puerto $port"
        return 1
    fi
}

# Iniciar servicios
log "Iniciando microservicios..."

# API Gateway (principal)
start_service "api-gateway" 8000 "tausestack.services.api_gateway"

# Analytics Service
start_service "analytics" 8001 "tausestack.services.analytics.api.main"

# Communications Service
start_service "communications" 8002 "tausestack.services.communications.api.main"

# Billing Service
start_service "billing" 8003 "tausestack.services.billing.api.main"

# Templates Service
start_service "templates" 8004 "tausestack.services.templates.api.main"

# AI Services
start_service "ai-services" 8005 "tausestack.services.ai_services.api.main"

# Esperar a que todos los servicios estén listos
log "Esperando a que todos los servicios estén listos..."
sleep 5

# Verificar servicios
log "Verificando servicios..."
all_services_ok=true

services=(
    "api-gateway:8000"
    "analytics:8001"
    "communications:8002"
    "billing:8003"
    "templates:8004"
    "ai-services:8005"
)

for service in "${services[@]}"; do
    IFS=':' read -r name port <<< "$service"
    if ! check_service "$name" "$port"; then
        all_services_ok=false
    fi
done

if $all_services_ok; then
    log "✅ Todos los servicios están funcionando correctamente!"
    echo ""
    echo -e "${BLUE}🌐 URLs de los servicios:${NC}"
    echo "  • API Gateway:     http://localhost:8000"
    echo "  • Analytics:       http://localhost:8001"
    echo "  • Communications:  http://localhost:8002"
    echo "  • Billing:         http://localhost:8003"
    echo "  • Templates:       http://localhost:8004"
    echo "  • AI Services:     http://localhost:8005"
    echo ""
    echo -e "${BLUE}📚 Documentación:${NC}"
    echo "  • API Docs:        http://localhost:8000/docs"
    echo "  • Redoc:           http://localhost:8000/redoc"
    echo ""
    echo -e "${BLUE}🔧 Comandos útiles:${NC}"
    echo "  • Ver logs:        tail -f data/logs/*.log"
    echo "  • Detener todo:    ./scripts/stop-dev.sh"
    echo "  • Reiniciar:       ./scripts/restart-dev.sh"
    echo ""
    echo -e "${GREEN}🎉 TauseStack SDK está listo para desarrollo!${NC}"
else
    error "Algunos servicios no pudieron iniciarse. Revisa los logs en data/logs/"
    exit 1
fi

# Función para cleanup al recibir señal
cleanup() {
    log "Deteniendo servicios..."
    for service in "${services[@]}"; do
        IFS=':' read -r name port <<< "$service"
        if [[ -f "data/logs/${name}.pid" ]]; then
            pid=$(cat "data/logs/${name}.pid")
            if kill -0 $pid 2>/dev/null; then
                kill $pid
                log "$name detenido"
            fi
            rm -f "data/logs/${name}.pid"
        fi
    done
    log "Todos los servicios han sido detenidos"
    exit 0
}

# Registrar función de cleanup
trap cleanup SIGINT SIGTERM

# Mantener el script corriendo
log "Servicios en ejecución. Presiona Ctrl+C para detener todos los servicios."
while true; do
    sleep 10
done 