# Módulo de Autenticación del SDK de TauseStack (`tausestack.sdk.auth`)

## Visión General

El módulo `tausestack.sdk.auth` proporciona un sistema flexible y extensible para manejar la autenticación en aplicaciones construidas con TauseStack. Está diseñado para integrarse fácilmente con FastAPI y permite el uso de diferentes backends de autenticación.

Actualmente, incluye una implementación robusta para Firebase Authentication.

## Componentes Principales

### 1. `AbstractAuthBackend`
Es una clase base abstracta que define la interfaz para todos los backends de autenticación. Cualquier nuevo backend de autenticación (ej. para Auth0, JWT personalizado, etc.) debe heredar de esta clase e implementar sus métodos.

Métodos clave a implementar:
- `verify_token(token: str, request: Optional[Any] = None) -> VerifiedToken`: Verifica un token.
- `get_user_from_token(verified_token: VerifiedToken) -> Optional[User]`: Obtiene un usuario desde un token verificado.
- `get_user_by_id(user_id: str) -> Optional[User]`: Obtiene un usuario por su ID.
- `get_user_by_email(email: EmailStr) -> Optional[User]`: Obtiene un usuario por su email.
- `create_user(...) -> User`: Crea un nuevo usuario.
- `update_user(user_id: str, ...) -> User`: Actualiza un usuario existente.
- `delete_user(user_id: str) -> None`: Elimina un usuario.
- `set_custom_user_claims(user_id: str, claims: Dict[str, Any]) -> None`: Establece claims personalizados.

### 2. `FirebaseAuthBackend`
Una implementación concreta de `AbstractAuthBackend` que utiliza Firebase Admin SDK para gestionar la autenticación.

#### Configuración de `FirebaseAuthBackend`
Para usar `FirebaseAuthBackend`, necesitas inicializarlo con las credenciales de tu cuenta de servicio de Firebase. Esto se puede hacer de dos maneras al instanciar el backend:

1.  **Mediante la ruta a un archivo JSON de credenciales:**
    ```python
    from tausestack.sdk.auth.backends.firebase_admin import FirebaseAuthBackend

    auth_backend = FirebaseAuthBackend(service_account_key_path="/ruta/a/tu/firebase-credentials.json")
    ```

2.  **Mediante un diccionario con el contenido de las credenciales:**
    ```python
    from tausestack.sdk.auth.backends.firebase_admin import FirebaseAuthBackend

    credentials_dict = {
        "type": "service_account",
        "project_id": "tu-project-id",
        # ...otros campos de tus credenciales...
    }
    auth_backend = FirebaseAuthBackend(service_account_key_dict=credentials_dict)
    ```

Es recomendable gestionar estas credenciales de forma segura, por ejemplo, utilizando el módulo `tausestack.sdk.secrets` o variables de entorno.

El backend se configura globalmente (una vez por aplicación) y luego se recupera mediante `get_auth_backend()` donde sea necesario.

### 3. Modelo `User`
Un modelo Pydantic (`tausestack.sdk.auth.base.User`) que representa la información del usuario autenticado. Incluye campos estándar como `id`, `email`, `display_name`, `photo_url`, `disabled`, `custom_claims`, etc.

```python
class User(BaseModel):
    id: str
    email: Optional[EmailStr] = None
    email_verified: Optional[bool] = False
    # ... y otros campos
```

### 4. Dependencias FastAPI

El módulo proporciona dependencias listas para usar en tus rutas de FastAPI para proteger endpoints y obtener el usuario actual.

-   **`get_current_user`**:
    Exige un token Bearer válido. Si el token es válido y el usuario existe y está habilitado, devuelve el objeto `User`. De lo contrario, lanza una `HTTPException` apropiada (401, 403, 404).

    ```python
    from fastapi import FastAPI, Depends
    from tausestack.sdk.auth.main import get_current_user
    from tausestack.sdk.auth.base import User

    app = FastAPI()

    @app.get("/users/me")
    async def read_users_me(current_user: User = Depends(get_current_user)):
        return current_user
    ```

