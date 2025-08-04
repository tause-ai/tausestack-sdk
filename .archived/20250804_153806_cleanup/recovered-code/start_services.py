#!/usr/bin/env python3
"""
Script para arrancar todos los servicios de TauseStack en producción
"""

import subprocess
import sys
import os
import time
from pathlib import Path
import signal
import atexit

# Lista de procesos para limpieza
processes = []

def cleanup():
    """Limpia procesos al salir"""
    for process in processes:
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            try:
                process.kill()
            except:
                pass

def signal_handler(signum, frame):
    """Manejador de señales"""
    print("\n⏹️  Deteniendo servicios...")
    cleanup()
    sys.exit(0)

def start_service(service_name, module_path, port):
    """Inicia un servicio específico"""
    cmd = [
        sys.executable, "-m", "uvicorn",
        module_path,
        "--host", "0.0.0.0",
        "--port", str(port),
        "--log-level", "info"
    ]
    
    print(f"🚀 Iniciando {service_name} en puerto {port}...")
    
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        processes.append(process)
        return process
    except Exception as e:
        print(f"❌ Error iniciando {service_name}: {e}")
        return None

def main():
    """Función principal para arrancar todos los servicios"""
    
    # Registrar manejadores de señales
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    atexit.register(cleanup)
    
    # Cambiar al directorio del proyecto
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print("🚀 Iniciando TauseStack Production Services...")
    print("=" * 50)
    
    # Configuración de servicios
    services = [
        ("API Gateway", "tausestack.services.api_gateway:app", 8000),
        ("Analytics", "tausestack.services.analytics.api.main:app", 8001),
        ("Communications", "tausestack.services.communications.api.main:app", 8002),
        ("Billing", "tausestack.services.billing.api.main:app", 8003),
        ("Templates", "tausestack.services.templates.api.main:app", 8004),
        ("AI Services", "tausestack.services.ai_services.api.main:app", 8005),
        ("Builder API", "tausestack.services.builder_api:app", 8006),
        ("Agent Team API", "tausestack.services.agent_team_api:app", 8007),
        ("Admin API", "tausestack.services.admin_api:app", 8008),
    ]
    
    # Mostrar servicios a iniciar
    print("📋 Servicios a iniciar:")
    for name, _, port in services:
        print(f"   • {name}: http://0.0.0.0:{port}")
    
    print("\n🔥 Iniciando servicios...")
    print("=" * 50)
    
    # Iniciar cada servicio
    for service_name, module_path, port in services:
        process = start_service(service_name, module_path, port)
        if process:
            time.sleep(1)  # Esperar un segundo entre servicios
    
    print(f"\n✅ {len(processes)} servicios iniciados")
    print("🌍 API Gateway disponible en: http://0.0.0.0:8000")
    print("📚 Documentación: http://0.0.0.0:8000/docs")
    
    # Mantener el proceso principal vivo y monitorear servicios
    try:
        while True:
            # Verificar si algún servicio ha terminado
            for i, process in enumerate(processes):
                if process.poll() is not None:
                    print(f"⚠️  Servicio {i+1} terminó unexpectadamente")
            
            time.sleep(5)
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)


if __name__ == "__main__":
    main() 