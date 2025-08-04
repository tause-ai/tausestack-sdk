#!/bin/bash

# TauseStack Economical Deployment Script for tause.pro
# Optimized for minimal AWS costs

set -e

# Configuration
STACK_NAME="tausestack-economical"
DOMAIN_NAME="tause.pro"
AWS_REGION="us-east-1"
TEMPLATE_FILE="infrastructure/aws/tause-pro-economical.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Verificando prerrequisitos..."
    
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI no está instalado"
        exit 1
    fi
    
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials no configuradas"
        exit 1
    fi
    
    if [ ! -f "$TEMPLATE_FILE" ]; then
        log_error "Template CloudFormation no encontrado: $TEMPLATE_FILE"
        exit 1
    fi
    
    log_success "Prerrequisitos verificados ✓"
}

# Generate secure password
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

# Create SSL certificate
create_ssl_certificate() {
    log_info "Verificando certificado SSL..."
    
    CERT_ARN=$(aws acm list-certificates \
        --region $AWS_REGION \
        --query "CertificateSummaryList[?DomainName=='*.${DOMAIN_NAME}'].CertificateArn" \
        --output text 2>/dev/null || echo "")
    
    if [ -z "$CERT_ARN" ] || [ "$CERT_ARN" == "None" ]; then
        log_error "No se encontró certificado SSL para *.${DOMAIN_NAME}"
        log_error "Debes crear y validar el certificado SSL primero"
        exit 1
    else
        log_success "Certificado SSL encontrado: $CERT_ARN"
    fi
    
    echo "$CERT_ARN"
}

# Create ECR repository
create_ecr_repository() {
    log_info "Verificando repositorio ECR..."
    
    if ! aws ecr describe-repositories --repository-names tausestack --region $AWS_REGION >/dev/null 2>&1; then
        log_info "Creando repositorio ECR..."
        aws ecr create-repository \
            --repository-name tausestack \
            --region $AWS_REGION \
            --image-scanning-configuration scanOnPush=true \
            --encryption-configuration encryptionType=AES256 >/dev/null
        log_success "Repositorio ECR creado ✓"
    else
        log_success "Repositorio ECR ya existe ✓"
    fi
}

# Build and push using CodeBuild
build_and_push_image() {
    log_info "Construyendo imagen con AWS CodeBuild..."
    
    # Create buildspec
    cat > buildspec.yml << 'BUILDSPEC_EOF'
version: 0.2
phases:
  pre_build:
    commands:
      - echo Logging in to Amazon ECR...
      - aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com
  build:
    commands:
      - echo Build started on `date`
      - echo Building the Docker image...
      - docker build -t $IMAGE_REPO_NAME:$IMAGE_TAG .
      - docker tag $IMAGE_REPO_NAME:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG
  post_build:
    commands:
      - echo Build completed on `date`
      - echo Pushing the Docker image...
      - docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG
BUILDSPEC_EOF

    # Get account ID
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    
    # Create CodeBuild role if needed
    if ! aws iam get-role --role-name TauseStackCodeBuildRole >/dev/null 2>&1; then
        log_info "Creando rol para CodeBuild..."
        
        cat > trust-policy.json << 'TRUST_EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "codebuild.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
TRUST_EOF

        aws iam create-role \
            --role-name TauseStackCodeBuildRole \
            --assume-role-policy-document file://trust-policy.json >/dev/null

        aws iam attach-role-policy \
            --role-name TauseStackCodeBuildRole \
            --policy-arn arn:aws:iam::aws:policy/CloudWatchLogsFullAccess >/dev/null

        aws iam attach-role-policy \
            --role-name TauseStackCodeBuildRole \
            --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser >/dev/null

        sleep 10
        rm trust-policy.json
    fi
    
    # Create CodeBuild project if needed
    if ! aws codebuild batch-get-projects --names tausestack-build --region $AWS_REGION >/dev/null 2>&1; then
        log_info "Creando proyecto CodeBuild..."
        
        aws codebuild create-project \
            --name tausestack-build \
            --source type=NO_SOURCE,buildspec=buildspec.yml \
            --artifacts type=NO_ARTIFACTS \
            --environment type=LINUX_CONTAINER,image=aws/codebuild/standard:5.0,computeType=BUILD_GENERAL1_MEDIUM,privilegedMode=true \
            --service-role arn:aws:iam::${ACCOUNT_ID}:role/TauseStackCodeBuildRole \
            --region $AWS_REGION >/dev/null
    fi

    # Prepare source
    log_info "Preparando código fuente..."
    zip -r source.zip . -x "*.git*" "*.zip" >/dev/null
    
    # Create temporary S3 bucket
    BUCKET_NAME="tausestack-build-$(date +%s)"
    aws s3 mb s3://$BUCKET_NAME --region $AWS_REGION >/dev/null
    aws s3 cp source.zip s3://$BUCKET_NAME/source.zip >/dev/null
    
    # Start build
    log_info "Iniciando construcción..."
    BUILD_ID=$(aws codebuild start-build \
        --project-name tausestack-build \
        --source-override type=S3,location=$BUCKET_NAME/source.zip \
        --environment-variables-override \
            name=AWS_DEFAULT_REGION,value=$AWS_REGION \
            name=AWS_ACCOUNT_ID,value=$ACCOUNT_ID \
            name=IMAGE_REPO_NAME,value=tausestack \
            name=IMAGE_TAG,value=latest \
        --region $AWS_REGION \
        --query 'build.id' \
        --output text)
    
    log_info "Esperando construcción (ID: $BUILD_ID)..."
    
    # Wait for completion
    while true; do
        STATUS=$(aws codebuild batch-get-builds \
            --ids $BUILD_ID \
            --region $AWS_REGION \
            --query 'builds[0].buildStatus' \
            --output text)
        
        if [ "$STATUS" = "SUCCEEDED" ]; then
            log_success "Imagen construida exitosamente ✓"
            break
        elif [ "$STATUS" = "FAILED" ]; then
            log_error "Error en construcción"
            aws s3 rm s3://$BUCKET_NAME/source.zip >/dev/null 2>&1 || true
            aws s3 rb s3://$BUCKET_NAME >/dev/null 2>&1 || true
            rm -f source.zip buildspec.yml
            exit 1
        else
            echo -n "."
            sleep 10
        fi
    done
    
    # Cleanup
    aws s3 rm s3://$BUCKET_NAME/source.zip >/dev/null 2>&1 || true
    aws s3 rb s3://$BUCKET_NAME >/dev/null 2>&1 || true
    rm -f source.zip buildspec.yml
}

