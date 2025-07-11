# Configuración de Dominios: TausePro + TauseStack

Esta guía explica cómo configurar los dominios para la arquitectura híbrida TausePro + TauseStack.

## 🏗️ Arquitectura de Dominios

### **Dominios TausePro**
- **tause.pro** → Landing page de TausePro
- **app.tause.pro** → Aplicación de marketing TausePro
- **api.tause.pro** → API proxy que conecta con TauseStack

### **Dominios TauseStack**
- **tausestack.dev** → Landing page de TauseStack
- **app.tausestack.dev** → Aplicación principal TauseStack
- **api.tausestack.dev** → API REST de TauseStack
- **admin.tausestack.dev** → Panel de administración

## 📋 Requisitos Previos

1. **AWS CLI** configurado
2. **Docker** instalado
3. **Dominios registrados** (tause.pro y tausestack.dev)
4. **Supabase** configurado

## 🚀 Configuración e Instalación

### **Paso 1: Configurar Variables de Entorno**

```bash
# Configuración de dominios
export TAUSEPRO_BASE_DOMAIN=tause.pro
export TAUSESTACK_BASE_DOMAIN=tausestack.dev
export ENVIRONMENT=production

# Configuración de Supabase
export SUPABASE_URL=https://your-project.supabase.co
export SUPABASE_ANON_KEY=your-anon-key

# Configuración de AWS
export AWS_REGION=us-east-1
export AWS_PROFILE=default
```

### **Paso 2: Configurar Hosted Zones en Route 53**

```bash
# Crear hosted zone para tause.pro
aws route53 create-hosted-zone \
    --name tause.pro \
    --caller-reference $(date +%s)

# Crear hosted zone para tausestack.dev (si no existe)
aws route53 create-hosted-zone \
    --name tausestack.dev \
    --caller-reference $(date +%s)
```

### **Paso 3: Desplegar TausePro**

```bash
# Hacer script ejecutable
chmod +x scripts/deploy-tausepro.sh

# Ejecutar deployment
./scripts/deploy-tausepro.sh
```

### **Paso 4: Configurar DNS en tu Proveedor**

Después del deployment, obtendrás un DNS del Load Balancer (ejemplo: `tausepro-alb-123456789.us-east-1.elb.amazonaws.com`).

Configura los siguientes registros DNS:

```
# Registros A (o ALIAS para AWS)
tause.pro           → tausepro-alb-123456789.us-east-1.elb.amazonaws.com
*.tause.pro         → tausepro-alb-123456789.us-east-1.elb.amazonaws.com
app.tause.pro       → tausepro-alb-123456789.us-east-1.elb.amazonaws.com
api.tause.pro       → tausepro-alb-123456789.us-east-1.elb.amazonaws.com
www.tause.pro       → tausepro-alb-123456789.us-east-1.elb.amazonaws.com
```

## 🔧 Configuración de Routing

### **DomainManager Multi-Dominio**

El sistema automáticamente detecta y enruta según el dominio:

```python
# Ejemplos de routing automático
host = "app.tause.pro"       → tenant_id = "tausepro_app"
host = "api.tausestack.dev"  → tenant_id = "api_service"
host = "tause.pro"           → tenant_id = "landing"
host = "admin.tausestack.dev"→ tenant_id = "admin_panel"
```

### **Configuración Manual**

```python
from tausestack.config.domains import domain_configuration

# Verificar configuración
config = domain_configuration.get_domain_config("app.tause.pro")
print(f"Tenant ID: {config.tenant_id}")  # Output: tausepro_app

# Obtener endpoint API
api_endpoint = domain_configuration.get_api_endpoint("app.tause.pro")
print(api_endpoint)  # Output: https://api.tausestack.dev
```

## 🐳 Configuración de Docker

### **Variables de Entorno para Contenedores**

```bash
# Landing Page (tause.pro)
NEXT_PUBLIC_DOMAIN=tause.pro
NEXT_PUBLIC_TAUSESTACK_API=https://api.tausestack.dev
NEXT_PUBLIC_APP_MODE=landing
NEXT_PUBLIC_BASE_URL=https://tause.pro

# Aplicación (app.tause.pro)
NEXT_PUBLIC_DOMAIN=tause.pro
NEXT_PUBLIC_TAUSESTACK_API=https://api.tausestack.dev
NEXT_PUBLIC_APP_MODE=app
NEXT_PUBLIC_BASE_URL=https://app.tause.pro
```

