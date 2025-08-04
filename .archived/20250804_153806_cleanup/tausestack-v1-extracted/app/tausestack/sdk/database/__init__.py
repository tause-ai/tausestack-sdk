import uuid
from typing import Optional, Union, Any, Type # Any, Type might be useful for advanced scenarios or SQLAlchemy type hints

from pydantic import BaseModel as PydanticBaseModel, ConfigDict

from .base import AbstractDatabaseBackend # _PydanticModelType and ItemID (TypeVar) are kept in base.py for internal type hinting
# Model and ItemID are now defined concretely in this __init__.py file

from .exceptions import (
    DatabaseException,
    ConnectionException,
    RecordNotFoundException,
    DuplicateRecordException,
    QueryExecutionException,
    TransactionException,
    SchemaException
)

# --- Base Pydantic Model and ItemID Type Definition ---
ItemID = Union[int, str, uuid.UUID]

class Model(PydanticBaseModel):
    """
    Base model for all Pydantic data models intended for database interaction.
    It includes a common 'id' field (Optional[ItemID]) and sets Pydantic's
    `from_attributes=True` for compatibility with ORM model instances.
    `arbitrary_types_allowed=True` is also set for convenience with ORM relationships.
    """
    model_config = ConfigDict(
        from_attributes=True,
        arbitrary_types_allowed=True
    )
    id: Optional[ItemID] = None
from .backends import SQLAlchemyBackend

__all__ = [
    "AbstractDatabaseBackend",
    "Model",
    "ItemID",
    "DatabaseException",
    "ConnectionException",
    "RecordNotFoundException",
    "DuplicateRecordException",
    "QueryExecutionException",
    "TransactionException",
    "SchemaException",
    "SQLAlchemyBackend",
]
