"""
AI Client - Cliente principal para interactuar con TauseStack AI Services
"""
import httpx
import asyncio
from typing import Dict, List, Optional, Any, AsyncGenerator
import json
from dataclasses import dataclass
from enum import Enum
import logging

# Importar configuración centralizada
try:
    from tausestack.config.settings import settings
    DEFAULT_AI_URL = settings.AI_SERVICES_URL
except ImportError:
    DEFAULT_AI_URL = "http://localhost:8005"

logger = logging.getLogger(__name__)


class GenerationStrategy(str, Enum):
    """Estrategias de generación"""
    FAST = "fast"
    QUALITY = "quality"
    BALANCED = "balanced"
    MULTI_PROVIDER = "multi_provider"
    ADAPTIVE = "adaptive"


@dataclass
class AIResponse:
    """Respuesta del servicio de IA"""
    success: bool
    code: str
    provider: str
    model: str
    tokens_used: int
    cost_estimate: float
    response_time: float
    quality_score: Optional[float] = None
    suggestions: List[str] = None
    explanation: Optional[str] = None
    session_id: Optional[str] = None


class AIClient:
    """Cliente para interactuar con TauseStack AI Services"""
    
    def __init__(self, base_url: str = DEFAULT_AI_URL, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session_id = None
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0),
            headers={"Content-Type": "application/json"}
        )
        if api_key:
            self.client.headers["Authorization"] = f"Bearer {api_key}"
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica el estado del servicio de IA"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def generate_component(
        self,
        description: str,
        component_type: str = "component",
        required_props: List[str] = None,
        features: List[str] = None,
        styling_preferences: str = "modern",
        strategy: GenerationStrategy = GenerationStrategy.BALANCED,
        session_id: Optional[str] = None
    ) -> AIResponse:
        """Genera un componente React/TypeScript"""
        
        payload = {
            "description": description,
            "component_type": component_type,
            "required_props": required_props or [],
            "features": features or [],
            "styling_preferences": styling_preferences,
            "strategy": strategy.value,
            "session_id": session_id or self.session_id
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/generate/component",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            return AIResponse(
                success=data["success"],
                code=data["code"],
                provider=data["provider"],
                model=data["model"],
                tokens_used=data["tokens_used"],
                cost_estimate=data["cost_estimate"],
                response_time=data["response_time"],
                quality_score=data.get("quality_score"),
                suggestions=data.get("suggestions", []),
                explanation=data.get("explanation"),
                session_id=data.get("session_id")
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error generating component: {e}")
            raise
        except Exception as e:
            logger.error(f"Error generating component: {e}")
            raise
    
    async def generate_api_endpoint(
        self,
        description: str,
        http_method: str,
        route: str,
        parameters: List[str] = None,
        session_id: Optional[str] = None
    ) -> AIResponse:
        """Genera un endpoint de API"""
        
        payload = {
            "description": description,
            "http_method": http_method,
            "route": route,
            "parameters": parameters or [],
            "session_id": session_id or self.session_id
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/generate/api",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            return AIResponse(
                success=data["success"],
                code=data["code"],
                provider=data["provider"],
                model=data["model"],
                tokens_used=data["tokens_used"],
                cost_estimate=data["cost_estimate"],
                response_time=data["response_time"],
                quality_score=data.get("quality_score"),
                suggestions=data.get("suggestions", []),
                explanation=data.get("explanation"),
                session_id=data.get("session_id")
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error generating API: {e}")
            raise
        except Exception as e:
            logger.error(f"Error generating API: {e}")
            raise
    
    async def debug_code(
        self,
        error_code: str,
        error_message: str,
        context: str = "",
        session_id: Optional[str] = None
    ) -> AIResponse:
        """Debuggea código con errores"""
        
        payload = {
            "error_code": error_code,
            "error_message": error_message,
            "context": context,
            "session_id": session_id or self.session_id
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/debug",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            return AIResponse(
                success=data["success"],
                code=data["code"],
                provider=data["provider"],
                model=data["model"],
                tokens_used=data["tokens_used"],
                cost_estimate=data["cost_estimate"],
                response_time=data["response_time"],
                quality_score=data.get("quality_score"),
                suggestions=data.get("suggestions", []),
                explanation=data.get("explanation"),
                session_id=data.get("session_id")
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error debugging code: {e}")
            raise
        except Exception as e:
            logger.error(f"Error debugging code: {e}")
            raise
    
    async def enhance_template(
        self,
        template_code: str,
        improvement_goals: List[str],
        session_id: Optional[str] = None
    ) -> AIResponse:
        """Mejora un template existente"""
        
        payload = {
            "template_code": template_code,
            "improvement_goals": improvement_goals,
            "session_id": session_id or self.session_id
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/enhance/template",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            return AIResponse(
                success=data["success"],
                code=data["code"],
                provider=data["provider"],
                model=data["model"],
                tokens_used=data["tokens_used"],
                cost_estimate=data["cost_estimate"],
                response_time=data["response_time"],
                quality_score=data.get("quality_score"),
                suggestions=data.get("suggestions", []),
                explanation=data.get("explanation"),
                session_id=data.get("session_id")
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error enhancing template: {e}")
            raise
        except Exception as e:
            logger.error(f"Error enhancing template: {e}")
            raise
    
    async def generate_multiple_options(
        self,
        description: str,
        num_options: int = 3,
        component_type: str = "component",
        required_props: List[str] = None,
        features: List[str] = None,
        styling_preferences: str = "modern",
        strategy: GenerationStrategy = GenerationStrategy.MULTI_PROVIDER
    ) -> Dict[str, Any]:
        """Genera múltiples opciones de código"""
        
        base_request = {
            "description": description,
            "component_type": component_type,
            "required_props": required_props or [],
            "features": features or [],
            "styling_preferences": styling_preferences,
            "strategy": strategy.value,
            "session_id": self.session_id
        }
        
        payload = {
            "base_request": base_request,
            "num_options": num_options
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/generate/multiple",
                json=payload
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error generating multiple options: {e}")
            raise
        except Exception as e:
            logger.error(f"Error generating multiple options: {e}")
            raise
    
    async def chat(
        self,
        message: str,
        session_id: Optional[str] = None,
        context_type: str = "general"
    ) -> Dict[str, Any]:
        """Chat directo con IA"""
        
        payload = {
            "message": message,
            "session_id": session_id or self.session_id,
            "context_type": context_type
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/chat",
                json=payload
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error in chat: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            raise
    
    async def generate_component_stream(
        self,
        description: str,
        component_type: str = "component",
        required_props: List[str] = None,
        features: List[str] = None,
        styling_preferences: str = "modern",
        strategy: GenerationStrategy = GenerationStrategy.BALANCED
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Genera componente con streaming"""
        
        payload = {
            "description": description,
            "component_type": component_type,
            "required_props": required_props or [],
            "features": features or [],
            "styling_preferences": styling_preferences,
            "strategy": strategy.value,
            "session_id": self.session_id,
            "stream": True
        }
        
        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/generate/component/stream",
                json=payload
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])  # Remove "data: " prefix
                            yield data
                        except json.JSONDecodeError:
                            continue
                            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error in streaming: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in streaming: {e}")
            raise
    
    async def get_providers(self) -> Dict[str, Any]:
        """Obtiene información de proveedores de IA"""
        try:
            response = await self.client.get(f"{self.base_url}/providers")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting providers: {e}")
            raise
    
    async def get_templates(self) -> Dict[str, Any]:
        """Obtiene templates de prompts disponibles"""
        try:
            response = await self.client.get(f"{self.base_url}/templates")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting templates: {e}")
            raise
    
    async def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de generación"""
        try:
            response = await self.client.get(f"{self.base_url}/stats")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            raise
    
    async def clear_session(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Limpia el contexto de una sesión"""
        sid = session_id or self.session_id
        if not sid:
            raise ValueError("No session ID provided")
        
        try:
            response = await self.client.delete(f"{self.base_url}/session/{sid}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error clearing session: {e}")
            raise
    
    def set_session_id(self, session_id: str):
        """Establece el ID de sesión para mantener contexto"""
        self.session_id = session_id
    
    async def close(self):
        """Cierra el cliente HTTP"""
        await self.client.aclose()


# Funciones de conveniencia
async def generate_component(
    description: str,
    ai_service_url: str = DEFAULT_AI_URL,
    **kwargs
) -> AIResponse:
    """Función de conveniencia para generar componentes"""
    async with AIClient(ai_service_url) as client:
        return await client.generate_component(description, **kwargs)


async def debug_code(
    error_code: str,
    error_message: str,
    ai_service_url: str = DEFAULT_AI_URL,
    **kwargs
) -> AIResponse:
    """Función de conveniencia para debugging"""
    async with AIClient(ai_service_url) as client:
        return await client.debug_code(error_code, error_message, **kwargs)