#!/bin/bash

# TauseStack Local Development Stop Script
# Este script detiene todos los servicios de desarrollo local

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🛑 Deteniendo TauseStack Local Development${NC}"
echo "=================================================="

# Detener procesos por PIDs guardados
if [ -f .pids ]; then
    echo -e "${YELLOW}📋 Deteniendo procesos por PIDs...${NC}"
    for pid in $(cat .pids); do
        if kill -0 $pid 2>/dev/null; then
            echo -e "${GREEN}✅ Deteniendo proceso $pid${NC}"
            kill $pid
        else
            echo -e "${YELLOW}⚠️  Proceso $pid ya no está corriendo${NC}"
        fi
    done
    rm .pids
    echo -e "${GREEN}✅ PIDs limpiados${NC}"
fi

# Detener procesos por nombre (backup)
echo -e "${YELLOW}🔍 Deteniendo procesos por nombre...${NC}"
pkill -f "tausestack framework run" && echo -e "${GREEN}✅ Framework detenido${NC}" || echo -e "${YELLOW}⚠️  Framework no estaba corriendo${NC}"
pkill -f "uvicorn.*tausestack" && echo -e "${GREEN}✅ Uvicorn detenido${NC}" || echo -e "${YELLOW}⚠️  Uvicorn no estaba corriendo${NC}"
pkill -f "python.*start_services" && echo -e "${GREEN}✅ Start services detenido${NC}" || echo -e "${YELLOW}⚠️  Start services no estaba corriendo${NC}"

# Verificar que no queden procesos
echo -e "${YELLOW}🔍 Verificando que no queden procesos...${NC}"
if pgrep -f "tausestack\|uvicorn.*tausestack" > /dev/null; then
    echo -e "${RED}❌ Aún hay procesos corriendo:${NC}"
    pgrep -f "tausestack\|uvicorn.*tausestack" | xargs ps -p
else
    echo -e "${GREEN}✅ Todos los procesos han sido detenidos${NC}"
fi

echo ""
echo -e "${GREEN}🎉 ¡TauseStack ha sido detenido completamente!${NC}"
echo ""
echo -e "${YELLOW}💡 Para reiniciar:${NC}"
echo "  ./scripts/start_local.sh" 