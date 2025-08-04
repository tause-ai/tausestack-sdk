"""
Claude Client - Integración con Anthropic Claude para razonamiento complejo
"""
import os
import asyncio
from typing import Dict, List, Optional, Any
import json
import logging
from dataclasses import dataclass

try:
    import anthropic
    from anthropic import AsyncAnthropic
except ImportError:
    anthropic = None
    AsyncAnthropic = None

from ..core.prompt_engine import PromptTemplate, AIProvider


logger = logging.getLogger(__name__)


@dataclass
class ClaudeResponse:
    """Respuesta de Claude con metadata"""
    content: str
    model: str
    tokens_used: int
    cost_estimate: float
    stop_reason: str
    response_time: float


class ClaudeClient:
    """Cliente para integración con Anthropic Claude"""
    
    def __init__(self, api_key: Optional[str] = None):
        if not anthropic:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")
        
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key not provided")
        
        self.client = AsyncAnthropic(api_key=self.api_key)
        self.model_costs = {
            "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},  # per 1K tokens
            "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
            "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125}
        }
        self.default_model = "claude-3-sonnet-20240229"
    
    async def generate_code(
        self,
        prompt: str,
        template: PromptTemplate,
        context: Optional[List[Dict]] = None,
        stream: bool = False
    ) -> ClaudeResponse:
        """Genera código usando Claude"""
        
        start_time = asyncio.get_event_loop().time()
        
        # Preparar mensajes para Claude
        messages = []
        
        # Agregar contexto previo si existe
        if context:
            for msg in context[-4:]:  # Claude maneja menos contexto
                if msg["role"] in ["user", "assistant"]:
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
        
        # Agregar el prompt principal
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        try:
            if stream:
                return await self._generate_streaming(messages, template)
            else:
                return await self._generate_complete(messages, template, start_time)
                
        except Exception as e:
            logger.error(f"Error generating code with Claude: {e}")
            raise
    
    async def _generate_complete(
        self,
        messages: List[Dict],
        template: PromptTemplate,
        start_time: float
    ) -> ClaudeResponse:
        """Generación completa (no streaming)"""
        
        # Claude usa system message por separado
        system_message = template.system_message or "You are a helpful AI assistant specialized in code generation."
        
        response = await self.client.messages.create(
            model=self.default_model,
            max_tokens=template.max_tokens,
            temperature=template.temperature,
            system=system_message,
            messages=messages
        )
        
        end_time = asyncio.get_event_loop().time()
        response_time = end_time - start_time
        
        # Extraer información de la respuesta
        content = response.content[0].text if response.content else ""
        stop_reason = response.stop_reason
        
        # Calcular tokens y costo
        tokens_used = response.usage.input_tokens + response.usage.output_tokens
        cost_estimate = self._calculate_cost(
            response.usage.input_tokens,
            response.usage.output_tokens,
            self.default_model
        )
        
        return ClaudeResponse(
            content=content,
            model=self.default_model,
            tokens_used=tokens_used,
            cost_estimate=cost_estimate,
            stop_reason=stop_reason,
            response_time=response_time
        )
    
    async def _generate_streaming(
        self,
        messages: List[Dict],
        template: PromptTemplate
    ):
        """Generación con streaming"""
        
        system_message = template.system_message or "You are a helpful AI assistant."
        
        async with self.client.messages.stream(
            model=self.default_model,
            max_tokens=template.max_tokens,
            temperature=template.temperature,
            system=system_message,
            messages=messages
        ) as stream:
            async for text in stream.text_stream:
                yield text
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        """Calcula el costo estimado de la request"""
        if model not in self.model_costs:
            return 0.0
        
        costs = self.model_costs[model]
        input_cost = (input_tokens / 1000) * costs["input"]
        output_cost = (output_tokens / 1000) * costs["output"]
        
        return input_cost + output_cost
    
    async def validate_api_key(self) -> bool:
        """Valida que la API key sea válida"""
        try:
            response = await self.client.messages.create(
                model=self.default_model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Hello"}]
            )
            return True
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return False
    
    async def analyze_template_structure(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza la estructura de un template y sugiere mejoras"""
        
        analysis_prompt = f"""
Analiza la estructura del siguiente template y proporciona recomendaciones de mejora:

Template Data:
{json.dumps(template_data, indent=2)}

Analiza:
1. Estructura y organización
2. Componentes utilizados
3. Patrones de diseño aplicados
4. Escalabilidad y mantenibilidad
5. Mejores prácticas seguidas
6. Áreas de mejora específicas

Proporciona un análisis detallado en formato JSON con:
- overall_score: puntuación 1-10
- strengths: lista de fortalezas
- weaknesses: lista de debilidades
- recommendations: recomendaciones específicas
- architectural_patterns: patrones identificados
- suggested_improvements: mejoras sugeridas con prioridad

Responde SOLO con JSON válido.
"""
        
        try:
            response = await self.client.messages.create(
                model=self.default_model,
                max_tokens=1500,
                temperature=0.3,
                system="Eres un arquitecto de software experto en análisis de templates y estructuras de aplicaciones.",
                messages=[{"role": "user", "content": analysis_prompt}]
            )
            
            content = response.content[0].text
            # Intentar parsear como JSON
            analysis = json.loads(content)
            return analysis
            
        except json.JSONDecodeError:
            logger.warning("Could not parse template analysis as JSON")
            return {
                "overall_score": 7,
                "strengths": ["Template structure is functional"],
                "weaknesses": ["Requires detailed analysis"],
                "recommendations": ["Consider manual review"],
                "architectural_patterns": [],
                "suggested_improvements": []
            }
        except Exception as e:
            logger.error(f"Error analyzing template structure: {e}")
            return {"error": str(e)}
    
    async def enhance_template(self, template_code: str, requirements: List[str]) -> str:
        """Mejora un template basado en requisitos específicos"""
        
        enhancement_prompt = f"""
Mejora el siguiente template de código basándote en estos requisitos:

Template actual:
```
{template_code}
```

Requisitos de mejora:
{chr(10).join(f"- {req}" for req in requirements)}

Proporciona una versión mejorada que:
1. Mantenga la funcionalidad existente
2. Implemente las mejoras solicitadas
3. Siga mejores prácticas modernas
4. Sea más mantenible y escalable
5. Incluya comentarios explicativos

Responde con el código mejorado completo.
"""
        
        try:
            response = await self.client.messages.create(
                model=self.default_model,
                max_tokens=2000,
                temperature=0.4,
                system="Eres un experto en refactoring y mejora de código, especializado en React y TypeScript.",
                messages=[{"role": "user", "content": enhancement_prompt}]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Error enhancing template: {e}")
            return template_code  # Retornar original si falla
    
    async def generate_documentation(self, code: str, doc_type: str = "component") -> str:
        """Genera documentación para código"""
        
        doc_prompt = f"""
Genera documentación completa para el siguiente código:

```
{code}
```

Tipo de documentación: {doc_type}

Incluye:
1. Descripción general del propósito
2. Parámetros/Props con tipos y descripciones
3. Ejemplos de uso
4. Notas de implementación
5. Consideraciones de rendimiento
6. Accesibilidad
7. Casos de uso comunes

Formato: Markdown bien estructurado y profesional.
"""
        
        try:
            response = await self.client.messages.create(
                model=self.default_model,
                max_tokens=1200,
                temperature=0.3,
                system="Eres un technical writer experto en documentación de código y APIs.",
                messages=[{"role": "user", "content": doc_prompt}]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Error generating documentation: {e}")
            return f"# Documentación\n\nError generando documentación: {str(e)}"
    
    async def review_architecture(self, architecture_description: str) -> Dict[str, Any]:
        """Revisa una arquitectura de software y proporciona feedback"""
        
        review_prompt = f"""
Revisa la siguiente descripción de arquitectura de software:

{architecture_description}

Proporciona una revisión completa en formato JSON con:

1. architecture_score: puntuación general (1-10)
2. scalability_assessment: evaluación de escalabilidad
3. security_concerns: preocupaciones de seguridad identificadas
4. performance_considerations: consideraciones de rendimiento
5. maintainability_score: puntuación de mantenibilidad (1-10)
6. recommended_patterns: patrones recomendados
7. potential_bottlenecks: posibles cuellos de botella
8. improvement_roadmap: hoja de ruta de mejoras
9. technology_recommendations: recomendaciones tecnológicas
10. risk_assessment: evaluación de riesgos

Responde SOLO con JSON válido y bien estructurado.
"""
        
        try:
            response = await self.client.messages.create(
                model=self.default_model,
                max_tokens=2000,
                temperature=0.2,
                system="Eres un arquitecto de software senior con experiencia en sistemas distribuidos y escalables.",
                messages=[{"role": "user", "content": review_prompt}]
            )
            
            content = response.content[0].text
            analysis = json.loads(content)
            return analysis
            
        except json.JSONDecodeError:
            logger.warning("Could not parse architecture review as JSON")
            return {
                "architecture_score": 7,
                "scalability_assessment": "Requires detailed analysis",
                "security_concerns": [],
                "performance_considerations": [],
                "maintainability_score": 7,
                "recommended_patterns": [],
                "potential_bottlenecks": [],
                "improvement_roadmap": [],
                "technology_recommendations": [],
                "risk_assessment": "Medium risk - requires review"
            }
        except Exception as e:
            logger.error(f"Error reviewing architecture: {e}")
            return {"error": str(e)}
    
    async def get_available_models(self) -> List[str]:
        """Obtiene lista de modelos disponibles"""
        # Claude tiene modelos fijos
        return [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229", 
            "claude-3-haiku-20240307"
        ]


# Instancia global del cliente Claude
claude_client = None

def get_claude_client() -> ClaudeClient:
    """Obtiene instancia singleton del cliente Claude"""
    global claude_client
    if claude_client is None:
        claude_client = ClaudeClient()
    return claude_client