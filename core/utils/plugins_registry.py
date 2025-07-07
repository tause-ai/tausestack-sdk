"""
Registro centralizado y sistema de descubrimiento/carga para plugins de dominio en TauseStack.
Permite registrar, listar y obtener instancias de plugins dinámicamente.
"""
from typing import Dict, Type, List, Any
from .plugins_base import DomainPlugin

class PluginRegistry:
    """Registro central de plugins de dominio."""
    _registry: Dict[str, Type[DomainPlugin]] = {}

    @classmethod
    def register(cls, plugin_cls: Type[DomainPlugin]) -> None:
        """Registra un plugin en el sistema."""
        name = plugin_cls.name
        if name in cls._registry:
            raise ValueError(f"Ya existe un plugin registrado con el nombre: {name}")
        cls._registry[name] = plugin_cls

    @classmethod
    def get(cls, name: str) -> Type[DomainPlugin]:
        """Obtiene la clase de un plugin por nombre."""
        return cls._registry[name]

    @classmethod
    def list_plugins(cls) -> List[Dict[str, Any]]:
        """Lista los metadatos de todos los plugins registrados."""
        return [plugin.plugin_info() for plugin in cls._registry.values()]

    @classmethod
    def create_instance(cls, name: str, config: dict = None) -> DomainPlugin:
        """Crea una instancia de un plugin registrado y ejecuta setup."""
        plugin_cls = cls.get(name)
        instance = plugin_cls()
        if config:
            instance.setup(config)
        return instance
