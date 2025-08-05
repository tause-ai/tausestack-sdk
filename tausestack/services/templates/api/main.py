"""
Template Engine API - FastAPI endpoints para gestión de templates
"""
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import json
from pathlib import Path

try:
    from ..schemas.template_schema import (
        TemplateSchema, TemplateGenerationRequest, TemplateGenerationResponse,
        TemplateMetadata, TemplateCategory, ComponentType
    )
    from ..core.engine import TemplateEngine
    from ..storage.template_loader import TemplateRegistry
except ImportError:
    # Fallback para imports relativos
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from schemas.template_schema import (
        TemplateSchema, TemplateGenerationRequest, TemplateGenerationResponse,
        TemplateMetadata, TemplateCategory, ComponentType
    )
    from core.engine import TemplateEngine
    from storage.template_loader import TemplateRegistry

app = FastAPI(
    title="TauseStack Template Engine",
    description="API para gestión y generación de templates con shadcn/ui",
    version="0.8.0"
)

# Instancia global del engine
template_engine = TemplateEngine()
template_registry = TemplateRegistry()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "template-engine", "version": "0.8.0"}


@app.get("/templates", response_model=List[TemplateMetadata])
async def list_templates(
    category: Optional[TemplateCategory] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """Lista todos los templates disponibles"""
    try:
        templates = await template_registry.list_templates(
            category=category,
            search=search,
            limit=limit,
            offset=offset
        )
        return templates
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/templates/{template_id}", response_model=TemplateSchema)
async def get_template(template_id: str):
    """Obtiene un template específico por ID"""
    template = template_engine.load_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template {template_id} not found")
    return template


@app.post("/templates/{template_id}/generate", response_model=TemplateGenerationResponse)
async def generate_project(
    template_id: str,
    request: TemplateGenerationRequest,
    background_tasks: BackgroundTasks
):
    """Genera un proyecto completo desde un template"""
    try:
        # Validar que el template existe
        template = template_engine.load_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail=f"Template {template_id} not found")
        
        # Actualizar request con template_id
        request.template_id = template_id
        
        # Generar proyecto
        result = template_engine.generate_project(request)
        
        if not result.success:
            raise HTTPException(status_code=400, detail=result.errors)
        
        # Programar tareas en background (deployment, etc.)
        background_tasks.add_task(
            deploy_generated_project,
            result.project_id,
            request.tenant_id
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/templates/{template_id}/preview")
async def preview_template(template_id: str):
    """Genera preview HTML del template"""
    try:
        template = template_engine.load_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail=f"Template {template_id} not found")
        
        # Generar preview básico
        preview_html = generate_template_preview(template)
        
        return JSONResponse(
            content={"html": preview_html, "template_id": template_id},
            headers={"Content-Type": "application/json"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/components", response_model=List[str])
async def list_available_components():
    """Lista todos los componentes disponibles (shadcn/ui)"""
    return [component.value for component in ComponentType]


@app.get("/components/{component_type}/variants")
async def get_component_variants(component_type: str):
    """Obtiene las variantes disponibles para un componente"""
    try:
        component_enum = ComponentType(component_type)
        variants = get_shadcn_variants(component_enum)
        return {"component": component_type, "variants": variants}
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Component {component_type} not found")


@app.post("/templates", response_model=TemplateSchema)
async def create_template(template: TemplateSchema):
    """Crea un nuevo template"""
    try:
        # Validar template
        await template_registry.validate_template(template)
        
        # Guardar template
        saved_template = await template_registry.save_template(template)
        
        return saved_template
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/templates/{template_id}", response_model=TemplateSchema)
async def update_template(template_id: str, template: TemplateSchema):
    """Actualiza un template existente"""
    try:
        # Verificar que existe
        existing = template_engine.load_template(template_id)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Template {template_id} not found")
        
        # Actualizar ID
        template.id = template_id
        
        # Validar y guardar
        await template_registry.validate_template(template)
        updated_template = await template_registry.save_template(template)
        
        return updated_template
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/templates/{template_id}")
async def delete_template(template_id: str):
    """Elimina un template"""
    try:
        success = await template_registry.delete_template(template_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Template {template_id} not found")
        
        return {"message": f"Template {template_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/projects/{project_id}/status")
async def get_project_status(project_id: str):
    """Obtiene el estado de un proyecto generado"""
    try:
        status = await get_generation_status(project_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")


# Funciones auxiliares

async def deploy_generated_project(project_id: str, tenant_id: Optional[str]):
    """Tarea en background para deploy de proyecto generado"""
    try:
        # Aquí implementaríamos el deployment automático
        # Por ahora, solo log
        print(f"Deploying project {project_id} for tenant {tenant_id}")
        
        # Simular deployment
        import asyncio
        await asyncio.sleep(5)
        
        print(f"Project {project_id} deployed successfully")
        
    except Exception as e:
        print(f"Error deploying project {project_id}: {e}")


def generate_template_preview(template: TemplateSchema) -> str:
    """Genera HTML preview del template"""
    # Preview básico con componentes shadcn/ui
    preview_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{template.metadata.name} - Preview</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            /* shadcn/ui CSS variables */
            :root {{
                --background: 0 0% 100%;
                --foreground: 222.2 84% 4.9%;
                --card: 0 0% 100%;
                --card-foreground: 222.2 84% 4.9%;
                --popover: 0 0% 100%;
                --popover-foreground: 222.2 84% 4.9%;
                --primary: 222.2 47.4% 11.2%;
                --primary-foreground: 210 40% 98%;
                --secondary: 210 40% 96%;
                --secondary-foreground: 222.2 84% 4.9%;
                --muted: 210 40% 96%;
                --muted-foreground: 215.4 16.3% 46.9%;
                --accent: 210 40% 96%;
                --accent-foreground: 222.2 84% 4.9%;
                --destructive: 0 84.2% 60.2%;
                --destructive-foreground: 210 40% 98%;
                --border: 214.3 31.8% 91.4%;
                --input: 214.3 31.8% 91.4%;
                --ring: 222.2 84% 4.9%;
                --radius: 0.5rem;
            }}
        </style>
    </head>
    <body class="bg-background text-foreground">
        <div class="container mx-auto py-8">
            <h1 class="text-3xl font-bold mb-4">{template.metadata.name}</h1>
            <p class="text-muted-foreground mb-8">{template.metadata.description}</p>
            
            <div class="grid gap-6">
    """
    
    # Agregar preview de páginas
    for page in template.pages:
        preview_html += f"""
                <div class="border rounded-lg p-6">
                    <h2 class="text-xl font-semibold mb-4">{page.name}</h2>
                    <div class="bg-muted p-4 rounded">
                        <p class="text-sm text-muted-foreground">
                            Página con {len(page.components)} componentes
                        </p>
                    </div>
                </div>
        """
    
    preview_html += """
            </div>
        </div>
    </body>
    </html>
    """
    
    return preview_html


def get_shadcn_variants(component_type: ComponentType) -> List[Dict[str, Any]]:
    """Obtiene variantes de componente shadcn/ui"""
    variants = {
        ComponentType.BUTTON: [
            {"name": "default", "description": "Default button style"},
            {"name": "destructive", "description": "Destructive action button"},
            {"name": "outline", "description": "Outlined button"},
            {"name": "secondary", "description": "Secondary button"},
            {"name": "ghost", "description": "Ghost button"},
            {"name": "link", "description": "Link-styled button"},
        ],
        ComponentType.CARD: [
            {"name": "default", "description": "Default card style"},
        ],
        ComponentType.BADGE: [
            {"name": "default", "description": "Default badge"},
            {"name": "secondary", "description": "Secondary badge"},
            {"name": "destructive", "description": "Destructive badge"},
            {"name": "outline", "description": "Outlined badge"},
        ],
    }
    
    return variants.get(component_type, [{"name": "default", "description": "Default variant"}])


async def get_generation_status(project_id: str) -> Dict[str, Any]:
    """Obtiene estado de generación de proyecto"""
    # Aquí implementaríamos la lógica real de estado
    return {
        "project_id": project_id,
        "status": "completed",
        "progress": 100,
        "files_generated": 15,
        "deployment_status": "pending",
        "preview_url": f"/preview/{project_id}",
        "created_at": "2024-01-15T10:30:00Z"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)