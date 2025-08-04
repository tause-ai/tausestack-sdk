import os
import logging

logger = logging.getLogger(__name__)
from typing import Optional

from .base import AbstractSecretsProvider

class EnvironmentVariablesProvider(AbstractSecretsProvider):
    """Retrieves secrets from environment variables."""

    def get(self, secret_name: str) -> Optional[str]:
        """Gets the secret value from an environment variable.

        Args:
            secret_name: The name of the environment variable.

        Returns:
            The secret value if the environment variable is set, otherwise None.
        """
        value = os.getenv(secret_name)
        if value is not None:
            logger.debug(f"Retrieved secret '{secret_name}' from environment variable.")
        else:
            logger.debug(f"Secret '{secret_name}' not found in environment variables.")
        return value


try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    class ClientError(Exception): pass # Dummy for type hinting

class AWSSecretsManagerProvider(AbstractSecretsProvider):
    """Retrieves secrets from AWS Secrets Manager."""

    def __init__(self, region_name: Optional[str] = None, secrets_manager_client=None):
        """
        Initializes the AWSSecretsManagerProvider.

        Args:
            region_name: Optional AWS region name. If None, boto3 will attempt to determine it.
            secrets_manager_client: Optional pre-configured boto3 Secrets Manager client for testing.
        """
        if not BOTO3_AVAILABLE:
            logger.critical("boto3 is required for AWSSecretsManagerProvider but is not installed.")
            raise ImportError("boto3 is required for AWSSecretsManagerProvider. Please install it: pip install boto3")

        self.region_name = region_name or os.getenv('AWS_REGION') or os.getenv('AWS_DEFAULT_REGION')
        # If region_name is still None, boto3 client might pick it up from shared config or IAM role, or fail.
        self.client = secrets_manager_client if secrets_manager_client else boto3.client(
            service_name='secretsmanager',
            region_name=self.region_name
        )
        logger.debug(f"AWSSecretsManagerProvider initialized. Region: {self.region_name if self.region_name else 'determined by boto3'}. Custom client provided: {secrets_manager_client is not None}")

    def get(self, secret_name: str) -> Optional[str]:
        """Gets the secret value from AWS Secrets Manager.

        Args:
            secret_name: The name or ARN of the secret.

        Returns:
            The secret string if found, otherwise None.
            Note: AWS Secrets Manager can store binary secrets too, but this provider
                  currently assumes string secrets. For binary, use get_secret_binary.
        """
        try:
            get_secret_value_response = self.client.get_secret_value(SecretId=secret_name)
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            if error_code == 'ResourceNotFoundException':
                logger.warning(f"Secret '{secret_name}' not found in AWS Secrets Manager.")
                return None
            elif error_code == 'InvalidParameterException':
                logger.error(f"Invalid secret name/ARN '{secret_name}' for AWS Secrets Manager. Error details: {e}", exc_info=True)
                return None
            elif error_code == 'DecryptionFailure':
                logger.error(f"Decryption failure for secret '{secret_name}' in AWS Secrets Manager. Error details: {e}", exc_info=True)
                raise
            else:
                logger.error(f"Error retrieving secret '{secret_name}' from AWS Secrets Manager: {e}", exc_info=True)
                raise
        else:
            # Decrypts secret using the associated KMS CMK.
            # Depending on whether the secret is a string or binary, one of these fields will be populated.
            if 'SecretString' in get_secret_value_response:
                secret_value = get_secret_value_response['SecretString']
                logger.debug(f"Retrieved SecretString for '{secret_name}' from AWS Secrets Manager.")
                return secret_value
            elif 'SecretBinary' in get_secret_value_response:
                logger.debug(f"Retrieved SecretBinary for '{secret_name}' from AWS Secrets Manager. Decoding as UTF-8 (errors='replace').")
                decoded_binary = get_secret_value_response['SecretBinary'].decode('utf-8', errors='replace')
                return decoded_binary
            else:
                logger.warning(f"Secret '{secret_name}' retrieved from AWS Secrets Manager but contained neither SecretString nor SecretBinary.")
                return None
