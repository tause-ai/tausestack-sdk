# 🚀 Guía de Despliegue Económico - TauseStack

## 🎯 **Configuración AWS Súper Económica para tause.pro**

**Costo total: ~$35-45/mes** para una plataforma multi-tenant completa con todos los subdominios bajo control.

---

## 🌐 **Arquitectura de Subdominios Completa**

```
🌐 tause.pro
├── 🏠 tause.pro                    - Landing page principal
├── 📱 app.tause.pro                - Aplicación principal (tenant default)
├── 🔧 api.tause.pro                - API REST endpoints
├── ⚙️ admin.tause.pro              - Panel de administración
├── 📚 docs.tause.pro               - Documentación
├── 📊 status.tause.pro             - Página de estado del sistema
├── 🆘 help.tause.pro               - Centro de ayuda
├── 📝 blog.tause.pro               - Blog/contenido
├── 🚀 cdn.tause.pro                - Assets estáticos
└── 🏢 {tenant}.tause.pro           - Subdominios de clientes
```

## 💰 **Desglose Económico**

| Servicio | Configuración | Costo/mes |
|----------|---------------|-----------|
| **ECS Fargate Spot** | 512 CPU / 1GB RAM | ~$15 |
| **RDS PostgreSQL** | db.t3.micro (20GB) | ~$12 |
| **Application Load Balancer** | 1 ALB compartido | ~$16 |
| **S3 Storage** | 50GB con lifecycle | ~$3 |
| **Route 53** | DNS + queries | ~$0.50 |
| **CloudFront** | Free tier (1TB) | $0 |
| **Otros** | Logs, ECR, transfer | ~$8 |
| **TOTAL** | | **~$35-45** |

---

## 🚀 **Despliegue en 5 Pasos**

### **Paso 1: Preparar Entorno**

```bash
# Verificar herramientas
aws --version
docker --version

# Configurar AWS (si no está configurado)
aws configure
```

### **Paso 2: Ejecutar Despliegue**

```bash
# Dar permisos de ejecución
chmod +x infrastructure/deploy-tause-pro-economical.sh

# Ejecutar despliegue
./infrastructure/deploy-tause-pro-economical.sh
```

### **Paso 3: Validar Certificado SSL**

El script pausará para que valides el certificado SSL:

