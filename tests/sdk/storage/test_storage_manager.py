"""
Tests for the unified StorageManager class.
"""
import tempfile
import pytest
from tausestack.sdk.storage.main import StorageManager
from tausestack.sdk.storage.backends import LocalStorage

class TestStorageManager:
    """Test the unified StorageManager interface."""
    
    def test_storage_manager_initialization(self):
        """Test that StorageManager initializes correctly."""
        manager = StorageManager()
        assert manager is not None
        assert hasattr(manager, '_backend')
        assert hasattr(manager, '_json_client')
        assert hasattr(manager, '_binary_client')
    
    def test_storage_manager_with_custom_backend(self):
        """Test StorageManager with a custom backend."""
        backend = LocalStorage(
            base_json_path=tempfile.mkdtemp(),
            base_binary_path=tempfile.mkdtemp(),
            base_dataframe_path=tempfile.mkdtemp()
        )
        manager = StorageManager(backend=backend)
        assert manager._backend is backend
    
    def test_json_operations(self):
        """Test JSON operations through StorageManager."""
        backend = LocalStorage(
            base_json_path=tempfile.mkdtemp(),
            base_binary_path=tempfile.mkdtemp(),
            base_dataframe_path=tempfile.mkdtemp()
        )
        manager = StorageManager(backend=backend)
        
        # Test put and get
        test_data = {"name": "John", "age": 30, "city": "Madrid"}
        key = "user/123"
        
        manager.put_json(key, test_data)
        retrieved = manager.get_json(key)
        assert retrieved == test_data
        
        # Test delete
        manager.delete_json(key)
        assert manager.get_json(key) is None
    
    def test_binary_operations(self):
        """Test binary operations through StorageManager."""
        backend = LocalStorage(
            base_json_path=tempfile.mkdtemp(),
            base_binary_path=tempfile.mkdtemp(),
            base_dataframe_path=tempfile.mkdtemp()
        )
        manager = StorageManager(backend=backend)
        
        # Test put and get
        test_data = b"Hello, world! This is binary data."
        key = "files/test.bin"
        
        manager.put_binary(key, test_data)
        retrieved = manager.get_binary(key)
        assert retrieved == test_data
        
        # Test with content type
        manager.put_binary(key, test_data, content_type="application/octet-stream")
        retrieved = manager.get_binary(key)
        assert retrieved == test_data
        
        # Test delete
        manager.delete_binary(key)
        assert manager.get_binary(key) is None
    
    def test_client_properties(self):
        """Test access to client properties."""
        manager = StorageManager()
        
        # Test json client access
        json_client = manager.json
        assert json_client is not None
        assert hasattr(json_client, 'get')
        assert hasattr(json_client, 'put')
        assert hasattr(json_client, 'delete')
        
        # Test binary client access
        binary_client = manager.binary
        assert binary_client is not None
        assert hasattr(binary_client, 'get')
        assert hasattr(binary_client, 'put')
        assert hasattr(binary_client, 'delete')
        
        # Test dataframe client access
        dataframe_client = manager.dataframe
        # May be None if pandas is not installed
        if dataframe_client:
            assert hasattr(dataframe_client, 'get')
            assert hasattr(dataframe_client, 'put')
            assert hasattr(dataframe_client, 'delete')
    
    def test_dataframe_operations_without_pandas(self):
        """Test that DataFrame operations raise appropriate errors without pandas."""
        backend = LocalStorage(
            base_json_path=tempfile.mkdtemp(),
            base_binary_path=tempfile.mkdtemp(),
            base_dataframe_path=tempfile.mkdtemp()
        )
        manager = StorageManager(backend=backend)
        
        # If pandas is not available, these should raise ImportError
        if manager._dataframe_client is None:
            with pytest.raises(ImportError, match="pandas and pyarrow are required"):
                manager.get_dataframe("test")
            
            with pytest.raises(ImportError, match="pandas and pyarrow are required"):
                manager.put_dataframe("test", None)  # type: ignore
            
            with pytest.raises(ImportError, match="pandas and pyarrow are required"):
                manager.delete_dataframe("test")
    
    def test_key_validation_through_manager(self):
        """Test that key validation works through StorageManager."""
        backend = LocalStorage(
            base_json_path=tempfile.mkdtemp(),
            base_binary_path=tempfile.mkdtemp(),
            base_dataframe_path=tempfile.mkdtemp()
        )
        manager = StorageManager(backend=backend)
        
        # Valid keys should work
        valid_key = "valid/path/file"
        test_data = {"test": "data"}
        manager.put_json(valid_key, test_data)
        assert manager.get_json(valid_key) == test_data
        manager.delete_json(valid_key)
        
        # Invalid keys should raise ValueError
        invalid_keys = ["../evil", "/absolute", "bad*key", "space key"]
        for invalid_key in invalid_keys:
            with pytest.raises(ValueError):
                manager.put_json(invalid_key, test_data)
            
            with pytest.raises(ValueError):
                manager.get_json(invalid_key)
            
            with pytest.raises(ValueError):
                manager.delete_json(invalid_key) 