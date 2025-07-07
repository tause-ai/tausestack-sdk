# Guía Rápida (Quick Start) – TauseStack

Esta guía te muestra cómo crear y desplegar una aplicación básica con TauseStack.

---

## 1. Requisitos previos
- Docker y Docker Compose
- Python 3.11+
- Node.js 18+

## 2. Inicializa un nuevo proyecto
```bash
tause init my-app --type website
cd my-app
```

## 3. Instala las dependencias
```bash
# Backend
pip install -r requirements.txt
# Frontend
cd frontend && npm install
```

## 4. Ejecuta el entorno de desarrollo
```bash
tause dev
```
El backend estará en `http://localhost:8000` y el frontend en `http://localhost:3000`.

## 5. Agrega un módulo (ejemplo: auth)
```bash
tause add auth --project my-app
```

## 6. Ejecuta los tests
```bash
tause test
```

## 7. Despliega a producción
```bash
tause deploy --env production
```

---

## Estructura del proyecto
Consulta el archivo `README.md` y la documentación en `/docs` para más detalles sobre la estructura y los módulos.

## Recursos adicionales
- [Documentación completa](../index.md)
- [Ejemplos de integración](../examples/)

¡Listo! Ya puedes comenzar a desarrollar con TauseStack.
