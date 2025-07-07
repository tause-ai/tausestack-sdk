# Ejemplo de integración entre módulos: Auth y Users

Este ejemplo muestra cómo el módulo de autenticación (`auth`) puede interactuar con el módulo de usuarios (`users`) para validar credenciales y obtener información de usuario.

---

## 1. Escenario típico: Login
Cuando un usuario intenta iniciar sesión:
1. El endpoint `/auth/login` recibe las credenciales.
2. El servicio de autenticación consulta el módulo `users` para buscar el usuario por nombre de usuario.
3. Si el usuario existe y la contraseña es válida, se genera un token.
4. Se retorna la información básica del usuario junto con el token.

## 2. Código de ejemplo

### Servicio de autenticación (simplificado)
```python
from core.modules.users.services.service import get_user_by_username
from core.modules.auth.services.tokens import create_token

def login(username: str, password: str):
    user = get_user_by_username(username)
    if not user:
        raise Exception("Usuario no encontrado")
    if not verify_password(password, user.hashed_password):
        raise Exception("Contraseña incorrecta")
    token = create_token(user)
    return {"access_token": token, "user": {"id": user.id, "username": user.username}}
```

### Test de integración
```python
def test_login_integration(monkeypatch):
    fake_user = type('User', (), {"id": 1, "username": "admin", "hashed_password": "hashed"})
    def mock_get_user_by_username(username):
        return fake_user if username == "admin" else None
    def mock_verify_password(password, hashed):
        return password == "admin" and hashed == "hashed"
    def mock_create_token(user):
        return "fake-token"
    monkeypatch.setattr("core.modules.users.services.service.get_user_by_username", mock_get_user_by_username)
    monkeypatch.setattr("core.modules.auth.services.service.verify_password", mock_verify_password)
    monkeypatch.setattr("core.modules.auth.services.tokens.create_token", mock_create_token)
    result = login("admin", "admin")
    assert result["access_token"] == "fake-token"
    assert result["user"]["username"] == "admin"
```

## 3. Notas
- Cada módulo mantiene su independencia, pero expone funciones públicas para ser utilizadas por otros módulos.
- La integración se prueba fácilmente con mocks en los tests.

---

Para más ejemplos y detalles, consulta la documentación de cada módulo y los tests de integración.
