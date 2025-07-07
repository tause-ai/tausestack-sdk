#!/usr/bin/env python3
"""
Script de prueba para verificar la autenticación de Supabase
"""

import asyncio
import httpx
import json
from datetime import datetime

# Configuración
API_BASE_URL = "http://localhost:9001"
SUPABASE_URL = "https://vjoxmprmcbkmhwmbniaz.supabase.co"

async def test_public_endpoints():
    """Probar endpoints públicos que no requieren autenticación."""
    print("🔍 Probando endpoints públicos...")
    
    async with httpx.AsyncClient() as client:
        # Health check
        response = await client.get(f"{API_BASE_URL}/health")
        print(f"✅ Health check: {response.status_code}")
        
        # API info
        response = await client.get(f"{API_BASE_URL}/api")
        print(f"✅ API info: {response.status_code}")
        
        # Frontend (debería servir el index)
        response = await client.get(f"{API_BASE_URL}/")
        print(f"✅ Frontend: {response.status_code}")

async def test_protected_endpoints_without_auth():
    """Probar endpoints protegidos sin autenticación (deberían fallar)."""
    print("\n🔒 Probando endpoints protegidos SIN autenticación...")
    
    async with httpx.AsyncClient() as client:
        # Métricas (requiere admin/monitor)
        response = await client.get(f"{API_BASE_URL}/metrics")
        print(f"❌ Métricas sin auth: {response.status_code} (esperado: 401)")
        
        # Admin tenants (requiere admin)
        response = await client.get(f"{API_BASE_URL}/admin/tenants")
        print(f"❌ Admin tenants sin auth: {response.status_code} (esperado: 401)")

async def test_with_mock_token():
    """Probar con un token mock (debería fallar por firma inválida)."""
    print("\n🎭 Probando con token mock...")
    
    # Token mock inválido
    mock_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0Iiwicm9sZSI6ImF1dGhlbnRpY2F0ZWQiLCJhdWQiOiJhdXRoZW50aWNhdGVkIn0.invalid_signature"
    
    headers = {"Authorization": f"Bearer {mock_token}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/metrics", headers=headers)
        print(f"❌ Métricas con token mock: {response.status_code} (esperado: 401)")

async def test_supabase_connection():
    """Probar conexión a Supabase."""
    print("\n🔗 Probando conexión a Supabase...")
    
    async with httpx.AsyncClient() as client:
        # Probar JWKS endpoint
        try:
            response = await client.get(f"{SUPABASE_URL}/.well-known/jwks.json")
            if response.status_code == 200:
                print("✅ JWKS endpoint accesible")
            else:
                print(f"⚠️ JWKS endpoint: {response.status_code}")
        except Exception as e:
            print(f"❌ Error conectando a JWKS: {e}")

def print_test_instructions():
    """Imprimir instrucciones para testing manual."""
    print("\n" + "="*60)
    print("🧪 INSTRUCCIONES PARA TESTING MANUAL")
    print("="*60)
    print("""
Para probar con un token real de Supabase:

1. Ve a tu aplicación frontend (http://localhost:3000)
2. Inicia sesión con Supabase
3. Abre DevTools > Console y ejecuta:
   ```javascript
   const { data: { session } } = await supabase.auth.getSession()
   console.log('Token:', session?.access_token)
   ```
4. Copia el token y úsalo en curl:
   ```bash
   curl http://localhost:9001/metrics \\
     -H "Authorization: Bearer TU_TOKEN_AQUI"
   ```

Para crear un usuario con rol admin:
1. Ve a Supabase Dashboard > Authentication > Users
2. Edita un usuario y agrega en app_metadata:
   ```json
   {
     "roles": ["admin"]
   }
   ```
    """)

async def main():
    """Función principal de testing."""
    print("🚀 Iniciando tests de autenticación Supabase")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    try:
        await test_public_endpoints()
        await test_protected_endpoints_without_auth()
        await test_with_mock_token()
        await test_supabase_connection()
        
        print_test_instructions()
        
    except Exception as e:
        print(f"❌ Error durante testing: {e}")
    
    print("\n✅ Testing completado!")

if __name__ == "__main__":
    asyncio.run(main()) 