-   **`get_optional_current_user`**:
    Intenta autenticar al usuario si se proporciona un token Bearer. Si el token es válido, devuelve el objeto `User`. Si no se proporciona token, o si el token es inválido/usuario no encontrado/deshabilitado, devuelve `None` sin lanzar una excepción. Esto es útil para rutas que pueden ser accedidas por usuarios autenticados y anónimos.

    ```python
    from fastapi import FastAPI, Depends
    from tausestack.sdk.auth.main import get_optional_current_user
    from tausestack.sdk.auth.base import User
    from typing import Optional

    app = FastAPI()

    @app.get("/items/{item_id}")
    async def read_item(item_id: str, current_user: Optional[User] = Depends(get_optional_current_user)):
        if current_user:
            return {"item_id": item_id, "owner_id": current_user.id}
        return {"item_id": item_id, "owner_id": "anonymous"}
    ```

### Configuración del Backend de Autenticación
Para que las dependencias FastAPI funcionen, debes configurar qué backend de autenticación se utilizará. Esto se hace estableciendo la variable de entorno `TAUSESTACK_AUTH_BACKEND_TYPE`.

Actualmente, el valor soportado es:
- `TAUSESTACK_AUTH_BACKEND_TYPE="firebase"`

Además, para `FirebaseAuthBackend`, las credenciales deben estar disponibles, usualmente a través de variables de entorno que tu aplicación lee al inicializar el backend (por ejemplo, `GOOGLE_APPLICATION_CREDENTIALS` si usas un path, o variables específicas si pasas un diccionario).

La inicialización del backend y la configuración de la función `get_auth_backend` se manejan típicamente en el punto de entrada de tu aplicación (ej. `main.py`).

```python
# En tu main.py o un archivo de configuración
import os
from tausestack.sdk.auth.main import set_auth_backend_instance
from tausestack.sdk.auth.backends.firebase_admin import FirebaseAuthBackend

# Ejemplo de inicialización (ajusta según tu manejo de credenciales)
# Esto es una simplificación; en producción, carga credenciales de forma segura.
if os.getenv("TAUSESTACK_AUTH_BACKEND_TYPE") == "firebase":
    # Asume que las credenciales JSON están en una variable de entorno o archivo
    # Aquí deberías cargar tu service_account_key_dict o path de forma segura
    # Por ejemplo, desde tausestack.sdk.secrets o variables de entorno directas
    
    # Ejemplo simplificado si las credenciales están en un archivo apuntado por una variable de entorno:
    # firebase_creds_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY_PATH")
    # if firebase_creds_path:
    #     auth_backend_instance = FirebaseAuthBackend(service_account_key_path=firebase_creds_path)
    #     set_auth_backend_instance(auth_backend_instance)
    # else:
    #     # Manejar el caso donde las credenciales no están configuradas
    #     print("Advertencia: Credenciales de Firebase no configuradas para el backend de autenticación.")
    
    # O si usas un diccionario (ej. cargado desde variables de entorno individuales)
    # service_account_dict = load_firebase_credentials_from_env() # Implementa esta función
    # auth_backend_instance = FirebaseAuthBackend(service_account_key_dict=service_account_dict)
    # set_auth_backend_instance(auth_backend_instance)
    pass # La inicialización real debe hacerse en la app del usuario
```

**Nota:** La lógica exacta de inicialización del backend (`FirebaseAuthBackend` con sus credenciales) y la llamada a `set_auth_backend_instance` debe ser implementada por la aplicación que utiliza este SDK, típicamente al inicio.

## Excepciones

El módulo define excepciones personalizadas en `tausestack.sdk.auth.exceptions`:
- `AuthException`: Excepción base para errores de autenticación.
- `InvalidTokenException`: Para tokens inválidos, malformados o expirados.
- `UserNotFoundException`: Si el usuario no se encuentra.
- `AccountDisabledException`: Si la cuenta del usuario está deshabilitada.

Estas excepciones son capturadas por las dependencias FastAPI y convertidas en `HTTPException` con los códigos de estado y detalles apropiados.

## Futuras Mejoras
- Implementación de otros backends (ej. JWT, OAuth2).
- Funcionalidades adicionales como generación de enlaces para verificación de email o reseteo de contraseña.
