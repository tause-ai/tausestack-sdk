import pytest
from fastapi import status
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session

# Pruebas para los endpoints de la API
class TestUserEndpoints:
    def test_get_users_unauthenticated(self, test_client):
        """Debe requerir autenticación"""
        response = test_client.get("/users")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_users_authenticated(self, authenticated_client):
        """Debe devolver la lista de usuarios para usuarios autenticados"""
        response = authenticated_client.get("/users")
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)

class TestOrganizationEndpoints:
    def test_create_organization_unauthenticated(self, test_client):
        """Debe requerir autenticación"""
        response = test_client.post("/organizations", json={"name": "Test Org"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_organization_authenticated(self, authenticated_client):
        """Debe permitir a usuarios autenticados crear organizaciones"""
        org_data = {"name": "Test Org", "description": "Test Description"}
        response = authenticated_client.post("/organizations", json=org_data)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["success"] is True
        assert response.json()["data"]["name"] == "Test Org"

    def test_list_organizations(self, authenticated_client):
        """Debe listar organizaciones"""
        response = authenticated_client.get("/organizations")
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)

# Pruebas de integración con base de datos
class TestDatabaseIntegration:
    def test_organization_creation_persists(self, authenticated_client):
        """Verifica que las organizaciones se guarden en la base de datos"""
        # Crear organización
        org_data = {"name": "Persistent Org", "description": "Should persist"}
        create_response = authenticated_client.post("/organizations", json=org_data)
        assert create_response.status_code == status.HTTP_200_OK
        
        # Verificar que aparece en el listado
        list_response = authenticated_client.get("/organizations")
        orgs = list_response.json()
        assert any(org["name"] == "Persistent Org" for org in orgs)

# Pruebas de manejo de errores
class TestErrorHandling:
    def test_invalid_json_returns_422(self, authenticated_client):
        """Debe manejar JSON inválido"""
        response = authenticated_client.post(
            "/organizations", 
            content=b"{invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_duplicate_organization_name(self, authenticated_client):
        """No debe permitir nombres de organización duplicados"""
        org_data = {"name": "Unique Org"}
        
        # Primera creación exitosa
        response1 = authenticated_client.post("/organizations", json=org_data)
        assert response1.status_code == status.HTTP_200_OK
        
        # Segunda creación con el mismo nombre debe fallar
        response2 = authenticated_client.post("/organizations", json=org_data)
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        assert "ya existe" in response2.json().get("detail", "").lower()
