"""
Template Manager para SDK External

Gestiona templates avanzados, validación y metadata
"""

import httpx
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class TemplateValidationResult:
    valid: bool
    errors: List[str]
    warnings: List[str]


@dataclass
class TemplateMetadata:
    id: str
    name: str
    description: str
    category: str
    version: str
    author: str
    created_at: str
    updated_at: str
    download_count: int
    rating: float
    tags: List[str]
    preview_images: List[str]
    demo_url: Optional[str]
    documentation_url: Optional[str]


class TemplateManager:
    """
    Gestión avanzada de templates para builders externos
    """
    
    def __init__(self, api_key: str, base_url: str = "http://localhost:9001"):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "TauseStack-Template-Manager/0.7.0"
            }
        )
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def get_template_metadata(self, template_id: str) -> TemplateMetadata:
        """
        Obtener metadata completa de un template
        
        Args:
            template_id: ID del template
            
        Returns:
            TemplateMetadata: Metadata completa
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/templates/{template_id}/metadata"
            )
            response.raise_for_status()
            
            data = response.json()
            return TemplateMetadata(
                id=data["id"],
                name=data["name"],
                description=data["description"],
                category=data["category"],
                version=data["version"],
                author=data["author"],
                created_at=data["created_at"],
                updated_at=data["updated_at"],
                download_count=data["download_count"],
                rating=data["rating"],
                tags=data["tags"],
                preview_images=data["preview_images"],
                demo_url=data.get("demo_url"),
                documentation_url=data.get("documentation_url")
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting template metadata: {e.response.status_code}")
            raise Exception(f"Failed to get template metadata: {e.response.text}")
        except Exception as e:
            logger.error(f"Error getting template metadata: {str(e)}")
            raise

    async def validate_template_config(self, template_id: str, config: Dict[str, Any]) -> TemplateValidationResult:
        """
        Validar configuración contra schema del template
        
        Args:
            template_id: ID del template
            config: Configuración a validar
            
        Returns:
            TemplateValidationResult: Resultado de la validación
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/templates/{template_id}/validate",
                json={"config": config}
            )
            response.raise_for_status()
            
            data = response.json()
            return TemplateValidationResult(
                valid=data["valid"],
                errors=data["errors"],
                warnings=data["warnings"]
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error validating template config: {e.response.status_code}")
            raise Exception(f"Failed to validate template config: {e.response.text}")
        except Exception as e:
            logger.error(f"Error validating template config: {str(e)}")
            raise

    async def get_template_schema(self, template_id: str) -> Dict[str, Any]:
        """
        Obtener schema de configuración del template
        
        Args:
            template_id: ID del template
            
        Returns:
            Dict: JSON Schema para la configuración
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/templates/{template_id}/schema"
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting template schema: {e.response.status_code}")
            raise Exception(f"Failed to get template schema: {e.response.text}")
        except Exception as e:
            logger.error(f"Error getting template schema: {str(e)}")
            raise

    async def search_templates(
        self, 
        query: str, 
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Buscar templates con filtros avanzados
        
        Args:
            query: Texto de búsqueda
            category: Filtrar por categoría
            tags: Filtrar por tags
            limit: Límite de resultados
            offset: Offset para paginación
            
        Returns:
            Dict: Resultados de búsqueda con metadatos
        """
        try:
            params = {
                "query": query,
                "limit": limit,
                "offset": offset
            }
            
            if category:
                params["category"] = category
            if tags:
                params["tags"] = ",".join(tags)
                
            response = await self.client.get(
                f"{self.base_url}/api/v1/templates/search",
                params=params
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error searching templates: {e.response.status_code}")
            raise Exception(f"Failed to search templates: {e.response.text}")
        except Exception as e:
            logger.error(f"Error searching templates: {str(e)}")
            raise

    async def get_template_dependencies(self, template_id: str) -> Dict[str, Any]:
        """
        Obtener dependencias del template
        
        Args:
            template_id: ID del template
            
        Returns:
            Dict: Dependencias y servicios requeridos
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/templates/{template_id}/dependencies"
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting template dependencies: {e.response.status_code}")
            raise Exception(f"Failed to get template dependencies: {e.response.text}")
        except Exception as e:
            logger.error(f"Error getting template dependencies: {str(e)}")
            raise

    async def clone_template(self, template_id: str, new_name: str, custom_config: Optional[Dict[str, Any]] = None) -> str:
        """
        Clonar template con configuración personalizada
        
        Args:
            template_id: ID del template original
            new_name: Nombre del nuevo template
            custom_config: Configuración personalizada
            
        Returns:
            str: ID del nuevo template clonado
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/templates/{template_id}/clone",
                json={
                    "new_name": new_name,
                    "custom_config": custom_config or {}
                }
            )
            response.raise_for_status()
            
            data = response.json()
            return data["new_template_id"]
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error cloning template: {e.response.status_code}")
            raise Exception(f"Failed to clone template: {e.response.text}")
        except Exception as e:
            logger.error(f"Error cloning template: {str(e)}")
            raise

    async def get_popular_templates(self, category: Optional[str] = None, limit: int = 10) -> List[TemplateMetadata]:
        """
        Obtener templates más populares
        
        Args:
            category: Filtrar por categoría
            limit: Límite de resultados
            
        Returns:
            List[TemplateMetadata]: Templates populares
        """
        try:
            params = {"limit": limit}
            if category:
                params["category"] = category
                
            response = await self.client.get(
                f"{self.base_url}/api/v1/templates/popular",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            return [
                TemplateMetadata(
                    id=t["id"],
                    name=t["name"],
                    description=t["description"],
                    category=t["category"],
                    version=t["version"],
                    author=t["author"],
                    created_at=t["created_at"],
                    updated_at=t["updated_at"],
                    download_count=t["download_count"],
                    rating=t["rating"],
                    tags=t["tags"],
                    preview_images=t["preview_images"],
                    demo_url=t.get("demo_url"),
                    documentation_url=t.get("documentation_url")
                )
                for t in data["templates"]
            ]
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting popular templates: {e.response.status_code}")
            raise Exception(f"Failed to get popular templates: {e.response.text}")
        except Exception as e:
            logger.error(f"Error getting popular templates: {str(e)}")
            raise

    async def rate_template(self, template_id: str, rating: int, review: Optional[str] = None) -> bool:
        """
        Calificar un template
        
        Args:
            template_id: ID del template
            rating: Calificación (1-5)
            review: Reseña opcional
            
        Returns:
            bool: True si se guardó la calificación
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/templates/{template_id}/rate",
                json={
                    "rating": rating,
                    "review": review
                }
            )
            response.raise_for_status()
            return True
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error rating template: {e.response.status_code}")
            raise Exception(f"Failed to rate template: {e.response.text}")
        except Exception as e:
            logger.error(f"Error rating template: {str(e)}")
            raise 