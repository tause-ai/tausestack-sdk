import unittest
import time
import pickle
import redis # Added to access redis.exceptions

from tausestack.sdk.cache.backends import RedisCacheBackend, CacheTTL

# Attempt to import fakeredis
try:
    import fakeredis
except ImportError:
    fakeredis = None

# Conditionally skip tests if fakeredis is not installed
@unittest.skipIf(fakeredis is None, "fakeredis package not installed, skipping RedisCacheBackend tests.")
class TestRedisCacheBackend(unittest.TestCase):

    def setUp(self):
        # Use a unique prefix for each test run, though fakeredis instances are isolated
        self.test_prefix = f"test_tausestack_cache_{time.time_ns()}:"
        # Create a new fakeredis server instance for each test or use a shared one if appropriate
        # For simplicity and isolation, we'll create a new client which implies a new fake server logic for each test method.
        # fakeredis.FakeServer() could be used for more explicit server management if needed.
        self.redis_server = fakeredis.FakeServer()
        self.redis_client = fakeredis.FakeStrictRedis(server=self.redis_server, decode_responses=False)
        
        # Mock the redis.Redis.from_url to return our fake client
        self.patcher = unittest.mock.patch('redis.Redis.from_url')
        self.mock_from_url = self.patcher.start()
        self.mock_from_url.return_value = self.redis_client
        
        self.cache = RedisCacheBackend(redis_url="redis://fakehost:1234/0", default_ttl=10, redis_prefix=self.test_prefix)
        # Ensure the client used by the cache is our fake client
        self.cache.client = self.redis_client 

    def tearDown(self):
        # Clean up the fakeredis instance by flushing all its keys or re-initializing
        if self.redis_client:
            self.redis_client.flushall()
        self.patcher.stop()

    def test_initialization_and_connection(self):
        # The setUp already tests this implicitly. If it fails, setUp will raise an error.
        # We can add an explicit ping check if the backend exposes it or via the client.
        self.assertTrue(self.cache.client.ping())

    def test_set_and_get(self):
        self.cache.set("key1", "value1")
        self.assertEqual(self.cache.get("key1"), "value1")
        # Check raw Redis value to ensure prefix and pickling
        raw_value = self.redis_client.get(f"{self.test_prefix}key1")
        self.assertIsNotNone(raw_value)
        self.assertEqual(pickle.loads(raw_value), "value1")

    def test_get_non_existent_key(self):
        self.assertIsNone(self.cache.get("non_existent_key"))

    def test_set_overwrite(self):
        self.cache.set("key1", "value1")
        self.cache.set("key1", "value2")
        self.assertEqual(self.cache.get("key1"), "value2")

    def test_delete(self):
        self.cache.set("key_to_delete", "value_to_delete")
        self.assertIsNotNone(self.cache.get("key_to_delete"))
        self.assertTrue(self.redis_client.exists(f"{self.test_prefix}key_to_delete"))
        
        self.cache.delete("key_to_delete")
        self.assertIsNone(self.cache.get("key_to_delete"))
        self.assertFalse(self.redis_client.exists(f"{self.test_prefix}key_to_delete"))

    def test_delete_non_existent_key(self):
        try:
            self.cache.delete("non_existent_key_for_delete")
        except Exception as e:
            self.fail(f"Deleting non-existent key raised an exception: {e}")
        self.assertIsNone(self.cache.get("non_existent_key_for_delete"))

    def test_clear(self):
        self.cache.set("key_a", "val_a")
        self.cache.set("key_b", "val_b")
        # Add a key with a different prefix to ensure it's not deleted
        self.redis_client.set("other_prefix:key_c", pickle.dumps("val_c"))
        
        self.assertIsNotNone(self.cache.get("key_a"))
        self.assertIsNotNone(self.cache.get("key_b"))
        
        self.cache.clear() # Should only clear keys with self.test_prefix
        
        self.assertIsNone(self.cache.get("key_a"))
        self.assertIsNone(self.cache.get("key_b"))
        self.assertTrue(self.redis_client.exists(f"{self.test_prefix}key_a") == 0)
        self.assertTrue(self.redis_client.exists(f"{self.test_prefix}key_b") == 0)
        # Check that the key with a different prefix still exists
        self.assertIsNotNone(self.redis_client.get("other_prefix:key_c"))

    def test_item_expiration_with_specific_ttl_on_set(self):
        # fakeredis does not automatically expire keys with time.sleep(). 
        # It requires manual time adjustment or checking TTL directly.
        # For simplicity, we'll check the TTL using the `ttl` command.
        self.cache.set("exp_key_set", "exp_value_set", ttl=5) # 5s TTL
        self.assertEqual(self.cache.get("exp_key_set"), "exp_value_set")
        ttl_remaining = self.redis_client.ttl(f"{self.test_prefix}exp_key_set")
        self.assertIsNotNone(ttl_remaining)
        self.assertTrue(0 < ttl_remaining <= 5)
        
        # To simulate expiration with fakeredis, you'd typically use its time manipulation features
        # if available and exposed, or rely on its internal logic for commands like PEXPIRETIME.
        # For this test, we'll assume fakeredis respects SETEX. If we could advance time:
        # self.redis_server.ElastiCacheFakeRedis.time_travel(6)
        # self.assertIsNone(self.cache.get("exp_key_set"))
        # Since direct time travel is complex to set up robustly here, we focus on TTL set correctly.

    def test_item_expiration_with_default_ttl_on_init(self):
        cache_short_ttl = RedisCacheBackend(redis_url="redis://fakehost:1234/0", default_ttl=3, redis_prefix=self.test_prefix)
        cache_short_ttl.client = self.redis_client # Ensure it uses our fake client
        cache_short_ttl.set("exp_key_init", "exp_value_init")
        self.assertEqual(cache_short_ttl.get("exp_key_init"), "exp_value_init")
        ttl_remaining = self.redis_client.ttl(f"{self.test_prefix}exp_key_init")
        self.assertIsNotNone(ttl_remaining)
        self.assertTrue(0 < ttl_remaining <= 3)

    def test_cache_forever_with_ttl_zero(self):
        self.cache.set("perm_key", "perm_value", ttl=0) # ttl=0 means cache forever
        self.assertEqual(self.cache.get("perm_key"), "perm_value")
        # In Redis, 'forever' means no TTL is set, so `ttl` command returns -1
        self.assertEqual(self.redis_client.ttl(f"{self.test_prefix}perm_key"), -1)

    def test_cache_forever_with_default_ttl_inf(self):
        inf_cache = RedisCacheBackend(redis_url="redis://fakehost:1234/0", default_ttl=float('inf'), redis_prefix=self.test_prefix)
        inf_cache.client = self.redis_client # Ensure it uses our fake client
        inf_cache.set("perm_key_inf", "perm_value_inf")
        self.assertEqual(inf_cache.get("perm_key_inf"), "perm_value_inf")
        self.assertEqual(self.redis_client.ttl(f"{self.test_prefix}perm_key_inf"), -1)

    def test_get_corrupted_pickle_data(self):
        key = "corrupted_pickle"
        redis_key = f"{self.test_prefix}{key}"
        self.redis_client.set(redis_key, b"this is not valid pickle data")
        
        self.assertTrue(self.redis_client.exists(redis_key))
        # Get should return None and log a warning (check logs manually or mock logger)
        self.assertIsNone(self.cache.get(key))
        # The backend should delete the corrupted key upon unpickling error
        self.assertFalse(self.redis_client.exists(redis_key), "Corrupted key was not deleted.")

    def test_connection_error_on_init(self):
        # Stop the current patcher to allow redis.Redis.from_url to be called directly by the constructor
        self.patcher.stop()
        
        # Temporarily unpatch and then re-patch to test constructor's error handling
        with unittest.mock.patch('redis.Redis.from_url') as mock_connect:
            mock_connect.side_effect = redis.exceptions.ConnectionError("Test connection error")
            with self.assertRaises(redis.exceptions.ConnectionError):
                RedisCacheBackend(redis_url="redis://unknown:1234/0", default_ttl=10)
        
        # Restart the original patcher for subsequent tests if any, or ensure it's clean for tearDown
        self.patcher.start() # Restart original patcher

if __name__ == '__main__':
    # Need to import mock here if running file directly for patcher to work in setUp/tearDown
    from unittest import mock
    unittest.main()
