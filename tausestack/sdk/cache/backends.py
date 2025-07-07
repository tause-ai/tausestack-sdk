# TauseStack SDK - Cache Module Backends

from typing import Union # Added for CacheTTL

# Helper type for TTL: int for seconds, float for sub-seconds or inf
CacheTTL = Union[int, float]

import logging
from typing import Any, Optional
from cachetools import TTLCache
import os
import pathlib
import pickle
import hashlib
import time
# Union is now imported at the top of the file

from .base import AbstractCacheBackend

try:
    import redis
except ImportError:
    redis = None # type: ignore

logger = logging.getLogger(__name__)

class MemoryCacheBackend(AbstractCacheBackend):
    """
    In-memory cache backend using cachetools.TTLCache.
    The TTL for items is determined by the `default_ttl` this instance is configured with.
    `default_ttl=float('inf')` means cache forever (or until maxsize is reached).
    """
    def __init__(self, maxsize: int = 1024, default_ttl: float = 300.0):
        # TTLCache's ttl is the default TTL for all items in this instance.
        # It does not support per-item TTLs on set; the instance's TTL is always used.
        self.cache: TTLCache = TTLCache(maxsize=maxsize, ttl=default_ttl)
        self.instance_ttl = default_ttl # Store for logging/reference
        logger.info(f"MemoryCacheBackend instance initialized with maxsize={maxsize}, instance_ttl={self.instance_ttl}s")

    def get(self, key: str) -> Optional[Any]:
        try:
            value = self.cache.get(key)
            if value is not None:
                logger.debug(f"MemoryCacheBackend: Cache hit for key '{key}'")
                return value
            else:
                logger.debug(f"MemoryCacheBackend: Cache miss for key '{key}'")
                return None
        except KeyError: # Should be handled by cache.get() returning None
            logger.debug(f"MemoryCacheBackend: Cache miss (KeyError) for key '{key}'")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set an item in the cache.
        The 'ttl' argument provided here is informational for backends that support per-item TTL.
        This MemoryCacheBackend uses the TTL it was configured with at initialization for all items.
        """
        self.cache[key] = value # This uses the TTLCache instance's configured TTL.
        logger.debug(f"MemoryCacheBackend: Set key '{key}'. Item will use instance_ttl={self.instance_ttl}s. Argument ttl={ttl} is noted but not used by this item.")

    def delete(self, key: str) -> None:
        try:
            del self.cache[key]
            logger.debug(f"MemoryCacheBackend: Deleted key '{key}'")
        except KeyError:
            logger.debug(f"MemoryCacheBackend: Key '{key}' not found for deletion, no action taken.")
            pass # Key not in cache, compliant with expected behavior

    def clear(self) -> None:
        self.cache.clear()
        logger.info("MemoryCacheBackend: Cache cleared")


class DiskCacheBackend(AbstractCacheBackend):
    """
    Cache backend that stores cached items as individual files on disk.
    Uses pickle for serialization and hashlib for key hashing.
    """
    def __init__(self, base_path: str, default_ttl: CacheTTL = 300):
        self.base_path = pathlib.Path(base_path)
        self.default_ttl: CacheTTL = default_ttl # Can be float('inf') for forever
        try:
            self.base_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"DiskCacheBackend initialized. Base path: '{self.base_path}', Default TTL: {self.default_ttl}s")
        except OSError as e:
            logger.error(f"DiskCacheBackend: Error creating base_path '{self.base_path}': {e}", exc_info=True)
            raise

    def _hash_key(self, key: str) -> str:
        """Hashes the key to create a safe filename."""
        return hashlib.md5(key.encode('utf-8')).hexdigest()

    def _get_file_path(self, key: str) -> pathlib.Path:
        """Gets the full path to the cache file for a given key."""
        return self.base_path / self._hash_key(key)

    def get(self, key: str) -> Optional[Any]:
        file_path = self._get_file_path(key)
        try:
            if not file_path.exists():
                logger.debug(f"DiskCacheBackend: Cache miss (file not found) for key '{key}' (file: {file_path})")
                return None

            with open(file_path, 'rb') as f:
                cached_data = pickle.load(f)
            
            expiry_timestamp = cached_data.get('expiry_timestamp')
            
            if expiry_timestamp is not None and time.time() > expiry_timestamp:
                logger.info(f"DiskCacheBackend: Cache expired for key '{key}' (file: {file_path}). Deleting.")
                self.delete(key) # Remove expired file
                return None
            
            logger.debug(f"DiskCacheBackend: Cache hit for key '{key}' (file: {file_path})")
            return cached_data.get('value')
        except (OSError, pickle.PickleError, EOFError) as e:
            logger.warning(f"DiskCacheBackend: Error reading or unpickling cache file '{file_path}' for key '{key}': {e}. Treating as miss.", exc_info=True)
            # Attempt to delete corrupted file
            if file_path.exists():
                try:
                    file_path.unlink()
                except OSError as del_e:
                    logger.error(f"DiskCacheBackend: Failed to delete corrupted cache file '{file_path}': {del_e}", exc_info=True)
            return None

    def set(self, key: str, value: Any, ttl: Optional[CacheTTL] = None) -> None:
        file_path = self._get_file_path(key)
        current_time = time.time()
        
        effective_ttl = ttl if ttl is not None else self.default_ttl
        
        if effective_ttl == 0: # Interpret 0 as 'cache forever' for consistency with @cached
            expiry_timestamp = float('inf') 
        elif effective_ttl is None: # Should not happen if default_ttl is set, but as a fallback
             expiry_timestamp = float('inf') # Or handle as error, or use a very long time
        else:
            expiry_timestamp = current_time + effective_ttl

        data_to_store = {
            'expiry_timestamp': expiry_timestamp,
            'original_ttl': effective_ttl,
            'value': value,
            'cached_at': current_time
        }
        
        try:
            # Ensure parent directory exists (should be handled by __init__, but good practice)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'wb') as f:
                pickle.dump(data_to_store, f)
            logger.debug(f"DiskCacheBackend: Set key '{key}' (file: {file_path}), TTL: {effective_ttl}s, Expires: {expiry_timestamp}")
        except (OSError, pickle.PickleError) as e:
            logger.error(f"DiskCacheBackend: Error writing cache file '{file_path}' for key '{key}': {e}", exc_info=True)

    def delete(self, key: str) -> None:
        file_path = self._get_file_path(key)
        try:
            if file_path.exists():
                file_path.unlink()
                logger.debug(f"DiskCacheBackend: Deleted key '{key}' (file: {file_path})")
            else:
                logger.debug(f"DiskCacheBackend: Key '{key}' (file: {file_path}) not found for deletion.")
        except OSError as e:
            logger.error(f"DiskCacheBackend: Error deleting cache file '{file_path}' for key '{key}': {e}", exc_info=True)

    def clear(self) -> None:
        if not self.base_path.exists():
            logger.info("DiskCacheBackend: Cache directory '{self.base_path}' does not exist. Nothing to clear.")
            return
        
        deleted_count = 0
        error_count = 0
        for item in self.base_path.iterdir():
            if item.is_file(): # Only delete files, not subdirectories (if any)
                try:
                    item.unlink()
                    deleted_count += 1
                except OSError as e:
                    logger.warning(f"DiskCacheBackend: Error deleting file '{item}' during clear: {e}", exc_info=True)
                    error_count += 1
        if error_count > 0:
             logger.warning(f"DiskCacheBackend: Cache cleared from '{self.base_path}'. Deleted {deleted_count} files with {error_count} errors.")
        else:
            logger.info(f"DiskCacheBackend: Cache cleared from '{self.base_path}'. Deleted {deleted_count} files.")


class RedisCacheBackend(AbstractCacheBackend):
    """
    Cache backend that uses Redis as the storage medium.
    Serializes values using pickle.
    """
    def __init__(self, redis_url: str, default_ttl: CacheTTL = 300, redis_prefix: str = "tausestack_cache:"):
        if redis is None:
            logger.critical("RedisCacheBackend: 'redis' package is not installed. Please install it using 'pip install redis'.")
            raise ImportError("'redis' package is not installed. Cannot use RedisCacheBackend.")
        
        self.redis_url = redis_url
        self.default_ttl: CacheTTL = default_ttl # Can be float('inf') for forever
        self.prefix = redis_prefix
        try:
            # from_url automatically handles connection pooling
            self.client = redis.Redis.from_url(redis_url, decode_responses=False) # Store bytes, handle pickle
            self.client.ping() # Check connection
            logger.info(f"RedisCacheBackend initialized. Connected to: '{redis_url}', Default TTL: {self.default_ttl}s, Prefix: '{self.prefix}'")
        except redis.exceptions.ConnectionError as e:
            logger.error(f"RedisCacheBackend: Could not connect to Redis at '{redis_url}': {e}", exc_info=True)
            raise
        except Exception as e: # Catch other potential errors from redis.Redis.from_url
            logger.error(f"RedisCacheBackend: Error initializing Redis client with URL '{redis_url}': {e}", exc_info=True)
            raise

    def _get_redis_key(self, key: str) -> str:
        return f"{self.prefix}{key}"

    def get(self, key: str) -> Optional[Any]:
        redis_key = self._get_redis_key(key)
        try:
            cached_value_bytes = self.client.get(redis_key)
            if cached_value_bytes is None:
                logger.debug(f"RedisCacheBackend: Cache miss for key '{key}' (Redis key: '{redis_key}')")
                return None
            
            # Deserialize using pickle
            value = pickle.loads(cached_value_bytes)
            logger.debug(f"RedisCacheBackend: Cache hit for key '{key}' (Redis key: '{redis_key}')")
            return value
        except (redis.exceptions.RedisError, pickle.PickleError, EOFError) as e:
            logger.warning(f"RedisCacheBackend: Error getting or unpickling key '{key}' (Redis key: '{redis_key}'): {e}. Treating as miss.", exc_info=True)
            # Optionally, delete potentially corrupted key
            try:
                self.client.delete(redis_key)
            except redis.exceptions.RedisError as del_e:
                logger.error(f"RedisCacheBackend: Failed to delete potentially corrupted key '{redis_key}': {del_e}", exc_info=True)
            return None

    def set(self, key: str, value: Any, ttl: Optional[CacheTTL] = None) -> None:
        redis_key = self._get_redis_key(key)
        effective_ttl = ttl if ttl is not None else self.default_ttl

        try:
            # Serialize using pickle
            serialized_value = pickle.dumps(value)

            if effective_ttl == 0 or effective_ttl == float('inf'): # Cache forever
                self.client.set(redis_key, serialized_value)
                logger.debug(f"RedisCacheBackend: Set key '{key}' (Redis key: '{redis_key}') with no expiration (forever)")
            else:
                # Redis EX expects an integer number of seconds. For floats, round or ceil.
                # We'll use int() which truncates; for sub-second precision, Redis would need Lua or different commands.
                # For simplicity, we'll cast to int. If ttl is < 1s but > 0, it might become 0 (expire immediately) or 1s.
                # Let's ensure it's at least 1 if it's a small positive float, or handle as error/warning.
                # For now, simple int conversion. Consider math.ceil for small positive floats to ensure at least 1s TTL.
                ttl_seconds = int(effective_ttl)
                if ttl_seconds <= 0 and effective_ttl > 0: # e.g. ttl=0.5 became 0
                    ttl_seconds = 1 # Minimum 1 second for positive non-zero TTLs
                
                if ttl_seconds > 0:
                    self.client.setex(redis_key, ttl_seconds, serialized_value)
                    logger.debug(f"RedisCacheBackend: Set key '{key}' (Redis key: '{redis_key}') with TTL: {ttl_seconds}s")
                else: # TTL was non-positive after conversion (e.g. negative ttl passed, or became 0 from a small float)
                    # This case should ideally be caught by @cached validator, but as a safeguard:
                    # If ttl_seconds is 0 here due to a very small positive float, it might expire immediately.
                    # Or, if original ttl was negative, it's an issue.
                    # For now, if ttl_seconds is 0, we treat as 'set with no expiry' to avoid immediate deletion.
                    # This aligns with how TTLCache might handle a 0 ttl if not float('inf').
                    # A more robust solution might involve raising an error for negative TTLs here too.
                    self.client.set(redis_key, serialized_value)
                    logger.warning(f"RedisCacheBackend: Effective TTL for key '{key}' (Redis key: '{redis_key}') is {ttl_seconds}s. Setting with no expiration as a fallback.")

        except (redis.exceptions.RedisError, pickle.PickleError) as e:
            logger.error(f"RedisCacheBackend: Error setting key '{key}' (Redis key: '{redis_key}'): {e}", exc_info=True)

    def delete(self, key: str) -> None:
        redis_key = self._get_redis_key(key)
        try:
            deleted_count = self.client.delete(redis_key)
            if deleted_count > 0:
                logger.debug(f"RedisCacheBackend: Deleted key '{key}' (Redis key: '{redis_key}')")
            else:
                logger.debug(f"RedisCacheBackend: Key '{key}' (Redis key: '{redis_key}') not found for deletion.")
        except redis.exceptions.RedisError as e:
            logger.error(f"RedisCacheBackend: Error deleting key '{key}' (Redis key: '{redis_key}'): {e}", exc_info=True)

    def clear(self) -> None:
        # This is a potentially DANGEROUS operation on a shared Redis instance.
        # FLUSHDB clears the current database. FLUSHALL clears all databases.
        # A safer approach for a shared Redis is to delete keys by prefix.
        # For now, we'll implement delete by prefix.
        # Note: SCAN is preferred over KEYS for production to avoid blocking.
        logger.warning(f"RedisCacheBackend: Clearing cache with prefix '{self.prefix}'. This may be slow on large Redis instances.")
        try:
            # Use SCAN to iterate over keys matching the prefix
            deleted_count = 0
            for r_key_bytes in self.client.scan_iter(match=f"{self.prefix}*"):
                self.client.delete(r_key_bytes)
                deleted_count += 1
            logger.info(f"RedisCacheBackend: Cleared {deleted_count} keys with prefix '{self.prefix}'.")
        except redis.exceptions.RedisError as e:
            logger.error(f"RedisCacheBackend: Error clearing cache with prefix '{self.prefix}': {e}", exc_info=True)
