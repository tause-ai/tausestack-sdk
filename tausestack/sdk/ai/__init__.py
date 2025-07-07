"""
TauseStack AI SDK - Cliente para integración con servicios de IA

Proporciona una interfaz simplificada para interactuar con los servicios de IA
de TauseStack desde aplicaciones externas.
"""

from .clients.ai_client import AIClient
from .generators.component_generator import ComponentGenerator
from .prompts.prompt_builder import PromptBuilder

__version__ = "0.9.0"
__all__ = ["AIClient", "ComponentGenerator", "PromptBuilder"]