# SDK de Base de Datos TauseStack - Backend SQLAlchemy

El `SQLAlchemyBackend` proporciona una interfaz para interactuar con bases de datos relacionales utilizando SQLAlchemy de forma asíncrona. Permite realizar operaciones CRUD (Crear, Leer, Actualizar, Eliminar), gestionar transacciones de forma explícita o mediante un gestor de contexto, y ejecutar consultas SQL crudas para operaciones complejas o específicas de la base de datos.

## Uso Básico

Para utilizar `SQLAlchemyBackend`, necesitas definir tus modelos de datos Pydantic, tus modelos de tabla SQLAlchemy, y un mapeo entre ellos.

### 1. Definir Modelos Pydantic

Tus modelos Pydantic deben heredar de `tausestack.sdk.database.Model` (que es un alias de `pydantic.BaseModel` con configuración para `from_attributes=True` y un campo `id` opcional).

```python
# en tu_app/models_pydantic.py
from typing import Optional
from tausestack.sdk.database import Model, ItemID # ItemID es Union[int, str]

class UserPydantic(Model):
    id: Optional[ItemID] = None # Heredado de Model, pero puedes redefinirlo si es necesario
    username: str
    email: str
    is_active: bool = True

    # Config para Pydantic v2, ya incluido en sdk.database.Model
    # class Config:
    #     orm_mode = True # Pydantic v1
    #     from_attributes = True # Pydantic v2
```

### 2. Definir Modelos SQLAlchemy

Define tus tablas utilizando la base declarativa de SQLAlchemy.

```python
# en tu_app/models_sqla.py
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class UserSQLA(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
```

### 3. Crear el `model_mapping`

Este diccionario es esencial para que el backend sepa cómo convertir entre tus modelos Pydantic y SQLAlchemy.

```python
# en tu_app/database_setup.py
from .models_pydantic import UserPydantic
from .models_sqla import UserSQLA

model_mapping = {
    UserPydantic: UserSQLA,
    # ... otros mapeos de modelos ...
}
```

### 4. Inicializar `SQLAlchemyBackend`

Ahora puedes instanciar el backend.

```python
# en tu_app/database_setup.py
from sqlalchemy import MetaData
from tausestack.sdk.database import SQLAlchemyBackend
from .models_sqla import Base # La Base de tus modelos SQLAlchemy
# model_mapping definido arriba

DATABASE_URL = "sqlite+aiosqlite:///./test_app.db" # O tu URL de PostgreSQL, etc.

# La metadata de SQLAlchemy debe contener todas tus tablas
# Si usas la Base de declarative_base, su metadata es Base.metadata
sqla_metadata = Base.metadata 

db_backend = SQLAlchemyBackend(
    database_url=DATABASE_URL,
    metadata=sqla_metadata,
    model_mapping=model_mapping,
    echo=True # Opcional, para logging de SQL
)

async def main():
    await db_backend.connect()
    await db_backend.create_tables() # Crea las tablas si no existen

    # Ejemplo de uso:
    # new_user_data = {"username": "johndoe", "email": "john@example.com"}
    # created_user = await db_backend.create(UserPydantic, new_user_data)
    # print(f"Usuario creado: {created_user}")

    await db_backend.disconnect()

# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(main())
```

Con esta estructura, el `SQLAlchemyBackend` puede manejar la conversión entre los datos que recibe/devuelve (Pydantic) y cómo se almacenan (SQLAlchemy).

## Gestión de Transacciones

El `SQLAlchemyBackend` ofrece control sobre las transacciones de la base de datos, lo cual es crucial para asegurar la atomicidad de las operaciones.

### Control Manual de Transacciones

Puedes controlar las transacciones manualmente utilizando los siguientes métodos:

- `await db_backend.begin_transaction()`: Inicia una nueva transacción.
- `await db_backend.commit_transaction()`: Confirma los cambios realizados dentro de la transacción actual.
- `await db_backend.rollback_transaction()`: Revierte los cambios realizados dentro de la transacción actual.

```python
# Ejemplo de control manual de transacciones
async def manual_transaction_example():
    try:
        await db_backend.begin_transaction()
        user_data = {"username": "testuser_manual", "email": "manual@example.com"}
        created_user = await db_backend.create(UserPydantic, user_data)
        # ... otras operaciones ...
        await db_backend.commit_transaction()
        print(f"Usuario creado y transacción confirmada: {created_user}")
    except Exception as e:
        print(f"Error en la transacción, revirtiendo: {e}")
        await db_backend.rollback_transaction()
```

### Gestor de Contexto para Transacciones

Para un manejo más simple y seguro de las transacciones, puedes utilizar el gestor de contexto `transaction()`:

```python
# Ejemplo con gestor de contexto
async def context_manager_transaction_example():
    try:
        async with db_backend.transaction():
            user_data = {"username": "testuser_context", "email": "context@example.com"}
            created_user = await db_backend.create(UserPydantic, user_data)
            # ... otras operaciones ...
            # Si ocurre una excepción aquí, se hará rollback automáticamente
        print(f"Usuario creado, transacción confirmada automáticamente: {created_user}")
    except Exception as e:
        # La excepción se propaga después del rollback automático
        print(f"Error capturado fuera del contexto de transacción: {e}")
```

El gestor de contexto se encarga automáticamente de hacer `commit` si el bloque se completa sin errores, o `rollback` si ocurre cualquier excepción.

## Ejecución de SQL Crudo

Para situaciones donde necesitas ejecutar consultas SQL directamente (ej. consultas muy complejas, DDL, o funciones específicas de la base de datos), el backend proporciona los siguientes métodos:

### `fetch_all_raw(query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]`

Ejecuta una consulta SQL cruda y devuelve una lista de diccionarios, donde cada diccionario representa una fila.

```python
async def fetch_all_example():
    # Asegúrate de que la tabla 'users' y los datos existan
    query = "SELECT id, username, email FROM users WHERE is_active = :active ORDER BY username"
    params = {"active": True}
    active_users = await db_backend.fetch_all_raw(query, params)
    for user in active_users:
        print(f"Usuario activo: {user['username']} ({user['email']})")
```

### `fetch_one_raw(query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]`

Ejecuta una consulta SQL cruda y devuelve un único diccionario (la primera fila) o `None` si no hay resultados.

```python
async def fetch_one_example():
    query = "SELECT id, username FROM users WHERE email = :email"
    params = {"email": "john@example.com"}
    user = await db_backend.fetch_one_raw(query, params)
    if user:
        print(f"Usuario encontrado: {user['username']}")
    else:
        print("Usuario no encontrado.")
```

### `execute_raw(query: str, params: Optional[Dict[str, Any]] = None) -> Any`

Ejecuta una sentencia SQL cruda que no se espera que devuelva filas directamente (como `INSERT`, `UPDATE`, `DELETE`, o DDL). Para sentencias DML (Data Manipulation Language), devuelve el número de filas afectadas (`rowcount`). Para DDL (Data Definition Language) u otras sentencias, el valor de retorno puede variar según el driver de la base de datos (a menudo es -1 o None si `rowcount` no es aplicable).

```python
async def execute_update_example():
    # Suponiendo que el usuario con id 1 existe
    query = "UPDATE users SET is_active = :new_status WHERE id = :user_id"
    params = {"new_status": False, "user_id": 1}
    rows_affected = await db_backend.execute_raw(query, params)
    print(f"Filas afectadas por la actualización: {rows_affected}")

    # Ejemplo de creación de una tabla (DDL)
    # try:
    #     create_table_query = """
    #     CREATE TABLE IF NOT EXISTS audit_log (
    #         id SERIAL PRIMARY KEY,
    #         action VARCHAR(255) NOT NULL,
    #         timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
    #     );
    #     """
    #     await db_backend.execute_raw(create_table_query)
    #     print("Tabla 'audit_log' verificada/creada.")
    # except Exception as e:
    #     print(f"Error creando tabla 'audit_log': {e}")
```

**Nota de Seguridad:** Al usar SQL crudo, ten mucho cuidado con la inyección SQL. Utiliza siempre consultas parametrizadas (pasando valores a través del argumento `params`) en lugar de formatear cadenas SQL directamente con datos de entrada del usuario.

## Gestión de Migraciones con Alembic

Alembic es una herramienta de migración de bases de datos para SQLAlchemy. Permite gestionar la evolución del esquema de tu base de datos a medida que tu aplicación cambia. El SDK de TauseStack integra Alembic para facilitar este proceso con `SQLAlchemyBackend`.

### Estructura de Directorios

La configuración y los scripts de migración de Alembic para el SDK se encuentran en:
`tausestack/sdk/database/migrations_alembic/`

Dentro de este directorio, encontrarás:
- `alembic.ini`: Archivo principal de configuración de Alembic.
- `env.py`: Script que Alembic ejecuta para configurar el entorno de migración, incluyendo la conexión a la base de datos y la detección de metadatos de tus modelos.
- `versions/`: Directorio que contendrá los scripts de migración generados.

### Configuración Inicial (para usuarios del SDK)

Para utilizar Alembic con tus modelos y base de datos, necesitas:

