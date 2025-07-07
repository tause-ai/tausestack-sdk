"""
TauseStack Multi-Tenant Isolation Module

Provides comprehensive data and resource isolation for multi-tenant applications.
Ensures complete separation between tenants at all levels: database, storage, cache, and resources.

Usage:
    from tausestack.sdk.isolation import IsolationManager
    
    # Configure isolation for a tenant
    isolation.configure_tenant_isolation("client_123", {
        "database_schema": "tenant_client_123",
        "storage_prefix": "tenants/client_123/",
        "cache_prefix": "tenant:client_123:",
        "resource_limits": {"storage_gb": 10, "api_calls_per_hour": 1000}
    })
    
    # Get isolated configuration for current tenant
    config = isolation.get_current_tenant_config()
"""

from typing import Dict, Any, Optional, Union
from contextlib import contextmanager
import threading
import re
import logging

from ..tenancy import get_current_tenant_id, tenancy

logger = logging.getLogger(__name__)

class IsolationManager:
    """
    Manages complete isolation between tenants.
    
    Provides:
    - Database schema isolation
    - Storage path isolation  
    - Cache key isolation
    - Resource limits enforcement
    - Cross-tenant access prevention
    """
    
    def __init__(self):
        self._tenant_configs: Dict[str, Dict[str, Any]] = {}
        self._default_config = {
            "database_schema": "public",
            "storage_prefix": "",
            "cache_prefix": "",
            "resource_limits": {
                "storage_gb": 1,
                "api_calls_per_hour": 100,
                "database_connections": 5,
                "cache_memory_mb": 50
            },
            "isolation_level": "strict"  # strict, relaxed, shared
        }
    
    def configure_tenant_isolation(self, tenant_id: str, config: Dict[str, Any]) -> None:
        """
        Configure isolation settings for a specific tenant.
        
        Args:
            tenant_id: Unique tenant identifier
            config: Isolation configuration
        """
        # Validate tenant_id format
        if not self._is_valid_tenant_id(tenant_id):
            raise ValueError(f"Invalid tenant_id format: {tenant_id}")
        
        # Merge with defaults
        tenant_config = self._default_config.copy()
        tenant_config.update(config)
        
        # Validate configuration
        self._validate_isolation_config(tenant_config)
        
        self._tenant_configs[tenant_id] = tenant_config
        logger.info(f"Configured isolation for tenant: {tenant_id}")
    
    def get_tenant_isolation_config(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get isolation configuration for a tenant.
        
        Args:
            tenant_id: Tenant ID, defaults to current tenant
            
        Returns:
            Isolation configuration dictionary
        """
        effective_tenant_id = tenant_id or get_current_tenant_id()
        return self._tenant_configs.get(effective_tenant_id, self._default_config)
    
    def get_current_tenant_config(self) -> Dict[str, Any]:
        """Get isolation configuration for current tenant."""
        return self.get_tenant_isolation_config()
    
    def isolate_database_schema(self, tenant_id: Optional[str] = None) -> str:
        """
        Get isolated database schema name for tenant.
        
        Args:
            tenant_id: Tenant ID, defaults to current tenant
            
        Returns:
            Schema name for the tenant
        """
        config = self.get_tenant_isolation_config(tenant_id)
        return config["database_schema"]
    
    def isolate_storage_path(self, path: str, tenant_id: Optional[str] = None) -> str:
        """
        Isolate storage path for tenant.
        
        Args:
            path: Original storage path
            tenant_id: Tenant ID, defaults to current tenant
            
        Returns:
            Isolated storage path
        """
        config = self.get_tenant_isolation_config(tenant_id)
        prefix = config["storage_prefix"]
        
        if not prefix:
            return path
        
        # Ensure path doesn't start with slash
        clean_path = path.lstrip("/")
        return f"{prefix.rstrip('/')}/{clean_path}"
    
    def isolate_cache_key(self, key: str, tenant_id: Optional[str] = None) -> str:
        """
        Isolate cache key for tenant.
        
        Args:
            key: Original cache key
            tenant_id: Tenant ID, defaults to current tenant
            
        Returns:
            Isolated cache key
        """
        config = self.get_tenant_isolation_config(tenant_id)
        prefix = config["cache_prefix"]
        
        if not prefix:
            return key
        
        return f"{prefix.rstrip(':')}:{key}"
    
    def check_resource_limits(self, resource_type: str, usage: Union[int, float], 
                            tenant_id: Optional[str] = None) -> bool:
        """
        Check if tenant is within resource limits.
        
        Args:
            resource_type: Type of resource (storage_gb, api_calls_per_hour, etc.)
            usage: Current usage
            tenant_id: Tenant ID, defaults to current tenant
            
        Returns:
            True if within limits, False otherwise
        """
        config = self.get_tenant_isolation_config(tenant_id)
        limits = config["resource_limits"]
        
        limit = limits.get(resource_type)
        if limit is None:
            logger.warning(f"No limit configured for resource: {resource_type}")
            return True
        
        return usage <= limit
    
    def enforce_cross_tenant_isolation(self, source_tenant: str, target_tenant: str) -> bool:
        """
        Enforce cross-tenant isolation rules.
        
        Args:
            source_tenant: Source tenant ID
            target_tenant: Target tenant ID
            
        Returns:
            True if access is allowed, False if blocked
        """
        if source_tenant == target_tenant:
            return True
        
        # Get isolation levels
        source_config = self.get_tenant_isolation_config(source_tenant)
        target_config = self.get_tenant_isolation_config(target_tenant)
        
        source_level = source_config.get("isolation_level", "strict")
        target_level = target_config.get("isolation_level", "strict")
        
        # Strict isolation: no cross-tenant access
        if source_level == "strict" or target_level == "strict":
            logger.warning(f"Cross-tenant access blocked: {source_tenant} -> {target_tenant}")
            return False
        
        # Relaxed isolation: allow with logging
        if source_level == "relaxed" or target_level == "relaxed":
            logger.info(f"Cross-tenant access allowed (relaxed): {source_tenant} -> {target_tenant}")
            return True
        
        # Shared isolation: allow
        return True
    
    def _is_valid_tenant_id(self, tenant_id: str) -> bool:
        """Validate tenant ID format."""
        # Allow alphanumeric, hyphens, underscores, minimum 2 chars
        return bool(re.match(r'^[a-zA-Z0-9_-]{2,}$', tenant_id))
    
    def _validate_isolation_config(self, config: Dict[str, Any]) -> None:
        """Validate isolation configuration."""
        # Validate database schema
        schema = config.get("database_schema")
        if schema and not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', schema):
            raise ValueError(f"Invalid database schema name: {schema}")
        
        # Validate resource limits
        limits = config.get("resource_limits", {})
        for resource, limit in limits.items():
            if not isinstance(limit, (int, float)) or limit < 0:
                raise ValueError(f"Invalid resource limit for {resource}: {limit}")
    
    @contextmanager
    def isolation_context(self, tenant_id: str):
        """
        Context manager for executing code with specific tenant isolation.
        
        Usage:
            with isolation.isolation_context("client_123"):
                # All operations will use client_123 isolation
                storage_path = isolation.isolate_storage_path("data.json")
        """
        previous_tenant = get_current_tenant_id()
        tenancy.set_current_tenant(tenant_id)
        try:
            yield
        finally:
            tenancy.set_current_tenant(previous_tenant)

# Global isolation manager instance
isolation = IsolationManager()

# Convenience functions
def get_current_isolation_config() -> Dict[str, Any]:
    """Get isolation configuration for current tenant."""
    return isolation.get_current_tenant_config()

def isolate_path(path: str, tenant_id: Optional[str] = None) -> str:
    """Isolate storage path for current tenant."""
    return isolation.isolate_storage_path(path, tenant_id)

def isolate_cache_key(key: str, tenant_id: Optional[str] = None) -> str:
    """Isolate cache key for current tenant."""
    return isolation.isolate_cache_key(key, tenant_id)

def check_limits(resource_type: str, usage: Union[int, float], tenant_id: Optional[str] = None) -> bool:
    """Check resource limits for current tenant."""
    return isolation.check_resource_limits(resource_type, usage, tenant_id)

__all__ = [
    "IsolationManager",
    "isolation",
    "get_current_isolation_config",
    "isolate_path", 
    "isolate_cache_key",
    "check_limits"
] 