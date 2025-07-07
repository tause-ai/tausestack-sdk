#!/usr/bin/env python3
"""
Script de verificación para TauseStack.
Verifica que todos los componentes estén funcionando correctamente.
"""

import sys
import os
import importlib
from pathlib import Path

def print_status(message, status):
    """Imprime un mensaje con estado."""
    icon = "✅" if status else "❌"
    print(f"{icon} {message}")

def check_imports():
    """Verifica que los módulos principales se puedan importar."""
    print("\n🔍 Verificando importaciones...")
    
    modules = [
        ("tausestack", "Framework principal"),
        ("tausestack.sdk", "SDK"),
        ("tausestack.sdk.auth", "Autenticación"),
        ("tausestack.sdk.cache", "Cache"),
        ("tausestack.sdk.storage", "Storage"),
        ("tausestack.sdk.notify", "Notificaciones"),
        ("tausestack.sdk.secrets", "Secrets"),
        ("tausestack.sdk.database", "Database"),
        ("tausestack.framework", "Framework"),
        ("tausestack.cli", "CLI"),
    ]
    
    all_good = True
    for module_name, description in modules:
        try:
            importlib.import_module(module_name)
            print_status(f"{description} ({module_name})", True)
        except ImportError as e:
            print_status(f"{description} ({module_name}): {e}", False)
            all_good = False
    
    return all_good

def check_files():
    """Verifica que los archivos importantes existan."""
    print("\n📁 Verificando archivos...")
    
    files = [
        (".env", "Archivo de configuración"),
        ("pyproject.toml", "Configuración del proyecto"),
        ("requirements.txt", "Dependencias"),
        ("Makefile", "Automatización"),
        (".pre-commit-config.yaml", "Pre-commit hooks"),
    ]
    
    all_good = True
    for file_path, description in files:
        if Path(file_path).exists():
            print_status(f"{description} ({file_path})", True)
        else:
            print_status(f"{description} ({file_path})", False)
            all_good = False
    
    return all_good

def check_environment():
    """Verifica la configuración del entorno."""
    print("\n🌍 Verificando entorno...")
    
    # Verificar Python
    python_version = sys.version_info
    python_ok = python_version.major == 3 and python_version.minor >= 11
    print_status(f"Python {python_version.major}.{python_version.minor}.{python_version.micro}", python_ok)
    
    # Verificar entorno virtual
    venv_ok = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    print_status("Entorno virtual activo", venv_ok)
    
    # Verificar variables de entorno
    env_vars = [
        ("TAUSESTACK_BASE_DOMAIN", "Dominio base"),
        ("NODE_ENV", "Entorno"),
        ("LOG_LEVEL", "Nivel de log"),
    ]
    
    env_ok = True
    for var, description in env_vars:
        value = os.getenv(var)
        if value:
            print_status(f"{description} ({var}={value})", True)
        else:
            print_status(f"{description} ({var})", False)
            env_ok = False
    
    return python_ok and venv_ok and env_ok

def check_services():
    """Verifica que los servicios estén disponibles."""
    print("\n🔧 Verificando servicios...")
    
    try:
        import httpx
        import asyncio
        
        async def check_service(url, name):
            try:
                async with httpx.AsyncClient(timeout=2.0) as client:
                    response = await client.get(url)
                    return response.status_code == 200
            except:
                return False
        
        services = [
            ("http://localhost:8000/health", "Framework (8000)"),
            ("http://localhost:9001/health", "API Gateway (9001)"),
            ("http://localhost:8001/health", "Analytics (8001)"),
            ("http://localhost:8002/health", "Communications (8002)"),
            ("http://localhost:8003/health", "Billing (8003)"),
        ]
        
        all_good = True
        for url, name in services:
            status = asyncio.run(check_service(url, name))
            print_status(f"{name}", status)
            if not status:
                all_good = False
        
        return all_good
        
    except ImportError:
        print_status("httpx no disponible para verificar servicios", False)
        return False

def main():
    """Función principal."""
    print("🚀 Verificación de TauseStack")
    print("=" * 50)
    
    checks = [
        ("Importaciones", check_imports),
        ("Archivos", check_files),
        ("Entorno", check_environment),
        ("Servicios", check_services),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Error en {name}: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 50)
    print("📊 Resumen:")
    
    all_passed = True
    for name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"  {name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ¡TauseStack está listo para usar!")
        print("\nPróximos pasos:")
        print("  1. Ejecutar: tausestack framework run")
        print("  2. Visitar: http://localhost:8000")
        print("  3. Para AWS: make deploy-aws")
    else:
        print("⚠️  Hay problemas que necesitan atención.")
        print("\nRecomendaciones:")
        print("  1. Verificar el entorno virtual")
        print("  2. Revisar las dependencias: pip install -e '.[dev]'")
        print("  3. Configurar variables de entorno")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main()) 