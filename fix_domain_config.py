#!/usr/bin/env python3
"""
Script para configurar TAUSESTACK_BASE_DOMAIN=tausestack.dev en ECS
"""

import json
import subprocess
import sys

def run_command(cmd):
    """Ejecutar comando y devolver output"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Error ejecutando: {cmd}")
        print(f"Error: {result.stderr}")
        return None
    return result.stdout.strip()

def main():
    print("🔧 CONFIGURANDO TAUSESTACK_BASE_DOMAIN=tausestack.dev")
    print("="*60)
    
    # 1. Descargar task definition actual
    print("\n1. Descargando task definition actual...")
    task_def_json = run_command("aws ecs describe-task-definition --task-definition tausestack-final-fixed-task --region us-east-1")
    if not task_def_json:
        sys.exit(1)
    
    task_def = json.loads(task_def_json)
    
    # 2. Extraer configuración limpia
    print("2. Preparando nueva configuración...")
    clean_task_def = {
        'family': task_def['taskDefinition']['family'],
        'taskRoleArn': task_def['taskDefinition']['taskRoleArn'],
        'executionRoleArn': task_def['taskDefinition']['executionRoleArn'],
        'networkMode': task_def['taskDefinition']['networkMode'],
        'requiresCompatibilities': task_def['taskDefinition']['requiresCompatibilities'],
        'cpu': task_def['taskDefinition']['cpu'],
        'memory': task_def['taskDefinition']['memory'],
        'containerDefinitions': task_def['taskDefinition']['containerDefinitions']
    }
    
    # 3. Verificar si la variable ya existe
    env_vars = clean_task_def['containerDefinitions'][0]['environment']
    domain_var_exists = any(var['name'] == 'TAUSESTACK_BASE_DOMAIN' for var in env_vars)
    
    if not domain_var_exists:
        print("3. Agregando variable TAUSESTACK_BASE_DOMAIN=tausestack.dev...")
        env_vars.append({
            'name': 'TAUSESTACK_BASE_DOMAIN',
            'value': 'tausestack.dev'
        })
    else:
        print("3. Actualizando variable TAUSESTACK_BASE_DOMAIN=tausestack.dev...")
        for var in env_vars:
            if var['name'] == 'TAUSESTACK_BASE_DOMAIN':
                var['value'] = 'tausestack.dev'
                break
    
    # 4. Guardar nueva configuración
    with open('updated-task-def.json', 'w') as f:
        json.dump(clean_task_def, f, indent=2)
    
    print("4. Registrando nueva task definition...")
    result = run_command("aws ecs register-task-definition --cli-input-json file://updated-task-def.json --region us-east-1")
    if not result:
        sys.exit(1)
    
    print("5. Actualizando servicio ECS...")
    result = run_command("aws ecs update-service --cluster tausestack-final-fixed-cluster --service tausestack-final-fixed-service --task-definition tausestack-final-fixed-task --region us-east-1")
    if not result:
        sys.exit(1)
    
    print("\n✅ CONFIGURACIÓN COMPLETADA")
    print("="*60)
    print("🔄 El servicio se está reiniciando con la nueva configuración...")
    print("⏳ Espera 2-3 minutos para que los cambios tomen efecto")
    print("🌐 Luego prueba: curl https://api.tausestack.dev/health")

if __name__ == "__main__":
    main() 