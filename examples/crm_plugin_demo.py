"""
Demo de registro, instanciación y uso del plugin CRMAdapterPlugin con el sistema de plugins de TauseStack.
"""
from core.utils.plugins_registry import PluginRegistry
from examples.crm_adapter_plugin import CRMAdapterPlugin

# Registro del plugin en el sistema
PluginRegistry.register(CRMAdapterPlugin)

# Listar plugins disponibles
print("Plugins registrados:", PluginRegistry.list_plugins())

# Crear instancia y usar el plugin
crm = PluginRegistry.create_instance("crm_adapter", config={"api_key": "demo-key", "endpoint": "https://demo.crm/api"})

print(crm.execute("connect"))
print(crm.execute("push_lead", data={"email": "test@demo.com", "name": "Demo Lead"}))
print(crm.execute("get_status"))

crm.teardown()
print(crm.execute("get_status"))
