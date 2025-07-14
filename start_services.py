#!/usr/bin/env python3
"""
Script para arrancar TauseStack en producción
Usando los módulos exactos que funcionan localmente
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
    print("\n⏹️  Deteniendo servicios...")
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
    cleanup()
    sys.exit(0)

def start_builder_api():
    """Inicia Builder API con factory (como localmente)"""
    cmd = [
        sys.executable, "-m", "uvicorn",
        "tausestack.services.builder_api:create_builder_api_app",
        "--host", "0.0.0.0",
        "--port", "8006",
        "--factory",
        "--log-level", "info"
    ]
    
    print("🚀 Iniciando Builder API en puerto 8006...")
    try:
        process = subprocess.Popen(cmd)
        processes.append(process)
        return process
    except Exception as e:
        print(f"❌ Error iniciando Builder API: {e}")
        return None

def start_api_gateway():
    """Inicia API Gateway (como localmente)"""
    cmd = [
        sys.executable, "-m", "uvicorn",
        "tausestack.services.api_gateway:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--log-level", "info"
    ]
    
    print("🚀 Iniciando API Gateway en puerto 8000...")
    try:
        process = subprocess.Popen(cmd)
        processes.append(process)
        return process
    except Exception as e:
        print(f"❌ Error iniciando API Gateway: {e}")
        return None

def main():
    """Función principal - exactamente como funciona localmente"""
    
    # Registrar manejadores de señales
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    atexit.register(cleanup)
    
    # Cambiar al directorio del proyecto
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print("🚀 Iniciando TauseStack Production Services...")
    print("=" * 50)
    
    # 1. Iniciar Builder API primero (dependencia del API Gateway)
    builder_process = start_builder_api()
    if not builder_process:
        print("❌ Error crítico: Builder API no pudo iniciarse")
        sys.exit(1)
    
    # Esperar un poco para que Builder API arranque
    print("⏳ Esperando Builder API...")
    time.sleep(10)
    
    # 2. Iniciar API Gateway
    gateway_process = start_api_gateway()
    if not gateway_process:
        print("❌ Error crítico: API Gateway no pudo iniciarse")
        sys.exit(1)
    
    print("✅ Servicios iniciados:")
    print("   • Builder API: http://0.0.0.0:8006")
    print("   • API Gateway + Frontend: http://0.0.0.0:8000")
    print("   • Health Check: http://0.0.0.0:8000/health")
    
    # Mantener el proceso principal vivo
    try:
        while True:
            time.sleep(1)
    except Exception as e:
        print(f"❌ Error en el proceso principal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 