"""
TauseStack Builder SDK - External Integration

Permite a builders externos (como TausePro) crear y gestionar aplicaciones
usando TauseStack como backend framework.
"""

import httpx
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class AppStatus(Enum):
    CREATING = "creating"
    DEPLOYING = "deploying"
    ACTIVE = "active"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class AppConfig:
    template_id: str
    name: str
    tenant_id: str
    environment: Dict[str, Any]
    custom_config: Optional[Dict[str, Any]] = None


@dataclass
class App:
    id: str
    name: str
    template_id: str
    tenant_id: str
    status: AppStatus
    urls: Dict[str, str]  # frontend_url, api_url, admin_url
    created_at: str
    updated_at: str


@dataclass
class Template:
    id: str
    name: str
    description: str
    category: str
    version: str
    preview_url: Optional[str]
    config_schema: Dict[str, Any]
    features: List[str]


class TauseStackBuilder:
    """
    Cliente SDK para builders externos que consumen TauseStack
    """
    
    def __init__(self, api_key: str, base_url: str = "http://localhost:9001"):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "TauseStack-Builder-SDK/0.7.0"
            }
        )
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def create_app(self, config: AppConfig) -> App:
        """
        Crear nueva aplicación desde template
        
        Args:
            config: Configuración de la aplicación
            
        Returns:
            App: Aplicación creada
            
        Raises:
            Exception: Si hay error en la creación
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/apps/create",
                json={
                    "template_id": config.template_id,
                    "name": config.name,
                    "tenant_id": config.tenant_id,
                    "environment": config.environment,
                    "custom_config": config.custom_config or {}
                }
            )
            response.raise_for_status()
            
            data = response.json()
            return App(
                id=data["id"],
                name=data["name"],
                template_id=data["template_id"],
                tenant_id=data["tenant_id"],
                status=AppStatus(data["status"]),
                urls=data["urls"],
                created_at=data["created_at"],
                updated_at=data["updated_at"]
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error creating app: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to create app: {e.response.text}")
        except Exception as e:
            logger.error(f"Error creating app: {str(e)}")
            raise

    async def list_templates(self, category: Optional[str] = None) -> List[Template]:
        """
        Listar templates disponibles
        
        Args:
            category: Filtrar por categoría (optional)
            
        Returns:
            List[Template]: Lista de templates
        """
        try:
            params = {}
            if category:
                params["category"] = category
                
            response = await self.client.get(
                f"{self.base_url}/api/v1/templates/list",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            return [
                Template(
                    id=t["id"],
                    name=t["name"],
                    description=t["description"],
                    category=t["category"],
                    version=t["version"],
                    preview_url=t.get("preview_url"),
                    config_schema=t["config_schema"],
                    features=t["features"]
                )
                for t in data["templates"]
            ]
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error listing templates: {e.response.status_code}")
            raise Exception(f"Failed to list templates: {e.response.text}")
        except Exception as e:
            logger.error(f"Error listing templates: {str(e)}")
            raise

    async def get_app(self, app_id: str) -> App:
        """
        Obtener información de una aplicación
        
        Args:
            app_id: ID de la aplicación
            
        Returns:
            App: Información de la aplicación
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/apps/{app_id}"
            )
            response.raise_for_status()
            
            data = response.json()
            return App(
                id=data["id"],
                name=data["name"],
                template_id=data["template_id"],
                tenant_id=data["tenant_id"],
                status=AppStatus(data["status"]),
                urls=data["urls"],
                created_at=data["created_at"],
                updated_at=data["updated_at"]
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting app {app_id}: {e.response.status_code}")
            raise Exception(f"Failed to get app: {e.response.text}")
        except Exception as e:
            logger.error(f"Error getting app {app_id}: {str(e)}")
            raise

    async def list_apps(self, tenant_id: Optional[str] = None) -> List[App]:
        """
        Listar aplicaciones del usuario
        
        Args:
            tenant_id: Filtrar por tenant (optional)
            
        Returns:
            List[App]: Lista de aplicaciones
        """
        try:
            params = {}
            if tenant_id:
                params["tenant_id"] = tenant_id
                
            response = await self.client.get(
                f"{self.base_url}/api/v1/apps/list",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            return [
                App(
                    id=app["id"],
                    name=app["name"],
                    template_id=app["template_id"],
                    tenant_id=app["tenant_id"],
                    status=AppStatus(app["status"]),
                    urls=app["urls"],
                    created_at=app["created_at"],
                    updated_at=app["updated_at"]
                )
                for app in data["apps"]
            ]
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error listing apps: {e.response.status_code}")
            raise Exception(f"Failed to list apps: {e.response.text}")
        except Exception as e:
            logger.error(f"Error listing apps: {str(e)}")
            raise

    async def update_app_config(self, app_id: str, config: Dict[str, Any]) -> App:
        """
        Actualizar configuración de aplicación
        
        Args:
            app_id: ID de la aplicación
            config: Nueva configuración
            
        Returns:
            App: Aplicación actualizada
        """
        try:
            response = await self.client.put(
                f"{self.base_url}/api/v1/apps/{app_id}/config",
                json={"config": config}
            )
            response.raise_for_status()
            
            data = response.json()
            return App(
                id=data["id"],
                name=data["name"],
                template_id=data["template_id"],
                tenant_id=data["tenant_id"],
                status=AppStatus(data["status"]),
                urls=data["urls"],
                created_at=data["created_at"],
                updated_at=data["updated_at"]
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error updating app {app_id}: {e.response.status_code}")
            raise Exception(f"Failed to update app: {e.response.text}")
        except Exception as e:
            logger.error(f"Error updating app {app_id}: {str(e)}")
            raise

    async def delete_app(self, app_id: str) -> bool:
        """
        Eliminar aplicación
        
        Args:
            app_id: ID de la aplicación
            
        Returns:
            bool: True si se eliminó correctamente
        """
        try:
            response = await self.client.delete(
                f"{self.base_url}/api/v1/apps/{app_id}"
            )
            response.raise_for_status()
            return True
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error deleting app {app_id}: {e.response.status_code}")
            raise Exception(f"Failed to delete app: {e.response.text}")
        except Exception as e:
            logger.error(f"Error deleting app {app_id}: {str(e)}")
            raise

    async def health_check(self) -> Dict[str, Any]:
        """
        Verificar estado del API de TauseStack
        
        Returns:
            Dict: Estado del sistema
        """
        try:
            response = await self.client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {"status": "error", "message": str(e)}


# Utility functions para uso más sencillo

async def create_app_simple(
    api_key: str,
    template_id: str,
    app_name: str,
    tenant_id: str,
    environment: Dict[str, Any],
    base_url: str = "http://localhost:9001"
) -> App:
    """
    Función utilitaria para crear app con menos boilerplate
    """
    async with TauseStackBuilder(api_key, base_url) as builder:
        config = AppConfig(
            template_id=template_id,
            name=app_name,
            tenant_id=tenant_id,
            environment=environment
        )
        return await builder.create_app(config)


async def list_templates_simple(
    api_key: str,
    category: Optional[str] = None,
    base_url: str = "http://localhost:9001"
) -> List[Template]:
    """
    Función utilitaria para listar templates con menos boilerplate
    """
    async with TauseStackBuilder(api_key, base_url) as builder:
        return await builder.list_templates(category)


# Example usage
if __name__ == "__main__":
    async def demo():
        # Example integration with TausePro
        async with TauseStackBuilder("your-api-key") as builder:
            
            # List available templates
            templates = await builder.list_templates("saas")
            print(f"Available SaaS templates: {len(templates)}")
            
            # Create new app
            if templates:
                config = AppConfig(
                    template_id=templates[0].id,
                    name="My SaaS App",
                    tenant_id="tenant-123",
                    environment={
                        "DATABASE_URL": "postgresql://...",
                        "REDIS_URL": "redis://...",
                        "APP_SECRET": "secret-key"
                    }
                )
                
                app = await builder.create_app(config)
                print(f"Created app: {app.name} with URL: {app.urls.get('frontend_url')}")
    
    asyncio.run(demo()) 