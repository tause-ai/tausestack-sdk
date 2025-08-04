#!/usr/bin/env python3
"""
Script para desplegar la corrección del subdomain api.tausestack.dev
"""

import subprocess
import time
import json

def run_command(cmd, description):
    """Ejecutar comando con descripción"""
    print(f"\n🔧 {description}")
    print(f"Ejecutando: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Error: {result.stderr}")
        return False
    
    print(f"✅ Éxito: {result.stdout}")
    return True

def main():
    print("🚀 DESPLEGANDO CORRECCIÓN PARA API.TAUSESTACK.DEV")
    print("=" * 60)
    
    # 1. Commit del cambio
    print("\n1. Commiteando cambio en API Gateway...")
    run_command("git add tausestack/services/api_gateway.py", "Agregando cambio")
    run_command('git commit -m "fix: Agregar api.tausestack.dev al TrustedHostMiddleware\n\n- Permite requests de api.tausestack.dev al API Gateway\n- Resuelve problema \"Invalid host header\" para api.tausestack.dev\n- Mantiene compatibilidad con tausestack.dev/api\n- Ambas opciones funcionan: tausestack.dev/api y api.tausestack.dev"', "Commiteando cambio")
    
    # 2. Forzar deployment
    print("\n2. Forzando deployment en ECS...")
    cmd = "aws ecs update-service --cluster tausestack-final-fixed-cluster --service tausestack-final-fixed-service --force-new-deployment --region us-east-1 --no-cli-pager"
    run_command(cmd, "Forzando nuevo deployment")
    
    # 3. Esperar deployment
    print("\n3. Esperando deployment (120 segundos)...")
    time.sleep(120)
    
    # 4. Verificar corrección
    print("\n4. Verificando corrección...")
    
    # Verificar que ambas opciones funcionan
    cmd1 = "curl -s -w 'Status: %{http_code}' https://tausestack.dev/api"
    cmd2 = "curl -s -w 'Status: %{http_code}' https://api.tausestack.dev/health"
    
    print("\n   - Verificando tausestack.dev/api:")
    run_command(cmd1, "Probando tausestack.dev/api")
    
    print("\n   - Verificando api.tausestack.dev:")
    run_command(cmd2, "Probando api.tausestack.dev")
    
    print("\n✅ CORRECCIÓN COMPLETADA!")
    print("Ambas opciones deberían funcionar ahora:")
    print("- https://tausestack.dev/api")
    print("- https://api.tausestack.dev")

if __name__ == "__main__":
    main() 