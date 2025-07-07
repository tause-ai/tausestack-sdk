# 🚀 TauseStack SDK - Guía Completa de Deployment en AWS

## 📋 **RESUMEN EJECUTIVO**

Esta guía documenta el proceso completo para desplegar TauseStack SDK en AWS utilizando ECS Fargate, incluyendo frontend Next.js y backend FastAPI con autenticación Supabase.

**🎯 Estado Actual**: ✅ **FUNCIONANDO EN PRODUCCIÓN**
- **URL Principal**: https://tausestack.dev/
- **API Gateway**: https://tausestack.dev/api
- **Infraestructura**: AWS ECS Fargate + Application Load Balancer
- **Autenticación**: Supabase Auth integrada

---

## 🏗️ **ARQUITECTURA DESPLEGADA**

### **Componentes Principales**
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   CloudFront    │    │  Application     │    │   ECS Fargate   │
│   (Opcional)    │────│  Load Balancer   │────│   Container     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                │                        │
                       ┌──────────────────┐    ┌─────────────────┐
                       │   Route 53 DNS   │    │   Supabase      │
                       │   tausestack.dev  │    │   Auth + DB     │
                       └──────────────────┘    └─────────────────┘
```

### **Stack de CloudFormation**
- **Nombre**: `tausestack-final-fixed`
- **Región**: `us-east-1`
- **Template**: `tausestack/infrastructure/aws/mvp-stack.yml`

---

## 🔧 **CONFIGURACIÓN ACTUAL**

### **1. Repositorio ECR**
```bash
Repository: 349622182214.dkr.ecr.us-east-1.amazonaws.com/tausestack-production
Tag: latest
Arquitectura: linux/amd64
```

### **2. ECS Cluster**
```bash
Cluster: tausestack-final-fixed-cluster
Service: tausestack-final-fixed-service
Task Definition: tausestack-final-fixed-task:2
Launch Type: FARGATE
```

### **3. Configuración de Supabase**
```bash
URL: https://vjoxmprmcbkmhwmbniaz.supabase.co
Anon Key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZqb3htcHJtY2JrbWh3bWJuaWF6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE1NzM4NzQsImV4cCI6MjA2NzE0OTg3NH0.bY4FrlKtDK2TnMt7hOC5_KpIuoHwqJLOYkB-bWs_Wd8
JWT Secret: [Configurado en el backend]
```

### **4. Dominio y SSL**
```bash
Dominio: tausestack.dev
Certificado SSL: arn:aws:acm:us-east-1:349622182214:certificate/f190e0dd-5ce9-4702-85cf-4d3ce5faba79
Hosted Zone: Z057501928Q0UDHS32I3I
```

---

## 🚀 **PROCESO DE DEPLOYMENT**

### **Prerequisitos**
1. **AWS CLI configurado** con credenciales de `tausestack-deploy`
2. **Docker** con soporte para buildx (multi-arquitectura)
3. **Node.js 18+** para construir el frontend
4. **Python 3.11+** para desarrollo local

### **Variables de Entorno Requeridas**
```bash
export AWS_REGION="us-east-1"
export AWS_ACCOUNT_ID="349622182214"
export AWS_PAGER=""  # IMPORTANTE: Evita problemas con el shell
```

### **Pasos de Deployment**

#### **1. Preparar el Frontend**
```bash
cd frontend
npm install
npm run build
cd ..
```

#### **2. Construir la Imagen Docker**
```bash
# CRÍTICO: Usar linux/amd64 para compatibilidad con ECS
docker buildx build --platform linux/amd64 -t tausestack-production:latest .
```

#### **3. Subir a ECR**
```bash
# Login a ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Tag y push
docker tag tausestack-production:latest \
  $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/tausestack-production:latest

docker push $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/tausestack-production:latest
```

#### **4. Deployment del Servicio**
```bash
# Forzar nuevo deployment
aws ecs update-service \
  --cluster tausestack-final-fixed-cluster \
  --service tausestack-final-fixed-service \
  --force-new-deployment \
  --region us-east-1
```

#### **5. Verificación**
```bash
# Health check
curl -I https://tausestack.dev/

