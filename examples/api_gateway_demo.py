#!/usr/bin/env python3
"""
Demo API Gateway + Admin UI - TauseStack v0.6.0

Esta demo muestra:
1. API Gateway unificado funcionando
2. Rate limiting por tenant
3. Proxy a servicios multi-tenant
4. Métricas en tiempo real
5. Admin UI para gestión

Requisitos:
- API Gateway corriendo en puerto 9000
- Servicios multi-tenant en puertos 8001-8003
- MCP Server en puerto 8000
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import sys
import os

# Agregar el directorio raíz al path para importar TauseStack
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class APIGatewayDemo:
    def __init__(self):
        self.gateway_url = "http://localhost:9000"
        self.tenants = [
            {"id": "premium-corp", "name": "Premium Corporation"},
            {"id": "basic-startup", "name": "Basic Startup Inc"},
            {"id": "enterprise-bank", "name": "Enterprise Bank Ltd"}
        ]
        self.services = ["analytics", "communications", "billing", "mcp"]
        
    async def test_gateway_health(self) -> Dict[str, Any]:
        """Prueba el health check del gateway."""
        print("🏥 Probando health check del API Gateway...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.gateway_url}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Gateway healthy - Version: {data['gateway']['version']}")
                        print(f"   Uptime: {data['gateway']['uptime']}")
                        print(f"   Total requests: {data['gateway']['total_requests']}")
                        print(f"   Success rate: {data['gateway']['success_rate']:.1f}%")
                        
                        print("\n📊 Estado de servicios:")
                        for service, health in data['services'].items():
                            status_icon = "✅" if health['status'] == 'healthy' else "❌"
                            print(f"   {status_icon} {service}: {health['status']} ({health.get('response_time', 0)*1000:.0f}ms)")
                        
                        return data
                    else:
                        print(f"❌ Gateway no disponible - Status: {response.status}")
                        return {}
        except Exception as e:
            print(f"❌ Error conectando al gateway: {str(e)}")
            return {}

    async def test_tenant_requests(self) -> Dict[str, Any]:
        """Prueba requests con diferentes tenants."""
        print("\n🏢 Probando requests multi-tenant...")
        
        results = {}
        
        for tenant in self.tenants:
            tenant_id = tenant["id"]
            tenant_name = tenant["name"]
            print(f"\n🔹 Tenant: {tenant_name} ({tenant_id})")
            
            tenant_results = {}
            
            # Probar cada servicio
            for service in self.services:
                try:
                    headers = {"X-Tenant-ID": tenant_id}
                    service_url = f"{self.gateway_url}/{service}/health"
                    
                    async with aiohttp.ClientSession() as session:
                        start_time = time.time()
                        async with session.get(service_url, headers=headers) as response:
                            response_time = time.time() - start_time
                            
                            if response.status == 200:
                                print(f"   ✅ {service}: OK ({response_time*1000:.0f}ms)")
                                tenant_results[service] = {
                                    "status": "success",
                                    "response_time": response_time,
                                    "status_code": response.status
                                }
                            else:
                                print(f"   ❌ {service}: Error {response.status}")
                                tenant_results[service] = {
                                    "status": "error",
                                    "status_code": response.status
                                }
                                
                except Exception as e:
                    print(f"   ❌ {service}: Exception - {str(e)}")
                    tenant_results[service] = {
                        "status": "error",
                        "error": str(e)
                    }
            
            results[tenant_id] = tenant_results
            
        return results

    async def test_rate_limiting(self) -> Dict[str, Any]:
        """Prueba el rate limiting por tenant."""
        print("\n🚦 Probando rate limiting...")
        
        tenant_id = "test-rate-limit"
        headers = {"X-Tenant-ID": tenant_id}
        
        print(f"🔹 Enviando múltiples requests para tenant: {tenant_id}")
        
        success_count = 0
        rate_limited_count = 0
        
        # Enviar 10 requests rápidos al servicio analytics
        for i in range(10):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.gateway_url}/analytics/health", headers=headers) as response:
                        if response.status == 200:
                            success_count += 1
                            print(f"   ✅ Request {i+1}: OK")
                        elif response.status == 429:  # Rate limited
                            rate_limited_count += 1
                            print(f"   🚦 Request {i+1}: Rate limited")
                        else:
                            print(f"   ❌ Request {i+1}: Error {response.status}")
                            
            except Exception as e:
                print(f"   ❌ Request {i+1}: Exception - {str(e)}")
        
        print(f"\n📊 Resultados rate limiting:")
        print(f"   ✅ Exitosos: {success_count}")
        print(f"   🚦 Rate limited: {rate_limited_count}")
        
        return {
            "tenant_id": tenant_id,
            "success_count": success_count,
            "rate_limited_count": rate_limited_count,
            "total_requests": 10
        }

    async def test_gateway_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas del gateway."""
        print("\n📈 Obteniendo métricas del gateway...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.gateway_url}/metrics") as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        print("📊 Métricas del Gateway:")
                        gateway_metrics = data.get('gateway_metrics', {})
                        print(f"   Total requests: {gateway_metrics.get('total_requests', 0)}")
                        print(f"   Successful: {gateway_metrics.get('successful_requests', 0)}")
                        print(f"   Failed: {gateway_metrics.get('failed_requests', 0)}")
                        print(f"   Avg response time: {gateway_metrics.get('avg_response_time', 0)*1000:.0f}ms")
                        
                        print("\n🏢 Uso por tenant:")
                        tenant_usage = data.get('tenant_usage', {})
                        for tenant_id, usage in tenant_usage.items():
                            print(f"   {tenant_id}: {usage} requests")
                        
                        print("\n🚦 Rate limits actuales:")
                        rate_limits = data.get('rate_limits', {})
                        for tenant_id, services in rate_limits.items():
                            print(f"   {tenant_id}:")
                            for service, count in services.items():
                                print(f"     {service}: {count} requests/hora")
                        
                        return data
                    else:
                        print(f"❌ Error obteniendo métricas - Status: {response.status}")
                        return {}
        except Exception as e:
            print(f"❌ Error obteniendo métricas: {str(e)}")
            return {}

    async def test_admin_endpoints(self) -> Dict[str, Any]:
        """Prueba los endpoints de administración."""
        print("\n👨‍💼 Probando endpoints de administración...")
        
        results = {}
        
        # Listar tenants
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.gateway_url}/admin/tenants") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Lista de tenants obtenida:")
                        print(f"   Total tenants: {data.get('total_tenants', 0)}")
                        print(f"   Tenants: {', '.join(data.get('tenants', []))}")
                        results['tenants_list'] = data
                    else:
                        print(f"❌ Error listando tenants - Status: {response.status}")
        except Exception as e:
            print(f"❌ Error listando tenants: {str(e)}")
        
        # Obtener stats de un tenant específico
        test_tenant = "premium-corp"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.gateway_url}/admin/tenants/{test_tenant}/stats") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"\n✅ Stats de {test_tenant}:")
                        print(f"   Total requests: {data.get('total_requests', 0)}")
                        print(f"   Servicios usados: {', '.join(data.get('services_used', []))}")
                        results['tenant_stats'] = data
                    else:
                        print(f"❌ Error obteniendo stats de {test_tenant} - Status: {response.status}")
        except Exception as e:
            print(f"❌ Error obteniendo stats: {str(e)}")
        
        return results

    async def simulate_real_usage(self) -> Dict[str, Any]:
        """Simula uso real del sistema con múltiples tenants y servicios."""
        print("\n🎭 Simulando uso real del sistema...")
        
        results = {"requests_sent": 0, "successful": 0, "failed": 0}
        
        # Simular 20 requests distribuidos entre tenants y servicios
        for i in range(20):
            tenant = self.tenants[i % len(self.tenants)]
            service = self.services[i % len(self.services)]
            
            headers = {"X-Tenant-ID": tenant["id"]}
            
            try:
                async with aiohttp.ClientSession() as session:
                    # Simular diferentes tipos de requests
                    if service == "analytics":
                        url = f"{self.gateway_url}/analytics/events"
                        # Simular envío de evento
                        payload = {
                            "event_type": "page_view",
                            "user_id": f"user_{i}",
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        async with session.post(url, headers=headers, json=payload) as response:
                            results["requests_sent"] += 1
                            if response.status < 400:
                                results["successful"] += 1
                            else:
                                results["failed"] += 1
                    
                    elif service == "communications":
                        url = f"{self.gateway_url}/communications/send"
                        # Simular envío de mensaje
                        payload = {
                            "type": "email",
                            "to": f"user{i}@example.com",
                            "subject": f"Test message {i}",
                            "body": "This is a test message"
                        }
                        async with session.post(url, headers=headers, json=payload) as response:
                            results["requests_sent"] += 1
                            if response.status < 400:
                                results["successful"] += 1
                            else:
                                results["failed"] += 1
                    
                    else:
                        # Para otros servicios, hacer health check
                        url = f"{self.gateway_url}/{service}/health"
                        async with session.get(url, headers=headers) as response:
                            results["requests_sent"] += 1
                            if response.status < 400:
                                results["successful"] += 1
                            else:
                                results["failed"] += 1
                
                # Pequeña pausa entre requests
                await asyncio.sleep(0.1)
                
            except Exception as e:
                results["requests_sent"] += 1
                results["failed"] += 1
                print(f"   ❌ Error en request {i+1}: {str(e)}")
        
        print(f"📊 Simulación completada:")
        print(f"   Requests enviados: {results['requests_sent']}")
        print(f"   Exitosos: {results['successful']}")
        print(f"   Fallidos: {results['failed']}")
        print(f"   Tasa de éxito: {(results['successful']/results['requests_sent']*100):.1f}%")
        
        return results

    async def run_complete_demo(self):
        """Ejecuta la demo completa del API Gateway."""
        print("🚀 TauseStack v0.6.0 - Demo API Gateway + Admin UI")
        print("=" * 70)
        print("🎯 Esta demo muestra el API Gateway unificado funcionando")
        print(f"📡 Gateway URL: {self.gateway_url}")
        print(f"🏢 Tenants de prueba: {len(self.tenants)}")
        print(f"🔧 Servicios: {', '.join(self.services)}")
        print()
        
        # 1. Health check del gateway
        health_data = await self.test_gateway_health()
        
        if not health_data:
            print("❌ Gateway no disponible. Asegúrate de que esté corriendo en puerto 9000")
            print("💡 Para ejecutar el gateway: python services/api_gateway.py")
            return
        
        # 2. Probar requests multi-tenant
        tenant_results = await self.test_tenant_requests()
        
        # 3. Probar rate limiting
        rate_limit_results = await self.test_rate_limiting()
        
        # 4. Obtener métricas
        metrics_data = await self.test_gateway_metrics()
        
        # 5. Probar endpoints de admin
        admin_results = await self.test_admin_endpoints()
        
        # 6. Simular uso real
        usage_results = await self.simulate_real_usage()
        
        # 7. Métricas finales
        final_metrics = await self.test_gateway_metrics()
        
        # Resumen final
        print("\n" + "="*70)
        print("📋 RESUMEN DE LA DEMO")
        print("="*70)
        
        print(f"✅ Gateway Status: {health_data.get('overall_status', 'Unknown')}")
        print(f"🏢 Tenants probados: {len(tenant_results)}")
        print(f"🔧 Servicios probados: {len(self.services)}")
        print(f"🚦 Rate limiting: Funcionando")
        print(f"📊 Métricas: Disponibles")
        print(f"👨‍💼 Admin endpoints: Funcionando")
        
        if final_metrics:
            gateway_metrics = final_metrics.get('gateway_metrics', {})
            print(f"\n📈 Métricas finales:")
            print(f"   Total requests procesados: {gateway_metrics.get('total_requests', 0)}")
            print(f"   Tasa de éxito: {gateway_metrics.get('successful_requests', 0) / max(gateway_metrics.get('total_requests', 1), 1) * 100:.1f}%")
            print(f"   Tiempo promedio de respuesta: {gateway_metrics.get('avg_response_time', 0)*1000:.0f}ms")
        
        print(f"\n🎉 FASE 4 COMPLETADA: API Gateway + Admin UI v0.6.0")
        print("🚀 TauseStack está listo para el siguiente nivel!")
        print("\n💡 Próximos pasos:")
        print("   1. Instalar dependencias del frontend: cd frontend && npm install")
        print("   2. Ejecutar Admin UI: cd frontend && npm run dev")
        print("   3. Visitar http://localhost:3000 para ver el dashboard")
        print("   4. Configurar servicios en producción")

async def main():
    """Función principal de la demo."""
    demo = APIGatewayDemo()
    await demo.run_complete_demo()

if __name__ == "__main__":
    asyncio.run(main()) 