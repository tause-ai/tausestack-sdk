"""
Roadmap del Framework TauseStack

Este documento rastrea el progreso del desarrollo del framework TauseStack, diseñado para igualar y superar la funcionalidad de la plataforma anterior construida en Databutton.

Objetivo 1: Un Sólido Núcleo de Framework (Backend)
- Formalizar la Base de FastAPI, establecer una estructura estándar de proyecto y gestionar dependencias.
- Implementar un sistema de ruteo dinámico y configurable con TauseStackRouter.
- Crear un middleware de autenticación central basado en sdk.auth.

Objetivo 2: SDK de TauseStack Potenciado
- Re-alcance del módulo sdk.auth con FirebaseAuthBackend y pruebas unitarias.
- Creación del módulo sdk.database con integración SQLAlchemy.
- Expansión del módulo sdk.storage para soportar archivos binarios y DataFrames.

Objetivo 3: Experiencia de Desarrollador (DX) y Herramientas
- Crear un CLI de TauseStack con comandos para inicializar, ejecutar y desplegar proyectos.
- Documentación y ejemplos completos para mostrar el uso de todos los componentes del framework y SDK.

Módulos del SDK Ya Implementados (Base)
- sdk.storage (JSON), sdk.secrets, sdk.cache, sdk.notify completados.
"""

# Roadmap del Framework TauseStack

Este documento rastrea el progreso del desarrollo del framework TauseStack, diseñado para igualar y superar la funcionalidad de la plataforma anterior construida en Databutton.

## Objetivo 1: Un Sólido Núcleo de Framework (Backend)

- [x] **Tarea 1.1: Formalizar la Base de FastAPI.**
  - [x] Definir una estructura de proyecto estándar para aplicaciones TauseStack (ej. `app/`, `main.py`, configuración centralizada).
  - [x] Establecer patrones para la gestión de dependencias y configuración (ej. Pydantic para settings).
- [x] **Tarea 1.2: Sistema de Ruteo Dinámico y Configurable.**
  - [x] Implementar un cargador de rutas dinámico que escanee un directorio específico (ej. `app/routes/` o `app/apis/`).
  - [x] Desarrollar un decorador (ej. `@tausestack.router(auth_required=True, tags=["mi_tag"])`) para que los `APIRouter` definan sus metadatos y requisitos de autenticación.
    *Nota: Implementado mediante `TauseStackRouter` (subclase de `APIRouter`) y `TauseStackRoute` para la lógica de autenticación por ruta.*
- [x] **Tarea 1.3: Middleware de Autenticación Central.**
  - [ ] Crear un middleware FastAPI que se integre con `sdk.auth`.
  - [ ] Permitir la protección de rutas basada en la configuración del decorador del router o por defecto.
    *Nota: Se optó por una autenticación por ruta más flexible usando `TauseStackRoute` en lugar de un middleware central. Esta aproximación cumple el objetivo de proteger rutas de manera configurable.*

## Objetivo 2: SDK de TauseStack Potenciado

- [x] **Tarea 2.1: Re-alcance del Módulo `sdk.auth` (Prioridad Máxima).**
  - [x] **Sub-Tarea 2.1.1: Interfaz `AbstractAuthBackend`.**
    - [x] Definir métodos para: verificar token, obtener usuario por UID, crear usuario, actualizar usuario, gestionar claims/roles.
  - [x] **Sub-Tarea 2.1.2: Implementación `FirebaseAuthBackend`.**
    - [x] Integración con `firebase-admin`.
    - [x] Implementar todos los métodos de `AbstractAuthBackend`.
    - [x] Manejo seguro de credenciales de servicio Firebase (vía `sdk.secrets` o variables de entorno).
  - [x] **Sub-Tarea 2.1.3: Dependencia FastAPI `get_current_user`.**
    - [x] Crear una dependencia FastAPI (ej. `current_user: User = Depends(sdk.auth.get_current_user)`) que utilice el backend configurado para autenticar y devolver el usuario.
    - [x] Definir un modelo Pydantic `User` para la información del usuario autenticado.
  - [x] **Sub-Tarea 2.1.4: Pruebas Unitarias Exhaustivas.**
  - [x] **Sub-Tarea 2.1.5: Documentación del Módulo `auth`.**
