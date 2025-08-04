"""
Admin API Service - Gestión centralizada de configuraciones administrativas
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import httpx
import json
import os
from enum import Enum
import aiofiles
from pathlib import Path
from fastapi import Request

# Modelos de datos
class APIType(str, Enum):
    ai = "ai"
    payment = "payment"
    external = "external"

class APIStatus(str, Enum):
    active = "active"
    inactive = "inactive"  
    error = "error"

class APIConfig(BaseModel):
    id: str
    name: str
    type: APIType
    status: APIStatus
    endpoint: Optional[str] = None
    api_key: Optional[str] = None
    description: str
    last_check: datetime
    config_data: Dict[str, Any] = Field(default_factory=dict)

class APIConfigUpdate(BaseModel):
    endpoint: Optional[str] = None
    api_key: Optional[str] = None
    config_data: Dict[str, Any] = Field(default_factory=dict)

class APIConfigCreate(BaseModel):
    name: str
    type: APIType
    endpoint: Optional[str] = None
    api_key: Optional[str] = None
    description: str
    config_data: Dict[str, Any] = Field(default_factory=dict)

class HealthCheckResult(BaseModel):
    api_id: str
    status: APIStatus
    latency_ms: Optional[int] = None
    error_message: Optional[str] = None
    timestamp: datetime

class AdminAPIService:
    def __init__(self):
        self.app = FastAPI(title="TauseStack Admin API", version="1.0.0")
        self.security = HTTPBearer()
        self.api_configs: Dict[str, APIConfig] = {}
        self.health_history: List[HealthCheckResult] = []
        
        # Configurar CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Configurar directorios de persistence
        self.data_dir = Path(".tausestack_storage/admin")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.apis_file = self.data_dir / "api_configs.json"
        self.health_file = self.data_dir / "health_history.json"
        
        # Configurar eventos de FastAPI
        self.app.add_event_handler("startup", self._load_configurations)
        
        # Configurar rutas
        self._setup_routes()
    
    async def _load_configurations(self):
        """Cargar configuraciones desde archivo JSON"""
        try:
            # Cargar APIs
            if self.apis_file.exists():
                async with aiofiles.open(self.apis_file, 'r') as f:
                    content = await f.read()
                    apis_data = json.loads(content)
                    for api_data in apis_data:
                        api_data['last_check'] = datetime.fromisoformat(api_data['last_check'])
                        api_config = APIConfig(**api_data)
                        self.api_configs[api_config.id] = api_config
            else:
                # Cargar configuraciones por defecto
                await self._load_default_configs()
            
            # Cargar historial de health checks
            if self.health_file.exists():
                async with aiofiles.open(self.health_file, 'r') as f:
                    content = await f.read()
                    health_data = json.loads(content)
                    for health_item in health_data:
                        health_item['timestamp'] = datetime.fromisoformat(health_item['timestamp'])
                        self.health_history.append(HealthCheckResult(**health_item))
                        
        except Exception as e:
            print(f"Error loading configurations: {e}")
            await self._load_default_configs()
    
    async def _load_default_configs(self):
        """Cargar configuraciones predeterminadas"""
        default_configs = [
            {
                "id": "openai",
                "name": "OpenAI",
                "type": "ai",
                "status": "inactive",
                "description": "Integración con GPT-4 y otros modelos OpenAI",
                "endpoint": "https://api.openai.com/v1",
                "last_check": datetime.now(),
                "config_data": {
                    "model": "gpt-4",
                    "temperature": 0.7,
                    "max_tokens": 4000
                }
            },
            {
                "id": "claude",
                "name": "Anthropic Claude",
                "type": "ai",
                "status": "inactive",
                "description": "Integración con Claude para análisis avanzados",
                "endpoint": "https://api.anthropic.com/v1",
                "last_check": datetime.now(),
                "config_data": {
                    "model": "claude-3-sonnet-20240229",
                    "max_tokens": 4000
                }
            }
        ]
        
        for config in default_configs:
            api_config = APIConfig(**config)
            self.api_configs[config["id"]] = api_config
        
        # Guardar configuraciones por defecto
        await self._save_apis()
    
    async def _save_apis(self):
        """Guardar configuraciones de APIs en archivo JSON"""
        try:
            apis_data = []
            for api_config in self.api_configs.values():
                api_dict = api_config.dict()
                api_dict['last_check'] = api_dict['last_check'].isoformat()
                apis_data.append(api_dict)
            
            async with aiofiles.open(self.apis_file, 'w') as f:
                await f.write(json.dumps(apis_data, indent=2))
        except Exception as e:
            print(f"Error saving APIs: {e}")
    
    async def _save_health_history(self):
        """Guardar historial de health checks"""
        try:
            # Mantener solo los últimos 100 registros
            recent_history = self.health_history[-100:]
            
            health_data = []
            for health_result in recent_history:
                health_dict = health_result.dict()
                health_dict['timestamp'] = health_dict['timestamp'].isoformat()
                health_data.append(health_dict)
            
            async with aiofiles.open(self.health_file, 'w') as f:
                await f.write(json.dumps(health_data, indent=2))
        except Exception as e:
            print(f"Error saving health history: {e}")
    
    def _setup_routes(self):
        """Configurar todas las rutas del API"""
        
        # Middleware de autenticación - DESHABILITADO PARA DEMOS
        # @self.app.middleware("http")
        # async def auth_middleware(request: Request, call_next):
        #     # Verificar token para rutas protegidas
        #     if request.url.path.startswith("/admin/"):
        #         auth_header = request.headers.get("authorization")
        #         if not auth_header or not auth_header.startswith("Bearer "):
        #             return JSONResponse(
        #                 status_code=401,
        #                 content={"detail": "No se proporcionó token de autenticación."}
        #             )
        #         
        #         token = auth_header.split(" ")[1]
        #         
        #         try:
        #             payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        #             request.state.user = payload
        #         except jwt.PyJWTError:
        #             return JSONResponse(
        #                 status_code=401,
        #                 content={"detail": "Token inválido."}
        #             )
        #     
        #     return await call_next(request)
        
        # PARA DEMOS: Agregar automáticamente tenant_id de tause.pro
        @self.app.middleware("http")
        async def demo_middleware(request: Request, call_next):
            # Agregar tenant_id automáticamente para demos
            if hasattr(request.state, 'user') is False:
                request.state.user = {"tenant_id": "tause.pro"}
            
            return await call_next(request)
        
        @self.app.get("/admin/apis", response_model=List[APIConfig])
        async def get_all_apis():
            """Obtener todas las configuraciones de APIs"""
            return list(self.api_configs.values())
        
        @self.app.get("/admin/apis/{api_id}", response_model=APIConfig)
        async def get_api_config(api_id: str):
            """Obtener configuración específica de una API"""
            if api_id not in self.api_configs:
                raise HTTPException(status_code=404, detail="API no encontrada")
            return self.api_configs[api_id]
        
        @self.app.post("/admin/apis", response_model=APIConfig)
        async def create_api_config(config_create: APIConfigCreate):
            """Crear nueva configuración de API"""
            # Generar ID único
            api_id = config_create.name.lower().replace(' ', '-').replace('.', '-')
            
            # Verificar que no exista
            if api_id in self.api_configs:
                raise HTTPException(status_code=400, detail="API con ese nombre ya existe")
            
            # Crear configuración
            api_config = APIConfig(
                id=api_id,
                name=config_create.name,
                type=config_create.type,
                status=APIStatus.inactive,
                endpoint=config_create.endpoint,
                api_key=config_create.api_key,
                description=config_create.description,
                last_check=datetime.now(),
                config_data=config_create.config_data
            )
            
            # Guardar
            self.api_configs[api_id] = api_config
            await self._save_apis()
            
            return api_config
        
        @self.app.put("/admin/apis/{api_id}", response_model=APIConfig)
        async def update_api_config(api_id: str, config_update: APIConfigUpdate):
            """Actualizar configuración de una API"""
            if api_id not in self.api_configs:
                raise HTTPException(status_code=404, detail="API no encontrada")
            
            api_config = self.api_configs[api_id]
            
            # Actualizar campos
            if config_update.endpoint is not None:
                api_config.endpoint = config_update.endpoint
            if config_update.api_key is not None:
                api_config.api_key = config_update.api_key
            if config_update.config_data:
                api_config.config_data.update(config_update.config_data)
            
            # Guardar configuración
            await self._save_apis()
            
            return api_config
        
        @self.app.delete("/admin/apis/{api_id}")
        async def delete_api_config(api_id: str):
            """Eliminar configuración de API"""
            if api_id not in self.api_configs:
                raise HTTPException(status_code=404, detail="API no encontrada")
            
            # No permitir eliminar APIs por defecto
            if api_id in ["openai", "claude"]:
                raise HTTPException(status_code=400, detail="No se puede eliminar API por defecto")
            
            del self.api_configs[api_id]
            await self._save_apis()
            
            return {"message": f"API {api_id} eliminada exitosamente"}
        
        @self.app.post("/admin/apis/{api_id}/test", response_model=HealthCheckResult)
        async def test_api_connection(api_id: str):
            """Probar conexión a una API específica"""
            if api_id not in self.api_configs:
                raise HTTPException(status_code=404, detail="API no encontrada")
            
            result = await self._test_connection(api_id)
            return result
        
        @self.app.get("/admin/apis/{api_id}/health", response_model=List[HealthCheckResult])
        async def get_health_history(api_id: str, limit: int = 10):
            """Obtener historial de health checks para una API"""
            history = [h for h in self.health_history if h.api_id == api_id]
            return history[-limit:]
        
        @self.app.post("/admin/health-check-all")
        async def run_health_check_all():
            """Ejecutar health check para todas las APIs"""
            results = []
            for api_id in self.api_configs:
                result = await self._test_connection(api_id)
                results.append(result)
            
            # Actualizar estados
            for result in results:
                if result.api_id in self.api_configs:
                    self.api_configs[result.api_id].status = result.status
                    self.api_configs[result.api_id].last_check = result.timestamp
            
            await self._save_apis()
            await self._save_health_history()
            
            return {"message": "Health check completado", "results": results}
        
        @self.app.get("/admin/dashboard/stats")
        async def get_dashboard_stats():
            """Obtener estadísticas del dashboard"""
            return {
                "total_tenants": 1,
                "active_tenants": 1,
                "total_requests": 1247,
                "success_rate": 99.2,
                "avg_response_time": 125,
                "monthly_revenue": 2850.00,
                "total_endpoints": 18,
                "healthy_services": 5,
                "total_services": 8,
                "api_calls_today": 247,
                "error_rate": 0.8,
                "uptime": 99.9,
                "storage_usage_gb": 2.3,
                "active_users": 12
            }
        
        @self.app.get("/admin/dashboard/metrics")
        async def get_dashboard_metrics():
            """Obtener métricas detalladas del dashboard"""
            
            # Métricas de servicios
            service_metrics = [
                {
                    "name": "API Gateway",
                    "status": "healthy",
                    "response_time": 95,
                    "requests_per_minute": 45,
                    "error_rate": 0.2
                },
                {
                    "name": "Admin API",
                    "status": "healthy",
                    "response_time": 120,
                    "requests_per_minute": 12,
                    "error_rate": 0.1
                },
                {
                    "name": "AI Services",
                    "status": "healthy",
                    "response_time": 230,
                    "requests_per_minute": 8,
                    "error_rate": 0.3
                },
                {
                    "name": "Analytics",
                    "status": "healthy",
                    "response_time": 180,
                    "requests_per_minute": 15,
                    "error_rate": 0.0
                },
                {
                    "name": "Communications",
                    "status": "healthy",
                    "response_time": 150,
                    "requests_per_minute": 6,
                    "error_rate": 0.1
                }
            ]
            
            # Métricas de tenants
            tenant_metrics = [
                {
                    "tenant_id": "tause.pro",
                    "requests_today": 247,
                    "active_endpoints": 12,
                    "storage_usage_gb": 2.3,
                    "monthly_usage": 8450
                }
            ]
            
            return {
                "service_metrics": service_metrics,
                "tenant_metrics": tenant_metrics,
                "system_health": {
                    "cpu_usage": 45.2,
                    "memory_usage": 67.8,
                    "disk_usage": 34.1,
                    "network_io": 1.2
                }
            }
        
        @self.app.get("/admin/dashboard/top-endpoints")
        async def get_top_endpoints():
            """Obtener endpoints más utilizados"""
            endpoints = [
                {
                    "endpoint": "/api/ai/generate",
                    "requests": 1247,
                    "avg_response_time": 340,
                    "error_rate": 0.3
                },
                {
                    "endpoint": "/api/analytics/events",
                    "requests": 890,
                    "avg_response_time": 120,
                    "error_rate": 0.1
                },
                {
                    "endpoint": "/api/billing/usage",
                    "requests": 567,
                    "avg_response_time": 90,
                    "error_rate": 0.0
                },
                {
                    "endpoint": "/api/communications/send",
                    "requests": 234,
                    "avg_response_time": 180,
                    "error_rate": 0.2
                },
                {
                    "endpoint": "/api/templates/render",
                    "requests": 123,
                    "avg_response_time": 250,
                    "error_rate": 0.1
                }
            ]
            
            return {"top_endpoints": endpoints}
        
        @self.app.get("/admin/dashboard/top-tenants")
        async def get_top_tenants():
            """Obtener tenants más activos"""
            tenants = [
                {
                    "tenant_id": "tause.pro",
                    "total_requests": 3847,
                    "active_endpoints": 12,
                    "monthly_revenue": 2850.00,
                    "storage_usage_gb": 2.3,
                    "last_activity": "2024-01-07T15:30:00"
                }
            ]
            
            return {"top_tenants": tenants}
        
        @self.app.get("/admin/dashboard/recent-activity")
        async def get_recent_activity():
            """Obtener actividad reciente del sistema"""
            activities = [
                {
                    "timestamp": "2024-01-07T15:45:00",
                    "type": "api_request",
                    "tenant_id": "tause.pro",
                    "endpoint": "/api/ai/generate",
                    "status": "success",
                    "response_time": 340
                },
                {
                    "timestamp": "2024-01-07T15:42:00",
                    "type": "api_request",
                    "tenant_id": "tause.pro",
                    "endpoint": "/api/analytics/events",
                    "status": "success",
                    "response_time": 120
                },
                {
                    "timestamp": "2024-01-07T15:40:00",
                    "type": "health_check",
                    "service": "ai_services",
                    "status": "healthy",
                    "response_time": 95
                },
                {
                    "timestamp": "2024-01-07T15:38:00",
                    "type": "api_request",
                    "tenant_id": "tause.pro",
                    "endpoint": "/api/billing/usage",
                    "status": "success",
                    "response_time": 90
                },
                {
                    "timestamp": "2024-01-07T15:35:00",
                    "type": "error",
                    "tenant_id": "tause.pro",
                    "endpoint": "/api/communications/send",
                    "status": "error",
                    "error_message": "Rate limit exceeded"
                }
            ]
            
            return {"recent_activity": activities}
        
        @self.app.get("/health")
        async def health_check():
            """Health check básico del Admin API"""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
                "service": "admin_api"
            }
    
    async def _test_connection(self, api_id: str) -> HealthCheckResult:
        """Probar conexión con una API específica"""
        api_config = self.api_configs[api_id]
        start_time = datetime.now()
        
        try:
            if api_config.type == APIType.ai:
                success = await self._test_ai_connection(api_config)
            else:
                success = await self._test_generic_connection(api_config)
            
            # Calcular latencia
            latency = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Actualizar estado
            new_status = APIStatus.active if success else APIStatus.error
            api_config.status = new_status
            api_config.last_check = datetime.now()
            
            health_result = HealthCheckResult(
                api_id=api_id,
                status=new_status,
                latency_ms=latency,
                timestamp=datetime.now()
            )
            
            self.health_history.append(health_result)
            await self._save_apis()
            return health_result
            
        except Exception as e:
            api_config.status = APIStatus.error
            api_config.last_check = datetime.now()
            
            health_result = HealthCheckResult(
                api_id=api_id,
                status=APIStatus.error,
                error_message=str(e),
                timestamp=datetime.now()
            )
            
            self.health_history.append(health_result)
            await self._save_apis()
            return health_result
    
    async def _test_ai_connection(self, api_config: APIConfig) -> bool:
        """Probar conexión con APIs de IA"""
        if not api_config.api_key or not api_config.endpoint:
            return False
        
        try:
            timeout = httpx.Timeout(10.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                if api_config.id == "openai":
                    headers = {"Authorization": f"Bearer {api_config.api_key}"}
                    test_url = f"{api_config.endpoint}/models"
                    response = await client.get(test_url, headers=headers)
                    return response.status_code == 200
                
                elif api_config.id == "claude":
                    headers = {
                        "x-api-key": api_config.api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    }
                    test_url = f"{api_config.endpoint}/messages"
                    test_payload = {
                        "model": api_config.config_data.get("model", "claude-3-sonnet-20240229"),
                        "max_tokens": 10,
                        "messages": [{"role": "user", "content": "test"}]
                    }
                    response = await client.post(test_url, headers=headers, json=test_payload)
                    return response.status_code < 400
                
                else:
                    # Test genérico para otras APIs de IA
                    headers = {"Authorization": f"Bearer {api_config.api_key}"}
                    response = await client.get(api_config.endpoint, headers=headers)
                    return response.status_code < 400
                    
        except Exception as e:
            print(f"AI connection test failed for {api_config.id}: {e}")
            return False
    
    async def _test_generic_connection(self, api_config: APIConfig) -> bool:
        """Probar conexión genérica"""
        if not api_config.endpoint:
            return False
        
        try:
            timeout = httpx.Timeout(5.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(api_config.endpoint)
                return response.status_code < 400
        except Exception as e:
            print(f"Generic connection test failed for {api_config.id}: {e}")
            return False

# Instancia global del servicio
admin_service = AdminAPIService()

# Exportar la app para uso en el servidor principal
app = admin_service.app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 