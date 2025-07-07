# TauseStack SDK

El SDK de TauseStack proporciona un conjunto de herramientas y utilidades para interactuar con diversos servicios de backend de una manera simplificada y configurable.

## Módulos Disponibles

Actualmente, el SDK incluye los siguientes módulos:

1.  **Storage (`sdk.storage`)**: Para almacenamiento de objetos JSON.
2.  **Secrets (`sdk.secrets`)**: Para la gestión segura de secretos.
3.  **Cache (`sdk.cache`)**: Para cachear resultados de funciones.
4.  **Notify (`sdk.notify`)**: Para enviar notificaciones (actualmente, correos electrónicos).

### 1. Módulo de Storage (`sdk.storage`)

Este módulo facilita el almacenamiento y la recuperación de objetos JSON y archivos binarios.

#### API (`sdk.storage.json`)

El cliente principal para JSON se accede a través de `sdk.storage.json`:

-   `sdk.storage.json.put(key: str, value: dict) -> None`:
    Almacena un objeto JSON (`value`) asociado a una `key`.
-   `sdk.storage.json.get(key: str) -> dict | None`:
    Recupera un objeto JSON por su `key`. Retorna `None` si la clave no existe.
-   `sdk.storage.json.delete(key: str) -> None`:
    Elimina un objeto JSON por su `key`.

#### API (`sdk.storage.dataframe`)

El cliente para DataFrames de pandas se accede a través de `sdk.storage.dataframe`.

**Nota**: Para utilizar esta funcionalidad, debes instalar las dependencias adicionales:
```bash
pip install tausestack[storage-df]
```

-   `sdk.storage.dataframe.put(key: str, value: pd.DataFrame) -> None`:
    Almacena un DataFrame (`value`) asociado a una `key` en formato Parquet.
-   `sdk.storage.dataframe.get(key: str) -> pd.DataFrame | None`:
    Recupera un DataFrame por su `key`. Retorna `None` si la clave no existe.
-   `sdk.storage.dataframe.delete(key: str) -> None`:
    Elimina un DataFrame por su `key`.

#### API (`sdk.storage.binary`)

El cliente para archivos binarios se accede a través de `sdk.storage.binary`:

-   `sdk.storage.binary.put(key: str, value: bytes, content_type: str | None = None) -> None`:
    Almacena datos binarios (`value`) asociados a una `key`. Opcionalmente, se puede especificar el `content_type` (MIME type), lo cual es útil para backends como S3.
-   `sdk.storage.binary.get(key: str) -> bytes | None`:
    Recupera los datos binarios por su `key`. Retorna `None` si la clave no existe.
-   `sdk.storage.binary.delete(key: str) -> None`:
    Elimina los datos binarios por su `key`.

#### Configuración

El backend de almacenamiento se configura mediante las siguientes variables de entorno:

-   `TAUSESTACK_STORAGE_BACKEND`: Especifica el backend a utilizar.
    -   `'local'` (default): Utiliza `LocalStorage`.
    -   `'s3'`: Utiliza `S3Storage`.
-   `TAUSESTACK_LOCAL_JSON_STORAGE_PATH`: (Para `LocalStorage`) Ruta base para archivos JSON. Default: `./.tausestack_storage/json`.
-   `TAUSESTACK_LOCAL_BINARY_STORAGE_PATH`: (Para `LocalStorage`) Ruta base para archivos binarios. Default: `./.tausestack_storage/binary`.
-   `TAUSESTACK_LOCAL_DATAFRAME_STORAGE_PATH`: (Para `LocalStorage`) Ruta base para DataFrames. Default: `./.tausestack_storage/dataframe`.
-   `TAUSESTACK_S3_BUCKET_NAME`: (Para `S3Storage`) Nombre del bucket S3 a utilizar.

#### Backends

