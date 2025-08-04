"""
OpenAI Client - Integración con GPT-4 para generación de código
"""
import os
import asyncio
from typing import Dict, List, Optional, Any, AsyncGenerator
import json
import logging
from dataclasses import dataclass

try:
    import openai
    from openai import AsyncOpenAI
except ImportError:
    openai = None
    AsyncOpenAI = None

from ..core.prompt_engine import PromptTemplate, AIProvider


logger = logging.getLogger(__name__)


@dataclass
class OpenAIResponse:
    """Respuesta de OpenAI con metadata"""
    content: str
    model: str
    tokens_used: int
    cost_estimate: float
    finish_reason: str
    response_time: float


class OpenAIClient:
    """Cliente para integración con OpenAI GPT-4"""
    
    def __init__(self, api_key: Optional[str] = None):
        if not openai:
            raise ImportError("openai package not installed. Run: pip install openai")
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model_costs = {
            "gpt-4": {"input": 0.03, "output": 0.06},  # per 1K tokens
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002}
        }
        self.default_model = "gpt-4-turbo"
    
    async def generate_code(
        self,
        prompt: str,
        template: PromptTemplate,
        context: Optional[List[Dict]] = None,
        stream: bool = False
    ) -> OpenAIResponse:
        """Genera código usando OpenAI"""
        
        start_time = asyncio.get_event_loop().time()
        
        # Preparar mensajes
        messages = []
        
        # Mensaje del sistema si existe
        if template.system_message:
            messages.append({
                "role": "system",
                "content": template.system_message
            })
        
        # Agregar contexto previo si existe
        if context:
            for msg in context[-5:]:  # Solo últimos 5 mensajes
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
            logger.error(f"Error generating code with OpenAI: {e}")
            raise
    
    async def _generate_complete(
        self,
        messages: List[Dict],
        template: PromptTemplate,
        start_time: float
    ) -> OpenAIResponse:
        """Generación completa (no streaming)"""
        
        response = await self.client.chat.completions.create(
            model=self.default_model,
            messages=messages,
            max_tokens=template.max_tokens,
            temperature=template.temperature,
            top_p=0.9,
            frequency_penalty=0.1,
            presence_penalty=0.1
        )
        
        end_time = asyncio.get_event_loop().time()
        response_time = end_time - start_time
        
        # Extraer información de la respuesta
        choice = response.choices[0]
        content = choice.message.content
        finish_reason = choice.finish_reason
        
        # Calcular tokens y costo
        tokens_used = response.usage.total_tokens
        cost_estimate = self._calculate_cost(
            response.usage.prompt_tokens,
            response.usage.completion_tokens,
            self.default_model
        )
        
        return OpenAIResponse(
            content=content,
            model=self.default_model,
            tokens_used=tokens_used,
            cost_estimate=cost_estimate,
            finish_reason=finish_reason,
            response_time=response_time
        )
    
    async def _generate_streaming(
        self,
        messages: List[Dict],
        template: PromptTemplate
    ) -> AsyncGenerator[str, None]:
        """Generación con streaming"""
        
        stream = await self.client.chat.completions.create(
            model=self.default_model,
            messages=messages,
            max_tokens=template.max_tokens,
            temperature=template.temperature,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
    
    def _calculate_cost(self, prompt_tokens: int, completion_tokens: int, model: str) -> float:
        """Calcula el costo estimado de la request"""
        if model not in self.model_costs:
            return 0.0
        
        costs = self.model_costs[model]
        prompt_cost = (prompt_tokens / 1000) * costs["input"]
        completion_cost = (completion_tokens / 1000) * costs["output"]
        
        return prompt_cost + completion_cost
    
    async def validate_api_key(self) -> bool:
        """Valida que la API key sea válida"""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            return True
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return False
    
    async def get_available_models(self) -> List[str]:
        """Obtiene lista de modelos disponibles"""
        try:
            models = await self.client.models.list()
            gpt_models = [
                model.id for model in models.data 
                if "gpt" in model.id.lower()
            ]
            return sorted(gpt_models)
        except Exception as e:
            logger.error(f"Error fetching models: {e}")
            return [self.default_model]
    
    async def analyze_code_quality(self, code: str, language: str = "typescript") -> Dict[str, Any]:
        """Analiza la calidad del código generado"""
        
        analysis_prompt = f"""
Analiza la calidad del siguiente código {language}:

```{language}
{code}
```

Proporciona un análisis en formato JSON con:
1. score: puntuación de 1-10
2. strengths: fortalezas del código
3. improvements: áreas de mejora
4. security_issues: problemas de seguridad
5. performance_notes: notas de rendimiento
6. accessibility_score: puntuación de accesibilidad (1-10)

Responde SOLO con JSON válido.
"""
        
        messages = [
            {
                "role": "system",
                "content": "Eres un experto en análisis de código y calidad de software."
            },
            {
                "role": "user",
                "content": analysis_prompt
            }
        ]
        
        try:
            response = await self.client.chat.completions.create(
                model=self.default_model,
                messages=messages,
                max_tokens=800,
                temperature=0.2
            )
            
            content = response.choices[0].message.content
            # Intentar parsear como JSON
            analysis = json.loads(content)
            return analysis
            
        except json.JSONDecodeError:
            logger.warning("Could not parse code analysis as JSON")
            return {
                "score": 7,
                "strengths": ["Code generated successfully"],
                "improvements": ["Manual review recommended"],
                "security_issues": [],
                "performance_notes": [],
                "accessibility_score": 7
            }
        except Exception as e:
            logger.error(f"Error analyzing code quality: {e}")
            return {"error": str(e)}
    
    async def suggest_improvements(self, code: str, context: str = "") -> List[str]:
        """Sugiere mejoras para el código"""
        
        improvement_prompt = f"""
Analiza este código y sugiere mejoras específicas:

```
{code}
```

Contexto: {context}

Proporciona 3-5 sugerencias específicas y accionables para mejorar:
1. Legibilidad
2. Performance
3. Mantenibilidad
4. Seguridad
5. Accesibilidad

Responde con una lista de sugerencias claras y específicas.
"""
        
        messages = [
            {
                "role": "system",
                "content": "Eres un senior developer especializado en mejores prácticas."
            },
            {
                "role": "user",
                "content": improvement_prompt
            }
        ]
        
        try:
            response = await self.client.chat.completions.create(
                model=self.default_model,
                messages=messages,
                max_tokens=600,
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            # Extraer sugerencias (asumiendo formato de lista)
            suggestions = [
                line.strip().lstrip('- ').lstrip('* ').lstrip('1. ').lstrip('2. ')
                for line in content.split('\n')
                if line.strip() and any(char.isalpha() for char in line)
            ]
            
            return suggestions[:5]  # Máximo 5 sugerencias
            
        except Exception as e:
            logger.error(f"Error getting improvement suggestions: {e}")
            return ["Manual code review recommended"]
    
    async def explain_code(self, code: str) -> str:
        """Explica qué hace un bloque de código"""
        
        explanation_prompt = f"""
Explica qué hace este código de manera clara y concisa:

```
{code}
```

Incluye:
1. Propósito principal
2. Componentes clave
3. Flujo de funcionamiento
4. Casos de uso

Usa un lenguaje claro y técnico pero accesible.
"""
        
        messages = [
            {
                "role": "system",
                "content": "Eres un experto en explicar código de manera clara y educativa."
            },
            {
                "role": "user",
                "content": explanation_prompt
            }
        ]
        
        try:
            response = await self.client.chat.completions.create(
                model=self.default_model,
                messages=messages,
                max_tokens=500,
                temperature=0.4
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error explaining code: {e}")
            return "No se pudo generar una explicación del código."


# Instancia global del cliente OpenAI
openai_client = None

def get_openai_client() -> OpenAIClient:
    """Obtiene instancia singleton del cliente OpenAI"""
    global openai_client
    if openai_client is None:
        openai_client = OpenAIClient()
    return openai_client