"""
TauseStack Domain Manager

Manages domain routing and tenant resolution for multi-tenant applications.
Supports subdomain-based tenancy and custom domains.

Architecture for tause.pro:
- app.tause.pro (default/demo tenant)
- {tenant}.tause.pro (tenant-specific subdomains)
- custom.domain.com (custom domains pointing to specific tenants)
"""

import re
import os
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

class DomainManager:
    """
    Manages domain-based tenant resolution and routing.
    
    Supports multiple domain patterns:
    1. Subdomain-based: {tenant}.tause.pro
    2. Custom domains: client.com -> tenant_id
    3. Path-based: tause.pro/{tenant} (fallback)
    """
    
    def __init__(self):
        self.base_domain = os.getenv("TAUSESTACK_BASE_DOMAIN", "tause.pro")
        self.default_tenant = os.getenv("TAUSESTACK_DEFAULT_TENANT_ID", "default")
        
        # Domain patterns
        self.subdomain_pattern = rf"^([a-z0-9-]+)\.{re.escape(self.base_domain)}$"
        
        # Custom domain mappings (tenant_id -> custom_domain)
        self._custom_domains: Dict[str, str] = {}
        # Reverse mapping (custom_domain -> tenant_id)
        self._domain_to_tenant: Dict[str, str] = {}
        
        # Reserved subdomains that cannot be used as tenant IDs
        self._reserved_subdomains = {
            "www", "api", "admin", "app", "docs", "blog", "support", 
            "mail", "ftp", "cdn", "static", "assets", "dev", "staging",
            "test", "demo", "sandbox", "portal", "dashboard", "status",
            "help", "console", "manage"
        }
        
        # System subdomains and their service mappings
        self._system_subdomains = {
            "api": "api_service",      # API REST endpoints
            "admin": "admin_panel",    # Panel de administración
            "docs": "documentation",   # Documentación
            "app": "default",          # Aplicación principal (tenant por defecto)
            "www": "landing",          # Landing page redirect
            "cdn": "static_assets",    # CDN para assets estáticos
            "status": "status_page",   # Página de estado del sistema
            "blog": "blog_content",    # Blog/contenido
            "help": "help_center"      # Centro de ayuda
        }
        
        logger.info(f"DomainManager initialized for base domain: {self.base_domain}")
    
    def resolve_tenant_from_host(self, host: str) -> Optional[str]:
        """
        Resolve tenant ID from HTTP Host header.
        
        Args:
            host: HTTP Host header value (e.g., "client1.tause.pro", "app.client.com")
            
        Returns:
            Tenant ID or None if cannot resolve
        """
        if not host:
            return self.default_tenant
        
        # Remove port if present
        host = host.split(':')[0].lower()
        
        # Check custom domain mappings first
        if host in self._domain_to_tenant:
            tenant_id = self._domain_to_tenant[host]
            logger.debug(f"Resolved custom domain {host} to tenant: {tenant_id}")
            return tenant_id
        
        # Check subdomain pattern
        match = re.match(self.subdomain_pattern, host)
        if match:
            subdomain = match.group(1)
            
            # Check if it's a system subdomain first
            if subdomain in self._system_subdomains:
                service_tenant = self._system_subdomains[subdomain]
                logger.debug(f"System subdomain {subdomain} resolved to service: {service_tenant}")
                return service_tenant
            
            # Check if subdomain is reserved (but not system)
            if subdomain in self._reserved_subdomains:
                logger.warning(f"Reserved subdomain {subdomain} cannot be used as tenant")
                return self.default_tenant
            
            # This is a custom tenant subdomain
            logger.debug(f"Resolved subdomain {subdomain} to tenant: {subdomain}")
            return subdomain
        
        # Check if it's the base domain
        if host == self.base_domain:
            logger.debug(f"Base domain {host} resolved to landing page")
            return "landing"
        elif host == f"www.{self.base_domain}":
            logger.debug(f"WWW domain {host} resolved to landing page")
            return "landing"
        
        # Fallback to default tenant for unrecognized domains
        logger.warning(f"Unrecognized host {host}, falling back to default tenant")
        return self.default_tenant
    
    def resolve_tenant_from_url(self, url: str) -> Optional[str]:
        """
        Resolve tenant ID from full URL.
        
        Args:
            url: Full URL (e.g., "https://client1.tause.pro/api/users")
            
        Returns:
            Tenant ID or None if cannot resolve
        """
        try:
            parsed = urlparse(url)
            return self.resolve_tenant_from_host(parsed.netloc)
        except Exception as e:
            logger.error(f"Error parsing URL {url}: {e}")
            return self.default_tenant
    
    def register_custom_domain(self, tenant_id: str, custom_domain: str) -> bool:
        """
        Register a custom domain for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            custom_domain: Custom domain (e.g., "app.client.com")
            
        Returns:
            True if registration successful, False otherwise
        """
        try:
            # Validate domain format
            if not self._is_valid_domain(custom_domain):
                logger.error(f"Invalid domain format: {custom_domain}")
                return False
            
            # Check if domain is already registered
            if custom_domain in self._domain_to_tenant:
                existing_tenant = self._domain_to_tenant[custom_domain]
                if existing_tenant != tenant_id:
                    logger.error(f"Domain {custom_domain} already registered to tenant {existing_tenant}")
                    return False
            
            # Register domain
            self._custom_domains[tenant_id] = custom_domain
            self._domain_to_tenant[custom_domain] = tenant_id
            
            logger.info(f"Registered custom domain {custom_domain} for tenant {tenant_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error registering custom domain {custom_domain} for tenant {tenant_id}: {e}")
            return False
    
    def unregister_custom_domain(self, tenant_id: str) -> bool:
        """
        Unregister custom domain for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            True if unregistration successful, False otherwise
        """
        try:
            if tenant_id in self._custom_domains:
                custom_domain = self._custom_domains[tenant_id]
                del self._custom_domains[tenant_id]
                del self._domain_to_tenant[custom_domain]
                logger.info(f"Unregistered custom domain {custom_domain} for tenant {tenant_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error unregistering custom domain for tenant {tenant_id}: {e}")
            return False
    
    def get_tenant_url(self, tenant_id: str, path: str = "", https: bool = True) -> str:
        """
        Generate URL for a specific tenant.
        
        Args:
            tenant_id: Tenant identifier
            path: URL path (optional)
            https: Use HTTPS protocol
            
        Returns:
            Full URL for the tenant
        """
        protocol = "https" if https else "http"
        
        # Use custom domain if available
        if tenant_id in self._custom_domains:
            domain = self._custom_domains[tenant_id]
        elif tenant_id == self.default_tenant:
            domain = f"app.{self.base_domain}"
        else:
            domain = f"{tenant_id}.{self.base_domain}"
        
        path = path.lstrip('/')
        if path:
            return f"{protocol}://{domain}/{path}"
        else:
            return f"{protocol}://{domain}"
    
    def get_available_subdomain(self, preferred_name: str) -> Optional[str]:
        """
        Get an available subdomain based on preferred name.
        
        Args:
            preferred_name: Preferred subdomain name
            
        Returns:
            Available subdomain or None if cannot generate
        """
        # Sanitize preferred name
        sanitized = re.sub(r'[^a-z0-9-]', '', preferred_name.lower())
        sanitized = sanitized.strip('-')
        
        if not sanitized:
            return None
        
        # Check if preferred name is available
        if (sanitized not in self._reserved_subdomains and 
            sanitized not in self._get_existing_subdomains()):
            return sanitized
        
        # Try with numbers
        for i in range(1, 100):
            candidate = f"{sanitized}{i}"
            if (candidate not in self._reserved_subdomains and 
                candidate not in self._get_existing_subdomains()):
                return candidate
        
        return None
    
    def validate_subdomain(self, subdomain: str) -> tuple[bool, str]:
        """
        Validate if a subdomain can be used for a tenant.
        
        Args:
            subdomain: Proposed subdomain
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not subdomain:
            return False, "Subdomain cannot be empty"
        
        # Check format
        if not re.match(r'^[a-z0-9-]+$', subdomain):
            return False, "Subdomain can only contain lowercase letters, numbers, and hyphens"
        
        if subdomain.startswith('-') or subdomain.endswith('-'):
            return False, "Subdomain cannot start or end with a hyphen"
        
        if len(subdomain) < 2:
            return False, "Subdomain must be at least 2 characters long"
        
        if len(subdomain) > 63:
            return False, "Subdomain cannot be longer than 63 characters"
        
        # Check if reserved
        if subdomain in self._reserved_subdomains:
            return False, f"Subdomain '{subdomain}' is reserved"
        
        # Check if already taken
        if subdomain in self._get_existing_subdomains():
            return False, f"Subdomain '{subdomain}' is already taken"
        
        return True, ""
    
    def list_tenant_domains(self) -> Dict[str, Dict[str, str]]:
        """
        List all tenant domains and their configurations.
        
        Returns:
            Dictionary mapping tenant_id to domain configuration
        """
        result = {}
        
        # Add custom domains
        for tenant_id, custom_domain in self._custom_domains.items():
            result[tenant_id] = {
                "type": "custom",
                "domain": custom_domain,
                "url": f"https://{custom_domain}"
            }
        
        # Add default tenant
        if self.default_tenant not in result:
            result[self.default_tenant] = {
                "type": "subdomain",
                "domain": f"app.{self.base_domain}",
                "url": f"https://app.{self.base_domain}"
            }
        
        return result
    
    def _is_valid_domain(self, domain: str) -> bool:
        """Validate domain format."""
        domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
        return bool(re.match(domain_pattern, domain)) and len(domain) <= 253
    
    def _get_existing_subdomains(self) -> set:
        """Get set of existing subdomains (would query database in real implementation)."""
        # This would typically query the database for existing tenants
        # For now, return empty set as placeholder
        return set()

# Global domain manager instance
domain_manager = DomainManager()

# Convenience functions
def resolve_tenant_from_host(host: str) -> Optional[str]:
    """Resolve tenant ID from HTTP Host header."""
    return domain_manager.resolve_tenant_from_host(host)

def resolve_tenant_from_url(url: str) -> Optional[str]:
    """Resolve tenant ID from full URL."""
    return domain_manager.resolve_tenant_from_url(url)

def get_tenant_url(tenant_id: str, path: str = "", https: bool = True) -> str:
    """Generate URL for a specific tenant."""
    return domain_manager.get_tenant_url(tenant_id, path, https)

__all__ = [
    "DomainManager",
    "domain_manager",
    "resolve_tenant_from_host",
    "resolve_tenant_from_url", 
    "get_tenant_url"
] 