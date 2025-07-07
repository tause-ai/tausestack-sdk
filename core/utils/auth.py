"""
Middleware y decorador para autenticación JWT en endpoints críticos.
Permite validar tokens, claims y restringir acceso a peers confiables.
"""
import os
from fastapi import Request, HTTPException
from functools import wraps
import jwt

def get_jwt_secret():
    return os.getenv("MCP_JWT_SECRET", "dummy_secret")
def get_jwt_algorithm():
    return os.getenv("MCP_JWT_ALGORITHM", "HS256")
def get_allowed_peers():
    val = os.getenv("MCP_ALLOWED_PEERS", "")
    return set(val.split(",")) if val else set()

# Decorador para proteger endpoints
def require_jwt(fn):
    @wraps(fn)
    def sync_wrapper(*args, **kwargs):
        request = args[0] if args and isinstance(args[0], Request) else kwargs.get('request')
        if request is None:
            raise HTTPException(status_code=400, detail="No se pudo obtener el request para autenticación JWT")
        auth = request.headers.get("Authorization")
        if not auth or not auth.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Token JWT requerido")
        token = auth.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, get_jwt_secret(), algorithms=[get_jwt_algorithm()])
            if "iss" not in payload or "exp" not in payload:
                raise HTTPException(status_code=401, detail="JWT inválido: claims faltantes")
            request.state.jwt_payload = payload
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"JWT inválido: {e}")
        return fn(*args, **kwargs)
    @wraps(fn)
    async def async_wrapper(*args, **kwargs):
        request = args[0] if args and isinstance(args[0], Request) else kwargs.get('request')
        if request is None:
            raise HTTPException(status_code=400, detail="No se pudo obtener el request para autenticación JWT")
        auth = request.headers.get("Authorization")
        if not auth or not auth.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Token JWT requerido")
        token = auth.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, get_jwt_secret(), algorithms=[get_jwt_algorithm()])
            if "iss" not in payload or "exp" not in payload:
                raise HTTPException(status_code=401, detail="JWT inválido: claims faltantes")
            request.state.jwt_payload = payload
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"JWT inválido: {e}")
        return await fn(*args, **kwargs)
    import inspect
    if inspect.iscoroutinefunction(fn):
        return async_wrapper
    else:
        return sync_wrapper

# Utilidad para validar peers confiables
def is_peer_allowed(url: str) -> bool:
    allowed_peers = get_allowed_peers()
    if not allowed_peers:
        return True  # Permitir todo si no está configurado
    for peer in allowed_peers:
        if url.startswith(peer):
            return True
    return False
