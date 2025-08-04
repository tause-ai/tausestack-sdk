# TauseStack SDK - Cache Module Main Logic

import functools
import logging
import os
import traceback # For detailed error logging
from typing import Callable, Any, Optional, Dict, TYPE_CHECKING # Added TYPE_CHECKING
import hashlib # Added for Redis instance key generation

from .base import AbstractCacheBackend
# Backends will be imported dynamically by _get_cache_backend
if TYPE_CHECKING:
    from .backends import MemoryCacheBackend, DiskCacheBackend, RedisCacheBackend, CacheTTL

logger = logging.getLogger(__name__)

_cache_backend_instances: Dict[str, AbstractCacheBackend] = {}
DEFAULT_DISK_CACHE_PATH = ".tausestack_cache/disk"
DEFAULT_REDIS_URL = "redis://localhost:6379/0"
DEFAULT_REDIS_PREFIX = "tausestack_cache:"  # Default path for disk cache
_default_backend_name_config: Optional[str] = None
DEFAULT_CACHE_BACKEND_CONFIG: Dict[str, Dict[str, Any]] = {
    "memory": {"default_ttl": 300},
    "disk": {"default_ttl": 3600, "base_path": DEFAULT_DISK_CACHE_PATH},
    "redis": {"default_ttl": 3600, "redis_url": DEFAULT_REDIS_URL, "redis_prefix": DEFAULT_REDIS_PREFIX}
}

def _get_default_backend_name() -> str:
    global _default_backend_name_config
    if _default_backend_name_config is None:
        _default_backend_name_config = os.getenv('TAUSESTACK_CACHE_DEFAULT_BACKEND', 'memory')
        logger.info(f"Default cache backend set to: '{_default_backend_name_config}' (from TAUSESTACK_CACHE_DEFAULT_BACKEND or default 'memory')")
    return _default_backend_name_config

def _get_cache_backend(backend_name: Optional[str] = None, config: Optional[Dict[str, Any]] = None) -> AbstractCacheBackend:
    """
    Retrieves or initializes a cache backend instance.
    Instance identity can be tied to configuration (e.g., TTL for 'memory', TTL and path for 'disk').
    
    Args:
        backend_name: The name of the backend to get (e.g., 'memory', 'disk').
        config: Backend-specific configuration. 
                For 'memory', expects {'ttl': CacheTTL}.
                For 'disk', expects {'ttl': CacheTTL, 'base_path': str (optional)}.
                For 'redis', expects {'redis_url': str, 'default_ttl': int|float (optional), 'redis_prefix': str (optional)}.
    """
    effective_backend_name = backend_name or _get_default_backend_name()
    instance_config = config or {}

    # Determine the specific TTL for this backend instance based on decorator's ttl
    decorator_ttl_value = instance_config.get('ttl')
    # ttl=0 from decorator means 'cache forever', map to float('inf') for backend's default_ttl
    # If decorator_ttl_value is None, default to a standard TTL from DEFAULT_CACHE_BACKEND_CONFIG,
    # or float('inf') if explicitly 0.
    default_config_ttl = DEFAULT_CACHE_BACKEND_CONFIG.get(effective_backend_name, {}).get('default_ttl', 300)
    instance_default_ttl = float('inf') if decorator_ttl_value == 0 else (decorator_ttl_value if decorator_ttl_value is not None else default_config_ttl)

    # Create a unique key for the instance based on its type and configuration
    instance_key = effective_backend_name
    if effective_backend_name == "memory":
        instance_key = f"memory_ttl_{str(instance_default_ttl).replace('.', '_')}"
    elif effective_backend_name == "disk":
        base_path = instance_config.get('base_path', os.getenv("TAUSESTACK_DISK_CACHE_PATH", DEFAULT_DISK_CACHE_PATH))
        # Using a simple replace for path component; consider hashlib for more complex/long paths if needed
        path_key_component = base_path.replace('/', '_').replace('.', '_') 
        instance_key = f"disk_ttl_{str(instance_default_ttl).replace('.', '_')}_path_{path_key_component}"
    elif effective_backend_name == "redis":
        redis_url = instance_config.get('redis_url', os.getenv("TAUSESTACK_REDIS_URL", DEFAULT_REDIS_URL))
        redis_prefix = instance_config.get('redis_prefix', DEFAULT_REDIS_PREFIX)
        # Sanitize URL and prefix for key to avoid issues with special characters if any
        url_key_component = hashlib.md5(redis_url.encode()).hexdigest()
        prefix_key_component = redis_prefix.replace(':', '_').replace('/', '_') # Basic sanitization
        instance_key = f"redis_ttl_{str(instance_default_ttl).replace('.', '_')}_url_{url_key_component}_prefix_{prefix_key_component}"
    # Add other backend key generation logic here if they depend on config for instance uniqueness

    if instance_key not in _cache_backend_instances:
        logger.info(f"Initializing cache backend instance: '{instance_key}' (Backend Type: '{effective_backend_name}', Configured TTL: {instance_default_ttl}s)")
        from .backends import MemoryCacheBackend, DiskCacheBackend, RedisCacheBackend, CacheTTL # Delayed import
        
        if effective_backend_name == "memory":
            _cache_backend_instances[instance_key] = MemoryCacheBackend(default_ttl=instance_default_ttl)
        elif effective_backend_name == "disk":
            # base_path would have been determined above for instance_key generation
            current_base_path = instance_config.get('base_path', os.getenv("TAUSESTACK_DISK_CACHE_PATH", DEFAULT_DISK_CACHE_PATH))
            _cache_backend_instances[instance_key] = DiskCacheBackend(base_path=current_base_path, default_ttl=instance_default_ttl)
            logger.info(f"DiskCacheBackend instance '{instance_key}' will use path: '{current_base_path}'")
        elif effective_backend_name == "redis":
            redis_url = instance_config.get('redis_url', os.getenv("TAUSESTACK_REDIS_URL", DEFAULT_REDIS_URL))
            redis_prefix = instance_config.get('redis_prefix', DEFAULT_REDIS_PREFIX)
            _cache_backend_instances[instance_key] = RedisCacheBackend(redis_url=redis_url, default_ttl=instance_default_ttl, redis_prefix=redis_prefix) # Corrected param name
            logger.info(f"RedisCacheBackend instance '{instance_key}' will use URL: '{redis_url}' and redis_prefix: '{redis_prefix}'") # Corrected param name in log
        else:
            logger.error(f"Unsupported or not yet implemented cache backend: '{effective_backend_name}'")
            raise ValueError(f"Unsupported cache backend: {effective_backend_name}")
        logger.info(f"Cache backend instance '{instance_key}' initialized successfully.")
    
    return _cache_backend_instances[instance_key]

