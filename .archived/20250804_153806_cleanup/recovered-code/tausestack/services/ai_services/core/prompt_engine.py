"""
Prompt Engine - Sistema de gestión y optimización de prompts para IA
"""
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import re


class PromptType(str, Enum):
    """Tipos de prompts disponibles"""
    COMPONENT_GENERATION = "component_generation"
    TEMPLATE_ENHANCEMENT = "template_enhancement"
    CODE_DEBUGGING = "code_debugging"
    UI_IMPROVEMENT = "ui_improvement"
    API_GENERATION = "api_generation"
    DATABASE_SCHEMA = "database_schema"
    STYLING = "styling"
    ACCESSIBILITY = "accessibility"


class AIProvider(str, Enum):
    """Proveedores de IA soportados"""
    OPENAI_GPT4 = "openai_gpt4"
    ANTHROPIC_CLAUDE = "anthropic_claude"
    LOCAL_MODEL = "local_model"
    COHERE = "cohere"


@dataclass
class PromptTemplate:
    """Template de prompt con metadata"""
    id: str
    name: str
    type: PromptType
    template: str
    variables: List[str]
    provider: AIProvider
    max_tokens: int = 2000
    temperature: float = 0.7
    system_message: Optional[str] = None
    examples: List[Dict[str, str]] = None


