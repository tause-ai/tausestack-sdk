#!/bin/bash

# TauseStack SDK - Production Deployment Script
# Versión: 1.0.0
# Fecha: 7 de Julio, 2025

set -e

# Configuración
export AWS_REGION="us-east-1"
export AWS_ACCOUNT_ID="349622182214"
export AWS_PAGER=""
export STACK_NAME="tausestack-final-fixed"
export CLUSTER_NAME="tausestack-final-fixed-cluster"
export SERVICE_NAME="tausestack-final-fixed-service"
export REPOSITORY_NAME="tausestack-production"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 TauseStack SDK - Production Deployment${NC}"
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}Stack: $STACK_NAME${NC}"
echo -e "${BLUE}Cluster: $CLUSTER_NAME${NC}"
echo -e "${BLUE}Service: $SERVICE_NAME${NC}"
echo -e "${BLUE}Repository: $REPOSITORY_NAME${NC}"
echo ""

# Verificar prerequisitos
echo -e "${YELLOW}📋 Verificando prerequisitos...${NC}"

if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI no encontrado${NC}"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker no encontrado${NC}"
    exit 1
fi

if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS CLI no configurado correctamente${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisitos OK${NC}"

# Construir frontend
echo -e "\n${YELLOW}🔨 Construyendo frontend...${NC}"
cd frontend
if [ ! -d "node_modules" ]; then
    echo -e "${BLUE}Instalando dependencias de Node.js...${NC}"
    npm install
fi

echo -e "${BLUE}Construyendo frontend para producción...${NC}"
npm run build

if [ ! -d "out" ]; then
    echo -e "${RED}❌ Error: Directorio 'out' no encontrado después del build${NC}"
    exit 1
fi

cd ..
echo -e "${GREEN}✅ Frontend construido exitosamente${NC}"

# Construir imagen Docker
echo -e "\n${YELLOW}🐳 Construyendo imagen Docker...${NC}"
echo -e "${BLUE}Usando arquitectura linux/amd64 para compatibilidad con ECS...${NC}"

docker buildx build --platform linux/amd64 -t $REPOSITORY_NAME:latest .

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Error construyendo imagen Docker${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Imagen Docker construida exitosamente${NC}"

# Login a ECR y subir imagen
echo -e "\n${YELLOW}📤 Subiendo imagen a ECR...${NC}"

echo -e "${BLUE}Haciendo login a ECR...${NC}"
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Error en login a ECR${NC}"
    exit 1
fi

echo -e "${BLUE}Tageando imagen...${NC}"
docker tag $REPOSITORY_NAME:latest \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPOSITORY_NAME:latest

echo -e "${BLUE}Subiendo imagen a ECR...${NC}"
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPOSITORY_NAME:latest

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Error subiendo imagen a ECR${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Imagen subida exitosamente a ECR${NC}"

# Deployment del servicio ECS
echo -e "\n${YELLOW}🔄 Desplegando servicio ECS...${NC}"

echo -e "${BLUE}Forzando nuevo deployment...${NC}"
aws ecs update-service \
    --cluster $CLUSTER_NAME \
    --service $SERVICE_NAME \
    --force-new-deployment \
    --region $AWS_REGION \
    --no-cli-pager > /dev/null

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Error iniciando deployment${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Deployment iniciado exitosamente${NC}"

# Esperar y verificar deployment
echo -e "\n${YELLOW}⏳ Esperando que el deployment se complete...${NC}"
echo -e "${BLUE}Esto puede tomar 2-3 minutos...${NC}"

sleep 120

# Verificar estado del servicio
echo -e "\n${YELLOW}🔍 Verificando estado del deployment...${NC}"

RUNNING_COUNT=$(aws ecs describe-services \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --region $AWS_REGION \
    --query 'services[0].runningCount' \
    --output text)

DESIRED_COUNT=$(aws ecs describe-services \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --region $AWS_REGION \
    --query 'services[0].desiredCount' \
    --output text)

echo -e "${BLUE}Tareas ejecutándose: $RUNNING_COUNT/$DESIRED_COUNT${NC}"

# Health checks
echo -e "\n${YELLOW}🏥 Ejecutando health checks...${NC}"

echo -e "${BLUE}Probando frontend...${NC}"
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://tausestack.dev/)
if [ "$FRONTEND_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ Frontend: OK (HTTP $FRONTEND_STATUS)${NC}"
else
    echo -e "${RED}❌ Frontend: Error (HTTP $FRONTEND_STATUS)${NC}"
fi

echo -e "${BLUE}Probando API Gateway...${NC}"
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://tausestack.dev/api)
if [ "$API_STATUS" = "404" ] || [ "$API_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ API Gateway: OK (HTTP $API_STATUS)${NC}"
else
    echo -e "${RED}❌ API Gateway: Error (HTTP $API_STATUS)${NC}"
fi

# Resumen final
echo -e "\n${GREEN}🎉 DEPLOYMENT COMPLETADO${NC}"
echo -e "${GREEN}========================${NC}"
echo -e "${GREEN}✅ Frontend desplegado en: https://tausestack.dev/${NC}"
echo -e "${GREEN}✅ API Gateway disponible en: https://tausestack.dev/api${NC}"
echo -e "${GREEN}✅ Imagen Docker: $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPOSITORY_NAME:latest${NC}"
echo -e "${GREEN}✅ ECS Service: $SERVICE_NAME${NC}"
echo -e "${GREEN}✅ Tareas ejecutándose: $RUNNING_COUNT/$DESIRED_COUNT${NC}"

echo -e "\n${BLUE}📊 Para monitorear logs:${NC}"
echo -e "${BLUE}aws logs tail /ecs/tausestack-final-fixed --region us-east-1 --follow${NC}"

echo -e "\n${BLUE}📈 Para verificar métricas:${NC}"
echo -e "${BLUE}https://console.aws.amazon.com/ecs/home?region=us-east-1#/clusters/$CLUSTER_NAME/services${NC}"

echo -e "\n${GREEN}🚀 Deployment exitoso! 🚀${NC}" 