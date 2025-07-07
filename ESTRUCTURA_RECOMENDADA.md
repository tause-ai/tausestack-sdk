# Estructura de Directorios Recomendada para TauseStack

## 🎯 Estructura Simplificada y Consistente

```
tausestack/
├── cli/                    # CLI tools únicamente
│   ├── commands/
│   └── main.py
├── sdk/                    # SDK principal - TODO aquí
│   ├── auth/              # Autenticación (UNA sola implementación)
│   ├── database/          # Base de datos
│   ├── storage/           # Almacenamiento
│   ├── cache/             # Cache
│   ├── notify/            # Notificaciones
│   ├── secrets/           # Secretos
│   └── __init__.py        # Exporta todo el SDK
├── framework/             # Framework core
│   ├── config.py          # Configuración central
│   ├── routing.py         # Routing avanzado
│   └── main.py            # App base
├── services/              # Microservicios específicos (solo si son independientes)
│   ├── mcp_server/        # Servidor MCP (justificado como microservicio)
│   └── agent_orchestration/  # Orquestación (justificado)
├── templates/             # Templates de aplicaciones
│   ├── base/
│   ├── crm/
│   ├── ecommerce/
│   └── chatbot/
├── frontend/              # Frontend Next.js
├── tests/                 # Tests organizados por módulo
│   ├── sdk/
│   ├── framework/
│   ├── services/
│   └── integration/
├── docs/                  # Documentación
├── examples/              # Ejemplos de uso
└── pyproject.toml
```

## 🔧 Cambios Necesarios

### 1. Eliminar Duplicaciones
```bash
# ELIMINAR estos directorios:
rm -rf core/                    # Mover contenido a sdk/ o framework/
rm -rf services/auth/           # Ya existe en sdk/auth/
rm -rf services/storage/        # Ya existe en sdk/storage/
rm -rf services/database/       # Ya existe en sdk/database/
rm -rf services/users/          # Integrar en sdk/auth/
```

### 2. Consolidar Implementaciones
```python
# EN LUGAR DE:
from core.modules.auth import ...
from services.auth import ...
from tausestack.sdk.auth import ...

# SOLO UNA FORMA:
from tausestack.sdk.auth import ...
```

### 3. Reglas Claras
- **sdk/**: Toda la funcionalidad reutilizable
- **framework/**: Core del framework (routing, config)
- **services/**: Solo microservicios independientes (MCP, orquestación)
- **templates/**: Templates de aplicaciones
- **cli/**: Herramientas CLI

## 📋 Plan de Refactorización

### Fase 1: Consolidación (1-2 días)
1. Mover toda funcionalidad de `core/modules/` a `sdk/`
2. Eliminar duplicaciones en `services/`
3. Actualizar imports en todo el proyecto

### Fase 2: Reorganización (1 día)
1. Limpiar estructura de tests
2. Actualizar documentación
3. Verificar que todo funciona

### Fase 3: Validación (1 día)
1. Ejecutar toda la suite de tests
2. Verificar CLI funciona
3. Probar templates

## 🎯 Beneficios

- **Simplicidad**: Una sola forma de hacer cada cosa
- **Consistencia**: Estructura predecible
- **Mantenibilidad**: Menos código duplicado
- **Claridad**: Desarrolladores saben dónde encontrar/agregar código
- **Escalabilidad**: Estructura que crece de forma ordenada

## 🚨 Riesgos Actuales

Sin esta refactorización:
- Confusión para nuevos desarrolladores
- Bugs por usar implementaciones incorrectas
- Mantenimiento complejo
- Dificultad para escalar el equipo 