#!/bin/bash

# TauseStack SDK - Project Cleanup Script
# Versión: 1.0.0
# Fecha: 7 de Julio, 2025

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🧹 TauseStack SDK - Project Cleanup${NC}"
echo -e "${BLUE}===================================${NC}"

# Crear directorio de archivos obsoletos
echo -e "\n${YELLOW}📁 Creando directorio de archivos obsoletos...${NC}"
mkdir -p .archived

# Scripts obsoletos de deployment
echo -e "\n${YELLOW}🗑️ Archivando scripts obsoletos de deployment...${NC}"
OBSOLETE_SCRIPTS=(
    "deploy-mvp.sh"
    "deploy-complete.sh"
    "start-production-simple.sh"
    "cleanup_for_aws.py"
    "real_cleanup_for_aws.py"
)

for script in "${OBSOLETE_SCRIPTS[@]}"; do
    if [ -f "scripts/$script" ]; then
        echo -e "${BLUE}Archivando: $script${NC}"
        mv "scripts/$script" ".archived/"
    fi
done

# Scripts de desarrollo local (mantener pero organizar)
echo -e "\n${YELLOW}📂 Organizando scripts de desarrollo...${NC}"
mkdir -p scripts/dev
DEV_SCRIPTS=(
    "start_local.sh"
    "stop_local.sh"
    "start-dev.sh"
    "start_services.py"
    "start_ai_services.py"
    "start_template_engine.py"
    "verify_setup.py"
)

for script in "${DEV_SCRIPTS[@]}"; do
    if [ -f "scripts/$script" ]; then
        echo -e "${BLUE}Moviendo a dev/: $script${NC}"
        mv "scripts/$script" "scripts/dev/"
    fi
done

# Scripts de infraestructura
echo -e "\n${YELLOW}🏗️ Organizando scripts de infraestructura...${NC}"
mkdir -p scripts/infrastructure
INFRA_SCRIPTS=(
    "setup-domain.sh"
    "setup-supabase-production.sh"
)

for script in "${INFRA_SCRIPTS[@]}"; do
    if [ -f "scripts/$script" ]; then
        echo -e "${BLUE}Moviendo a infrastructure/: $script${NC}"
        mv "scripts/$script" "scripts/infrastructure/"
    fi
done

# Limpiar archivos temporales de Docker
echo -e "\n${YELLOW}🐳 Limpiando imágenes Docker no utilizadas...${NC}"
if command -v docker &> /dev/null; then
    echo -e "${BLUE}Eliminando imágenes Docker sin usar...${NC}"
    docker image prune -f > /dev/null 2>&1 || true
    echo -e "${GREEN}✅ Imágenes Docker limpiadas${NC}"
else
    echo -e "${YELLOW}⚠️ Docker no encontrado, saltando limpieza${NC}"
fi

# Limpiar archivos de build del frontend
echo -e "\n${YELLOW}🔧 Limpiando archivos de build...${NC}"
if [ -d "frontend/.next" ]; then
    echo -e "${BLUE}Eliminando .next/...${NC}"
    rm -rf frontend/.next
fi

if [ -d "frontend/out" ]; then
    echo -e "${BLUE}Manteniendo out/ (necesario para deployment)${NC}"
fi

# Limpiar archivos Python temporales
echo -e "\n${YELLOW}🐍 Limpiando archivos Python temporales...${NC}"
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true
echo -e "${GREEN}✅ Archivos Python temporales eliminados${NC}"

# Crear README para archivos archivados
echo -e "\n${YELLOW}📝 Creando documentación de archivos archivados...${NC}"
cat > .archived/README.md << 'EOF'
# Archivos Archivados - TauseStack SDK

Este directorio contiene scripts y archivos que fueron utilizados durante el desarrollo y deployment inicial del proyecto, pero que ya no son necesarios para el funcionamiento actual del sistema.

## Scripts Archivados

### Scripts de Deployment Obsoletos
- `deploy-mvp.sh` - Script inicial de deployment MVP
- `deploy-complete.sh` - Script de deployment completo obsoleto
- `start-production-simple.sh` - Script simplificado de producción
- `cleanup_for_aws.py` - Script de limpieza inicial
- `real_cleanup_for_aws.py` - Script de limpieza mejorado

