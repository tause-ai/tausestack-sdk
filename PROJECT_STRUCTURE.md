# Estructura de Proyecto Recomendada para Aplicaciones TauseStack

Este documento describe la estructura de directorios y el enfoque de configuración recomendados al construir aplicaciones utilizando el framework TauseStack.

## Vista General de la Estructura

```
mi_aplicacion_tausestack/
├── app/                                # Directorio principal del código de la aplicación
│   ├── __init__.py
│   ├── main.py                         # Punto de entrada: FastAPI app, incluye routers, usa settings de TauseStack y/o de la app
│   ├── core/                           # Lógica central de la aplicación
│   │   ├── __init__.py
│   │   └── config.py                   # (Opcional) Settings Pydantic específicas de la app, puede heredar de tausestack.framework.config.BaseAppSettings
│   ├── apis/                           # Módulos con routers (APIRouter o TauseStackRouter)
│   │   ├── __init__.py                 # Podría usarse para la carga dinámica de routers (futuro)
│   │   └── (nombre_modulo_api).py      # Ejemplo: users_api.py, items_api.py
│   ├── models/                         # Modelos Pydantic para request/response (schemas)
│   │   ├── __init__.py
│   │   └── (nombre_modelo).py          # Ejemplo: user_models.py, item_models.py
│   ├── services/                       # Lógica de negocio, interactúa con módulos del SDK de TauseStack
│   │   ├── __init__.py
│   │   └── (nombre_servicio).py        # Ejemplo: user_service.py
│   └── dependencies.py                 # (Opcional) Dependencias personalizadas de FastAPI para la aplicación
├── tests/                              # Pruebas unitarias y de integración para la aplicación
│   └── ...
├── .env                                # Variables de entorno para TauseStack y settings específicas de la app
├── pyproject.toml                      # Dependencias del proyecto (incluyendo 'tausestack') y configuración de herramientas
└── README.md                           # README específico de la aplicación
```

## Componentes Clave

### 1. `app/main.py`

-   **Punto de Entrada Principal**: Aquí se crea y configura la instancia principal de `FastAPI`.
-   **Configuración**: Puede acceder a la configuración global del framework TauseStack a través de `tausestack.framework.config.settings` (una instancia de `BaseAppSettings`), o usar/extender con configuraciones propias en `app/core/config.py`.
-   **Inclusión de Routers**: Utiliza la función `tausestack.framework.routing.load_routers_from_directory` para escanear automáticamente el directorio `app/apis/` y registrar todos los routers (`APIRouter` o `TauseStackRouter`) que encuentre. Esto simplifica la gestión de múltiples módulos de API.

    ```python
    # Ejemplo: app/main.py
    import os
    from fastapi import FastAPI
    from tausestack.framework.config import settings as tausestack_settings
    from tausestack.framework.routing import load_routers_from_directory
    # from .core.config import my_app_settings # Si se usa config específica de la app

    # Determinar la ruta base de la aplicación para construir la ruta a 'apis'
    # Esto asume que main.py está en app/main.py
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    APIS_DIR = os.path.join(APP_DIR, "apis")

    app = FastAPI(
        title=getattr(my_app_settings, 'APP_TITLE', tausestack_settings.APP_TITLE), # Usar getattr para seguridad
        version=getattr(my_app_settings, 'APP_VERSION', tausestack_settings.APP_VERSION),
        # ... otras configuraciones de FastAPI
    )

    # Carga dinámica de routers desde el directorio app/apis/
    # La función buscará archivos .py que contengan una variable 'router' (APIRouter o TauseStackRouter)
    loaded_router_modules = load_routers_from_directory(app, APIS_DIR)
    # Puedes imprimir o loggear los módulos cargados si es necesario:
    # print(f"Routers cargados desde: {loaded_router_modules}")

    @app.get("/")
    async def root():
        return {"message": f"Bienvenido a {app.title} v{app.version}"}
    ```

### 2. `app/core/config.py` (Opcional)

