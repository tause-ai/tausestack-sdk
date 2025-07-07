"""
Pruebas de integración para orquestación multiagente con MCP.
"""
import os
import pytest
import jwt
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from services.mcp_server_api import app, AGENT_MEMORIES, TOOLS
from core.utils.federation_client import FederationClient
from unittest.mock import patch, MagicMock
import json

# Configuración para pruebas
os.environ["MCP_JWT_SECRET"] = "test_secret"
os.environ["MCP_JWT_ALGORITHM"] = "HS256"
os.environ["MCP_ALLOWED_PEERS"] = "http://localhost,http://remote-mcp:8000"

# Cliente para el MCP local
client = TestClient(app)

def get_test_jwt():
    """Genera un token JWT para pruebas."""
    payload = {
        "iss": "test_issuer",
        "exp": datetime.utcnow() + timedelta(hours=1),
        "sub": "test_user",
        "role": "admin"
    }
    return jwt.encode(
        payload,
        os.environ["MCP_JWT_SECRET"],
        algorithm=os.environ["MCP_JWT_ALGORITHM"]
    )

# Headers de autenticación para pruebas
auth_headers = {"Authorization": f"Bearer {get_test_jwt()}"}

# Datos de prueba
AGENT_ANALYZER = "analyzer_agent"
AGENT_PROCESSOR = "processor_agent"
AGENT_REPORTER = "reporter_agent"
TOOL_ANALYZE = "analyze_tool"
TOOL_PROCESS = "process_tool"
TOOL_REPORT = "report_tool"

@pytest.fixture(autouse=True)
def setup_teardown():
    """Limpia el estado antes y después de cada prueba."""
    AGENT_MEMORIES.clear()
    TOOLS.clear()
    yield
    AGENT_MEMORIES.clear()
    TOOLS.clear()

def test_multi_agent_workflow():
    """
    Prueba un flujo completo de orquestación multiagente:
    1. Registrar herramientas necesarias
    2. Iniciar flujo con el agente analizador
    3. Verificar que los agentes se comunican correctamente
    """
    # 1. Registrar herramientas
    tools = [
        {
            "tool_id": TOOL_ANALYZE,
            "name": "Analyze Data",
            "description": "Analiza datos de entrada",
            "config": {}
        },
        {
            "tool_id": TOOL_PROCESS,
            "name": "Process Data",
            "description": "Procesa datos analizados",
            "config": {}
        },
        {
            "tool_id": TOOL_REPORT,
            "name": "Generate Report",
            "description": "Genera un reporte final",
            "config": {}
        }
    ]
    
    for tool in tools:
        resp = client.post("/tools/register", json=tool, headers=auth_headers)
        assert resp.status_code == 200, f"Error al registrar herramienta: {resp.text}"
    
    # 2. Iniciar flujo con el agente analizador
    initial_data = {
        "agent_id": AGENT_ANALYZER,
        "context": {
            "workflow_id": "wf_123",
            "status": "started",
            "input_data": [1, 2, 3, 4, 5],
            "next_agent": AGENT_PROCESSOR,
            "tools_used": [TOOL_ANALYZE]
        }
    }
    
    resp = client.post(
        "/memory/register", 
        json={
            "agent_id": AGENT_ANALYZER,
            "context": initial_data["context"]
        },
        headers=auth_headers
    )
    assert resp.status_code == 200, f"Error al registrar memoria del analizador: {resp.text}"
    
    # 3. Simular que el agente procesador lee la salida del analizador
    resp = client.get(f"/memory/{AGENT_ANALYZER}", headers=auth_headers)
    assert resp.status_code == 200, f"Error al obtener memoria del analizador: {resp.text}"
    analyzer_context = resp.json()["context"]
    
    # 4. Agregar lógica de procesamiento (simulada)
    processed_data = {
        "agent_id": AGENT_PROCESSOR,
        "context": {
            "workflow_id": analyzer_context["workflow_id"],
            "status": "processing",
            "input_data": analyzer_context["input_data"],
            "analysis_result": {"sum": sum(analyzer_context["input_data"])},
            "next_agent": AGENT_REPORTER,
            "tools_used": [TOOL_PROCESS],
            "source_agent": AGENT_ANALYZER
        }
    }
    
    resp = client.post(
        "/memory/register", 
        json=processed_data,
        headers=auth_headers
    )
    assert resp.status_code == 200, f"Error al registrar memoria del procesador: {resp.text}"
    
    # 5. Verificar que el agente reportero puede acceder a los datos
    resp = client.get(
        f"/memory/{AGENT_PROCESSOR}",
        headers=auth_headers
    )
    assert resp.status_code == 200, f"Error al obtener memoria del procesador: {resp.text}"
    processor_context = resp.json()["context"]
    
    # 6. Generar reporte final
    report_data = {
        "agent_id": AGENT_REPORTER,
        "context": {
            "workflow_id": processor_context["workflow_id"],
            "status": "completed",
            "analysis_result": processor_context["analysis_result"],
            "report": f"Reporte final: {processor_context['analysis_result']}",
            "tools_used": [TOOL_REPORT],
            "source_agent": AGENT_PROCESSOR
        }
    }
    
    resp = client.post(
        "/memory/register",
        json=report_data,
        headers=auth_headers
    )
    assert resp.status_code == 200, f"Error al registrar memoria del reportero: {resp.text}"
    
    # 7. Verificar que todos los agentes tienen los estados correctos
    resp = client.get(
        f"/memory/{AGENT_ANALYZER}",
        headers=auth_headers
    )
    assert resp.status_code == 200, f"Error al obtener memoria del analizador: {resp.text}"
    assert resp.json()["context"]["status"] == "started"
    
    resp = client.get(
        f"/memory/{AGENT_PROCESSOR}",
        headers=auth_headers
    )
    assert resp.status_code == 200, f"Error al obtener memoria del procesador: {resp.text}"
    assert resp.json()["context"]["status"] == "processing"
    
    resp = client.get(
        f"/memory/{AGENT_REPORTER}",
        headers=auth_headers
    )
    assert resp.status_code == 200, f"Error al obtener memoria del reportero: {resp.text}"
    assert resp.json()["context"]["status"] == "completed"
    assert "Reporte final" in resp.json()["context"]["report"]
    assert resp.json()["context"]["analysis_result"]["sum"] == 15

