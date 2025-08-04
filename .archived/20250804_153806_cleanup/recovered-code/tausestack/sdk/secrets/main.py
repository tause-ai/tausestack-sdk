from typing import Optional, Type, Dict, Any
import logging

logger = logging.getLogger(__name__)
import os

from .base import AbstractSecretsProvider
from .providers import EnvironmentVariablesProvider, AWSSecretsManagerProvider

_secrets_provider_instance: Optional[AbstractSecretsProvider] = None

def _get_secrets_provider_instance(provider_class: Optional[Type[AbstractSecretsProvider]] = None, config: Optional[Dict[str, Any]] = None) -> AbstractSecretsProvider:
    """Initializes and returns a singleton instance of the secrets provider."""
    global _secrets_provider_instance
    if _secrets_provider_instance is None:
        logger.debug("Attempting to initialize secrets provider instance.")
        resolved_config = config or {}
        if provider_class:
            _secrets_provider_instance = provider_class(**resolved_config) # type: ignore
            logger.info(f"Secrets provider initialized with explicitly provided class: {provider_class.__name__} using config: {resolved_config}")
        else:
            # TODO: Implement configuration-based provider selection
            # For now, defaults to EnvironmentVariablesProvider
            # In the future, read TAUSESTACK_SECRETS_BACKEND env var
            secrets_backend_type = os.getenv('TAUSESTACK_SECRETS_BACKEND', 'env')
            
            if secrets_backend_type == 'env':
                _secrets_provider_instance = EnvironmentVariablesProvider()
                logger.info("Secrets provider initialized with EnvironmentVariablesProvider. Backend type: 'env'")
            elif secrets_backend_type == 'aws':
                # AWSSecretsManagerProvider specific config could be passed via 'resolved_config'
                # e.g., region_name if not relying on default AWS SDK behavior.
                # For now, we assume region_name is handled by boto3 defaults or env vars like AWS_REGION.
                try:
                    _secrets_provider_instance = AWSSecretsManagerProvider(**resolved_config)
                    logger.info(f"Secrets provider initialized with AWSSecretsManagerProvider. Backend type: 'aws', config: {resolved_config}")
                except ImportError as e:
                    logger.critical(f"Failed to initialize AWSSecretsManagerProvider due to ImportError (likely missing boto3): {e}", exc_info=True)
                    # AWSSecretsManagerProvider already logs critical if BOTO3_AVAILABLE is False
                    raise ImportError(f"{e} Ensure boto3 is installed for AWS Secrets Manager support: pip install boto3") from e
            else:
                logger.error(f"Unsupported secrets backend type specified: '{secrets_backend_type}'. Supported types are 'env', 'aws'.")
                raise ValueError(f"Unsupported secrets backend type: {secrets_backend_type}. Supported types are 'env', 'aws'.")
    
    if _secrets_provider_instance is None: # Should not happen if logic above is correct
        logger.critical("Secrets provider could not be initialized after attempting all configuration paths.")
        raise RuntimeError("Secrets provider could not be initialized.")
    return _secrets_provider_instance

def get_secret(secret_name: str) -> Optional[str]:
    """Retrieves a secret by its name using the configured secrets provider.

    Args:
        secret_name: The name of the secret to retrieve.

    Returns:
        The secret value if found, otherwise None.
    """
    provider = _get_secrets_provider_instance()
    logger.debug(f"Getting secret '{secret_name}' using provider: {provider.__class__.__name__}")
    return provider.get(secret_name)
