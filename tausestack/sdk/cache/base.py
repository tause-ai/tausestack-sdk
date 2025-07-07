# TauseStack SDK - Cache Module Base

from abc import ABC, abstractmethod
from typing import Any, Optional

class AbstractCacheBackend(ABC):
    """Abstract base class for all cache backends."""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Retrieve an item from the cache by key."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set an item in the cache with an optional TTL (in seconds).
           A TTL of None might mean 'cache forever' if the backend supports it.
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete an item from the cache by key."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all items from the cache."""
        pass