@patch('httpx.get')
def test_distributed_workflow_with_federation(mock_get):
    """
    Prueba un flujo de trabajo distribuido que involucra múltiples MCPs.
    """
    # Configurar mock para el MCP remoto
    remote_tools = [
        {
            "tool_id": "remote_tool_1",
            "name": "Remote Analysis",
            "description": "Herramienta remota de análisis",
            "config": {}
        }
    ]
    
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = remote_tools
    
    # 1. Sincronizar herramientas desde el MCP remoto
    resp = client.post(
        "/federation/tools/pull",
        json={
            "url": "http://remote-mcp:8000",
            "token": get_test_jwt()  # Incluir token JWT para autenticación
        },
        headers=auth_headers
    )
    assert resp.status_code == 200, f"Error al sincronizar herramientas: {resp.text}"
    
    # 2. Verificar que las herramientas remotas están disponibles
    resp = client.get("/tools", headers=auth_headers)
    assert resp.status_code == 200, f"Error al listar herramientas: {resp.text}"
    tools = resp.json()
    assert any(tool["tool_id"] == "remote_tool_1" for tool in tools), \
        f"La herramienta remota no está disponible: {tools}"
    
    # 3. Iniciar flujo de trabajo que usa herramienta remota
    workflow_data = {
        "agent_id": "workflow_manager",
        "context": {
            "workflow_id": "dist_wf_001",
            "status": "started",
            "remote_tool_used": True,
            "tools_used": ["remote_tool_1"]
        }
    }
    
    resp = client.post(
        "/memory/register",
        json=workflow_data,
        headers=auth_headers
    )
    assert resp.status_code == 200, f"Error al registrar flujo de trabajo: {resp.text}"
    
    # 4. Verificar que el flujo se completó correctamente
    resp = client.get(
        "/memory/workflow_manager",
        headers=auth_headers
    )
    assert resp.status_code == 200, f"Error al obtener memoria del workflow: {resp.text}"
    
    context = resp.json()["context"]
    assert context["status"] == "started"
    assert "remote_tool_1" in context["tools_used"], \
        f"La herramienta remota no está en la lista de herramientas usadas: {context}"
    assert context["remote_tool_used"] is True, \
        f"El campo remote_tool_used no es True: {context}"
