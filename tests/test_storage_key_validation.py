import os
import tempfile
import pytest
from tausestack.sdk.storage.backends import LocalStorage

def test_valid_keys():
    """Test that valid keys work correctly."""
    storage = LocalStorage(
        base_json_path=tempfile.mkdtemp(),
        base_binary_path=tempfile.mkdtemp(),
        base_dataframe_path=tempfile.mkdtemp()
    )
    
    valid_keys = [
        "simple.txt",
        "folder/file.txt", 
        "nested/deep/path/file.txt",
        "file_with-dashes.txt",
        "file.with.dots.txt",
        "123numbers.txt",
        "MixedCase.txt"
    ]
    
    for key in valid_keys:
        # Should not raise any exceptions
        data = b"test data"
        storage.put_binary(key, data)
        retrieved = storage.get_binary(key)
        assert retrieved == data
        storage.delete_binary(key)

def test_invalid_key_regex():
    """Test that invalid keys are rejected by regex validation."""
    storage = LocalStorage(
        base_json_path=tempfile.mkdtemp(),
        base_binary_path=tempfile.mkdtemp(),
        base_dataframe_path=tempfile.mkdtemp()
    )
    
    invalid_keys = [
        "inva|id.txt", 
        "bad*name.bin", 
        "white space.txt", 
        "ç.txt", 
        "a/bad\\path.txt",
        "emoji😀.txt",
        "special@char.txt",
        "percent%.txt"
    ]
    
    for key in invalid_keys:
        with pytest.raises(ValueError, match="Invalid key format"):
            storage.put_binary(key, b"data")
        with pytest.raises(ValueError, match="Invalid key format"):
            storage.get_binary(key)
        with pytest.raises(ValueError, match="Invalid key format"):
            storage.delete_binary(key)

def test_invalid_key_path_traversal():
    """Test that path traversal attempts are rejected."""
    storage = LocalStorage(
        base_json_path=tempfile.mkdtemp(),
        base_binary_path=tempfile.mkdtemp(),
        base_dataframe_path=tempfile.mkdtemp()
    )
    
    # Keys that will be caught by path traversal check
    path_traversal_keys = [
        "../evil.txt", 
        "/abs/path.txt", 
        "folder/../../escape.txt",
        "folder/../escape.txt"
    ]
    
    # Keys that will be caught by regex check first  
    regex_invalid_keys = [
        "..\\windows\\path.txt"  # backslashes not allowed in regex
    ]
    
    for key in path_traversal_keys:
        with pytest.raises(ValueError, match="No absolute paths"):
            storage.put_binary(key, b"data")
        with pytest.raises(ValueError, match="No absolute paths"):
            storage.get_binary(key)
        with pytest.raises(ValueError, match="No absolute paths"):
            storage.delete_binary(key)
    
    for key in regex_invalid_keys:
        with pytest.raises(ValueError, match="Invalid key format"):
            storage.put_binary(key, b"data")
        with pytest.raises(ValueError, match="Invalid key format"):
            storage.get_binary(key)
        with pytest.raises(ValueError, match="Invalid key format"):
            storage.delete_binary(key)

def test_json_validation():
    """Test that JSON operations also validate keys."""
    storage = LocalStorage(
        base_json_path=tempfile.mkdtemp(),
        base_binary_path=tempfile.mkdtemp(),
        base_dataframe_path=tempfile.mkdtemp()
    )
    
    # Valid key should work
    valid_key = "valid/json/file"
    data = {"test": "data"}
    storage.put_json(valid_key, data)
    retrieved = storage.get_json(valid_key)
    assert retrieved == data
    storage.delete_json(valid_key)
    
    # Invalid key should fail
    invalid_key = "../invalid.json"
    with pytest.raises(ValueError):
        storage.put_json(invalid_key, data)

def test_nested_directory_creation():
    """Test that nested directories are created correctly."""
    temp_base = tempfile.mkdtemp()
    storage = LocalStorage(
        base_json_path=temp_base + "/json",
        base_binary_path=temp_base + "/binary", 
        base_dataframe_path=temp_base + "/dataframe"
    )
    
    nested_key = "very/deep/nested/path/file"
    data = b"nested data"
    
    storage.put_binary(nested_key, data)
    retrieved = storage.get_binary(nested_key)
    assert retrieved == data
    
    # Verify the directory structure was created
    expected_path = os.path.join(temp_base, "binary", "very", "deep", "nested", "path", "file")
    assert os.path.exists(expected_path)
