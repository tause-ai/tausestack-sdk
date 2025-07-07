import unittest
import time
import pathlib
import tempfile
import os
import shutil
import pickle

from tausestack.sdk.cache.backends import DiskCacheBackend, CacheTTL

class TestDiskCacheBackend(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory for the cache for each test method
        self.temp_dir_obj = tempfile.TemporaryDirectory()
        self.cache_base_path = self.temp_dir_obj.name
        # Ensure a clean state for each test by creating a new instance
        self.cache = DiskCacheBackend(base_path=self.cache_base_path, default_ttl=10) # Default TTL for tests

    def tearDown(self):
        # Clean up the temporary directory after each test method
        self.temp_dir_obj.cleanup()
        # Safety net if cleanup didn't work, though TemporaryDirectory should handle it.
        if os.path.exists(self.cache_base_path):
            shutil.rmtree(self.cache_base_path, ignore_errors=True)

    def test_initialization_creates_directory(self):
        self.assertTrue(pathlib.Path(self.cache_base_path).exists())
        self.assertTrue(pathlib.Path(self.cache_base_path).is_dir())

    def test_set_and_get(self):
        self.cache.set("key1", "value1")
        self.assertEqual(self.cache.get("key1"), "value1")

    def test_get_non_existent_key(self):
        self.assertIsNone(self.cache.get("non_existent_key"))

    def test_set_overwrite(self):
        self.cache.set("key1", "value1")
        self.cache.set("key1", "value2") # Overwrite
        self.assertEqual(self.cache.get("key1"), "value2")

    def test_delete(self):
        self.cache.set("key_to_delete", "value_to_delete")
        self.assertIsNotNone(self.cache.get("key_to_delete"))
        file_path = self.cache._get_file_path("key_to_delete")
        self.assertTrue(file_path.exists())
        
        self.cache.delete("key_to_delete")
        self.assertIsNone(self.cache.get("key_to_delete"))
        self.assertFalse(file_path.exists())

    def test_delete_non_existent_key(self):
        # Deleting a non-existent key should not raise an error
        try:
            self.cache.delete("non_existent_key_for_delete")
        except Exception as e:
            self.fail(f"Deleting non-existent key raised an exception: {e}")
        self.assertIsNone(self.cache.get("non_existent_key_for_delete"))

    def test_clear(self):
        self.cache.set("key_a", "val_a")
        self.cache.set("key_b", "val_b")
        self.assertTrue(len(list(pathlib.Path(self.cache_base_path).iterdir())) > 0)
        
        self.cache.clear()
        self.assertIsNone(self.cache.get("key_a"))
        self.assertIsNone(self.cache.get("key_b"))
        # Check if the directory is empty (or only contains non-cache files if any)
        # For this backend, clear removes all files directly under base_path.
        self.assertEqual(len(list(pathlib.Path(self.cache_base_path).iterdir())), 0)

    def test_item_expiration_with_specific_ttl_on_set(self):
        self.cache.set("exp_key_set", "exp_value_set", ttl=0.1) # Short TTL for testing
        self.assertEqual(self.cache.get("exp_key_set"), "exp_value_set")
        time.sleep(0.2) # Wait for item to expire
        self.assertIsNone(self.cache.get("exp_key_set"))
        # Check that the expired file was deleted by the get method
        self.assertFalse(self.cache._get_file_path("exp_key_set").exists())

    def test_item_expiration_with_default_ttl_on_init(self):
        # Re-init cache with a very short default TTL for this test
        short_ttl_cache = DiskCacheBackend(base_path=self.cache_base_path, default_ttl=0.1)
        short_ttl_cache.set("exp_key_init", "exp_value_init")
        self.assertEqual(short_ttl_cache.get("exp_key_init"), "exp_value_init")
        time.sleep(0.2)
        self.assertIsNone(short_ttl_cache.get("exp_key_init"))
        self.assertFalse(short_ttl_cache._get_file_path("exp_key_init").exists())

    def test_cache_forever_with_ttl_zero(self):
        self.cache.set("perm_key", "perm_value", ttl=0) # ttl=0 means cache forever
        time.sleep(0.1) # Wait a bit, should still be there
        self.assertEqual(self.cache.get("perm_key"), "perm_value")
        # Verify expiry_timestamp is inf
        file_path = self.cache._get_file_path("perm_key")
        with open(file_path, 'rb') as f:
            cached_data = pickle.load(f)
        self.assertEqual(cached_data['expiry_timestamp'], float('inf'))

    def test_cache_forever_with_default_ttl_inf(self):
        inf_cache = DiskCacheBackend(base_path=self.cache_base_path, default_ttl=float('inf'))
        inf_cache.set("perm_key_inf", "perm_value_inf")
        time.sleep(0.1)
        self.assertEqual(inf_cache.get("perm_key_inf"), "perm_value_inf")

    def test_get_corrupted_file_returns_none_and_deletes_file(self):
        key = "corrupted_key"
        file_path = self.cache._get_file_path(key)
        # Manually create a corrupted file
        with open(file_path, 'wb') as f:
            f.write(b"this is not valid pickle data")
        
        self.assertTrue(file_path.exists())
        self.assertIsNone(self.cache.get(key))
        # The backend should attempt to delete the corrupted file upon read error
        self.assertFalse(file_path.exists(), "Corrupted file was not deleted after get attempt.")

    def test_different_instances_different_paths(self):
        with tempfile.TemporaryDirectory() as path1_dir:
            with tempfile.TemporaryDirectory() as path2_dir:
                cache1 = DiskCacheBackend(base_path=path1_dir, default_ttl=10)
                cache2 = DiskCacheBackend(base_path=path2_dir, default_ttl=10)

                cache1.set("mykey", "cache1_value")
                cache2.set("mykey", "cache2_value") # Same key, different cache instance

                self.assertEqual(cache1.get("mykey"), "cache1_value")
                self.assertEqual(cache2.get("mykey"), "cache2_value")
                self.assertTrue((pathlib.Path(path1_dir) / cache1._hash_key("mykey")).exists())
                self.assertTrue((pathlib.Path(path2_dir) / cache2._hash_key("mykey")).exists())

if __name__ == '__main__':
    unittest.main()
