#!/bin/bash

# TauseStack Deployment Script for tause.pro
# Deploys multi-tenant infrastructure to AWS

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN_NAME="tause.pro"
STACK_NAME="tausestack-prod"
REGION="us-east-1"  # Required for CloudFront certificates
ENVIRONMENT="production"

# Functions
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

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI not found. Please install it first."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured. Run 'aws configure' first."
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker not found. Please install it first."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

create_ecr_repository() {
    log_info "Creating ECR repository..."
    
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    ECR_REPO="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/tausestack"
    
    # Create repository if it doesn't exist
    if ! aws ecr describe-repositories --repository-names tausestack --region $REGION &> /dev/null; then
        aws ecr create-repository \
            --repository-name tausestack \
            --region $REGION \
            --image-scanning-configuration scanOnPush=true
        log_success "ECR repository created"
    else
        log_info "ECR repository already exists"
    fi
    
    echo $ECR_REPO
}

build_and_push_image() {
    log_info "Building and pushing Docker image..."
    
    ECR_REPO=$1
    
    # Get login token
    aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_REPO
    
    # Build image
    docker build -t tausestack:latest .
    docker tag tausestack:latest $ECR_REPO:latest
    
    # Push image
    docker push $ECR_REPO:latest
    
    log_success "Docker image built and pushed"
}

request_certificate() {
    log_info "Requesting SSL certificate for *.${DOMAIN_NAME}..."
    
    # Check if certificate already exists
    CERT_ARN=$(aws acm list-certificates \
        --region $REGION \
        --query "CertificateSummaryList[?DomainName=='*.${DOMAIN_NAME}'].CertificateArn" \
        --output text)
    
    if [ -z "$CERT_ARN" ]; then
        # Request new certificate
        CERT_ARN=$(aws acm request-certificate \
            --domain-name "*.${DOMAIN_NAME}" \
            --subject-alternative-names "${DOMAIN_NAME}" \
            --validation-method DNS \
            --region $REGION \
            --query CertificateArn \
            --output text)
        
        log_warning "Certificate requested: $CERT_ARN"
        log_warning "Please validate the certificate via DNS before continuing deployment"
        log_warning "Check AWS ACM console for validation instructions"
        
        read -p "Press Enter when certificate is validated..."
    else
        log_info "Using existing certificate: $CERT_ARN"
    fi
    
    echo $CERT_ARN
}

generate_db_password() {
    # Generate secure random password
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

deploy_infrastructure() {
    log_info "Deploying CloudFormation stack..."
    
    CERT_ARN=$1
    DB_PASSWORD=$(generate_db_password)
    
    # Deploy stack
    aws cloudformation deploy \
        --template-file infrastructure/aws/tause-pro-architecture.yml \
        --stack-name $STACK_NAME \
        --parameter-overrides \
            Environment=$ENVIRONMENT \
            DomainName=$DOMAIN_NAME \
            CertificateArn=$CERT_ARN \
            DBPassword=$DB_PASSWORD \
        --capabilities CAPABILITY_IAM \
        --region $REGION \
        --no-fail-on-empty-changeset
    
    if [ $? -eq 0 ]; then
        log_success "Infrastructure deployed successfully"
    else
        log_error "Infrastructure deployment failed"
        exit 1
    fi
}

get_outputs() {
    log_info "Getting stack outputs..."
    
    aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION \
        --query 'Stacks[0].Outputs' \
        --output table
}

update_dns() {
    log_info "DNS configuration:"
    log_info "1. Update your domain registrar to use these nameservers:"
    
    HOSTED_ZONE_ID=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`HostedZoneId`].OutputValue' \
        --output text)
    
    aws route53 get-hosted-zone \
        --id $HOSTED_ZONE_ID \
        --query 'DelegationSet.NameServers' \
        --output table
    
    log_info "2. After DNS propagation, your application will be available at:"
    log_info "   - https://${DOMAIN_NAME} (main site)"
    log_info "   - https://app.${DOMAIN_NAME} (default tenant)"
    log_info "   - https://{tenant}.${DOMAIN_NAME} (tenant-specific)"
}

setup_monitoring() {
    log_info "Setting up monitoring and alerts..."
    
    # Create CloudWatch dashboard
    cat > /tmp/dashboard.json << EOF
{
    "widgets": [
        {
            "type": "metric",
            "properties": {
                "metrics": [
                    [ "AWS/ECS", "CPUUtilization", "ServiceName", "${STACK_NAME}-service" ],
                    [ ".", "MemoryUtilization", ".", "." ]
                ],
                "period": 300,
                "stat": "Average",
                "region": "${REGION}",
                "title": "ECS Service Metrics"
            }
        },
        {
            "type": "metric",
            "properties": {
                "metrics": [
                    [ "AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", "${STACK_NAME}-db" ],
                    [ ".", "DatabaseConnections", ".", "." ]
                ],
                "period": 300,
                "stat": "Average",
                "region": "${REGION}",
                "title": "RDS Metrics"
            }
        }
    ]
}
EOF
    
    aws cloudwatch put-dashboard \
        --dashboard-name "${STACK_NAME}-dashboard" \
        --dashboard-body file:///tmp/dashboard.json \
        --region $REGION
    
    log_success "Monitoring dashboard created"
}

main() {
    echo "🚀 TauseStack Deployment for ${DOMAIN_NAME}"
    echo "================================================"
    
    # Check prerequisites
    check_prerequisites
    
    # Create ECR repository and build image
    ECR_REPO=$(create_ecr_repository)
    build_and_push_image $ECR_REPO
    
    # Request SSL certificate
    CERT_ARN=$(request_certificate)
    
    # Deploy infrastructure
    deploy_infrastructure $CERT_ARN
    
    # Get outputs
    get_outputs
    
    # Setup monitoring
    setup_monitoring
    
    # DNS instructions
    update_dns
    
    echo ""
    log_success "🎉 Deployment completed successfully!"
    echo ""
    log_info "Next steps:"
    log_info "1. Update your domain's nameservers as shown above"
    log_info "2. Wait for DNS propagation (up to 48 hours)"
    log_info "3. Test your application at https://app.${DOMAIN_NAME}"
    log_info "4. Configure your first tenant via the admin panel"
    echo ""
    log_info "Useful commands:"
    log_info "  - View logs: aws logs tail /ecs/${STACK_NAME} --follow"
    log_info "  - Scale service: aws ecs update-service --cluster ${STACK_NAME}-cluster --service ${STACK_NAME}-service --desired-count 4"
    log_info "  - Monitor: https://console.aws.amazon.com/cloudwatch/home?region=${REGION}#dashboards:name=${STACK_NAME}-dashboard"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --domain)
            DOMAIN_NAME="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [--domain DOMAIN] [--region REGION] [--environment ENV]"
            echo ""
            echo "Options:"
            echo "  --domain      Domain name (default: tause.pro)"
            echo "  --region      AWS region (default: us-east-1)"
            echo "  --environment Environment (default: production)"
            echo "  --help        Show this help message"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Update stack name based on environment
if [ "$ENVIRONMENT" != "production" ]; then
    STACK_NAME="tausestack-${ENVIRONMENT}"
fi

# Run main function
main 