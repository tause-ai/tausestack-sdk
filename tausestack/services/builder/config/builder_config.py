"""
TauseStack Builder Configuration
Configuración centralizada para el Builder siguiendo el patrón de TauseStack
"""

import os
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class BuilderConfig:
    """
    Configuración del Builder siguiendo el patrón de TauseStack
    """
    
    # Configuración del servicio
    SERVICE_NAME: str = "tausestack-builder"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_PORT: int = 8006
    
    # Configuración de templates
    TEMPLATES_PATH: str = "templates/builder"
    DEFAULT_TEMPLATES: List[str] = None
    
    # Configuración de AI
    AI_ENABLED: bool = True
    AI_MODEL: str = "gpt-4"
    AI_MAX_TOKENS: int = 4000
    
    # Configuración de despliegue
    DEPLOY_ENABLED: bool = True
    DEPLOY_DOMAINS: List[str] = None
    DEPLOY_TIMEOUT: int = 300
    
    # Configuración de storage
    STORAGE_BACKEND: str = "tausestack"
    STORAGE_BUCKET: str = "builder-projects"
    
    # Configuración de notificaciones
    NOTIFICATIONS_ENABLED: bool = True
    WEBHOOK_URL: Optional[str] = None
    
    # Configuración de rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600
    
    # Configuración de logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    def __post_init__(self):
        """Inicializar valores por defecto"""
        if self.DEFAULT_TEMPLATES is None:
            self.DEFAULT_TEMPLATES = [
                "web-basic",
                "api-rest", 
                "agent-ai",
                "ecommerce-basic",
                "dashboard-analytics"
            ]
        
        if self.DEPLOY_DOMAINS is None:
            self.DEPLOY_DOMAINS = [
                "tausestack.dev",
                "tause.pro",
                "app.tause.pro"
            ]


# Configuración global
builder_config = BuilderConfig()

# Configuración específica por entorno
ENVIRONMENT_CONFIGS = {
    "development": {
        "AI_MODEL": "gpt-3.5-turbo",
        "DEPLOY_ENABLED": False,
        "RATE_LIMIT_ENABLED": False,
        "LOG_LEVEL": "DEBUG"
    },
    "staging": {
        "AI_MODEL": "gpt-4",
        "DEPLOY_ENABLED": True,
        "RATE_LIMIT_ENABLED": True,
        "LOG_LEVEL": "INFO"
    },
    "production": {
        "AI_MODEL": "gpt-4",
        "DEPLOY_ENABLED": True,
        "RATE_LIMIT_ENABLED": True,
        "LOG_LEVEL": "WARNING"
    }
}

def get_config() -> BuilderConfig:
    """
    Obtener configuración del Builder según el entorno
    """
    env = os.getenv("ENVIRONMENT", "development")
    config = builder_config
    
    # Aplicar configuración específica del entorno
    if env in ENVIRONMENT_CONFIGS:
        env_config = ENVIRONMENT_CONFIGS[env]
        for key, value in env_config.items():
            if hasattr(config, key):
                setattr(config, key, value)
    
    return config


# Configuración de templates por defecto
DEFAULT_TEMPLATES_CONFIG = {
    "web-basic": {
        "name": "Web App Básica",
        "description": "Aplicación web con React + FastAPI",
        "type": "web",
        "components": [
            {
                "type": "frontend",
                "name": "React App",
                "config": {
                    "framework": "react",
                    "version": "18.x",
                    "ui_library": "shadcn/ui"
                }
            },
            {
                "type": "backend",
                "name": "FastAPI Server",
                "config": {
                    "framework": "fastapi",
                    "version": "0.104.x",
                    "auth": True
                }
            },
            {
                "type": "database",
                "name": "PostgreSQL",
                "config": {
                    "type": "postgresql",
                    "version": "15.x"
                }
            }
        ]
    },
    "api-rest": {
        "name": "API REST",
        "description": "API REST con FastAPI y documentación",
        "type": "api",
        "components": [
            {
                "type": "backend",
                "name": "FastAPI Server",
                "config": {
                    "framework": "fastapi",
                    "version": "0.104.x",
                    "docs": True,
                    "auth": True
                }
            },
            {
                "type": "database",
                "name": "PostgreSQL",
                "config": {
                    "type": "postgresql",
                    "version": "15.x"
                }
            }
        ]
    },
    "agent-ai": {
        "name": "Agente IA",
        "description": "Agente IA con MCP y herramientas",
        "type": "agent",
        "components": [
            {
                "type": "agent",
                "name": "AI Agent",
                "config": {
                    "model": "gpt-4",
                    "tools": ["web_search", "file_operations", "database"],
                    "mcp_enabled": True
                }
            },
            {
                "type": "tools",
                "name": "MCP Tools",
                "config": {
                    "tools": ["web", "filesystem", "database"]
                }
            },
            {
                "type": "memory",
                "name": "Vector Memory",
                "config": {
                    "type": "vectordb",
                    "dimensions": 1536
                }
            }
        ]
    },
    "ecommerce-basic": {
        "name": "E-commerce Básico",
        "description": "Tienda online con carrito y pagos",
        "type": "ecommerce",
        "components": [
            {
                "type": "frontend",
                "name": "Next.js Store",
                "config": {
                    "framework": "nextjs",
                    "version": "14.x",
                    "ui_library": "shadcn/ui"
                }
            },
            {
                "type": "backend",
                "name": "FastAPI Server",
                "config": {
                    "framework": "fastapi",
                    "version": "0.104.x",
                    "auth": True
                }
            },
            {
                "type": "database",
                "name": "PostgreSQL",
                "config": {
                    "type": "postgresql",
                    "version": "15.x"
                }
            },
            {
                "type": "payments",
                "name": "Stripe Integration",
                "config": {
                    "provider": "stripe",
                    "webhook_enabled": True
                }
            }
        ]
    },
    "dashboard-analytics": {
        "name": "Dashboard Analytics",
        "description": "Dashboard con métricas y gráficos",
        "type": "dashboard",
        "components": [
            {
                "type": "frontend",
                "name": "Dashboard UI",
                "config": {
                    "framework": "react",
                    "version": "18.x",
                    "charts": "recharts"
                }
            },
            {
                "type": "backend",
                "name": "Analytics API",
                "config": {
                    "framework": "fastapi",
                    "version": "0.104.x",
                    "auth": True
                }
            },
            {
                "type": "analytics",
                "name": "Analytics Engine",
                "config": {
                    "type": "custom",
                    "real_time": True
                }
            }
        ]
    }
}

def get_template_config(template_id: str) -> Optional[Dict]:
    """
    Obtener configuración de un template específico
    """
    return DEFAULT_TEMPLATES_CONFIG.get(template_id)


def list_available_templates() -> List[Dict]:
    """
    Listar todos los templates disponibles
    """
    return [
        {
            "id": template_id,
            "name": template_data["name"],
            "description": template_data["description"],
            "type": template_data["type"],
            "components": [comp["name"] for comp in template_data["components"]]
        }
        for template_id, template_data in DEFAULT_TEMPLATES_CONFIG.items()
    ] 