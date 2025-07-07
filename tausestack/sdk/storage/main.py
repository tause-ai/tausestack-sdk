import logging
import os
from typing import Any, Dict, Optional, Union

from .backends import BOTO3_AVAILABLE, LocalStorage, S3Storage, PANDAS_AVAILABLE
from .base import (
    AbstractBinaryStorageBackend,
    AbstractDataFrameStorageBackend,
    AbstractJsonStorageBackend,
)
from .exceptions import StorageException

# Import tenancy support
try:
    from ..tenancy import get_current_tenant_id, get_tenant_config, is_multi_tenant_enabled
except ImportError:
    # Fallback for backward compatibility
    def get_current_tenant_id() -> str:
        return "default"
    def get_tenant_config(tenant_id: Optional[str] = None) -> Dict[str, Any]:
        return {}
    def is_multi_tenant_enabled() -> bool:
        return False

if PANDAS_AVAILABLE:
    import pandas as pd
else:
    pd = None

logger = logging.getLogger(__name__)

# Global storage backend instances (per tenant)
_storage_backend_instances: Dict[str, Union[AbstractJsonStorageBackend, AbstractBinaryStorageBackend, AbstractDataFrameStorageBackend]] = {}

def _get_storage_backend(
    backend_name: Optional[str] = None, 
    config: Optional[Dict[str, Any]] = None,
    tenant_id: Optional[str] = None
) -> Union[AbstractJsonStorageBackend, AbstractBinaryStorageBackend, AbstractDataFrameStorageBackend]:
    """
    Get or create a storage backend instance.
    
    Supports both monolithic and multi-tenant modes:
    - Monolithic: Uses default tenant configuration
    - Multi-tenant: Uses tenant-specific configuration
    """
    # Determine effective tenant ID
    effective_tenant_id = tenant_id or get_current_tenant_id()
    
    # Get tenant-specific configuration if multi-tenant mode is enabled
    if is_multi_tenant_enabled():
        tenant_config = get_tenant_config(effective_tenant_id)
        tenant_storage_config = tenant_config.get("storage_config", {})
        
        # Merge tenant config with provided config
        effective_config = {**tenant_storage_config, **(config or {})}
        effective_backend_name = backend_name or tenant_storage_config.get("backend") or os.getenv("TAUSESTACK_STORAGE_BACKEND", "local")
    else:
        # Monolithic mode - use environment variables and provided config
        effective_config = config or {}
        effective_backend_name = backend_name or os.getenv("TAUSESTACK_STORAGE_BACKEND", "local")
    
    # Create unique instance key for this tenant + backend + config combination
    config_hash = str(hash(frozenset(effective_config.items()))) if effective_config else "default"
    instance_key = f"{effective_tenant_id}_{effective_backend_name}_{config_hash}"
    
    if instance_key not in _storage_backend_instances:
        logger.info(f"Initializing storage backend: {effective_backend_name} for tenant: {effective_tenant_id}")
        
        from .backends import LocalStorage, S3Storage
        
        if effective_backend_name == "local":
            # Tenant-specific paths for local storage
            base_path = effective_config.get("base_path", f"./.tausestack_storage/{effective_tenant_id}")
            _storage_backend_instances[instance_key] = LocalStorage(
                base_json_path=f"{base_path}/json",
                base_binary_path=f"{base_path}/binary", 
                base_dataframe_path=f"{base_path}/dataframe"
            )
            
        elif effective_backend_name == "s3":
            # Tenant-specific S3 configuration
            bucket_name = effective_config.get("bucket_name") or os.getenv("TAUSESTACK_S3_BUCKET_NAME")
            if not bucket_name:
                raise StorageException("S3 bucket name required for S3 storage backend")
            
            # S3Storage doesn't support key_prefix in constructor, so we'll use the existing implementation
            _storage_backend_instances[instance_key] = S3Storage(bucket_name=bucket_name)
            
        elif effective_backend_name == "gcs":
            # GCS BACKEND NOT IMPLEMENTED - Using local storage fallback
            logger.warning("GCS backend not implemented, falling back to local storage")
            base_path = effective_config.get("base_path", f"./.tausestack_storage/{effective_tenant_id}")
            _storage_backend_instances[instance_key] = LocalStorage(
                base_json_path=f"{base_path}/json",
                base_binary_path=f"{base_path}/binary", 
                base_dataframe_path=f"{base_path}/dataframe"
            )
            
        elif effective_backend_name == "supabase":
            # SUPABASE BACKEND NOT IMPLEMENTED - Using local storage fallback
            logger.warning("Supabase backend not implemented, falling back to local storage")
            base_path = effective_config.get("base_path", f"./.tausestack_storage/{effective_tenant_id}")
            _storage_backend_instances[instance_key] = LocalStorage(
                base_json_path=f"{base_path}/json",
                base_binary_path=f"{base_path}/binary", 
                base_dataframe_path=f"{base_path}/dataframe"
            )
            
        else:
            raise StorageException(f"Unsupported storage backend: {effective_backend_name}")
        
        logger.info(f"Storage backend initialized: {instance_key}")
    
    return _storage_backend_instances[instance_key]

