"""
TauseStack Builder API - Siguiendo el API Pattern de TauseStack
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

from tausestack.services.builder.core.builder_service import (
    BuilderService,
    ProjectType,
    ProjectStatus,
    Project,
    BuilderStats
)
from tausestack.sdk.auth import get_current_user

# Función temporal para simular tenant
def get_current_tenant():
    """Función temporal para simular tenant"""
    return "default"


# Modelos Pydantic para validación
class CreateProjectRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., max_length=500)
    type: ProjectType
    template_id: Optional[str] = None
    tenant_id: str


class UpdateProjectRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    status: Optional[ProjectStatus] = None
    config: Optional[dict] = None


class DeployProjectRequest(BaseModel):
    domain: Optional[str] = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str
    type: str
    status: str
    tenant_id: str
    created_at: str
    updated_at: str
    components: List[dict]
    config: dict


class BuilderStatsResponse(BaseModel):
    total_projects: int
    active_builds: int
    successful_deploys: int
    failed_deploys: int
    templates_used: int


# Router principal del Builder
router = APIRouter(prefix="/api/builder", tags=["builder"])


@router.get("/health")
async def health_check():
    """
    Health check para el servicio Builder
    """
    return {"status": "healthy", "service": "tausestack-builder"}


@router.get("/stats", response_model=BuilderStatsResponse)
async def get_builder_stats(tenant_id: str = Depends(get_current_tenant)):
    """
    Obtener estadísticas del Builder para el tenant
    """
    try:
        builder_service = BuilderService(tenant_id)
        stats = await builder_service.get_stats()
        
        return BuilderStatsResponse(
            total_projects=stats.total_projects,
            active_builds=stats.active_builds,
            successful_deploys=stats.successful_deploys,
            failed_deploys=stats.failed_deploys,
            templates_used=stats.templates_used
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting builder stats: {str(e)}"
        )


@router.get("/projects", response_model=List[ProjectResponse])
async def list_projects(
    project_type: Optional[ProjectType] = None,
    status: Optional[ProjectStatus] = None,
    tenant_id: str = Depends(get_current_tenant)
):
    """
    Listar proyectos del tenant con filtros opcionales
    """
    try:
        builder_service = BuilderService(tenant_id)
        projects = await builder_service.list_projects(
            project_type=project_type,
            status=status
        )
        
        return [
            ProjectResponse(
                id=p.id,
                name=p.name,
                description=p.description,
                type=p.type.value,
                status=p.status.value,
                tenant_id=p.tenant_id,
                created_at=p.created_at,
                updated_at=p.updated_at,
                components=[
                    {
                        "id": c.id,
                        "type": c.type,
                        "name": c.name,
                        "config": c.config,
                        "dependencies": c.dependencies
                    }
                    for c in p.components
                ],
                config={
                    "domain": p.config.domain,
                    "database_type": p.config.database_type,
                    "ai_services": p.config.ai_services,
                    "notifications": p.config.notifications,
                    "analytics": p.config.analytics
                }
            )
            for p in projects
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing projects: {str(e)}"
        )


@router.post("/projects", response_model=ProjectResponse)
async def create_project(
    request: CreateProjectRequest,
    tenant_id: str = Depends(get_current_tenant)
):
    """
    Crear nuevo proyecto
    """
    try:
        # Validar que el tenant_id coincida
        if request.tenant_id != tenant_id:
            raise HTTPException(
                status_code=403,
                detail="Tenant ID mismatch"
            )
        
        builder_service = BuilderService(tenant_id)
        project = await builder_service.create_project(
            name=request.name,
            description=request.description,
            project_type=request.type,
            template_id=request.template_id
        )
        
        return ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            type=project.type.value,
            status=project.status.value,
            tenant_id=project.tenant_id,
            created_at=project.created_at,
            updated_at=project.updated_at,
            components=[
                {
                    "id": c.id,
                    "type": c.type,
                    "name": c.name,
                    "config": c.config,
                    "dependencies": c.dependencies
                }
                for c in project.components
            ],
            config={
                "domain": project.config.domain,
                "database_type": project.config.database_type,
                "ai_services": project.config.ai_services,
                "notifications": project.config.notifications,
                "analytics": project.config.analytics
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating project: {str(e)}"
        )


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    tenant_id: str = Depends(get_current_tenant)
):
    """
    Obtener proyecto específico
    """
    try:
        builder_service = BuilderService(tenant_id)
        project = await builder_service.get_project(project_id)
        
        if not project:
            raise HTTPException(
                status_code=404,
                detail="Project not found"
            )
            
        return ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            type=project.type.value,
            status=project.status.value,
            tenant_id=project.tenant_id,
            created_at=project.created_at,
            updated_at=project.updated_at,
            components=[
                {
                    "id": c.id,
                    "type": c.type,
                    "name": c.name,
                    "config": c.config,
                    "dependencies": c.dependencies
                }
                for c in project.components
            ],
            config={
                "domain": project.config.domain,
                "database_type": project.config.database_type,
                "ai_services": project.config.ai_services,
                "notifications": project.config.notifications,
                "analytics": project.config.analytics
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting project: {str(e)}"
        )


@router.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    request: UpdateProjectRequest,
    tenant_id: str = Depends(get_current_tenant)
):
    """
    Actualizar proyecto existente
    """
    try:
        builder_service = BuilderService(tenant_id)
        
        # Preparar updates
        updates = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.description is not None:
            updates["description"] = request.description
        if request.status is not None:
            updates["status"] = request.status
        if request.config is not None:
            updates["config"] = request.config
            
        project = await builder_service.update_project(project_id, updates)
        
        if not project:
            raise HTTPException(
                status_code=404,
                detail="Project not found"
            )
            
        return ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            type=project.type.value,
            status=project.status.value,
            tenant_id=project.tenant_id,
            created_at=project.created_at,
            updated_at=project.updated_at,
            components=[
                {
                    "id": c.id,
                    "type": c.type,
                    "name": c.name,
                    "config": c.config,
                    "dependencies": c.dependencies
                }
                for c in project.components
            ],
            config={
                "domain": project.config.domain,
                "database_type": project.config.database_type,
                "ai_services": project.config.ai_services,
                "notifications": project.config.notifications,
                "analytics": project.config.analytics
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating project: {str(e)}"
        )


@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: str,
    tenant_id: str = Depends(get_current_tenant)
):
    """
    Eliminar proyecto
    """
    try:
        builder_service = BuilderService(tenant_id)
        success = await builder_service.delete_project(project_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Project not found"
            )
            
        return {"message": "Project deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting project: {str(e)}"
        )


@router.post("/projects/{project_id}/build")
async def build_project(
    project_id: str,
    tenant_id: str = Depends(get_current_tenant)
):
    """
    Construir proyecto usando IA
    """
    try:
        builder_service = BuilderService(tenant_id)
        success = await builder_service.build_project(project_id)
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Failed to build project"
            )
            
        return {"message": "Project build started successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error building project: {str(e)}"
        )


@router.post("/projects/{project_id}/deploy")
async def deploy_project(
    project_id: str,
    request: DeployProjectRequest,
    tenant_id: str = Depends(get_current_tenant)
):
    """
    Desplegar proyecto
    """
    try:
        builder_service = BuilderService(tenant_id)
        success = await builder_service.deploy_project(
            project_id,
            domain=request.domain
        )
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Failed to deploy project"
            )
            
        return {"message": "Project deployed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deploying project: {str(e)}"
        )


@router.get("/templates")
async def list_templates(tenant_id: str = Depends(get_current_tenant)):
    """
    Listar templates disponibles
    TODO: Integrar con sistema de templates existente
    """
    try:
        # Templates básicos por ahora
        templates = [
            {
                "id": "web-basic",
                "name": "Web App Básica",
                "description": "Aplicación web con React + FastAPI",
                "type": "web",
                "components": ["frontend", "backend", "database"]
            },
            {
                "id": "api-rest",
                "name": "API REST",
                "description": "API REST con FastAPI y documentación",
                "type": "api",
                "components": ["backend", "database", "docs"]
            },
            {
                "id": "agent-ai",
                "name": "Agente IA",
                "description": "Agente IA con MCP y herramientas",
                "type": "agent",
                "components": ["agent", "tools", "memory"]
            },
            {
                "id": "ecommerce-basic",
                "name": "E-commerce Básico",
                "description": "Tienda online con carrito y pagos",
                "type": "ecommerce",
                "components": ["frontend", "backend", "database", "payments"]
            },
            {
                "id": "dashboard-analytics",
                "name": "Dashboard Analytics",
                "description": "Dashboard con métricas y gráficos",
                "type": "dashboard",
                "components": ["frontend", "backend", "analytics"]
            }
        ]
        
        return templates
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing templates: {str(e)}"
        )


# Incluir el router en la aplicación principal
def include_builder_api(app):
    """
    Incluir las rutas del Builder en la aplicación FastAPI
    """
    app.include_router(router) 