-   **`LocalStorage`**: Almacena objetos JSON y archivos binarios en el sistema de archivos local.
-   **`S3Storage`**: Almacena objetos JSON, archivos binarios y DataFrames en un bucket de AWS S3. Requiere que `boto3` esté instalado (`pip install tausestack[storage-s3]`).

#### Ejemplo de Uso (JSON)

```python
from tausestack import sdk

# Almacenar un objeto
sdk.storage.json.put("mi_configuracion", {"usuario": "test", "activo": True})

# Recuperar un objeto
config = sdk.storage.json.get("mi_configuracion")
if config:
    print(f"Usuario: {config.get('usuario')}")

# Eliminar un objeto
sdk.storage.json.delete("mi_configuracion")
```

#### Ejemplo de Uso (Binario)

```python
from tausestack import sdk

# Crear datos binarios (ej. un archivo de texto simple)
binary_content = b"Este es el contenido de mi archivo binario."

# Almacenar el archivo
# El 'key' puede incluir una ruta y extension, p.ej. 'documentos/reporte.txt'
sdk.storage.binary.put("mi_archivo.bin", binary_content)

# Recuperar el archivo
retrieved_content = sdk.storage.binary.get("mi_archivo.bin")
if retrieved_content:
    print(retrieved_content.decode('utf-8'))

# Eliminar el archivo
sdk.storage.binary.delete("mi_archivo.bin")
```

#### Ejemplo de Uso (DataFrame)

```python
from tausestack import sdk
import pandas as pd

# Crear un DataFrame de ejemplo
df = pd.DataFrame({
    'columna1': [1, 2, 3],
    'columna2': ['A', 'B', 'C']
})

# Almacenar el DataFrame
sdk.storage.dataframe.put("mi_dataframe", df)

# Recuperar el DataFrame
retrieved_df = sdk.storage.dataframe.get("mi_dataframe")
if retrieved_df is not None:
    print(retrieved_df)

# Eliminar el DataFrame
sdk.storage.dataframe.delete("mi_dataframe")
```

### 2. Módulo de Secrets (`sdk.secrets`)

Este módulo permite acceder de forma segura a secretos y credenciales.

#### API (`sdk.secrets`)

-   `sdk.secrets.get(secret_name: str) -> str | None`:
    Recupera el valor de un secreto por su nombre. Retorna `None` si el secreto no se encuentra.

#### Configuración

El proveedor de secretos se configura mediante la siguiente variable de entorno:

-   `TAUSESTACK_SECRETS_BACKEND`: Especifica el proveedor a utilizar.
    -   `'env'` (default): Utiliza `EnvironmentVariablesProvider`.
    -   `'aws'`: Utiliza `AWSSecretsManagerProvider`.

#### Proveedores

-   **`EnvironmentVariablesProvider`**: Obtiene los secretos de las variables de entorno del sistema.
-   **`AWSSecretsManagerProvider`**: Obtiene los secretos desde AWS Secrets Manager. Requiere que `boto3` esté instalado (`pip install boto3`). La región de AWS se determina a través de la configuración estándar de Boto3 (variables de entorno `AWS_REGION`, `AWS_DEFAULT_REGION`, o configuración del perfil).

#### Ejemplo de Uso

```python
from tausestack import sdk
import os

# Asumiendo que TAUSESTACK_SECRETS_BACKEND='env'
# y la variable de entorno MI_API_KEY está definida
# os.environ['MI_API_KEY'] = 'supersecreto123'

api_key = sdk.secrets.get("MI_API_KEY")
if api_key:
    print(f"API Key obtenida: {api_key[:4]}...")
else:
    print("API Key no encontrada.")
```

### 3. Módulo de Cache (`sdk.cache`)

Este módulo proporciona un decorador para cachear los resultados de funciones, ayudando a mejorar el rendimiento al evitar recálculos costosos.

#### API (`sdk.cache`)

La funcionalidad principal se accede a través del decorador `@sdk.cache.cached()`:

-   `@sdk.cache.cached(ttl: int | float, backend: Optional[str] = None, backend_config: Optional[Dict[str, Any]] = None)`:
    Decora una función para que sus resultados sean cacheados.
    -   `ttl`: Tiempo de vida (Time-To-Live) para la entrada de caché en segundos. Un valor de `0` significa cachear indefinidamente (si el backend lo soporta).
    -   `backend`: Nombre del backend de caché a utilizar (e.g., `'memory'`, `'disk'`, `'redis'`). Si es `None`, se utiliza el backend configurado por defecto.
    -   `backend_config`: Un diccionario con configuraciones específicas para el backend. Las opciones comunes incluyen:
        -   Para todos los backends: `default_ttl` (sobrescribe el TTL del backend para esta instancia si `ttl` del decorador no se usa directamente).
        -   Para `'disk'`: `base_path` (str, ruta al directorio de caché en disco).
        -   Para `'redis'`: `redis_url` (str, URL de conexión a Redis), `redis_prefix` (str, prefijo para las claves en Redis).

#### Configuración

El comportamiento del módulo de caché se puede configurar mediante las siguientes variables de entorno:

-   `TAUSESTACK_CACHE_DEFAULT_BACKEND`: Especifica el backend de caché por defecto.
    -   `'memory'` (default): Utiliza `MemoryCacheBackend`.
    -   `'disk'`: Utiliza `DiskCacheBackend`.
    -   `'redis'`: Utiliza `RedisCacheBackend`.
-   `TAUSESTACK_DISK_CACHE_PATH`: (Para `DiskCacheBackend`) Ruta base en el sistema de archivos donde se almacenarán los archivos de caché. Default: `./.tausestack_cache/disk`.
-   `TAUSESTACK_REDIS_URL`: (Para `RedisCacheBackend`) URL de conexión al servidor Redis. Default: `redis://localhost:6379/0`.

#### Backends

-   **`MemoryCacheBackend`**: Almacena los datos en memoria usando `cachetools.TTLCache`. Es el más rápido pero los datos se pierden al finalizar el proceso.
-   **`DiskCacheBackend`**: Almacena los datos en archivos en el disco local, serializados con `pickle`. Persiste entre ejecuciones del programa.
-   **`RedisCacheBackend`**: Almacena los datos en un servidor Redis, serializados con `pickle`. Requiere que el paquete `redis` esté instalado (`pip install redis`).

#### Ejemplo de Uso

```python
from tausestack import sdk
import time

@sdk.cache.cached(ttl=60) # Cachea por 60 segundos usando el backend por defecto
def funcion_costosa(parametro1: str, parametro2: int) -> str:
    print(f"Ejecutando función costosa con {parametro1}, {parametro2}...")
    time.sleep(2) # Simula trabajo
    return f"Resultado para {parametro1}-{parametro2}"

# Primera llamada: se ejecuta la función
print(funcion_costosa("A", 1))

# Segunda llamada (dentro de los 60s): se retorna el resultado cacheado
print(funcion_costosa("A", 1))

# Ejemplo con backend de disco y TTL infinito
@sdk.cache.cached(ttl=0, backend='disk', backend_config={'base_path': '/tmp/my_app_cache'})
def otra_funcion(id_usuario: int):
    print(f"Calculando datos permanentes para el usuario {id_usuario}")
    return {"id": id_usuario, "datos": "muy importantes"}

print(otra_funcion(123))
print(otra_funcion(123)) # Debería ser cacheado en disco
```

### 4. Módulo de Notify (`sdk.notify`)

Este módulo permite enviar notificaciones, comenzando con correos electrónicos.

#### API (`sdk.notify`)

La funcionalidad principal para enviar correos se accede a través de `sdk.notify.email()`:

