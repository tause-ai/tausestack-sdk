"""
Agent Tools - Herramientas integradas con TauseStack
"""

from typing import Dict, Any, List, Optional, Callable
from enum import Enum


class ToolCategory(str, Enum):
    """Categorías de herramientas"""
    COMMUNICATION = "communication"
    DATA_ANALYSIS = "data_analysis"
    CONTENT_CREATION = "content_creation"
    ECOMMERCE = "ecommerce"
    PAYMENTS = "payments"
    INTEGRATION = "integration"
    UTILITY = "utility"


class AgentTool:
    """Definición de una herramienta"""
    
    def __init__(
        self,
        name: str,
        description: str,
        category: ToolCategory,
        parameters: Dict[str, Any],
        handler: Optional[Callable] = None,
        requires_auth: bool = False,
        tenant_scoped: bool = True
    ):
        self.name = name
        self.description = description
        self.category = category
        self.parameters = parameters
        self.handler = handler
        self.requires_auth = requires_auth
        self.tenant_scoped = tenant_scoped
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            'name': self.name,
            'description': self.description,
            'category': self.category.value,
            'parameters': self.parameters,
            'requires_auth': self.requires_auth,
            'tenant_scoped': self.tenant_scoped
        }


class AgentToolsManager:
    """Gestor de herramientas para agentes"""
    
    def __init__(
        self,
        allowed_tools: List[str] = None,
        restricted_tools: List[str] = None
    ):
        self.allowed_tools = allowed_tools or []
        self.restricted_tools = restricted_tools or []
        self.tools: Dict[str, AgentTool] = {}
        
        # Cargar herramientas por defecto
        self._load_default_tools()
    
    def _load_default_tools(self):
        """Cargar herramientas por defecto integradas con TauseStack"""
        
        # Herramientas de comunicación
        self.tools['send_email'] = AgentTool(
            name="send_email",
            description="Enviar email usando el sistema de notificaciones de TauseStack",
            category=ToolCategory.COMMUNICATION,
            parameters={
                'to': {'type': 'string', 'required': True},
                'subject': {'type': 'string', 'required': True},
                'body': {'type': 'string', 'required': True},
                'template': {'type': 'string', 'required': False}
            },
            requires_auth=True,
            tenant_scoped=True
        )
        
        self.tools['send_notification'] = AgentTool(
            name="send_notification",
            description="Enviar notificación usando el sistema de notificaciones",
            category=ToolCategory.COMMUNICATION,
            parameters={
                'message': {'type': 'string', 'required': True},
                'type': {'type': 'string', 'required': True},
                'recipients': {'type': 'array', 'required': True}
            },
            requires_auth=True,
            tenant_scoped=True
        )
        
        # Herramientas de análisis de datos
        self.tools['analyze_data'] = AgentTool(
            name="analyze_data",
            description="Analizar datos usando el sistema de analytics",
            category=ToolCategory.DATA_ANALYSIS,
            parameters={
                'data_source': {'type': 'string', 'required': True},
                'analysis_type': {'type': 'string', 'required': True},
                'filters': {'type': 'object', 'required': False}
            },
            tenant_scoped=True
        )
        
        self.tools['generate_report'] = AgentTool(
            name="generate_report",
            description="Generar reporte usando datos del tenant",
            category=ToolCategory.DATA_ANALYSIS,
            parameters={
                'report_type': {'type': 'string', 'required': True},
                'date_range': {'type': 'object', 'required': True},
                'format': {'type': 'string', 'required': False}
            },
            tenant_scoped=True
        )
        
        # Herramientas de creación de contenido
        self.tools['create_template'] = AgentTool(
            name="create_template",
            description="Crear plantilla usando el Template Engine",
            category=ToolCategory.CONTENT_CREATION,
            parameters={
                'template_type': {'type': 'string', 'required': True},
                'content': {'type': 'string', 'required': True},
                'variables': {'type': 'object', 'required': False}
            },
            tenant_scoped=True
        )
        
        self.tools['render_template'] = AgentTool(
            name="render_template",
            description="Renderizar plantilla con datos",
            category=ToolCategory.CONTENT_CREATION,
            parameters={
                'template_id': {'type': 'string', 'required': True},
                'data': {'type': 'object', 'required': True}
            },
            tenant_scoped=True
        )
        
        # Herramientas de ecommerce
        self.tools['get_product_info'] = AgentTool(
            name="get_product_info",
            description="Obtener información de productos (integración Saleor)",
            category=ToolCategory.ECOMMERCE,
            parameters={
                'product_id': {'type': 'string', 'required': False},
                'sku': {'type': 'string', 'required': False},
                'category': {'type': 'string', 'required': False}
            },
            tenant_scoped=True
        )
        
        self.tools['update_inventory'] = AgentTool(
            name="update_inventory",
            description="Actualizar inventario de productos",
            category=ToolCategory.ECOMMERCE,
            parameters={
                'product_id': {'type': 'string', 'required': True},
                'quantity': {'type': 'number', 'required': True},
                'operation': {'type': 'string', 'required': True}
            },
            requires_auth=True,
            tenant_scoped=True
        )
        
        self.tools['create_order'] = AgentTool(
            name="create_order",
            description="Crear orden de compra",
            category=ToolCategory.ECOMMERCE,
            parameters={
                'customer_id': {'type': 'string', 'required': True},
                'items': {'type': 'array', 'required': True},
                'shipping_address': {'type': 'object', 'required': True}
            },
            requires_auth=True,
            tenant_scoped=True
        )
        
        # Herramientas de pagos
        self.tools['process_payment'] = AgentTool(
            name="process_payment",
            description="Procesar pago usando Wompi",
            category=ToolCategory.PAYMENTS,
            parameters={
                'amount': {'type': 'number', 'required': True},
                'currency': {'type': 'string', 'required': True},
                'payment_method': {'type': 'string', 'required': True},
                'customer_info': {'type': 'object', 'required': True}
            },
            requires_auth=True,
            tenant_scoped=True
        )
        
        self.tools['check_payment_status'] = AgentTool(
            name="check_payment_status",
            description="Verificar estado de pago",
            category=ToolCategory.PAYMENTS,
            parameters={
                'payment_id': {'type': 'string', 'required': True}
            },
            tenant_scoped=True
        )
        
        # Herramientas de integración
        self.tools['call_external_api'] = AgentTool(
            name="call_external_api",
            description="Llamar API externa configurada",
            category=ToolCategory.INTEGRATION,
            parameters={
                'api_name': {'type': 'string', 'required': True},
                'endpoint': {'type': 'string', 'required': True},
                'method': {'type': 'string', 'required': True},
                'data': {'type': 'object', 'required': False}
            },
            requires_auth=True,
            tenant_scoped=True
        )
        
        # Herramientas de utilidad
        self.tools['store_data'] = AgentTool(
            name="store_data",
            description="Almacenar datos usando TauseStack Storage",
            category=ToolCategory.UTILITY,
            parameters={
                'key': {'type': 'string', 'required': True},
                'data': {'type': 'object', 'required': True},
                'ttl': {'type': 'number', 'required': False}
            },
            tenant_scoped=True
        )
        
        self.tools['retrieve_data'] = AgentTool(
            name="retrieve_data",
            description="Recuperar datos del storage",
            category=ToolCategory.UTILITY,
            parameters={
                'key': {'type': 'string', 'required': True}
            },
            tenant_scoped=True
        )
        
        self.tools['search_knowledge_base'] = AgentTool(
            name="search_knowledge_base",
            description="Buscar en la base de conocimiento",
            category=ToolCategory.UTILITY,
            parameters={
                'query': {'type': 'string', 'required': True},
                'limit': {'type': 'number', 'required': False}
            },
            tenant_scoped=True
        )
    
    def get_available_tools(self) -> List[str]:
        """Obtener lista de herramientas disponibles"""
        available = []
        
        for tool_name in self.tools.keys():
            if self.is_tool_available(tool_name):
                available.append(tool_name)
        
        return available
    
    def is_tool_available(self, tool_name: str) -> bool:
        """Verificar si una herramienta está disponible"""
        if tool_name not in self.tools:
            return False
        
        # Si está en la lista de restricciones, no está disponible
        if tool_name in self.restricted_tools:
            return False
        
        # Si hay lista de permitidas, debe estar en ella
        if self.allowed_tools:
            return tool_name in self.allowed_tools
        
        return True
    
    def get_tool(self, tool_name: str) -> Optional[AgentTool]:
        """Obtener herramienta por nombre"""
        if self.is_tool_available(tool_name):
            return self.tools.get(tool_name)
        return None
    
    def get_tools_by_category(self, category: ToolCategory) -> List[AgentTool]:
        """Obtener herramientas por categoría"""
        tools = []
        for tool in self.tools.values():
            if tool.category == category and self.is_tool_available(tool.name):
                tools.append(tool)
        return tools
    
    def update_tools(
        self,
        allowed_tools: List[str] = None,
        restricted_tools: List[str] = None
    ):
        """Actualizar configuración de herramientas"""
        if allowed_tools is not None:
            self.allowed_tools = allowed_tools
        if restricted_tools is not None:
            self.restricted_tools = restricted_tools
    
    def add_custom_tool(self, tool: AgentTool):
        """Agregar herramienta personalizada"""
        self.tools[tool.name] = tool
    
    def remove_tool(self, tool_name: str) -> bool:
        """Eliminar herramienta"""
        if tool_name in self.tools:
            del self.tools[tool_name]
            return True
        return False
    
    def get_all_tools(self) -> Dict[str, AgentTool]:
        """Obtener todas las herramientas"""
        return self.tools
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Obtener información detallada de una herramienta"""
        tool = self.get_tool(tool_name)
        if tool:
            return tool.to_dict()
        return None 