# Tests for EnvironmentVariablesProvider
import pytest
import os
from unittest.mock import patch

from tausestack.sdk.secrets.providers import EnvironmentVariablesProvider

@pytest.fixture
def env_provider():
    """Provides an instance of EnvironmentVariablesProvider."""
    return EnvironmentVariablesProvider()

def test_get_existing_secret(env_provider: EnvironmentVariablesProvider):
    """
    Verifica que se puede obtener el valor de una variable de entorno existente.
    """
    secret_name = "MY_TEST_SECRET"
    secret_value = "s3cr3t_v4lu3"
    
    with patch.dict(os.environ, {secret_name: secret_value}):
        retrieved_value = env_provider.get(secret_name)
        assert retrieved_value == secret_value

def test_get_non_existent_secret(env_provider: EnvironmentVariablesProvider):
    """
    Verifica que al intentar obtener una variable de entorno que no existe,
    se devuelve None.
    """
    secret_name = "NON_EXISTENT_SECRET_XYZ"
    
    # Asegurarse de que la variable no está en el entorno para esta prueba específica
    # Usamos clear=True para empezar con un os.environ 'limpio' dentro del contexto de patch.dict
    # y luego nos aseguramos de que la clave específica no esté.
    # Esto es más robusto que simplemente eliminarla si existiera globalmente.
    current_env = os.environ.copy()
    if secret_name in current_env:
        del current_env[secret_name]

    with patch.dict(os.environ, current_env, clear=True):
        retrieved_value = env_provider.get(secret_name)
        assert retrieved_value is None

def test_get_secret_with_empty_value(env_provider: EnvironmentVariablesProvider):
    """
    Verifica el comportamiento si una variable de entorno existe pero tiene
    un valor vacío (debería devolver la cadena vacía).
    """
    secret_name = "EMPTY_VALUE_SECRET"
    secret_value = "" # Valor vacío
    
    with patch.dict(os.environ, {secret_name: secret_value}):
        retrieved_value = env_provider.get(secret_name)
        assert retrieved_value == secret_value

def test_get_secret_case_sensitivity(env_provider: EnvironmentVariablesProvider):
    """
    Verifica que la obtención de secretos es sensible a mayúsculas/minúsculas
    (comportamiento estándar de las variables de entorno).
    """
    secret_name_upper = "CASE_SENSITIVE_SECRET"
    secret_name_lower = "case_sensitive_secret"
    secret_value = "ValueForUpperCase"

    # Empezar con un entorno limpio para esta prueba y añadir solo la variable en mayúsculas
    with patch.dict(os.environ, {secret_name_upper: secret_value}, clear=True):
        # Obtener con el nombre exacto (mayúsculas)
        assert env_provider.get(secret_name_upper) == secret_value
        # Intentar obtener con el nombre en minúsculas (debería ser None)
        assert env_provider.get(secret_name_lower) is None
