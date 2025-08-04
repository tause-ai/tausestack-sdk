"""
External Auth para SDK External

Gestiona autenticación y autorización para builders externos
"""

import httpx
import jwt
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class UserRole(Enum):
    BUILDER = "builder"
    DEVELOPER = "developer"
    ADMIN = "admin"
    ENTERPRISE = "enterprise"


@dataclass
class ApiKey:
    id: str
    name: str
    key: str
    role: UserRole
    permissions: List[str]
    expires_at: Optional[str]
    created_at: str
    last_used: Optional[str]
    usage_count: int


@dataclass
class User:
    id: str
    email: str
    name: str
    role: UserRole
    organization: Optional[str]
    api_keys: List[str]
    created_at: str
    last_login: Optional[str]
    is_active: bool
    subscription_tier: str


@dataclass
class AuthToken:
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: User


class ExternalAuth:
    """
    Gestión de autenticación para builders externos
    """
    
    def __init__(self, base_url: str = "http://localhost:9001"):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "TauseStack-External-Auth/0.7.0"
            }
        )
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def login(self, email: str, password: str) -> AuthToken:
        """
        Login de usuario
        
        Args:
            email: Email del usuario
            password: Password del usuario
            
        Returns:
            AuthToken: Token de autenticación
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/auth/login",
                json={
                    "email": email,
                    "password": password
                }
            )
            response.raise_for_status()
            
            data = response.json()
            return AuthToken(
                access_token=data["access_token"],
                refresh_token=data["refresh_token"],
                token_type=data["token_type"],
                expires_in=data["expires_in"],
                user=User(
                    id=data["user"]["id"],
                    email=data["user"]["email"],
                    name=data["user"]["name"],
                    role=UserRole(data["user"]["role"]),
                    organization=data["user"].get("organization"),
                    api_keys=data["user"]["api_keys"],
                    created_at=data["user"]["created_at"],
                    last_login=data["user"].get("last_login"),
                    is_active=data["user"]["is_active"],
                    subscription_tier=data["user"]["subscription_tier"]
                )
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during login: {e.response.status_code}")
            raise Exception(f"Login failed: {e.response.text}")
        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            raise

    async def refresh_token(self, refresh_token: str) -> AuthToken:
        """
        Renovar token de acceso
        
        Args:
            refresh_token: Token de refresh
            
        Returns:
            AuthToken: Nuevo token de autenticación
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/auth/refresh",
                json={"refresh_token": refresh_token}
            )
            response.raise_for_status()
            
            data = response.json()
            return AuthToken(
                access_token=data["access_token"],
                refresh_token=data["refresh_token"],
                token_type=data["token_type"],
                expires_in=data["expires_in"],
                user=User(
                    id=data["user"]["id"],
                    email=data["user"]["email"],
                    name=data["user"]["name"],
                    role=UserRole(data["user"]["role"]),
                    organization=data["user"].get("organization"),
                    api_keys=data["user"]["api_keys"],
                    created_at=data["user"]["created_at"],
                    last_login=data["user"].get("last_login"),
                    is_active=data["user"]["is_active"],
                    subscription_tier=data["user"]["subscription_tier"]
                )
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error refreshing token: {e.response.status_code}")
            raise Exception(f"Token refresh failed: {e.response.text}")
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            raise

    async def create_api_key(self, access_token: str, name: str, permissions: List[str], expires_in_days: Optional[int] = None) -> ApiKey:
        """
        Crear nueva API key
        
        Args:
            access_token: Token de acceso del usuario
            name: Nombre de la API key
            permissions: Lista de permisos
            expires_in_days: Días hasta expiración (opcional)
            
        Returns:
            ApiKey: Nueva API key creada
        """
        try:
            payload = {
                "name": name,
                "permissions": permissions
            }
            if expires_in_days:
                payload["expires_in_days"] = expires_in_days
                
            response = await self.client.post(
                f"{self.base_url}/api/v1/auth/api-keys",
                json=payload,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            
            data = response.json()
            return ApiKey(
                id=data["id"],
                name=data["name"],
                key=data["key"],
                role=UserRole(data["role"]),
                permissions=data["permissions"],
                expires_at=data.get("expires_at"),
                created_at=data["created_at"],
                last_used=data.get("last_used"),
                usage_count=data["usage_count"]
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error creating API key: {e.response.status_code}")
            raise Exception(f"API key creation failed: {e.response.text}")
        except Exception as e:
            logger.error(f"Error creating API key: {str(e)}")
            raise

    async def list_api_keys(self, access_token: str) -> List[ApiKey]:
        """
        Listar API keys del usuario
        
        Args:
            access_token: Token de acceso del usuario
            
        Returns:
            List[ApiKey]: Lista de API keys
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/auth/api-keys",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            
            data = response.json()
            return [
                ApiKey(
                    id=key["id"],
                    name=key["name"],
                    key=key["key"][:8] + "..." if "key" in key else "***",  # Masked key
                    role=UserRole(key["role"]),
                    permissions=key["permissions"],
                    expires_at=key.get("expires_at"),
                    created_at=key["created_at"],
                    last_used=key.get("last_used"),
                    usage_count=key["usage_count"]
                )
                for key in data["api_keys"]
            ]
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error listing API keys: {e.response.status_code}")
            raise Exception(f"Failed to list API keys: {e.response.text}")
        except Exception as e:
            logger.error(f"Error listing API keys: {str(e)}")
            raise

    async def revoke_api_key(self, access_token: str, api_key_id: str) -> bool:
        """
        Revocar API key
        
        Args:
            access_token: Token de acceso del usuario
            api_key_id: ID de la API key a revocar
            
        Returns:
            bool: True si se revocó correctamente
        """
        try:
            response = await self.client.delete(
                f"{self.base_url}/api/v1/auth/api-keys/{api_key_id}",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return True
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error revoking API key: {e.response.status_code}")
            raise Exception(f"Failed to revoke API key: {e.response.text}")
        except Exception as e:
            logger.error(f"Error revoking API key: {str(e)}")
            raise

    async def verify_api_key(self, api_key: str) -> User:
        """
        Verificar API key y obtener información del usuario
        
        Args:
            api_key: API key a verificar
            
        Returns:
            User: Información del usuario
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/auth/verify",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            response.raise_for_status()
            
            data = response.json()
            return User(
                id=data["user"]["id"],
                email=data["user"]["email"],
                name=data["user"]["name"],
                role=UserRole(data["user"]["role"]),
                organization=data["user"].get("organization"),
                api_keys=data["user"]["api_keys"],
                created_at=data["user"]["created_at"],
                last_login=data["user"].get("last_login"),
                is_active=data["user"]["is_active"],
                subscription_tier=data["user"]["subscription_tier"]
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error verifying API key: {e.response.status_code}")
            raise Exception(f"API key verification failed: {e.response.text}")
        except Exception as e:
            logger.error(f"Error verifying API key: {str(e)}")
            raise

    async def get_user_profile(self, access_token: str) -> User:
        """
        Obtener perfil del usuario
        
        Args:
            access_token: Token de acceso
            
        Returns:
            User: Perfil del usuario
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/auth/profile",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            
            data = response.json()
            return User(
                id=data["id"],
                email=data["email"],
                name=data["name"],
                role=UserRole(data["role"]),
                organization=data.get("organization"),
                api_keys=data["api_keys"],
                created_at=data["created_at"],
                last_login=data.get("last_login"),
                is_active=data["is_active"],
                subscription_tier=data["subscription_tier"]
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting user profile: {e.response.status_code}")
            raise Exception(f"Failed to get user profile: {e.response.text}")
        except Exception as e:
            logger.error(f"Error getting user profile: {str(e)}")
            raise

    async def update_user_profile(self, access_token: str, updates: Dict[str, Any]) -> User:
        """
        Actualizar perfil del usuario
        
        Args:
            access_token: Token de acceso
            updates: Campos a actualizar
            
        Returns:
            User: Perfil actualizado
        """
        try:
            response = await self.client.put(
                f"{self.base_url}/api/v1/auth/profile",
                json=updates,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            
            data = response.json()
            return User(
                id=data["id"],
                email=data["email"],
                name=data["name"],
                role=UserRole(data["role"]),
                organization=data.get("organization"),
                api_keys=data["api_keys"],
                created_at=data["created_at"],
                last_login=data.get("last_login"),
                is_active=data["is_active"],
                subscription_tier=data["subscription_tier"]
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error updating user profile: {e.response.status_code}")
            raise Exception(f"Failed to update user profile: {e.response.text}")
        except Exception as e:
            logger.error(f"Error updating user profile: {str(e)}")
            raise

    def decode_jwt_token(self, token: str, secret: str) -> Dict[str, Any]:
        """
        Decodificar JWT token localmente
        
        Args:
            token: JWT token
            secret: Secret para verificar
            
        Returns:
            Dict: Payload del token
        """
        try:
            return jwt.decode(token, secret, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise Exception("Token has expired")
        except jwt.InvalidTokenError:
            raise Exception("Invalid token")

    def is_token_expired(self, token: str) -> bool:
        """
        Verificar si un token está expirado (sin verificar signature)
        
        Args:
            token: JWT token
            
        Returns:
            bool: True si está expirado
        """
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            exp = payload.get("exp")
            if exp:
                return datetime.utcnow().timestamp() > exp
            return False
        except:
            return True


# Utility functions

async def quick_login(email: str, password: str, base_url: str = "http://localhost:9001") -> str:
    """
    Login rápido que retorna solo el access token
    """
    async with ExternalAuth(base_url) as auth:
        token_data = await auth.login(email, password)
        return token_data.access_token


async def create_builder_api_key(
    access_token: str, 
    name: str = "TausePro Builder Key",
    base_url: str = "http://localhost:9001"
) -> str:
    """
    Crear API key para builder con permisos básicos
    """
    async with ExternalAuth(base_url) as auth:
        api_key = await auth.create_api_key(
            access_token=access_token,
            name=name,
            permissions=[
                "apps:create",
                "apps:read",
                "apps:update",
                "apps:delete",
                "templates:read",
                "deploy:create",
                "deploy:read"
            ]
        )
        return api_key.key 