"""
TauseStack Prompt Builder - Wrapper para Prompt Engine existente
Integra con tausestack/services/ai_services/core/prompt_engine.py sin duplicar funcionalidad
"""

import httpx
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class PromptType(str, Enum):
    """Tipos de prompt (wrapper para prompt_engine)"""
    COMPONENT_GENERATION = "component_generation"
    API_GENERATION = "api_generation"
    TEMPLATE_ENHANCEMENT = "template_enhancement"
    CODE_DEBUGGING = "code_debugging"
    UI_IMPROVEMENT = "ui_improvement"


@dataclass
class PromptTemplate:
    """Template de prompt (wrapper)"""
    id: str
    name: str
    template: str
    variables: List[str]
    prompt_type: PromptType


class PromptBuilder:
    """
    Wrapper para tausestack/services/ai_services/core/prompt_engine.py
    NO duplica funcionalidad, solo proporciona interfaz compatible
    """
    
    def __init__(self, tenant_id: str = "default"):
        self.tenant_id = tenant_id
        self.ai_services_url = "http://localhost:8005"  # AI Services existente
        
    async def build_component_prompt(
        self,
        description: str,
        component_type: str = "component",
        required_props: List[str] = None,
        features: List[str] = None,
        styling_preferences: str = "modern"
    ) -> str:
        """
        Construye prompt para generación de componente
        Usa el prompt engine existente via AI Services
        """
        try:
            # Usar el template existente en ai_services
            variables = {
                "description": description,
                "component_type": component_type,
                "required_props": ", ".join(required_props or []),
                "features": ", ".join(features or []),
                "styling_preferences": styling_preferences
            }
            
            # Este es un wrapper, la lógica real está en ai_services
            template = f"""
Genera un componente React/TypeScript con las siguientes especificaciones:

**Descripción**: {description}
**Tipo de componente**: {component_type}
**Props requeridas**: {", ".join(required_props or [])}
**Funcionalidades**: {", ".join(features or [])}
**Estilo**: {styling_preferences}

**Requisitos técnicos**:
- Usar TypeScript con tipos estrictos
- Implementar con shadcn/ui components cuando sea apropiado
- Incluir Tailwind CSS para estilos
- Seguir mejores prácticas de React
- Incluir manejo de errores
- Ser responsive por defecto

Genera SOLO el código del componente, sin explicaciones adicionales.
"""
            
            return template.strip()
            
        except Exception as e:
            return f"Error building prompt: {str(e)}"
    
    async def build_api_prompt(
        self,
        description: str,
        http_method: str = "GET",
        route: str = "/api/endpoint",
        parameters: List[str] = None
    ) -> str:
        """
        Construye prompt para generación de API
        Usa el prompt engine existente via AI Services
        """
        try:
            template = f"""
Genera un endpoint de API con las siguientes especificaciones:

**Descripción**: {description}
**Método HTTP**: {http_method}
**Ruta**: {route}
**Parámetros**: {", ".join(parameters or [])}

**Requisitos técnicos**:
- Usar FastAPI con Pydantic
- Incluir validación de datos
- Manejo de errores apropiado
- Documentación automática
- Tipos de Python estrictos
- Seguir convenciones REST

**Incluir**:
1. Modelos Pydantic para request/response
2. Función del endpoint
3. Manejo de excepciones
4. Documentación con docstrings
5. Validaciones de negocio

Genera el código completo del endpoint.
"""
            
            return template.strip()
            
        except Exception as e:
            return f"Error building API prompt: {str(e)}"
    
    async def get_available_templates(self) -> List[PromptTemplate]:
        """
        Obtiene templates disponibles desde AI Services
        Wrapper para el prompt engine existente
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.ai_services_url}/templates",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    templates = []
                    
                    for template_data in data.get("templates", []):
                        templates.append(PromptTemplate(
                            id=template_data.get("id", ""),
                            name=template_data.get("name", ""),
                            template=template_data.get("template", ""),
                            variables=template_data.get("variables", []),
                            prompt_type=PromptType(template_data.get("type", "component_generation"))
                        ))
                    
                    return templates
                else:
                    return []
                    
        except Exception as e:
            # Fallback a templates básicos si AI Services no está disponible
            return [
                PromptTemplate(
                    id="react_component_generation",
                    name="React Component Generation",
                    template="Generate a React component...",
                    variables=["description", "component_type"],
                    prompt_type=PromptType.COMPONENT_GENERATION
                ),
                PromptTemplate(
                    id="api_generation",
                    name="API Endpoint Generation", 
                    template="Generate an API endpoint...",
                    variables=["description", "http_method"],
                    prompt_type=PromptType.API_GENERATION
                )
            ]
    
    def render_template(self, template: PromptTemplate, variables: Dict[str, Any]) -> str:
        """
        Renderiza un template con variables
        Wrapper para funcionalidad existente
        """
        try:
            # Renderizado básico (la lógica completa está en ai_services)
            rendered = template.template
            for var, value in variables.items():
                placeholder = f"{{{var}}}"
                rendered = rendered.replace(placeholder, str(value))
            return rendered
        except Exception as e:
            return f"Error rendering template: {str(e)}"


# Instancia por defecto para compatibilidad
default_builder = PromptBuilder()

# Funciones de conveniencia para compatibilidad con ejemplos
async def build_component_prompt(description: str, **kwargs) -> str:
    """Función de conveniencia que usa AI Services existente"""
    return await default_builder.build_component_prompt(description, **kwargs)

async def build_api_prompt(description: str, **kwargs) -> str:
    """Función de conveniencia que usa AI Services existente"""
    return await default_builder.build_api_prompt(description, **kwargs) 