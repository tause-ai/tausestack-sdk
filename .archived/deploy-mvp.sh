#!/bin/bash

# TauseStack MVP Deployment Script
# Minimal resources for demo/testing

set -e

# Set AWS environment variables
export AWS_REGION="us-east-1"
export AWS_PAGER=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
STACK_NAME="tausestack-mvp"
REGION="us-east-1"
DOMAIN_NAME="tausestack.dev"

echo -e "${BLUE}🚀 TauseStack MVP Deployment${NC}"
echo -e "${BLUE}=============================${NC}"
echo -e "${BLUE}Stack: $STACK_NAME${NC}"
echo -e "${BLUE}Domain: $DOMAIN_NAME${NC}"
echo -e "${BLUE}Region: $REGION${NC}"

# Check prerequisites
echo -e "\n${YELLOW}📋 Checking prerequisites...${NC}"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found. Please install it first.${NC}"
    exit 1
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found. Please install it first.${NC}"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS credentials not configured. Run 'aws configure' first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites OK${NC}"

# Get AWS Account ID
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✅ AWS Account ID: $AWS_ACCOUNT_ID${NC}"

# Step 1: Build and push Docker image
echo -e "\n${YELLOW}🐳 Step 1: Building and pushing Docker image...${NC}"

# Login to ECR
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

# Create ECR repository if it doesn't exist
echo -e "${BLUE}Creating ECR repository...${NC}"
aws ecr describe-repositories --repository-names $STACK_NAME --region $REGION 2>/dev/null || \
aws ecr create-repository --repository-name $STACK_NAME --region $REGION

# Build image
echo -e "${BLUE}Building Docker image...${NC}"
docker build -t $STACK_NAME:latest .

# Tag and push
echo -e "${BLUE}Pushing to ECR...${NC}"
docker tag $STACK_NAME:latest $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$STACK_NAME:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$STACK_NAME:latest

echo -e "${GREEN}✅ Docker image built and pushed${NC}"

# Step 2: Deploy CloudFormation stack
echo -e "\n${YELLOW}☁️ Step 2: Deploying CloudFormation stack...${NC}"

# Check if hosted zone exists
HOSTED_ZONE_ID=$(aws route53 list-hosted-zones-by-name \
    --dns-name $DOMAIN_NAME \
    --query 'HostedZones[0].Id' \
    --output text 2>/dev/null | sed 's|/hostedzone/||' || echo "None")

if [ "$HOSTED_ZONE_ID" = "None" ] || [ -z "$HOSTED_ZONE_ID" ]; then
    echo -e "${YELLOW}⚠️ No hosted zone found for $DOMAIN_NAME${NC}"
    echo -e "${YELLOW}Creating hosted zone...${NC}"
    
    # The CloudFormation template will create the hosted zone
    USE_EXISTING_ZONE="false"
else
    echo -e "${GREEN}✅ Found existing hosted zone: $HOSTED_ZONE_ID${NC}"
    USE_EXISTING_ZONE="true"
fi

# Deploy stack
echo -e "${BLUE}Deploying CloudFormation stack...${NC}"
aws cloudformation deploy \
    --template-file infrastructure/aws/mvp-stack.yml \
    --stack-name $STACK_NAME \
    --parameter-overrides \
        DomainName=$DOMAIN_NAME \
    --capabilities CAPABILITY_IAM \
    --region $REGION \
    --no-fail-on-empty-changeset

echo -e "${GREEN}✅ CloudFormation stack deployed${NC}"

# Step 3: Wait for certificate validation
echo -e "\n${YELLOW}🔐 Step 3: Waiting for SSL certificate validation...${NC}"

# Get certificate ARN
CERT_ARN=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`CertificateArn`].OutputValue' \
    --output text 2>/dev/null || echo "")

if [ -n "$CERT_ARN" ]; then
    echo -e "${BLUE}Certificate ARN: $CERT_ARN${NC}"
    echo -e "${YELLOW}⏳ Waiting for certificate validation (this may take a few minutes)...${NC}"
    
    # Wait for certificate validation (with timeout)
    timeout 600 aws acm wait certificate-validated --certificate-arn $CERT_ARN --region $REGION || {
        echo -e "${YELLOW}⚠️ Certificate validation timeout. Please check DNS records manually.${NC}"
    }
else
    echo -e "${YELLOW}⚠️ Certificate ARN not found. Continuing...${NC}"
fi

