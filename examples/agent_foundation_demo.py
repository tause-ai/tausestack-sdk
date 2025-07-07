#!/usr/bin/env python3
"""
Demo del TauseStack Agent Engine - Primer agente funcionando

Este demo muestra:
1. Creación de un agente simple
2. Ejecución de tareas básicas
3. Integración con la infraestructura TauseStack
4. Memoria persistente
5. Herramientas disponibles
"""

import asyncio
import sys
import os

# Agregar el path para importar TauseStack
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from tausestack.services.agent_engine.core.agent_role import AgentRole, AgentType, PresetRoles
from tausestack.services.agent_engine.core.agent_config import AgentConfig
from tausestack.services.agent_engine.core.tausestack_agent import TauseStackAgent, TauseStackAgentManager


async def demo_basic_agent():
    """Demostrar funcionamiento básico de un agente"""
    
    print("🤖 TauseStack Agent Engine - Demo Básico")
    print("=" * 50)
    
    # 1. Crear un rol de agente
    research_role = PresetRoles.research_agent()
    print(f"✅ Rol creado: {research_role.name}")
    print(f"   Goal: {research_role.goal}")
    print(f"   Tools: {research_role.tools}")
    print()
    
    # 2. Crear configuración del agente
    agent_config = AgentConfig(
        agent_id="demo-research-001",
        tenant_id="demo-tenant",
        name="Demo Research Agent",
        role=research_role,
        enabled=True,
        custom_instructions="Siempre responde en español y sé muy detallado en las explicaciones."
    )
    
    print(f"✅ Configuración creada para agente: {agent_config.name}")
    print(f"   Tenant: {agent_config.tenant_id}")
    print(f"   Herramientas permitidas: {len(agent_config.allowed_tools)}")
    print()
    
    # 3. Crear agente
    agent = TauseStackAgent(
        config=agent_config,
        api_base_url="http://localhost:9001",  # API Gateway
        storage_path=".tausestack_storage"
    )
    
    print(f"✅ Agente creado: {agent.config.name}")
    print(f"   Memoria inicializada: {await agent.memory.get_size()} interacciones")
    print(f"   Herramientas disponibles: {len(agent.tools_manager.get_available_tools())}")
    print()
    
    # 4. Mostrar estado inicial
    status = await agent.get_status()
    print("📊 Estado inicial del agente:")
    print(f"   - Habilitado: {status['enabled']}")
    print(f"   - Ocupado: {status['is_busy']}")
    print(f"   - Tareas completadas: {status['stats']['tasks_completed']}")
    print(f"   - Tamaño de memoria: {status['memory_size']}")
    print()
    
    # 5. Mostrar herramientas disponibles
    available_tools = agent.tools_manager.get_available_tools()
    print(f"🛠️ Herramientas disponibles ({len(available_tools)}):")
    for tool in available_tools[:10]:  # Mostrar primeras 10
        tool_info = agent.tools_manager.get_tool_info(tool)
        print(f"   - {tool}: {tool_info['description']}")
    if len(available_tools) > 10:
        print(f"   ... y {len(available_tools) - 10} más")
    print()
    
    return agent


async def demo_agent_tasks(agent: TauseStackAgent):
    """Demostrar ejecución de tareas"""
    
    print("🎯 Ejecutando tareas con el agente")
    print("=" * 50)
    
    # Lista de tareas de prueba
    tasks = [
        "Explica qué es TauseStack en 2 párrafos",
        "Analiza las ventajas de usar agentes de IA multi-tenant",
        "Describe cómo funciona la memoria persistente en agentes"
    ]
    
    for i, task in enumerate(tasks, 1):
        print(f"📝 Tarea {i}: {task}")
        
        try:
            # Simular contexto adicional
            context = {
                "user_id": "demo-user",
                "session_id": f"demo-session-{i}",
                "preferences": {
                    "language": "es",
                    "detail_level": "high"
                }
            }
            
            # Ejecutar tarea
            print("   ⏳ Ejecutando...")
            result = await agent.execute_task(task, context)
            
            # Mostrar resultado
            if result.is_successful():
                print(f"   ✅ Completada en {result.get_duration_ms()}ms")
                print(f"   📊 Tokens usados: {result.metrics.tokens_used if result.metrics else 'N/A'}")
                print(f"   🧠 Modelo: {result.metrics.model_used if result.metrics else 'N/A'}")
                
                # Mostrar parte del resultado (simulado)
                print(f"   📄 Resultado: [Respuesta del agente sería mostrada aquí]")
            else:
                print(f"   ❌ Error: {result.error_message}")
            
        except Exception as e:
            print(f"   ❌ Excepción: {str(e)}")
        
        print()
    
    # Mostrar estadísticas finales
    final_status = await agent.get_status()
    print("📊 Estadísticas finales:")
    print(f"   - Tareas completadas: {final_status['stats']['tasks_completed']}")
    print(f"   - Tareas fallidas: {final_status['stats']['tasks_failed']}")
    print(f"   - Total tokens usados: {final_status['stats']['total_tokens_used']}")
    print(f"   - Tiempo total de ejecución: {final_status['stats']['total_execution_time_ms']}ms")
    print()


