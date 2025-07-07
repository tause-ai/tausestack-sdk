"""
Ejemplo de uso de FederationClient para federar memoria y tools desde un MCP remoto.
Incluye buenas prácticas de manejo de errores y validación de datos.
"""
from core.utils.federation_client import FederationClient
from services.mcp_server_api import AGENT_MEMORIES, TOOLS, AgentMemory, ToolRegistration, save_data
import sys

def federate_from_remote(remote_url, token=None):
    client = FederationClient(remote_url, token)
    try:
        # Federar memorias
        remote = client.pull_memories()
        count_mem = 0
        for mem in remote.get("memories", []):
            agent_id = mem.get("agent_id")
            context = mem.get("context", {})
            if agent_id:
                AGENT_MEMORIES[agent_id] = AgentMemory(agent_id=agent_id, context=context)
                count_mem += 1
        # Federar tools
        remote_tools = client.pull_tools()
        count_tools = 0
        for tool in remote_tools:
            tool_id = tool.get("tool_id")
            if tool_id:
                TOOLS[tool_id] = ToolRegistration(**tool)
                count_tools += 1
        save_data()
        print(f"Federación exitosa: {count_mem} memorias, {count_tools} tools importados.")
    except Exception as e:
        print(f"Error en federación: {e}", file=sys.stderr)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Federar memoria/tools desde un MCP remoto")
    parser.add_argument("--url", required=True, help="URL base del MCP remoto")
    parser.add_argument("--token", help="Token de autenticación (opcional)")
    args = parser.parse_args()
    federate_from_remote(args.url, args.token)