# Step 4: Update ECS service to pull new image
echo -e "\n${YELLOW}🔄 Step 4: Updating ECS service...${NC}"

# Get cluster and service names
CLUSTER_NAME=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`ClusterName`].OutputValue' \
    --output text)

SERVICE_NAME=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`ServiceName`].OutputValue' \
    --output text)

if [ -n "$CLUSTER_NAME" ] && [ -n "$SERVICE_NAME" ]; then
    echo -e "${BLUE}Updating ECS service...${NC}"
    aws ecs update-service \
        --cluster $CLUSTER_NAME \
        --service $SERVICE_NAME \
        --force-new-deployment \
        --region $REGION > /dev/null
    
    echo -e "${YELLOW}⏳ Waiting for service to stabilize...${NC}"
    aws ecs wait services-stable \
        --cluster $CLUSTER_NAME \
        --services $SERVICE_NAME \
        --region $REGION
    
    echo -e "${GREEN}✅ ECS service updated${NC}"
else
    echo -e "${YELLOW}⚠️ ECS service not found. Skipping update.${NC}"
fi

# Step 5: Get deployment information
echo -e "\n${YELLOW}📊 Step 5: Getting deployment information...${NC}"

# Get stack outputs
LOAD_BALANCER_URL=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerURL`].OutputValue' \
    --output text)

APP_URL=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`ApplicationURL`].OutputValue' \
    --output text)

API_URL=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`APIURL`].OutputValue' \
    --output text)

# Step 6: Health checks
echo -e "\n${YELLOW}🔍 Step 6: Running health checks...${NC}"

# Wait for DNS propagation
echo -e "${BLUE}Waiting for DNS propagation...${NC}"
sleep 60

# Test endpoints
endpoints=(
    "$APP_URL"
    "$API_URL"
)

for endpoint in "${endpoints[@]}"; do
    if [ -n "$endpoint" ]; then
        echo -e "${BLUE}Testing $endpoint...${NC}"
        for i in {1..5}; do
            if curl -f -s -k "$endpoint" > /dev/null 2>&1; then
                echo -e "${GREEN}✅ $endpoint is responding${NC}"
                break
            fi
            if [ $i -eq 5 ]; then
                echo -e "${YELLOW}⚠️ $endpoint not responding yet${NC}"
            else
                echo -e "${YELLOW}⏳ Waiting for $endpoint... (attempt $i/5)${NC}"
                sleep 30
            fi
        done
    fi
done

# Step 7: Display results
echo -e "\n${GREEN}🎉 MVP DEPLOYMENT COMPLETED!${NC}"
echo -e "${GREEN}============================${NC}"

echo -e "\n${BLUE}📊 Deployment Summary:${NC}"
echo -e "${BLUE}├─ Stack Name:${NC} $STACK_NAME"
echo -e "${BLUE}├─ Region:${NC} $REGION"
echo -e "${BLUE}├─ Domain:${NC} $DOMAIN_NAME"
echo -e "${BLUE}└─ Load Balancer:${NC} $LOAD_BALANCER_URL"

echo -e "\n${BLUE}🌐 Access URLs:${NC}"
if [ -n "$APP_URL" ]; then
    echo -e "${BLUE}├─ Application:${NC} $APP_URL"
fi
if [ -n "$API_URL" ]; then
    echo -e "${BLUE}└─ API:${NC} $API_URL"
fi

echo -e "\n${BLUE}🛠️ Management Commands:${NC}"
echo -e "${BLUE}├─ View logs:${NC} aws logs tail /ecs/$STACK_NAME --follow --region $REGION"
echo -e "${BLUE}├─ Scale service:${NC} aws ecs update-service --cluster $CLUSTER_NAME --service $SERVICE_NAME --desired-count N"
echo -e "${BLUE}└─ Delete stack:${NC} aws cloudformation delete-stack --stack-name $STACK_NAME --region $REGION"

echo -e "\n${YELLOW}📝 Next Steps:${NC}"
echo -e "${YELLOW}1.${NC} Test the application at $APP_URL"
echo -e "${YELLOW}2.${NC} Configure Supabase with production domain"
echo -e "${YELLOW}3.${NC} Monitor logs and performance"
echo -e "${YELLOW}4.${NC} Scale resources as needed"

echo -e "\n${BLUE}💰 Estimated Cost:${NC} ~$20-30/month"
echo -e "${GREEN}✅ TauseStack MVP is now LIVE!${NC}" 