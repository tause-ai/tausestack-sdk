import logging

# Configure base logger for the SDK
# This prevents "No handlers could be found" warnings if the using application
# does not configure logging. It's up to the application to add handlers if it
# wants to see SDK logs.
_sdk_logger = logging.getLogger(__name__) # __name__ will be 'tausestack.sdk'
if not _sdk_logger.hasHandlers():
    _sdk_logger.addHandler(logging.NullHandler())

# Tausestack SDK - Main Module

# Import all SDK modules
from . import storage
from . import secrets  
from . import cache
from . import notify
from . import auth
from . import database

# Import tenancy module for multi-tenant support
from . import tenancy

# Import isolation module for multi-tenant isolation
from . import isolation

# For backward compatibility, expose main interfaces at top level
from .storage import json_client, binary_client
from .secrets import get_secret as secrets_get
from .cache import cached
from .notify import send_email
from .auth import get_current_user, get_optional_current_user
from .database import Model, ItemID

# Expose tenancy for multi-tenant capabilities
from .tenancy import tenancy, get_current_tenant_id, get_tenant_config, is_multi_tenant_enabled

# Expose isolation for multi-tenant isolation
from .isolation import isolation as isolation_manager, get_current_isolation_config, isolate_path, isolate_cache_key, check_limits

__version__ = "0.7.0"

__all__ = [
    # Core modules
    "storage",
    "secrets", 
    "cache",
    "notify",
    "auth", 
    "database",
    
    # Multi-tenant support
    "tenancy",
    "get_current_tenant_id",
    "get_tenant_config", 
    "is_multi_tenant_enabled",
    
    # Multi-tenant isolation
    "isolation",
    "isolation_manager",
    "get_current_isolation_config",
    "isolate_path",
    "isolate_cache_key", 
    "check_limits",
    
    # Backward compatibility - direct access
    "json",           # storage.json
    "binary",         # storage.binary  
    "dataframe",      # storage.dataframe
    "secrets_get",    # secrets.get
    "cached",         # cache.cached
    "send_email",     # notify.send_email
    "get_current_user",  # auth.get_current_user
    "require_auth",   # auth.require_auth
    "Model",          # database.Model
    "ItemID",         # database.ItemID
]

# Option 1: Allow direct import of clients if preferred
# from .storage import json_client as storage_json_client # Example alias

# Option 2: Create namespace objects similar to Databutton
# This makes it usable like: from tausestack import sdk; sdk.storage.json.put(...)

class StorageNamespace:
    def __init__(self):
        from .storage import json_client as json_storage_client
        self.json = json_storage_client
        # In the future, you can add other storage types here:
        # from .storage import text_client
        # self.text = text_client

storage = StorageNamespace()

class SecretsNamespace:
    def __init__(self):
        from .secrets import get_secret as _get_secret
        # Expose get_secret directly as a method of the namespace instance
        self.get = _get_secret

secrets = SecretsNamespace()

class NotifyNamespace:
    def __init__(self):
        from .notify import send_email as _send_email
        self.email = _send_email # Permite sdk.notify.email(...)
        # Podríamos hacer self.send = _send_email si queremos sdk.notify.send(...)
        # Pero sdk.notify.email.send(...) es más explícito si tenemos otros tipos de notificaciones.
        # Por ahora, como solo es email, sdk.notify.email(...) es conciso.

notify = NotifyNamespace()

class IsolationNamespace:
    def __init__(self):
        from .isolation import isolation as _isolation_manager
        from .isolation.database_isolation import db_isolation
        from .isolation.storage_isolation import storage_isolation
        from .isolation.cache_isolation import cache_isolation
        
        self.manager = _isolation_manager
        self.database = db_isolation
        self.storage = storage_isolation
        self.cache = cache_isolation

isolation = IsolationNamespace()
