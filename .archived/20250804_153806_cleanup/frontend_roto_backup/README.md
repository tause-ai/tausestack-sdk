# TauseStack Admin UI v0.6.0

Admin interface para gestión de servicios multi-tenant de TauseStack.

## 🚀 Características

- **Dashboard en tiempo real** con métricas de todos los servicios
- **Gestión de tenants** con estadísticas detalladas y acciones administrativas
- **Monitoreo de servicios** con health checks y tiempos de respuesta
- **API Gateway management** con rate limiting y métricas
- **Interfaz responsiva** optimizada para desktop y móvil

## 🛠️ Tecnologías

- **Next.js 15** con App Router
- **React 19** con TypeScript
- **Tailwind CSS 4** para estilos
- **Heroicons** para iconografía
- **Recharts** para gráficos y visualizaciones

## 📦 Instalación

```bash
# Instalar dependencias
npm install

# Ejecutar en modo desarrollo
npm run dev

# Construir para producción
npm run build

# Ejecutar en producción
npm start
```

## 🔧 Configuración

El Admin UI se conecta al API Gateway de TauseStack que debe estar corriendo en `http://localhost:9000`.

### Variables de entorno (opcional)

Crear `.env.local`:

```env
NEXT_PUBLIC_API_GATEWAY_URL=http://localhost:9000
NEXT_PUBLIC_ADMIN_TITLE="TauseStack Admin"
```

## 📱 Páginas

### Dashboard (`/`)
- Métricas generales del sistema
- Estado de todos los servicios
- Uso por tenant
- Información del sistema

### Gestión de Tenants (`/tenants`)
- Lista de todos los tenants
- Estadísticas por tenant
- Rate limiting actual
- Acciones administrativas

### Servicios (`/services`)
- Estado de cada servicio
- Health checks
- Métricas de performance

### Analytics (`/analytics`)
- Gráficos de uso
- Tendencias temporales
- Reportes detallados

### API Gateway (`/gateway`)
- Configuración del gateway
- Rate limiting global
- Métricas de proxy

## 🔗 Integración con Backend

El Admin UI consume las siguientes APIs del gateway:

```typescript
// Health check
GET /health

// Métricas
GET /metrics

// Gestión de tenants
GET /admin/tenants
GET /admin/tenants/{id}/stats
POST /admin/tenants/{id}/reset-limits

// Servicios
GET /analytics/health
GET /communications/health
GET /billing/health
GET /mcp/health
```

## 🎨 Estructura de Componentes

```
src/
├── app/
│   ├── layout.tsx          # Layout principal con sidebar
│   ├── page.tsx           # Dashboard principal
│   ├── tenants/
│   │   └── page.tsx       # Gestión de tenants
│   ├── services/
│   │   └── page.tsx       # Estado de servicios
│   ├── analytics/
│   │   └── page.tsx       # Analytics y reportes
│   └── gateway/
│       └── page.tsx       # Configuración del gateway
├── components/            # Componentes reutilizables
│   ├── Dashboard/
│   ├── Tenants/
│   ├── Services/
│   └── Common/
└── lib/
    ├── api.ts            # Cliente API
    ├── types.ts          # Tipos TypeScript
    └── utils.ts          # Utilidades
```

## 🚀 Desarrollo

### Agregar nueva página

1. Crear archivo en `src/app/nueva-pagina/page.tsx`
2. Agregar enlace en el sidebar (`layout.tsx`)
3. Implementar la interfaz

### Agregar nuevo componente

```typescript
// src/components/MiComponente.tsx
'use client'

import { useState } from 'react'

interface MiComponenteProps {
  data: any
}

export default function MiComponente({ data }: MiComponenteProps) {
  return (
    <div className="bg-white shadow rounded-lg p-6">
      {/* Contenido del componente */}
    </div>
  )
}
```

### Consumir API

```typescript
// Ejemplo de uso de la API
const fetchTenants = async () => {
  try {
    const response = await fetch('/admin/tenants')
    const data = await response.json()
    setTenants(data.tenants)
  } catch (error) {
    console.error('Error fetching tenants:', error)
  }
}
```

## 🔒 Autenticación (Próximamente)

En futuras versiones se agregará:
- Login con Firebase Auth
- Roles y permisos
- Sesiones seguras
- Audit logs

## 📊 Métricas y Monitoreo

El Admin UI muestra métricas en tiempo real:

- **Gateway**: Total requests, success rate, response time
- **Servicios**: Health status, response times, errors
- **Tenants**: Usage stats, rate limits, active services
- **Sistema**: Uptime, version, configuration

## 🎯 Roadmap

- [ ] Gráficos avanzados con Recharts
- [ ] Notificaciones en tiempo real
- [ ] Configuración de alertas
- [ ] Exportación de reportes
- [ ] Tema oscuro
- [ ] Autenticación y autorización
- [ ] Audit logs
- [ ] Configuración avanzada de servicios

## 🤝 Contribuir

1. Fork el repositorio
2. Crear branch para la feature
3. Implementar cambios
4. Agregar tests si es necesario
5. Crear Pull Request

## 📄 Licencia

MIT - Ver archivo LICENSE para más detalles.

---

**TauseStack v0.6.0** - Admin UI Multi-Tenant  
Desarrollado por [Felipe Tause](https://www.tause.co)
