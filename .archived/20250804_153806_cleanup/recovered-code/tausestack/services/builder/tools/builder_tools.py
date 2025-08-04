"""
TauseStack Builder MCP Tools - Siguiendo el MCP Tool Pattern
"""

from typing import Dict, List, Optional, Any
from mcp.server import Server
from mcp.types import Tool, TextContent

from tausestack.services.builder.core.builder_service import (
    BuilderService,
    ProjectType,
    ProjectStatus
)
from tausestack.sdk.mcp import MCPToolBase


class BuilderMCPServer(MCPToolBase):
    """
    Servidor MCP para Builder siguiendo el MCP Tool Pattern de TauseStack
    
    ✅ Hereda de MCPToolBase
    ✅ Multi-tenant support
    ✅ Sigue el patrón establecido
    """
    
    def __init__(self, tenant_id: str):
        super().__init__()
        self.tenant_id = tenant_id
        self.builder_service = BuilderService(tenant_id)
        self.server = Server("tausestack-builder")
        self._setup_tools()
    
    def _setup_tools(self):
        """
        Configurar todas las herramientas MCP del Builder
        """
        tools = [
            Tool(
                name="create_project",
                description="Crear nuevo proyecto en TauseStack Builder",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Nombre del proyecto"
                        },
                        "description": {
                            "type": "string",
                            "description": "Descripción del proyecto"
                        },
                        "project_type": {
                            "type": "string",
                            "enum": ["web", "api", "agent", "ecommerce", "dashboard"],
                            "description": "Tipo de proyecto"
                        },
                        "template_id": {
                            "type": "string",
                            "description": "ID del template a usar (opcional)"
                        }
                    },
                    "required": ["name", "description", "project_type"]
                }
            ),
            Tool(
                name="list_projects",
                description="Listar proyectos del tenant",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_type": {
                            "type": "string",
                            "enum": ["web", "api", "agent", "ecommerce", "dashboard"],
                            "description": "Filtrar por tipo (opcional)"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["draft", "building", "ready", "deployed", "error"],
                            "description": "Filtrar por estado (opcional)"
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="get_project",
                description="Obtener detalles de un proyecto específico",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "ID del proyecto"
                        }
                    },
                    "required": ["project_id"]
                }
            ),
            Tool(
                name="update_project",
                description="Actualizar proyecto existente",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "ID del proyecto"
                        },
                        "name": {
                            "type": "string",
                            "description": "Nuevo nombre (opcional)"
                        },
                        "description": {
                            "type": "string",
                            "description": "Nueva descripción (opcional)"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["draft", "building", "ready", "deployed", "error"],
                            "description": "Nuevo estado (opcional)"
                        }
                    },
                    "required": ["project_id"]
                }
            ),
            Tool(
                name="delete_project",
                description="Eliminar proyecto",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "ID del proyecto"
                        }
                    },
                    "required": ["project_id"]
                }
            ),
            Tool(
                name="build_project",
                description="Construir proyecto usando IA",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "ID del proyecto"
                        }
                    },
                    "required": ["project_id"]
                }
            ),
            Tool(
                name="deploy_project",
                description="Desplegar proyecto",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "ID del proyecto"
                        },
                        "domain": {
                            "type": "string",
                            "description": "Dominio personalizado (opcional)"
                        }
                    },
                    "required": ["project_id"]
                }
            ),
            Tool(
                name="get_builder_stats",
                description="Obtener estadísticas del Builder",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="list_templates",
                description="Listar templates disponibles",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="generate_project_from_description",
                description="Generar proyecto completo desde descripción usando IA",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "description": {
                            "type": "string",
                            "description": "Descripción detallada del proyecto a generar"
                        },
                        "project_type": {
                            "type": "string",
                            "enum": ["web", "api", "agent", "ecommerce", "dashboard"],
                            "description": "Tipo de proyecto sugerido"
                        }
                    },
                    "required": ["description"]
                }
            )
        ]
        
        for tool in tools:
            self.server.list_tools.append(tool)
    
    async def handle_call_tool(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Manejar llamadas a herramientas MCP
        """
        try:
            if name == "create_project":
                return await self._create_project(arguments)
            elif name == "list_projects":
                return await self._list_projects(arguments)
            elif name == "get_project":
                return await self._get_project(arguments)
            elif name == "update_project":
                return await self._update_project(arguments)
            elif name == "delete_project":
                return await self._delete_project(arguments)
            elif name == "build_project":
                return await self._build_project(arguments)
            elif name == "deploy_project":
                return await self._deploy_project(arguments)
            elif name == "get_builder_stats":
                return await self._get_builder_stats(arguments)
            elif name == "list_templates":
                return await self._list_templates(arguments)
            elif name == "generate_project_from_description":
                return await self._generate_project_from_description(arguments)
            else:
                return [TextContent(
                    type="text",
                    text=f"Error: Unknown tool '{name}'"
                )]
                
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error executing tool '{name}': {str(e)}"
            )]
    
    async def _create_project(self, args: Dict[str, Any]) -> List[TextContent]:
        """
        Crear nuevo proyecto
        """
        project_type = ProjectType(args["project_type"])
        
        project = await self.builder_service.create_project(
            name=args["name"],
            description=args["description"],
            project_type=project_type,
            template_id=args.get("template_id")
        )
        
        return [TextContent(
            type="text",
            text=f"✅ Proyecto creado exitosamente!\n\n"
                 f"ID: {project.id}\n"
                 f"Nombre: {project.name}\n"
                 f"Tipo: {project.type.value}\n"
                 f"Estado: {project.status.value}\n"
                 f"Tenant: {project.tenant_id}\n"
                 f"Componentes: {len(project.components)}"
        )]
    
    async def _list_projects(self, args: Dict[str, Any]) -> List[TextContent]:
        """
        Listar proyectos
        """
        project_type = ProjectType(args["project_type"]) if args.get("project_type") else None
        status = ProjectStatus(args["status"]) if args.get("status") else None
        
        projects = await self.builder_service.list_projects(
            project_type=project_type,
            status=status
        )
        
        if not projects:
            return [TextContent(
                type="text",
                text="No hay proyectos disponibles."
            )]
        
        projects_text = f"📋 Proyectos encontrados: {len(projects)}\n\n"
        
        for project in projects:
            projects_text += f"• **{project.name}** ({project.id})\n"
            projects_text += f"  - Tipo: {project.type.value}\n"
            projects_text += f"  - Estado: {project.status.value}\n"
            projects_text += f"  - Componentes: {len(project.components)}\n"
            projects_text += f"  - Actualizado: {project.updated_at[:10]}\n\n"
        
        return [TextContent(type="text", text=projects_text)]
    
    async def _get_project(self, args: Dict[str, Any]) -> List[TextContent]:
        """
        Obtener proyecto específico
        """
        project = await self.builder_service.get_project(args["project_id"])
        
        if not project:
            return [TextContent(
                type="text",
                text=f"❌ Proyecto {args['project_id']} no encontrado."
            )]
        
        project_text = f"🎯 **{project.name}**\n\n"
        project_text += f"ID: {project.id}\n"
        project_text += f"Descripción: {project.description}\n"
        project_text += f"Tipo: {project.type.value}\n"
        project_text += f"Estado: {project.status.value}\n"
        project_text += f"Tenant: {project.tenant_id}\n"
        project_text += f"Creado: {project.created_at[:10]}\n"
        project_text += f"Actualizado: {project.updated_at[:10]}\n"
        project_text += f"Componentes: {len(project.components)}\n\n"
        
        if project.components:
            project_text += "**Componentes:**\n"
            for comp in project.components:
                project_text += f"• {comp.name} ({comp.type})\n"
        
        if project.config.domain:
            project_text += f"\n**Dominio:** {project.config.domain}\n"
        
        return [TextContent(type="text", text=project_text)]
    
    async def _update_project(self, args: Dict[str, Any]) -> List[TextContent]:
        """
        Actualizar proyecto
        """
        updates = {}
        for key in ["name", "description", "status"]:
            if key in args:
                updates[key] = args[key]
        
        if not updates:
            return [TextContent(
                type="text",
                text="❌ No se proporcionaron campos para actualizar."
            )]
        
        project = await self.builder_service.update_project(
            args["project_id"],
            updates
        )
        
        if not project:
            return [TextContent(
                type="text",
                text=f"❌ Proyecto {args['project_id']} no encontrado."
            )]
        
        return [TextContent(
            type="text",
            text=f"✅ Proyecto actualizado exitosamente!\n\n"
                 f"Nombre: {project.name}\n"
                 f"Estado: {project.status.value}\n"
                 f"Actualizado: {project.updated_at[:16]}"
        )]
    
    async def _delete_project(self, args: Dict[str, Any]) -> List[TextContent]:
        """
        Eliminar proyecto
        """
        success = await self.builder_service.delete_project(args["project_id"])
        
        if not success:
            return [TextContent(
                type="text",
                text=f"❌ Error eliminando proyecto {args['project_id']}."
            )]
        
        return [TextContent(
            type="text",
            text=f"✅ Proyecto {args['project_id']} eliminado exitosamente."
        )]
    
    async def _build_project(self, args: Dict[str, Any]) -> List[TextContent]:
        """
        Construir proyecto
        """
        success = await self.builder_service.build_project(args["project_id"])
        
        if not success:
            return [TextContent(
                type="text",
                text=f"❌ Error construyendo proyecto {args['project_id']}."
            )]
        
        return [TextContent(
            type="text",
            text=f"🔨 Construcción iniciada para proyecto {args['project_id']}.\n"
                 f"El proyecto se está generando usando IA. Revisa el estado en unos minutos."
        )]
    
    async def _deploy_project(self, args: Dict[str, Any]) -> List[TextContent]:
        """
        Desplegar proyecto
        """
        success = await self.builder_service.deploy_project(
            args["project_id"],
            domain=args.get("domain")
        )
        
        if not success:
            return [TextContent(
                type="text",
                text=f"❌ Error desplegando proyecto {args['project_id']}."
            )]
        
        domain_text = f" en {args['domain']}" if args.get("domain") else ""
        
        return [TextContent(
            type="text",
            text=f"🚀 Proyecto {args['project_id']} desplegado exitosamente{domain_text}!"
        )]
    
    async def _get_builder_stats(self, args: Dict[str, Any]) -> List[TextContent]:
        """
        Obtener estadísticas del Builder
        """
        stats = await self.builder_service.get_stats()
        
        stats_text = f"📊 **Estadísticas del Builder**\n\n"
        stats_text += f"• Total proyectos: {stats.total_projects}\n"
        stats_text += f"• Construyendo actualmente: {stats.active_builds}\n"
        stats_text += f"• Despliegues exitosos: {stats.successful_deploys}\n"
        stats_text += f"• Errores: {stats.failed_deploys}\n"
        stats_text += f"• Templates usados: {stats.templates_used}\n"
        
        return [TextContent(type="text", text=stats_text)]
    
    async def _list_templates(self, args: Dict[str, Any]) -> List[TextContent]:
        """
        Listar templates disponibles
        """
        templates = [
            {"id": "web-basic", "name": "Web App Básica", "type": "web"},
            {"id": "api-rest", "name": "API REST", "type": "api"},
            {"id": "agent-ai", "name": "Agente IA", "type": "agent"},
            {"id": "ecommerce-basic", "name": "E-commerce Básico", "type": "ecommerce"},
            {"id": "dashboard-analytics", "name": "Dashboard Analytics", "type": "dashboard"}
        ]
        
        templates_text = f"📋 **Templates disponibles:**\n\n"
        
        for template in templates:
            templates_text += f"• **{template['name']}** (`{template['id']}`)\n"
            templates_text += f"  - Tipo: {template['type']}\n\n"
        
        return [TextContent(type="text", text=templates_text)]
    
    async def _generate_project_from_description(self, args: Dict[str, Any]) -> List[TextContent]:
        """
        Generar proyecto completo desde descripción usando IA
        """
        description = args["description"]
        project_type = ProjectType(args.get("project_type", "web"))
        
        # Generar nombre automáticamente
        name = description.split('.')[0][:50] if '.' in description else description[:50]
        
        project = await self.builder_service.create_project(
            name=name,
            description=description,
            project_type=project_type
        )
        
        # Construir automáticamente
        build_success = await self.builder_service.build_project(project.id)
        
        result_text = f"🎯 **Proyecto generado desde descripción:**\n\n"
        result_text += f"Nombre: {project.name}\n"
        result_text += f"ID: {project.id}\n"
        result_text += f"Tipo: {project.type.value}\n"
        result_text += f"Estado: {project.status.value}\n\n"
        
        if build_success:
            result_text += "✅ Construcción iniciada automáticamente.\n"
            result_text += "El proyecto se está generando usando IA basado en tu descripción."
        else:
            result_text += "⚠️ Proyecto creado pero la construcción falló."
        
        return [TextContent(type="text", text=result_text)]
    
    def get_server(self) -> Server:
        """
        Obtener instancia del servidor MCP
        """
        return self.server 