1.  **Asegurar que Alembic está instalado**: Ya está incluido como dependencia del SDK TauseStack.
2.  **Definir tus Modelos SQLAlchemy**: Asegúrate de que tus modelos SQLAlchemy (como `UserSQLA` en el ejemplo anterior) hereden de una `Base` declarativa común (ej. `Base = declarative_base()`).
3.  **Establecer Variables de Entorno**: El `env.py` configurado en el SDK espera dos variables de entorno para funcionar correctamente:
    *   `TAUSESTACK_DATABASE_URL`: La URL de conexión a tu base de datos SQLAlchemy. Debe ser la misma que usarías para `SQLAlchemyBackend`.
        *   Ejemplo SQLite: `export TAUSESTACK_DATABASE_URL="sqlite+aiosqlite:///./mi_app.db"`
        *   Ejemplo PostgreSQL: `export TAUSESTACK_DATABASE_URL="postgresql+asyncpg://user:pass@host:port/dbname"`
    *   `TAUSESTACK_ALEMBIC_METADATA_TARGET`: La ruta de importación completa a tu objeto `MetaData` de SQLAlchemy. Este objeto `MetaData` es el que Alembic usará para detectar cambios en tus tablas.
        *   Si usas `Base = declarative_base()`, esto típicamente es `Base.metadata`.
        *   Ejemplo: `export TAUSESTACK_ALEMBIC_METADATA_TARGET="tu_app.modelos_sqla:Base.metadata"` (asumiendo que `Base` está en `tu_app/modelos_sqla.py`).
        *   O si tienes un objeto `MetaData` explícito: `export TAUSESTACK_ALEMBIC_METADATA_TARGET="tu_app.db_config:metadata_obj"`

### Comandos Comunes de Alembic

Los comandos de Alembic deben ejecutarse desde el directorio `tausestack/sdk/database/migrations_alembic/`. Asegúrate de que las variables de entorno mencionadas arriba estén definidas en tu sesión de terminal.

*   **Generar una nueva revisión (script de migración)**:
    Después de modificar tus modelos SQLAlchemy, ejecuta:
    ```bash
    alembic revision -m "descripcion_breve_del_cambio" --autogenerate
    ```
    Esto comparará tus modelos con el estado actual de la base de datos (según lo registrado por Alembic) y generará un nuevo script en el directorio `versions/`.

*   **Aplicar migraciones a la base de datos**:
    Para aplicar todas las migraciones pendientes hasta la última revisión (`head`):
    ```bash
    alembic upgrade head
    ```
    También puedes aplicar hasta una revisión específica: `alembic upgrade <revision_id>`

*   **Revertir migraciones**:
    Para revertir la última migración aplicada:
    ```bash
    alembic downgrade -1
    ```
    O para revertir a una revisión específica: `alembic downgrade <revision_id>`

*   **Ver el historial de migraciones**:
    ```bash
    alembic history
    ```

*   **Ver la revisión actual de la base de datos**:
    ```bash
    alembic current
    ```

### Flujo de Trabajo Típico

1.  **Modifica tus modelos SQLAlchemy** (ej. añadir una nueva tabla, una nueva columna, cambiar un tipo de dato).
2.  **Asegúrate de que las variables de entorno** `TAUSESTACK_DATABASE_URL` y `TAUSESTACK_ALEMBIC_METADATA_TARGET` estén correctamente configuradas.
3.  **Navega al directorio de migraciones**: `cd path/to/your_project/tausestack/sdk/database/migrations_alembic/`
4.  **Genera el script de migración**:
    ```bash
    alembic revision -m "añadida_columna_xyz_a_tabla_abc" --autogenerate
    ```
5.  **(Recomendado) Revisa el script de migración generado** en el directorio `versions/` para asegurarte de que los cambios son los esperados.
6.  **Aplica la migración a tu base de datos**:
    ```bash
    alembic upgrade head
    ```

### Notas Importantes

*   **Directorio de Ejecución**: Es crucial ejecutar los comandos de Alembic desde `tausestack/sdk/database/migrations_alembic/` porque `alembic.ini` está configurado con `script_location = .`, lo que significa que busca `env.py` y el directorio `versions/` de forma relativa a su propia ubicación.
*   **Autogeneración**: La función `--autogenerate` de Alembic es potente pero no perfecta. Siempre revisa los scripts generados, especialmente para operaciones complejas como cambios de nombre de tablas/columnas o alteraciones de restricciones que podrían no ser detectadas automáticamente o podrían requerir ajustes manuales.
*   **Bases de Datos Múltiples**: Si trabajas con múltiples bases de datos (ej. una para desarrollo, otra para producción), asegúrate de que `TAUSESTACK_DATABASE_URL` apunte a la base de datos correcta antes de ejecutar comandos de `upgrade` o `downgrade`.
*   **Trabajo en Equipo**: Cuando trabajes en equipo, coordina las migraciones. Después de obtener los últimos cambios del repositorio (que pueden incluir nuevas migraciones de otros desarrolladores), ejecuta `alembic upgrade head` para poner tu base de datos local al día.
