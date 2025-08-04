# Base classes for storage backends
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

try:
    import pandas as pd
except ImportError:
    pd = None

class AbstractJsonStorageBackend(ABC):
    """Abstract Base Class for JSON storage backends."""

    @abstractmethod
    def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a JSON object by key."""
        pass

    @abstractmethod
    def put_json(self, key: str, value: Dict[str, Any]) -> None:
        """Store a JSON object by key."""
        pass

    @abstractmethod
    def delete_json(self, key: str) -> None:
        """Delete a JSON object by key."""
        pass

class AbstractBinaryStorageBackend(ABC):
    """Abstract Base Class for Binary storage backends."""

    @abstractmethod
    def get_binary(self, key:str) -> Optional[bytes]:
        """Retrieve binary data by key."""
        pass

    @abstractmethod
    def put_binary(self, key: str, value: bytes, content_type: Optional[str] = None) -> None:
        """Store binary data by key.

        Args:
            key: The key under which to store the data.
            value: The binary data (bytes) to store.
            content_type: Optional. The MIME type of the content (e.g., 'image/jpeg', 'application/pdf').
                          This is particularly useful for object stores like S3.
        """
        pass

    @abstractmethod
    def delete_binary(self, key: str) -> None:
        """Delete binary data by key."""
        pass

class AbstractDataFrameStorageBackend(ABC):
    """Abstract Base Class for DataFrame storage backends."""

    @abstractmethod
    def get_dataframe(self, key: str) -> Optional['pd.DataFrame']:
        """Retrieve a DataFrame by key."""
        pass

    @abstractmethod
    def put_dataframe(self, key: str, value: 'pd.DataFrame') -> None:
        """Store a DataFrame by key."""
        pass

    @abstractmethod
    def delete_dataframe(self, key: str) -> None:
        """Delete a DataFrame by key."""
        pass
