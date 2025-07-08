"""
Admin API Service - Gestión centralizada de configuraciones administrativas
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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
            """Probar conexión con una API"""
            if api_id not in self.api_configs:
                raise HTTPException(status_code=404, detail="API no encontrada")
            
            result = await self._test_connection(api_id)
            await self._save_health_history()
            return result
        
        @self.app.get("/admin/apis/{api_id}/health", response_model=List[HealthCheckResult])
        async def get_health_history(api_id: str, limit: int = 10):
            """Obtener historial de health checks"""
            history = [h for h in self.health_history if h.api_id == api_id]
            return history[-limit:]
        
        @self.app.post("/admin/health-check-all")
        async def run_health_check_all():
            """Ejecutar health check para todas las APIs"""
            results = []
            for api_id in self.api_configs.keys():
                try:
                    result = await self._test_connection(api_id)
                    results.append(result)
                except Exception as e:
                    results.append(HealthCheckResult(
                        api_id=api_id,
                        status=APIStatus.error,
                        error_message=str(e),
                        timestamp=datetime.now()
                    ))
            
            await self._save_health_history()
            return results
        
        @self.app.get("/admin/dashboard/stats")
        async def get_dashboard_stats():
            """Obtener estadísticas del dashboard administrativo"""
            active_apis = sum(1 for api in self.api_configs.values() if api.status == APIStatus.active)
            total_apis = len(self.api_configs)
            
            recent_checks = [h for h in self.health_history if h.timestamp.date() == datetime.now().date()]
            success_rate = (
                sum(1 for h in recent_checks if h.status == APIStatus.active) / len(recent_checks) * 100
                if recent_checks else 0
            )
            
            return {
                "total_apis": total_apis,
                "active_apis": active_apis,
                "inactive_apis": total_apis - active_apis,
                "success_rate": round(success_rate, 1),
                "last_check": max([api.last_check for api in self.api_configs.values()]) if self.api_configs else datetime.now(),
                "health_checks_today": len(recent_checks)
            }

        @self.app.get("/admin/dashboard/metrics")
        async def get_dashboard_metrics():
            """Obtener métricas del dashboard en tiempo real"""
            try:
                # Simular datos reales (en producción vendría de bases de datos y logs)
                import random
                import time
                
                # Datos base con variación para simular tiempo real
                base_calls = 2847392
                variation = random.randint(-50000, 50000)
                
                metrics = {
                    "apiCallsToday": base_calls + variation,
                    "apiCallsGrowth": random.randint(8, 15),
                    "activeTenants": random.randint(125, 130),
                    "newTenantsWeek": random.randint(6, 10),
                    "revenueMTD": random.randint(12000, 15000),
                    "revenueGrowth": random.randint(18, 28),
                    "uptime": round(random.uniform(99.5, 99.9), 1),
                    "incidents": random.randint(1, 5),
                    "requestsPerSecond": random.randint(750, 950),
                    "avgResponseTime": random.randint(70, 120),
                    "errorRate": round(random.uniform(0.1, 0.8), 1),
                    "timestamp": int(time.time())
                }
                
                return metrics
                
            except Exception as e:
                print(f"Error getting dashboard metrics: {e}")
                return {"error": str(e)}, 500

        @self.app.get("/admin/dashboard/top-endpoints")
        async def get_top_endpoints():
            """Obtener los endpoints más utilizados"""
            try:
                endpoints = [
                    {"path": "/api/v1/ai/generate", "calls": 234829, "icon": "🔥"},
                    {"path": "/api/v1/auth/login", "calls": 189472, "icon": "🔐"},
                    {"path": "/api/v1/storage/upload", "calls": 156394, "icon": "💾"},
                    {"path": "/api/v1/analytics/track", "calls": 98847, "icon": "📊"},
                    {"path": "/api/v1/colombia/nit", "calls": 45283, "icon": "🇨🇴"},
                    {"path": "/api/v1/notifications/send", "calls": 34829, "icon": "📧"},
                    {"path": "/api/v1/payments/process", "calls": 28947, "icon": "💳"},
                    {"path": "/api/v1/templates/render", "calls": 23847, "icon": "📄"}
                ]
                
                # Agregar variación para simular tiempo real
                import random
                for endpoint in endpoints:
                    endpoint["calls"] += random.randint(-1000, 1000)
                    
                return endpoints
                
            except Exception as e:
                print(f"Error getting top endpoints: {e}")
                return {"error": str(e)}, 500

        @self.app.get("/admin/dashboard/top-tenants")
        async def get_top_tenants():
            """Obtener los tenants con más consumo"""
            try:
                tenants = [
                    {"name": "Acme Corp", "plan": "Enterprise", "calls": 847392, "revenue": 2847, "badge": "🏆"},
                    {"name": "DevCorp", "plan": "Pro", "calls": 234829, "revenue": 847, "badge": "🥈"},
                    {"name": "StartupABC", "plan": "Starter", "calls": 89472, "revenue": 29, "badge": "🥉"},
                    {"name": "TechFlow", "plan": "Pro", "calls": 67829, "revenue": 245, "badge": "🔥"},
                    {"name": "CloudBiz", "plan": "Enterprise", "calls": 45283, "revenue": 1567, "badge": "💼"},
                    {"name": "AppMakers", "plan": "Starter", "calls": 23847, "revenue": 49, "badge": "🚀"}
                ]
                
                return tenants
                
            except Exception as e:
                print(f"Error getting top tenants: {e}")
                return {"error": str(e)}, 500

        @self.app.get("/admin/dashboard/recent-activity")
        async def get_recent_activity():
            """Obtener actividad reciente del sistema"""
            try:
                import random
                from datetime import datetime, timedelta
                
                activity_templates = [
                    {"type": "new_tenant", "message": "New tenant: {name} registered", "icon": "🆕"},
                    {"type": "alert", "message": "High usage alert: {name} exceeded 95%", "icon": "⚠️"},
                    {"type": "plugin", "message": "Plugin approved: {name}", "icon": "✅"},
                    {"type": "maintenance", "message": "System maintenance completed", "icon": "🔧"},
                    {"type": "support", "message": "Support ticket resolved: Tenant #{number}", "icon": "💬"},
                    {"type": "payment", "message": "Payment processed for {name}", "icon": "💳"},
                    {"type": "upgrade", "message": "{name} upgraded to {plan} plan", "icon": "⬆️"},
                    {"type": "integration", "message": "New integration: {name} API connected", "icon": "🔗"},
                    {"type": "backup", "message": "Database backup completed successfully", "icon": "💾"},
                    {"type": "security", "message": "Security scan completed - No issues found", "icon": "🛡️"}
                ]
                
                companies = ["StartupXYZ", "TechCorp", "DevFlow", "CloudTech", "AppBuild", "DataFlow"]
                plugins = ["HubSpot Connector", "Slack Integration", "Zoom API", "WhatsApp Business"]
                plans = ["Pro", "Enterprise", "Premium"]
                integrations = ["Salesforce", "Google Workspace", "Microsoft Teams", "Shopify"]
                
                activities = []
                for i in range(10):
                    template = random.choice(activity_templates)
                    activity = template.copy()
                    
                    # Personalizar mensaje según tipo
                    if "{name}" in activity["message"]:
                        if template["type"] == "new_tenant" or template["type"] == "alert":
                            activity["message"] = activity["message"].format(name=random.choice(companies))
                        elif template["type"] == "plugin":
                            activity["message"] = activity["message"].format(name=random.choice(plugins))
                        elif template["type"] == "payment":
                            activity["message"] = activity["message"].format(name=random.choice(companies))
                        elif template["type"] == "upgrade":
                            activity["message"] = activity["message"].format(
                                name=random.choice(companies), 
                                plan=random.choice(plans)
                            )
                        elif template["type"] == "integration":
                            activity["message"] = activity["message"].format(name=random.choice(integrations))
                            
                    if "{number}" in activity["message"]:
                        activity["message"] = activity["message"].format(number=random.randint(100, 999))
                        
                    # Generar timestamp relativo
                    minutes_ago = random.randint(1, 120)
                    if minutes_ago < 60:
                        activity["time"] = f"{minutes_ago}m ago"
                    else:
                        activity["time"] = f"{minutes_ago // 60}h ago"
                        
                    activities.append(activity)
                
                return activities
                
            except Exception as e:
                print(f"Error getting recent activity: {e}")
                return {"error": str(e)}, 500
    
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