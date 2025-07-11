#!/usr/bin/env python3
"""
Script para lanzar el TauseStack Builder localmente
"""

import sys
import os
import subprocess
import time
from pathlib import Path

def main():
    print("🚀 Lanzando TauseStack Builder...")
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists("tausestack") or not os.path.exists("frontend"):
        print("❌ Error: Este script debe ejecutarse desde el directorio raíz del proyecto")
        sys.exit(1)
    
    # Verificar dependencias de Python
    try:
        import fastapi
        import uvicorn
        print("✅ Dependencias de Python OK")
    except ImportError as e:
        print(f"❌ Error: Falta dependencia de Python: {e}")
        print("💡 Ejecuta: pip install -r requirements.txt")
        sys.exit(1)
    
    # Verificar que Node.js esté instalado
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js: {result.stdout.strip()}")
        else:
            print("❌ Error: Node.js no está instalado")
            sys.exit(1)
    except FileNotFoundError:
        print("❌ Error: Node.js no está instalado")
        sys.exit(1)
    
    # Verificar que el frontend esté construido
    frontend_build = Path("frontend/out") 
    if not frontend_build.exists():
        print("⚠️  Frontend no está construido. Construyendo...")
        try:
            subprocess.run(["npm", "run", "build"], cwd="frontend", check=True)
            print("✅ Frontend construido")
        except subprocess.CalledProcessError:
            print("❌ Error construyendo el frontend")
            print("💡 Ejecuta manualmente: cd frontend && npm run build")
            sys.exit(1)
    
    print("\n🎯 Lanzando servicios...")
    
    # Lanzar API Gateway
    print("📡 Iniciando API Gateway en puerto 9001...")
    try:
        # Configurar variables de entorno
        env = os.environ.copy()
        env["ENVIRONMENT"] = "development"
        env["PYTHONPATH"] = os.getcwd()
        
        # Ejecutar API Gateway con uvicorn directamente
        api_process = subprocess.Popen([
            "uvicorn", 
            "tausestack.services.api_gateway:app",
            "--host", "0.0.0.0",
            "--port", "9001", 
            "--reload",
            "--log-level", "info"
        ], env=env)
        
        # Esperar a que inicie
        time.sleep(3)
        
        # Verificar que esté corriendo
        if api_process.poll() is None:
            print("✅ API Gateway iniciado en http://localhost:9001")
        else:
            print("❌ Error iniciando API Gateway")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error ejecutando API Gateway: {e}")
        sys.exit(1)
    
    print("\n🎉 ¡TauseStack Builder listo!")
    print("\n📋 URLs disponibles:")
    print("   • Frontend: http://localhost:9001")
    print("   • Admin: http://localhost:9001/admin")
    print("   • 🏗️  Builder: http://localhost:9001/admin/builder")
    print("   • API Docs: http://localhost:9001/docs")
    print("   • Health Check: http://localhost:9001/health")
    
    print("\n💡 Instrucciones:")
    print("   1. Abre http://localhost:9001/admin/builder en tu navegador")
    print("   2. Inicia sesión con tus credenciales de admin")
    print("   3. ¡Empieza a crear proyectos con el Builder!")
    
    print("\n⚠️  Presiona Ctrl+C para detener los servicios")
    
    try:
        # Mantener el proceso corriendo
        api_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo servicios...")
        api_process.terminate()
        api_process.wait()
        print("✅ Servicios detenidos")

if __name__ == "__main__":
    main() 