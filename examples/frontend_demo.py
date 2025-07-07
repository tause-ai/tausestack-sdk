#!/usr/bin/env python3
"""
🎯 Demo del Frontend TauseStack v0.6.0
Genera actividad en el API Gateway para mostrar datos reales en el Admin UI
"""
import asyncio
import aiohttp
import random
import time
from datetime import datetime

GATEWAY_URL = "http://localhost:9001"
TENANTS = ["premium-corp", "basic-startup", "enterprise-bank", "default"]
SERVICES = ["analytics", "communications", "billing", "mcp_server"]

async def make_request(session, tenant_id, service, endpoint="/health"):
    """Hace una request al API Gateway con un tenant específico"""
    try:
        headers = {"X-Tenant-ID": tenant_id}
        url = f"{GATEWAY_URL}/{service}{endpoint}"
        
        async with session.get(url, headers=headers) as response:
            status = "✅" if response.status == 200 else "❌"
            print(f"{status} {tenant_id} -> {service}{endpoint} ({response.status})")
            return response.status == 200
    except Exception as e:
        print(f"❌ Error: {tenant_id} -> {service}: {str(e)}")
        return False

async def simulate_tenant_activity(session, tenant_id, requests_count=10):
    """Simula actividad de un tenant específico"""
    print(f"\n🏢 Simulando actividad para tenant: {tenant_id}")
    
    for i in range(requests_count):
        # Seleccionar servicio aleatorio
        service = random.choice(SERVICES)
        
        # Diferentes endpoints según el servicio
        endpoints = {
            "analytics": ["/health", "/metrics", "/reports"],
            "communications": ["/health", "/send", "/templates"],
            "billing": ["/health", "/invoices", "/payments"],
            "mcp_server": ["/health", "/agents", "/tasks"]
        }
        
        endpoint = random.choice(endpoints.get(service, ["/health"]))
        
        await make_request(session, tenant_id, service, endpoint)
        
        # Pausa aleatoria entre requests
        await asyncio.sleep(random.uniform(0.1, 0.5))

async def check_gateway_metrics():
    """Obtiene y muestra las métricas del gateway"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{GATEWAY_URL}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"\n📊 Métricas del Gateway:")
                    print(f"   • Total Requests: {data['gateway']['total_requests']}")
                    print(f"   • Success Rate: {data['gateway']['success_rate']:.1f}%")
                    print(f"   • Avg Response Time: {data['gateway']['avg_response_time']:.3f}s")
                    print(f"   • Overall Status: {data['overall_status']}")
                    
                    print(f"\n🔧 Estado de Servicios:")
                    for service, info in data['services'].items():
                        status_icon = "✅" if info['status'] == 'healthy' else "❌"
                        print(f"   {status_icon} {service}: {info['response_time']:.3f}s")
                    
                    return True
    except Exception as e:
        print(f"❌ Error obteniendo métricas: {str(e)}")
        return False

async def check_tenant_stats():
    """Obtiene y muestra estadísticas de tenants"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{GATEWAY_URL}/admin/tenants") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"\n👥 Estadísticas de Tenants:")
                    print(f"   • Total Tenants: {data['total_tenants']}")
                    print(f"   • Tenants Activos: {', '.join(data['tenants'])}")
                    
                    print(f"\n📈 Uso por Tenant:")
                    for tenant, requests in data['usage_stats'].items():
                        print(f"   • {tenant}: {requests} requests")
                    
                    return True
    except Exception as e:
        print(f"❌ Error obteniendo stats de tenants: {str(e)}")
        return False

async def main():
    """Función principal del demo"""
    print("🚀 TauseStack v0.6.0 - Demo del Frontend")
    print("=" * 50)
    
    # Verificar que el gateway esté funcionando
    print("🔍 Verificando API Gateway...")
    if not await check_gateway_metrics():
        print("❌ API Gateway no disponible. Ejecuta: python scripts/start_services.py")
        return
    
    print("\n✅ API Gateway funcionando correctamente!")
    
    # Mostrar estadísticas iniciales
    await check_tenant_stats()
    
    print(f"\n🎯 Iniciando simulación de actividad...")
    print(f"💡 Abre el Admin UI en: http://localhost:3001")
    print(f"📊 Verás los datos actualizándose en tiempo real")
    
    async with aiohttp.ClientSession() as session:
        # Simular actividad continua
        for round_num in range(1, 6):  # 5 rondas de actividad
            print(f"\n🔄 Ronda {round_num}/5 - Generando actividad...")
            
            # Simular actividad para cada tenant
            tasks = []
            for tenant in TENANTS:
                requests_count = random.randint(5, 15)
                task = simulate_tenant_activity(session, tenant, requests_count)
                tasks.append(task)
            
            # Ejecutar todas las simulaciones en paralelo
            await asyncio.gather(*tasks)
            
            # Mostrar métricas actualizadas
            print(f"\n📊 Métricas después de la ronda {round_num}:")
            await check_gateway_metrics()
            await check_tenant_stats()
            
            if round_num < 5:
                print(f"\n⏱️  Esperando 10 segundos antes de la siguiente ronda...")
                await asyncio.sleep(10)
    
    print(f"\n🎉 Demo completado!")
    print(f"💡 El Admin UI ahora muestra datos reales de actividad")
    print(f"🔄 Los datos se actualizan automáticamente cada 30 segundos")

if __name__ == "__main__":
    asyncio.run(main()) 