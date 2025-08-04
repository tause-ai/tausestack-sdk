"""
Deployment Manager para SDK External

Gestiona deployments, pipelines y monitoring
"""

import httpx
import asyncio
from typing import Dict, List, Optional, Any, AsyncGenerator
from dataclasses import dataclass
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class DeploymentStatus(Enum):
    PENDING = "pending"
    BUILDING = "building"
    DEPLOYING = "deploying"
    ACTIVE = "active"
    FAILED = "failed"
    STOPPED = "stopped"
    ROLLED_BACK = "rolled_back"


class DeploymentEnvironment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class DeploymentConfig:
    app_id: str
    environment: DeploymentEnvironment
    config: Dict[str, Any]
    auto_deploy: bool = False
    rollback_on_failure: bool = True


@dataclass
class Deployment:
    id: str
    app_id: str
    environment: str
    status: DeploymentStatus
    version: str
    urls: Dict[str, str]
    logs_url: str
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    error_message: Optional[str]
    metrics: Dict[str, Any]


@dataclass
class DeploymentLog:
    timestamp: str
    level: str
    message: str
    source: str


class DeploymentManager:
    """
    Gestión de deployments para builders externos
    """
    
    def __init__(self, api_key: str, base_url: str = "http://localhost:9001"):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(
            timeout=60.0,  # Longer timeout for deployments
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "TauseStack-Deployment-Manager/0.7.0"
            }
        )
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def start_deployment(self, config: DeploymentConfig) -> Deployment:
        """
        Iniciar nuevo deployment
        
        Args:
            config: Configuración del deployment
            
        Returns:
            Deployment: Deployment iniciado
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/deploy/start",
                json={
                    "app_id": config.app_id,
                    "environment": config.environment.value,
                    "config": config.config,
                    "auto_deploy": config.auto_deploy,
                    "rollback_on_failure": config.rollback_on_failure
                }
            )
            response.raise_for_status()
            
            data = response.json()
            return Deployment(
                id=data["id"],
                app_id=data["app_id"],
                environment=data["environment"],
                status=DeploymentStatus(data["status"]),
                version=data["version"],
                urls=data["urls"],
                logs_url=data["logs_url"],
                created_at=data["created_at"],
                started_at=data.get("started_at"),
                completed_at=data.get("completed_at"),
                error_message=data.get("error_message"),
                metrics=data.get("metrics", {})
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error starting deployment: {e.response.status_code}")
            raise Exception(f"Failed to start deployment: {e.response.text}")
        except Exception as e:
            logger.error(f"Error starting deployment: {str(e)}")
            raise

    async def get_deployment(self, deployment_id: str) -> Deployment:
        """
        Obtener información de un deployment
        
        Args:
            deployment_id: ID del deployment
            
        Returns:
            Deployment: Información del deployment
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/deploy/{deployment_id}"
            )
            response.raise_for_status()
            
            data = response.json()
            return Deployment(
                id=data["id"],
                app_id=data["app_id"],
                environment=data["environment"],
                status=DeploymentStatus(data["status"]),
                version=data["version"],
                urls=data["urls"],
                logs_url=data["logs_url"],
                created_at=data["created_at"],
                started_at=data.get("started_at"),
                completed_at=data.get("completed_at"),
                error_message=data.get("error_message"),
                metrics=data.get("metrics", {})
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting deployment: {e.response.status_code}")
            raise Exception(f"Failed to get deployment: {e.response.text}")
        except Exception as e:
            logger.error(f"Error getting deployment: {str(e)}")
            raise

    async def list_deployments(self, app_id: Optional[str] = None, environment: Optional[str] = None) -> List[Deployment]:
        """
        Listar deployments
        
        Args:
            app_id: Filtrar por app ID
            environment: Filtrar por environment
            
        Returns:
            List[Deployment]: Lista de deployments
        """
        try:
            params = {}
            if app_id:
                params["app_id"] = app_id
            if environment:
                params["environment"] = environment
                
            response = await self.client.get(
                f"{self.base_url}/api/v1/deploy/list",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            return [
                Deployment(
                    id=d["id"],
                    app_id=d["app_id"],
                    environment=d["environment"],
                    status=DeploymentStatus(d["status"]),
                    version=d["version"],
                    urls=d["urls"],
                    logs_url=d["logs_url"],
                    created_at=d["created_at"],
                    started_at=d.get("started_at"),
                    completed_at=d.get("completed_at"),
                    error_message=d.get("error_message"),
                    metrics=d.get("metrics", {})
                )
                for d in data["deployments"]
            ]
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error listing deployments: {e.response.status_code}")
            raise Exception(f"Failed to list deployments: {e.response.text}")
        except Exception as e:
            logger.error(f"Error listing deployments: {str(e)}")
            raise

    async def stop_deployment(self, deployment_id: str) -> bool:
        """
        Detener un deployment
        
        Args:
            deployment_id: ID del deployment
            
        Returns:
            bool: True si se detuvo correctamente
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/deploy/{deployment_id}/stop"
            )
            response.raise_for_status()
            return True
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error stopping deployment: {e.response.status_code}")
            raise Exception(f"Failed to stop deployment: {e.response.text}")
        except Exception as e:
            logger.error(f"Error stopping deployment: {str(e)}")
            raise

    async def rollback_deployment(self, deployment_id: str, target_version: Optional[str] = None) -> Deployment:
        """
        Hacer rollback de un deployment
        
        Args:
            deployment_id: ID del deployment
            target_version: Versión objetivo (si no se especifica, usa la anterior)
            
        Returns:
            Deployment: Nuevo deployment con rollback
        """
        try:
            payload = {}
            if target_version:
                payload["target_version"] = target_version
                
            response = await self.client.post(
                f"{self.base_url}/api/v1/deploy/{deployment_id}/rollback",
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            return Deployment(
                id=data["id"],
                app_id=data["app_id"],
                environment=data["environment"],
                status=DeploymentStatus(data["status"]),
                version=data["version"],
                urls=data["urls"],
                logs_url=data["logs_url"],
                created_at=data["created_at"],
                started_at=data.get("started_at"),
                completed_at=data.get("completed_at"),
                error_message=data.get("error_message"),
                metrics=data.get("metrics", {})
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error rolling back deployment: {e.response.status_code}")
            raise Exception(f"Failed to rollback deployment: {e.response.text}")
        except Exception as e:
            logger.error(f"Error rolling back deployment: {str(e)}")
            raise

    async def get_deployment_logs(self, deployment_id: str, lines: int = 100) -> List[DeploymentLog]:
        """
        Obtener logs de un deployment
        
        Args:
            deployment_id: ID del deployment
            lines: Número de líneas a obtener
            
        Returns:
            List[DeploymentLog]: Logs del deployment
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/deploy/{deployment_id}/logs",
                params={"lines": lines}
            )
            response.raise_for_status()
            
            data = response.json()
            return [
                DeploymentLog(
                    timestamp=log["timestamp"],
                    level=log["level"],
                    message=log["message"],
                    source=log["source"]
                )
                for log in data["logs"]
            ]
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting deployment logs: {e.response.status_code}")
            raise Exception(f"Failed to get deployment logs: {e.response.text}")
        except Exception as e:
            logger.error(f"Error getting deployment logs: {str(e)}")
            raise

    async def stream_deployment_logs(self, deployment_id: str) -> AsyncGenerator[DeploymentLog, None]:
        """
        Stream logs de un deployment en tiempo real
        
        Args:
            deployment_id: ID del deployment
            
        Yields:
            DeploymentLog: Logs en tiempo real
        """
        try:
            async with self.client.stream(
                "GET",
                f"{self.base_url}/api/v1/deploy/{deployment_id}/logs/stream"
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            log_data = json.loads(line)
                            yield DeploymentLog(
                                timestamp=log_data["timestamp"],
                                level=log_data["level"],
                                message=log_data["message"],
                                source=log_data["source"]
                            )
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse log line: {line}")
                            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error streaming deployment logs: {e.response.status_code}")
            raise Exception(f"Failed to stream deployment logs: {e.response.text}")
        except Exception as e:
            logger.error(f"Error streaming deployment logs: {str(e)}")
            raise

    async def get_deployment_metrics(self, deployment_id: str) -> Dict[str, Any]:
        """
        Obtener métricas de un deployment
        
        Args:
            deployment_id: ID del deployment
            
        Returns:
            Dict: Métricas del deployment
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/deploy/{deployment_id}/metrics"
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting deployment metrics: {e.response.status_code}")
            raise Exception(f"Failed to get deployment metrics: {e.response.text}")
        except Exception as e:
            logger.error(f"Error getting deployment metrics: {str(e)}")
            raise

    async def wait_for_deployment(self, deployment_id: str, timeout: int = 600) -> Deployment:
        """
        Esperar a que un deployment se complete
        
        Args:
            deployment_id: ID del deployment
            timeout: Timeout en segundos
            
        Returns:
            Deployment: Deployment completado
        """
        start_time = asyncio.get_event_loop().time()
        
        while True:
            deployment = await self.get_deployment(deployment_id)
            
            if deployment.status in [DeploymentStatus.ACTIVE, DeploymentStatus.FAILED, DeploymentStatus.STOPPED]:
                return deployment
                
            current_time = asyncio.get_event_loop().time()
            if current_time - start_time > timeout:
                raise TimeoutError(f"Deployment {deployment_id} did not complete within {timeout} seconds")
                
            await asyncio.sleep(5)  # Check every 5 seconds

    async def health_check_deployment(self, deployment_id: str) -> Dict[str, Any]:
        """
        Health check de un deployment específico
        
        Args:
            deployment_id: ID del deployment
            
        Returns:
            Dict: Estado de salud del deployment
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/deploy/{deployment_id}/health"
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error checking deployment health: {e.response.status_code}")
            raise Exception(f"Failed to check deployment health: {e.response.text}")
        except Exception as e:
            logger.error(f"Error checking deployment health: {str(e)}")
            raise


# Utility functions

async def deploy_app_simple(
    api_key: str,
    app_id: str,
    environment: str = "production",
    config: Optional[Dict[str, Any]] = None,
    wait: bool = True,
    base_url: str = "http://localhost:9001"
) -> Deployment:
    """
    Deploy app con menos boilerplate
    """
    async with DeploymentManager(api_key, base_url) as deployer:
        deploy_config = DeploymentConfig(
            app_id=app_id,
            environment=DeploymentEnvironment(environment),
            config=config or {},
            auto_deploy=True
        )
        
        deployment = await deployer.start_deployment(deploy_config)
        
        if wait:
            deployment = await deployer.wait_for_deployment(deployment.id)
            
        return deployment 