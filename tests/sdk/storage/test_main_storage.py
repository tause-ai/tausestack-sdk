# Tests for JsonClient in tausestack.sdk.storage.main
import pytest
import os
import json
from pathlib import Path
import importlib
from unittest.mock import patch

from tausestack.sdk.storage import main as storage_main_module

@pytest.fixture
def temp_storage_path(tmp_path: Path) -> Path:
    """Create a temporary directory for local storage tests."""
    storage_dir = tmp_path / "sdk_storage_main_tests"
    storage_dir.mkdir()
    return storage_dir

@pytest.fixture(autouse=True)
def manage_global_json_client(temp_storage_path: Path):
    """
    Fixture to manage and re-initialize the global json_client from
    tausestack.sdk.storage.main for each test, configured for local storage.
    """
    # Store original state to restore after test
    original_provider_instance = getattr(storage_main_module, '_storage_provider_instance', None)
    original_client_provider = None
    if hasattr(storage_main_module, 'json_client') and storage_main_module.json_client is not None:
        original_client_provider = getattr(storage_main_module.json_client, '_provider', None)

    env_vars = {
        "TAUSESTACK_STORAGE_BACKEND": "local",
        "TAUSESTACK_LOCAL_JSON_STORAGE_PATH": str(temp_storage_path / "json"),
        "TAUSESTACK_LOCAL_BINARY_STORAGE_PATH": str(temp_storage_path / "binary"),
        "TAUSESTACK_LOCAL_DATAFRAME_STORAGE_PATH": str(temp_storage_path / "dataframe")
    }

    with patch.dict(os.environ, env_vars):
        # Reset global state in the module before reloading
        storage_main_module._storage_provider_instance = None
        if hasattr(storage_main_module, 'json_client') and storage_main_module.json_client is not None:
             storage_main_module.json_client._provider = None

        # Reload the module to pick up new env vars and re-initialize the client
        importlib.reload(storage_main_module)
        
        yield # Test runs here

    # Teardown: Restore original state or ensure clean state for next test
    storage_main_module._storage_provider_instance = original_provider_instance
    if hasattr(storage_main_module, 'json_client') and storage_main_module.json_client is not None:
        storage_main_module.json_client._provider = original_client_provider
    
    # If the original was None (first run or cleared by previous test), ensure it's fully reset
    if original_provider_instance is None and hasattr(storage_main_module, 'json_client') and storage_main_module.json_client is not None:
         storage_main_module.json_client._provider = None


def test_json_client_put_and_get(temp_storage_path: Path):
    """
    Test that json_client.put correctly stores data and json_client.get retrieves it,
    using the re-initialized global client with LocalJsonStorage.
    """
    client = storage_main_module.json_client # Use the reloaded client
    key = "test_data"
    data = {"message": "Hello, SDK!", "version": 1}

    client.put(key, data)

    expected_file = temp_storage_path / "json" / (key + ".json")
    assert expected_file.exists()
    with open(expected_file, 'r', encoding='utf-8') as f:
        stored_data = json.load(f)
    assert stored_data == data

    retrieved_data = client.get(key)
    assert retrieved_data == data

def test_json_client_get_non_existent(temp_storage_path: Path):
    """Test json_client.get returns None for a non-existent key."""
    client = storage_main_module.json_client
    key = "non_existent_key"
    assert client.get(key) is None

def test_json_client_delete(temp_storage_path: Path):
    """Test json_client.delete removes the data."""
    client = storage_main_module.json_client
    key = "to_be_deleted"
    data = {"status": "ephemeral"}

    client.put(key, data)
    expected_file = temp_storage_path / "json" / (key + ".json")
    assert expected_file.exists() # Confirm creation

    client.delete(key)
    assert not expected_file.exists() # Confirm deletion
    assert client.get(key) is None # Confirm get returns None

def test_json_client_put_overwrite(temp_storage_path: Path):
    """Test that json_client.put overwrites existing data for the same key."""
    client = storage_main_module.json_client
    key = "overwrite_test"
    initial_data = {"value": "initial"}
    updated_data = {"value": "updated"}

    client.put(key, initial_data)
    assert client.get(key) == initial_data

    client.put(key, updated_data)
    assert client.get(key) == updated_data

    expected_file = temp_storage_path / "json" / (key + ".json")
    with open(expected_file, 'r', encoding='utf-8') as f:
        stored_data = json.load(f)
    assert stored_data == updated_data

def test_json_client_nested_key_paths(temp_storage_path: Path):
    """Test json_client with keys that imply directory structures."""
    client = storage_main_module.json_client
    key = "nested/path/to/data"
    data = {"detail": "deeply_stored"}

    client.put(key, data)

    expected_file = temp_storage_path / "json" / "nested" / "path" / "to" / "data.json"
    assert expected_file.exists()
    with open(expected_file, 'r', encoding='utf-8') as f:
        stored_data = json.load(f)
    assert stored_data == data

    assert client.get(key) == data

    client.delete(key)
    assert not expected_file.exists()
    assert client.get(key) is None
