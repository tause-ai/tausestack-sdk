"""
FederationClient: utilidad para federar memoria y tools desde MCPs externos.
Permite consumir endpoints remotos y sincronizar con el MCP local.
"""
import httpx

class FederationClient:
    def __init__(self, base_url: str, token: str = None):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}

    def pull_memories(self):
        url = f"{self.base_url}/memory/all"
        resp = httpx.get(url, headers=self.headers, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def pull_tools(self):
        url = f"{self.base_url}/tools"
        resp = httpx.get(url, headers=self.headers, timeout=10)
        resp.raise_for_status()
        return resp.json()
