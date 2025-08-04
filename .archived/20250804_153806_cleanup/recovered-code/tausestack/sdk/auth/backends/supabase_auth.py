import jwt
import httpx
import json
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import os
import asyncio
from functools import lru_cache

from ..base import AbstractAuthBackend, User
from ..exceptions import (
    InvalidTokenException,
    UserNotFoundException,
    AuthException
)


class SupabaseVerifiedToken:
    """Token verificado de Supabase con claims incluidos."""
    
    def __init__(self, payload: Dict[str, Any]):
        self.payload = payload
        self.sub = payload.get("sub")  # user ID
        self.email = payload.get("email")
        self.email_verified = payload.get("email_verified", False)
        self.phone = payload.get("phone")
        self.role = payload.get("role", "authenticated")
        self.aud = payload.get("aud")
        self.exp = payload.get("exp")
        self.iat = payload.get("iat")
        self.app_metadata = payload.get("app_metadata", {})
        self.user_metadata = payload.get("user_metadata", {})


class SupabaseAuthBackend(AbstractAuthBackend):
    """Backend de autenticación para Supabase."""
    
    def __init__(self, supabase_url: Optional[str] = None, supabase_jwt_secret: Optional[str] = None):
        """
        Inicializa el backend de Supabase.
        
        Args:
            supabase_url: URL de tu proyecto Supabase
            supabase_jwt_secret: JWT secret para verificar tokens
        """
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.jwt_secret = supabase_jwt_secret or os.getenv("SUPABASE_JWT_SECRET")
        
        # Fallback a las credenciales hardcodeadas de desarrollo
        if not self.supabase_url:
            self.supabase_url = "https://vjoxmprmcbkmhwmbniaz.supabase.co"
        
        if not self.jwt_secret:
            # JWT secret del proyecto Supabase de desarrollo
            # En producción, deberías usar variables de entorno SUPABASE_JWT_SECRET
            self.jwt_secret = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZqb3htcHJtY2JrbWh3bWJuaWF6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MTU3Mzg3NCwiZXhwIjoyMDY3MTQ5ODc0fQ.PfU_xe38vl3wW1DQZaOp10p1HaM89Og-O0hYfJcgFBk"
        
        if not self.supabase_url:
            raise AuthException("SUPABASE_URL is required")
        
        self._jwks_cache = {}
        self._jwks_last_updated = None
    
    async def _get_jwks(self) -> Dict[str, Any]:
        """Obtiene las claves públicas de Supabase para verificar JWT."""
        try:
            # Supabase expone las claves públicas en /.well-known/jwks.json
            jwks_url = f"{self.supabase_url}/.well-known/jwks.json"
            
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(jwks_url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            raise AuthException(f"Error fetching JWKS from Supabase: {e}")
    
    @lru_cache(maxsize=10)
    def _get_jwt_secret_sync(self) -> str:
        """Obtiene el JWT secret de forma síncrona (para desarrollo)."""
        # En desarrollo, Supabase usa un JWT secret fijo
        # En producción, deberías obtener esto de las variables de entorno
        return self.jwt_secret
    
    async def verify_token(self, token: str, request: Optional[Any] = None) -> SupabaseVerifiedToken:
        """
        Verifica un token JWT de Supabase.
        """
        try:
            # Decodificar el token sin verificar primero para obtener el header
            unverified_payload = jwt.decode(token, options={"verify_signature": False})
            
            # Verificar el token con el secret real de Supabase
            payload = jwt.decode(
                token,
                self._get_jwt_secret_sync(),
                algorithms=["HS256"],
                audience="authenticated"
            )
            
            # Verificar expiración
            if "exp" in payload:
                exp_timestamp = payload["exp"]
                if datetime.now(timezone.utc).timestamp() > exp_timestamp:
                    raise InvalidTokenException("Token has expired")
            
            # Verificar que sea un token de usuario autenticado
            if payload.get("role") != "authenticated":
                raise InvalidTokenException("Token does not have authenticated role")
            
            return SupabaseVerifiedToken(payload)
            
        except jwt.ExpiredSignatureError:
            raise InvalidTokenException("Token has expired")
        except jwt.InvalidTokenError as e:
            raise InvalidTokenException(f"Invalid token: {e}")
        except Exception as e:
            raise AuthException(f"Error verifying token: {e}")
    
    async def get_user_from_token(self, verified_token: SupabaseVerifiedToken) -> Optional[User]:
        """
        Convierte un token verificado de Supabase en un objeto User.
        """
        try:
            payload = verified_token.payload
            
            # Extraer roles de app_metadata o user_metadata
            app_metadata = payload.get("app_metadata", {})
            user_metadata = payload.get("user_metadata", {})
            
            # Los roles pueden estar en diferentes lugares según la configuración
            roles = []
            if "roles" in app_metadata:
                roles = app_metadata["roles"]
            elif "roles" in user_metadata:
                roles = user_metadata["roles"]
            elif "role" in app_metadata:
                roles = [app_metadata["role"]]
            else:
                roles = ["user"]  # rol por defecto
            
            # Asegurar que roles sea una lista
            if isinstance(roles, str):
                roles = [roles]
            
            # Crear custom claims
            custom_claims = {
                "roles": roles,
                "app_metadata": app_metadata,
                "user_metadata": user_metadata
            }
            
            user = User(
                id=payload.get("sub"),
                email=payload.get("email"),
                email_verified=payload.get("email_verified", False),
                phone_number=payload.get("phone"),
                display_name=user_metadata.get("display_name") or user_metadata.get("name"),
                disabled=False,  # Supabase no tiene disabled por defecto
                custom_claims=custom_claims,
                created_at=payload.get("iat"),
                last_login_at=payload.get("iat")
            )
            
            return user
            
        except Exception as e:
            raise AuthException(f"Error extracting user from token: {e}")
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Obtiene un usuario por ID desde Supabase.
        Nota: Requiere configurar la API de Supabase.
        """
        # Para implementar esto completamente, necesitarías usar la API de Supabase
        # Por ahora, retorna None ya que no tenemos acceso directo a la base de datos
        return None
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Obtiene un usuario por email desde Supabase.
        Nota: Requiere configurar la API de Supabase.
        """
        # Para implementar esto completamente, necesitarías usar la API de Supabase
        return None
    
    async def create_user(self, **kwargs) -> User:
        """
        Crea un usuario en Supabase.
        Nota: Requiere configurar la API de Supabase.
        """
        raise NotImplementedError("User creation should be done through Supabase Auth API")
    
    async def update_user(self, user_id: str, **kwargs) -> User:
        """
        Actualiza un usuario en Supabase.
        Nota: Requiere configurar la API de Supabase.
        """
        raise NotImplementedError("User updates should be done through Supabase Auth API")
    
    async def delete_user(self, user_id: str) -> None:
        """
        Elimina un usuario de Supabase.
        Nota: Requiere configurar la API de Supabase.
        """
        raise NotImplementedError("User deletion should be done through Supabase Auth API")
    
    async def set_custom_user_claims(self, user_id: str, claims: Dict[str, Any]) -> None:
        """
        Establece claims personalizados para un usuario.
        Nota: En Supabase, esto se maneja a través de triggers de base de datos.
        """
        raise NotImplementedError("Custom claims should be set through Supabase database triggers") 