import json
import logging
import os
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Optional

from .base import (
    AbstractBinaryStorageBackend,
    AbstractDataFrameStorageBackend,
    AbstractJsonStorageBackend,
)

try:
    import pandas as pd
    import pyarrow

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None
    pyarrow = None

logger = logging.getLogger(__name__)

class LocalStorage(
    AbstractJsonStorageBackend, AbstractBinaryStorageBackend, AbstractDataFrameStorageBackend
):
    """Stores JSON objects, binary files, and DataFrames in the local filesystem."""

    def __init__(
        self,
        base_json_path: str = ".tausestack_storage/json",
        base_binary_path: str = ".tausestack_storage/binary",
        base_dataframe_path: str = ".tausestack_storage/dataframe",
    ):
        self.base_json_path = Path(base_json_path)
        self.base_binary_path = Path(base_binary_path)
        self.base_dataframe_path = Path(base_dataframe_path)
        self.base_json_path.mkdir(parents=True, exist_ok=True)
        self.base_binary_path.mkdir(parents=True, exist_ok=True)
        self.base_dataframe_path.mkdir(parents=True, exist_ok=True)
        logger.debug(
            f"LocalStorage initialized. JSON path: {self.base_json_path}, "
            f"Binary path: {self.base_binary_path}, DataFrame path: {self.base_dataframe_path}"
        )

    def _validate_key(self, key: str):
        """Validate key format for security."""
        import re
        # Put the dash at the end to avoid range interpretation
        key_regex = re.compile(r'^[a-zA-Z0-9._/-]+$')
        if not key_regex.match(key):
            raise ValueError(f"Invalid key format: '{key}'. Must match regex ^[a-zA-Z0-9._/-]+$")
        if key.startswith('/') or '..' in key:
            raise ValueError(f"Invalid key: '{key}'. No absolute paths or '..' allowed")

    # --- JSON Methods --- 
    def _get_json_file_path(self, key: str) -> Path:
        path_key = Path(key)
        if path_key.suffix.lower() != ".json":
            path_key = path_key.with_suffix(".json")
        return self.base_json_path / path_key

    def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        self._validate_key(key)
        file_path = self._get_json_file_path(key)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.debug(f"JSON file not found at {file_path} for key '{key}'")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from {file_path} for key '{key}': {e}", exc_info=True)
            return None # Or re-raise as a custom storage exception

    def put_json(self, key: str, value: Dict[str, Any]) -> None:
        self._validate_key(key)
        self._validate_key(key)
        file_path = self._get_json_file_path(key)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(value, f, indent=4, ensure_ascii=False)
            logger.debug(f"Successfully wrote JSON to {file_path} for key '{key}'")
        except IOError as e:
            logger.error(f"Error writing JSON to {file_path} for key '{key}': {e}", exc_info=True)
            raise

    def delete_json(self, key: str) -> None:
        self._validate_key(key)
        file_path = self._get_json_file_path(key)
        try:
            os.remove(file_path)
            logger.debug(f"Successfully deleted JSON file {file_path} for key '{key}'")
        except FileNotFoundError:
            logger.debug(f"JSON file not found at {file_path} for key '{key}' during delete.")
            pass 
        except OSError as e:
            logger.error(f"Error deleting JSON file {file_path} for key '{key}': {e}", exc_info=True)
            raise

    # --- Binary Methods --- 
    def _get_binary_file_path(self, key: str) -> Path:
        # For binary files, use the key as is, without assuming/adding extensions.
        # The key should represent the intended filename or path relative to base_binary_path.
        return self.base_binary_path / Path(key)

    def get_binary(self, key: str) -> Optional[bytes]:
        self._validate_key(key)
        file_path = self._get_binary_file_path(key)
        try:
            with open(file_path, 'rb') as f:
                return f.read()
        except FileNotFoundError:
            logger.debug(f"Binary file not found at {file_path} for key '{key}'")
            return None
        except IOError as e:
            logger.error(f"Error reading binary file {file_path} for key '{key}': {e}", exc_info=True)
            raise

    def put_binary(self, key: str, value: bytes, content_type: Optional[str] = None) -> None:
        self._validate_key(key)
        # content_type is ignored for local storage but kept for interface consistency
        file_path = self._get_binary_file_path(key)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(file_path, 'wb') as f:
                f.write(value)
            logger.debug(f"Successfully wrote binary data to {file_path} for key '{key}'")
        except IOError as e:
            logger.error(f"Error writing binary data to {file_path} for key '{key}': {e}", exc_info=True)
            raise

    def delete_binary(self, key: str) -> None:
        self._validate_key(key)
        file_path = self._get_binary_file_path(key)
        try:
            os.remove(file_path)
            logger.debug(f"Successfully deleted binary file {file_path} for key '{key}'")
        except FileNotFoundError:
            logger.debug(f"Binary file not found at {file_path} for key '{key}' during delete.")
            pass
        except OSError as e:
            logger.error(f"Error deleting binary file {file_path} for key '{key}': {e}", exc_info=True)
            raise

    # --- DataFrame Methods ---
    def _get_dataframe_file_path(self, key: str) -> Path:
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas and pyarrow are required for DataFrame storage.")
        path_key = Path(key)
        if path_key.suffix.lower() != ".parquet":
            path_key = path_key.with_suffix(".parquet")
        return self.base_dataframe_path / path_key

    def get_dataframe(self, key: str) -> Optional["pd.DataFrame"]:
        self._validate_key(key)
        file_path = self._get_dataframe_file_path(key)
        try:
            return pd.read_parquet(file_path)
        except FileNotFoundError:
            logger.debug(f"DataFrame file not found at {file_path} for key '{key}'")
            return None
        except Exception as e:
            logger.error(
                f"Error reading DataFrame from {file_path} for key '{key}': {e}",
                exc_info=True,
            )
            raise

    def put_dataframe(self, key: str, value: "pd.DataFrame") -> None:
        self._validate_key(key)
        file_path = self._get_dataframe_file_path(key)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            value.to_parquet(file_path)
            logger.debug(f"Successfully wrote DataFrame to {file_path} for key '{key}'")
        except Exception as e:
            logger.error(
                f"Error writing DataFrame to {file_path} for key '{key}': {e}",
                exc_info=True,
            )
            raise

    def delete_dataframe(self, key: str) -> None:
        self._validate_key(key)
        file_path = self._get_dataframe_file_path(key)
        try:
            os.remove(file_path)
            logger.debug(f"Successfully deleted DataFrame file {file_path} for key '{key}'")
        except FileNotFoundError:
            logger.debug(
                f"DataFrame file not found at {file_path} for key '{key}' during delete."
            )
            pass
        except OSError as e:
            logger.error(
                f"Error deleting DataFrame file {file_path} for key '{key}': {e}",
                exc_info=True,
            )
            raise

