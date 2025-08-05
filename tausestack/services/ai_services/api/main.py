"""
AI Services API - Microservicio de integración con IA para TauseStack v0.9.0
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
import asyncio
import json
import logging
from datetime import datetime
import uuid

try:
    from ..core.code_generator import (
        CodeGenerator, 
        GenerationRequest, 
        GenerationResult, 
        GenerationStrategy,
        get_code_generator
    )
    from ..core.prompt_engine import PromptType, AIProvider
except ImportError:
    # Fallback para imports relativos
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from core.code_generator import (
        CodeGenerator, 
        GenerationRequest, 
        GenerationResult, 
        GenerationStrategy,
        get_code_generator
    )
    from core.prompt_engine import PromptType, AIProvider


# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="TauseStack AI Services",
    description="Microservicio de integración con IA para generación de código y asistencia",
    version="0.9.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios exactos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === Modelos de Request/Response ===

class ComponentGenerationRequest(BaseModel):
    """Request para generación de componentes"""
    description: str = Field(..., description="Descripción del componente a generar")
    component_type: str = Field(default="component", description="Tipo de componente")
    required_props: List[str] = Field(default=[], description="Props requeridas")
    features: List[str] = Field(default=[], description="Funcionalidades específicas")
    styling_preferences: str = Field(default="modern", description="Preferencias de estilo")
    strategy: GenerationStrategy = Field(default=GenerationStrategy.BALANCED, description="Estrategia de generación")
    session_id: Optional[str] = Field(default=None, description="ID de sesión para contexto")
    stream: bool = Field(default=False, description="Respuesta en streaming")
    
    class Config:
        schema_extra = {
            "example": {
                "description": "Un dashboard de métricas de ventas con gráficos",
                "component_type": "dashboard",
                "required_props": ["salesData", "period"],
                "features": ["responsive", "interactive charts", "export data"],
                "styling_preferences": "modern dark theme",
                "strategy": "quality",
                "session_id": "user_123_session",
                "stream": False
            }
        }


class APIGenerationRequest(BaseModel):
    """Request para generación de endpoints de API"""
    description: str = Field(..., description="Descripción del endpoint")
    http_method: str = Field(..., description="Método HTTP (GET, POST, etc.)")
    route: str = Field(..., description="Ruta del endpoint")
    parameters: List[str] = Field(default=[], description="Parámetros del endpoint")
    session_id: Optional[str] = Field(default=None, description="ID de sesión")
    
    class Config:
        schema_extra = {
            "example": {
                "description": "Endpoint para crear un nuevo usuario",
                "http_method": "POST",
                "route": "/api/users",
                "parameters": ["name", "email", "password"],
                "session_id": "dev_session_456"
            }
        }


class DebugRequest(BaseModel):
    """Request para debugging de código"""
    error_code: str = Field(..., description="Código con error")
    error_message: str = Field(..., description="Mensaje de error")
    context: str = Field(default="", description="Contexto adicional")
    session_id: Optional[str] = Field(default=None, description="ID de sesión")


class TemplateEnhancementRequest(BaseModel):
    """Request para mejora de templates"""
    template_code: str = Field(..., description="Código del template actual")
    improvement_goals: List[str] = Field(..., description="Objetivos de mejora")
    session_id: Optional[str] = Field(default=None, description="ID de sesión")


class MultiGenerationRequest(BaseModel):
    """Request para generación múltiple"""
    base_request: ComponentGenerationRequest
    num_options: int = Field(default=3, ge=1, le=5, description="Número de opciones")


class GenerationResponse(BaseModel):
    """Respuesta de generación"""
    success: bool
    code: str
    provider: str
    model: str
    tokens_used: int
    cost_estimate: float
    response_time: float
    quality_score: Optional[float] = None
    validation_result: Optional[Dict] = None
    suggestions: List[str] = []
    explanation: Optional[str] = None
    session_id: Optional[str] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class MultiGenerationResponse(BaseModel):
    """Respuesta de generación múltiple"""
    success: bool
    options: List[GenerationResponse]
    best_option_index: int
    total_cost: float
    comparison_notes: str


class ChatMessage(BaseModel):
    """Mensaje de chat con IA"""
    message: str = Field(..., description="Mensaje del usuario")
    session_id: str = Field(..., description="ID de sesión")
    context_type: str = Field(default="general", description="Tipo de contexto")


class ChatResponse(BaseModel):
    """Respuesta de chat"""
    response: str
    session_id: str
    provider: str
    tokens_used: int
    cost_estimate: float


# === Dependencias ===

async def get_generator() -> CodeGenerator:
    """Dependencia para obtener el generador de código"""
    return await get_code_generator()


# === Endpoints Principales ===

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "service": "TauseStack AI Services",
        "version": "0.9.0",
        "status": "active",
        "capabilities": [
            "React/TypeScript component generation",
            "API endpoint generation", 
            "Code debugging assistance",
            "Template enhancement",
            "Multi-provider AI integration"
        ]
    }


@app.get("/health")
async def health_check(generator: CodeGenerator = Depends(get_generator)):
    """Health check del servicio"""
    try:
        health_status = await generator.health_check()
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "ai_providers": health_status,
            "stats": generator.get_stats()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@app.post("/generate/component", response_model=GenerationResponse)
async def generate_component(
    request: ComponentGenerationRequest,
    generator: CodeGenerator = Depends(get_generator)
):
    """Genera un componente React/TypeScript"""
    try:
        # Crear request interno
        gen_request = GenerationRequest(
            description=request.description,
            component_type=request.component_type,
            required_props=request.required_props,
            features=request.features,
            styling_preferences=request.styling_preferences,
            strategy=request.strategy,
            session_id=request.session_id or str(uuid.uuid4()),
            stream=request.stream
        )
        
        # Generar componente
        result = await generator.generate_component(gen_request)
        
        return GenerationResponse(
            success=True,
            code=result.code,
            provider=result.provider,
            model=result.model,
            tokens_used=result.tokens_used,
            cost_estimate=result.cost_estimate,
            response_time=result.response_time,
            quality_score=result.quality_score,
            validation_result=result.validation_result,
            suggestions=result.suggestions or [],
            explanation=result.explanation,
            session_id=gen_request.session_id
        )
        
    except Exception as e:
        logger.error(f"Error generating component: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate/api", response_model=GenerationResponse)
async def generate_api_endpoint(
    request: APIGenerationRequest,
    generator: CodeGenerator = Depends(get_generator)
):
    """Genera un endpoint de API"""
    try:
        result = await generator.generate_api_endpoint(
            description=request.description,
            http_method=request.http_method,
            route=request.route,
            parameters=request.parameters,
            session_id=request.session_id or str(uuid.uuid4())
        )
        
        return GenerationResponse(
            success=True,
            code=result.code,
            provider=result.provider,
            model=result.model,
            tokens_used=result.tokens_used,
            cost_estimate=result.cost_estimate,
            response_time=result.response_time,
            quality_score=result.quality_score,
            validation_result=result.validation_result,
            suggestions=result.suggestions or [],
            explanation=result.explanation,
            session_id=request.session_id
        )
        
    except Exception as e:
        logger.error(f"Error generating API endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/debug", response_model=GenerationResponse)
async def debug_code(
    request: DebugRequest,
    generator: CodeGenerator = Depends(get_generator)
):
    """Debuggea código con errores"""
    try:
        result = await generator.debug_code(
            error_code=request.error_code,
            error_message=request.error_message,
            context=request.context,
            session_id=request.session_id or str(uuid.uuid4())
        )
        
        return GenerationResponse(
            success=True,
            code=result.code,
            provider=result.provider,
            model=result.model,
            tokens_used=result.tokens_used,
            cost_estimate=result.cost_estimate,
            response_time=result.response_time,
            quality_score=result.quality_score,
            validation_result=result.validation_result,
            suggestions=result.suggestions or [],
            explanation=result.explanation,
            session_id=request.session_id
        )
        
    except Exception as e:
        logger.error(f"Error debugging code: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/enhance/template", response_model=GenerationResponse)
async def enhance_template(
    request: TemplateEnhancementRequest,
    generator: CodeGenerator = Depends(get_generator)
):
    """Mejora un template existente"""
    try:
        result = await generator.enhance_template(
            template_code=request.template_code,
            improvement_goals=request.improvement_goals,
            session_id=request.session_id or str(uuid.uuid4())
        )
        
        return GenerationResponse(
            success=True,
            code=result.code,
            provider=result.provider,
            model=result.model,
            tokens_used=result.tokens_used,
            cost_estimate=result.cost_estimate,
            response_time=result.response_time,
            quality_score=result.quality_score,
            validation_result=result.validation_result,
            suggestions=result.suggestions or [],
            explanation=result.explanation,
            session_id=request.session_id
        )
        
    except Exception as e:
        logger.error(f"Error enhancing template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate/multiple", response_model=MultiGenerationResponse)
async def generate_multiple_options(
    request: MultiGenerationRequest,
    generator: CodeGenerator = Depends(get_generator)
):
    """Genera múltiples opciones de código"""
    try:
        # Crear request interno
        gen_request = GenerationRequest(
            description=request.base_request.description,
            component_type=request.base_request.component_type,
            required_props=request.base_request.required_props,
            features=request.base_request.features,
            styling_preferences=request.base_request.styling_preferences,
            strategy=request.base_request.strategy,
            session_id=request.base_request.session_id or str(uuid.uuid4())
        )
        
        # Generar múltiples opciones
        results = await generator.generate_multiple_options(gen_request, request.num_options)
        
        # Convertir a respuestas
        options = []
        total_cost = 0.0
        
        for result in results:
            options.append(GenerationResponse(
                success=True,
                code=result.code,
                provider=result.provider,
                model=result.model,
                tokens_used=result.tokens_used,
                cost_estimate=result.cost_estimate,
                response_time=result.response_time,
                quality_score=result.quality_score,
                validation_result=result.validation_result,
                suggestions=result.suggestions or [],
                explanation=result.explanation,
                session_id=gen_request.session_id
            ))
            total_cost += result.cost_estimate
        
        # Determinar mejor opción (por quality_score)
        best_index = 0
        best_score = 0.0
        for i, option in enumerate(options):
            if option.quality_score and option.quality_score > best_score:
                best_score = option.quality_score
                best_index = i
        
        comparison_notes = f"Se generaron {len(options)} opciones. La mejor opción (índice {best_index}) tiene un score de calidad de {best_score:.1f}/10."
        
        return MultiGenerationResponse(
            success=True,
            options=options,
            best_option_index=best_index,
            total_cost=total_cost,
            comparison_notes=comparison_notes
        )
        
    except Exception as e:
        logger.error(f"Error generating multiple options: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    message: ChatMessage,
    generator: CodeGenerator = Depends(get_generator)
):
    """Chat directo con IA para asistencia"""
    try:
        # Para chat general, usar una generación simple
        gen_request = GenerationRequest(
            description=message.message,
            component_type="chat_response",
            template_id="react_component_generation",  # Usar template base
            session_id=message.session_id,
            strategy=GenerationStrategy.FAST
        )
        
        result = await generator.generate_component(gen_request)
        
        return ChatResponse(
            response=result.code,
            session_id=message.session_id,
            provider=result.provider,
            tokens_used=result.tokens_used,
            cost_estimate=result.cost_estimate
        )
        
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# === Endpoints de Información ===

@app.get("/providers")
async def get_providers(generator: CodeGenerator = Depends(get_generator)):
    """Obtiene información de proveedores de IA disponibles"""
    health = await generator.health_check()
    return {
        "providers": health["providers"],
        "preferences": {
            "component_generation": "openai_gpt4",
            "template_enhancement": "anthropic_claude",
            "debugging": "openai_gpt4",
            "api_generation": "openai_gpt4"
        }
    }


@app.get("/templates")
async def get_templates(generator: CodeGenerator = Depends(get_generator)):
    """Obtiene templates de prompts disponibles"""
    templates = generator.prompt_engine.list_templates()
    return {
        "templates": [
            {
                "id": t.id,
                "name": t.name,
                "type": t.type,
                "provider": t.provider,
                "variables": t.variables,
                "max_tokens": t.max_tokens,
                "temperature": t.temperature
            }
            for t in templates
        ]
    }


@app.get("/stats")
async def get_generation_stats(generator: CodeGenerator = Depends(get_generator)):
    """Obtiene estadísticas de generación"""
    return generator.get_stats()


@app.delete("/session/{session_id}")
async def clear_session(
    session_id: str,
    generator: CodeGenerator = Depends(get_generator)
):
    """Limpia el contexto de una sesión"""
    generator.prompt_engine.clear_context(session_id)
    return {"message": f"Session {session_id} cleared"}


# === Streaming Endpoints ===

@app.post("/generate/component/stream")
async def generate_component_stream(
    request: ComponentGenerationRequest,
    generator: CodeGenerator = Depends(get_generator)
):
    """Genera componente con respuesta en streaming"""
    
    async def generate_stream():
        try:
            # Nota: Implementación básica de streaming
            # En una implementación completa, se usaría el streaming real de los clientes
            gen_request = GenerationRequest(
                description=request.description,
                component_type=request.component_type,
                required_props=request.required_props,
                features=request.features,
                styling_preferences=request.styling_preferences,
                strategy=request.strategy,
                session_id=request.session_id or str(uuid.uuid4()),
                stream=True
            )
            
            result = await generator.generate_component(gen_request)
            
            # Simular streaming dividiendo el resultado
            code_chunks = [result.code[i:i+50] for i in range(0, len(result.code), 50)]
            
            for chunk in code_chunks:
                yield f"data: {json.dumps({'chunk': chunk, 'type': 'code'})}\n\n"
                await asyncio.sleep(0.1)  # Simular delay
            
            # Enviar metadata final
            yield f"data: {json.dumps({'type': 'complete', 'metadata': {'provider': result.provider, 'tokens': result.tokens_used}})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


# === Configuración de startup ===

@app.on_event("startup")
async def startup_event():
    """Evento de inicio de la aplicación"""
    logger.info("Iniciando AI Services...")
    
    # Inicializar generador de código
    generator = await get_code_generator()
    logger.info("AI Services iniciado correctamente")


@app.on_event("shutdown")
async def shutdown_event():
    """Evento de cierre de la aplicación"""
    logger.info("Cerrando AI Services...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005, reload=True)