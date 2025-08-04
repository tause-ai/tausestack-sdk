# Base classes for secrets providers
from abc import ABC, abstractmethod
from typing import Optional

class AbstractSecretsProvider(ABC):
    """Abstract Base Class for secrets providers."""

    @abstractmethod
    def get(self, secret_name: str) -> Optional[str]:
        """Retrieve a secret by its name."""
        pass