-   `sdk.notify.email(to: Union[str, List[str]], subject: str, body_text: Optional[str] = None, body_html: Optional[str] = None, backend: Optional[str] = None, backend_config: Optional[Dict[str, Any]] = None, **kwargs: Any) -> bool`:
    Envía un correo electrónico.
    -   `to`: Destinatario (string) o lista de destinatarios (lista de strings).
    -   `subject`: Asunto del correo.
    -   `body_text`: Cuerpo del correo en formato de texto plano.
    -   `body_html`: Cuerpo del correo en formato HTML. Se debe proporcionar `body_text` o `body_html`.
    -   `backend`: Nombre del backend a utilizar (e.g., `'console'`, `'ses'`, `'smtp'`). Si es `None`, se utiliza el backend configurado por defecto.
    -   `backend_config`: Un diccionario con configuraciones específicas para el backend (actualmente no se usa para `'console'`).
    -   `**kwargs`: Argumentos adicionales para pasar al método `send` del backend.
    -   Retorna `True` si el envío fue exitoso (o simulado exitosamente), `False` en caso contrario.

#### Configuración

El comportamiento del módulo de notificación se puede configurar mediante las siguientes variables de entorno:

-   `TAUSESTACK_NOTIFY_BACKEND`: Especifica el backend de notificación por defecto.
    -   `'console'` (default): Utiliza `ConsoleNotifyBackend`.
    -   `'local_file'`: Utiliza `LocalFileNotifyBackend`.
    -   `'ses'`: Utiliza `SESNotifyBackend`.

#### Backends

-   **`ConsoleNotifyBackend`**: Imprime los detalles del correo electrónico en la salida estándar (consola). Es útil para desarrollo y pruebas, ya que no envía correos reales ni requiere configuración adicional.

-   **`LocalFileNotifyBackend`**: Guarda cada notificación como un archivo en el sistema de ficheros local. El contenido del correo (destinatario, asunto, cuerpo, y cualquier `kwargs` adicional) se escribe en un archivo de texto (`.txt`) o HTML (`.html` si se proporciona `body_html`).

    -   **Ruta de almacenamiento**: Los archivos se guardan en el directorio especificado por la variable de entorno `TAUSESTACK_NOTIFY_LOCAL_FILE_PATH`, o en `./.tausestack_notifications` si la variable no está definida.
    -   **Nombre de archivo**: Se genera un nombre de archivo único utilizando un timestamp y una versión sanitizada del asunto del correo.

    Es útil para desarrollo, pruebas, o para mantener un registro persistente de las notificaciones enviadas en un entorno local sin depender de servicios externos.

