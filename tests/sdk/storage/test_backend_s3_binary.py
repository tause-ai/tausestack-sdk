import unittest
import os
from unittest.mock import patch
import boto3
from moto import mock_aws
from pathlib import Path

from tausestack.sdk.storage.backends import S3Storage

@mock_aws
class TestS3StorageBinary(unittest.TestCase):
    """Test suite for S3Storage binary operations."""

    def setUp(self):
        """Set up the S3 bucket and S3Storage client for binary tests."""
        self.bucket_name = "test-tausestack-s3-binary-storage-bucket"
        self.s3_client = boto3.client("s3", region_name="us-east-1")
        self.s3_client.create_bucket(Bucket=self.bucket_name)

        # Mock environment variables for S3Storage
        self.mock_env = patch.dict(os.environ, {
            "TAUSESTACK_STORAGE_BACKEND": "s3",
            "TAUSESTACK_S3_BUCKET_NAME": self.bucket_name,
            "AWS_ACCESS_KEY_ID": "testing", # Moto doesn't actually use these for mock
            "AWS_SECRET_ACCESS_KEY": "testing",
            "AWS_SECURITY_TOKEN": "testing",
            "AWS_SESSION_TOKEN": "testing",
            "AWS_DEFAULT_REGION": "us-east-1"
        })
        self.mock_env.start()

        self.storage = S3Storage(bucket_name=self.bucket_name)
        # Ensure BOTO3_AVAILABLE is true for S3Storage internal checks if any
        self.patch_boto3_available = patch('tausestack.sdk.storage.backends.BOTO3_AVAILABLE', True)
        self.patch_boto3_available.start()

    def tearDown(self):
        """Clean up S3 bucket and stop mocks."""
        # Delete all objects in the bucket first
        objects = self.s3_client.list_objects_v2(Bucket=self.bucket_name).get('Contents', [])
        if objects:
            delete_objects = {'Objects': [{'Key': obj['Key']} for obj in objects]}
            self.s3_client.delete_objects(Bucket=self.bucket_name, Delete=delete_objects)
        self.s3_client.delete_bucket(Bucket=self.bucket_name)
        self.mock_env.stop()
        self.patch_boto3_available.stop()

    def test_put_and_get_binary(self):
        key = "my_binary_file.dat"
        binary_data = b"\x00\x01\x02\x03Binary data for S3!\xff\xfe"
        self.storage.put_binary(key, binary_data)
        retrieved_data = self.storage.get_binary(key)
        self.assertEqual(retrieved_data, binary_data)

    def test_get_non_existent_binary(self):
        retrieved_data = self.storage.get_binary("non_existent_file.bin")
        self.assertIsNone(retrieved_data)

    def test_overwrite_binary(self):
        key = "overwrite_me.bin"
        original_data = b"Original S3 binary content."
        updated_data = b"Updated S3 binary content, now different."
        self.storage.put_binary(key, original_data)
        self.storage.put_binary(key, updated_data)  # Overwrite
        retrieved_data = self.storage.get_binary(key)
        self.assertEqual(retrieved_data, updated_data)

    def test_delete_binary(self):
        key = "to_be_deleted.tmp"
        binary_data = b"This binary file will be deleted from S3."
        self.storage.put_binary(key, binary_data)
        self.storage.delete_binary(key)
        retrieved_data = self.storage.get_binary(key)
        self.assertIsNone(retrieved_data)
        # Verify it's actually deleted from S3
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            self.fail("Object was not deleted from S3")
        except Exception as e:
            self.assertTrue("Not Found" in str(e) or "NoSuchKey" in str(e))

    def test_delete_non_existent_binary(self):
        # Deleting a non-existent key should not raise an error
        try:
            self.storage.delete_binary("surely_not_existing_file.dat")
        except Exception as e:
            self.fail(f"Deleting non-existent binary key raised an exception: {e}")

    def test_put_with_subdirectories_binary(self):
        key = "folder/subfolder/my_deep_file.data"
        binary_data = b"Binary data in a subdirectory in S3."
        self.storage.put_binary(key, binary_data)
        retrieved_data = self.storage.get_binary(key)
        self.assertEqual(retrieved_data, binary_data)
        # Verify object exists at the correct S3 path
        response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
        self.assertEqual(response['Body'].read(), binary_data)

    def test_put_binary_with_content_type(self):
        key = "image.png"
        binary_data = b"fake png data"
        content_type = "image/png"
        self.storage.put_binary(key, binary_data, content_type=content_type)
        retrieved_data = self.storage.get_binary(key)
        self.assertEqual(retrieved_data, binary_data)
        # Verify ContentType in S3
        s3_object = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
        self.assertEqual(s3_object['ContentType'], content_type)

    def test_binary_key_persists_extension(self):
        key = "archive.tar.gz"
        binary_data = b"gzipped tarball data"
        self.storage.put_binary(key, binary_data)
        retrieved_data = self.storage.get_binary(key)
        self.assertEqual(retrieved_data, binary_data)
        # Check S3 object key is exactly as provided
        response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
        self.assertEqual(response['Body'].read(), binary_data)
        self.storage.delete_binary(key)

if __name__ == '__main__':
    unittest.main()
