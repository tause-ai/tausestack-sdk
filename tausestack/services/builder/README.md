# TauseStack Builder - Visual App Builder

## 🎯 Descripción

El **TauseStack Builder** es un builder visual de aplicaciones que permite crear y desplegar aplicaciones completas usando una interfaz intuitiva. 

## 🏗️ Arquitectura

Siguiendo el **TauseStack Framework**, el Builder implementa:

### ✅ Service Pattern
- **BuilderService**: Lógica de negocio centralizada
- **Multi-tenant**: Soporte nativo para múltiples tenants
- **Async/await**: Operaciones asíncronas para mejor rendimiento

### ✅ API Pattern
- **FastAPI**: API REST con validación Pydantic
- **Autenticación**: Integración con sistema de auth de TauseStack
- **Rate Limiting**: Control de uso por tenant

### ✅ MCP Tool Pattern
- **BuilderMCPServer**: Herramientas MCP para acceso externo
- **Extensible**: Nuevas herramientas fáciles de agregar

### ✅ Frontend Pattern
- **Next.js**: Frontend integrado con admin de TauseStack
- **Shadcn/ui**: Componentes UI consistentes
- **Responsive**: Diseño adaptativo

## 🚀 Características

### 🎨 Builder Visual
- **Interfaz intuitiva** para crear aplicaciones
- **Templates predefinidos** para diferentes tipos de apps
- **Componentes drag-and-drop** (próximamente)
- **Preview en tiempo real** (próximamente)

### 🤖 IA Integrada
- **Generación automática** de código usando GPT-4
- **Descripción a código** - describe tu app y la IA la genera
- **Optimización inteligente** de componentes

### 🔧 Templates Disponibles
- **Web App Básica**: React + FastAPI + PostgreSQL
- **API REST**: FastAPI con documentación automática
- **Agente IA**: Agente con MCP y herramientas
- **E-commerce**: Tienda online con pagos
- **Dashboard Analytics**: Panel de métricas

### 🚀 Despliegue
- **Multi-dominio**: Soporte para tause.pro y dominios personalizados
- **AWS**: Despliegue automático en infraestructura AWS
- **SSL**: Certificados automáticos
- **Monitoreo**: Métricas y logs integrados

## 📁 Estructura del Proyecto

```
tausestack/services/builder/
├── __init__.py                 # Exports principales
├── README.md                   # Este archivo
├── core/
│   └── builder_service.py      # Servicio principal
├── api/
│   └── builder_api.py         # API REST
├── tools/
│   └── builder_tools.py       # Herramientas MCP
└── config/
    └── builder_config.py      # Configuración

frontend/src/app/admin/builder/
└── page.tsx                   # Interfaz frontend
```

## 🛠️ Instalación y Uso

### 1. Requisitos
- Python 3.8+
- Node.js 18+
- PostgreSQL 15+
- Redis (para cache)

### 2. Configuración
```bash
# Variables de entorno
export ENVIRONMENT=development
export TAUSESTACK_DATABASE_URL=postgresql://user:pass@localhost/tausestack
export TAUSESTACK_REDIS_URL=redis://localhost:6379
```

### 3. Ejecutar el Builder
```bash
# Backend (ya incluido en API Gateway)
cd tausestack-sdk
python -m tausestack.services.api_gateway

# Frontend (ya incluido en admin)
cd frontend
npm run dev
```

### 4. Acceder al Builder
- **URL**: http://localhost:3000/admin/builder
- **Autenticación**: Requerida (rol admin)

## 📊 Uso del Builder

### 1. Crear Proyecto
```python
# Usando API directamente
POST /api/builder/projects
{
    "name": "Mi App",
    "description": "Una aplicación increíble",
    "type": "web",
    "template_id": "web-basic",
    "tenant_id": "mi-tenant"
}
```

### 2. Usar MCP Tools
```python
# Crear proyecto via MCP
await builder_mcp.handle_call_tool("create_project", {
    "name": "Mi App",
    "description": "Una aplicación increíble",
    "project_type": "web"
})
```

### 3. Generar desde Descripción
```python
# Generar automáticamente
await builder_mcp.handle_call_tool("generate_project_from_description", {
    "description": "Quiero una tienda online para vender productos artesanales con carrito de compras y pagos con Stripe",
    "project_type": "ecommerce"
})
```

## 🔧 Configuración Avanzada

### Templates Personalizados
```python
# En builder_config.py
CUSTOM_TEMPLATES = {
    "mi-template": {
        "name": "Mi Template",
        "description": "Template personalizado",
        "type": "web",
        "components": [
            {
                "type": "frontend",
                "name": "Custom React App",
                "config": {"framework": "react", "version": "18.x"}
            }
        ]
    }
}
```

### Dominios Personalizados
```python
# En builder_config.py
DEPLOY_DOMAINS = [
    "tausestack.dev",
    "tause.pro",
    "app.tause.pro",
    "mi-dominio.com"
]
```

## 🎯 Roadmap

### ✅ Completado
- [x] Arquitectura base siguiendo TauseStack Framework
- [x] Service Pattern implementado
- [x] API Pattern implementado
- [x] MCP Tool Pattern implementado
- [x] Frontend básico integrado
- [x] Templates predefinidos
- [x] Integración con API Gateway

### 🔄 En Desarrollo
- [ ] Builder visual drag-and-drop
- [ ] Preview en tiempo real
- [ ] Generación de código mejorada
- [ ] Integración con sistema de templates existente

### 🚀 Próximamente
- [ ] Marketplace de templates
- [ ] Colaboración en tiempo real
- [ ] Versionado de proyectos
- [ ] Analytics de uso
- [ ] Integración con GitHub

## 🤝 Contribuir

### Agregar Template
1. Definir en `builder_config.py`
2. Crear lógica en `builder_service.py`
3. Agregar al frontend en `page.tsx`
4. Documentar en README

### Agregar Herramienta MCP
1. Definir tool en `builder_tools.py`
2. Implementar handler
3. Agregar al setup de tools
4. Documentar uso

### Extender API
1. Agregar endpoint en `builder_api.py`
2. Agregar validación Pydantic
3. Agregar al proxy en `api_gateway.py`
4. Documentar endpoint

## 📝 Licencia

Este proyecto es parte de TauseStack y sigue la misma licencia del proyecto principal.

## 🔗 Enlaces

- [TauseStack Framework](../../README.md)
- [API Gateway](../api_gateway.py)
- [Frontend Admin](../../../frontend/src/app/admin/)
- [Documentación MCP](../../../docs/mcp.md)

---

**¡El Builder está listo para usar!** 🎉

Para empezar, visita http://localhost:3000/admin/builder después de ejecutar el proyecto. 