async def demo_memory_system(agent: TauseStackAgent):
    """Demostrar sistema de memoria"""
    
    print("🧠 Sistema de Memoria")
    print("=" * 50)
    
    # Obtener resumen de memoria
    memory_summary = await agent.get_memory_summary()
    print("📊 Resumen de memoria:")
    print(f"   - Total interacciones: {memory_summary['total_interactions']}")
    print(f"   - Tipos de contexto: {memory_summary['context_types']}")
    print(f"   - Última actividad: {memory_summary['last_activity']}")
    print(f"   - Tamaño: {memory_summary['memory_size_mb']} MB")
    
    if memory_summary.get('task_statistics'):
        print("   - Estadísticas por tipo de tarea:")
        for task_type, count in memory_summary['task_statistics'].items():
            print(f"     {task_type}: {count}")
    print()
    
    # Probar contexto relevante
    test_query = "memoria persistente"
    relevant_context = await agent.memory.get_relevant_context(test_query)
    
    print(f"🔍 Contexto relevante para '{test_query}':")
    if relevant_context:
        print(f"   {relevant_context[:200]}...")
    else:
        print("   (No hay contexto relevante aún)")
    print()


async def demo_agent_manager():
    """Demostrar gestor de agentes múltiples"""
    
    print("👥 Gestor de Agentes Múltiples")
    print("=" * 50)
    
    # Crear manager
    manager = TauseStackAgentManager(
        api_base_url="http://localhost:9001",
        storage_path=".tausestack_storage"
    )
    
    # Crear múltiples agentes
    agents_configs = [
        {
            "agent_id": "writer-001",
            "name": "Content Writer",
            "role": PresetRoles.writer_agent(),
            "tenant_id": "demo-tenant"
        },
        {
            "agent_id": "support-001", 
            "name": "Customer Support",
            "role": PresetRoles.customer_support_agent(),
            "tenant_id": "demo-tenant"
        },
        {
            "agent_id": "ecommerce-001",
            "name": "Ecommerce Assistant",
            "role": PresetRoles.ecommerce_agent(),
            "tenant_id": "demo-tenant"
        }
    ]
    
    # Crear agentes
    for config_data in agents_configs:
        config = AgentConfig(
            agent_id=config_data["agent_id"],
            tenant_id=config_data["tenant_id"],
            name=config_data["name"],
            role=config_data["role"]
        )
        
        agent = manager.create_agent(config)
        print(f"✅ Agente creado: {agent.config.name} ({agent.config.agent_id})")
    
    print()
    
    # Mostrar todos los estados
    all_statuses = await manager.get_all_statuses()
    print(f"📊 Estado de {len(all_statuses)} agentes:")
    
    for status in all_statuses:
        print(f"   - {status['name']}: {status['role']} ({'Habilitado' if status['enabled'] else 'Deshabilitado'})")
    
    print()


async def main():
    """Función principal del demo"""
    
    print("🚀 TauseStack Agent Engine - Demostración Completa")
    print("=" * 60)
    print()
    
    try:
        # Demo 1: Agente básico
        agent = await demo_basic_agent()
        
        # Demo 2: Ejecución de tareas (simulado)
        await demo_agent_tasks(agent)
        
        # Demo 3: Sistema de memoria
        await demo_memory_system(agent)
        
        # Demo 4: Gestor de agentes múltiples
        await demo_agent_manager()
        
        print("🎉 Demo completado exitosamente!")
        print()
        print("💡 Próximos pasos:")
        print("   1. Conectar con AI Services reales (OpenAI/Claude)")
        print("   2. Implementar herramientas funcionales")
        print("   3. Crear API REST para agentes")
        print("   4. Integrar con CrewAI para multi-agent")
        print("   5. Crear panel administrativo de agentes")
        
    except Exception as e:
        print(f"❌ Error durante el demo: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 