# Deploy stack
deploy_stack() {
    local CERT_ARN=$1
    local DB_PASSWORD=$2
    
    log_info "Desplegando CloudFormation..."
    
    if aws cloudformation describe-stacks --stack-name $STACK_NAME --region $AWS_REGION >/dev/null 2>&1; then
        log_info "Actualizando stack..."
        aws cloudformation update-stack \
            --stack-name $STACK_NAME \
            --template-body file://$TEMPLATE_FILE \
            --parameters \
                ParameterKey=DomainName,ParameterValue=$DOMAIN_NAME \
                ParameterKey=CertificateArn,ParameterValue=$CERT_ARN \
                ParameterKey=DBPassword,ParameterValue=$DB_PASSWORD \
            --capabilities CAPABILITY_IAM \
            --region $AWS_REGION
        
        aws cloudformation wait stack-update-complete \
            --stack-name $STACK_NAME \
            --region $AWS_REGION
    else
        log_info "Creando stack..."
        aws cloudformation create-stack \
            --stack-name $STACK_NAME \
            --template-body file://$TEMPLATE_FILE \
            --parameters \
                ParameterKey=DomainName,ParameterValue=$DOMAIN_NAME \
                ParameterKey=CertificateArn,ParameterValue=$CERT_ARN \
                ParameterKey=DBPassword,ParameterValue=$DB_PASSWORD \
            --capabilities CAPABILITY_IAM \
            --region $AWS_REGION >/dev/null
        
        aws cloudformation wait stack-create-complete \
            --stack-name $STACK_NAME \
            --region $AWS_REGION
    fi
    
    log_success "Stack desplegado ✓"
}

# Main function
main() {
    echo "🚀 TauseStack Deployment para ${DOMAIN_NAME}"
    echo "============================================"
    
    check_prerequisites
    
    DB_PASSWORD=$(generate_password)
    log_info "Contraseña generada"
    
    CERT_ARN=$(create_ssl_certificate)
    
    create_ecr_repository
    build_and_push_image
    
    deploy_stack $CERT_ARN $DB_PASSWORD
    
    echo
    log_success "🎉 Despliegue completado!"
    echo
    echo "🔐 Contraseña BD: $DB_PASSWORD"
    echo "🌐 Dominio: https://${DOMAIN_NAME}"
    echo "📱 App: https://app.${DOMAIN_NAME}"
    echo "🔧 API: https://api.${DOMAIN_NAME}"
}

main "$@" 