"""
Code Generator - Orquestador de generación de código con múltiples proveedores de IA
"""
import asyncio
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import json
import logging
import time

from .prompt_engine import PromptEngine, PromptType, AIProvider, PromptTemplate
from ..api.openai_client import OpenAIClient, OpenAIResponse, get_openai_client
from ..api.claude_client import ClaudeClient, ClaudeResponse, get_claude_client


logger = logging.getLogger(__name__)


class GenerationStrategy(str, Enum):
    """Estrategias de generación de código"""
    FAST = "fast"  # Usar el modelo más rápido
    QUALITY = "quality"  # Usar el modelo de mejor calidad
    BALANCED = "balanced"  # Balance entre velocidad y calidad
    MULTI_PROVIDER = "multi_provider"  # Usar múltiples proveedores y comparar
    ADAPTIVE = "adaptive"  # Adaptar según el tipo de tarea


@dataclass
class GenerationRequest:
    """Request para generación de código"""
    description: str
    component_type: str = "component"
    required_props: List[str] = None
    features: List[str] = None
    styling_preferences: str = "modern"
    template_id: str = "react_component_generation"
    strategy: GenerationStrategy = GenerationStrategy.BALANCED
    context: List[Dict] = None
    session_id: str = None
    stream: bool = False


@dataclass
class GenerationResult:
    """Resultado de generación de código"""
    code: str
    provider: str
    model: str
    tokens_used: int
    cost_estimate: float
    response_time: float
    quality_score: Optional[float] = None
    validation_result: Optional[Dict] = None
    suggestions: List[str] = None
    explanation: Optional[str] = None


