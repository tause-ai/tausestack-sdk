from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

from pydantic import BaseModel, EmailStr, HttpUrl


# Modelo Pydantic para la información del usuario
class User(BaseModel):
    id: str  # UID del proveedor de autenticación (ej. Firebase UID)
    email: Optional[EmailStr] = None
    email_verified: Optional[bool] = False
    phone_number: Optional[str] = None
    display_name: Optional[str] = None
    photo_url: Optional[HttpUrl] = None
    disabled: Optional[bool] = False
    custom_claims: Optional[Dict[str, Any]] = {}
    provider_data: Optional[List[Dict[str, Any]]] = [] # Datos específicos del proveedor
    created_at: Optional[int] = None # Timestamp de creación
    last_login_at: Optional[int] = None # Timestamp del último login


# Tipo genérico para el token verificado, puede variar según el backend
VerifiedToken = TypeVar("VerifiedToken")


class AbstractAuthBackend(ABC, Generic[VerifiedToken]):
    """
    Interfaz abstracta para los backends de autenticación.
    Define los métodos que cada backend debe implementar.
    """

    @abstractmethod
    async def verify_token(self, token: str, request: Optional[Any] = None) -> VerifiedToken:
        """
        Verifica un token de autenticación.
        El 'request' es opcional y puede ser usado por backends que necesiten
        información adicional de la solicitud (ej. FastAPI Request).
        Devuelve el token decodificado/verificado o lanza una excepción.
        """
        pass

    @abstractmethod
    async def get_user_from_token(self, verified_token: VerifiedToken) -> Optional[User]:
        """
        Obtiene la información del usuario a partir de un token ya verificado.
        """
        pass

    @abstractmethod
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Obtiene la información de un usuario por su ID.
        """
        pass

    @abstractmethod
    async def get_user_by_email(self, email: EmailStr) -> Optional[User]:
        """
        Obtiene la información de un usuario por su email.
        """
        pass

    @abstractmethod
    async def create_user(
        self,
        email: Optional[EmailStr] = None,
        phone_number: Optional[str] = None,
        password: Optional[str] = None,
        display_name: Optional[str] = None,
        photo_url: Optional[HttpUrl] = None,
        email_verified: bool = False,
        disabled: bool = False,
        **kwargs: Any,
    ) -> User:
        """
        Crea un nuevo usuario.
        Los parámetros exactos pueden variar según el backend.
        """
        pass

    @abstractmethod
    async def update_user(
        self,
        user_id: str,
        email: Optional[EmailStr] = None,
        phone_number: Optional[str] = None,
        password: Optional[str] = None, # Puede requerir manejo especial
        display_name: Optional[str] = None,
        photo_url: Optional[HttpUrl] = None,
        email_verified: Optional[bool] = None,
        disabled: Optional[bool] = None,
        custom_claims: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> User:
        """
        Actualiza un usuario existente.
        """
        pass

    @abstractmethod
    async def delete_user(self, user_id: str) -> None:
        """
        Elimina un usuario.
        """
        pass

    @abstractmethod
    async def set_custom_user_claims(
        self, user_id: str, claims: Dict[str, Any]
    ) -> None:
        """
        Establece claims personalizados para un usuario.
        Esto es útil para roles y permisos.
        """
        pass

    # Opcional: Métodos adicionales que podrían ser útiles
    # @abstractmethod
    # async def generate_email_verification_link(self, email: EmailStr) -> str:
    #     pass

    # @abstractmethod
    # async def generate_password_reset_link(self, email: EmailStr) -> str:
    #     pass
