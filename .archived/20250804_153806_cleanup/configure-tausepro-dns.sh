#!/bin/bash

# Script para configurar DNS de tause.pro apuntando al Load Balancer existente de TauseStack
# Ejecutar: ./configure-tausepro-dns.sh

set -e

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuración
DOMAIN="tause.pro"
REGION="us-east-1"
LOAD_BALANCER_DNS="tausestack-final-fixed-alb-334527200.us-east-1.elb.amazonaws.com"
LOAD_BALANCER_HOSTED_ZONE_ID="Z35SXDOTRQ7X7K"  # Hosted Zone ID para ALB en us-east-1

echo -e "${BLUE}🌐 Configurando DNS para TausePro...${NC}"

# Obtener Hosted Zone ID para tause.pro
echo -e "${BLUE}Buscando hosted zone para $DOMAIN...${NC}"
HOSTED_ZONE_ID=$(aws route53 list-hosted-zones-by-name \
    --dns-name $DOMAIN \
    --query 'HostedZones[0].Id' \
    --output text 2>/dev/null)

if [ "$HOSTED_ZONE_ID" = "None" ] || [ -z "$HOSTED_ZONE_ID" ]; then
    echo -e "${RED}❌ No se encontró hosted zone para $DOMAIN${NC}"
    echo -e "${BLUE}Debes crear una hosted zone para $DOMAIN en Route 53 primero${NC}"
    exit 1
fi

# Limpiar el hosted zone ID
HOSTED_ZONE_ID=$(echo $HOSTED_ZONE_ID | sed 's|/hostedzone/||')

echo -e "${GREEN}✅ Hosted zone encontrada: $HOSTED_ZONE_ID${NC}"

# Crear registros DNS
echo -e "${BLUE}Creando registros DNS...${NC}"

# Crear archivo JSON temporal para los registros
cat > /tmp/tausepro-dns-records.json << EOF
{
    "Comment": "Configuración DNS para TausePro -> TauseStack Load Balancer",
    "Changes": [
        {
            "Action": "UPSERT",
            "ResourceRecordSet": {
                "Name": "$DOMAIN",
                "Type": "A",
                "AliasTarget": {
                    "DNSName": "$LOAD_BALANCER_DNS",
                    "HostedZoneId": "$LOAD_BALANCER_HOSTED_ZONE_ID",
                    "EvaluateTargetHealth": false
                }
            }
        },
        {
            "Action": "UPSERT",
            "ResourceRecordSet": {
                "Name": "app.$DOMAIN",
                "Type": "A",
                "AliasTarget": {
                    "DNSName": "$LOAD_BALANCER_DNS",
                    "HostedZoneId": "$LOAD_BALANCER_HOSTED_ZONE_ID",
                    "EvaluateTargetHealth": false
                }
            }
        },
        {
            "Action": "UPSERT",
            "ResourceRecordSet": {
                "Name": "api.$DOMAIN",
                "Type": "A",
                "AliasTarget": {
                    "DNSName": "$LOAD_BALANCER_DNS",
                    "HostedZoneId": "$LOAD_BALANCER_HOSTED_ZONE_ID",
                    "EvaluateTargetHealth": false
                }
            }
        },
        {
            "Action": "UPSERT",
            "ResourceRecordSet": {
                "Name": "www.$DOMAIN",
                "Type": "A",
                "AliasTarget": {
                    "DNSName": "$LOAD_BALANCER_DNS",
                    "HostedZoneId": "$LOAD_BALANCER_HOSTED_ZONE_ID",
                    "EvaluateTargetHealth": false
                }
            }
        }
    ]
}
EOF

# Ejecutar cambios DNS
echo -e "${BLUE}Aplicando cambios DNS...${NC}"
CHANGE_ID=$(aws route53 change-resource-record-sets \
    --hosted-zone-id $HOSTED_ZONE_ID \
    --change-batch file:///tmp/tausepro-dns-records.json \
    --query 'ChangeInfo.Id' \
    --output text)

echo -e "${GREEN}✅ Cambios DNS aplicados. Change ID: $CHANGE_ID${NC}"

# Verificar propagación
echo -e "${BLUE}Verificando propagación DNS...${NC}"
aws route53 wait resource-record-sets-changed --id $CHANGE_ID
echo -e "${GREEN}✅ Propagación DNS completada${NC}"

# Limpiar archivos temporales
rm -f /tmp/tausepro-dns-records.json

echo -e "${GREEN}🎉 ¡Configuración DNS completada!${NC}"
echo -e "${BLUE}Los siguientes dominios ahora apuntan al Load Balancer de TauseStack:${NC}"
echo -e "  • https://tause.pro"
echo -e "  • https://app.tause.pro"
echo -e "  • https://api.tause.pro"
echo -e "  • https://www.tause.pro"
echo ""
echo -e "${BLUE}Nota: La propagación DNS puede tardar hasta 48 horas en completarse globalmente.${NC}"
echo -e "${BLUE}Para verificar localmente, usa: dig tause.pro${NC}" 