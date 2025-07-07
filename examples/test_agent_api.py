#!/usr/bin/env python3
"""
Test del Agent API - Crear agente y ejecutar tareas

Este script prueba la funcionalidad completa del Agent API:
1. Crear un agente nuevo
2. Listar agentes
3. Ejecutar una tarea
4. Ver el estado del agente
"""

import asyncio
import json
import requests
import time

AGENT_API_URL = "http://localhost:8003"

def test_agent_api():
    """Test completo del Agent API"""
    
    print("🧪 Testing TauseStack Agent API")
    print("=" * 50)
    
    # 1. Listar agentes existentes
    print("\n📋 1. Listando agentes existentes...")
    response = requests.get(f"{AGENT_API_URL}/agents")
    
    if response.status_code == 200:
        agents = response.json()
        print(f"   ✅ Agentes encontrados: {len(agents)}")
        for agent in agents:
            print(f"   - {agent['name']} ({agent['agent_id']})")
    else:
        print(f"   ❌ Error: {response.status_code}")
        return
    
    # 2. Crear un nuevo agente
    print("\n🤖 2. Creando nuevo agente...")
    agent_data = {
        "name": "Demo Agent API",
        "tenant_id": "demo-api-test",
        "role_type": "research",
        "enabled": True,
        "custom_instructions": "Siempre responde en español y sé muy técnico en tus explicaciones.",
        "allowed_tools": ["web_search", "data_analysis"]
    }
    
    response = requests.post(f"{AGENT_API_URL}/agents", json=agent_data)
    
    if response.status_code == 200:
        new_agent = response.json()
        agent_id = new_agent['agent_id']
        print(f"   ✅ Agente creado: {new_agent['name']}")
        print(f"   📧 ID: {agent_id}")
        print(f"   🏢 Tenant: {new_agent['tenant_id']}")
        print(f"   👤 Rol: {new_agent['role_name']}")
    else:
        print(f"   ❌ Error creando agente: {response.status_code}")
        print(f"   Response: {response.text}")
        return
    
    # 3. Ver detalles del agente
    print(f"\n🔍 3. Obteniendo detalles del agente {agent_id}...")
    response = requests.get(f"{AGENT_API_URL}/agents/{agent_id}")
    
    if response.status_code == 200:
        agent_details = response.json()
        print(f"   ✅ Agente encontrado:")
        print(f"   - Nombre: {agent_details['name']}")
        print(f"   - Estado: {'Habilitado' if agent_details['enabled'] else 'Deshabilitado'}")
        print(f"   - Ocupado: {'Sí' if agent_details['is_busy'] else 'No'}")
        print(f"   - Tareas completadas: {agent_details['tasks_completed']}")
        print(f"   - Memoria: {agent_details['memory_size']} items")
    else:
        print(f"   ❌ Error: {response.status_code}")
    
    # 4. Ejecutar una tarea
    print(f"\n⚡ 4. Ejecutando tarea con el agente...")
    task_data = {
        "task": "Explica qué es TauseStack Agent Engine y por qué es innovador",
        "context": {
            "user_id": "test-user",
            "session_id": "test-session",
            "priority": "normal"
        }
    }
    
    response = requests.post(f"{AGENT_API_URL}/agents/{agent_id}/execute", json=task_data)
    
    if response.status_code == 200:
        task_response = response.json()
        task_id = task_response['task_id']
        print(f"   ✅ Tarea creada: {task_id}")
        print(f"   📊 Estado: {task_response['status']}")
        print(f"   ⏰ Creada: {task_response['created_at']}")
        
        # Esperar a que complete
        print("   ⏳ Esperando ejecución...")
        for i in range(10):  # Esperar hasta 10 segundos
            time.sleep(1)
            response = requests.get(f"{AGENT_API_URL}/tasks/{task_id}")
            if response.status_code == 200:
                task_status = response.json()
                if task_status['status'] in ['completed', 'failed']:
                    break
                print(f"      Estado: {task_status['status']}")
        
        # Ver resultado final
        if response.status_code == 200:
            final_task = response.json()
            print(f"   📋 Estado final: {final_task['status']}")
            if final_task['status'] == 'completed':
                print(f"   ✅ Tiempo: {final_task['duration_ms']}ms")
                print(f"   🧠 Tokens: {final_task['tokens_used']}")
                print(f"   📄 Resultado disponible")
            elif final_task['status'] == 'failed':
                print(f"   ❌ Error: {final_task['error']}")
    else:
        print(f"   ❌ Error ejecutando tarea: {response.status_code}")
        print(f"   Response: {response.text}")
    
    # 5. Ver memoria del agente
    print(f"\n🧠 5. Verificando memoria del agente...")
    response = requests.get(f"{AGENT_API_URL}/agents/{agent_id}/memory")
    
    if response.status_code == 200:
        memory = response.json()
        print(f"   ✅ Memoria cargada:")
        print(f"   - Total interacciones: {memory['total_interactions']}")
        print(f"   - Tamaño: {memory['memory_size_mb']} MB")
        print(f"   - Tipos de contexto: {memory['context_types']}")
        if memory.get('task_statistics'):
            print(f"   - Estadísticas por tipo:")
            for task_type, count in memory['task_statistics'].items():
                print(f"     {task_type}: {count}")
    else:
        print(f"   ❌ Error: {response.status_code}")
    
    # 6. Listar todas las tareas
    print(f"\n📋 6. Listando historial de tareas...")
    response = requests.get(f"{AGENT_API_URL}/tasks?limit=10&agent_id={agent_id}")
    
    if response.status_code == 200:
        tasks = response.json()
        print(f"   ✅ Tareas encontradas: {len(tasks)}")
        for task in tasks:
            status_emoji = "✅" if task['status'] == 'completed' else "❌" if task['status'] == 'failed' else "⏳"
            print(f"   {status_emoji} {task['task_id'][:8]}... - {task['status']}")
    else:
        print(f"   ❌ Error: {response.status_code}")
    
    # 7. Estado final de todos los agentes
    print(f"\n📊 7. Estado final de todos los agentes...")
    response = requests.get(f"{AGENT_API_URL}/agents")
    
    if response.status_code == 200:
        final_agents = response.json()
        print(f"   ✅ Total de agentes: {len(final_agents)}")
        for agent in final_agents:
            status = "🟢" if agent['enabled'] and not agent['is_busy'] else "🔴" if not agent['enabled'] else "🟡"
            print(f"   {status} {agent['name']}")
            print(f"     - Tareas: {agent['tasks_completed']} completadas, {agent['tasks_failed']} fallidas")
            print(f"     - Tokens: {agent['total_tokens_used']:,}")
            print(f"     - Memoria: {agent['memory_size']} items")
    
    print("\n🎉 Test del Agent API completado exitosamente!")
    print(f"\n💡 Ahora puedes ver el agente en: http://localhost:3000/admin/agents")

if __name__ == "__main__":
    test_agent_api() 