-   **`SESNotifyBackend`**: Envía correos electrónicos utilizando AWS Simple Email Service (SES). Requiere que el paquete `boto3` esté instalado y que las credenciales de AWS estén configuradas correctamente en el entorno (o pasadas explícitamente).

    -   **Variables de Entorno para Configuración Básica:**
        -   `TAUSESTACK_NOTIFY_BACKEND=ses`: Activa este backend.
        -   `TAUSESTACK_NOTIFY_SES_SOURCE_EMAIL`: (Requerido) La dirección de correo electrónico verificada en SES que se usará como remitente.
        -   `TAUSESTACK_NOTIFY_SES_AWS_REGION`: (Opcional) La región de AWS donde se encuentra configurado SES. Si no se especifica, se usará la región por defecto configurada para `boto3`.
        -   También se respetarán las variables estándar de AWS para credenciales (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`) si `boto3` las necesita y no se usan roles IAM.

    -   **Configuración Avanzada (vía `backend_config` en `sdk.notify.email()`):

        Al llamar a `sdk.notify.email()`, puedes pasar un diccionario `backend_config` para sobrescribir o proveer parámetros específicos para la instancia de `SESNotifyBackend`:

        ```python
        sdk.notify.email(
            to="recipient@example.com",
            subject="Asunto Importante",
            body_text="Contenido del correo.",
            backend='ses', # Opcional si ya es el backend por defecto
            backend_config={
                "source_email": "custom_sender@example.com", # Debe estar verificado en SES
                "aws_region": "eu-west-1",
                "aws_access_key_id": "YOUR_ACCESS_KEY", # No recomendado para producción, preferir roles IAM o variables de entorno seguras
                "aws_secret_access_key": "YOUR_SECRET_KEY" # No recomendado para producción
            }
        )
        ```

    -   **Requisitos:**
        -   Paquete `boto3` instalado (`pip install boto3`).
        -   Credenciales de AWS configuradas (variables de entorno, archivo `~/.aws/credentials`, roles IAM, etc.).
        -   La dirección de correo electrónico especificada en `TAUSESTACK_NOTIFY_SES_SOURCE_EMAIL` (o `source_email` en `backend_config`) debe estar verificada en AWS SES.

#### Ejemplo de Uso

```python
from tausestack import sdk

# Enviar un correo simple usando el backend por defecto (consola)
success = sdk.notify.email(
    to='test@example.com',
    subject='Prueba de Notificación',
    body_text='Este es un correo de prueba desde el SDK de TauseStack.'
)

if success:
    print("Correo (simulado) enviado exitosamente.")
else:
    print("Falló el envío del correo (simulado).")

# Enviar a múltiples destinatarios con cuerpo HTML
success_html = sdk.notify.email(
    to=['user1@example.com', 'user2@example.com'],
    subject='Notificación HTML Importante',
    body_html='<h1>Título Importante</h1><p>Este es un mensaje con <b>formato HTML</b>.</p>'
)
```

### 5. Módulo de Autenticación (`sdk.auth`)

Este módulo proporciona funcionalidades para la autenticación de usuarios y la protección de rutas en aplicaciones FastAPI, integrándose con backends de autenticación como Firebase.

#### Modelos de Datos

-   **`User`**: Representa al usuario autenticado. Sus campos principales incluyen:
    -   `uid: str`: Identificador único del usuario.
    -   `email: Optional[str]`: Dirección de correo electrónico.
    -   `display_name: Optional[str]`: Nombre para mostrar.
    -   `photo_url: Optional[str]`: URL de la foto de perfil.
    -   `disabled: bool`: Indica si la cuenta está deshabilitada.
    -   `email_verified: bool`: Indica si el correo ha sido verificado.
    -   `provider_data: Dict[str, Any]`: Datos específicos del proveedor (ej. Firebase).
    -   `custom_claims: Dict[str, Any]`: Reclamaciones personalizadas asociadas al token del usuario.
    -   `roles: List[str]`: Lista de roles del usuario, extraída de `custom_claims['roles']` (si existe).

#### Backends de Autenticación

-   **`AbstractAuthBackend`**: Define la interfaz para los backends de autenticación, asegurando que implementen métodos como `verify_token`, `get_user`, `create_user`, `update_user`, y `delete_user`.
-   **`FirebaseAuthBackend`**: Implementación para Firebase Authentication.
    -   **Inicialización y Credenciales**: El backend se inicializa automáticamente al primer uso. Las credenciales de Firebase Admin se cargan con la siguiente prioridad:
        1.  Argumentos directos pasados al constructor (si se instancia manualmente: `credentials_path`, `credentials_dict`, `project_id`).
        2.  Variable de entorno `TAUSESTACK_FIREBASE_SA_KEY_PATH`: Ruta a un archivo JSON de cuenta de servicio.
        3.  Variable de entorno `TAUSESTACK_FIREBASE_SA_KEY_JSON`: Nombre de un secreto (gestionado por `sdk.secrets`) que contiene el contenido del archivo JSON de la cuenta de servicio.
        4.  Variable de entorno `GOOGLE_APPLICATION_CREDENTIALS` (estándar de Google Cloud).
        5.  Credenciales de ambiente de Google Cloud (si la aplicación se ejecuta en GCP con una cuenta de servicio asociada).
        -   El `project_id` de Firebase se puede especificar con `TAUSESTACK_FIREBASE_PROJECT_ID` si no se puede inferir de las credenciales.
    -   Internamente, el backend utiliza nombres de aplicación Firebase únicos (ej. `tausestack-firebase-app-<uuid>`) para evitar conflictos si múltiples instancias o la app por defecto de Firebase ya están inicializadas.

#### Dependencias de FastAPI para Rutas

Estas dependencias facilitan la protección de rutas en FastAPI:

-   **`get_current_user`**: `current_user: User = Depends(get_current_user)`
    -   Verifica el token `Authorization: Bearer <token>` de la cabecera.
    -   Obtiene la información del usuario desde el backend de autenticación configurado.
    -   Lanza `HTTPException(status_code=401, detail="Not authenticated")` si el token falta, es inválido, o el usuario no se encuentra.
    -   Lanza `HTTPException(status_code=403, detail="Account disabled")` si la cuenta del usuario está deshabilitada.

-   **`get_optional_current_user`**: `current_user: Optional[User] = Depends(get_optional_current_user)`
    -   Similar a `get_current_user`, pero si el token es inválido o no se proporciona, devuelve `None` en lugar de lanzar una excepción. Útil para rutas que pueden ser accedidas por usuarios autenticados y anónimos.

-   **`require_user`**: `current_user: User = Depends(require_user(required_roles: Optional[List[str]] = None))`
    -   Combina la funcionalidad de `get_current_user` con la verificación de roles.
    -   Si se proporciona `required_roles` (ej. `["admin", "editor"]`), verifica que el usuario tenga al menos uno de los roles especificados.
    -   Los roles del usuario se esperan en `user.custom_claims['roles']` como una lista de strings.
    -   Lanza `HTTPException(status_code=403, detail="Insufficient permissions")` si el usuario no cumple con los roles requeridos.

#### Excepciones Personalizadas del SDK

El módulo `sdk.auth` puede lanzar las siguientes excepciones específicas (además de las `HTTPException` en las dependencias):

-   `AuthException`: Excepción base para errores de autenticación.
-   `InvalidTokenException`: El token proporcionado es inválido o ha expirado.
-   `UserNotFoundException`: El usuario asociado al token no se encuentra en el backend.
-   `AccountDisabledException`: La cuenta del usuario está deshabilitada.
-   `AuthenticationBackendNotConfigured`: No se ha configurado un backend de autenticación.

#### Configuración (Variables de Entorno)

-   `TAUSESTACK_AUTH_BACKEND`: Especifica el backend de autenticación a utilizar.
    -   `'firebase'` (default): Utiliza `FirebaseAuthBackend`.
-   `TAUSESTACK_FIREBASE_SA_KEY_PATH`: Ruta al archivo JSON de la cuenta de servicio de Firebase.
-   `TAUSESTACK_FIREBASE_SA_KEY_JSON`: Nombre del secreto (gestionado por `sdk.secrets`) que contiene el JSON de la cuenta de servicio.
-   `TAUSESTACK_FIREBASE_PROJECT_ID`: (Opcional) ID del proyecto Firebase. Útil si no se puede inferir de las credenciales.

#### Ejemplo de Uso

```python
from fastapi import FastAPI, Depends
from typing import Optional
from tausestack.sdk.auth import get_current_user, get_optional_current_user, require_user
from tausestack.sdk.auth.models import User

app = FastAPI()

@app.get("/public")
async def public_route():
    return {"message": "Esta ruta es pública"}

@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.get("/admin/dashboard")
async def admin_dashboard(current_user: User = Depends(require_user(required_roles=["admin"]))):
    return {"message": f"Bienvenido al panel de admin, {current_user.display_name}!"}

@app.get("/profile/info")
async def get_profile_info(current_user: Optional[User] = Depends(get_optional_current_user)):
    if current_user:
        return {"message": f"Información para {current_user.uid}", "email": current_user.email}
    return {"message": "Información para usuarios anónimos"}

# Para ejecutar este ejemplo:
# 1. Configura tus variables de entorno para Firebase (ej. TAUSESTACK_FIREBASE_SA_KEY_PATH).
# 2. Instala FastAPI y Uvicorn: pip install fastapi uvicorn
# 3. Guarda el código como main.py y ejecuta: uvicorn main:app --reload
# 4. Realiza peticiones con un Bearer token válido en la cabecera Authorization.
```

## Logging en el SDK

El SDK de TauseStack utiliza el módulo `logging` estándar de Python para registrar información sobre sus operaciones y posibles errores.

### Configuración por Defecto

Por defecto, el logger principal del SDK (`tausestack.sdk`) y sus loggers hijos están configurados con un `logging.NullHandler()`. Esto significa que, a menos que la aplicación que utiliza el SDK configure explícitamente los handlers de logging, no se mostrará ninguna salida de log del SDK. Esta es una práctica recomendada para bibliotecas, ya que evita la contaminación de la salida de la consola o logs de la aplicación si no se desea.

### Habilitar Logs del SDK

Para ver los logs del SDK, la aplicación consumidora debe configurar el sistema de `logging` de Python. Aquí hay un ejemplo básico de cómo habilitar logs a nivel `DEBUG` para el SDK y enviarlos a la consola:

```python
import logging

# Configurar el logger raíz de la aplicación (o un logger específico)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Obtener y configurar el logger del SDK
sdk_logger = logging.getLogger('tausestack.sdk')
sdk_logger.setLevel(logging.DEBUG)
sdk_logger.addHandler(console_handler)
sdk_logger.propagate = False # Opcional: evitar que los logs se propaguen al logger raíz si ya tiene un handler

# Ahora, al usar el SDK, los logs se mostrarán
# from tausestack import sdk
# sdk.storage.json.get("test_key") # Esto generará logs
```

### Loggers Clave

Puedes configurar la verbosidad y los handlers para loggers específicos dentro del SDK si necesitas un control más granular:

-   `tausestack.sdk`: Logger raíz para todo el SDK.
-   `tausestack.sdk.storage.main`: Logs relacionados con el cliente `JsonClient` y la selección del backend de almacenamiento.
-   `tausestack.sdk.storage.backends`: Logs específicos de los backends `LocalJsonStorage` y `S3JsonStorage`.
-   `tausestack.sdk.secrets.main`: Logs relacionados con la función `get_secret` y la selección del proveedor de secretos.
-   `tausestack.sdk.secrets.providers`: Logs específicos de los proveedores `EnvironmentVariablesProvider` y `AWSSecretsManagerProvider`.
-   `tausestack.sdk.notify.main`: Logs relacionados con la función `send_email` y la selección del backend de notificación.
-   `tausestack.sdk.notify.backends`: Logs específicos de los backends de notificación (e.g., `ConsoleNotifyBackend`).
-   `tausestack.sdk.cache.main`: Logs relacionados con el decorador `@cached` y la selección/gestión de backends de caché.
-   `tausestack.sdk.cache.backends`: Logs específicos de `MemoryCacheBackend`, `DiskCacheBackend` y `RedisCacheBackend`.

## Dependencias

-   Para utilizar las funcionalidades que interactúan con AWS (`S3JsonStorage`, `AWSSecretsManagerProvider`), necesitarás instalar `boto3`:
    ```bash
    pip install boto3
    ```
-   Para utilizar `RedisCacheBackend` en el módulo `cache`, necesitarás instalar `redis`:
    ```bash
    pip install redis
    ```
-   Si deseas ejecutar las pruebas para `RedisCacheBackend` (que usan `fakeredis`), instala:
    ```bash
    pip install fakeredis
    ```
