"""
TauseStack Builder Service - Visual App Builder
Siguiendo el Service Pattern de TauseStack
"""

import uuid
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

from tausestack.sdk.storage import json_client, binary_client


class ProjectType(Enum):
    WEB = "web"
    API = "api"
    AGENT = "agent"
    ECOMMERCE = "ecommerce"
    DASHBOARD = "dashboard"


class ProjectStatus(Enum):
    DRAFT = "draft"
    BUILDING = "building"
    READY = "ready"
    DEPLOYED = "deployed"
    ERROR = "error"


@dataclass
class ProjectComponent:
    id: str
    type: str  # 'page', 'component', 'api', 'database', 'service'
    name: str
    config: Dict[str, Any]
    dependencies: List[str]


@dataclass
class ProjectConfig:
    domain: Optional[str] = None
    database_type: Optional[str] = None
    ai_services: Optional[List[str]] = None
    notifications: bool = False
    analytics: bool = False


@dataclass
class Project:
    id: str
    name: str
    description: str
    type: ProjectType
    status: ProjectStatus
    tenant_id: str
    created_at: str
    updated_at: str
    components: List[ProjectComponent]
    config: ProjectConfig


@dataclass
class BuilderStats:
    total_projects: int
    active_builds: int
    successful_deploys: int
    failed_deploys: int
    templates_used: int