# --- Client Classes ---

class JSONStorageClient:
    """Client for JSON storage operations with multi-tenant support."""
    
    def put(self, key: str, value: dict, tenant_id: Optional[str] = None) -> None:
        """
        Store a JSON object.
        
        Args:
            key: Storage key
            value: JSON object to store
            tenant_id: Optional tenant ID (uses current tenant if not specified)
        """
        backend = _get_storage_backend(tenant_id=tenant_id)
        backend.put_json(key, value)
    
    def get(self, key: str, tenant_id: Optional[str] = None) -> Optional[dict]:
        """
        Retrieve a JSON object.
        
        Args:
            key: Storage key
            tenant_id: Optional tenant ID (uses current tenant if not specified)
            
        Returns:
            JSON object or None if not found
        """
        backend = _get_storage_backend(tenant_id=tenant_id)
        return backend.get_json(key)
    
    def delete(self, key: str, tenant_id: Optional[str] = None) -> None:
        """
        Delete a JSON object.
        
        Args:
            key: Storage key
            tenant_id: Optional tenant ID (uses current tenant if not specified)
        """
        backend = _get_storage_backend(tenant_id=tenant_id)
        backend.delete_json(key)

class BinaryStorageClient:
    """Client for binary storage operations with multi-tenant support."""
    
    def put(self, key: str, value: bytes, content_type: Optional[str] = None, tenant_id: Optional[str] = None) -> None:
        """Store binary data."""
        backend = _get_storage_backend(tenant_id=tenant_id)
        backend.put_binary(key, value, content_type)
    
    def get(self, key: str, tenant_id: Optional[str] = None) -> Optional[bytes]:
        """Retrieve binary data."""
        backend = _get_storage_backend(tenant_id=tenant_id)
        return backend.get_binary(key)
    
    def delete(self, key: str, tenant_id: Optional[str] = None) -> None:
        """Delete binary data."""
        backend = _get_storage_backend(tenant_id=tenant_id)
        backend.delete_binary(key)

class DataFrameStorageClient:
    """Client for DataFrame storage operations with multi-tenant support."""
    
    def put(self, key: str, value: "pd.DataFrame", tenant_id: Optional[str] = None) -> None:
        """Store a pandas DataFrame."""
        if not PANDAS_AVAILABLE:
            raise StorageException("Pandas is not available. Install pandas to use DataFrame storage.")
        backend = _get_storage_backend(tenant_id=tenant_id)
        backend.put_dataframe(key, value)
    
    def get(self, key: str, tenant_id: Optional[str] = None) -> Optional["pd.DataFrame"]:
        """Retrieve a pandas DataFrame."""
        if not PANDAS_AVAILABLE:
            raise StorageException("Pandas is not available. Install pandas to use DataFrame storage.")
        backend = _get_storage_backend(tenant_id=tenant_id)
        return backend.get_dataframe(key)
    
    def delete(self, key: str, tenant_id: Optional[str] = None) -> None:
        """Delete a pandas DataFrame."""
        if not PANDAS_AVAILABLE:
            raise StorageException("Pandas is not available. Install pandas to use DataFrame storage.")
        backend = _get_storage_backend(tenant_id=tenant_id)
        backend.delete_dataframe(key)

