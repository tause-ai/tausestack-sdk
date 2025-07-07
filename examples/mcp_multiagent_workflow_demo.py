"""
Ejemplo de workflow multiagente con sincronización de memoria/contexto vía MCP.
Cada agente actualiza y consulta el MCP antes/después de su paso, demostrando coordinación real.
"""
import requests
import time

API_URL = "http://localhost:8000"

AGENTS = [
    {"id": "agente_1", "context": {"estado": "inicial", "rol": "analizador"}},
    {"id": "agente_2", "context": {"estado": "inicial", "rol": "ejecutor"}},
]

def register_agent_memory(agent_id, context):
    requests.post(f"{API_URL}/memory/register", json={"agent_id": agent_id, "context": context})

def get_agent_memory(agent_id):
    resp = requests.get(f"{API_URL}/memory/{agent_id}")
    return resp.json() if resp.status_code == 200 else None

def agent_step(agent):
    # Consulta contexto propio y del otro agente
    my_mem = get_agent_memory(agent["id"])
    other_id = AGENTS[1]["id"] if agent["id"] == AGENTS[0]["id"] else AGENTS[0]["id"]
    other_mem = get_agent_memory(other_id)
    print(f"[{agent['id']}] Contexto propio: {my_mem}")
    print(f"[{agent['id']}] Contexto del otro agente: {other_mem}")
    # Actualiza contexto
    new_context = dict(my_mem["context"])
    new_context["ultimo_paso"] = f"paso_{int(time.time())}"
    register_agent_memory(agent["id"], new_context)
    print(f"[{agent['id']}] Contexto actualizado: {new_context}")

if __name__ == "__main__":
    # Registrar memoria inicial
    for ag in AGENTS:
        register_agent_memory(ag["id"], ag["context"])
    print("--- INICIO WORKFLOW MULTIAGENTE ---")
    # Simulación de pasos alternos
    for ciclo in range(2):
        print(f"\n--- Ciclo {ciclo+1} ---")
        for ag in AGENTS:
            agent_step(ag)
            time.sleep(1)
    print("--- FIN WORKFLOW ---")
