import unittest
import time
from tausestack.sdk.cache.backends import MemoryCacheBackend

class TestMemoryCacheBackend(unittest.TestCase):

    def test_set_and_get(self):
        cache = MemoryCacheBackend(default_ttl=10) # TTL of 10 seconds for this instance
        cache.set("key1", "value1")
        self.assertEqual(cache.get("key1"), "value1")

    def test_get_non_existent_key(self):
        cache = MemoryCacheBackend(default_ttl=10)
        self.assertIsNone(cache.get("non_existent_key"))

    def test_set_overwrite(self):
        cache = MemoryCacheBackend(default_ttl=10)
        cache.set("key1", "value1")
        cache.set("key1", "value2")
        self.assertEqual(cache.get("key1"), "value2")

    def test_delete(self):
        cache = MemoryCacheBackend(default_ttl=10)
        cache.set("key1", "value1")
        cache.delete("key1")
        self.assertIsNone(cache.get("key1"))

    def test_delete_non_existent_key(self):
        cache = MemoryCacheBackend(default_ttl=10)
        # Deleting a non-existent key should not raise an error
        try:
            cache.delete("non_existent_key")
        except Exception as e:
            self.fail(f"Deleting non-existent key raised an exception: {e}")

    def test_clear(self):
        cache = MemoryCacheBackend(default_ttl=10)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        self.assertIsNone(cache.get("key1"))
        self.assertIsNone(cache.get("key2"))

    def test_item_expiration(self):
        cache = MemoryCacheBackend(default_ttl=0.1) # Short TTL for testing
        cache.set("exp_key", "exp_value")
        self.assertEqual(cache.get("exp_key"), "exp_value")
        time.sleep(0.2) # Wait for item to expire
        self.assertIsNone(cache.get("exp_key"))

    def test_cache_forever_with_inf_ttl(self):
        cache = MemoryCacheBackend(default_ttl=float('inf')) # Cache forever
        cache.set("perm_key", "perm_value")
        time.sleep(0.1) # Wait a bit, should still be there
        self.assertEqual(cache.get("perm_key"), "perm_value")

    def test_maxsize_behavior(self):
        cache = MemoryCacheBackend(maxsize=2, default_ttl=10)
        cache.set("a", 1)
        cache.set("b", 2)
        self.assertEqual(cache.get("a"), 1)
        self.assertEqual(cache.get("b"), 2)
        
        # Adding a third item 'c' should evict the least recently used ('a' if get('a') wasn't called recently)
        # cachetools.TTLCache uses an LRU policy when maxsize is reached.
        # To make 'a' less recent than 'b', we access 'b' again before adding 'c'.
        cache.get("b") # Access 'b' to make it more recent than 'a'
        cache.set("c", 3)
        
        self.assertIsNone(cache.get("a")) # 'a' should be evicted
        self.assertEqual(cache.get("b"), 2)
        self.assertEqual(cache.get("c"), 3)

if __name__ == '__main__':
    unittest.main()