-   **Configuraciones Específicas de la Aplicación**: Si tu aplicación requiere configuraciones adicionales que deben cargarse desde variables de entorno o un archivo `.env` (siguiendo el patrón de Pydantic Settings), puedes definirlas aquí.
-   **Herencia Recomendada**: Se recomienda que tu clase de settings herede de `tausestack.framework.config.BaseAppSettings` para mantener la consistencia, heredar las configuraciones base del framework y su mecanismo de carga.

    ```python
    # Ejemplo: app/core/config.py
    from tausestack.framework.config import BaseAppSettings
    from pydantic import Field

    class MyAppSettings(BaseAppSettings):
        # Sobrescribir settings del framework si es necesario
        APP_TITLE: str = "Mi Increíble Aplicación TauseStack"
        APP_VERSION: str = "1.0.0"

        # Settings específicas de la aplicación
        MI_CONFIG_ESPECIFICA: str = Field(default="valor_por_defecto", env="MI_CONFIG_ESPECIFICA")
        OTRA_API_KEY: str = Field(env="OTRA_API_KEY") # Esta será requerida en el .env

        class Config:
            env_file = ".env" # Asegura que también lee el .env del proyecto
            extra = 'ignore' # O 'allow' si prefieres

    my_app_settings = MyAppSettings()
    ```
-   Si no se necesitan configuraciones adicionales específicas de la aplicación con este patrón, este archivo puede omitirse, y se usa `tausestack.framework.config.settings` para todas las necesidades de configuración del framework.

### 3. `app/apis/`

-   **Módulos de Endpoints**: Contiene los módulos que definen los `APIRouter` (o preferiblemente `tausestack.framework.routing.TauseStackRouter`) para organizar los endpoints de tu API.
-   Cada archivo (ej. `users_api.py`) típicamente define un router y sus rutas asociadas.

    ```python
    # Ejemplo: app/apis/users_api.py
    from tausestack.framework.routing import TauseStackRouter
    # from ..models.user_models import UserResponse, UserCreate
    # from ..services import user_service

    router = TauseStackRouter(prefix="/users", tags=["Users"])

    @router.get("/me", response_model=UserResponse, auth_required=True)
    async def get_current_user_info(current_user: User = Depends(get_current_user)):
        return current_user
    ```

### 4. `app/models/`

-   **Schemas de Datos**: Define los modelos Pydantic utilizados para la validación de datos de entrada (request bodies) y la serialización de datos de salida (response bodies).

### 5. `app/services/`

-   **Lógica de Negocio**: Contiene la lógica de negocio más compleja que no encaja directamente en los endpoints. Estos servicios son utilizados por los routers en `app/apis/` y pueden interactuar con los módulos del SDK de TauseStack (ej. `sdk.database`, `sdk.storage`, `sdk.auth` para operaciones más allá de la autenticación de ruta).

### 6. `.env` (Archivo de Entorno)

-   **Configuración Centralizada**: Un único archivo `.env` en la raíz del proyecto de la aplicación debe usarse para todas las variables de entorno.
-   Esto incluye variables requeridas por el framework TauseStack (ej. `TAUSESTACK_FIREBASE_SA_KEY_PATH`, `TAUSESTACK_STORAGE_BACKEND`, `TAUSESTACK_DATABASE_URL`) y cualquier variable específica de la aplicación definida en `app/core/config.py` (ej. `MI_CONFIG_ESPECIFICA`, `OTRA_API_KEY`).
-   Tanto `tausestack.framework.config.settings` como la instancia de `MyAppSettings` (si se usa) cargarán automáticamente las variables relevantes desde este archivo `.env` gracias a Pydantic Settings.

## Beneficios de esta Estructura

-   **Claridad y Organización**: Separa las preocupaciones de la aplicación (APIs, modelos, servicios) de manera lógica.
-   **Escalabilidad**: Facilita el crecimiento de la aplicación al tener una estructura bien definida.
-   **Integración con TauseStack**: Permite una integración fluida con las características de configuración y los módulos del SDK de TauseStack.
-   **Mantenibilidad**: Hace que el código sea más fácil de entender, mantener y probar.

## Próximos Pasos para el Framework

-   **Carga Dinámica de Routers**: Implementada. La función `tausestack.framework.routing.load_routers_from_directory` permite cargar automáticamente routers desde el directorio `app/apis/`, simplificando la configuración en `app/main.py`.
-   **CLI para Scaffolding**: Proporcionar un comando CLI (`tausestack init`) para generar esta estructura de proyecto base automáticamente, utilizando la carga dinámica de routers.
