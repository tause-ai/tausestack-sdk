"""
Ejemplo de integración: agente Python interactuando con el servidor MCP TauseStack.
Registra memoria, consulta memoria y tools, y registra una nueva tool.
"""
import requests

API_URL = "http://localhost:8000"

# 1. Registrar memoria de agente
def register_agent_memory(agent_id, context):
    resp = requests.post(f"{API_URL}/memory/register", json={"agent_id": agent_id, "context": context})
    print("Memoria registrada:", resp.json())

# 2. Consultar memoria de agente
def get_agent_memory(agent_id):
    resp = requests.get(f"{API_URL}/memory/{agent_id}")
    print("Memoria recuperada:", resp.json())

# 3. Registrar una tool
def register_tool(tool_id, name, description, config=None):
    data = {"tool_id": tool_id, "name": name, "description": description, "config": config or {}}
    resp = requests.post(f"{API_URL}/tools/register", json=data)
    print("Tool registrada:", resp.json())

# 4. Listar tools disponibles
def list_tools():
    resp = requests.get(f"{API_URL}/tools")
    print("Tools registradas:", resp.json())

if __name__ == "__main__":
    agent_id = "agente_demo"
    context = {"estado": "activo", "tarea": "demo MCP"}
    register_agent_memory(agent_id, context)
    get_agent_memory(agent_id)
    register_tool("tool_demo", "Demo Tool", "Herramienta de prueba MCP", {"param": 123})
    list_tools()
