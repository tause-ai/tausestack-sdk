"""
Domain configuration for TauseStack and TausePro
Manages domain routing and configuration for multi-domain setup
"""

import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class DomainType(Enum):
    """Tipos de dominio soportados"""
    TAUSESTACK = "tausestack"
    TAUSEPRO = "tausepro"
    LANDING = "landing"
    APP = "app"
    API = "api"

@dataclass
class DomainConfig:
    """Configuración de dominio"""
    domain: str
    domain_type: DomainType
    tenant_id: str
    ssl_enabled: bool = True
    cdn_enabled: bool = True
    description: str = ""

class DomainConfiguration:
    """Configuración central de dominios"""
    
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "production")
        self.base_domains = self._get_base_domains()
        self.domain_configs = self._initialize_domain_configs()
    
    def _get_base_domains(self) -> Dict[str, str]:
        """Obtener dominios base según el entorno"""
        if self.environment == "production":
            return {
                "tausestack": os.getenv("TAUSESTACK_BASE_DOMAIN", "tausestack.dev"),
                "tausepro": os.getenv("TAUSEPRO_BASE_DOMAIN", "tause.pro")
            }
        else:
            return {
                "tausestack": os.getenv("TAUSESTACK_BASE_DOMAIN", "tausestack.local"),
                "tausepro": os.getenv("TAUSEPRO_BASE_DOMAIN", "tause.local")
            }
    
    def _initialize_domain_configs(self) -> Dict[str, DomainConfig]:
        """Inicializar configuraciones de dominio"""
        configs = {}
        
        # TauseStack domains
        tausestack_base = self.base_domains["tausestack"]
        configs[tausestack_base] = DomainConfig(
            domain=tausestack_base,
            domain_type=DomainType.LANDING,
            tenant_id="landing",
            description="TauseStack Landing Page"
        )
        
        configs[f"app.{tausestack_base}"] = DomainConfig(
            domain=f"app.{tausestack_base}",
            domain_type=DomainType.APP,
            tenant_id="default",
            description="TauseStack Main Application"
        )
        
        configs[f"api.{tausestack_base}"] = DomainConfig(
            domain=f"api.{tausestack_base}",
            domain_type=DomainType.API,
            tenant_id="api_service",
            description="TauseStack API Service"
        )
        
        configs[f"admin.{tausestack_base}"] = DomainConfig(
            domain=f"admin.{tausestack_base}",
            domain_type=DomainType.APP,
            tenant_id="admin_panel",
            description="TauseStack Admin Panel"
        )
        
        # TausePro domains
        tausepro_base = self.base_domains["tausepro"]
        configs[tausepro_base] = DomainConfig(
            domain=tausepro_base,
            domain_type=DomainType.LANDING,
            tenant_id="landing",
            description="TausePro Landing Page"
        )
        
        configs[f"app.{tausepro_base}"] = DomainConfig(
            domain=f"app.{tausepro_base}",
            domain_type=DomainType.APP,
            tenant_id="tausepro_app",
            description="TausePro Marketing Application"
        )
        
        configs[f"api.{tausepro_base}"] = DomainConfig(
            domain=f"api.{tausepro_base}",
            domain_type=DomainType.API,
            tenant_id="tausepro_api",
            description="TausePro API Proxy"
        )
        
        return configs
    
    def get_domain_config(self, domain: str) -> Optional[DomainConfig]:
        """Obtener configuración de dominio"""
        return self.domain_configs.get(domain)
    
    def get_tenant_domain(self, tenant_id: str) -> Optional[str]:
        """Obtener dominio para un tenant"""
        for domain, config in self.domain_configs.items():
            if config.tenant_id == tenant_id:
                return domain
        return None
    
    def get_domains_by_type(self, domain_type: DomainType) -> List[DomainConfig]:
        """Obtener dominios por tipo"""
        return [config for config in self.domain_configs.values() 
                if config.domain_type == domain_type]
    
    def get_tausestack_domains(self) -> List[DomainConfig]:
        """Obtener dominios de TauseStack"""
        tausestack_base = self.base_domains["tausestack"]
        return [config for config in self.domain_configs.values() 
                if config.domain.endswith(tausestack_base)]
    
    def get_tausepro_domains(self) -> List[DomainConfig]:
        """Obtener dominios de TausePro"""
        tausepro_base = self.base_domains["tausepro"]
        return [config for config in self.domain_configs.values() 
                if config.domain.endswith(tausepro_base)]
    
    def is_tausepro_domain(self, domain: str) -> bool:
        """Verificar si es un dominio de TausePro"""
        tausepro_base = self.base_domains["tausepro"]
        return domain.endswith(tausepro_base) or domain == tausepro_base
    
    def is_tausestack_domain(self, domain: str) -> bool:
        """Verificar si es un dominio de TauseStack"""
        tausestack_base = self.base_domains["tausestack"]
        return domain.endswith(tausestack_base) or domain == tausestack_base
    
    def get_api_endpoint(self, domain: str) -> str:
        """Obtener endpoint API para un dominio"""
        if self.is_tausepro_domain(domain):
            # TausePro siempre usa TauseStack API
            return f"https://api.{self.base_domains['tausestack']}"
        else:
            # TauseStack usa su propia API
            return f"https://api.{self.base_domains['tausestack']}"
    
    def get_cors_origins(self) -> List[str]:
        """Obtener lista de orígenes CORS permitidos"""
        origins = []
        
        for config in self.domain_configs.values():
            origins.append(f"https://{config.domain}")
            origins.append(f"https://www.{config.domain}")
        
        # Añadir localhost para desarrollo
        if self.environment != "production":
            origins.extend([
                "http://localhost:3000",
                "http://localhost:3001",
                "http://localhost:8000",
                "http://localhost:5173"
            ])
        
        return list(set(origins))
    
    def get_allowed_hosts(self) -> List[str]:
        """Obtener lista de hosts permitidos"""
        hosts = []
        
        for config in self.domain_configs.values():
            hosts.append(config.domain)
            hosts.append(f"www.{config.domain}")
        
        # Añadir localhost para desarrollo
        if self.environment != "production":
            hosts.extend([
                "localhost",
                "127.0.0.1",
                "0.0.0.0"
            ])
        
        return list(set(hosts))
    
    def to_dict(self) -> Dict:
        """Convertir configuración a diccionario"""
        return {
            "environment": self.environment,
            "base_domains": self.base_domains,
            "domain_configs": {
                domain: {
                    "domain": config.domain,
                    "domain_type": config.domain_type.value,
                    "tenant_id": config.tenant_id,
                    "ssl_enabled": config.ssl_enabled,
                    "cdn_enabled": config.cdn_enabled,
                    "description": config.description
                }
                for domain, config in self.domain_configs.items()
            }
        }

