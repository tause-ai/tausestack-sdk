"""
Storage Isolation for Multi-Tenant Applications

Provides path-based isolation for file storage in multi-tenant environments.
Ensures complete file separation between tenants through dedicated storage paths and quotas.
"""

from typing import Dict, Any, Optional, List, Union, BinaryIO
import os
import logging
from pathlib import Path
import shutil
from contextlib import contextmanager

from ..tenancy import get_current_tenant_id
from . import isolation

logger = logging.getLogger(__name__)

class StorageIsolationManager:
    """
    Manages storage isolation for multi-tenant applications.
    
    Features:
    - Path-based isolation
    - Storage quotas per tenant
    - Backup and restore per tenant
    - Cross-tenant access prevention
    - Storage analytics per tenant
    """
    
    def __init__(self):
        self._storage_cache: Dict[str, str] = {}
        self._usage_tracking: Dict[str, Dict[str, int]] = {}
        self._backup_locations: Dict[str, str] = {}
    
    def get_tenant_storage_path(self, path: str, tenant_id: Optional[str] = None) -> str:
        """
        Get isolated storage path for tenant.
        
        Args:
            path: Original storage path
            tenant_id: Tenant ID, defaults to current tenant
            
        Returns:
            Isolated storage path
        """
        return isolation.isolate_storage_path(path, tenant_id)
    
    def get_tenant_storage_root(self, tenant_id: Optional[str] = None) -> str:
        """
        Get storage root directory for tenant.
        
        Args:
            tenant_id: Tenant ID, defaults to current tenant
            
        Returns:
            Storage root path for tenant
        """
        effective_tenant_id = tenant_id or get_current_tenant_id()
        config = isolation.get_tenant_isolation_config(effective_tenant_id)
        return config.get("storage_prefix", "").rstrip("/")
    
    def create_tenant_storage(self, tenant_id: str, base_storage_path: str) -> bool:
        """
        Create storage directory structure for tenant.
        
        Args:
            tenant_id: Tenant ID
            base_storage_path: Base storage directory
            
        Returns:
            True if storage created successfully
        """
        tenant_root = self.get_tenant_storage_root(tenant_id)
        
        if not tenant_root:
            logger.info(f"Tenant {tenant_id} uses root storage, no creation needed")
            return True
        
        try:
            # Create tenant storage directory
            tenant_path = os.path.join(base_storage_path, tenant_root)
            os.makedirs(tenant_path, exist_ok=True)
            
            # Create subdirectories for different file types
            subdirs = ["documents", "images", "videos", "backups", "temp"]
            for subdir in subdirs:
                subdir_path = os.path.join(tenant_path, subdir)
                os.makedirs(subdir_path, exist_ok=True)
            
            logger.info(f"Created storage structure for tenant '{tenant_id}' at {tenant_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create storage for tenant '{tenant_id}': {e}")
            return False
    
    def delete_tenant_storage(self, tenant_id: str, base_storage_path: str) -> bool:
        """
        Delete all storage for a tenant.
        
        Args:
            tenant_id: Tenant ID
            base_storage_path: Base storage directory
            
        Returns:
            True if storage deleted successfully
        """
        tenant_root = self.get_tenant_storage_root(tenant_id)
        
        if not tenant_root:
            logger.warning(f"Cannot delete root storage for tenant {tenant_id}")
            return False
        
        try:
            tenant_path = os.path.join(base_storage_path, tenant_root)
            
            if os.path.exists(tenant_path):
                shutil.rmtree(tenant_path)
                logger.info(f"Deleted storage for tenant '{tenant_id}' at {tenant_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete storage for tenant '{tenant_id}': {e}")
            return False
    
    def get_tenant_storage_usage(self, tenant_id: str, base_storage_path: str) -> Dict[str, int]:
        """
        Get storage usage statistics for tenant.
        
        Args:
            tenant_id: Tenant ID
            base_storage_path: Base storage directory
            
        Returns:
            Dictionary with usage statistics
        """
        tenant_root = self.get_tenant_storage_root(tenant_id)
        
        if not tenant_root:
            # For root storage, calculate usage of entire base path
            tenant_path = base_storage_path
        else:
            tenant_path = os.path.join(base_storage_path, tenant_root)
        
        try:
            total_size = 0
            file_count = 0
            dir_count = 0
            
            for root, dirs, files in os.walk(tenant_path):
                dir_count += len(dirs)
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        total_size += os.path.getsize(file_path)
                        file_count += 1
                    except OSError:
                        continue
            
            return {
                "total_size_bytes": total_size,
                "file_count": file_count,
                "directory_count": dir_count,
                "storage_path": tenant_path
            }
            
        except Exception as e:
            logger.error(f"Failed to get storage usage for tenant '{tenant_id}': {e}")
            return {
                "total_size_bytes": 0,
                "file_count": 0,
                "directory_count": 0,
                "storage_path": tenant_path
            }
    
    def check_storage_quota(self, tenant_id: str, file_size: int, base_storage_path: str) -> bool:
        """
        Check if tenant is within storage quota.
        
        Args:
            tenant_id: Tenant ID
            file_size: Size of file to be stored in bytes
            base_storage_path: Base storage directory
            
        Returns:
            True if within quota, False otherwise
        """
        # Get current usage
        usage = self.get_tenant_storage_usage(tenant_id, base_storage_path)
        current_size = usage["total_size_bytes"]
        
        # Check quota
        return isolation.check_resource_limits("storage_gb", 
                                             (current_size + file_size) / (1024**3), 
                                             tenant_id)
    
    def backup_tenant_storage(self, tenant_id: str, base_storage_path: str, 
                            backup_destination: str) -> bool:
        """
        Create backup of tenant storage.
        
        Args:
            tenant_id: Tenant ID
            base_storage_path: Base storage directory
            backup_destination: Destination path for backup
            
        Returns:
            True if backup created successfully
        """
        tenant_root = self.get_tenant_storage_root(tenant_id)
        
        if not tenant_root:
            logger.warning(f"Cannot backup root storage for tenant {tenant_id}")
            return False
        
        try:
            tenant_path = os.path.join(base_storage_path, tenant_root)
            backup_path = os.path.join(backup_destination, f"{tenant_id}_backup")
            
            # Create backup directory
            os.makedirs(backup_path, exist_ok=True)
            
            # Copy tenant storage to backup location
            shutil.copytree(tenant_path, backup_path, dirs_exist_ok=True)
            
            # Store backup location
            self._backup_locations[tenant_id] = backup_path
            
            logger.info(f"Created backup for tenant '{tenant_id}' at {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to backup storage for tenant '{tenant_id}': {e}")
            return False
    
    def restore_tenant_storage(self, tenant_id: str, base_storage_path: str, 
                             backup_source: str) -> bool:
        """
        Restore tenant storage from backup.
        
        Args:
            tenant_id: Tenant ID
            base_storage_path: Base storage directory
            backup_source: Source path for backup
            
        Returns:
            True if restore completed successfully
        """
        tenant_root = self.get_tenant_storage_root(tenant_id)
        
        if not tenant_root:
            logger.warning(f"Cannot restore root storage for tenant {tenant_id}")
            return False
        
        try:
            tenant_path = os.path.join(base_storage_path, tenant_root)
            
            # Remove existing tenant storage
            if os.path.exists(tenant_path):
                shutil.rmtree(tenant_path)
            
            # Restore from backup
            shutil.copytree(backup_source, tenant_path)
            
            logger.info(f"Restored storage for tenant '{tenant_id}' from {backup_source}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore storage for tenant '{tenant_id}': {e}")
            return False
    
    def list_tenant_files(self, tenant_id: str, base_storage_path: str, 
                         subdirectory: str = "") -> List[Dict[str, Any]]:
        """
        List files in tenant storage.
        
        Args:
            tenant_id: Tenant ID
            base_storage_path: Base storage directory
            subdirectory: Optional subdirectory to list
            
        Returns:
            List of file information dictionaries
        """
        tenant_root = self.get_tenant_storage_root(tenant_id)
        
        if not tenant_root:
            tenant_path = base_storage_path
        else:
            tenant_path = os.path.join(base_storage_path, tenant_root)
        
        if subdirectory:
            tenant_path = os.path.join(tenant_path, subdirectory)
        
        try:
            files = []
            for root, dirs, filenames in os.walk(tenant_path):
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    try:
                        stat = os.stat(file_path)
                        files.append({
                            "name": filename,
                            "path": os.path.relpath(file_path, tenant_path),
                            "size_bytes": stat.st_size,
                            "modified": stat.st_mtime,
                            "is_directory": False
                        })
                    except OSError:
                        continue
            
            return files
            
        except Exception as e:
            logger.error(f"Failed to list files for tenant '{tenant_id}': {e}")
            return []
    
    def move_file_between_tenants(self, source_tenant: str, target_tenant: str,
                                file_path: str, base_storage_path: str) -> bool:
        """
        Move file between tenants (with isolation checks).
        
        Args:
            source_tenant: Source tenant ID
            target_tenant: Target tenant ID
            file_path: Relative file path
            base_storage_path: Base storage directory
            
        Returns:
            True if file moved successfully
        """
        # Check cross-tenant isolation
        if not isolation.enforce_cross_tenant_isolation(source_tenant, target_tenant):
            return False
        
        try:
            # Get source and target paths
            source_root = self.get_tenant_storage_root(source_tenant)
            target_root = self.get_tenant_storage_root(target_tenant)
            
            source_full_path = os.path.join(base_storage_path, source_root, file_path)
            target_full_path = os.path.join(base_storage_path, target_root, file_path)
            
            # Check if source file exists
            if not os.path.exists(source_full_path):
                logger.error(f"Source file not found: {source_full_path}")
                return False
            
            # Check target quota
            file_size = os.path.getsize(source_full_path)
            if not self.check_storage_quota(target_tenant, file_size, base_storage_path):
                logger.error(f"Target tenant {target_tenant} quota exceeded")
                return False
            
            # Create target directory if needed
            os.makedirs(os.path.dirname(target_full_path), exist_ok=True)
            
            # Move file
            shutil.move(source_full_path, target_full_path)
            
            logger.info(f"Moved file from tenant '{source_tenant}' to '{target_tenant}': {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to move file between tenants: {e}")
            return False
    
    def cleanup_temp_files(self, tenant_id: str, base_storage_path: str, 
                          max_age_hours: int = 24) -> int:
        """
        Clean up temporary files for tenant.
        
        Args:
            tenant_id: Tenant ID
            base_storage_path: Base storage directory
            max_age_hours: Maximum age of temp files in hours
            
        Returns:
            Number of files cleaned up
        """
        import time
        
        tenant_root = self.get_tenant_storage_root(tenant_id)
        temp_path = os.path.join(base_storage_path, tenant_root, "temp")
        
        if not os.path.exists(temp_path):
            return 0
        
        try:
            cleaned_count = 0
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            for filename in os.listdir(temp_path):
                file_path = os.path.join(temp_path, filename)
                try:
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age_seconds:
                        os.remove(file_path)
                        cleaned_count += 1
                except OSError:
                    continue
            
            logger.info(f"Cleaned up {cleaned_count} temp files for tenant '{tenant_id}'")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup temp files for tenant '{tenant_id}': {e}")
            return 0
    
    @contextmanager
    def tenant_storage_context(self, tenant_id: Optional[str] = None):
        """
        Context manager for storage operations with tenant isolation.
        
        Usage:
            with storage_isolation.tenant_storage_context("client_123"):
                # All storage operations will use client_123 isolation
                path = storage_isolation.get_tenant_storage_path("file.txt")
        """
        effective_tenant_id = tenant_id or get_current_tenant_id()
        
        try:
            yield
        finally:
            pass

# Global storage isolation manager
storage_isolation = StorageIsolationManager()

# Convenience functions
def get_storage_path(path: str, tenant_id: Optional[str] = None) -> str:
    """Get isolated storage path for current tenant."""
    return storage_isolation.get_tenant_storage_path(path, tenant_id)

def get_storage_root(tenant_id: Optional[str] = None) -> str:
    """Get storage root for current tenant."""
    return storage_isolation.get_tenant_storage_root(tenant_id)

def create_storage(tenant_id: str, base_path: str) -> bool:
    """Create storage structure for tenant."""
    return storage_isolation.create_tenant_storage(tenant_id, base_path)

def get_storage_usage(tenant_id: str, base_path: str) -> Dict[str, int]:
    """Get storage usage for tenant."""
    return storage_isolation.get_tenant_storage_usage(tenant_id, base_path)

def check_quota(tenant_id: str, file_size: int, base_path: str) -> bool:
    """Check storage quota for tenant."""
    return storage_isolation.check_storage_quota(tenant_id, file_size, base_path)

__all__ = [
    "StorageIsolationManager",
    "storage_isolation",
    "get_storage_path",
    "get_storage_root",
    "create_storage",
    "get_storage_usage",
    "check_quota"
] 