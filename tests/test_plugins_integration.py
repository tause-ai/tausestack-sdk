"""
Test de integración para el sistema de plugins/adaptadores de dominio en TauseStack.
Valida registro, descubrimiento, instanciación y uso real de plugins externos (ejemplo CRM).
"""
import pytest
from core.utils.plugins_registry import PluginRegistry
from examples.crm_adapter_plugin import CRMAdapterPlugin

def test_plugin_registry_register_and_list():
    # Usar nombre único para evitar colisiones
    class TempCRMPlugin(CRMAdapterPlugin):
        name = "crm_adapter_test1"
    PluginRegistry.register(TempCRMPlugin)
    plugins = [p["name"] for p in PluginRegistry.list_plugins()]
    assert "crm_adapter_test1" in plugins

def test_plugin_registry_create_instance():
    class TempCRMPlugin(CRMAdapterPlugin):
        name = "crm_adapter_test2"
    PluginRegistry.register(TempCRMPlugin)
    config = {"api_key": "demo", "endpoint": "https://crm.local"}
    instance = PluginRegistry.create_instance("crm_adapter_test2", config=config)
    # setup debería inicializar los atributos
    assert hasattr(instance, "api_key")
    assert instance.api_key == "demo"
    assert hasattr(instance, "endpoint")
    assert instance.endpoint == "https://crm.local"

def test_crm_adapter_plugin_execute():
    class TempCRMPlugin(CRMAdapterPlugin):
        name = "crm_adapter_test3"
    # Limpiar registro por si acaso
    if hasattr(PluginRegistry, '_registry'):
        PluginRegistry._registry.pop("crm_adapter_test3", None)
    config = {"api_key": "demo", "endpoint": "https://crm.local"}
    PluginRegistry.register(TempCRMPlugin)
    instance = PluginRegistry.create_instance("crm_adapter_test3", config=config)
    assert hasattr(instance, "config")
    # Simular acción soportada: connect
    result = instance.execute("connect")
    assert result["status"] == "connected"
    # Simular acción soportada: push_lead
    instance.connected = True  # simular conexión previa
    lead_data = {"name": "Test Lead", "email": "lead@demo.com"}
    result = instance.execute("push_lead", data=lead_data)
    assert result["status"] == "lead_sent"
    assert result["lead"] == lead_data
    # Simular acción no soportada
    try:
        instance.execute("unknown_action", data={})
    except Exception as e:
        assert "no soportada" in str(e) or "not implemented" in str(e).lower()