class BuilderService:
    """
    Servicio Builder siguiendo el Service Pattern de TauseStack
    
    ✅ Multi-tenant con tenant_id
    ✅ Usa servicios existentes de TauseStack
    ✅ Sigue el patrón establecido
    """
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.json_client = json_client
        self.binary_client = binary_client
        
        # Clave base para el tenant en storage
        self.tenant_key = f"builder/{tenant_id}"
        
    async def create_project(self, 
                           name: str, 
                           description: str, 
                           project_type: ProjectType,
                           template_id: Optional[str] = None) -> Project:
        """
        Crear nuevo proyecto siguiendo el patrón multi-tenant
        """
        project_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        # Crear proyecto base
        project = Project(
            id=project_id,
            name=name,
            description=description,
            type=project_type,
            status=ProjectStatus.DRAFT,
            tenant_id=self.tenant_id,
            created_at=now,
            updated_at=now,
            components=[],
            config=ProjectConfig()
        )
        
        # Si hay template, aplicar configuración
        if template_id:
            await self._apply_template(project, template_id)
        
        # Guardar en storage multi-tenant
        await self.json_client.save(
            f"{self.tenant_key}/projects/{project_id}",
            asdict(project)
        )
        
        # TODO: Integrar con sistema de notificaciones cuando esté disponible
        # await self.notify.send_notification(...)
        print(f"Proyecto creado: {name} ({project_id})")
        
        return project
        
    async def get_project(self, project_id: str) -> Optional[Project]:
        """
        Obtener proyecto específico respetando multi-tenant
        """
        try:
            project_data = await self.json_client.load(
                f"{self.tenant_key}/projects/{project_id}"
            )
            
            if not project_data:
                return None
                
            # Convertir dict a Project
            return self._dict_to_project(project_data)
            
        except Exception as e:
            print(f"Error loading project {project_id}: {e}")
            return None
            
    async def list_projects(self, 
                          project_type: Optional[ProjectType] = None,
                          status: Optional[ProjectStatus] = None) -> List[Project]:
        """
        Listar proyectos del tenant con filtros opcionales
        """
        try:
            # TODO: Implementar list_projects cuando json_client tenga list_keys
            # Por ahora devolvemos una lista vacía
            projects = []
            return projects
            
        except Exception as e:
            print(f"Error listing projects: {e}")
            return []
            
    async def update_project(self, project_id: str, updates: Dict[str, Any]) -> Optional[Project]:
        """
        Actualizar proyecto existente
        """
        project = await self.get_project(project_id)
        if not project:
            return None
            
        # Aplicar updates
        for key, value in updates.items():
            if hasattr(project, key):
                setattr(project, key, value)
                
        # Actualizar timestamp
        project.updated_at = datetime.utcnow().isoformat()
        
        # Guardar cambios
        await self.json_client.save(
            f"{self.tenant_key}/projects/{project_id}",
            asdict(project)
        )
        
        return project
        
    async def delete_project(self, project_id: str) -> bool:
        """
        Eliminar proyecto del tenant
        """
        try:
            # Verificar que existe
            project = await self.get_project(project_id)
            if not project:
                return False
                
            # Eliminar del storage
            await self.json_client.delete(f"{self.tenant_key}/projects/{project_id}")
            
            # TODO: Integrar con sistema de notificaciones cuando esté disponible
            print(f"Proyecto eliminado: {project.name} ({project_id})")
            
            return True
            
        except Exception as e:
            print(f"Error deleting project {project_id}: {e}")
            return False
            
    async def build_project(self, project_id: str) -> bool:
        """
        Construir proyecto usando servicios IA de TauseStack
        """
        project = await self.get_project(project_id)
        if not project:
            return False
            
        try:
            # Actualizar estado
            project.status = ProjectStatus.BUILDING
            await self.update_project(project_id, {"status": ProjectStatus.BUILDING})
            
            # Generar código usando AI service
            build_prompt = f"""
            Generar código para proyecto:
            - Nombre: {project.name}
            - Tipo: {project.type.value}
            - Descripción: {project.description}
            - Componentes: {len(project.components)}
            
            Crear estructura completa del proyecto siguiendo las mejores prácticas.
            """
            
            # TODO: Integrar con AI service cuando esté disponible
            # Por ahora simularemos la construcción
            ai_response = {
                "success": True,
                "code": "# Código generado simulado",
                "components": []
            }
            
            if ai_response.get("success"):
                # Guardar código generado
                await self.json_client.save(
                    f"{self.tenant_key}/projects/{project_id}/build",
                    ai_response
                )
                
                # Actualizar estado
                project.status = ProjectStatus.READY
                await self.update_project(project_id, {"status": ProjectStatus.READY})
                
                return True
            else:
                # Error en generación
                project.status = ProjectStatus.ERROR
                await self.update_project(project_id, {"status": ProjectStatus.ERROR})
                return False
                
        except Exception as e:
            print(f"Error building project {project_id}: {e}")
            project.status = ProjectStatus.ERROR
            await self.update_project(project_id, {"status": ProjectStatus.ERROR})
            return False
            
    async def deploy_project(self, project_id: str, domain: Optional[str] = None) -> bool:
        """
        Desplegar proyecto usando infraestructura de TauseStack
        """
        project = await self.get_project(project_id)
        if not project or project.status != ProjectStatus.READY:
            return False
            
        try:
            # Obtener código generado
            build_data = await self.json_client.load(
                f"{self.tenant_key}/projects/{project_id}/build"
            )
            
            if not build_data:
                return False
                
            # Configurar dominio
            if domain:
                project.config.domain = domain
                
            # Simular despliegue (integrar con infraestructura real)
            deployment_config = {
                "project_id": project_id,
                "tenant_id": self.tenant_id,
                "domain": project.config.domain,
                "build_data": build_data
            }
            
            # Guardar configuración de despliegue
            await self.json_client.save(
                f"{self.tenant_key}/projects/{project_id}/deployment",
                deployment_config
            )
            
            # Actualizar estado
            project.status = ProjectStatus.DEPLOYED
            await self.update_project(project_id, {"status": ProjectStatus.DEPLOYED})
            
            # TODO: Integrar con sistema de notificaciones cuando esté disponible
            print(f"Proyecto desplegado: {project.name} en {project.config.domain}")
            
            return True
            
        except Exception as e:
            print(f"Error deploying project {project_id}: {e}")
            return False
            
    async def get_stats(self) -> BuilderStats:
        """
        Obtener estadísticas del tenant
        """
        try:
            projects = await self.list_projects()
            
            stats = BuilderStats(
                total_projects=len(projects),
                active_builds=len([p for p in projects if p.status == ProjectStatus.BUILDING]),
                successful_deploys=len([p for p in projects if p.status == ProjectStatus.DEPLOYED]),
                failed_deploys=len([p for p in projects if p.status == ProjectStatus.ERROR]),
                templates_used=0  # TODO: implementar tracking de templates
            )
            
            return stats
            
        except Exception as e:
            print(f"Error getting stats: {e}")
            return BuilderStats(0, 0, 0, 0, 0)
            
    async def _apply_template(self, project: Project, template_id: str):
        """
        Aplicar template al proyecto
        """
        try:
            # Cargar template (integrar con sistema de templates existente)
            template_data = await self.json_client.load(f"templates/{template_id}")
            
            if template_data:
                # Aplicar componentes del template
                if "components" in template_data:
                    for comp_data in template_data["components"]:
                        component = ProjectComponent(
                            id=str(uuid.uuid4()),
                            type=comp_data.get("type", "component"),
                            name=comp_data.get("name", "Untitled"),
                            config=comp_data.get("config", {}),
                            dependencies=comp_data.get("dependencies", [])
                        )
                        project.components.append(component)
                        
                # Aplicar configuración del template
                if "config" in template_data:
                    config_data = template_data["config"]
                    project.config = ProjectConfig(
                        domain=config_data.get("domain"),
                        database_type=config_data.get("database_type"),
                        ai_services=config_data.get("ai_services"),
                        notifications=config_data.get("notifications", False),
                        analytics=config_data.get("analytics", False)
                    )
                    
        except Exception as e:
            print(f"Error applying template {template_id}: {e}")
            
    def _dict_to_project(self, data: Dict[str, Any]) -> Project:
        """
        Convertir dict a Project object
        """
        components = []
        if "components" in data:
            for comp_data in data["components"]:
                component = ProjectComponent(
                    id=comp_data["id"],
                    type=comp_data["type"],
                    name=comp_data["name"],
                    config=comp_data["config"],
                    dependencies=comp_data["dependencies"]
                )
                components.append(component)
                
        config = ProjectConfig()
        if "config" in data:
            config_data = data["config"]
            config = ProjectConfig(
                domain=config_data.get("domain"),
                database_type=config_data.get("database_type"),
                ai_services=config_data.get("ai_services"),
                notifications=config_data.get("notifications", False),
                analytics=config_data.get("analytics", False)
            )
            
        return Project(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            type=ProjectType(data["type"]),
            status=ProjectStatus(data["status"]),
            tenant_id=data["tenant_id"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            components=components,
            config=config
        ) 