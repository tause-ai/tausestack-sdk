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
