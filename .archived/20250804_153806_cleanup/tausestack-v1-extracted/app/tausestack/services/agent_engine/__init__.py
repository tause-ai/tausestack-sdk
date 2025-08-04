"""
TauseStack Agent Engine - Agentes de IA multi-tenant nativos

Aprovecha la infraestructura existente de TauseStack:
- AI Services (OpenAI, Claude) 
- Storage multi-tenant
- Analytics
- Memory persistente por tenant
"""

from .core.agent_role import AgentRole
from .core.tausestack_agent import TauseStackAgent
from .core.agent_result import AgentResult
from .core.agent_config import AgentConfig

__version__ = "0.1.0"
__all__ = ["AgentRole", "TauseStackAgent", "AgentResult", "AgentConfig"] 