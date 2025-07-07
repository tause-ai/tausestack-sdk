# Tests for AWSSecretsManagerProvider in tausestack.sdk.secrets.providers
import pytest
import os
import boto3
from moto import mock_aws
import base64

from tausestack.sdk.secrets.providers import AWSSecretsManagerProvider

@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1" # Moto needs a region

@pytest.fixture(scope="function")
def secretsmanager_client_fixture(aws_credentials):
    """Provides a mocked Secrets Manager client using moto."""
    with mock_aws():
        client = boto3.client("secretsmanager", region_name=os.environ["AWS_DEFAULT_REGION"])
        yield client

@pytest.fixture
def aws_secrets_provider(secretsmanager_client_fixture):
    """Provides an AWSSecretsManagerProvider instance with a mocked client."""
    return AWSSecretsManagerProvider(secrets_manager_client=secretsmanager_client_fixture)

# --- Test Cases ---

def test_get_secret_string(aws_secrets_provider: AWSSecretsManagerProvider, secretsmanager_client_fixture):
    secret_name = "MyTestSecretString"
    secret_value = "supersecretvalue"
    secretsmanager_client_fixture.create_secret(Name=secret_name, SecretString=secret_value)

    retrieved_value = aws_secrets_provider.get(secret_name)
    assert retrieved_value == secret_value

    secretsmanager_client_fixture.delete_secret(SecretId=secret_name, ForceDeleteWithoutRecovery=True)

def test_get_secret_binary(aws_secrets_provider: AWSSecretsManagerProvider, secretsmanager_client_fixture):
    secret_name = "MyTestSecretBinary"
    original_binary_data = b"binary\x00\x01data"
    # Secrets Manager stores binary data as base64 encoded string in the API response for SecretBinary
    # but the SDK should handle the decoding.
    # For create_secret, SecretBinary expects bytes.
    secretsmanager_client_fixture.create_secret(Name=secret_name, SecretBinary=original_binary_data)

    retrieved_value = aws_secrets_provider.get(secret_name)
    # The provider's get() method should return the decoded string if it was binary
    # or the direct string if it was SecretString. AWS SDK decodes binary to string by default.
    # If the binary data is not valid UTF-8, this might be an issue or require specific handling.
    # For this test, assuming it's a UTF-8 representable binary for simplicity, or that the provider handles it.
    # Let's check what the provider actually does. The current implementation decodes 'utf-8'.
    assert retrieved_value == original_binary_data.decode('utf-8', errors='replace')

    secretsmanager_client_fixture.delete_secret(SecretId=secret_name, ForceDeleteWithoutRecovery=True)

def test_get_secret_not_found(aws_secrets_provider: AWSSecretsManagerProvider):
    secret_name = "NonExistentSecret"
    retrieved_value = aws_secrets_provider.get(secret_name)
    assert retrieved_value is None

def test_aws_provider_instantiation_with_default_client(aws_credentials):
    """Test AWSSecretsManagerProvider instantiation without an explicit client."""
    secret_name = "DefaultClientSecret"
    secret_value = "default_client_works"
    with mock_aws():
        # Need to use a temporary client to create the secret for the test
        temp_sm_client = boto3.client("secretsmanager", region_name=os.environ["AWS_DEFAULT_REGION"])
        temp_sm_client.create_secret(Name=secret_name, SecretString=secret_value)

        provider = AWSSecretsManagerProvider() # Instantiate with default client
        assert provider.client is not None
        retrieved_value = provider.get(secret_name)
        assert retrieved_value == secret_value

        temp_sm_client.delete_secret(SecretId=secret_name, ForceDeleteWithoutRecovery=True)

def test_get_secret_string_special_chars(aws_secrets_provider: AWSSecretsManagerProvider, secretsmanager_client_fixture):
    secret_name = "MySpecialCharSecret"
    secret_value = "{\"key\": \"value with spaces and !@#$%^&*()\"}"
    secretsmanager_client_fixture.create_secret(Name=secret_name, SecretString=secret_value)

    retrieved_value = aws_secrets_provider.get(secret_name)
    assert retrieved_value == secret_value

    secretsmanager_client_fixture.delete_secret(SecretId=secret_name, ForceDeleteWithoutRecovery=True)
