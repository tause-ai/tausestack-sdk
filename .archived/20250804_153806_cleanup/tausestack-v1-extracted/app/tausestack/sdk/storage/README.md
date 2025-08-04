# TauseStack Storage SDK

El módulo de storage de TauseStack proporciona una interfaz unificada para almacenar y recuperar datos en diferentes formatos y backends.

## Características

- **Múltiples formatos**: JSON, Binary, DataFrame (pandas)
- **Múltiples backends**: Local, AWS S3, GCS, Supabase
- **Validación de seguridad**: Prevención de path traversal
- **Interfaz unificada**: Una sola clase para todos los tipos de storage

## Uso Básico

### StorageManager - Interfaz Principal

```python
from tausestack.sdk.storage.main import StorageManager

# Crear manager con backend por defecto (configurado por variables de entorno)
storage = StorageManager()

# O con un backend específico
from tausestack.sdk.storage.backends import LocalStorage
backend = LocalStorage()
storage = StorageManager(backend=backend)
```

### Operaciones JSON

```python
# Guardar datos JSON
user_data = {
    "id": 123,
    "name": "Juan Pérez",
    "email": "juan@example.com",
    "preferences": {
        "theme": "dark",
        "language": "es"
    }
}
storage.put_json("users/123", user_data)

# Recuperar datos JSON
user = storage.get_json("users/123")
print(user["name"])  # "Juan Pérez"

# Eliminar datos JSON
storage.delete_json("users/123")
```

### Operaciones Binarias

```python
# Guardar archivo binario
with open("imagen.jpg", "rb") as f:
    image_data = f.read()

storage.put_binary("images/profile/123.jpg", image_data, content_type="image/jpeg")

# Recuperar archivo binario
image_data = storage.get_binary("images/profile/123.jpg")

# Guardar en archivo
with open("downloaded_image.jpg", "wb") as f:
    f.write(image_data)

# Eliminar archivo
storage.delete_binary("images/profile/123.jpg")
```

### Operaciones DataFrame (requiere pandas)

```python
import pandas as pd

# Crear DataFrame
df = pd.DataFrame({
    "nombre": ["Ana", "Luis", "María"],
    "edad": [25, 30, 28],
    "ciudad": ["Madrid", "Barcelona", "Valencia"]
})

# Guardar DataFrame
storage.put_dataframe("analytics/users_data", df)

# Recuperar DataFrame
df_loaded = storage.get_dataframe("analytics/users_data")
print(df_loaded.head())

# Eliminar DataFrame
storage.delete_dataframe("analytics/users_data")
```

### Acceso a Clientes Específicos

```python
# Acceso directo a clientes específicos
json_client = storage.json
binary_client = storage.binary
dataframe_client = storage.dataframe  # Puede ser None si pandas no está instalado

# Usar clientes directamente
json_client.put("config/app", {"version": "1.0"})
data = json_client.get("config/app")
```

## Configuración de Backends

### Local Storage (por defecto)

```bash
# Variables de entorno opcionales
export TAUSESTACK_STORAGE_BACKEND=local
export TAUSESTACK_LOCAL_JSON_STORAGE_PATH=./data/json
export TAUSESTACK_LOCAL_BINARY_STORAGE_PATH=./data/binary
export TAUSESTACK_LOCAL_DATAFRAME_STORAGE_PATH=./data/dataframes
```

### AWS S3

```bash
# Variables de entorno requeridas
export TAUSESTACK_STORAGE_BACKEND=s3
export TAUSESTACK_S3_BUCKET_NAME=mi-bucket
export AWS_ACCESS_KEY_ID=tu-access-key
export AWS_SECRET_ACCESS_KEY=tu-secret-key
export AWS_DEFAULT_REGION=us-west-2
```

```python
# O programáticamente
from tausestack.sdk.storage.backends import S3Storage
backend = S3Storage(bucket_name="mi-bucket")
storage = StorageManager(backend=backend)
```

## Validación de Claves

Todas las claves son validadas por seguridad:

```python
# Claves válidas
storage.put_json("users/123", data)           # ✅
storage.put_json("files/docs/report.pdf", data)  # ✅
storage.put_json("config_v2.json", data)      # ✅

# Claves inválidas (lanzan ValueError)
storage.put_json("../etc/passwd", data)       # ❌ Path traversal
storage.put_json("/absolute/path", data)      # ❌ Path absoluto
storage.put_json("bad*name", data)            # ❌ Caracteres especiales
storage.put_json("space file", data)          # ❌ Espacios
```

## Manejo de Errores

```python
try:
    data = storage.get_json("users/999")
    if data is None:
        print("Usuario no encontrado")
except ValueError as e:
    print(f"Clave inválida: {e}")
except Exception as e:
    print(f"Error de storage: {e}")
```

## Serializers

El módulo también incluye funciones de serialización para casos avanzados:

```python
from tausestack.sdk.storage.serializers import (
    serialize_json, deserialize_json,
    serialize_text, deserialize_text,
    serialize_dataframe, deserialize_dataframe
)

# Serializar manualmente
json_bytes = serialize_json({"key": "value"})
text_bytes = serialize_text("Hola mundo")

# Deserializar
data = deserialize_json(json_bytes)
text = deserialize_text(text_bytes)
```

## Backends Disponibles

- **LocalStorage**: Almacenamiento en sistema de archivos local
- **S3Storage**: AWS S3 (requiere `boto3`)
- **GCSStorage**: Google Cloud Storage (en desarrollo)
- **SupabaseStorage**: Supabase Storage (en desarrollo)

## Instalación de Dependencias Opcionales

```bash
# Para AWS S3
pip install tausestack[storage-s3]

# Para Google Cloud Storage
pip install tausestack[storage-gcs]

# Para Supabase
pip install tausestack[storage-supabase]

# Para DataFrames
pip install tausestack[dataframes]

# Todo incluido
pip install tausestack[full]
``` 