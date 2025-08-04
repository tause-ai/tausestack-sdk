# TauseStack SDK

**SDK completo multi-tenant con microservicios para desarrollo empresarial**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/tausestack/tausestack-sdk/workflows/Tests/badge.svg)](https://github.com/tausestack/tausestack-sdk/actions)

## 🚀 Características Principales

- ✅ **Multi-tenant nativo** - Aislamiento completo por tenant
- 🔧 **Microservicios distribuidos** - Arquitectura escalable
- 🌐 **Backends configurables** - Local, AWS, GCP, Azure
- 📊 **Analytics en tiempo real** - Dashboards y métricas
- 💰 **Sistema de billing** - Facturación automatizada
- 🤖 **IA integrada** - Múltiples proveedores (OpenAI, Anthropic)
- 📧 **Notificaciones multi-canal** - Email, SMS, Push
- 🔒 **Autenticación robusta** - Firebase, JWT, OAuth2
- 📄 **Templates dinámicos** - Motor de plantillas
- 🇨🇴 **Funcionalidades para Colombia** - Pasarelas de pago, validaciones

## 📦 Instalación

```bash
# Instalación básica
pip install tausestack-sdk

# Con todas las funcionalidades
pip install tausestack-sdk[all]

# Instalaciones específicas
pip install tausestack-sdk[aws]        # Soporte AWS
pip install tausestack-sdk[analytics]  # Analytics y DataFrames
pip install tausestack-sdk[ai]         # Servicios de IA
pip install tausestack-sdk[payments]   # Pasarelas de pago
```

## 🏃‍♂️ Inicio Rápido

### 1. Configuración Básica

```python
import tausestack as ts

# Configurar tenant (opcional, usa 'default' si no se especifica)
ts.set_tenant("mi-empresa")

# Storage multi-tenant
ts.storage.json.put("config", {"theme": "dark", "lang": "es"})
data = ts.storage.json.get("config")
print(data)  # {"theme": "dark", "lang": "es"}

# Cache distribuido
@ts.cache(ttl=300)
def expensive_operation(param):
    # Operación costosa
    return f"Result for {param}"

result = expensive_operation("test")  # Se ejecuta y cachea
result = expensive_operation("test")  # Se obtiene del cache
```

### 2. Microservicios

```python
# Analytics en tiempo real
ts.analytics.track_event("user_login", {
    "user_id": "123",
    "source": "web",
    "timestamp": "2024-01-15T10:30:00Z"
})

# Sistema de billing
invoice = ts.billing.create_invoice(
    customer_id="cust_123",
    items=[
        {"name": "Plan Pro", "amount": 99.99, "currency": "USD"},
        {"name": "Storage Extra", "amount": 19.99, "currency": "USD"}
    ]
)

# Notificaciones
ts.notify.email(
    to="usuario@empresa.com",
    subject="Bienvenido a nuestro servicio",
    html="<h1>¡Hola!</h1><p>Gracias por registrarte.</p>"
)

# Templates dinámicos
content = ts.templates.render("welcome_email", {
    "user_name": "Juan Pérez",
    "company": "Mi Empresa",
    "plan": "Pro"
})
```

### 3. IA Integrada

```python
# Generación de texto
response = ts.ai.generate_text(
    prompt="Escribe un email de bienvenida profesional",
    model="gpt-4",
    max_tokens=200
)

# Generación de código
code = ts.ai.generate_code(
    description="Función para validar email en Python",
    language="python"
)

# Análisis de sentimientos
sentiment = ts.ai.analyze_sentiment(
    text="Me encanta este producto, es increíble!"
)
```

### 4. Funcionalidades para Colombia

```python
# Validaciones colombianas
is_valid = ts.colombia.validate_cedula("12345678")
is_valid_nit = ts.colombia.validate_nit("900123456-1")

# Pasarelas de pago
payment = ts.payments.create_wompi_payment(
    amount=50000,  # $50,000 COP
    currency="COP",
    customer_email="cliente@email.com",
    reference="orden-123"
)

# PSE
pse_payment = ts.payments.create_pse_payment(
    amount=100000,  # $100,000 COP
    customer_email="cliente@email.com",
    bank_code="1007"  # Bancolombia
)

# Datos geográficos
departamentos = ts.colombia.get_departamentos()
municipios = ts.colombia.get_municipios("05")  # Antioquia
```

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                    TauseStack SDK                               │
├─────────────────────────────────────────────────────────────────┤
│  Storage  │  Cache  │  Notify  │  Auth  │  Analytics  │  AI    │
├─────────────────────────────────────────────────────────────────┤
│                    API Gateway Multi-tenant                    │
├─────────────────────────────────────────────────────────────────┤
│ Analytics │ Billing │ Comms │ Templates │ AI │ Payments │ Jobs │
├─────────────────────────────────────────────────────────────────┤
│              Backends Configurables                            │
│   Local │ AWS │ GCP │ Azure │ Redis │ PostgreSQL │ MongoDB    │
└─────────────────────────────────────────────────────────────────┘
```

## ⚙️ Configuración

### Variables de Entorno

```bash
# Configuración básica
TAUSESTACK_TENANT_ID=mi-empresa
TAUSESTACK_API_URL=http://localhost:8000

# Storage
TAUSESTACK_STORAGE_BACKEND=aws  # local, aws, gcp, azure
TAUSESTACK_S3_BUCKET=mi-bucket
TAUSESTACK_S3_REGION=us-east-1

# Cache
TAUSESTACK_CACHE_BACKEND=redis  # memory, disk, redis
TAUSESTACK_REDIS_URL=redis://localhost:6379/0

# Notificaciones
TAUSESTACK_NOTIFY_BACKEND=ses   # console, file, ses, smtp
TAUSESTACK_SES_REGION=us-east-1

# IA
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Pagos Colombia
WOMPI_PUBLIC_KEY=pub_test_...
WOMPI_PRIVATE_KEY=prv_test_...
```

### Configuración por Código

```python
import tausestack as ts

# Configurar backend de storage
ts.configure_storage(
    backend="s3",
    bucket="mi-bucket",
    region="us-east-1"
)

# Configurar cache
ts.configure_cache(
    backend="redis",
    url="redis://localhost:6379/0",
    prefix="mi-app:"
)

# Configurar notificaciones
ts.configure_notify(
    backend="ses",
    region="us-east-1",
    from_email="noreply@miempresa.com"
)
```

## 🔧 Desarrollo Local

```bash
# Clonar el repositorio
git clone https://github.com/tausestack/tausestack-sdk.git
cd tausestack-sdk

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias de desarrollo
pip install -e .[dev]

# Ejecutar tests
pytest

# Ejecutar servicios localmente
tausestack dev start

# Ver documentación
tausestack docs serve
```

## 🚀 Despliegue

### Docker

```bash
# Construir imagen
docker build -t mi-app-tausestack .

# Ejecutar contenedor
docker run -p 8000:8000 \
  -e TAUSESTACK_TENANT_ID=mi-empresa \
  -e TAUSESTACK_STORAGE_BACKEND=local \
  mi-app-tausestack
```

### AWS

```bash
# Desplegar con CloudFormation
tausestack deploy aws \
  --stack-name mi-app-production \
  --region us-east-1 \
  --tenant-id mi-empresa
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tausestack-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: tausestack-app
  template:
    metadata:
      labels:
        app: tausestack-app
    spec:
      containers:
      - name: app
        image: mi-app-tausestack:latest
        ports:
        - containerPort: 8000
        env:
        - name: TAUSESTACK_TENANT_ID
          value: "mi-empresa"
        - name: TAUSESTACK_STORAGE_BACKEND
          value: "s3"
```

## 📚 Documentación

- [Guía de Inicio](docs/getting-started.md)
- [Referencia API](docs/api-reference.md)
- [Multi-tenant](docs/multi-tenant.md)
- [Microservicios](docs/microservices.md)
- [Backends](docs/backends.md)
- [Despliegue](docs/deployment.md)
- [Colombia](docs/colombia.md)

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Por favor lee nuestro [CONTRIBUTING.md](CONTRIBUTING.md) para más detalles.

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## 🆘 Soporte

- 📧 Email: support@tausestack.dev
- 💬 Discord: [TauseStack Community](https://discord.gg/tausestack)
- 🐛 Issues: [GitHub Issues](https://github.com/tausestack/tausestack-sdk/issues)
- 📖 Docs: [docs.tausestack.dev](https://docs.tausestack.dev)

---

**TauseStack SDK** - Desarrollado con ❤️ para la comunidad de desarrolladores
