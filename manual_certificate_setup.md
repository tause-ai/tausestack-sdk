# Configuración Manual de Certificados tause.pro

## 🎯 Objetivo
Agregar certificados SSL de tause.pro al Load Balancer existente de TauseStack.

## 📋 Información Necesaria

### **Load Balancer**
- **Nombre**: `tausestack-final-fixed-alb`
- **ARN**: `arn:aws:elasticloadbalancing:us-east-1:349622182214:loadbalancer/app/tausestack-final-fixed-alb/c0102867a94eeb90`

### **Certificados Disponibles**
- **TauseStack**: `arn:aws:acm:us-east-1:349622182214:certificate/f190e0dd-5ce9-4702-85cf-4d3ce5faba79`
- **TausePro**: `arn:aws:acm:us-east-1:349622182214:certificate/1e8403aa-614e-4299-aeb6-364bb4215609`

## 🔧 Pasos para Configurar Certificados

### **Paso 1: Acceder a la Consola AWS**
1. Ve a: https://console.aws.amazon.com/ec2/
2. Cambia a la región: **us-east-1** (N. Virginia)
3. En el menú izquierdo, busca "Load Balancers"

### **Paso 2: Encontrar el Load Balancer**
1. Busca el Load Balancer: `tausestack-final-fixed-alb`
2. Haz clic en su nombre para ver los detalles

### **Paso 3: Modificar el Listener HTTPS**
1. Ve a la pestaña **"Listeners"**
2. Encuentra el listener **HTTPS:443**
3. Haz clic en **"Edit"** o **"Modify"**

### **Paso 4: Agregar Certificados**
1. En la sección **"Security"** o **"SSL Certificates"**
2. Haz clic en **"Add certificate"**
3. Busca y selecciona el certificado de tause.pro:
   ```
   *.tause.pro (arn:aws:acm:...1e8403aa-614e-4299-aeb6-364bb4215609)
   ```
4. Haz clic en **"Add"**

### **Paso 5: Verificar Configuración**
Después de agregar el certificado, deberías ver **ambos certificados**:
- ✅ `*.tausestack.dev` (existente)
- ✅ `*.tause.pro` (nuevo)

### **Paso 6: Guardar Cambios**
1. Haz clic en **"Save"** o **"Update"**
2. Espera a que se complete la actualización (1-2 minutos)

## 🧪 Verificación

### **Verificar DNS**
```bash
# Verificar que los dominios resuelvan correctamente
dig tause.pro
dig app.tause.pro
dig api.tause.pro
```

### **Verificar SSL**
```bash
# Verificar certificados SSL
curl -I https://tause.pro
curl -I https://app.tause.pro
curl -I https://api.tause.pro
```

### **Verificar desde el Navegador**
- https://tause.pro ✅
- https://app.tause.pro ✅
- https://api.tause.pro ✅

## 🚨 Problemas Comunes

### **Error: "Invalid host header"**
- **Causa**: TauseStack no reconoce el dominio tause.pro
- **Solución**: Verificar que DomainManager esté configurado correctamente

### **Error: "SSL Certificate"**
- **Causa**: Certificado no asociado al Load Balancer
- **Solución**: Repetir pasos 3-6

### **Error: "Connection refused"**
- **Causa**: DNS no propagado o mal configurado
- **Solución**: Verificar registros DNS en Route 53

## 📞 Soporte
Si tienes problemas, revisa:
1. **Route 53**: Registros DNS correctos
2. **ACM**: Certificados válidos y activos
3. **Load Balancer**: Listener configurado correctamente 