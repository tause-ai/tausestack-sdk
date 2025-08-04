"""
TauseStack Tenancy Module

Provides multi-tenant capabilities while maintaining backward compatibility
with single-tenant (monolithic) applications.

Usage:
    # Monolithic mode (default, backward compatible)
    from tausestack import sdk
    sdk.storage.json.put("key", data)  # Uses default tenant
    
    # Multi-tenant mode
    sdk.tenancy.configure_tenant("client_123", config)
    sdk.storage.json.put("key", data, tenant_id="client_123")
"""

import os
from typing import Optional, Dict, Any, Union
from contextlib import contextmanager
import threading

# Thread-local storage for current tenant context
_tenant_context = threading.local()

class TenancyManager:
    """
    Manages multi-tenant configuration and context.
    
    Provides backward compatibility by defaulting to 'default' tenant
    when no tenant is specified.
    """
    
    def __init__(self):
        self._tenants: Dict[str, Dict[str, Any]] = {}
        self._multi_tenant_enabled = os.getenv("TAUSESTACK_MULTI_TENANT_MODE", "false").lower() == "true"
        self._default_tenant_id = os.getenv("TAUSESTACK_DEFAULT_TENANT_ID", "default")
        
        # Initialize default tenant for backward compatibility
        self._tenants[self._default_tenant_id] = {
            "name": "Default Tenant",
            "database_url": None,  # Will use existing SDK defaults
            "storage_config": {},
            "auth_config": {},
            "cache_config": {},
            "notify_config": {},
        }
    
    @property
    def is_multi_tenant_enabled(self) -> bool:
        """Check if multi-tenant mode is enabled."""
        return self._multi_tenant_enabled
    
    @property
    def default_tenant_id(self) -> str:
        """Get the default tenant ID for backward compatibility."""
        return self._default_tenant_id
    
    def configure_tenant(self, tenant_id: str, config: Dict[str, Any]) -> None:
        """
        Configure a tenant with specific settings.
        
        Args:
            tenant_id: Unique identifier for the tenant
            config: Tenant configuration including database, storage, etc.
        """
        self._tenants[tenant_id] = {
            "name": config.get("name", f"Tenant {tenant_id}"),
            "database_url": config.get("database_url"),
            "storage_config": config.get("storage", {}),
            "auth_config": config.get("auth", {}),
            "cache_config": config.get("cache", {}),
            "notify_config": config.get("notify", {}),
            "custom_domain": config.get("custom_domain"),
            "subdomain": config.get("subdomain"),
            **config
        }
    
    def get_tenant_config(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get configuration for a specific tenant.
        
        Args:
            tenant_id: Tenant ID, defaults to current context or default tenant
            
        Returns:
            Tenant configuration dictionary
        """
        effective_tenant_id = tenant_id or self.get_current_tenant_id()
        return self._tenants.get(effective_tenant_id, self._tenants[self._default_tenant_id])
    
    def get_current_tenant_id(self) -> str:
        """
        Get the current tenant ID from thread-local context.
        
        Returns:
            Current tenant ID or default tenant ID for backward compatibility
        """
        return getattr(_tenant_context, 'tenant_id', self._default_tenant_id)
    
    def set_current_tenant(self, tenant_id: str) -> None:
        """Set the current tenant in thread-local context."""
        _tenant_context.tenant_id = tenant_id
    
    @contextmanager
    def tenant_context(self, tenant_id: str):
        """
        Context manager for executing code within a specific tenant context.
        
        Usage:
            with tenancy.tenant_context("client_123"):
                # All SDK calls will use client_123 tenant
                sdk.storage.json.put("key", data)
        """
        previous_tenant = getattr(_tenant_context, 'tenant_id', None)
        _tenant_context.tenant_id = tenant_id
        try:
            yield
        finally:
            if previous_tenant:
                _tenant_context.tenant_id = previous_tenant
            else:
                delattr(_tenant_context, 'tenant_id')
    
    def list_tenants(self) -> Dict[str, Dict[str, Any]]:
        """List all configured tenants."""
        return self._tenants.copy()
    
    def enable_multi_tenant_mode(self) -> None:
        """Enable multi-tenant mode programmatically."""
        self._multi_tenant_enabled = True
    
    def disable_multi_tenant_mode(self) -> None:
        """Disable multi-tenant mode (fallback to monolithic)."""
        self._multi_tenant_enabled = False

# Global tenancy manager instance
tenancy = TenancyManager()

# Convenience functions for backward compatibility
def get_current_tenant_id() -> str:
    """Get current tenant ID (backward compatible)."""
    return tenancy.get_current_tenant_id()

def get_tenant_config(tenant_id: Optional[str] = None) -> Dict[str, Any]:
    """Get tenant configuration (backward compatible)."""
    return tenancy.get_tenant_config(tenant_id)

def is_multi_tenant_enabled() -> bool:
    """Check if multi-tenant mode is enabled."""
    return tenancy.is_multi_tenant_enabled

__all__ = [
    "TenancyManager",
    "tenancy",
    "get_current_tenant_id", 
    "get_tenant_config",
    "is_multi_tenant_enabled"
] 