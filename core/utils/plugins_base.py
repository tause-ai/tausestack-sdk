"""
Interfaz base para plugins/adaptadores de dominio en TauseStack.
Todos los plugins deben heredar de esta clase y registrar los metadatos mínimos requeridos.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict

class DomainPlugin(ABC):
    """Clase base para todos los plugins/adaptadores de dominio."""

    name: str  # Nombre único del plugin
    version: str  # Versión del plugin
    description: str = ""
    author: str = ""

    @abstractmethod
    def setup(self, config: Dict[str, Any]) -> None:
        """Inicializa el plugin con la configuración provista."""
        pass

    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """Ejecuta la función principal del plugin/adaptador."""
        pass

    def teardown(self) -> None:
        """Limpieza y cierre de recursos (opcional)."""
        pass

    @classmethod
    def plugin_info(cls) -> Dict[str, Any]:
        """Devuelve metadatos del plugin para registro y descubrimiento."""
        return {
            "name": cls.name,
            "version": cls.version,
            "description": getattr(cls, "description", ""),
            "author": getattr(cls, "author", ""),
        }
