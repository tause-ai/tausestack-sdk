#!/bin/bash

# TauseStack Local Development Startup Script
# Este script inicia todos los servicios necesarios para desarrollo local

set -e

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Iniciando TauseStack Local Development${NC}"
echo "=================================================="

# Verificar que estamos en el directorio correcto
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}❌ Error: No se encontró pyproject.toml. Ejecuta este script desde la raíz del proyecto.${NC}"
    exit 1
fi

# Activar entorno virtual
echo -e "${YELLOW}📦 Activando entorno virtual...${NC}"
if [ ! -d ".venv" ]; then
    echo -e "${RED}❌ Error: No se encontró el entorno virtual .venv${NC}"
    echo "Ejecuta: python3.12 -m venv .venv && source .venv/bin/activate && pip install -e '.[dev]'"
    exit 1
fi

source .venv/bin/activate

# Cargar variables de entorno
echo -e "${YELLOW}🌍 Cargando variables de entorno...${NC}"
set -a
source .env
set +a

echo -e "${GREEN}✅ Variables cargadas:${NC}"
echo "  - TAUSESTACK_BASE_DOMAIN: $TAUSESTACK_BASE_DOMAIN"
echo "  - NODE_ENV: $NODE_ENV"
echo "  - LOG_LEVEL: $LOG_LEVEL"

# Verificar que las dependencias estén instaladas
echo -e "${YELLOW}🔍 Verificando dependencias...${NC}"
if ! python -c "import tausestack" 2>/dev/null; then
    echo -e "${YELLOW}📦 Instalando dependencias...${NC}"
    pip install -e '.[dev]'
fi

# Detener procesos existentes
echo -e "${YELLOW}🛑 Deteniendo procesos existentes...${NC}"
pkill -f "tausestack framework run" || true
pkill -f "uvicorn.*tausestack" || true
pkill -f "python.*start_services" || true

# Iniciar servicios
echo -e "${YELLOW}🔧 Iniciando servicios...${NC}"

# 1. Framework principal
echo -e "${GREEN}🌐 Iniciando Framework (puerto 8000)...${NC}"
tausestack framework run --port 8000 &
FRAMEWORK_PID=$!
echo "  PID: $FRAMEWORK_PID"

# 2. API Gateway
echo -e "${GREEN}🚪 Iniciando API Gateway (puerto 9001)...${NC}"
python -m uvicorn tausestack.framework.main:app --host 0.0.0.0 --port 9001 --reload &
GATEWAY_PID=$!
echo "  PID: $GATEWAY_PID"

# 3. Servicios individuales
echo -e "${GREEN}📊 Iniciando Analytics (puerto 8001)...${NC}"
python -m uvicorn services.analytics.api.main:app --host 0.0.0.0 --port 8001 --reload &
ANALYTICS_PID=$!
echo "  PID: $ANALYTICS_PID"

echo -e "${GREEN}📧 Iniciando Communications (puerto 8002)...${NC}"
python -m uvicorn services.communications.api.main:app --host 0.0.0.0 --port 8002 --reload &
COMMUNICATIONS_PID=$!
echo "  PID: $COMMUNICATIONS_PID"

echo -e "${GREEN}💳 Iniciando Billing (puerto 8003)...${NC}"
python -m uvicorn services.billing.api.main:app --host 0.0.0.0 --port 8003 --reload &
BILLING_PID=$!
echo "  PID: $BILLING_PID"

echo -e "${GREEN}👥 Iniciando Users (puerto 8004)...${NC}"
python -m uvicorn services.users.api.main:app --host 0.0.0.0 --port 8004 --reload &
USERS_PID=$!
echo "  PID: $USERS_PID"

# Guardar PIDs para poder detenerlos después
echo "$FRAMEWORK_PID $GATEWAY_PID $ANALYTICS_PID $COMMUNICATIONS_PID $BILLING_PID $USERS_PID" > .pids

# Esperar un momento para que los servicios se inicien
echo -e "${YELLOW}⏳ Esperando que los servicios se inicien...${NC}"
sleep 5

# Verificar que los servicios estén funcionando
echo -e "${YELLOW}🔍 Verificando servicios...${NC}"

check_service() {
    local url=$1
    local name=$2
    if curl -s "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $name está funcionando${NC}"
        return 0
    else
        echo -e "${RED}❌ $name no está disponible${NC}"
        return 1
    fi
}

check_service "http://localhost:8000/health" "Framework"
check_service "http://localhost:9001/health" "API Gateway"
check_service "http://localhost:8001/health" "Analytics"
check_service "http://localhost:8002/health" "Communications"
check_service "http://localhost:8003/health" "Billing"
check_service "http://localhost:8004/health" "Users"

echo ""
echo -e "${GREEN}🎉 ¡TauseStack está funcionando!${NC}"
echo "=================================================="
echo -e "${GREEN}📱 URLs disponibles:${NC}"
echo "  - Framework:     http://localhost:8000"
echo "  - API Gateway:   http://localhost:9001"
echo "  - Analytics:     http://localhost:8001"
echo "  - Communications: http://localhost:8002"
echo "  - Billing:       http://localhost:8003"
echo "  - Users:         http://localhost:8004"
echo ""
echo -e "${GREEN}🔧 Comandos útiles:${NC}"
echo "  - Ver logs:      tail -f logs/tausestack.log"
echo "  - Detener:       ./scripts/stop_local.sh"
echo "  - Verificar:     python scripts/verify_setup.py"
echo ""
echo -e "${YELLOW}💡 Para desarrollo:${NC}"
echo "  - Los servicios se reiniciarán automáticamente al cambiar archivos"
echo "  - Usa Ctrl+C para detener todos los servicios"
echo "  - Los PIDs están guardados en .pids"

# Función de limpieza al salir
cleanup() {
    echo -e "\n${YELLOW}🛑 Deteniendo servicios...${NC}"
    if [ -f .pids ]; then
        for pid in $(cat .pids); do
            kill $pid 2>/dev/null || true
        done
        rm .pids
    fi
    echo -e "${GREEN}✅ Servicios detenidos${NC}"
    exit 0
}

# Capturar Ctrl+C
trap cleanup SIGINT

# Mantener el script corriendo
echo -e "${YELLOW}⏳ Presiona Ctrl+C para detener todos los servicios${NC}"
while true; do
    sleep 1
done 