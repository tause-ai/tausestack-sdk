#!/usr/bin/env python3
"""
Script de inicio para AI Services
Maneja los imports relativos correctamente
"""

import sys
import os
from pathlib import Path

# Agregar el directorio actual al path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Importar y ejecutar la aplicación
from api.main import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8014,
        reload=True,
        log_level="info"
    ) 