# API Gateway
curl -I https://tausestack.dev/api

# Logs del servicio
aws logs tail /ecs/tausestack-final-fixed --region us-east-1 --since 5m
```

---

## 🔒 **CONFIGURACIÓN DE SEGURIDAD**

### **Rutas Protegidas**
- `/admin/*` - Requiere rol "admin"
- `/metrics` - Requiere rol "admin" o "monitor"
- `/dashboard/*` - Requiere autenticación

### **CORS Configuration**
```python
allow_origins=[
    "https://tausestack.dev",
    "http://localhost:3000",
    "http://localhost:9001"
]
```

### **Trusted Hosts**
```python
allowed_hosts=[
    "tausestack.dev",
    "localhost",
    "127.0.0.1"
]
```

---

## 🐛 **TROUBLESHOOTING**

### **Problemas Comunes y Soluciones**

#### **1. Error de Arquitectura**
```
Error: image Manifest does not contain descriptor matching platform 'linux/amd64'
```
**Solución**: Usar `--platform linux/amd64` en docker buildx build

#### **2. Error de Permisos**
```
PermissionError: [Errno 13] Permission denied: '.tausestack_storage'
```
**Solución**: Verificar que el Dockerfile incluya `chown -R tausestack:tausestack /app`

#### **3. Error de Dependencias**
```
ImportError: email-validator is not installed
```
**Solución**: Verificar que `email-validator==2.1.0` esté en requirements.txt

#### **4. Problemas con AWS CLI**
```
head: |: No such file or directory
```
**Solución**: Ejecutar `export AWS_PAGER=""`

### **Comandos de Diagnóstico**
```bash
# Estado del servicio
aws ecs describe-services \
  --cluster tausestack-final-fixed-cluster \
  --services tausestack-final-fixed-service \
  --region us-east-1

# Logs en tiempo real
aws logs tail /ecs/tausestack-final-fixed \
  --region us-east-1 --follow

# Estado del stack
aws cloudformation describe-stacks \
  --stack-name tausestack-final-fixed \
  --region us-east-1
```

---

## 📊 **MONITOREO Y LOGS**

### **CloudWatch Logs**
- **Log Group**: `/ecs/tausestack-final-fixed`
- **Retention**: 7 días
- **Streams**: Uno por tarea ECS

### **Health Checks**
- **ECS Health Check**: `curl -f http://localhost:8000/health`
- **ALB Health Check**: `/health` (Puerto 8000)
- **Intervalo**: 60 segundos
- **Timeout**: 10 segundos

### **Métricas Clave**
- **CPU Utilization**: Target < 70%
- **Memory Utilization**: Target < 80%
- **Response Time**: Target < 500ms
- **Error Rate**: Target < 1%

---

## 💰 **COSTOS ESTIMADOS**

### **Recursos AWS (us-east-1)**
- **ECS Fargate**: ~$15-25/mes (0.5 vCPU, 1GB RAM)
- **Application Load Balancer**: ~$16/mes
- **Route 53**: ~$0.50/mes
- **ECR Storage**: ~$1-2/mes
- **CloudWatch Logs**: ~$1-3/mes

**Total Estimado**: ~$35-50/mes

---

## 🔄 **ACTUALIZACIONES FUTURAS**

### **Para Nuevas Versiones**
1. Actualizar código fuente
2. Construir nueva imagen Docker
3. Subir a ECR con tag específico
4. Actualizar Task Definition
5. Deployment del servicio

### **Para Cambios de Infraestructura**
1. Modificar `mvp-stack.yml`
2. Ejecutar `aws cloudformation update-stack`
3. Monitorear el progreso
4. Verificar funcionamiento

---

## 📞 **SOPORTE**

### **Información de Contacto**
- **Stack Name**: `tausestack-final-fixed`
- **AWS Account**: `349622182214`
- **Region**: `us-east-1`
- **Domain**: `tausestack.dev`

### **Recursos Útiles**
- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [Supabase Documentation](https://supabase.com/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)

---

**Última Actualización**: 7 de Julio, 2025
**Estado**: ✅ Producción Estable
**Versión**: 1.0.0 