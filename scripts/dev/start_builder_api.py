#!/usr/bin/env python3
"""
Script para iniciar el Builder API Service
Puerto: 8006
"""

import uvicorn
import sys
import os

# Agregar el proyecto al path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)

from tausestack.services.builder_api import create_builder_api_app

if __name__ == "__main__":
    print("🚀 Iniciando TauseStack Builder API Service...")
    print("📡 Puerto: 8006")
    print("📋 Endpoints disponibles:")
    print("   • GET  /v1/templates/list")
    print("   • GET  /v1/templates/{id}")
    print("   • POST /v1/apps/create")
    print("   • GET  /v1/apps/{id}")
    print("   • POST /v1/deploy/start")
    print("   • GET  /v1/deploy/{id}")
    print("   • POST /v1/tenants/create")
    print("   • GET  /v1/tenants/{id}")
    print("📚 Docs: http://localhost:8006/v1/docs")
    print("🌍 Via Gateway: http://localhost:9001/v1/...")
    
    uvicorn.run(
        "tausestack.services.builder_api:create_builder_api_app",
        host="0.0.0.0", 
        port=8006,
        factory=True,
        reload=True,
        log_level="info"
    ) 