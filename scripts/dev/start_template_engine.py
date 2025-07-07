#!/usr/bin/env python3
"""
Script para iniciar el Template Engine v0.8.0
"""

import subprocess
import sys
import os
from pathlib import Path

def start_template_engine():
    """Inicia el Template Engine"""
    
    # Cambiar al directorio del proyecto
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print("🚀 Iniciando TauseStack Template Engine v0.8.0...")
    print("=" * 50)
    
    # Verificar que el directorio de templates existe
    templates_dir = project_root / "templates" / "registry"
    templates_dir.mkdir(parents=True, exist_ok=True)
    
    # Verificar que el directorio de proyectos generados existe
    generated_dir = project_root / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)
    
    print("📁 Directorios creados:")
    print(f"   - Templates: {templates_dir}")
    print(f"   - Generated: {generated_dir}")
    
    # Comando para iniciar el servicio
    cmd = [
        sys.executable, "-m", "uvicorn",
        "services.templates.api.main:app",
        "--host", "0.0.0.0",
        "--port", "8004",
        "--reload",
        "--log-level", "info"
    ]
    
    print(f"\n🔥 Ejecutando: {' '.join(cmd)}")
    print("📡 Template Engine disponible en: http://localhost:8004")
    print("📚 Documentación API: http://localhost:8004/docs")
    print("\n⏹️  Presiona Ctrl+C para detener el servicio")
    print("=" * 50)
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n\n⏹️  Template Engine detenido por el usuario")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error al iniciar Template Engine: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    start_template_engine()