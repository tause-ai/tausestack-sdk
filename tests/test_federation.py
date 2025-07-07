"""
Tests de integración para federación de memoria y tools entre MCPs.
Mockea un MCP remoto y valida que FederationClient y los endpoints de federación funcionan correctamente.
"""
import pytest
from fastapi.testclient import TestClient
from services.mcp_server_api import app, AGENT_MEMORIES, TOOLS, AgentMemory, ToolRegistration
from core.utils.federation_client import FederationClient
from unittest.mock import patch

client = TestClient(app)

MOCK_REMOTE_MEMORIES = {"memories": [
    {"agent_id": "federated1", "context": {"foo": "bar"}},
    {"agent_id": "federated2", "context": {"alpha": 42}}
]}
MOCK_REMOTE_TOOLS = [
    {"tool_id": "tool_fed_1", "name": "ToolFed", "description": "desc", "config": {}}
]

@patch("httpx.get")
def test_pull_federated_memory(mock_get):
    AGENT_MEMORIES.clear()
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = MOCK_REMOTE_MEMORIES
    resp = client.post("/federation/memory/pull", json={"url": "http://remote-mcp"})
    assert resp.status_code == 200
    assert AGENT_MEMORIES["federated1"].context["foo"] == "bar"
    assert AGENT_MEMORIES["federated2"].context["alpha"] == 42

@patch("httpx.get")
def test_pull_federated_tools(mock_get):
    TOOLS.clear()
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = MOCK_REMOTE_TOOLS
    resp = client.post("/federation/tools/pull", json={"url": "http://remote-mcp"})
    assert resp.status_code == 200
    assert TOOLS["tool_fed_1"].name == "ToolFed"

@patch("httpx.get")
def test_federation_client_pull_memories(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = MOCK_REMOTE_MEMORIES
    client_fed = FederationClient("http://remote-mcp")
    data = client_fed.pull_memories()
    assert "memories" in data
    assert data["memories"][0]["agent_id"] == "federated1"

@patch("httpx.get")
def test_federation_client_pull_tools(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = MOCK_REMOTE_TOOLS
    client_fed = FederationClient("http://remote-mcp")
    data = client_fed.pull_tools()
    assert data[0]["tool_id"] == "tool_fed_1"
