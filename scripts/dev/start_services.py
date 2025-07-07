#!/usr/bin/env python3
"""
Script para lanzar todos los servicios de TauseStack v0.6.0
"""

import subprocess
import time
import sys
import os
from pathlib import Path

# Importar configuración centralizada
try:
    from tausestack.config.settings import settings
    USE_SETTINGS = True
except ImportError:
    USE_SETTINGS = False
    print("⚠️  Configuración centralizada no disponible, usando valores por defecto")

# Configuración de servicios
SERVICES = [
    {
        "name": "Analytics Service",
        "port": settings.DEV_ANALYTICS_PORT if USE_SETTINGS else 8001,
        "path": "services/analytics/api/main.py",
        "app": "services.analytics.api.main:app"
    },
    {
        "name": "Communications Service", 
        "port": settings.DEV_COMMUNICATIONS_PORT if USE_SETTINGS else 8002,
        "path": "services/communications/api/main.py",
        "app": "services.communications.api.main:app"
    },
    {
        "name": "Billing Service",
        "port": settings.DEV_BILLING_PORT if USE_SETTINGS else 8003,
        "path": "services/billing/api/main.py", 
        "app": "services.billing.api.main:app"
    },
    {
        "name": "MCP Server",
        "port": settings.DEV_MCP_PORT if USE_SETTINGS else 8000,
        "path": "services/mcp_server_api.py",
        "app": "services.mcp_server_api:app"
    },
    {
        "name": "AI Services",
        "port": settings.DEV_AI_SERVICES_PORT if USE_SETTINGS else 8005,
        "path": "services/ai_services/api/main.py",
        "app": "services.ai_services.api.main:app"
    }
]

def check_service_exists(service_path):
    """Verificar si el archivo del servicio existe."""
    return Path(service_path).exists()

def start_service(service):
    """Iniciar un servicio específico."""
    print(f"🚀 Iniciando {service['name']} en puerto {service['port']}...")
    
    if not check_service_exists(service['path']):
        print(f"❌ Archivo no encontrado: {service['path']}")
        return None
    
    try:
        # Usar configuración de host dinámico
        host = "0.0.0.0" if USE_SETTINGS and settings.is_production else "127.0.0.1"
        
        cmd = [
            "uvicorn",
            service['app'],
            "--host", host,
            "--port", str(service['port']),
            "--reload" if not (USE_SETTINGS and settings.is_production) else "--no-reload"
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print(f"✅ {service['name']} iniciado (PID: {process.pid})")
        return process
        
    except Exception as e:
        print(f"❌ Error iniciando {service['name']}: {e}")
        return None

def start_api_gateway():
    """Iniciar el API Gateway."""
    gateway_port = settings.DEV_API_GATEWAY_PORT if USE_SETTINGS else 9001
    print(f"🌐 Iniciando API Gateway en puerto {gateway_port}...")
    
    try:
        # Usar configuración de host dinámico
        host = "0.0.0.0" if USE_SETTINGS and settings.is_production else "127.0.0.1"
        
        cmd = [
            "uvicorn",
            "services.api_gateway:app",
            "--host", host, 
            "--port", str(gateway_port),
            "--reload" if not (USE_SETTINGS and settings.is_production) else "--no-reload"
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print(f"✅ API Gateway iniciado (PID: {process.pid})")
        return process
        
    except Exception as e:
        print(f"❌ Error iniciando API Gateway: {e}")
        return None

def main():
    """Función principal."""
    print("🚀 TauseStack v0.6.0 - Iniciando todos los servicios")
    print("=" * 60)
    
    if USE_SETTINGS:
        print(f"📍 Entorno: {settings.NODE_ENV}")
        print(f"🌐 Dominio base: {settings.BASE_DOMAIN}")
        print(f"🏢 Multi-tenant: {'Sí' if settings.MULTI_TENANT_MODE else 'No'}")
        print("-" * 60)
    
    # Verificar que estamos en el directorio correcto
    if not Path("services").exists():
        print("❌ Error: Ejecutar desde el directorio raíz de TauseStack")
        sys.exit(1)
    
    processes = []
    
    # Iniciar servicios individuales
    for service in SERVICES:
        process = start_service(service)
        if process:
            processes.append((service['name'], process))
        time.sleep(2)  # Esperar entre servicios
    
    # Iniciar API Gateway
    gateway_process = start_api_gateway()
    if gateway_process:
        processes.append(("API Gateway", gateway_process))
    
    print("\n" + "=" * 60)
    print(f"✅ Servicios iniciados: {len(processes)}")
    
    for name, process in processes:
        print(f"   • {name}: PID {process.pid}")
    
    # URLs dinámicas basadas en configuración
    gateway_port = settings.DEV_API_GATEWAY_PORT if USE_SETTINGS else 9001
    analytics_port = settings.DEV_ANALYTICS_PORT if USE_SETTINGS else 8001
    communications_port = settings.DEV_COMMUNICATIONS_PORT if USE_SETTINGS else 8002
    billing_port = settings.DEV_BILLING_PORT if USE_SETTINGS else 8003
    mcp_port = settings.DEV_MCP_PORT if USE_SETTINGS else 8000
    ai_port = settings.DEV_AI_SERVICES_PORT if USE_SETTINGS else 8005
    frontend_port = settings.DEV_FRONTEND_PORT if USE_SETTINGS else 3000
    
    host = "localhost" if not (USE_SETTINGS and settings.is_production) else settings.BASE_DOMAIN
    
    print("\n🌐 URLs disponibles:")
    print(f"   • API Gateway: http://{host}:{gateway_port}")
    print(f"   • Gateway Docs: http://{host}:{gateway_port}/docs")
    print(f"   • Analytics: http://{host}:{analytics_port}")
    print(f"   • Communications: http://{host}:{communications_port}") 
    print(f"   • Billing: http://{host}:{billing_port}")
    print(f"   • MCP Server: http://{host}:{mcp_port}")
    print(f"   • AI Services: http://{host}:{ai_port}")
    
    print("\n💡 Para el frontend:")
    print("   cd frontend && npm run dev")
    print(f"   Luego visita: http://{host}:{frontend_port}")
    
    print("\n⚠️  Presiona Ctrl+C para detener todos los servicios")
    
    try:
        # Mantener el script corriendo
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo servicios...")
        for name, process in processes:
            try:
                process.terminate()
                print(f"   ✅ {name} detenido")
            except:
                print(f"   ❌ Error deteniendo {name}")
        print("✅ Todos los servicios detenidos")

if __name__ == "__main__":
    main() 