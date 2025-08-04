from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel

# TypeVar para representar cualquier clase que herede de pydantic.BaseModel
_PydanticModelType = TypeVar("_PydanticModelType", bound=BaseModel)
# TypeVar para representar el tipo del ID de un item (e.g., int, str, UUID)
ItemID = TypeVar("ItemID")

class AbstractDatabaseBackend(ABC):
    """
    Interfaz abstracta para un backend de base de datos.
    Define las operaciones estándar que cualquier implementación de backend debe proporcionar.
    """

    @abstractmethod
    async def connect(self) -> None:
        """Establece la conexión con la base de datos."""
        raise NotImplementedError

    @abstractmethod
    async def disconnect(self) -> None:
        """Cierra la conexión con la base de datos."""
        raise NotImplementedError

    @abstractmethod
    async def create_tables(self, models: Optional[List[Type[_PydanticModelType]]] = None) -> None:
        """
        Crea las tablas en la base de datos para los modelos Pydantic proporcionados.
        Si `models` es None, puede intentar crear todas las tablas conocidas por el backend.
        """
        raise NotImplementedError

    @abstractmethod
    async def drop_tables(self, models: Optional[List[Type[_PydanticModelType]]] = None) -> None:
        """
        Elimina las tablas de la base de datos para los modelos Pydantic proporcionados.
        Si `models` es None, puede intentar eliminar todas las tablas conocidas por el backend.
        """
        raise NotImplementedError

    @abstractmethod
    async def create(self, model_cls: Type[_PydanticModelType], data: Dict[str, Any]) -> _PydanticModelType:
        """
        Crea un nuevo registro para la clase `model_cls` con los datos proporcionados.
        Devuelve una instancia del modelo Pydantic creado.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, model_cls: Type[_PydanticModelType], item_id: ItemID) -> Optional[_PydanticModelType]:
        """
        Obtiene un registro por su ID para la clase `model_cls`.
        Devuelve una instancia del modelo Pydantic o None si no se encuentra.
        """
        raise NotImplementedError

    @abstractmethod
    async def update(self, model_cls: Type[_PydanticModelType], item_id: ItemID, data: Dict[str, Any]) -> Optional[_PydanticModelType]:
        """
        Actualiza un registro por su ID para la clase `model_cls` con los datos proporcionados.
        Devuelve una instancia del modelo Pydantic actualizado o None si no se encuentra.
        """
        raise NotImplementedError

    @abstractmethod
    async def delete(self, model_cls: Type[_PydanticModelType], item_id: ItemID) -> bool:
        """
        Elimina un registro por su ID para la clase `model_cls`.
        Devuelve True si la eliminación fue exitosa, False en caso contrario.
        """
        raise NotImplementedError

    @abstractmethod
    async def find(
        self,
        model_cls: Type[_PydanticModelType],
        filters: Optional[Dict[str, Any]] = None,
        offset: int = 0,
        limit: Optional[int] = 100,
        sort_by: Optional[List[str]] = None  # e.g., ["name_asc", "created_at_desc"]
    ) -> List[_PydanticModelType]:
        """
        Busca registros para la clase `model_cls` aplicando filtros, paginación y ordenamiento.
        Devuelve una lista de instancias del modelo Pydantic.
        """
        raise NotImplementedError

    @abstractmethod
    async def count(
        self,
        model_cls: Type[_PydanticModelType],
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Cuenta el número de registros para la clase `model_cls` que coinciden con los filtros.
        Devuelve el número total de registros.
        """
        raise NotImplementedError

    @abstractmethod
    async def begin_transaction(self) -> None:
        """Inicia una nueva transacción en la base de datos."""
        raise NotImplementedError

    @abstractmethod
    async def commit_transaction(self) -> None:
        """Confirma (commit) la transacción actual."""
        raise NotImplementedError

    @abstractmethod
    async def rollback_transaction(self) -> None:
        """Revierte (rollback) la transacción actual."""
        raise NotImplementedError

    @abstractmethod
    async def execute_raw(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Ejecuta una consulta cruda (e.g., DDL, o DML que no devuelve filas como INSERT sin RETURNING).
        El valor de retorno depende del backend y de la consulta (e.g., número de filas afectadas).
        """
        raise NotImplementedError

    @abstractmethod
    async def fetch_all_raw(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Ejecuta una consulta cruda SELECT y devuelve todas las filas como una lista de diccionarios.
        """
        raise NotImplementedError

    @abstractmethod
    async def fetch_one_raw(self, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Ejecuta una consulta cruda SELECT y devuelve la primera fila como un diccionario, o None si no hay resultados.
        """
        raise NotImplementedError
