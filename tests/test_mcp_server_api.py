"""
Tests de integración para el microservicio MCP Server (memoria y tools de agentes).
Valida registro, consulta, actualización y manejo de errores de memoria y tools.
"""
import pytest
from fastapi.testclient import TestClient
from services.mcp_server_api import app

client = TestClient(app)

def test_register_agent_memory():
    data = {"agent_id": "agent_test_1", "context": {"foo": "bar"}}
    resp = client.post("/memory/register", json=data)
    assert resp.status_code == 200
    result = resp.json()
    assert result["agent_id"] == "agent_test_1"
    assert result["context"]["foo"] == "bar"

def test_query_agent_memory():
    # Primero registrar
    data = {"agent_id": "agent_test_2", "context": {"alpha": 123}}
    client.post("/memory/register", json=data)
    # Luego consultar
    resp = client.get("/memory/agent_test_2")
    assert resp.status_code == 200
    result = resp.json()
    assert result["agent_id"] == "agent_test_2"
    assert result["context"]["alpha"] == 123

def test_update_agent_memory():
    # Registrar primero
    data = {"agent_id": "agent_test_3", "context": {"x": 1}}
    client.post("/memory/register", json=data)
    # Sobrescribir con POST (no PUT)
    update = {"agent_id": "agent_test_3", "context": {"x": 99, "y": 42}}
    resp = client.post("/memory/register", json=update)
    assert resp.status_code == 200
    result = resp.json()
    assert result["context"]["x"] == 99
    assert result["context"]["y"] == 42

def test_register_and_query_tool():
    data = {"tool_id": "tool_test_1", "name": "toolA", "description": "demo", "config": {}}
    resp = client.post("/tools/register", json=data)
    assert resp.status_code == 200
    result = resp.json()
    assert result["tool_id"] == "tool_test_1"
    assert result["name"] == "toolA"
    # Consultar tool
    resp2 = client.get("/tools/tool_test_1")
    assert resp2.status_code == 200
    result2 = resp2.json()
    assert result2["tool_id"] == "tool_test_1"
    assert result2["name"] == "toolA"

def test_memory_not_found():
    resp = client.get("/memory/agent_no_exist")
    assert resp.status_code == 404

def test_tool_not_found():
    resp = client.get("/tools/tool_no_exist")
    assert resp.status_code == 404
