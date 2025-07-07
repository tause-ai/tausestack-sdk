"""
Ejemplo funcional de un plugin externo: Adaptador CRM para TauseStack.
Este plugin simula la integración con un CRM y sigue la interfaz base DomainPlugin.
"""
from core.utils.plugins_base import DomainPlugin

class CRMAdapterPlugin(DomainPlugin):
    name = "crm_adapter"
    version = "1.0.0"
    description = "Plugin de integración con CRM externo (demo)"
    author = "Equipo TauseStack"

    def setup(self, config):
        self.config = config if config is not None else {}
        self.api_key = self.config.get("api_key")
        self.endpoint = self.config.get("endpoint")
        self.connected = False

    def execute(self, action: str, data=None):
        if action == "connect":
            self.connected = True
            return {"status": "connected", "details": self.config}
        elif action == "push_lead":
            if not self.connected:
                raise RuntimeError("No conectado al CRM")
            return {"status": "lead_sent", "lead": data}
        elif action == "get_status":
            return {"connected": self.connected}
        else:
            raise ValueError(f"Acción no soportada: {action}")

    def teardown(self):
        self.connected = False