- [x] **Tarea 2.2: Creación del Módulo `sdk.database` (SQLAlchemyBackend).**
  - [x] **Sub-Tarea 2.2.1: Interfaz `AbstractDatabaseBackend`.**
    - [x] Definir operaciones CRUD básicas, gestión de transacciones, ejecución de consultas raw.
  - [x] **Sub-Tarea 2.2.2: Implementación `SQLAlchemyBackend`.**
    - [x] Integración con SQLAlchemy Core y ORM.
    - [x] Soporte para migraciones (ej. con Alembic).
    - [x] Configuración de la URL de la base de datos (vía `sdk.secrets` o variables de entorno).
  - [ ] **Sub-Tarea 2.2.3 (Alternativa/Adicional): Implementación `SupabaseBackend`.**
    - [ ] Integración con el cliente Python de Supabase.
  - [x] **Sub-Tarea 2.2.4: Pruebas Unitarias (SQLAlchemyBackend).**
  - [x] **Sub-Tarea 2.2.5: Documentación del Módulo `database` (SQLAlchemyBackend).**
- [ ] **Tarea 2.3: Expansión del Módulo `sdk.storage`.**
  - [ ] **Sub-Tarea 2.3.1: Soporte para Almacenamiento de Archivos Binarios.**
    - [ ] API: `sdk.storage.binary.put(key, file_object)`, `sdk.storage.binary.get(key) -> file_object`, `sdk.storage.binary.delete(key)`.
    - [ ] Actualizar `S3StorageBackend` y `LocalStorageBackend` para soportar binarios.
  - [ ] **Sub-Tarea 2.3.2: Soporte para Almacenamiento de DataFrames.**
    - [ ] API: `sdk.storage.dataframe.put(key, df)`, `sdk.storage.dataframe.get(key) -> pd.DataFrame`, `sdk.storage.dataframe.delete(key)`.
    - [ ] Usar Parquet como formato de serialización por defecto.
    - [ ] Actualizar backends.
  - [ ] **Sub-Tarea 2.3.3: Pruebas Unitarias para Nuevas Funcionalidades.**
  - [ ] **Sub-Tarea 2.3.4: Documentación Actualizada del Módulo `storage`.**

## Objetivo 3: Experiencia de Desarrollador (DX) y Herramientas

- [x] **Tarea 3.1: Crear un TauseStack CLI.**
  - [x] **Sub-Tarea 3.1.1: Comando `tausestack init`.**
    - [x] Generar estructura de proyecto base (con `main.py`, `app/`, `ROADMAP.md`, etc.).
    - [x] Configurar `pyproject.toml` con dependencias TauseStack.
    - [x] Opciones `--git`/`--no-git` y `--env`/`--no-env` implementadas.
  - [x] **Sub-Tarea 3.1.2: Comando `tausestack run`.**
    - [x] Iniciar el servidor de desarrollo FastAPI (uvicorn) con opciones `--host` y `--port`.
  - [x] **Sub-Tarea 3.1.3: Comando `tausestack deploy` (Base).**
    - [x] Implementación inicial del comando `deploy target <entorno>`.
    - [x] Añadida opción `--build` para construir imágenes Docker.
    - [ ] *Integración con herramientas de despliegue específicas (ej. Serverless Framework, Docker + ECS/Fargate) pendiente para futuro.*
- [ ] **Tarea 3.2: Documentación y Ejemplos Completos.**
  - [ ] Crear un proyecto de ejemplo completo (ej. una API de IA simple) que demuestre el uso de todos los componentes del framework y el SDK.
  - [ ] Mejorar la documentación en `README.md` de cada módulo del SDK y del framework general.

## Módulos del SDK Ya Implementados (Base)

- **`sdk.storage` (JSON):** Completado (S3, Local).
- **`sdk.secrets`:** Completado (AWS Secrets Manager, Env Vars).
- **`sdk.cache`:** Completado (Memory, Disk, Redis).
- **`sdk.notify`:** Completado (SES, Local File, Console).
