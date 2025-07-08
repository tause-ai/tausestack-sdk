#!/usr/bin/env python3
"""
Script para iniciar el Agent Team API Service
"""

import subprocess
import sys
import os
from pathlib import Path

def start_agent_team_api():
    """Inicia el Agent Team API Service"""
    
    # Cambiar al directorio del proyecto
    project_root = Path(__file__).parent.parent.parent
    os.chdir(project_root)
    
    print("🚀 Iniciando TauseStack Agent Team API Service...")
    print("📡 Puerto: 8007")
    print("📋 Endpoints disponibles:")
    print("   • GET  /teams")
    print("   • POST /teams")
    print("   • GET  /teams/{team_id}")
    print("   • POST /teams/{team_id}/execute")
    print("   • GET  /executions")
    print("   • GET  /teams/preset/research")
    print("   • GET  /teams/preset/content")
    print("📚 Docs: http://localhost:8007/docs")
    print("🌍 Via Gateway: http://localhost:9001/teams/...")
    
    # Comando para iniciar el servicio
    cmd = [
        sys.executable, "-m", "uvicorn",
        "tausestack.services.agent_team_api:AgentTeamAPIService().app",
        "--host", "0.0.0.0",
        "--port", "8007",
        "--reload",
        "--log-level", "info"
    ]
    
    print(f"\n🔥 Ejecutando: {' '.join(cmd)}")
    print("=" * 50)
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n\n⏹️  Agent Team API Service detenido por el usuario")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error al iniciar Agent Team API Service: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    start_agent_team_api() 