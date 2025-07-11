#!/bin/bash

# TausePro Deployment Script
# Configura dominios tause.pro y app.tause.pro
# Despliega landing page y aplicación separadas

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
STACK_NAME="tausepro-production"
DOMAIN_NAME="tause.pro"
REGION="us-east-1"
PROFILE="default"

# Verificar que Route 53 hosted zone existe
check_hosted_zone() {
    echo -e "${BLUE}Verificando hosted zone para $DOMAIN_NAME...${NC}"
    
    HOSTED_ZONE_ID=$(aws route53 list-hosted-zones \
        --query "HostedZones[?Name=='${DOMAIN_NAME}.'].Id" \
        --output text \
        --profile $PROFILE 2>/dev/null)
    
    if [ -z "$HOSTED_ZONE_ID" ]; then
        echo -e "${RED}Error: No se encontró hosted zone para $DOMAIN_NAME${NC}"
        echo -e "${YELLOW}Debes crear la hosted zone primero:${NC}"
        echo "aws route53 create-hosted-zone --name $DOMAIN_NAME --caller-reference $(date +%s)"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Hosted zone encontrada: $HOSTED_ZONE_ID${NC}"
}

# Verificar certificado SSL
check_ssl_certificate() {
    echo -e "${BLUE}Verificando certificado SSL para $DOMAIN_NAME...${NC}"
    
    CERT_ARN=$(aws acm list-certificates \
        --query "CertificateSummaryList[?DomainName=='${DOMAIN_NAME}'].CertificateArn" \
        --output text \
        --region $REGION \
        --profile $PROFILE 2>/dev/null)
    
    if [ -z "$CERT_ARN" ]; then
        echo -e "${YELLOW}Certificado SSL no encontrado. Se creará automáticamente.${NC}"
    else
        echo -e "${GREEN}✓ Certificado SSL encontrado: $CERT_ARN${NC}"
    fi
}

# Crear ECR repositories si no existen
create_ecr_repositories() {
    echo -e "${BLUE}Creando repositorios ECR...${NC}"
    
    # Crear repositorio principal
    aws ecr create-repository \
        --repository-name $STACK_NAME \
        --region $REGION \
        --profile $PROFILE 2>/dev/null || true
    
    echo -e "${GREEN}✓ Repositorio ECR creado/verificado${NC}"
}

# Validar template CloudFormation
validate_template() {
    echo -e "${BLUE}Validando template CloudFormation...${NC}"
    
    aws cloudformation validate-template \
        --template-body file://tausestack/infrastructure/aws/tause-pro-production.yml \
        --region $REGION \
        --profile $PROFILE
    
    echo -e "${GREEN}✓ Template válido${NC}"
}

# Desplegar stack
deploy_stack() {
    echo -e "${BLUE}Desplegando stack $STACK_NAME...${NC}"
    
    # Obtener credenciales Supabase
    SUPABASE_URL=${SUPABASE_URL:-"https://vjoxmprmcbkmhwmbniaz.supabase.co"}
    SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY:-"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZqb3htcHJtY2JrbWh3bWJuaWF6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE1NzM4NzQsImV4cCI6MjA2NzE0OTg3NH0.qGNPGLdUBIUiYlGNvOqOKqYNTSNvQHpHgOy7EZKfg7g"}
    
    aws cloudformation deploy \
        --template-file tausestack/infrastructure/aws/tause-pro-production.yml \
        --stack-name $STACK_NAME \
        --parameter-overrides \
            Environment=production \
            DomainName=$DOMAIN_NAME \
            SubabaseUrl=$SUPABASE_URL \
            SupabaseAnonKey=$SUPABASE_ANON_KEY \
        --capabilities CAPABILITY_IAM \
        --region $REGION \
        --profile $PROFILE
    
    echo -e "${GREEN}✓ Stack desplegado exitosamente${NC}"
}

