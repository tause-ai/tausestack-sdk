#!/bin/bash

# Domain Setup Script for TauseStack AWS Deployment
set -e

DOMAIN_NAME=${1:-"tausestack.dev"}
REGION=${2:-"us-east-1"}
STACK_NAME="tausestack-production"

echo "🌐 Setting up domain: $DOMAIN_NAME"

# Get Load Balancer DNS from CloudFormation
LOAD_BALANCER_DNS=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerDNS`].OutputValue' \
    --output text)

if [ -z "$LOAD_BALANCER_DNS" ]; then
    echo "❌ Error: Load Balancer DNS not found. Deploy the stack first."
    exit 1
fi

echo "📊 Load Balancer DNS: $LOAD_BALANCER_DNS"

# Create hosted zone if it doesn't exist
HOSTED_ZONE_ID=$(aws route53 list-hosted-zones-by-name \
    --dns-name $DOMAIN_NAME \
    --query 'HostedZones[0].Id' \
    --output text 2>/dev/null || echo "None")

if [ "$HOSTED_ZONE_ID" = "None" ] || [ -z "$HOSTED_ZONE_ID" ]; then
    echo "🆕 Creating hosted zone for $DOMAIN_NAME..."
    HOSTED_ZONE_ID=$(aws route53 create-hosted-zone \
        --name $DOMAIN_NAME \
        --caller-reference $(date +%s) \
        --query 'HostedZone.Id' \
        --output text)
    echo "✅ Hosted zone created: $HOSTED_ZONE_ID"
else
    echo "✅ Using existing hosted zone: $HOSTED_ZONE_ID"
fi

# Clean the hosted zone ID
HOSTED_ZONE_ID=$(echo $HOSTED_ZONE_ID | sed 's|/hostedzone/||')

# Create DNS records
cat > /tmp/dns-records.json << EOF
{
    "Changes": [
        {
            "Action": "UPSERT",
            "ResourceRecordSet": {
                "Name": "$DOMAIN_NAME",
                "Type": "A",
                "AliasTarget": {
                    "DNSName": "$LOAD_BALANCER_DNS",
                    "EvaluateTargetHealth": true,
                    "HostedZoneId": "Z35SXDOTRQ7X7K"
                }
            }
        },
        {
            "Action": "UPSERT",
            "ResourceRecordSet": {
                "Name": "api.$DOMAIN_NAME",
                "Type": "A",
                "AliasTarget": {
                    "DNSName": "$LOAD_BALANCER_DNS",
                    "EvaluateTargetHealth": true,
                    "HostedZoneId": "Z35SXDOTRQ7X7K"
                }
            }
        },
        {
            "Action": "UPSERT",
            "ResourceRecordSet": {
                "Name": "app.$DOMAIN_NAME",
                "Type": "A",
                "AliasTarget": {
                    "DNSName": "$LOAD_BALANCER_DNS",
                    "EvaluateTargetHealth": true,
                    "HostedZoneId": "Z35SXDOTRQ7X7K"
                }
            }
        }
    ]
}
EOF

# Apply DNS changes
echo "📝 Creating DNS records..."
CHANGE_ID=$(aws route53 change-resource-record-sets \
    --hosted-zone-id $HOSTED_ZONE_ID \
    --change-batch file:///tmp/dns-records.json \
    --query 'ChangeInfo.Id' \
    --output text)

echo "⏳ Waiting for DNS changes to propagate..."
aws route53 wait resource-record-sets-changed --id $CHANGE_ID

echo "✅ Domain setup completed!"
echo "🌐 Your application will be available at:"
echo "   - https://$DOMAIN_NAME"
echo "   - https://api.$DOMAIN_NAME"
echo "   - https://app.$DOMAIN_NAME"

# Show nameservers
echo "📋 Configure these nameservers with your domain registrar:"
aws route53 get-hosted-zone --id $HOSTED_ZONE_ID \
    --query 'DelegationSet.NameServers' \
    --output table

# Clean up
rm -f /tmp/dns-records.json 