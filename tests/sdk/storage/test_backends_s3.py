# Tests for S3Storage backend in tausestack.sdk.storage.backends
import pytest
import os
import json
import boto3
from moto import mock_aws

from tausestack.sdk.storage.backends import S3Storage, PANDAS_AVAILABLE

if PANDAS_AVAILABLE:
    import pandas as pd
    from pandas.testing import assert_frame_equal
    from io import BytesIO

TEST_BUCKET_NAME = "test-tausestack-s3-storage-bucket"

@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

@pytest.fixture(scope="function")
def s3_client_fixture(aws_credentials):
    """Provides a mocked S3 client using moto."""
    with mock_aws():
        client = boto3.client("s3", region_name=os.environ["AWS_DEFAULT_REGION"])
        yield client

@pytest.fixture(scope="function")
def s3_storage_backend(s3_client_fixture):
    """Provides an S3Storage instance with a mocked S3 client and a test bucket."""
    try:
        s3_client_fixture.create_bucket(Bucket=TEST_BUCKET_NAME)
    except Exception as e:
        print(f"Note: Could not create bucket {TEST_BUCKET_NAME} during fixture setup: {e}")

    storage = S3Storage(bucket_name=TEST_BUCKET_NAME, s3_client=s3_client_fixture)
    yield storage

# --- JSON Test Cases ---

class TestS3StorageJson:
    def test_put_get_delete_simple_key(self, s3_storage_backend: S3Storage):
        key = "test_object"
        data = {"message": "Hello, S3!", "version": 1}
        s3_storage_backend.put_json(key, data)
        retrieved_data = s3_storage_backend.get_json(key)
        assert retrieved_data is not None
        assert retrieved_data == data
        s3_storage_backend.delete_json(key)
        assert s3_storage_backend.get_json(key) is None

    def test_put_overwrite_existing_key(self, s3_storage_backend: S3Storage):
        key = "overwrite_test"
        initial_data = {"status": "initial"}
        updated_data = {"status": "updated"}
        s3_storage_backend.put_json(key, initial_data)
        assert s3_storage_backend.get_json(key) == initial_data
        s3_storage_backend.put_json(key, updated_data)
        assert s3_storage_backend.get_json(key) == updated_data
        s3_storage_backend.delete_json(key)

    def test_get_non_existent_key(self, s3_storage_backend: S3Storage):
        key = "does_not_exist"
        assert s3_storage_backend.get_json(key) is None

    def test_delete_non_existent_key(self, s3_storage_backend: S3Storage):
        key = "phantom_key"
        try:
            s3_storage_backend.delete_json(key)
        except Exception as e:
            pytest.fail(f"Deleting non-existent key raised an exception: {e}")

    def test_put_get_delete_nested_key(self, s3_storage_backend: S3Storage):
        key = "path/to/nested/object"
        data = {"detail": "This is a nested object."}
        s3_storage_backend.put_json(key, data)
        assert s3_storage_backend.get_json(key) == data
        s3_storage_backend.delete_json(key)
        assert s3_storage_backend.get_json(key) is None

    def test_get_corrupted_json_in_s3(self, s3_storage_backend: S3Storage, s3_client_fixture):
        key = "corrupted_data.json"
        corrupted_content = "this is not valid json { definitely not"
        s3_client_fixture.put_object(Bucket=TEST_BUCKET_NAME, Key=key, Body=corrupted_content.encode('utf-8'))
        with pytest.raises(json.JSONDecodeError):
            s3_storage_backend.get_json(key)
        s3_storage_backend.delete_json(key)

# --- DataFrame Test Cases ---

@pytest.mark.skipif(not PANDAS_AVAILABLE, reason="pandas and pyarrow are not installed")
class TestS3StorageDataFrame:
    def test_put_get_delete_dataframe(self, s3_storage_backend: S3Storage):
        key = "test_df"
        df = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})
        s3_storage_backend.put_dataframe(key, df)
        
        retrieved_df = s3_storage_backend.get_dataframe(key)
        assert retrieved_df is not None
        assert_frame_equal(retrieved_df, df)
        
        s3_storage_backend.delete_dataframe(key)
        assert s3_storage_backend.get_dataframe(key) is None

    def test_get_non_existent_dataframe(self, s3_storage_backend: S3Storage):
        key = "non_existent_df"
        assert s3_storage_backend.get_dataframe(key) is None

    def test_overwrite_dataframe(self, s3_storage_backend: S3Storage):
        key = "overwrite_df"
        original_df = pd.DataFrame({'a': [1]})
        updated_df = pd.DataFrame({'b': [2]})
        
        s3_storage_backend.put_dataframe(key, original_df)
        s3_storage_backend.put_dataframe(key, updated_df)
        
        retrieved_df = s3_storage_backend.get_dataframe(key)
        assert retrieved_df is not None
        assert_frame_equal(retrieved_df, updated_df)
        s3_storage_backend.delete_dataframe(key)

    def test_delete_non_existent_dataframe(self, s3_storage_backend: S3Storage):
        key = "phantom_df"
        try:
            s3_storage_backend.delete_dataframe(key)
        except Exception as e:
            pytest.fail(f"Deleting non-existent DataFrame key raised an exception: {e}")

    def test_put_get_nested_key_dataframe(self, s3_storage_backend: S3Storage):
        key = "data/source/nested_df"
        df = pd.DataFrame({'path': ['nested/object_df']})
        
        s3_storage_backend.put_dataframe(key, df)
        retrieved_df = s3_storage_backend.get_dataframe(key)
        
        assert retrieved_df is not None
        assert_frame_equal(retrieved_df, df)
        
        s3_storage_backend.delete_dataframe(key)
        assert s3_storage_backend.get_dataframe(key) is None