# Instancia global
domain_configuration = DomainConfiguration()

# Funciones de conveniencia
def get_domain_config(domain: str) -> Optional[DomainConfig]:
    """Obtener configuración de dominio"""
    return domain_configuration.get_domain_config(domain)

def get_tenant_domain(tenant_id: str) -> Optional[str]:
    """Obtener dominio para un tenant"""
    return domain_configuration.get_tenant_domain(tenant_id)

def is_tausepro_domain(domain: str) -> bool:
    """Verificar si es un dominio de TausePro"""
    return domain_configuration.is_tausepro_domain(domain)

def is_tausestack_domain(domain: str) -> bool:
    """Verificar si es un dominio de TauseStack"""
    return domain_configuration.is_tausestack_domain(domain)

def get_api_endpoint(domain: str) -> str:
    """Obtener endpoint API para un dominio"""
    return domain_configuration.get_api_endpoint(domain)

def get_cors_origins() -> List[str]:
    """Obtener lista de orígenes CORS permitidos"""
    return domain_configuration.get_cors_origins()

def get_allowed_hosts() -> List[str]:
    """Obtener lista de hosts permitidos"""
    return domain_configuration.get_allowed_hosts()

__all__ = [
    "DomainType",
    "DomainConfig", 
    "DomainConfiguration",
    "domain_configuration",
    "get_domain_config",
    "get_tenant_domain",
    "is_tausepro_domain",
    "is_tausestack_domain",
    "get_api_endpoint",
    "get_cors_origins",
    "get_allowed_hosts"
] 