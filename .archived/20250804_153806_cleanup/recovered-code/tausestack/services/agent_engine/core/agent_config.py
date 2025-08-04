"""
Agent Config - Configuraciones de agentes por tenant
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from .agent_role import AgentRole, AgentType


@dataclass
class AgentConfig:
    """
    Configuración de un agente específico para un tenant
    """
    agent_id: str
    tenant_id: str
    name: str
    role: AgentRole
    enabled: bool = True
    max_concurrent_tasks: int = 5
    priority: int = 1  # 1 = alta, 5 = baja
    retry_attempts: int = 3
    timeout_seconds: int = 300
    custom_instructions: str = ""
    allowed_tools: List[str] = field(default_factory=list)
    restricted_tools: List[str] = field(default_factory=list)
    api_preferences: Dict[str, Any] = field(default_factory=dict)
    memory_config: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Inicialización después de crear el objeto"""
        if not self.allowed_tools:
            self.allowed_tools = self.role.tools.copy()
        
        if not self.api_preferences:
            self.api_preferences = {
                'model': self.role.model_preference,
                'temperature': self.role.temperature,
                'max_tokens': self.role.max_tokens
            }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario para serialización"""
        return {
            'agent_id': self.agent_id,
            'tenant_id': self.tenant_id,
            'name': self.name,
            'role': self.role.to_dict(),
            'enabled': self.enabled,
            'max_concurrent_tasks': self.max_concurrent_tasks,
            'priority': self.priority,
            'retry_attempts': self.retry_attempts,
            'timeout_seconds': self.timeout_seconds,
            'custom_instructions': self.custom_instructions,
            'allowed_tools': self.allowed_tools,
            'restricted_tools': self.restricted_tools,
            'api_preferences': self.api_preferences,
            'memory_config': self.memory_config,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentConfig':
        """Crear desde diccionario"""
        return cls(
            agent_id=data['agent_id'],
            tenant_id=data['tenant_id'],
            name=data['name'],
            role=AgentRole.from_dict(data['role']),
            enabled=data.get('enabled', True),
            max_concurrent_tasks=data.get('max_concurrent_tasks', 5),
            priority=data.get('priority', 1),
            retry_attempts=data.get('retry_attempts', 3),
            timeout_seconds=data.get('timeout_seconds', 300),
            custom_instructions=data.get('custom_instructions', ''),
            allowed_tools=data.get('allowed_tools', []),
            restricted_tools=data.get('restricted_tools', []),
            api_preferences=data.get('api_preferences', {}),
            memory_config=data.get('memory_config', {}),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            metadata=data.get('metadata', {})
        )
    
    def update_config(self, **kwargs):
        """Actualizar configuración"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()
    
    def is_tool_allowed(self, tool_name: str) -> bool:
        """Verificar si una herramienta está permitida"""
        if tool_name in self.restricted_tools:
            return False
        return tool_name in self.allowed_tools
    
    def get_effective_instructions(self) -> str:
        """Obtener instrucciones efectivas (rol + personalizadas)"""
        instructions = f"Role: {self.role.name}\n"
        instructions += f"Goal: {self.role.goal}\n"
        instructions += f"Backstory: {self.role.backstory}\n"
        
        if self.custom_instructions:
            instructions += f"\nCustom Instructions: {self.custom_instructions}\n"
        
        return instructions
    
    def get_model_config(self) -> Dict[str, Any]:
        """Obtener configuración del modelo"""
        return {
            'model': self.api_preferences.get('model', self.role.model_preference),
            'temperature': self.api_preferences.get('temperature', self.role.temperature),
            'max_tokens': self.api_preferences.get('max_tokens', self.role.max_tokens)
        }


class AgentConfigManager:
    """Gestor de configuraciones de agentes"""
    
    def __init__(self, storage_path: str = ".tausestack_storage/agents"):
        self.storage_path = storage_path
        self.configs: Dict[str, AgentConfig] = {}
    
    def create_config(
        self, 
        agent_id: str, 
        tenant_id: str, 
        name: str, 
        role: AgentRole,
        **kwargs
    ) -> AgentConfig:
        """Crear nueva configuración de agente"""
        config = AgentConfig(
            agent_id=agent_id,
            tenant_id=tenant_id,
            name=name,
            role=role,
            **kwargs
        )
        
        self.configs[agent_id] = config
        return config
    
    def get_config(self, agent_id: str) -> Optional[AgentConfig]:
        """Obtener configuración de agente"""
        return self.configs.get(agent_id)
    
    def get_configs_by_tenant(self, tenant_id: str) -> List[AgentConfig]:
        """Obtener configuraciones por tenant"""
        return [config for config in self.configs.values() if config.tenant_id == tenant_id]
    
    def update_config(self, agent_id: str, **kwargs) -> bool:
        """Actualizar configuración"""
        config = self.get_config(agent_id)
        if config:
            config.update_config(**kwargs)
            return True
        return False
    
    def delete_config(self, agent_id: str) -> bool:
        """Eliminar configuración"""
        if agent_id in self.configs:
            del self.configs[agent_id]
            return True
        return False 