## Por qué se archivaron

Estos scripts fueron reemplazados por:
- `scripts/deploy-production.sh` - Script de deployment optimizado y actual
- Documentación completa en `DEPLOYMENT_AWS_GUIDE.md`
- Organización mejorada de scripts en subdirectorios

## Restauración

Si necesitas restaurar algún archivo:
```bash
mv .archived/[archivo] scripts/
```

**Fecha de archivado**: 7 de Julio, 2025
**Versión del proyecto**: 1.0.0
EOF

# Hacer ejecutables los scripts principales
echo -e "\n${YELLOW}⚙️ Configurando permisos de scripts...${NC}"
chmod +x scripts/deploy-production.sh
chmod +x scripts/cleanup-project.sh
chmod +x scripts/dev/* 2>/dev/null || true
chmod +x scripts/infrastructure/* 2>/dev/null || true

# Crear script de status del proyecto
echo -e "\n${YELLOW}📊 Creando script de status...${NC}"
cat > scripts/status.sh << 'EOF'
#!/bin/bash

# TauseStack SDK - Status Check Script

export AWS_PAGER=""
export AWS_REGION="us-east-1"

echo "🚀 TauseStack SDK - Status Check"
echo "================================"

echo -e "\n🌐 URLs:"
echo "Frontend: https://tausestack.dev/"
echo "API Gateway: https://tausestack.dev/api"

echo -e "\n📊 AWS Resources:"
echo "Stack: tausestack-final-fixed"
echo "Cluster: tausestack-final-fixed-cluster"
echo "Service: tausestack-final-fixed-service"

echo -e "\n🔍 Health Checks:"
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://tausestack.dev/)
echo "Frontend: HTTP $FRONTEND_STATUS"

API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://tausestack.dev/api)
echo "API Gateway: HTTP $API_STATUS"

echo -e "\n📈 ECS Service Status:"
aws ecs describe-services \
    --cluster tausestack-final-fixed-cluster \
    --services tausestack-final-fixed-service \
    --region us-east-1 \
    --query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount,Pending:pendingCount}' \
    --output table 2>/dev/null || echo "Error obteniendo estado de ECS"

echo -e "\n📋 Para ver logs en tiempo real:"
echo "aws logs tail /ecs/tausestack-final-fixed --region us-east-1 --follow"
EOF

chmod +x scripts/status.sh

# Resumen final
echo -e "\n${GREEN}🎉 LIMPIEZA COMPLETADA${NC}"
echo -e "${GREEN}=====================${NC}"
echo -e "${GREEN}✅ Scripts obsoletos archivados en .archived/${NC}"
echo -e "${GREEN}✅ Scripts de desarrollo organizados en scripts/dev/${NC}"
echo -e "${GREEN}✅ Scripts de infraestructura en scripts/infrastructure/${NC}"
echo -e "${GREEN}✅ Archivos temporales eliminados${NC}"
echo -e "${GREEN}✅ Permisos configurados correctamente${NC}"
echo -e "${GREEN}✅ Script de status creado${NC}"

echo -e "\n${BLUE}📁 Estructura final de scripts:${NC}"
echo -e "${BLUE}scripts/${NC}"
echo -e "${BLUE}├── deploy-production.sh    (Deployment principal)${NC}"
echo -e "${BLUE}├── status.sh              (Status del sistema)${NC}"
echo -e "${BLUE}├── cleanup-project.sh     (Este script)${NC}"
echo -e "${BLUE}├── dev/                   (Scripts de desarrollo)${NC}"
echo -e "${BLUE}└── infrastructure/        (Scripts de infraestructura)${NC}"

echo -e "\n${BLUE}📚 Documentación principal:${NC}"
echo -e "${BLUE}├── DEPLOYMENT_AWS_GUIDE.md (Guía completa de deployment)${NC}"
echo -e "${BLUE}├── README.md              (Documentación general)${NC}"
echo -e "${BLUE}└── .archived/README.md    (Documentación de archivos archivados)${NC}"

echo -e "\n${GREEN}🚀 Proyecto listo para Git push! 🚀${NC}" 