"""
Agent Role - Definición de roles y responsabilidades de agentes
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class AgentType(str, Enum):
    """Tipos de agentes disponibles"""
    RESEARCH = "research"
    WRITER = "writer"
    ANALYST = "analyst"
    CUSTOMER_SUPPORT = "customer_support"
    SALES = "sales"
    ECOMMERCE = "ecommerce"
    CUSTOM = "custom"


@dataclass
class AgentRole:
    """
    Definición de un rol de agente con sus capacidades y configuraciones
    """
    name: str
    type: AgentType
    goal: str
    backstory: str
    tools: List[str]
    max_tokens: int = 4000
    temperature: float = 0.7
    model_preference: str = "gpt-4"
    config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.config is None:
            self.config = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario para serialización"""
        return {
            'name': self.name,
            'type': self.type.value,
            'goal': self.goal,
            'backstory': self.backstory,
            'tools': self.tools,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'model_preference': self.model_preference,
            'config': self.config
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentRole':
        """Crear desde diccionario"""
        return cls(
            name=data['name'],
            type=AgentType(data['type']),
            goal=data['goal'],
            backstory=data['backstory'],
            tools=data['tools'],
            max_tokens=data.get('max_tokens', 4000),
            temperature=data.get('temperature', 0.7),
            model_preference=data.get('model_preference', 'gpt-4'),
            config=data.get('config', {})
        )


# Roles predefinidos
class PresetRoles:
    """Roles predefinidos comunes"""
    
    @staticmethod
    def research_agent() -> AgentRole:
        """Agente de investigación"""
        return AgentRole(
            name="Research Agent",
            type=AgentType.RESEARCH,
            goal="Realizar investigación exhaustiva sobre temas específicos",
            backstory="Soy un experto investigador con acceso a múltiples fuentes de información. Mi especialidad es encontrar datos relevantes y verificar información.",
            tools=["web_search", "data_analysis", "summarization"],
            temperature=0.3,
            model_preference="gpt-4"
        )
    
    @staticmethod
    def writer_agent() -> AgentRole:
        """Agente de escritura"""
        return AgentRole(
            name="Writer Agent", 
            type=AgentType.WRITER,
            goal="Crear contenido escrito de alta calidad",
            backstory="Soy un escritor experto capaz de crear contenido en múltiples formatos y estilos. Puedo adaptar mi escritura para diferentes audiencias.",
            tools=["content_generation", "grammar_check", "style_adaptation"],
            temperature=0.7,
            model_preference="claude-3-sonnet-20240229"
        )
    
    @staticmethod
    def customer_support_agent() -> AgentRole:
        """Agente de soporte al cliente"""
        return AgentRole(
            name="Customer Support Agent",
            type=AgentType.CUSTOMER_SUPPORT,
            goal="Brindar soporte excepcional a clientes",
            backstory="Soy un especialista en atención al cliente con amplia experiencia resolviendo problemas. Siempre mantengo un tono amigable y profesional.",
            tools=["knowledge_base", "ticket_management", "escalation"],
            temperature=0.4,
            model_preference="gpt-4"
        )
    
    @staticmethod
    def ecommerce_agent() -> AgentRole:
        """Agente especializado en ecommerce"""
        return AgentRole(
            name="Ecommerce Agent",
            type=AgentType.ECOMMERCE,
            goal="Optimizar operaciones de ecommerce y mejorar ventas",
            backstory="Soy un experto en ecommerce con conocimiento profundo de Saleor, Wompi y el mercado colombiano. Puedo ayudar con inventario, pagos y estrategias de venta.",
            tools=["saleor_integration", "wompi_payments", "inventory_management", "sales_analysis"],
            temperature=0.5,
            model_preference="gpt-4",
            config={
                "saleor_enabled": True,
                "wompi_enabled": True,
                "colombia_market": True
            }
        )
    
    @staticmethod
    def get_all_presets() -> List[AgentRole]:
        """Obtener todos los roles predefinidos"""
        return [
            PresetRoles.research_agent(),
            PresetRoles.writer_agent(),
            PresetRoles.customer_support_agent(),
            PresetRoles.ecommerce_agent()
        ] 