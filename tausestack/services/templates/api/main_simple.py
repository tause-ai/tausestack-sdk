#!/usr/bin/env python3
"""
Template Engine API - Versión Simplificada
Microservicio de gestión de templates para TauseStack v0.8.0
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
import json
import logging
from datetime import datetime
import uuid
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="TauseStack Template Engine",
    description="API para gestión y generación de templates con shadcn/ui",
    version="0.8.0",
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

class TemplateMetadata(BaseModel):
    """Metadatos de un template"""
    id: str
    name: str
    description: str
    category: str
    version: str
    author: str
    created_at: datetime
    updated_at: datetime
    downloads: int = 0
    rating: float = 0.0
    tags: List[str] = []

class TemplateGenerationRequest(BaseModel):
    """Request para generación de proyecto desde template"""
    template_id: str
    project_name: str
    tenant_id: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    features: List[str] = Field(default_factory=list)
    styling: str = Field(default="modern", description="Estilo preferido")

class TemplateGenerationResponse(BaseModel):
    """Respuesta de generación de proyecto"""
    success: bool
    project_id: str
    template_id: str
    generated_files: List[str] = []
    deployment_url: Optional[str] = None
    errors: List[str] = []
    warnings: List[str] = []
    generated_at: datetime = Field(default_factory=datetime.utcnow)

class ComponentType(BaseModel):
    """Tipo de componente"""
    name: str
    description: str
    variants: List[str] = []

# === Endpoints ===

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "service": "TauseStack Template Engine",
        "version": "0.8.0",
        "status": "operational",
        "endpoints": [
            "/health",
            "/templates",
            "/templates/{template_id}",
            "/templates/{template_id}/generate",
            "/components"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check del servicio"""
    return {
        "status": "healthy",
        "service": "template-engine",
        "version": "0.8.0",
        "timestamp": datetime.utcnow().isoformat(),
        "templates_available": 5,
        "components_available": 12,
        "categories": ["website", "dashboard", "ecommerce", "landing"]
    }

@app.get("/templates", response_model=List[TemplateMetadata])
async def list_templates(
    category: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """Lista todos los templates disponibles"""
    try:
        # Simulación de templates
        templates = [
            TemplateMetadata(
                id="website-modern",
                name="Modern Website",
                description="Website moderno con Next.js y Tailwind",
                category="website",
                version="1.0.0",
                author="TauseStack",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                downloads=150,
                rating=4.8,
                tags=["nextjs", "tailwind", "modern"]
            ),
            TemplateMetadata(
                id="dashboard-admin",
                name="Admin Dashboard",
                description="Dashboard administrativo completo",
                category="dashboard",
                version="1.2.0",
                author="TauseStack",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                downloads=89,
                rating=4.6,
                tags=["dashboard", "admin", "react"]
            ),
            TemplateMetadata(
                id="ecommerce-store",
                name="E-commerce Store",
                description="Tienda online completa",
                category="ecommerce",
                version="1.1.0",
                author="TauseStack",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                downloads=67,
                rating=4.7,
                tags=["ecommerce", "store", "shopping"]
            )
        ]
        
        # Filtrar por categoría si se especifica
        if category:
            templates = [t for t in templates if t.category == category]
        
        # Filtrar por búsqueda si se especifica
        if search:
            templates = [t for t in templates if search.lower() in t.name.lower() or search.lower() in t.description.lower()]
        
        return templates[offset:offset + limit]
    except Exception as e:
        logger.error(f"Error listando templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/templates/{template_id}", response_model=TemplateMetadata)
async def get_template(template_id: str):
    """Obtiene un template específico por ID"""
    try:
        # Simulación de template
        template = TemplateMetadata(
            id=template_id,
            name=f"Template {template_id}",
            description=f"Descripción del template {template_id}",
            category="website",
            version="1.0.0",
            author="TauseStack",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            downloads=100,
            rating=4.5,
            tags=["template", "example"]
        )
        return template
    except Exception as e:
        logger.error(f"Error obteniendo template {template_id}: {e}")
        raise HTTPException(status_code=404, detail=f"Template {template_id} not found")

@app.post("/templates/{template_id}/generate", response_model=TemplateGenerationResponse)
async def generate_project(
    template_id: str,
    request: TemplateGenerationRequest,
    background_tasks: BackgroundTasks
):
    """Genera un proyecto completo desde un template"""
    try:
        # Simulación de generación
        project_id = f"proj_{uuid.uuid4().hex[:8]}"
        
        result = TemplateGenerationResponse(
            success=True,
            project_id=project_id,
            template_id=template_id,
            generated_files=[
                "src/components/Header.tsx",
                "src/components/Footer.tsx",
                "src/pages/index.tsx",
                "src/styles/globals.css",
                "package.json",
                "README.md"
            ],
            deployment_url=f"https://{project_id}.vercel.app",
            errors=[],
            warnings=["Considerar optimizar imágenes"],
            generated_at=datetime.utcnow()
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error generando proyecto: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/components", response_model=List[str])
async def list_available_components():
    """Lista todos los componentes disponibles"""
    return [
        "Button", "Card", "Input", "Modal", "Dropdown",
        "Table", "Form", "Navigation", "Sidebar", "Footer",
        "Header", "Breadcrumb"
    ]

@app.get("/components/{component_type}/variants")
async def get_component_variants(component_type: str):
    """Obtiene las variantes disponibles para un componente"""
    variants = {
        "Button": ["primary", "secondary", "outline", "ghost", "destructive"],
        "Card": ["default", "elevated", "bordered", "interactive"],
        "Input": ["text", "email", "password", "number", "textarea"],
        "Modal": ["default", "fullscreen", "side-panel"]
    }
    
    return {
        "component": component_type,
        "variants": variants.get(component_type, ["default"])
    }

@app.get("/stats")
async def get_template_stats():
    """Estadísticas de templates"""
    return {
        "total_templates": 5,
        "total_downloads": 306,
        "average_rating": 4.7,
        "categories": {
            "website": 2,
            "dashboard": 1,
            "ecommerce": 1,
            "landing": 1
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8013, reload=True) 