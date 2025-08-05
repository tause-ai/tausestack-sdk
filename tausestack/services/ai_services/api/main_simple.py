#!/usr/bin/env python3
"""
AI Services API - Versión Simplificada
Microservicio de integración con IA para TauseStack v0.9.0
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
    allow_origins=["*"],
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
    session_id: Optional[str] = Field(default=None, description="ID de sesión para contexto")
    stream: bool = Field(default=False, description="Respuesta en streaming")

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
    suggestions: List[str] = []
    explanation: Optional[str] = None
    session_id: Optional[str] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)

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

# === Endpoints ===

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "service": "TauseStack AI Services",
        "version": "0.9.0",
        "status": "operational",
        "endpoints": [
            "/health",
            "/generate/component",
            "/chat",
            "/providers"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check del servicio"""
    return {
        "status": "healthy",
        "service": "ai-services",
        "version": "0.9.0",
        "timestamp": datetime.utcnow().isoformat(),
        "providers_available": ["openai", "anthropic"],
        "models_available": ["gpt-4", "claude-3"]
    }

@app.post("/generate/component", response_model=GenerationResponse)
async def generate_component(request: ComponentGenerationRequest):
    """Generar un componente React/Next.js"""
    try:
        # Simulación de generación
        component_code = f"""
import React from 'react';

interface {request.component_type.capitalize()}Props {{
  {', '.join([f'{prop}: string' for prop in request.required_props])}
}}

export const {request.component_type.capitalize()}: React.FC<{request.component_type.capitalize()}Props> = ({{ {', '.join(request.required_props)} }}) => {{
  return (
    <div className="p-4 bg-white rounded-lg shadow">
      <h2 className="text-xl font-bold mb-4">{request.description}</h2>
      <div className="space-y-2">
        {chr(10).join([f'<p key="{prop}">{prop}: {{{prop}}}</p>' for prop in request.required_props])}
      </div>
    </div>
  );
}};
"""
        
        return GenerationResponse(
            success=True,
            code=component_code,
            provider="openai",
            model="gpt-4",
            tokens_used=150,
            cost_estimate=0.003,
            response_time=0.5,
            quality_score=0.85,
            suggestions=["Considerar agregar TypeScript types", "Implementar responsive design"],
            explanation="Componente generado con estructura básica y props tipadas",
            session_id=request.session_id
        )
    except Exception as e:
        logger.error(f"Error generando componente: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat_with_ai(message: ChatMessage):
    """Chat con IA"""
    try:
        # Simulación de respuesta
        response_text = f"Entiendo tu mensaje: '{message.message}'. Como servicio de IA, puedo ayudarte con generación de código, debugging y asistencia técnica."
        
        return ChatResponse(
            response=response_text,
            session_id=message.session_id,
            provider="anthropic",
            tokens_used=50,
            cost_estimate=0.001
        )
    except Exception as e:
        logger.error(f"Error en chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/providers")
async def get_providers():
    """Listar proveedores de IA disponibles"""
    return {
        "providers": [
            {
                "name": "OpenAI",
                "models": ["gpt-4", "gpt-3.5-turbo"],
                "status": "available"
            },
            {
                "name": "Anthropic",
                "models": ["claude-3", "claude-2"],
                "status": "available"
            }
        ]
    }

@app.get("/stats")
async def get_generation_stats():
    """Estadísticas de generación"""
    return {
        "total_generations": 0,
        "total_tokens_used": 0,
        "total_cost": 0.0,
        "average_response_time": 0.0,
        "success_rate": 0.0
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8014, reload=True) 