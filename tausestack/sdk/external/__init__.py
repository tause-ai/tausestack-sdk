# TauseStack External SDK
# For external builders like TausePro Platform

from .builder import TauseStackBuilder
from .templates import TemplateManager
from .deployment import DeploymentManager
from .auth import ExternalAuth

__all__ = [
    "TauseStackBuilder",
    "TemplateManager", 
    "DeploymentManager",
    "ExternalAuth"
]

__version__ = "0.7.0" 