def _generate_cache_key(func: Callable, args: tuple, kwargs: dict) -> str:
    """Generates a cache key based on the function and its arguments."""
    key_parts = [func.__module__ or '', func.__name__]
    for arg in args:
        key_parts.append(str(arg))
    for k, v in sorted(kwargs.items()):
        key_parts.append(f"{k}={v}")
    return ":".join(key_parts)

def cached(ttl: 'CacheTTL', backend: Optional[str] = None, backend_config: Optional[Dict[str, Any]] = None) -> Callable:
    """
    Decorator to cache the result of a function.

    Args:
        ttl: Time-to-live for the cache entry in seconds. 
             A TTL of 0 means cache forever (if supported by backend).
        backend: Name of the cache backend to use (e.g., 'memory', 'disk', 'redis').
                 If None, uses the default configured backend.
        config: A dictionary with backend-specific configurations.
                - For 'memory': `default_ttl` (int|float, optional).
                - For 'disk': `default_ttl` (int|float, optional), `base_path` (str, optional).
                - For 'redis': `default_ttl` (int|float, optional), `redis_url` (str, optional), `redis_prefix` (str, optional).
    """
    if not isinstance(ttl, (int, float)) or ttl < 0:
        raise ValueError("TTL must be a non-negative integer or float.")
    
    final_backend_config = backend_config or {}
    final_backend_config.setdefault('ttl', ttl) # Ensure ttl from decorator is in config

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                # For memory backend, pass the decorator's TTL to determine the specific instance.
                # For other backends, this config might be used differently or not at all at instance retrieval.
                if (backend is None or backend == 'memory'): 
                    final_backend_config['ttl'] = ttl

                cache_backend_instance = _get_cache_backend(backend, config=final_backend_config)
                cache_key = _generate_cache_key(func, args, kwargs)
            except Exception as e:
                logger.error(f"Error in cache setup for {func.__name__}: {e}. Calling function directly.\n{traceback.format_exc()}", exc_info=False) # exc_info=False as we add traceback manually
                return func(*args, **kwargs)

            logger.debug(f"Cache check for key: '{cache_key}' in backend for function '{func.__name__}'")
            
            cached_value = cache_backend_instance.get(cache_key)
            if cached_value is not None:
                logger.info(f"Cache hit for key: '{cache_key}' from function '{func.__name__}'")
                return cached_value
            
            logger.info(f"Cache miss for key: '{cache_key}' from function '{func.__name__}'. Executing function.")
            result = func(*args, **kwargs)
            
            # Determine TTL for the set operation: None for 'forever' (if ttl=0), else the value.
            effective_set_ttl = None if ttl == 0 else ttl
            cache_backend_instance.set(cache_key, result, ttl=effective_set_ttl)
            return result
        return wrapper
    return decorator