# --- S3 Storage --- 
try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    class ClientError(Exception):
        """Dummy class for type hinting when boto3 is not available."""
        pass

class S3Storage(
    AbstractJsonStorageBackend, AbstractBinaryStorageBackend, AbstractDataFrameStorageBackend
):
    """Stores JSON objects, binary files, and DataFrames in AWS S3."""

    def __init__(self, bucket_name: str, s3_client=None):
        if not BOTO3_AVAILABLE:
            logger.critical("boto3 is required for S3Storage but is not installed.")
            raise ImportError("boto3 is required for S3Storage. Please install it: pip install boto3")
        
        self.bucket_name = bucket_name
        self.s3_client = s3_client if s3_client else boto3.client('s3')
        logger.debug(f"S3Storage initialized for bucket: {self.bucket_name}. Custom S3 client: {s3_client is not None}")

    def _validate_key(self, key: str):
        """Validate key format for security."""
        import re
        # Put the dash at the end to avoid range interpretation
        key_regex = re.compile(r'^[a-zA-Z0-9._/-]+$')
        if not key_regex.match(key):
            raise ValueError(f"Invalid key format: '{key}'. Must match regex ^[a-zA-Z0-9._/-]+$")
        if key.startswith('/') or '..' in key:
            raise ValueError(f"Invalid key: '{key}'. No absolute paths or '..' allowed")

    # --- JSON Methods --- 
    def _get_json_s3_key(self, key: str) -> str:
        s3_key = key.lstrip('/') 
        if not s3_key.endswith(".json"):
            s3_key += ".json"
        return s3_key

    def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        self._validate_key(key)
        s3_key = self._get_json_s3_key(key)
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            content = response['Body'].read().decode('utf-8')
            return json.loads(content)
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.debug(f"S3 JSON object {s3_key} not found in {self.bucket_name} for key '{key}'")
                return None
            logger.error(f"Error getting S3 JSON object {s3_key} from {self.bucket_name} for key '{key}': {e}", exc_info=True)
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from S3 object {s3_key} for key '{key}': {e}", exc_info=True)
            raise # Or return None / custom exception

    def put_json(self, key: str, value: Dict[str, Any]) -> None:
        self._validate_key(key)
        s3_key = self._get_json_s3_key(key)
        try:
            json_string = json.dumps(value, indent=4, ensure_ascii=False)
            self.s3_client.put_object(
                Bucket=self.bucket_name, 
                Key=s3_key, 
                Body=json_string.encode('utf-8'),
                ContentType='application/json'
            )
            logger.debug(f"Successfully put S3 JSON object {s3_key} to {self.bucket_name} for key '{key}'")
        except ClientError as e:
            logger.error(f"Error putting S3 JSON object {s3_key} to {self.bucket_name} for key '{key}': {e}", exc_info=True)
            raise
        except IOError as e: 
            logger.error(f"IOError before S3 JSON put for key {s3_key}: {e}", exc_info=True)
            raise

    def delete_json(self, key: str) -> None:
        self._validate_key(key)
        s3_key = self._get_json_s3_key(key)
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.debug(f"Successfully deleted S3 JSON object {s3_key} from {self.bucket_name} for key '{key}'")
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.debug(f"Attempted to delete non-existent S3 JSON object {s3_key}. No action.")
            else:
                logger.warning(f"Error deleting S3 JSON object {s3_key}: {e}", exc_info=True)
                raise

    # --- Binary Methods --- 
    def _get_binary_s3_key(self, key: str) -> str:
        # For binary files, use the key as is, removing leading slash.
        return key.lstrip('/')

    def get_binary(self, key: str) -> Optional[bytes]:
        self._validate_key(key)
        s3_key = self._get_binary_s3_key(key)
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            return response['Body'].read()
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.debug(f"S3 binary object {s3_key} not found in {self.bucket_name} for key '{key}'")
                return None
            logger.error(f"Error getting S3 binary object {s3_key} from {self.bucket_name} for key '{key}': {e}", exc_info=True)
            raise

    def put_binary(self, key: str, value: bytes, content_type: Optional[str] = None) -> None:
        self._validate_key(key)
        s3_key = self._get_binary_s3_key(key)
        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type
        
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name, 
                Key=s3_key, 
                Body=value,
                **extra_args
            )
            logger.debug(f"Successfully put S3 binary object {s3_key} to {self.bucket_name} for key '{key}' with content_type: {content_type}")
        except ClientError as e:
            logger.error(f"Error putting S3 binary object {s3_key} to {self.bucket_name} for key '{key}': {e}", exc_info=True)
            raise

    def delete_binary(self, key: str) -> None:
        self._validate_key(key)
        s3_key = self._get_binary_s3_key(key)
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.debug(f"Successfully deleted S3 binary object {s3_key} from {self.bucket_name} for key '{key}'")
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.debug(f"Attempted to delete non-existent S3 binary object {s3_key}. No action.")
            else:
                logger.warning(f"Error deleting S3 binary object {s3_key}: {e}", exc_info=True)
                raise

    # --- DataFrame Methods ---
    def _get_dataframe_s3_key(self, key: str) -> str:
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas and pyarrow are required for DataFrame storage.")
        s3_key = key.lstrip('/')
        if not s3_key.endswith(".parquet"):
            s3_key += ".parquet"
        return s3_key

    def get_dataframe(self, key: str) -> Optional["pd.DataFrame"]:
        self._validate_key(key)
        s3_key = self._get_dataframe_s3_key(key)
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            buffer = BytesIO(response['Body'].read())
            return pd.read_parquet(buffer)
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.debug(
                    f"S3 DataFrame object {s3_key} not found in {self.bucket_name} for key '{key}'"
                )
                return None
            logger.error(
                f"Error getting S3 DataFrame object {s3_key} from {self.bucket_name} for key '{key}': {e}",
                exc_info=True,
            )
            raise
        except Exception as e:
            logger.error(
                f"Error reading DataFrame from S3 object {s3_key} for key '{key}': {e}",
                exc_info=True,
            )
            raise

    def put_dataframe(self, key: str, value: "pd.DataFrame") -> None:
        self._validate_key(key)
        s3_key = self._get_dataframe_s3_key(key)
        try:
            buffer = BytesIO()
            value.to_parquet(buffer, index=False)
            buffer.seek(0)
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=buffer,
                ContentType='application/vnd.apache.parquet'
            )
            logger.debug(
                f"Successfully put S3 DataFrame object {s3_key} to {self.bucket_name} for key '{key}'"
            )
        except ClientError as e:
            logger.error(
                f"Error putting S3 DataFrame object {s3_key} to {self.bucket_name} for key '{key}': {e}",
                exc_info=True,
            )
            raise
        except Exception as e:
            logger.error(
                f"Error writing DataFrame to S3 for key {s3_key}: {e}", exc_info=True
            )
            raise

    def delete_dataframe(self, key: str) -> None:
        self._validate_key(key)
        s3_key = self._get_dataframe_s3_key(key)
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.debug(
                f"Successfully deleted S3 DataFrame object {s3_key} from {self.bucket_name} for key '{key}'"
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.debug(
                    f"Attempted to delete non-existent S3 DataFrame object {s3_key}. No action."
                )
            else:
                logger.warning(f"Error deleting S3 DataFrame object {s3_key}: {e}", exc_info=True)
                raise
