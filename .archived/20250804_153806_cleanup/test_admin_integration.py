#!/usr/bin/env python3
"""
Script de verificación para la integración completa del panel de administración
"""

import requests
import json
import time
from datetime import datetime

def test_service_health(service_name, url, endpoint=""):
    """Probar el health check de un servicio"""
    try:
        response = requests.get(f"{url}{endpoint}", timeout=10)
        if response.status_code == 200:
            print(f"✅ {service_name} - HEALTHY: {response.json()}")
            return True
        else:
            print(f"❌ {service_name} - UNHEALTHY: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ {service_name} - ERROR: {str(e)}")
        return False

def test_admin_api_direct():
    """Probar Admin API directamente"""
    print("\n🔍 Testing Admin API directly...")
    
    # Test GET /admin/apis
    try:
        response = requests.get("http://localhost:8001/admin/apis", timeout=10)
        if response.status_code == 200:
            apis = response.json()
            print(f"✅ Admin API - GET /admin/apis: {len(apis)} APIs found")
            return True
        else:
            print(f"❌ Admin API - GET /admin/apis failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Admin API - GET /admin/apis error: {str(e)}")
        return False

def test_ai_service():
    """Probar AI Service"""
    print("\n🔍 Testing AI Service...")
    
    # Test health check
    if test_service_health("AI Service", "http://localhost:8002", "/ai/health"):
        # Test completion endpoint
        try:
            response = requests.post(
                "http://localhost:8002/ai/completion",
                json={
                    "prompt": "Hello", 
                    "max_tokens": 10,
                    "model": "gpt-3.5-turbo",
                    "tenant_id": "test-tenant"
                },
                timeout=10
            )
            if response.status_code == 200:
                result = response.json()
                print(f"✅ AI Service - Completion: {result.get('text', 'No text')[:50]}...")
                return True
        except Exception as e:
            print(f"❌ AI Service - Completion error: {str(e)}")
    
    return False

def test_agent_api():
    """Probar Agent API"""
    print("\n🔍 Testing Agent API...")
    
    # Test health check
    if test_service_health("Agent API", "http://localhost:8003", "/health"):
        # Test agents endpoint
        try:
            response = requests.get("http://localhost:8003/agents", timeout=10)
            if response.status_code == 200:
                agents = response.json()
                print(f"✅ Agent API - GET /agents: {len(agents)} agents found")
                return True
        except Exception as e:
            print(f"❌ Agent API - GET /agents error: {str(e)}")
    
    return False

def test_api_gateway():
    """Probar API Gateway"""
    print("\n🔍 Testing API Gateway...")
    
    # Test health check
    if test_service_health("API Gateway", "http://localhost:9001", "/health"):
        print("✅ API Gateway - Health check passed")
        
        # Test metrics endpoint (requires auth, so we expect 401)
        try:
            response = requests.get("http://localhost:9001/metrics", timeout=10)
            if response.status_code == 401:
                print("✅ API Gateway - Metrics endpoint properly protected")
                return True
        except Exception as e:
            print(f"❌ API Gateway - Metrics test error: {str(e)}")
    
    return False

def test_frontend():
    """Probar Frontend"""
    print("\n🔍 Testing Frontend...")
    
    try:
        response = requests.get("http://localhost:3000", timeout=10)
        if response.status_code == 200 and "TauseStack" in response.text:
            print("✅ Frontend - Main page loaded successfully")
            return True
        else:
            print(f"❌ Frontend - Main page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend - Main page error: {str(e)}")
        return False

def main():
    """Función principal de pruebas"""
    print("🚀 TauseStack Integration Test Suite")
    print("=" * 50)
    
    results = []
    
    # Test all services
    tests = [
        ("Admin API", test_admin_api_direct),
        ("AI Service", test_ai_service),
        ("Agent API", test_agent_api),
        ("API Gateway", test_api_gateway),
        ("Frontend", test_frontend)
    ]
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} tests...")
        result = test_func()
        results.append((test_name, result))
        time.sleep(1)  # Small delay between tests
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 ALL TESTS PASSED! TauseStack integration is working correctly!")
        print("\n🌐 Services Available:")
        print("   • Frontend:     http://localhost:3000")
        print("   • Admin Panel:  http://localhost:3000/admin")
        print("   • API Gateway:  http://localhost:9001")
        print("   • Admin API:    http://localhost:8001")
        print("   • AI Service:   http://localhost:8002")
        print("   • Agent API:    http://localhost:8003")
        return True
    else:
        print(f"\n⚠️  {len(results) - passed} tests failed. Please check the services.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 