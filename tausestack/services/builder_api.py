#!/usr/bin/env python3
"""
TauseStack Builder API Service

API Service para builders externos (TausePro, etc.)
Proporciona endpoints v1 para creación de apps, gestión de templates y deployment.
"""

import asyncio
import json
import uuid
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import aiofiles
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

# Importar autenticación
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from tausestack.sdk.auth.main import require_user, get_current_user
from tausestack.sdk.auth.base import User


# ========================= MODELS =========================

class TemplateListResponse(BaseModel):
    id: str
    name: str
    description: str
    version: str
    author: str
    tags: List[str]
    category: str
    preview_image: Optional[str]
    demo_url: Optional[str]
    created_at: datetime
    updated_at: datetime

class TemplateDetailResponse(BaseModel):
    id: str
    metadata: Dict[str, Any]
    configuration: Dict[str, Any]
    dependencies: Dict[str, Any]
    pages: List[Dict[str, Any]]
    components: List[Dict[str, Any]]
    theme: Dict[str, str]
    environment_variables: List[Dict[str, Any]]
    database_schema: Optional[Dict[str, Any]]
    api_routes: List[Dict[str, Any]]

class AppCreateRequest(BaseModel):
    template_id: str
    app_name: str
    tenant_id: str
    configuration: Dict[str, Any] = Field(default_factory=dict)
    custom_data: Dict[str, Any] = Field(default_factory=dict)
    environment_variables: Dict[str, str] = Field(default_factory=dict)

class AppCreateResponse(BaseModel):
    app_id: str
    app_name: str
    template_id: str
    tenant_id: str
    status: str  # "creating", "ready", "failed"
    created_at: datetime
    build_logs: List[str] = Field(default_factory=list)
    endpoints: Dict[str, str] = Field(default_factory=dict)

class DeployRequest(BaseModel):
    app_id: str
    environment: str = "production"  # "development", "staging", "production"
    domain: Optional[str] = None
    ssl_enabled: bool = True
    environment_variables: Dict[str, str] = Field(default_factory=dict)

class DeployResponse(BaseModel):
    deployment_id: str
    app_id: str
    environment: str
    status: str  # "deploying", "deployed", "failed"
    url: Optional[str] = None
    ssl_url: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    logs: List[str] = Field(default_factory=list)

class TenantCreateRequest(BaseModel):
    tenant_id: str
    name: str
    description: Optional[str] = None
    settings: Dict[str, Any] = Field(default_factory=dict)
    limits: Dict[str, int] = Field(default_factory=dict)

class TenantResponse(BaseModel):
    tenant_id: str
    name: str
    description: Optional[str]
    created_at: datetime
    settings: Dict[str, Any]
    limits: Dict[str, int]
    usage: Dict[str, int]
    status: str


# ========================= SERVICE =========================