### **Construir Imágenes Docker**

```bash
# Landing Page
docker build -t tausepro:landing-latest \
    -f docker/Dockerfile.landing \
    --build-arg NEXT_PUBLIC_DOMAIN=tause.pro \
    --build-arg NEXT_PUBLIC_TAUSESTACK_API=https://api.tausestack.dev \
    .

# Aplicación
docker build -t tausepro:app-latest \
    -f docker/Dockerfile.app \
    --build-arg NEXT_PUBLIC_DOMAIN=tause.pro \
    --build-arg NEXT_PUBLIC_TAUSESTACK_API=https://api.tausestack.dev \
    .
```

## 🔒 Configuración de SSL

Los certificados SSL se generan automáticamente usando AWS Certificate Manager:

1. **Certificados creados**: `*.tause.pro` y `*.tausestack.dev`
2. **Validación automática**: DNS validation
3. **Renovación automática**: Gestionada por AWS

## 📊 Monitoreo

### **Health Checks**

```bash
# Verificar estado de los servicios
curl -f https://tause.pro/api/health
curl -f https://app.tause.pro/api/health
curl -f https://api.tausestack.dev/health
```

### **Logs**

```bash
# Ver logs de CloudFormation
aws cloudformation describe-stack-events \
    --stack-name tausepro-production

# Ver logs de ECS
aws logs tail /ecs/tausepro-production --follow
```

## 🛠️ Comandos Útiles

### **Verificar Configuración**

```bash
# Verificar DNS
dig tause.pro
dig app.tause.pro
dig api.tausestack.dev

# Verificar certificados SSL
aws acm list-certificates --region us-east-1

# Verificar hosted zones
aws route53 list-hosted-zones
```

### **Actualizar Stack**

```bash
# Actualizar solo infraestructura
aws cloudformation update-stack \
    --stack-name tausepro-production \
    --template-body file://tausestack/infrastructure/aws/tause-pro-production.yml

# Actualizar imágenes Docker
./scripts/deploy-tausepro.sh
```

### **Rollback**

```bash
# Rollback completo
aws cloudformation cancel-update-stack \
    --stack-name tausepro-production

# Rollback de servicio específico
aws ecs update-service \
    --cluster tausepro-production \
    --service tausepro-landing \
    --task-definition tausepro-landing:previous
```

## 🔍 Troubleshooting

### **Problema: DNS no resuelve**

```bash
# Verificar propagación DNS
nslookup tause.pro 8.8.8.8
nslookup app.tause.pro 8.8.8.8

# Verificar configuración Route 53
aws route53 list-resource-record-sets \
    --hosted-zone-id Z1234567890ABC
```

### **Problema: Certificado SSL no válido**

```bash
# Verificar estado del certificado
aws acm describe-certificate \
    --certificate-arn arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012

# Forzar renovación
aws acm request-certificate \
    --domain-name tause.pro \
    --subject-alternative-names "*.tause.pro" \
    --validation-method DNS
```

### **Problema: Servicio no responde**

```bash
# Verificar estado del servicio
aws ecs describe-services \
    --cluster tausepro-production \
    --services tausepro-landing

# Verificar logs
aws logs tail /ecs/tausepro-production/tausepro-landing --follow

# Reiniciar servicio
aws ecs update-service \
    --cluster tausepro-production \
    --service tausepro-landing \
    --force-new-deployment
```

## 📝 Notas Importantes

1. **Propagación DNS**: Puede tomar hasta 48 horas
2. **Certificados SSL**: Se generan automáticamente tras validación DNS
3. **Costos**: Revisa costos de ALB, ECS, y Route 53
4. **Backup**: Configura backup automático de RDS
5. **Monitoreo**: Configura alertas de CloudWatch

## 🎯 Próximos Pasos

1. **Configurar CI/CD** para deployments automáticos
2. **Implementar CDN** con CloudFront
3. **Configurar alertas** y monitoreo avanzado
4. **Optimizar costos** con auto-scaling
5. **Implementar backup** y disaster recovery

---

## 📞 Soporte

Si tienes problemas con la configuración, revisa:

1. **Logs de CloudFormation**
2. **Logs de ECS**
3. **Estado de Route 53**
4. **Certificados SSL**
5. **Configuración de seguridad**

Para soporte técnico, contacta al equipo de DevOps. 