# Obtener outputs del stack
get_stack_outputs() {
    echo -e "${BLUE}Obteniendo información del stack...${NC}"
    
    # Obtener ECR repository URI
    ECR_REPO=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --query "Stacks[0].Outputs[?OutputKey=='ECRRepository'].OutputValue" \
        --output text \
        --region $REGION \
        --profile $PROFILE)
    
    # Obtener URLs
    LANDING_URL=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --query "Stacks[0].Outputs[?OutputKey=='LandingPageURL'].OutputValue" \
        --output text \
        --region $REGION \
        --profile $PROFILE)
    
    APP_URL=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --query "Stacks[0].Outputs[?OutputKey=='AppURL'].OutputValue" \
        --output text \
        --region $REGION \
        --profile $PROFILE)
    
    # Obtener Load Balancer DNS
    ALB_DNS=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --query "Stacks[0].Outputs[?OutputKey=='LoadBalancerDNS'].OutputValue" \
        --output text \
        --region $REGION \
        --profile $PROFILE)
    
    echo -e "${GREEN}✓ Información del stack obtenida${NC}"
    echo -e "${BLUE}ECR Repository:${NC} $ECR_REPO"
    echo -e "${BLUE}Landing Page:${NC} $LANDING_URL"
    echo -e "${BLUE}App URL:${NC} $APP_URL"
    echo -e "${BLUE}Load Balancer DNS:${NC} $ALB_DNS"
}

# Construir y subir imágenes Docker
build_and_push_images() {
    echo -e "${BLUE}Construyendo imágenes Docker...${NC}"
    
    # Login a ECR
    aws ecr get-login-password --region $REGION --profile $PROFILE | \
        docker login --username AWS --password-stdin $ECR_REPO
    
    # Construir imagen para landing page
    echo -e "${BLUE}Construyendo landing page...${NC}"
    docker build -t $STACK_NAME:landing-latest \
        -f docker/Dockerfile.landing \
        --build-arg NEXT_PUBLIC_DOMAIN=$DOMAIN_NAME \
        --build-arg NEXT_PUBLIC_TAUSESTACK_API=https://api.tausestack.dev \
        .
    
    # Construir imagen para aplicación
    echo -e "${BLUE}Construyendo aplicación...${NC}"
    docker build -t $STACK_NAME:app-latest \
        -f docker/Dockerfile.app \
        --build-arg NEXT_PUBLIC_DOMAIN=$DOMAIN_NAME \
        --build-arg NEXT_PUBLIC_TAUSESTACK_API=https://api.tausestack.dev \
        .
    
    # Tagear y subir imágenes
    docker tag $STACK_NAME:landing-latest $ECR_REPO:landing-latest
    docker tag $STACK_NAME:app-latest $ECR_REPO:app-latest
    
    docker push $ECR_REPO:landing-latest
    docker push $ECR_REPO:app-latest
    
    echo -e "${GREEN}✓ Imágenes construidas y subidas${NC}"
}

# Función principal
main() {
    echo -e "${GREEN}🚀 Iniciando deployment de TausePro${NC}"
    echo -e "${BLUE}Stack: $STACK_NAME${NC}"
    echo -e "${BLUE}Dominio: $DOMAIN_NAME${NC}"
    echo -e "${BLUE}Región: $REGION${NC}"
    echo ""
    
    # Verificaciones previas
    check_hosted_zone
    check_ssl_certificate
    create_ecr_repositories
    validate_template
    
    # Desplegar infraestructura
    deploy_stack
    get_stack_outputs
    
    # Construir y subir imágenes (opcional)
    read -p "¿Deseas construir y subir las imágenes Docker? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        build_and_push_images
    fi
    
    echo ""
    echo -e "${GREEN}🎉 Deployment completado exitosamente!${NC}"
    echo -e "${BLUE}Landing Page:${NC} https://$DOMAIN_NAME"
    echo -e "${BLUE}Aplicación:${NC} https://app.$DOMAIN_NAME"
    echo ""
    echo -e "${YELLOW}📋 Próximos pasos:${NC}"
    echo "1. Configurar DNS en tu proveedor de dominio para apuntar a:"
    echo "   - $DOMAIN_NAME → $ALB_DNS"
    echo "   - app.$DOMAIN_NAME → $ALB_DNS"
    echo "2. Esperar propagación DNS (puede tomar hasta 48 horas)"
    echo "3. Verificar certificado SSL automático"
    echo "4. Construir y desplegar aplicaciones"
}

# Verificar requisitos
command -v aws >/dev/null 2>&1 || { echo "AWS CLI requerido pero no instalado. Saliendo." >&2; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "Docker requerido pero no instalado. Saliendo." >&2; exit 1; }

# Ejecutar función principal
main "$@" 