# --- Unified Storage Manager ---

class StorageManager:
    """
    Unified storage manager that provides access to JSON, binary, and DataFrame storage.
    This is the main entry point for storage operations.
    """
    
    def __init__(self, backend: Optional[Union[AbstractJsonStorageBackend, AbstractBinaryStorageBackend, AbstractDataFrameStorageBackend]] = None):
        """
        Initialize the storage manager.
        
        Args:
            backend: Optional storage backend. If None, uses the default backend from environment.
        """
        self._backend = backend or _get_storage_backend()
        self._json_client = JSONStorageClient()
        self._binary_client = BinaryStorageClient()
        self._dataframe_client = (
            DataFrameStorageClient() if PANDAS_AVAILABLE else None
        )
        logger.debug(f"StorageManager initialized with backend: {type(self._backend).__name__}")
    
    # JSON methods
    def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a JSON object from storage."""
        return self._json_client.get(key)
    
    def put_json(self, key: str, value: Dict[str, Any]) -> None:
        """Store a JSON object in storage."""
        self._json_client.put(key, value)
    
    def delete_json(self, key: str) -> None:
        """Delete a JSON object from storage."""
        self._json_client.delete(key)
    
    # Binary methods
    def get_binary(self, key: str) -> Optional[bytes]:
        """Get binary data from storage."""
        return self._binary_client.get(key)
    
    def put_binary(self, key: str, value: bytes, content_type: Optional[str] = None) -> None:
        """Store binary data in storage."""
        self._binary_client.put(key, value, content_type)
    
    def delete_binary(self, key: str) -> None:
        """Delete binary data from storage."""
        self._binary_client.delete(key)
    
    # DataFrame methods (if pandas is available)
    def get_dataframe(self, key: str) -> Optional["pd.DataFrame"]:
        """Get a DataFrame from storage."""
        if not self._dataframe_client:
            raise ImportError("pandas and pyarrow are required for DataFrame operations")
        return self._dataframe_client.get(key)
    
    def put_dataframe(self, key: str, value: "pd.DataFrame") -> None:
        """Store a DataFrame in storage."""
        if not self._dataframe_client:
            raise ImportError("pandas and pyarrow are required for DataFrame operations")
        self._dataframe_client.put(key, value)
    
    def delete_dataframe(self, key: str) -> None:
        """Delete a DataFrame from storage."""
        if not self._dataframe_client:
            raise ImportError("pandas and pyarrow are required for DataFrame operations")
        self._dataframe_client.delete(key)
    
    @property
    def json(self) -> JSONStorageClient:
        """Access to JSON storage client."""
        return self._json_client
    
    @property
    def binary(self) -> BinaryStorageClient:
        """Access to binary storage client."""
        return self._binary_client
    
    @property
    def dataframe(self) -> Optional[DataFrameStorageClient]:
        """Access to DataFrame storage client (if pandas is available)."""
        return self._dataframe_client

# --- Public API ---

# The public client instances that applications will import and use.
_backend = _get_storage_backend()

# The type ignore is used because _get_storage_backend returns a Union,
# but LocalStorage and S3Storage implement all necessary abstract backends.
json_client = JSONStorageClient()
binary_client = BinaryStorageClient()
dataframe_client = (
    DataFrameStorageClient() if PANDAS_AVAILABLE else None
)

# Create client instances for backward compatibility and public API
json = JSONStorageClient()
binary = BinaryStorageClient() 
dataframe = DataFrameStorageClient() if PANDAS_AVAILABLE else None

# Default storage manager instance
storage_manager = StorageManager()

__all__ = [
    'json', 'binary', 'dataframe',  # Backward compatible API
    'JSONStorageClient', 'BinaryStorageClient', 'DataFrameStorageClient',  # New classes
    'StorageManager', 'storage_manager'  # Manager API
]
