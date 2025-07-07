"""
Storage Exceptions

Defines custom exceptions for the storage module.
"""

class StorageException(Exception):
    """Base exception for storage operations."""
    pass

class StorageBackendException(StorageException):
    """Exception raised when storage backend operations fail."""
    pass

class StorageQuotaExceededException(StorageException):
    """Exception raised when storage quota is exceeded."""
    pass

class StorageKeyValidationException(StorageException):
    """Exception raised when storage key validation fails."""
    pass

class StorageSerializationException(StorageException):
    """Exception raised when data serialization/deserialization fails."""
    pass

class StorageConnectionException(StorageException):
    """Exception raised when connection to storage backend fails."""
    pass

class StoragePermissionException(StorageException):
    """Exception raised when permission to access storage is denied."""
    pass

class StorageNotFoundException(StorageException):
    """Exception raised when storage resource is not found."""
    pass

__all__ = [
    "StorageException",
    "StorageBackendException", 
    "StorageQuotaExceededException",
    "StorageKeyValidationException",
    "StorageSerializationException",
    "StorageConnectionException",
    "StoragePermissionException",
    "StorageNotFoundException"
] 