"""
TauseStack AI Prompts - Wrappers para Prompt Engine existente
NO duplica funcionalidad, integra con servicios existentes
"""

from .prompt_builder import (
    PromptBuilder,
    PromptTemplate,
    PromptType,
    build_component_prompt,
    build_api_prompt
)

__all__ = [
    "PromptBuilder",
    "PromptTemplate",
    "PromptType", 
    "build_component_prompt",
    "build_api_prompt"
] 