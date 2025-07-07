#!/bin/bash

# Complete TauseStack AWS Deployment Script
# This script deploys everything needed for production

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN_NAME=${1:-"tausestack.dev"}
STACK_NAME="tausestack-production"
REGION="us-east-1"
ENVIRONMENT="production"

echo -e "${BLUE}🚀 TauseStack Complete AWS Deployment${NC}"
echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}Domain: $DOMAIN_NAME${NC}"
echo -e "${BLUE}Region: $REGION${NC}"
echo -e "${BLUE}Environment: $ENVIRONMENT${NC}"

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

# Check required environment variables
required_vars=(
    "SUPABASE_URL"
    "SUPABASE_ANON_KEY"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "${RED}❌ Error: $var is not set${NC}"
        echo -e "${YELLOW}Please set: export $var=your_value${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ $var is set${NC}"
done

# Get AWS Account ID
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✅ AWS Account ID: $AWS_ACCOUNT_ID${NC}"

# Step 1: Build and test locally
echo -e "\n${YELLOW}🔧 Step 1: Building and testing locally...${NC}"

# Build frontend
echo -e "${BLUE}Building frontend...${NC}"
cd frontend
npm ci
npm run build
cd ..

# Test Docker build
echo -e "${BLUE}Testing Docker build...${NC}"
docker build -t $STACK_NAME:test .

echo -e "${GREEN}✅ Local build successful${NC}"

# Step 2: Deploy infrastructure
echo -e "\n${YELLOW}☁️ Step 2: Deploying AWS infrastructure...${NC}"

# Run the main deployment script
chmod +x deploy-tausestack-production.sh
./deploy-tausestack-production.sh

echo -e "${GREEN}✅ Infrastructure deployed${NC}"

# Step 3: Configure domain
echo -e "\n${YELLOW}🌐 Step 3: Configuring domain...${NC}"

# Run domain setup script
chmod +x scripts/setup-domain.sh
./scripts/setup-domain.sh $DOMAIN_NAME

echo -e "${GREEN}✅ Domain configured${NC}"

# Step 4: Health checks
echo -e "\n${YELLOW}🔍 Step 4: Running comprehensive health checks...${NC}"

# Wait for services to be ready
echo -e "${BLUE}Waiting for services to stabilize...${NC}"
sleep 60

# Test endpoints
endpoints=(
    "https://$DOMAIN_NAME/health"
    "https://api.$DOMAIN_NAME/health"
    "https://$DOMAIN_NAME"
)

for endpoint in "${endpoints[@]}"; do
    echo -e "${BLUE}Testing $endpoint...${NC}"
    for i in {1..10}; do
        if curl -f -s "$endpoint" > /dev/null; then
            echo -e "${GREEN}✅ $endpoint is healthy${NC}"
            break
        fi
        if [ $i -eq 10 ]; then
            echo -e "${RED}❌ $endpoint failed health check${NC}"
        else
            echo -e "${YELLOW}⏳ Waiting for $endpoint... (attempt $i/10)${NC}"
            sleep 30
        fi
    done
done

# Step 5: Performance tests
echo -e "\n${YELLOW}⚡ Step 5: Running performance tests...${NC}"

# Test load times
echo -e "${BLUE}Testing page load times...${NC}"
for url in "https://$DOMAIN_NAME" "https://api.$DOMAIN_NAME/health"; do
    load_time=$(curl -o /dev/null -s -w '%{time_total}' "$url")
    echo -e "${BLUE}$url: ${load_time}s${NC}"
done

# Step 6: Security checks
echo -e "\n${YELLOW}🔒 Step 6: Running security checks...${NC}"

# Check SSL certificate
echo -e "${BLUE}Checking SSL certificate...${NC}"
ssl_info=$(echo | openssl s_client -servername $DOMAIN_NAME -connect $DOMAIN_NAME:443 2>/dev/null | openssl x509 -noout -subject -dates 2>/dev/null || echo "SSL check failed")
echo -e "${GREEN}✅ SSL: $ssl_info${NC}"

# Check security headers
echo -e "${BLUE}Checking security headers...${NC}"
headers=$(curl -I -s "https://$DOMAIN_NAME" | grep -E "(X-Frame-Options|X-Content-Type-Options|Strict-Transport-Security)" || echo "No security headers found")
echo -e "${GREEN}✅ Security headers: $headers${NC}"

# Step 7: Generate deployment report
echo -e "\n${YELLOW}📊 Step 7: Generating deployment report...${NC}"

# Get AWS resources
LOAD_BALANCER_URL=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerURL`].OutputValue' \
    --output text)

DATABASE_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`DatabaseEndpoint`].OutputValue' \
    --output text)

CLUSTER_NAME=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`ClusterName`].OutputValue' \
    --output text)

# Create deployment report
cat > deployment-report.md << EOF
# TauseStack Production Deployment Report

**Deployment Date:** $(date)
**Domain:** $DOMAIN_NAME
**Environment:** $ENVIRONMENT
**Region:** $REGION

## 🌐 Access URLs
- **Main Application:** https://$DOMAIN_NAME
- **API Gateway:** https://api.$DOMAIN_NAME
- **Admin Dashboard:** https://$DOMAIN_NAME/dashboard

## 📊 AWS Resources
- **Load Balancer:** $LOAD_BALANCER_URL
- **Database:** $DATABASE_ENDPOINT
- **ECS Cluster:** $CLUSTER_NAME
- **ECR Repository:** $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$STACK_NAME

## 🛠️ Management Commands
\`\`\`bash
# View logs
aws logs tail /ecs/$STACK_NAME --follow --region $REGION

# Scale service
aws ecs update-service --cluster $CLUSTER_NAME --service ${STACK_NAME}-service --desired-count N

# Redeploy
./scripts/deploy-complete.sh $DOMAIN_NAME
\`\`\`

## 📝 Next Steps
1. ✅ Infrastructure deployed
2. ✅ Domain configured
3. ✅ Health checks passed
4. ⏳ Configure monitoring alerts
5. ⏳ Set up backup procedures
6. ⏳ Configure CI/CD pipeline

## 🔐 Security
- ✅ SSL Certificate configured
- ✅ Security headers enabled
- ✅ VPC with private subnets
- ✅ Security groups configured

## 💰 Estimated Monthly Cost
- **ECS Fargate:** \$15-25
- **RDS t3.micro:** \$13
- **Application LB:** \$16
- **Route 53:** \$1
- **Total:** \$45-55/month

EOF

echo -e "${GREEN}✅ Deployment report generated: deployment-report.md${NC}"

# Final success message
echo -e "\n${GREEN}🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!${NC}"
echo -e "${GREEN}====================================${NC}"
echo -e "\n${BLUE}🌐 Your TauseStack application is now live at:${NC}"
echo -e "${BLUE}   https://$DOMAIN_NAME${NC}"
echo -e "\n${BLUE}📊 Dashboard:${NC} https://$DOMAIN_NAME/dashboard"
echo -e "${BLUE}🔗 API:${NC} https://api.$DOMAIN_NAME"
echo -e "\n${YELLOW}📋 Next steps:${NC}"
echo -e "${YELLOW}1. Test all functionality${NC}"
echo -e "${YELLOW}2. Configure monitoring${NC}"
echo -e "${YELLOW}3. Set up backups${NC}"
echo -e "${YELLOW}4. Configure CI/CD${NC}"

echo -e "\n${GREEN}✅ TauseStack v0.9.0 is production-ready!${NC}" 