import unittest
import time
import os
from unittest.mock import patch, MagicMock

from tausestack.sdk.cache import cached
from tausestack.sdk.cache.main import _get_cache_backend, _cache_backend_instances, _default_backend_name_config
from tausestack.sdk.cache.backends import MemoryCacheBackend

# Helper function to reset global state for testing
def reset_cache_main_globals():
    global _cache_backend_instances, _default_backend_name_config
    _cache_backend_instances.clear()
    _default_backend_name_config = None
    # Ensure TAUSESTACK_CACHE_DEFAULT_BACKEND is not set or set to a known value for tests
    if 'TAUSESTACK_CACHE_DEFAULT_BACKEND' in os.environ:
        del os.environ['TAUSESTACK_CACHE_DEFAULT_BACKEND']

class TestCacheMain(unittest.TestCase):

    def setUp(self):
        reset_cache_main_globals()
        # Ensure MemoryCacheBackend is the default unless specified
        self.mock_function_call_count = 0

    def tearDown(self):
        reset_cache_main_globals()

    def mock_function(self, *args, **kwargs):
        self.mock_function_call_count += 1
        return f"called_with_{args}_{kwargs}"

    def test_cached_decorator_memory_backend_default(self):
        self.mock_function_call_count = 0
        decorated_func = cached(ttl=10)(self.mock_function)

        # First call - should execute and cache
        result1 = decorated_func("arg1", kwarg1="val1")
        self.assertEqual(self.mock_function_call_count, 1)
        self.assertEqual(result1, "called_with_('arg1',)_{'kwarg1': 'val1'}")

        # Second call - should hit cache
        result2 = decorated_func("arg1", kwarg1="val1")
        self.assertEqual(self.mock_function_call_count, 1) # Still 1
        self.assertEqual(result2, result1)

        # Third call with different args - should execute and cache
        result3 = decorated_func("arg2", kwarg1="val2")
        self.assertEqual(self.mock_function_call_count, 2)
        self.assertEqual(result3, "called_with_('arg2',)_{'kwarg1': 'val2'}")

    def test_cached_decorator_ttl_expiration(self):
        self.mock_function_call_count = 0
        decorated_func = cached(ttl=0.1)(self.mock_function)

        decorated_func("exp_test")
        self.assertEqual(self.mock_function_call_count, 1)

        time.sleep(0.2)
        decorated_func("exp_test") # Should re-execute after TTL
        self.assertEqual(self.mock_function_call_count, 2)

    def test_cached_decorator_ttl_zero_caches_forever_in_memory(self):
        self.mock_function_call_count = 0
        # ttl=0 means cache 'forever' (instance_ttl=inf for MemoryCacheBackend)
        decorated_func = cached(ttl=0)(self.mock_function)

        decorated_func("forever_test")
        self.assertEqual(self.mock_function_call_count, 1)

        time.sleep(0.1) # Should still be cached
        decorated_func("forever_test")
        self.assertEqual(self.mock_function_call_count, 1) 

    def test_multiple_decorators_different_ttls_get_different_memory_instances(self):
        self.mock_function_call_count = 0
        func_short_ttl = cached(ttl=0.1)(self.mock_function)
        func_long_ttl = cached(ttl=10)(self.mock_function) # Uses a different MemoryCacheBackend instance

        # Call short TTL func
        func_short_ttl("test_val")
        self.assertEqual(self.mock_function_call_count, 1)
        # Call long TTL func with same args - should be a miss in its own cache
        func_long_ttl("test_val")
        self.assertEqual(self.mock_function_call_count, 2)

        # Let short TTL expire
        time.sleep(0.2)

        # Call short TTL again - should re-execute
        func_short_ttl("test_val")
        self.assertEqual(self.mock_function_call_count, 3)

        # Call long TTL again - should still be cached in its instance
        func_long_ttl("test_val")
        self.assertEqual(self.mock_function_call_count, 3)
        
        # Verify two distinct memory backend instances were created based on TTL
        self.assertTrue(any('memory_ttl_0_1' in key for key in _cache_backend_instances))
        self.assertTrue(any('memory_ttl_10' in key for key in _cache_backend_instances))
        self.assertEqual(len(_cache_backend_instances), 2)

    @patch.dict(os.environ, {"TAUSESTACK_CACHE_DEFAULT_BACKEND": "memory"})
    def test_default_backend_selection_from_env_var(self):
        reset_cache_main_globals() # Reset to pick up env var
        backend_instance = _get_cache_backend(config={'ttl': 60}) # Pass config for memory instance
        self.assertIsInstance(backend_instance, MemoryCacheBackend)
        self.assertEqual(backend_instance.instance_ttl, 60)

    def test_invalid_ttl_raises_value_error(self):
        with self.assertRaises(ValueError):
            @cached(ttl=-1)
            def my_func_invalid_ttl(): pass
        
        with self.assertRaises(ValueError):
            @cached(ttl='abc') # type: ignore
            def my_func_invalid_type_ttl(): pass

    @patch('tausestack.sdk.cache.main.logger')
    def test_cache_setup_exception_calls_function_directly(self, mock_logger):
        self.mock_function_call_count = 0
        
        with patch('tausestack.sdk.cache.main._generate_cache_key', side_effect=Exception("Keygen error")):
            decorated_func = cached(ttl=10)(self.mock_function)
            result = decorated_func("test")
            self.assertEqual(self.mock_function_call_count, 1) # Function called directly
            self.assertEqual(result, "called_with_('test',)_{}")
            mock_logger.error.assert_called_once()
            self.assertIn("Error in cache setup", mock_logger.error.call_args[0][0])

    # Test for _get_cache_backend directly for unsupported backend
    def test_get_unsupported_backend_raises_error(self):
        with self.assertRaises(ValueError) as cm:
            _get_cache_backend("non_existent_backend")
        self.assertIn("Unsupported cache backend: non_existent_backend", str(cm.exception))

if __name__ == '__main__':
    unittest.main()
