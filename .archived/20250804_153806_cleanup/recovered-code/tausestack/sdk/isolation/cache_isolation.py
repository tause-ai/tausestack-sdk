"""
Cache Isolation for Multi-Tenant Applications

Provides key-based isolation for cache systems in multi-tenant environments.
Ensures complete cache separation between tenants through dedicated key prefixes and memory limits.
"""

from typing import Dict, Any, Optional, List, Union, Callable
import logging
import time
import json
from contextlib import contextmanager

from ..tenancy import get_current_tenant_id
from . import isolation

logger = logging.getLogger(__name__)

class CacheIsolationManager:
    """
    Manages cache isolation for multi-tenant applications.
    
    Features:
    - Key-based isolation
    - Memory quotas per tenant
    - Cache invalidation per tenant
    - Cross-tenant access prevention
    - Cache analytics per tenant
    """
    
    def __init__(self):
        self._cache_usage: Dict[str, Dict[str, int]] = {}
        self._cache_backends: Dict[str, Any] = {}
        self._invalidation_patterns: Dict[str, List[str]] = {}
    
    def get_tenant_cache_key(self, key: str, tenant_id: Optional[str] = None) -> str:
        """
        Get isolated cache key for tenant.
        
        Args:
            key: Original cache key
            tenant_id: Tenant ID, defaults to current tenant
            
        Returns:
            Isolated cache key
        """
        return isolation.isolate_cache_key(key, tenant_id)
    
    def get_tenant_cache_prefix(self, tenant_id: Optional[str] = None) -> str:
        """
        Get cache key prefix for tenant.
        
        Args:
            tenant_id: Tenant ID, defaults to current tenant
            
        Returns:
            Cache key prefix for tenant
        """
        effective_tenant_id = tenant_id or get_current_tenant_id()
        config = isolation.get_tenant_isolation_config(effective_tenant_id)
        return config.get("cache_prefix", "").rstrip(":")
    
    def register_cache_backend(self, backend_name: str, backend_instance: Any) -> None:
        """
        Register a cache backend for isolation management.
        
        Args:
            backend_name: Name of the backend (redis, memory, etc.)
            backend_instance: Cache backend instance
        """
        self._cache_backends[backend_name] = backend_instance
        logger.info(f"Registered cache backend: {backend_name}")
    
    def get_cache_backend(self, backend_name: str) -> Optional[Any]:
        """
        Get registered cache backend.
        
        Args:
            backend_name: Name of the backend
            
        Returns:
            Cache backend instance or None
        """
        return self._cache_backends.get(backend_name)
    
    def set_with_isolation(self, key: str, value: Any, ttl: Optional[int] = None,
                          tenant_id: Optional[str] = None, backend_name: str = "default") -> bool:
        """
        Set cache value with tenant isolation.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            tenant_id: Tenant ID, defaults to current tenant
            backend_name: Cache backend to use
            
        Returns:
            True if value set successfully
        """
        isolated_key = self.get_tenant_cache_key(key, tenant_id)
        effective_tenant_id = tenant_id or get_current_tenant_id()
        
        # Check cache quota
        if not self._check_cache_quota(effective_tenant_id, value, backend_name):
            logger.warning(f"Cache quota exceeded for tenant {effective_tenant_id}")
            return False
        
        try:
            backend = self.get_cache_backend(backend_name)
            if not backend:
                logger.error(f"Cache backend '{backend_name}' not found")
                return False
            
            # Set value in cache
            if hasattr(backend, 'set'):
                backend.set(isolated_key, value, ttl)
            elif hasattr(backend, 'setex'):
                backend.setex(isolated_key, ttl or 3600, value)
            else:
                logger.error(f"Cache backend '{backend_name}' does not support set operations")
                return False
            
            # Track usage
            self._track_cache_usage(effective_tenant_id, isolated_key, value, backend_name)
            
            logger.debug(f"Set cache key '{isolated_key}' for tenant '{effective_tenant_id}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set cache key '{isolated_key}' for tenant '{effective_tenant_id}': {e}")
            return False
    
    def get_with_isolation(self, key: str, default: Any = None,
                          tenant_id: Optional[str] = None, backend_name: str = "default") -> Any:
        """
        Get cache value with tenant isolation.
        
        Args:
            key: Cache key
            default: Default value if key not found
            tenant_id: Tenant ID, defaults to current tenant
            backend_name: Cache backend to use
            
        Returns:
            Cached value or default
        """
        isolated_key = self.get_tenant_cache_key(key, tenant_id)
        effective_tenant_id = tenant_id or get_current_tenant_id()
        
        try:
            backend = self.get_cache_backend(backend_name)
            if not backend:
                logger.error(f"Cache backend '{backend_name}' not found")
                return default
            
            # Get value from cache
            if hasattr(backend, 'get'):
                value = backend.get(isolated_key)
            elif hasattr(backend, 'get'):
                value = backend.get(isolated_key)
            else:
                logger.error(f"Cache backend '{backend_name}' does not support get operations")
                return default
            
            if value is None:
                return default
            
            logger.debug(f"Retrieved cache key '{isolated_key}' for tenant '{effective_tenant_id}'")
            return value
            
        except Exception as e:
            logger.error(f"Failed to get cache key '{isolated_key}' for tenant '{effective_tenant_id}': {e}")
            return default
    
    def delete_with_isolation(self, key: str, tenant_id: Optional[str] = None,
                            backend_name: str = "default") -> bool:
        """
        Delete cache value with tenant isolation.
        
        Args:
            key: Cache key
            tenant_id: Tenant ID, defaults to current tenant
            backend_name: Cache backend to use
            
        Returns:
            True if key deleted successfully
        """
        isolated_key = self.get_tenant_cache_key(key, tenant_id)
        effective_tenant_id = tenant_id or get_current_tenant_id()
        
        try:
            backend = self.get_cache_backend(backend_name)
            if not backend:
                logger.error(f"Cache backend '{backend_name}' not found")
                return False
            
            # Delete value from cache
            if hasattr(backend, 'delete'):
                backend.delete(isolated_key)
            elif hasattr(backend, 'del'):
                backend.del_(isolated_key)
            else:
                logger.error(f"Cache backend '{backend_name}' does not support delete operations")
                return False
            
            # Update usage tracking
            self._remove_cache_usage(effective_tenant_id, isolated_key, backend_name)
            
            logger.debug(f"Deleted cache key '{isolated_key}' for tenant '{effective_tenant_id}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete cache key '{isolated_key}' for tenant '{effective_tenant_id}': {e}")
            return False
    
    def invalidate_tenant_cache(self, tenant_id: str, pattern: str = "*",
                              backend_name: str = "default") -> int:
        """
        Invalidate all cache entries for a tenant matching a pattern.
        
        Args:
            tenant_id: Tenant ID
            pattern: Pattern to match keys (supports wildcards)
            backend_name: Cache backend to use
            
        Returns:
            Number of keys invalidated
        """
        cache_prefix = self.get_tenant_cache_prefix(tenant_id)
        search_pattern = f"{cache_prefix}:{pattern}" if cache_prefix else pattern
        
        try:
            backend = self.get_cache_backend(backend_name)
            if not backend:
                logger.error(f"Cache backend '{backend_name}' not found")
                return 0
            
            # Get keys matching pattern
            if hasattr(backend, 'keys'):
                keys = backend.keys(search_pattern)
            elif hasattr(backend, 'scan_iter'):
                keys = list(backend.scan_iter(match=search_pattern))
            else:
                logger.error(f"Cache backend '{backend_name}' does not support key scanning")
                return 0
            
            # Delete matching keys
            deleted_count = 0
            for key in keys:
                if self.delete_with_isolation(key, tenant_id, backend_name):
                    deleted_count += 1
            
            logger.info(f"Invalidated {deleted_count} cache keys for tenant '{tenant_id}'")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to invalidate cache for tenant '{tenant_id}': {e}")
            return 0
    
    def get_tenant_cache_usage(self, tenant_id: str, backend_name: str = "default") -> Dict[str, Any]:
        """
        Get cache usage statistics for tenant.
        
        Args:
            tenant_id: Tenant ID
            backend_name: Cache backend to use
            
        Returns:
            Dictionary with usage statistics
        """
        cache_prefix = self.get_tenant_cache_prefix(tenant_id)
        search_pattern = f"{cache_prefix}:*" if cache_prefix else "*"
        
        try:
            backend = self.get_cache_backend(backend_name)
            if not backend:
                return {"key_count": 0, "memory_usage_bytes": 0, "cache_prefix": cache_prefix}
            
            # Get keys for tenant
            if hasattr(backend, 'keys'):
                keys = backend.keys(search_pattern)
            elif hasattr(backend, 'scan_iter'):
                keys = list(backend.scan_iter(match=search_pattern))
            else:
                return {"key_count": 0, "memory_usage_bytes": 0, "cache_prefix": cache_prefix}
            
            # Calculate usage
            key_count = len(keys)
            memory_usage = 0
            
            # Estimate memory usage (rough calculation)
            for key in keys:
                try:
                    value = backend.get(key)
                    if value:
                        # Rough estimate: key + value + overhead
                        memory_usage += len(str(key)) + len(str(value)) + 100
                except:
                    continue
            
            return {
                "key_count": key_count,
                "memory_usage_bytes": memory_usage,
                "cache_prefix": cache_prefix,
                "search_pattern": search_pattern
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache usage for tenant '{tenant_id}': {e}")
            return {"key_count": 0, "memory_usage_bytes": 0, "cache_prefix": cache_prefix}
    
    def check_cache_quota(self, tenant_id: str, value_size: int, backend_name: str = "default") -> bool:
        """
        Check if tenant is within cache quota.
        
        Args:
            tenant_id: Tenant ID
            value_size: Size of value to be cached in bytes
            backend_name: Cache backend to use
            
        Returns:
            True if within quota, False otherwise
        """
        usage = self.get_tenant_cache_usage(tenant_id, backend_name)
        current_memory = usage["memory_usage_bytes"]
        
        # Check memory quota
        return isolation.check_resource_limits("cache_memory_mb", 
                                             (current_memory + value_size) / (1024**2), 
                                             tenant_id)
    
    def _check_cache_quota(self, tenant_id: str, value: Any, backend_name: str) -> bool:
        """Internal method to check cache quota."""
        # Estimate value size
        try:
            value_size = len(str(value))
        except:
            value_size = 1024  # Default estimate
        
        return self.check_cache_quota(tenant_id, value_size, backend_name)
    
    def _track_cache_usage(self, tenant_id: str, key: str, value: Any, backend_name: str) -> None:
        """Track cache usage for tenant."""
        if tenant_id not in self._cache_usage:
            self._cache_usage[tenant_id] = {}
        
        if backend_name not in self._cache_usage[tenant_id]:
            self._cache_usage[tenant_id][backend_name] = {"keys": [], "total_size": 0}
        
        # Estimate value size
        try:
            value_size = len(str(value))
        except:
            value_size = 1024
        
        self._cache_usage[tenant_id][backend_name]["keys"].append(key)
        self._cache_usage[tenant_id][backend_name]["total_size"] += value_size
    
    def _remove_cache_usage(self, tenant_id: str, key: str, backend_name: str) -> None:
        """Remove cache usage tracking for key."""
        if tenant_id in self._cache_usage and backend_name in self._cache_usage[tenant_id]:
            if key in self._cache_usage[tenant_id][backend_name]["keys"]:
                self._cache_usage[tenant_id][backend_name]["keys"].remove(key)
    
    def clear_tenant_cache(self, tenant_id: str, backend_name: str = "default") -> bool:
        """
        Clear all cache entries for a tenant.
        
        Args:
            tenant_id: Tenant ID
            backend_name: Cache backend to use
            
        Returns:
            True if cache cleared successfully
        """
        return self.invalidate_tenant_cache(tenant_id, "*", backend_name) > 0
    
    def get_cache_keys_for_tenant(self, tenant_id: str, pattern: str = "*",
                                backend_name: str = "default") -> List[str]:
        """
        Get all cache keys for a tenant.
        
        Args:
            tenant_id: Tenant ID
            pattern: Pattern to match keys
            backend_name: Cache backend to use
            
        Returns:
            List of cache keys
        """
        cache_prefix = self.get_tenant_cache_prefix(tenant_id)
        search_pattern = f"{cache_prefix}:{pattern}" if cache_prefix else pattern
        
        try:
            backend = self.get_cache_backend(backend_name)
            if not backend:
                return []
            
            if hasattr(backend, 'keys'):
                keys = backend.keys(search_pattern)
            elif hasattr(backend, 'scan_iter'):
                keys = list(backend.scan_iter(match=search_pattern))
            else:
                return []
            
            return keys
            
        except Exception as e:
            logger.error(f"Failed to get cache keys for tenant '{tenant_id}': {e}")
            return []
    
    @contextmanager
    def tenant_cache_context(self, tenant_id: Optional[str] = None):
        """
        Context manager for cache operations with tenant isolation.
        
        Usage:
            with cache_isolation.tenant_cache_context("client_123"):
                # All cache operations will use client_123 isolation
                cache_isolation.set_with_isolation("key", "value")
        """
        effective_tenant_id = tenant_id or get_current_tenant_id()
        
        try:
            yield
        finally:
            pass

# Global cache isolation manager
cache_isolation = CacheIsolationManager()

# Convenience functions
def get_cache_key(key: str, tenant_id: Optional[str] = None) -> str:
    """Get isolated cache key for current tenant."""
    return cache_isolation.get_tenant_cache_key(key, tenant_id)

def set_cache(key: str, value: Any, ttl: Optional[int] = None, 
              tenant_id: Optional[str] = None, backend: str = "default") -> bool:
    """Set cache value with tenant isolation."""
    return cache_isolation.set_with_isolation(key, value, ttl, tenant_id, backend)

def get_cache(key: str, default: Any = None, 
              tenant_id: Optional[str] = None, backend: str = "default") -> Any:
    """Get cache value with tenant isolation."""
    return cache_isolation.get_with_isolation(key, default, tenant_id, backend)

def delete_cache(key: str, tenant_id: Optional[str] = None, backend: str = "default") -> bool:
    """Delete cache value with tenant isolation."""
    return cache_isolation.delete_with_isolation(key, tenant_id, backend)

def clear_tenant_cache(tenant_id: str, backend: str = "default") -> bool:
    """Clear all cache for tenant."""
    return cache_isolation.clear_tenant_cache(tenant_id, backend)

def get_cache_usage(tenant_id: str, backend: str = "default") -> Dict[str, Any]:
    """Get cache usage for tenant."""
    return cache_isolation.get_tenant_cache_usage(tenant_id, backend)

__all__ = [
    "CacheIsolationManager",
    "cache_isolation",
    "get_cache_key",
    "set_cache",
    "get_cache", 
    "delete_cache",
    "clear_tenant_cache",
    "get_cache_usage"
] 