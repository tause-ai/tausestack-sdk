#!/usr/bin/env python3
"""
Script de inicio para AI Services - TauseStack v0.9.0
"""
import os
import sys
import subprocess
import time
import requests
import asyncio
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_dependencies():
    """Verifica que las dependencias estén instaladas"""
    required_packages = [
        "fastapi",
        "uvicorn", 
        "httpx",
        "openai",
        "anthropic"
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Paquetes faltantes: {', '.join(missing)}")
        print("Instalar con: pip install " + " ".join(missing))
        return False
    
    print("✅ Todas las dependencias están instaladas")
    return True

def check_env_vars():
    """Verifica variables de entorno necesarias"""
    required_vars = {
        "OPENAI_API_KEY": "OpenAI API Key",
        "ANTHROPIC_API_KEY": "Anthropic API Key (opcional)"
    }
    
    missing = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing.append(f"{var} ({description})")
    
    if missing:
        print("⚠️  Variables de entorno faltantes:")
        for var in missing:
            print(f"   - {var}")
        print("\nConfigura las variables de entorno en tu shell:")
        print("export OPENAI_API_KEY='tu-api-key'")
        print("export ANTHROPIC_API_KEY='tu-api-key'")
        
        # Permitir continuar sin Claude
        if "OPENAI_API_KEY" in [v.split(" ")[0] for v in missing]:
            return False
        else:
            print("\n⚠️  Continuando solo con OpenAI...")
    
    print("✅ Variables de entorno configuradas")
    return True

def start_ai_service():
    """Inicia el servicio de IA"""
    print("🚀 Iniciando AI Services...")
    
    # Cambiar al directorio de servicios
    services_dir = Path(__file__).parent.parent / "services" / "ai_services"
    
    # Comando para iniciar el servicio
    cmd = [
        sys.executable, "-m", "uvicorn",
        "api.main:app",
        "--host", "0.0.0.0",
        "--port", "8005",
        "--reload",
        "--log-level", "info"
    ]
    
    try:
        # Iniciar el proceso
        process = subprocess.Popen(
            cmd,
            cwd=services_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        print(f"✅ AI Services iniciado en PID {process.pid}")
        print("📡 Servicio disponible en: http://localhost:8005")
        print("📖 Documentación en: http://localhost:8005/docs")
        print("\n🔄 Logs del servicio:")
        print("-" * 50)
        
        # Mostrar logs en tiempo real
        for line in process.stdout:
            print(line.strip())
            
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo AI Services...")
        process.terminate()
        process.wait()
        print("✅ AI Services detenido")
    except Exception as e:
        print(f"❌ Error iniciando AI Services: {e}")
        return False
    
    return True

def wait_for_service(max_attempts=30):
    """Espera a que el servicio esté disponible"""
    print("⏳ Esperando a que AI Services esté disponible...")
    
    for attempt in range(max_attempts):
        try:
            response = requests.get("http://localhost:8005/health", timeout=2)
            if response.status_code == 200:
                print("✅ AI Services está disponible!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(1)
        print(f"   Intento {attempt + 1}/{max_attempts}...")
    
    print("❌ AI Services no respondió en tiempo esperado")
    return False

async def test_service():
    """Prueba básica del servicio"""
    print("\n🧪 Ejecutando pruebas básicas...")
    
    try:
        # Test health endpoint
        response = requests.get("http://localhost:8005/health")
        if response.status_code == 200:
            print("✅ Health check: OK")
        else:
            print(f"❌ Health check falló: {response.status_code}")
            return False
        
        # Test providers endpoint
        response = requests.get("http://localhost:8005/providers")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Proveedores disponibles: {list(data.get('providers', {}).keys())}")
        else:
            print(f"⚠️  Providers endpoint: {response.status_code}")
        
        # Test templates endpoint
        response = requests.get("http://localhost:8005/templates")
        if response.status_code == 200:
            data = response.json()
            templates = data.get('templates', [])
            print(f"✅ Templates disponibles: {len(templates)}")
        else:
            print(f"⚠️  Templates endpoint: {response.status_code}")
        
        print("✅ Todas las pruebas básicas pasaron!")
        return True
        
    except Exception as e:
        print(f"❌ Error en pruebas: {e}")
        return False

def show_usage_examples():
    """Muestra ejemplos de uso"""
    print("\n📚 Ejemplos de uso:")
    print("-" * 50)
    
    print("\n1. Generar componente React:")
    print("""
curl -X POST "http://localhost:8005/generate/component" \\
  -H "Content-Type: application/json" \\
  -d '{
    "description": "Un botón moderno con loading state",
    "component_type": "button",
    "features": ["loading", "disabled", "variants"],
    "styling_preferences": "modern tailwind"
  }'
""")
    
    print("\n2. Generar endpoint API:")
    print("""
curl -X POST "http://localhost:8005/generate/api" \\
  -H "Content-Type: application/json" \\
  -d '{
    "description": "Endpoint para crear usuarios",
    "http_method": "POST",
    "route": "/api/users",
    "parameters": ["name", "email", "password"]
  }'
""")
    
    print("\n3. Debug código:")
    print("""
curl -X POST "http://localhost:8005/debug" \\
  -H "Content-Type: application/json" \\
  -d '{
    "error_code": "const x = 1; x.map()",
    "error_message": "TypeError: x.map is not a function"
  }'
""")
    
    print("\n4. Chat con IA:")
    print("""
curl -X POST "http://localhost:8005/chat" \\
  -H "Content-Type: application/json" \\
  -d '{
    "message": "¿Cómo crear un hook personalizado en React?",
    "session_id": "my_session"
  }'
""")

def main():
    """Función principal"""
    print("🤖 TauseStack AI Services v0.9.0")
    print("=" * 50)
    
    # Verificar dependencias
    if not check_dependencies():
        sys.exit(1)
    
    # Verificar variables de entorno
    if not check_env_vars():
        print("\n❌ Configuración incompleta. Saliendo...")
        sys.exit(1)
    
    # Mostrar información del servicio
    print("\n📋 Información del servicio:")
    print(f"   Puerto: 8005")
    print(f"   Health: http://localhost:8005/health")
    print(f"   Docs: http://localhost:8005/docs")
    print(f"   Providers: OpenAI GPT-4" + (" + Anthropic Claude" if os.getenv("ANTHROPIC_API_KEY") else ""))
    
    # Preguntar si continuar
    try:
        input("\n📥 Presiona Enter para continuar o Ctrl+C para salir...")
    except KeyboardInterrupt:
        print("\n👋 Saliendo...")
        sys.exit(0)
    
    # Iniciar servicio
    if start_ai_service():
        # Esperar a que esté disponible
        if wait_for_service():
            # Ejecutar pruebas
            asyncio.run(test_service())
            
            # Mostrar ejemplos
            show_usage_examples()
            
            print("\n🎉 AI Services está listo para usar!")
            print("🛑 Presiona Ctrl+C para detener el servicio")
            
            # Mantener el script corriendo
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n👋 Deteniendo AI Services...")
        else:
            print("❌ No se pudo verificar que el servicio esté funcionando")
            sys.exit(1)
    else:
        print("❌ Error iniciando el servicio")
        sys.exit(1)

if __name__ == "__main__":
    main()