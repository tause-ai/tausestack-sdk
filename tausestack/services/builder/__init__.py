"""
TauseStack Builder Service - Visual App Builder

Siguiendo el Service Pattern de TauseStack:
- Multi-tenant architecture
- Integration with existing TauseStack services
- MCP tool pattern for external access
"""

from .core.builder_service import BuilderService
from .api.builder_api import include_builder_api
# from .tools.builder_tools import BuilderMCPServer

__version__ = "1.0.0"
__all__ = ["BuilderService", "include_builder_api"] 