# 🚀 TauseStack - Setup Local

Guía completa para configurar y ejecutar TauseStack en tu entorno local.

## 📋 Prerrequisitos

- **Python 3.11+** (recomendado: 3.12)
- **Git**
- **Docker** (opcional, para servicios externos)

## 🛠️ Instalación Rápida

### 1. Clonar y configurar

```bash
# Clonar el repositorio
git clone <repository-url>
cd tausestack

# Crear entorno virtual
python3.12 -m venv .venv
source .venv/bin/activate

# Instalar dependencias
pip install -e '.[dev]'
```

### 2. Configurar variables de entorno

```bash
# Copiar template de configuración
cp config/environment.template .env

# El archivo .env ya está configurado para desarrollo local
# con el dominio tausestack.dev
```

### 3. Verificar instalación

```bash
# Verificar que todo esté funcionando
python scripts/verify_setup.py
```

## 🚀 Iniciar Desarrollo Local

### Opción 1: Script automático (Recomendado)

```bash
# Iniciar todos los servicios
./scripts/start_local.sh

# Para detener
./scripts/stop_local.sh
```

### Opción 2: Comandos individuales

```bash
# Framework principal
tausestack framework run --port 8000

# API Gateway
python -m uvicorn tausestack.framework.main:app --host 0.0.0.0 --port 9001 --reload

# Servicios individuales
python -m uvicorn services.analytics.api.main:app --host 0.0.0.0 --port 8001 --reload
python -m uvicorn services.communications.api.main:app --host 0.0.0.0 --port 8002 --reload
python -m uvicorn services.billing.api.main:app --host 0.0.0.0 --port 8003 --reload
python -m uvicorn services.users.api.main:app --host 0.0.0.0 --port 8004 --reload
```

### Opción 3: Makefile

```bash
# Iniciar desarrollo local
make start-local

# Detener servicios
make stop-local

# Verificar estado
make verify
```

## 🌐 URLs Disponibles

Una vez iniciados los servicios, estarán disponibles en:

| Servicio | URL | Descripción |
|----------|-----|-------------|
| Framework | http://localhost:8000 | Framework principal |
| API Gateway | http://localhost:9001 | Gateway de APIs |
| Analytics | http://localhost:8001 | Servicio de analytics |
| Communications | http://localhost:8002 | Servicio de comunicaciones |
| Billing | http://localhost:8003 | Servicio de facturación |
| Users | http://localhost:8004 | Servicio de usuarios |

## 🔧 Comandos Útiles

### Desarrollo

```bash
# Verificar estado del proyecto
python scripts/verify_setup.py

# Ejecutar tests
pytest tests/ -v

# Formatear código
black .
isort .

# Linting
ruff check .

# Type checking
mypy tausestack/
```

### CLI

```bash
# Ver ayuda del CLI
tausestack --help

# Iniciar framework
tausestack framework run

# Inicializar proyecto
tausestack init

# Desplegar
tausestack deploy
```

## 📁 Estructura del Proyecto

```
tausestack/
├── tausestack/           # Framework principal
│   ├── sdk/             # SDK para desarrolladores
│   ├── framework/       # Framework core
│   └── cli/             # CLI tools
├── services/            # Microservicios
│   ├── analytics/       # Servicio de analytics
│   ├── communications/  # Servicio de comunicaciones
│   ├── billing/         # Servicio de facturación
│   └── users/           # Servicio de usuarios
├── scripts/             # Scripts de automatización
├── tests/               # Tests
├── config/              # Configuraciones
└── docs/                # Documentación
```

## 🔍 Troubleshooting

### Problemas Comunes

1. **Error de importación**
   ```bash
   # Reinstalar dependencias
   pip install -e '.[dev]'
   ```

2. **Puerto ocupado**
   ```bash
   # Detener procesos existentes
   ./scripts/stop_local.sh
   ```

3. **Variables de entorno no cargadas**
   ```bash
   # Cargar manualmente
   set -a && source .env && set +a
   ```

4. **Entorno virtual no activo**
   ```bash
   # Activar entorno
   source .venv/bin/activate
   ```

### Verificación Completa

```bash
# Ejecutar verificación completa
python scripts/verify_setup.py
```

## 🚀 Próximos Pasos

1. **Explorar la documentación**: Visita http://localhost:8000/docs
2. **Probar APIs**: Usa los endpoints disponibles en cada servicio
3. **Desarrollo**: Modifica código y ve los cambios en tiempo real
4. **Despliegue**: Cuando esté listo, usa `make deploy-aws`

## 📞 Soporte

- **Documentación**: http://localhost:8000/docs
- **Issues**: GitHub Issues
- **Comunidad**: Discord/Slack

---

¡Disfruta desarrollando con TauseStack! 🎉 