class PromptEngine:
    """Motor de gestión de prompts optimizados para diferentes tareas"""
    
    def __init__(self):
        self.templates: Dict[str, PromptTemplate] = {}
        self.context_history: Dict[str, List[Dict]] = {}
        self._load_default_templates()
    
    def _load_default_templates(self):
        """Carga templates de prompts por defecto"""
        
        # Template para generación de componentes React
        component_template = PromptTemplate(
            id="react_component_generation",
            name="React Component Generation",
            type=PromptType.COMPONENT_GENERATION,
            provider=AIProvider.OPENAI_GPT4,
            system_message="""Eres un experto desarrollador React/TypeScript especializado en shadcn/ui. 
Tu trabajo es generar componentes React modernos, accesibles y bien estructurados.""",
            template="""
Genera un componente React/TypeScript con las siguientes especificaciones:

**Descripción**: {description}
**Tipo de componente**: {component_type}
**Props requeridas**: {required_props}
**Funcionalidades**: {features}
**Estilo**: {styling_preferences}

**Requisitos técnicos**:
- Usar TypeScript con tipos estrictos
- Implementar con shadcn/ui components cuando sea apropiado
- Incluir Tailwind CSS para estilos
- Seguir mejores prácticas de React
- Incluir manejo de errores
- Ser responsive por defecto
- Incluir comentarios explicativos

**Estructura esperada**:
1. Imports necesarios
2. Interface de Props con TypeScript
3. Componente funcional
4. Export default

**Componentes shadcn/ui disponibles**:
Button, Card, Input, Select, Dialog, Form, Table, Badge, Alert-Dialog, Sheet

Genera SOLO el código del componente, sin explicaciones adicionales.
""",
            variables=["description", "component_type", "required_props", "features", "styling_preferences"],
            max_tokens=1500,
            temperature=0.3
        )
        
        # Template para mejora de templates
        template_enhancement = PromptTemplate(
            id="template_enhancement",
            name="Template Enhancement",
            type=PromptType.TEMPLATE_ENHANCEMENT,
            provider=AIProvider.ANTHROPIC_CLAUDE,
            system_message="""Eres un arquitecto de software especializado en mejorar templates y estructuras de aplicaciones.""",
            template="""
Analiza y mejora el siguiente template:

**Template actual**: {current_template}
**Objetivo de mejora**: {improvement_goal}
**Restricciones**: {constraints}
**Audiencia objetivo**: {target_audience}

**Áreas de análisis**:
1. Estructura y organización
2. Componentes utilizados
3. Patrones de diseño
4. Performance
5. Accesibilidad
6. Mantenibilidad
7. Escalabilidad

**Proporciona**:
1. Análisis detallado de problemas encontrados
2. Recomendaciones específicas de mejora
3. Código mejorado para las partes críticas
4. Justificación de los cambios propuestos

Formato de respuesta en JSON:
{
  "analysis": "...",
  "recommendations": ["..."],
  "improved_code": "...",
  "justification": "..."
}
""",
            variables=["current_template", "improvement_goal", "constraints", "target_audience"],
            max_tokens=2500,
            temperature=0.4
        )
        
        # Template para debugging
        debugging_template = PromptTemplate(
            id="code_debugging",
            name="Code Debugging Assistant",
            type=PromptType.CODE_DEBUGGING,
            provider=AIProvider.OPENAI_GPT4,
            system_message="""Eres un experto en debugging de código React/TypeScript y shadcn/ui.""",
            template="""
Analiza y corrige el siguiente código con error:

**Código con error**: 
```
{error_code}
```

**Mensaje de error**: {error_message}
**Contexto adicional**: {context}
**Entorno**: React + TypeScript + shadcn/ui + Tailwind CSS

**Proporciona**:
1. Identificación clara del problema
2. Explicación de por qué ocurre el error
3. Código corregido
4. Mejoras adicionales recomendadas
5. Cómo prevenir errores similares

Formato de respuesta:
```json
{
  "problem_identified": "...",
  "explanation": "...",
  "corrected_code": "...",
  "improvements": ["..."],
  "prevention_tips": ["..."]
}
```
""",
            variables=["error_code", "error_message", "context"],
            max_tokens=1800,
            temperature=0.2
        )
        
        # Template para generación de APIs
        api_generation_template = PromptTemplate(
            id="api_generation",
            name="API Endpoint Generation",
            type=PromptType.API_GENERATION,
            provider=AIProvider.OPENAI_GPT4,
            system_message="""Eres un experto en desarrollo de APIs con FastAPI y Python.""",
            template="""
Genera un endpoint de API con las siguientes especificaciones:

**Descripción**: {description}
**Método HTTP**: {http_method}
**Ruta**: {route}
**Parámetros**: {parameters}
**Modelo de datos**: {data_model}
**Validaciones**: {validations}
**Autenticación**: {auth_requirements}

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
""",
            variables=["description", "http_method", "route", "parameters", "data_model", "validations", "auth_requirements"],
            max_tokens=1600,
            temperature=0.3
        )
        
        # Registrar templates
        self.templates[component_template.id] = component_template
        self.templates[template_enhancement.id] = template_enhancement
        self.templates[debugging_template.id] = debugging_template
        self.templates[api_generation_template.id] = api_generation_template
    
    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """Obtiene un template de prompt por ID"""
        return self.templates.get(template_id)
    
    def list_templates(self, prompt_type: Optional[PromptType] = None) -> List[PromptTemplate]:
        """Lista templates disponibles, opcionalmente filtrados por tipo"""
        templates = list(self.templates.values())
        if prompt_type:
            templates = [t for t in templates if t.type == prompt_type]
        return templates
    
    def render_prompt(self, template_id: str, variables: Dict[str, Any]) -> Tuple[str, PromptTemplate]:
        """Renderiza un prompt con las variables proporcionadas"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        # Validar que todas las variables requeridas estén presentes
        missing_vars = set(template.variables) - set(variables.keys())
        if missing_vars:
            raise ValueError(f"Missing required variables: {missing_vars}")
        
        # Renderizar el prompt
        rendered_prompt = template.template.format(**variables)
        
        return rendered_prompt, template
    
    def add_context(self, session_id: str, role: str, content: str):
        """Agrega contexto a una sesión de conversación"""
        if session_id not in self.context_history:
            self.context_history[session_id] = []
        
        self.context_history[session_id].append({
            "role": role,
            "content": content,
            "timestamp": self._get_timestamp()
        })
    
    def get_context(self, session_id: str, max_messages: int = 10) -> List[Dict]:
        """Obtiene el contexto de conversación para una sesión"""
        if session_id not in self.context_history:
            return []
        
        return self.context_history[session_id][-max_messages:]
    
    def clear_context(self, session_id: str):
        """Limpia el contexto de una sesión"""
        if session_id in self.context_history:
            del self.context_history[session_id]
    
    def optimize_prompt_for_provider(self, prompt: str, provider: AIProvider) -> str:
        """Optimiza un prompt para un proveedor específico de IA"""
        if provider == AIProvider.OPENAI_GPT4:
            # OpenAI prefiere prompts más estructurados
            return self._structure_prompt_openai(prompt)
        elif provider == AIProvider.ANTHROPIC_CLAUDE:
            # Claude prefiere prompts más conversacionales
            return self._structure_prompt_claude(prompt)
        else:
            return prompt
    
    def _structure_prompt_openai(self, prompt: str) -> str:
        """Estructura un prompt para OpenAI"""
        # Agregar marcadores claros de sección
        if "**" not in prompt:
            return prompt
        
        # OpenAI responde mejor a prompts con secciones claras
        structured = prompt.replace("**", "###")
        return structured
    
    def _structure_prompt_claude(self, prompt: str) -> str:
        """Estructura un prompt para Claude"""
        # Claude prefiere un estilo más conversacional
        conversational = prompt.replace("**Requisitos técnicos**:", "\nPor favor, asegúrate de que:")
        conversational = conversational.replace("**Proporciona**:", "\nNecesito que me proporciones:")
        return conversational
    
    def _get_timestamp(self) -> str:
        """Obtiene timestamp actual"""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    def extract_code_from_response(self, response: str) -> Optional[str]:
        """Extrae código de una respuesta de IA"""
        # Buscar bloques de código entre ```
        code_pattern = r'```(?:typescript|tsx|javascript|jsx|python)?\n(.*?)```'
        matches = re.findall(code_pattern, response, re.DOTALL)
        
        if matches:
            return matches[0].strip()
        
        # Si no hay bloques de código, buscar líneas que parezcan código
        lines = response.split('\n')
        code_lines = []
        in_code_block = False
        
        for line in lines:
            if any(keyword in line for keyword in ['import ', 'export ', 'function ', 'const ', 'interface ', 'class ']):
                in_code_block = True
            
            if in_code_block:
                code_lines.append(line)
                
                # Terminar si encontramos una línea vacía después del código
                if line.strip() == '' and code_lines:
                    break
        
        return '\n'.join(code_lines) if code_lines else None
    
    def validate_generated_code(self, code: str, expected_type: str) -> Dict[str, Any]:
        """Valida código generado básicamente"""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": []
        }
        
        if expected_type == "react_component":
            # Validaciones básicas para componentes React
            if "import" not in code:
                validation_result["warnings"].append("No imports found")
            
            if "export default" not in code:
                validation_result["errors"].append("Missing default export")
                validation_result["is_valid"] = False
            
            if "interface" not in code and "type" not in code:
                validation_result["warnings"].append("No TypeScript types defined")
        
        elif expected_type == "api_endpoint":
            # Validaciones para endpoints de API
            if "@app." not in code and "async def" not in code:
                validation_result["errors"].append("Not a valid FastAPI endpoint")
                validation_result["is_valid"] = False
        
        return validation_result


# Instancia global del motor de prompts
prompt_engine = PromptEngine()