1. Ve a [AWS Certificate Manager](https://console.aws.amazon.com/acm/home?region=us-east-1#/)
2. Encuentra el certificado para `*.tause.pro`
3. Sigue las instrucciones de validación DNS
4. Presiona `y` cuando esté validado

### **Paso 4: Configurar DNS**

El script te mostrará los nameservers de Route 53:

1. Ve a tu registrador de dominios
2. Configura los nameservers de `tause.pro` con los proporcionados
3. Espera 5-15 minutos para propagación DNS

### **Paso 5: Verificar Funcionamiento**

```bash
# Verificar subdominios
curl -I https://tause.pro
curl -I https://app.tause.pro
curl -I https://api.tause.pro
curl -I https://admin.tause.pro
```

---

## 🔧 **Configuración Post-Despliegue**

### **1. Configurar Alertas de Costos**

```bash
# Crear alerta de costos en AWS Budgets
aws budgets create-budget \
  --account-id $(aws sts get-caller-identity --query Account --output text) \
  --budget '{
    "BudgetName": "TauseStack-Monthly-Budget",
    "BudgetLimit": {
      "Amount": "50",
      "Unit": "USD"
    },
    "TimeUnit": "MONTHLY",
    "BudgetType": "COST"
  }'
```

### **2. Configurar Monitoreo Básico**

```bash
# Crear alarma CloudWatch para CPU alta
aws cloudwatch put-metric-alarm \
  --alarm-name "TauseStack-High-CPU" \
  --alarm-description "Alert when CPU exceeds 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2
```

### **3. Configurar Backups Automatizados**

Los backups de RDS ya están configurados con retención de 1 día. Para aumentar:

```bash
aws rds modify-db-instance \
  --db-instance-identifier tausestack-economical-db \
  --backup-retention-period 7 \
  --apply-immediately
```

---

## 🛠️ **Gestión de Tenants**

### **Crear Nuevo Tenant**

```python
from tausestack.sdk.tenancy import tenancy

# Crear tenant
tenant_config = {
    "name": "Mi Cliente",
    "subdomain": "micliente",
    "plan": "basic"
}

tenant_id = tenancy.create_tenant("micliente", tenant_config)
print(f"Tenant creado: https://micliente.tause.pro")
```

### **Configurar Dominio Personalizado**

```python
from tausestack.sdk.tenancy import domain_manager

# Registrar dominio personalizado
domain_manager.register_custom_domain(
    tenant_id="micliente",
    custom_domain="app.micliente.com"
)
```

---

## 📊 **Monitoreo y Métricas**

### **Dashboard CloudWatch**

```bash
# Ver métricas en tiempo real
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average
```

### **Logs de Aplicación**

```bash
# Ver logs recientes
aws logs tail /ecs/tausestack-economical --follow
```

---

## 🔐 **Seguridad**

### **Credenciales Importantes**

- **Base de Datos**: La contraseña se genera automáticamente y se muestra al final del despliegue
- **ECR**: Autenticación automática via IAM roles
- **S3**: Acceso via IAM roles del contenedor

### **Configuración SSL**

- **Certificado**: Automático via AWS Certificate Manager
- **Renovación**: Automática
- **Cobertura**: `*.tause.pro` y `tause.pro`

---

## 🚀 **Escalabilidad**

### **Auto-scaling Horizontal**

```bash
# Configurar auto-scaling
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/tausestack-economical-cluster/tausestack-economical-service \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 1 \
  --max-capacity 10
```

### **Escalado Vertical**

Para aumentar recursos, actualiza el CloudFormation template:

```yaml
Cpu: 1024      # De 512 a 1024
Memory: 2048   # De 1024 a 2048
```

---

## 🆘 **Troubleshooting**

### **Problemas Comunes**

1. **Certificado SSL no valida**
   ```bash
   # Verificar estado del certificado
   aws acm describe-certificate --certificate-arn <CERT_ARN>
   ```

2. **DNS no propaga**
   ```bash
   # Verificar configuración DNS
   dig tause.pro NS
   dig app.tause.pro
   ```

3. **Contenedor no inicia**
   ```bash
   # Ver logs del contenedor
   aws logs tail /ecs/tausestack-economical --follow
   ```

### **Comandos de Diagnóstico**

```bash
# Estado del stack
aws cloudformation describe-stacks --stack-name tausestack-economical

# Estado del servicio ECS
aws ecs describe-services \
  --cluster tausestack-economical-cluster \
  --services tausestack-economical-service

# Estado de la base de datos
aws rds describe-db-instances \
  --db-instance-identifier tausestack-economical-db
```

---

## 🔄 **Actualizaciones**

### **Actualizar Aplicación**

```bash
# Rebuild y push imagen
docker build -t tausestack:latest .
docker tag tausestack:latest $ECR_URI:latest
docker push $ECR_URI:latest

# Forzar nuevo despliegue
aws ecs update-service \
  --cluster tausestack-economical-cluster \
  --service tausestack-economical-service \
  --force-new-deployment
```

### **Actualizar Infraestructura**

```bash
# Re-ejecutar script de despliegue
./infrastructure/deploy-tause-pro-economical.sh
```

---

## 💡 **Optimizaciones Futuras**

### **Cuando tengas más tráfico:**

1. **Migrar a Reserved Instances** (ahorro 30-60%)
2. **Implementar CDN personalizado** para assets
3. **Configurar Multi-AZ** para alta disponibilidad
4. **Implementar caché Redis** para mejor performance

### **Cuando tengas más presupuesto:**

1. **Aumentar recursos** de ECS y RDS
2. **Implementar multi-región**
3. **Agregar WAF** para seguridad avanzada
4. **Configurar monitoreo avanzado**

---

## 🎉 **¡Listo para Producción!**

Con esta configuración tienes:

✅ **Plataforma multi-tenant completa**  
✅ **Todos los subdominios bajo control**  
✅ **SSL automático y renovación**  
✅ **Escalabilidad automática**  
✅ **Monitoreo básico**  
✅ **Backups automatizados**  
✅ **Seguridad robusta**  
✅ **Costo súper optimizado: ~$35-45/mes**  

**¡Tu aplicación estará disponible en todos los subdominios en menos de 30 minutos!** 