class CodeGenerator:
    """Generador de código con múltiples proveedores de IA"""
    
    def __init__(self):
        self.prompt_engine = PromptEngine()
        self.openai_client: Optional[OpenAIClient] = None
        self.claude_client: Optional[ClaudeClient] = None
        self.provider_preferences = {
            PromptType.COMPONENT_GENERATION: AIProvider.OPENAI_GPT4,
            PromptType.TEMPLATE_ENHANCEMENT: AIProvider.ANTHROPIC_CLAUDE,
            PromptType.CODE_DEBUGGING: AIProvider.OPENAI_GPT4,
            PromptType.API_GENERATION: AIProvider.OPENAI_GPT4,
            PromptType.UI_IMPROVEMENT: AIProvider.ANTHROPIC_CLAUDE,
        }
        self.generation_stats = {
            "total_requests": 0,
            "successful_generations": 0,
            "failed_generations": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "avg_response_time": 0.0
        }
    
    async def initialize_clients(self):
        """Inicializa los clientes de IA"""
        try:
            self.openai_client = get_openai_client()
            if await self.openai_client.validate_api_key():
                logger.info("OpenAI client initialized successfully")
            else:
                logger.warning("OpenAI API key validation failed")
                self.openai_client = None
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self.openai_client = None
        
        try:
            self.claude_client = get_claude_client()
            if await self.claude_client.validate_api_key():
                logger.info("Claude client initialized successfully")
            else:
                logger.warning("Claude API key validation failed")
                self.claude_client = None
        except Exception as e:
            logger.error(f"Failed to initialize Claude client: {e}")
            self.claude_client = None
    
    async def generate_component(self, request: GenerationRequest) -> GenerationResult:
        """Genera un componente React/TypeScript"""
        
        self.generation_stats["total_requests"] += 1
        start_time = time.time()
        
        try:
            # Preparar variables para el prompt
            variables = {
                "description": request.description,
                "component_type": request.component_type,
                "required_props": ", ".join(request.required_props or []),
                "features": ", ".join(request.features or []),
                "styling_preferences": request.styling_preferences
            }
            
            # Renderizar prompt
            prompt, template = self.prompt_engine.render_prompt(
                request.template_id, variables
            )
            
            # Determinar proveedor según estrategia
            provider = self._select_provider(template, request.strategy)
            
            # Generar código
            if provider == AIProvider.OPENAI_GPT4:
                response = await self._generate_with_openai(prompt, template, request)
                result = self._process_openai_response(response, provider)
            elif provider == AIProvider.ANTHROPIC_CLAUDE:
                response = await self._generate_with_claude(prompt, template, request)
                result = self._process_claude_response(response, provider)
            else:
                raise ValueError(f"Unsupported provider: {provider}")
            
            # Post-procesamiento
            await self._post_process_result(result, request)
            
            # Actualizar estadísticas
            self.generation_stats["successful_generations"] += 1
            self.generation_stats["total_tokens"] += result.tokens_used
            self.generation_stats["total_cost"] += result.cost_estimate
            
            # Agregar contexto si hay sesión
            if request.session_id:
                self.prompt_engine.add_context(
                    request.session_id, "user", prompt
                )
                self.prompt_engine.add_context(
                    request.session_id, "assistant", result.code
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating component: {e}")
            self.generation_stats["failed_generations"] += 1
            raise
        finally:
            end_time = time.time()
            response_time = end_time - start_time
            self._update_avg_response_time(response_time)
    
    async def generate_api_endpoint(
        self,
        description: str,
        http_method: str,
        route: str,
        parameters: List[str] = None,
        session_id: str = None
    ) -> GenerationResult:
        """Genera un endpoint de API"""
        
        variables = {
            "description": description,
            "http_method": http_method,
            "route": route,
            "parameters": ", ".join(parameters or []),
            "data_model": "Pydantic models",
            "validations": "Standard validations",
            "auth_requirements": "JWT authentication"
        }
        
        prompt, template = self.prompt_engine.render_prompt(
            "api_generation", variables
        )
        
        # APIs se generan mejor con OpenAI
        if not self.openai_client:
            raise ValueError("OpenAI client not available for API generation")
        
        response = await self._generate_with_openai(
            prompt, template, 
            GenerationRequest(description=description, session_id=session_id)
        )
        
        result = self._process_openai_response(response, AIProvider.OPENAI_GPT4)
        await self._post_process_result(result, None)
        
        return result
    
    async def debug_code(
        self,
        error_code: str,
        error_message: str,
        context: str = "",
        session_id: str = None
    ) -> GenerationResult:
        """Debuggea código con errores"""
        
        variables = {
            "error_code": error_code,
            "error_message": error_message,
            "context": context
        }
        
        prompt, template = self.prompt_engine.render_prompt(
            "code_debugging", variables
        )
        
        # Debugging se hace mejor con OpenAI
        if not self.openai_client:
            raise ValueError("OpenAI client not available for debugging")
        
        response = await self._generate_with_openai(
            prompt, template,
            GenerationRequest(description="Debug code", session_id=session_id)
        )
        
        result = self._process_openai_response(response, AIProvider.OPENAI_GPT4)
        
        # Extraer información específica de debugging
        try:
            debug_info = json.loads(result.code)
            result.code = debug_info.get("corrected_code", result.code)
            result.suggestions = debug_info.get("improvements", [])
            result.explanation = debug_info.get("explanation", "")
        except json.JSONDecodeError:
            # Si no es JSON válido, extraer código manualmente
            result.code = self.prompt_engine.extract_code_from_response(result.code) or result.code
        
        return result
    
    async def enhance_template(
        self,
        template_code: str,
        improvement_goals: List[str],
        session_id: str = None
    ) -> GenerationResult:
        """Mejora un template existente"""
        
        variables = {
            "current_template": template_code,
            "improvement_goal": ", ".join(improvement_goals),
            "constraints": "Maintain existing functionality",
            "target_audience": "Developers"
        }
        
        prompt, template = self.prompt_engine.render_prompt(
            "template_enhancement", variables
        )
        
        # Template enhancement se hace mejor con Claude
        if not self.claude_client:
            raise ValueError("Claude client not available for template enhancement")
        
        response = await self._generate_with_claude(
            prompt, template,
            GenerationRequest(description="Enhance template", session_id=session_id)
        )
        
        result = self._process_claude_response(response, AIProvider.ANTHROPIC_CLAUDE)
        
        # Procesar respuesta de mejora
        try:
            enhancement_info = json.loads(result.code)
            result.code = enhancement_info.get("improved_code", result.code)
            result.suggestions = enhancement_info.get("recommendations", [])
            result.explanation = enhancement_info.get("justification", "")
        except json.JSONDecodeError:
            # Si no es JSON, usar respuesta directa
            pass
        
        return result
    
    async def generate_multiple_options(
        self,
        request: GenerationRequest,
        num_options: int = 3
    ) -> List[GenerationResult]:
        """Genera múltiples opciones de código"""
        
        if request.strategy != GenerationStrategy.MULTI_PROVIDER:
            # Generar múltiples variaciones con el mismo proveedor
            tasks = []
            for i in range(num_options):
                # Variar ligeramente la temperatura para obtener variaciones
                modified_request = GenerationRequest(
                    description=f"{request.description} (Variación {i+1})",
                    component_type=request.component_type,
                    required_props=request.required_props,
                    features=request.features,
                    styling_preferences=request.styling_preferences,
                    template_id=request.template_id,
                    strategy=request.strategy,
                    session_id=request.session_id
                )
                tasks.append(self.generate_component(modified_request))
            
            return await asyncio.gather(*tasks)
        
        else:
            # Generar con diferentes proveedores
            results = []
            
            # OpenAI version
            if self.openai_client:
                openai_request = GenerationRequest(**request.__dict__)
                openai_request.strategy = GenerationStrategy.QUALITY
                try:
                    openai_result = await self.generate_component(openai_request)
                    results.append(openai_result)
                except Exception as e:
                    logger.error(f"OpenAI generation failed: {e}")
            
            # Claude version
            if self.claude_client:
                claude_request = GenerationRequest(**request.__dict__)
                claude_request.strategy = GenerationStrategy.QUALITY
                try:
                    claude_result = await self.generate_component(claude_request)
                    results.append(claude_result)
                except Exception as e:
                    logger.error(f"Claude generation failed: {e}")
            
            return results
    
    def _select_provider(self, template: PromptTemplate, strategy: GenerationStrategy) -> AIProvider:
        """Selecciona el proveedor de IA según la estrategia"""
        
        if strategy == GenerationStrategy.FAST:
            # OpenAI es generalmente más rápido
            return AIProvider.OPENAI_GPT4 if self.openai_client else AIProvider.ANTHROPIC_CLAUDE
        
        elif strategy == GenerationStrategy.QUALITY:
            # Claude es mejor para análisis complejo
            return AIProvider.ANTHROPIC_CLAUDE if self.claude_client else AIProvider.OPENAI_GPT4
        
        elif strategy == GenerationStrategy.BALANCED:
            # Usar preferencia por tipo de prompt
            preferred = self.provider_preferences.get(template.type, template.provider)
            if preferred == AIProvider.OPENAI_GPT4 and self.openai_client:
                return AIProvider.OPENAI_GPT4
            elif preferred == AIProvider.ANTHROPIC_CLAUDE and self.claude_client:
                return AIProvider.ANTHROPIC_CLAUDE
            else:
                # Fallback al disponible
                return AIProvider.OPENAI_GPT4 if self.openai_client else AIProvider.ANTHROPIC_CLAUDE
        
        elif strategy == GenerationStrategy.ADAPTIVE:
            # Adaptar según el tipo de componente
            if "dashboard" in template.template.lower() or "complex" in template.template.lower():
                return AIProvider.ANTHROPIC_CLAUDE if self.claude_client else AIProvider.OPENAI_GPT4
            else:
                return AIProvider.OPENAI_GPT4 if self.openai_client else AIProvider.ANTHROPIC_CLAUDE
        
        else:
            return template.provider
    
    async def _generate_with_openai(
        self,
        prompt: str,
        template: PromptTemplate,
        request: GenerationRequest
    ) -> OpenAIResponse:
        """Genera código con OpenAI"""
        
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized")
        
        context = None
        if request.session_id:
            context = self.prompt_engine.get_context(request.session_id)
        
        return await self.openai_client.generate_code(
            prompt, template, context, request.stream
        )
    
    async def _generate_with_claude(
        self,
        prompt: str,
        template: PromptTemplate,
        request: GenerationRequest
    ) -> ClaudeResponse:
        """Genera código con Claude"""
        
        if not self.claude_client:
            raise ValueError("Claude client not initialized")
        
        context = None
        if request.session_id:
            context = self.prompt_engine.get_context(request.session_id)
        
        return await self.claude_client.generate_code(
            prompt, template, context, request.stream
        )
    
    def _process_openai_response(
        self,
        response: OpenAIResponse,
        provider: AIProvider
    ) -> GenerationResult:
        """Procesa respuesta de OpenAI"""
        
        # Extraer código de la respuesta
        code = self.prompt_engine.extract_code_from_response(response.content)
        if not code:
            code = response.content  # Usar respuesta completa si no hay código extraíble
        
        return GenerationResult(
            code=code,
            provider=provider.value,
            model=response.model,
            tokens_used=response.tokens_used,
            cost_estimate=response.cost_estimate,
            response_time=response.response_time
        )
    
    def _process_claude_response(
        self,
        response: ClaudeResponse,
        provider: AIProvider
    ) -> GenerationResult:
        """Procesa respuesta de Claude"""
        
        # Extraer código de la respuesta
        code = self.prompt_engine.extract_code_from_response(response.content)
        if not code:
            code = response.content  # Usar respuesta completa si no hay código extraíble
        
        return GenerationResult(
            code=code,
            provider=provider.value,
            model=response.model,
            tokens_used=response.tokens_used,
            cost_estimate=response.cost_estimate,
            response_time=response.response_time
        )
    
    async def _post_process_result(
        self,
        result: GenerationResult,
        request: Optional[GenerationRequest]
    ):
        """Post-procesa el resultado de generación"""
        
        # Validar código generado
        if request and request.component_type:
            expected_type = "react_component" if "component" in request.component_type else "api_endpoint"
            result.validation_result = self.prompt_engine.validate_generated_code(
                result.code, expected_type
            )
        
        # Obtener sugerencias de mejora si es OpenAI
        if result.provider == AIProvider.OPENAI_GPT4.value and self.openai_client:
            try:
                suggestions = await self.openai_client.suggest_improvements(
                    result.code, request.description if request else ""
                )
                result.suggestions = suggestions
            except Exception as e:
                logger.warning(f"Failed to get improvement suggestions: {e}")
        
        # Calcular score de calidad básico
        result.quality_score = self._calculate_quality_score(result)
    
    def _calculate_quality_score(self, result: GenerationResult) -> float:
        """Calcula un score de calidad básico"""
        score = 7.0  # Base score
        
        # Ajustar según validación
        if result.validation_result:
            if result.validation_result["is_valid"]:
                score += 1.0
            else:
                score -= 2.0
            
            # Penalizar por errores
            score -= len(result.validation_result.get("errors", [])) * 0.5
            score -= len(result.validation_result.get("warnings", [])) * 0.2
        
        # Ajustar según longitud del código (más código generalmente es mejor)
        code_length = len(result.code)
        if code_length > 1000:
            score += 1.0
        elif code_length < 200:
            score -= 1.0
        
        # Ajustar según tiempo de respuesta (más rápido es mejor)
        if result.response_time < 2.0:
            score += 0.5
        elif result.response_time > 10.0:
            score -= 0.5
        
        return max(1.0, min(10.0, score))
    
    def _update_avg_response_time(self, response_time: float):
        """Actualiza el tiempo promedio de respuesta"""
        total_requests = self.generation_stats["total_requests"]
        current_avg = self.generation_stats["avg_response_time"]
        
        new_avg = ((current_avg * (total_requests - 1)) + response_time) / total_requests
        self.generation_stats["avg_response_time"] = new_avg
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de generación"""
        stats = self.generation_stats.copy()
        stats["success_rate"] = (
            stats["successful_generations"] / max(stats["total_requests"], 1)
        ) * 100
        stats["avg_cost_per_request"] = (
            stats["total_cost"] / max(stats["successful_generations"], 1)
        )
        return stats
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica el estado de los clientes de IA"""
        health = {
            "status": "healthy",
            "providers": {},
            "timestamp": time.time()
        }
        
        # Verificar OpenAI
        if self.openai_client:
            try:
                is_valid = await self.openai_client.validate_api_key()
                health["providers"]["openai"] = {
                    "status": "available" if is_valid else "error",
                    "models": await self.openai_client.get_available_models()
                }
            except Exception as e:
                health["providers"]["openai"] = {
                    "status": "error",
                    "error": str(e)
                }
        else:
            health["providers"]["openai"] = {"status": "not_configured"}
        
        # Verificar Claude
        if self.claude_client:
            try:
                is_valid = await self.claude_client.validate_api_key()
                health["providers"]["claude"] = {
                    "status": "available" if is_valid else "error",
                    "models": await self.claude_client.get_available_models()
                }
            except Exception as e:
                health["providers"]["claude"] = {
                    "status": "error",
                    "error": str(e)
                }
        else:
            health["providers"]["claude"] = {"status": "not_configured"}
        
        # Determinar estado general
        available_providers = [
            p for p in health["providers"].values()
            if p["status"] == "available"
        ]
        
        if not available_providers:
            health["status"] = "error"
        elif len(available_providers) == 1:
            health["status"] = "degraded"
        
        return health


# Instancia global del generador de código
code_generator = None

async def get_code_generator() -> CodeGenerator:
    """Obtiene instancia singleton del generador de código"""
    global code_generator
    if code_generator is None:
        code_generator = CodeGenerator()
        await code_generator.initialize_clients()
    return code_generator