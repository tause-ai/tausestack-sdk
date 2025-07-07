"""
Tests de seguridad para federación MCP: JWT, peers confiables y protección de endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from services.mcp_server_api import app
import os
import jwt

client = TestClient(app)

# Configuración de entorno para los tests
def setup_module(module):
    os.environ["MCP_JWT_SECRET"] = "supersecret"
    os.environ["MCP_JWT_ALGORITHM"] = "HS256"
    os.environ["MCP_ALLOWED_PEERS"] = "http://peer-allowed"

def make_jwt(payload=None, secret=None):
    secret = secret or "supersecret"
    base = {"iss": "test", "exp": 9999999999}
    if payload:
        base.update(payload)
    return jwt.encode(base, secret, algorithm="HS256")

def test_federation_no_token():
    resp = client.post("/federation/memory/pull", json={"url": "http://peer-allowed"})
    assert resp.status_code == 401

def test_federation_invalid_token():
    token = "bad.token.value"
    resp = client.post("/federation/memory/pull", json={"url": "http://peer-allowed"}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401

def test_federation_peer_not_allowed():
    token = make_jwt()
    resp = client.post("/federation/memory/pull", json={"url": "http://peer-blocked"}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403

def test_federation_token_missing_claims():
    token = jwt.encode({"foo": "bar"}, "supersecret", algorithm="HS256")
    resp = client.post("/federation/memory/pull", json={"url": "http://peer-allowed"}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401

def test_federation_token_and_peer_ok(monkeypatch):
    token = make_jwt()
    # Mock httpx.get para evitar request real
    import httpx
    def mock_get(*args, **kwargs):
        class Resp:
            status_code = 200
            def raise_for_status(self): pass
            def json(self): return {"memories": []}
        return Resp()
    monkeypatch.setattr(httpx, "get", mock_get)
    resp = client.post("/federation/memory/pull", json={"url": "http://peer-allowed"}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