class BuilderAPIService:
    def __init__(self):
        self.app = FastAPI(
            title="TauseStack Builder API",
            description="API v1 para builders externos - Templates, Apps, Deploy",
            version="1.0.0",
            docs_url="/v1/docs",
            redoc_url="/v1/redoc"
        )
        
        self.security = HTTPBearer()
        
        # Storage paths
        self.data_dir = Path(".tausestack_storage/builder")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir = Path("templates")
        self.apps_dir = self.data_dir / "apps"
        self.apps_dir.mkdir(exist_ok=True)
        self.deployments_dir = self.data_dir / "deployments"
        self.deployments_dir.mkdir(exist_ok=True)
        
        # Storage files
        self.apps_file = self.data_dir / "apps.json"
        self.deployments_file = self.data_dir / "deployments.json"
        self.tenants_file = self.data_dir / "tenants.json"
        
        # In-memory state
        self.apps: Dict[str, AppCreateResponse] = {}
        self.deployments: Dict[str, DeployResponse] = {}
        self.tenants: Dict[str, TenantResponse] = {}
        
        # Configurar eventos
        self.app.add_event_handler("startup", self._load_data)
        
        # Configurar rutas
        self._setup_routes()
    
    async def _load_data(self):
        """Cargar datos persistentes al iniciar"""
        try:
            # Cargar apps
            if self.apps_file.exists():
                async with aiofiles.open(self.apps_file, 'r') as f:
                    content = await f.read()
                    apps_data = json.loads(content)
                    for app_data in apps_data:
                        app_data['created_at'] = datetime.fromisoformat(app_data['created_at'])
                        self.apps[app_data['app_id']] = AppCreateResponse(**app_data)
            
            # Cargar deployments
            if self.deployments_file.exists():
                async with aiofiles.open(self.deployments_file, 'r') as f:
                    content = await f.read()
                    deployments_data = json.loads(content)
                    for deploy_data in deployments_data:
                        deploy_data['started_at'] = datetime.fromisoformat(deploy_data['started_at'])
                        if deploy_data.get('completed_at'):
                            deploy_data['completed_at'] = datetime.fromisoformat(deploy_data['completed_at'])
                        self.deployments[deploy_data['deployment_id']] = DeployResponse(**deploy_data)
            
            # Cargar tenants
            if self.tenants_file.exists():
                async with aiofiles.open(self.tenants_file, 'r') as f:
                    content = await f.read()
                    tenants_data = json.loads(content)
                    for tenant_data in tenants_data:
                        tenant_data['created_at'] = datetime.fromisoformat(tenant_data['created_at'])
                        self.tenants[tenant_data['tenant_id']] = TenantResponse(**tenant_data)
            
            # Crear tenant default si no existe
            if 'default' not in self.tenants:
                await self._create_default_tenant()
                        
        except Exception as e:
            print(f"Error loading builder data: {e}")
            await self._create_default_tenant()
    
    async def _create_default_tenant(self):
        """Crear tenant por defecto"""
        default_tenant = TenantResponse(
            tenant_id="default",
            name="Default Tenant",
            description="Tenant por defecto para desarrollo",
            created_at=datetime.now(),
            settings={
                "timezone": "UTC",
                "currency": "USD",
                "language": "en"
            },
            limits={
                "max_apps": 10,
                "max_deployments": 50,
                "storage_gb": 1
            },
            usage={
                "apps_count": 0,
                "deployments_count": 0,
                "storage_used_mb": 0
            },
            status="active"
        )
        self.tenants["default"] = default_tenant
        await self._save_tenants()
    
    async def _save_apps(self):
        """Guardar apps en archivo JSON"""
        try:
            apps_data = []
            for app in self.apps.values():
                app_dict = app.dict()
                app_dict['created_at'] = app_dict['created_at'].isoformat()
                apps_data.append(app_dict)
            
            async with aiofiles.open(self.apps_file, 'w') as f:
                await f.write(json.dumps(apps_data, indent=2))
        except Exception as e:
            print(f"Error saving apps: {e}")
    
    async def _save_deployments(self):
        """Guardar deployments en archivo JSON"""
        try:
            deployments_data = []
            for deployment in self.deployments.values():
                deploy_dict = deployment.dict()
                deploy_dict['started_at'] = deploy_dict['started_at'].isoformat()
                if deploy_dict.get('completed_at'):
                    deploy_dict['completed_at'] = deploy_dict['completed_at'].isoformat()
                deployments_data.append(deploy_dict)
            
            async with aiofiles.open(self.deployments_file, 'w') as f:
                await f.write(json.dumps(deployments_data, indent=2))
        except Exception as e:
            print(f"Error saving deployments: {e}")
    
    async def _save_tenants(self):
        """Guardar tenants en archivo JSON"""
        try:
            tenants_data = []
            for tenant in self.tenants.values():
                tenant_dict = tenant.dict()
                tenant_dict['created_at'] = tenant_dict['created_at'].isoformat()
                tenants_data.append(tenant_dict)
            
            async with aiofiles.open(self.tenants_file, 'w') as f:
                await f.write(json.dumps(tenants_data, indent=2))
        except Exception as e:
            print(f"Error saving tenants: {e}")
    
    def _setup_routes(self):
        """Configurar todas las rutas del API v1"""
        
        @self.app.get("/health")
        async def health_check():
            """Health check del Builder API"""
            return {
                "service": "builder_api",
                "version": "1.0.0",
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "endpoints": {
                    "templates": "/v1/templates",
                    "apps": "/v1/apps", 
                    "deploy": "/v1/deploy",
                    "tenants": "/v1/tenants"
                }
            }
        
        # ============= TEMPLATE ENDPOINTS =============
        
        @self.app.get("/v1/templates/list", response_model=List[TemplateListResponse])
        async def list_templates():
            """Listar todos los templates disponibles"""
            templates = []
            
            try:
                # Leer metadata cache
                metadata_file = self.templates_dir / "registry" / "metadata_cache.json"
                if metadata_file.exists():
                    async with aiofiles.open(metadata_file, 'r') as f:
                        content = await f.read()
                        metadata_cache = json.loads(content)
                        
                        for template_id, metadata in metadata_cache.items():
                            templates.append(TemplateListResponse(
                                id=template_id,
                                name=metadata['name'],
                                description=metadata['description'],
                                version=metadata['version'],
                                author=metadata['author'],
                                tags=metadata['tags'],
                                category=metadata['category'],
                                preview_image=metadata.get('preview_image'),
                                demo_url=metadata.get('demo_url'),
                                created_at=datetime.fromisoformat(metadata['created_at']),
                                updated_at=datetime.fromisoformat(metadata['updated_at'])
                            ))
                
                return templates
                
            except Exception as e:
                print(f"Error listing templates: {e}")
                return []
        
        @self.app.get("/v1/templates/{template_id}", response_model=TemplateDetailResponse)
        async def get_template_detail(template_id: str):
            """Obtener detalles completos de un template"""
            try:
                template_file = self.templates_dir / "registry" / f"{template_id}.json"
                if not template_file.exists():
                    raise HTTPException(status_code=404, detail="Template not found")
                
                async with aiofiles.open(template_file, 'r') as f:
                    content = await f.read()
                    template_data = json.loads(content)
                    
                    return TemplateDetailResponse(**template_data)
                    
            except HTTPException:
                raise
            except Exception as e:
                print(f"Error getting template {template_id}: {e}")
                raise HTTPException(status_code=500, detail="Error loading template")
        
        # ============= APP ENDPOINTS =============
        
        @self.app.post("/v1/apps/create", response_model=AppCreateResponse)
        async def create_app(request: AppCreateRequest, background_tasks: BackgroundTasks):
            """Crear nueva app desde template"""
            
            # Validar que el template existe
            template_file = self.templates_dir / "registry" / f"{request.template_id}.json"
            if not template_file.exists():
                raise HTTPException(status_code=404, detail="Template not found")
            
            # Validar que el tenant existe
            if request.tenant_id not in self.tenants:
                raise HTTPException(status_code=404, detail="Tenant not found")
            
            # Generar app_id único
            app_id = f"app_{uuid.uuid4().hex[:8]}"
            
            # Crear respuesta inicial
            app_response = AppCreateResponse(
                app_id=app_id,
                app_name=request.app_name,
                template_id=request.template_id,
                tenant_id=request.tenant_id,
                status="creating",
                created_at=datetime.now(),
                build_logs=[],
                endpoints={}
            )
            
            # Guardar en memoria y persistir
            self.apps[app_id] = app_response
            await self._save_apps()
            
            # Ejecutar creación en background
            background_tasks.add_task(self._create_app_background, app_id, request)
            
            return app_response
        
        @self.app.get("/v1/apps/{app_id}", response_model=AppCreateResponse)
        async def get_app_status(app_id: str):
            """Obtener estado de una app"""
            if app_id not in self.apps:
                raise HTTPException(status_code=404, detail="App not found")
            
            return self.apps[app_id]
        
        @self.app.get("/v1/apps", response_model=List[AppCreateResponse])
        async def list_apps(tenant_id: Optional[str] = None):
            """Listar todas las apps, opcionalmente filtradas por tenant"""
            apps = list(self.apps.values())
            
            if tenant_id:
                apps = [app for app in apps if app.tenant_id == tenant_id]
            
            return apps
        
        # ============= DEPLOY ENDPOINTS =============
        
        @self.app.post("/v1/deploy/start", response_model=DeployResponse)
        async def start_deployment(request: DeployRequest, background_tasks: BackgroundTasks):
            """Iniciar deployment de una app"""
            
            # Validar que la app existe y está lista
            if request.app_id not in self.apps:
                raise HTTPException(status_code=404, detail="App not found")
            
            app = self.apps[request.app_id]
            if app.status != "ready":
                raise HTTPException(status_code=400, detail=f"App status is {app.status}, must be 'ready' to deploy")
            
            # Generar deployment_id único
            deployment_id = f"deploy_{uuid.uuid4().hex[:8]}"
            
            # Crear respuesta inicial
            deploy_response = DeployResponse(
                deployment_id=deployment_id,
                app_id=request.app_id,
                environment=request.environment,
                status="deploying",
                url=None,
                ssl_url=None,
                started_at=datetime.now(),
                completed_at=None,
                logs=[]
            )
            
            # Guardar en memoria y persistir
            self.deployments[deployment_id] = deploy_response
            await self._save_deployments()
            
            # Ejecutar deployment en background
            background_tasks.add_task(self._deploy_app_background, deployment_id, request)
            
            return deploy_response
        
        @self.app.get("/v1/deploy/{deployment_id}", response_model=DeployResponse)
        async def get_deployment_status(deployment_id: str):
            """Obtener estado de un deployment"""
            if deployment_id not in self.deployments:
                raise HTTPException(status_code=404, detail="Deployment not found")
            
            return self.deployments[deployment_id]
        
        # ============= TENANT ENDPOINTS =============
        
        @self.app.post("/v1/tenants/create", response_model=TenantResponse)
        async def create_tenant(request: TenantCreateRequest):
            """Crear nuevo tenant"""
            
            # Validar que no existe
            if request.tenant_id in self.tenants:
                raise HTTPException(status_code=400, detail="Tenant already exists")
            
            # Crear tenant
            tenant = TenantResponse(
                tenant_id=request.tenant_id,
                name=request.name,
                description=request.description,
                created_at=datetime.now(),
                settings=request.settings or {
                    "timezone": "UTC",
                    "currency": "USD", 
                    "language": "en"
                },
                limits=request.limits or {
                    "max_apps": 5,
                    "max_deployments": 20,
                    "storage_gb": 1
                },
                usage={
                    "apps_count": 0,
                    "deployments_count": 0,
                    "storage_used_mb": 0
                },
                status="active"
            )
            
            # Guardar
            self.tenants[request.tenant_id] = tenant
            await self._save_tenants()
            
            return tenant
        
        @self.app.get("/v1/tenants/{tenant_id}", response_model=TenantResponse)
        async def get_tenant(tenant_id: str):
            """Obtener información de un tenant"""
            if tenant_id not in self.tenants:
                raise HTTPException(status_code=404, detail="Tenant not found")
            
            return self.tenants[tenant_id]
        
        @self.app.get("/v1/tenants", response_model=List[TenantResponse])
        async def list_tenants():
            """Listar todos los tenants"""
            return list(self.tenants.values())
        
        @self.app.put("/v1/tenants/{tenant_id}/configure")
        async def configure_tenant(tenant_id: str, settings: Dict[str, Any]):
            """Configurar settings de un tenant"""
            if tenant_id not in self.tenants:
                raise HTTPException(status_code=404, detail="Tenant not found")
            
            tenant = self.tenants[tenant_id]
            tenant.settings.update(settings)
            await self._save_tenants()
            
            return {"message": "Tenant configured successfully", "settings": tenant.settings}
    
    async def _create_app_background(self, app_id: str, request: AppCreateRequest):
        """Crear app en background"""
        try:
            app = self.apps[app_id]
            app.build_logs.append(f"Starting app creation for {request.app_name}")
            
            # Leer template
            template_file = self.templates_dir / "registry" / f"{request.template_id}.json"
            async with aiofiles.open(template_file, 'r') as f:
                content = await f.read()
                template_data = json.loads(content)
            
            app.build_logs.append(f"Template {request.template_id} loaded successfully")
            
            # Crear directorio de la app
            app_dir = self.apps_dir / app_id
            app_dir.mkdir(exist_ok=True)
            
            # Aplicar configuración personalizada
            if request.configuration:
                template_data.update(request.configuration)
            
            # Guardar app data
            app_data_file = app_dir / "app_data.json"
            async with aiofiles.open(app_data_file, 'w') as f:
                await f.write(json.dumps({
                    "app_id": app_id,
                    "template_data": template_data,
                    "custom_data": request.custom_data,
                    "environment_variables": request.environment_variables
                }, indent=2))
            
            app.build_logs.append("App data saved successfully")
            
            # Simular endpoints generados
            app.endpoints = {
                "frontend": f"http://{app_id}.localhost:3000",
                "api": f"http://{app_id}.localhost:8000", 
                "admin": f"http://{app_id}.localhost:3000/admin"
            }
            
            # Marcar como listo
            app.status = "ready"
            app.build_logs.append("App created successfully and ready for deployment")
            
            # Actualizar usage del tenant
            tenant = self.tenants[request.tenant_id]
            tenant.usage["apps_count"] += 1
            
            await self._save_apps()
            await self._save_tenants()
            
        except Exception as e:
            app = self.apps[app_id]
            app.status = "failed"
            app.build_logs.append(f"Error creating app: {str(e)}")
            await self._save_apps()
    
    async def _deploy_app_background(self, deployment_id: str, request: DeployRequest):
        """Hacer deployment en background"""
        try:
            deployment = self.deployments[deployment_id]
            deployment.logs.append(f"Starting deployment to {request.environment}")
            
            # Simular proceso de deployment
            await asyncio.sleep(2)  # Simular tiempo de build
            
            deployment.logs.append("Building application...")
            await asyncio.sleep(3)  # Simular tiempo de deployment
            
            deployment.logs.append("Deploying to infrastructure...")
            await asyncio.sleep(2)  # Simular configuración de SSL
            
            # Generar URLs de deployment
            if request.domain:
                deployment.url = f"http://{request.domain}"
                deployment.ssl_url = f"https://{request.domain}" if request.ssl_enabled else None
            else:
                deployment.url = f"http://{request.app_id}-{request.environment}.tausestack.app"
                deployment.ssl_url = f"https://{request.app_id}-{request.environment}.tausestack.app" if request.ssl_enabled else None
            
            deployment.status = "deployed"
            deployment.completed_at = datetime.now()
            deployment.logs.append(f"Deployment completed successfully. URL: {deployment.ssl_url or deployment.url}")
            
            # Actualizar usage del tenant
            app = self.apps[request.app_id]
            tenant = self.tenants[app.tenant_id]
            tenant.usage["deployments_count"] += 1
            
            await self._save_deployments()
            await self._save_tenants()
            
        except Exception as e:
            deployment = self.deployments[deployment_id]
            deployment.status = "failed"
            deployment.completed_at = datetime.now()
            deployment.logs.append(f"Deployment failed: {str(e)}")
            await self._save_deployments()


# ========================= MAIN =========================

def create_builder_api_app():
    """Factory function para crear la app"""
    service = BuilderAPIService()
    return service.app

# Instancia global para import directo
app = create_builder_api_app()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8006) 