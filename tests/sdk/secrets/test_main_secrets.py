# Tests for secrets main logic in tausestack.sdk.secrets.main
import pytest
import os
import importlib
from unittest.mock import patch

# Correctly import the main module from the 'secrets' package directory
from tausestack.sdk.secrets import main as secrets_main_module

@pytest.fixture(autouse=True)
def manage_global_secrets_provider():
    """
    Fixture to manage and re-initialize the global secrets provider from
    tausestack.sdk.secrets.main for each test, configured for environment variables.
    """
    original_provider_instance = getattr(secrets_main_module, '_secrets_provider_instance', None)

    env_vars = {
        "TAUSESTACK_SECRETS_BACKEND": "env",
    }

    with patch.dict(os.environ, env_vars):
        # Reset global state in the module before reloading
        secrets_main_module._secrets_provider_instance = None
        
        # Reload the module to pick up new env vars and re-initialize the provider logic
        importlib.reload(secrets_main_module)
        
        yield # Test runs here

    # Teardown: Restore original state or ensure clean state for next test
    secrets_main_module._secrets_provider_instance = original_provider_instance


def test_get_secret_existing_env_var():
    """
    Test that secrets_main_module.get_secret retrieves an existing environment variable.
    """
    secret_name = "MY_MAIN_TEST_SECRET"
    secret_value = "s3cr3t_v4lu3_for_main_test"
    
    with patch.dict(os.environ, {secret_name: secret_value, "TAUSESTACK_SECRETS_BACKEND": "env"}):
        # Ensure the module is reloaded if os.environ changed after the fixture's reload
        # This is particularly important if a test case modifies os.environ directly for its specific scenario
        # after the autouse fixture has already run.
        importlib.reload(secrets_main_module) 
        retrieved_value = secrets_main_module.get_secret(secret_name)
        assert retrieved_value == secret_value

def test_get_secret_non_existent_env_var():
    """Test secrets_main_module.get_secret returns None for a non-existent environment variable."""
    secret_name = "NON_EXISTENT_MAIN_SECRET_XYZ"
    
    # Ensure the variable is not set for this test
    # The patch.dict in the fixture already sets the backend, 
    # we just need to ensure this specific secret_name is not in os.environ
    current_env = os.environ.copy()
    if secret_name in current_env:
        del current_env[secret_name]
    current_env["TAUSESTACK_SECRETS_BACKEND"] = "env"

    with patch.dict(os.environ, current_env, clear=True):
        importlib.reload(secrets_main_module)
        retrieved_value = secrets_main_module.get_secret(secret_name)
        assert retrieved_value is None

def test_get_secret_empty_value_env_var():
    """Test secrets_main_module.get_secret returns an empty string for an env var with an empty value."""
    secret_name = "EMPTY_VALUE_MAIN_SECRET"
    secret_value = ""
    
    with patch.dict(os.environ, {secret_name: secret_value, "TAUSESTACK_SECRETS_BACKEND": "env"}):
        importlib.reload(secrets_main_module)
        retrieved_value = secrets_main_module.get_secret(secret_name)
        assert retrieved_value == secret_value

def test_get_secret_backend_not_specified_defaults_to_env():
    """Test that if TAUSESTACK_SECRETS_BACKEND is not set, it defaults to 'env'."""
    secret_name = "DEFAULT_BACKEND_SECRET"
    secret_value = "default_value"

    # Ensure TAUSESTACK_SECRETS_BACKEND is NOT in the environment for this test
    # The fixture sets it, so we need to override that within the test's context.
    env_without_backend_spec = os.environ.copy()
    if "TAUSESTACK_SECRETS_BACKEND" in env_without_backend_spec:
        del env_without_backend_spec["TAUSESTACK_SECRETS_BACKEND"]
        # Corrected in next thought block
    env_without_backend_spec[secret_name] = secret_value

    with patch.dict(os.environ, env_without_backend_spec, clear=True):
        # Critical: reload module so it picks up the modified os.environ (without backend spec)
        importlib.reload(secrets_main_module)
        retrieved_value = secrets_main_module.get_secret(secret_name)
        assert retrieved_value == secret_value
