"""
TauseStack Component Generator - Wrapper para AI Services existente
Integra con tausestack/services/ai_services/ sin duplicar funcionalidad
"""

import asyncio
import httpx
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class GenerationStrategy(str, Enum):
    """Estrategias de generación (wrapper para ai_services)"""
    FAST = "fast"
    QUALITY = "quality"
    BALANCED = "balanced"
    MULTI_PROVIDER = "multi_provider"


@dataclass
class GenerationRequest:
    """Request de generación (wrapper)"""
    description: str
    component_type: str = "component"
    required_props: List[str] = None
    features: List[str] = None
    styling_preferences: str = "modern"
    strategy: GenerationStrategy = GenerationStrategy.BALANCED
    tenant_id: str = "default"


@dataclass
class GenerationResult:
    """Resultado de generación (wrapper)"""
    code: str
    provider: str
    model: str
    tokens_used: int
    cost_estimate: float
    response_time: float
    success: bool = True
    error: Optional[str] = None


class ComponentGenerator:
    """
    Wrapper para tausestack/services/ai_services/
    NO duplica funcionalidad, solo proporciona interfaz compatible
    """
    
    def __init__(self, tenant_id: str = "default"):
        self.tenant_id = tenant_id
        self.ai_services_url = "http://localhost:8005"  # AI Services existente
        
    async def generate_component(self, request: GenerationRequest) -> GenerationResult:
        """
        Genera componente usando AI Services existente
        Mantiene compatibilidad con ejemplos existentes
        """
        try:
            # Preparar payload para AI Services existente
            payload = {
                "description": request.description,
                "component_type": request.component_type,
                "required_props": request.required_props or [],
                "features": request.features or [],
                "styling_preferences": request.styling_preferences,
                "strategy": request.strategy.value,
                "session_id": f"{self.tenant_id}_component_gen"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ai_services_url}/generate/component",
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return GenerationResult(
                        code=data.get("code", ""),
                        provider=data.get("provider", "unknown"),
                        model=data.get("model", "unknown"),
                        tokens_used=data.get("tokens_used", 0),
                        cost_estimate=data.get("cost_estimate", 0.0),
                        response_time=data.get("response_time", 0.0),
                        success=True
                    )
                else:
                    return GenerationResult(
                        code="",
                        provider="error",
                        model="error",
                        tokens_used=0,
                        cost_estimate=0.0,
                        response_time=0.0,
                        success=False,
                        error=f"AI Services error: {response.status_code}"
                    )
                    
        except Exception as e:
            return GenerationResult(
                code="",
                provider="error", 
                model="error",
                tokens_used=0,
                cost_estimate=0.0,
                response_time=0.0,
                success=False,
                error=f"Connection error: {str(e)}"
            )
    
    async def generate_multiple_options(
        self, 
        request: GenerationRequest, 
        num_options: int = 3
    ) -> List[GenerationResult]:
        """Genera múltiples opciones usando AI Services existente"""
        try:
            payload = {
                "base_request": {
                    "description": request.description,
                    "component_type": request.component_type,
                    "required_props": request.required_props or [],
                    "features": request.features or [],
                    "styling_preferences": request.styling_preferences,
                    "strategy": request.strategy.value,
                    "session_id": f"{self.tenant_id}_multi_gen"
                },
                "num_options": num_options
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ai_services_url}/generate/multiple",
                    json=payload,
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    
                    for option in data.get("options", []):
                        results.append(GenerationResult(
                            code=option.get("code", ""),
                            provider=option.get("provider", "unknown"),
                            model=option.get("model", "unknown"),
                            tokens_used=option.get("tokens_used", 0),
                            cost_estimate=option.get("cost_estimate", 0.0),
                            response_time=option.get("response_time", 0.0),
                            success=True
                        ))
                    
                    return results
                else:
                    return [GenerationResult(
                        code="",
                        provider="error",
                        model="error", 
                        tokens_used=0,
                        cost_estimate=0.0,
                        response_time=0.0,
                        success=False,
                        error=f"AI Services error: {response.status_code}"
                    )]
                    
        except Exception as e:
            return [GenerationResult(
                code="",
                provider="error",
                model="error",
                tokens_used=0,
                cost_estimate=0.0,
                response_time=0.0,
                success=False,
                error=f"Connection error: {str(e)}"
            )]


# Instancia por defecto para compatibilidad
default_generator = ComponentGenerator()

# Funciones de conveniencia para compatibilidad con ejemplos
async def generate_component(request: GenerationRequest) -> GenerationResult:
    """Función de conveniencia que usa AI Services existente"""
    return await default_generator.generate_component(request)

async def generate_multiple_options(request: GenerationRequest, num_options: int = 3) -> List[GenerationResult]:
    """Función de conveniencia que usa AI Services existente"""
    return await default_generator.generate_multiple_options(request, num_options) 