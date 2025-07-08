#!/usr/bin/env python3
"""
Demo Completo: Estrategia Híbrida TauseStack + CrewAI

Este demo muestra:
1. Agentes individuales en TauseStack
2. Equipos con workflows predefinidos
3. Casos de uso para tause.pro
4. Métricas y comparación de enfoques
"""

import asyncio
import json
import time
from datetime import datetime

# Importar componentes
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from tausestack.services.agent_engine.core.tausestack_agent import TauseStackAgent, TauseStackAgentManager
from tausestack.services.agent_engine.core.agent_config import AgentConfig
from tausestack.services.agent_engine.core.agent_role import PresetRoles
from tausestack.services.agent_engine.core.agent_team import AgentTeam, TeamType, PresetTeams


class HybridStrategyDemo:
    """Demo de la estrategia híbrida completa"""
    
    def __init__(self):
        self.agent_manager = TauseStackAgentManager()
        self.individual_agents = []
        self.teams = []
        self.results = {
            "individual_agents": [],
            "team_workflows": [],
            "hybrid_orchestration": []
        }
    
    async def setup_individual_agents(self):
        """Configurar agentes individuales multi-tenant"""
        print("🔧 Configurando agentes individuales...")
        
        # Agentes para diferentes tenants
        agents_config = [
            {"name": "Research Pro", "tenant": "tause_pro", "role": "research"},
            {"name": "Content Creator", "tenant": "tause_pro", "role": "writer"},
            {"name": "Kumaway Assistant", "tenant": "kumaway", "role": "customer_support"},
            {"name": "TEZ Ecommerce", "tenant": "tez", "role": "ecommerce"},
            {"name": "Data Analyst", "tenant": "tause_pro", "role": "research"},
            {"name": "SEO Expert", "tenant": "tause_pro", "role": "writer"}
        ]
        
        for config in agents_config:
            agent = TauseStackAgent(
                config=AgentConfig(
                    agent_id=f"{config['name'].lower().replace(' ', '_')}_{config['tenant']}",
                    tenant_id=config['tenant'],
                    name=config['name'],
                    role=getattr(PresetRoles, f"{config['role']}_agent")(),
                    custom_instructions=f"Especializado para {config['tenant']} en {config['role']}"
                )
            )
            
            self.individual_agents.append(agent)
            self.agent_manager.register_agent(agent)
        
        print(f"✅ {len(self.individual_agents)} agentes individuales configurados")
    
    async def setup_teams(self):
        """Configurar equipos predefinidos"""
        print("👥 Configurando equipos...")
        
        # Equipo de investigación para tause.pro
        research_team = await PresetTeams.create_research_team("tause_pro")
        self.teams.append(research_team)
        
        # Equipo de contenido para tause.pro
        content_team = await PresetTeams.create_content_team("tause_pro")
        self.teams.append(content_team)
        
        # Equipo personalizado para TEZ
        tez_agents = [agent for agent in self.individual_agents if agent.config.tenant_id == "tez"]
        if tez_agents:
            tez_team = AgentTeam(
                team_id="tez_ecommerce_team",
                name="TEZ E-commerce Team",
                tenant_id="tez",
                team_type=TeamType.ECOMMERCE_OPTIMIZATION,
                agents=tez_agents,
                description="Equipo especializado en e-commerce para TEZ"
            )
            self.teams.append(tez_team)
        
        print(f"✅ {len(self.teams)} equipos configurados")
    
    async def demo_individual_agents(self):
        """Demo de agentes individuales"""
        print("\n🤖 === DEMO: AGENTES INDIVIDUALES ===")
        
        tasks = [
            {"agent": "research_pro_tause_pro", "task": "Investiga las tendencias de IA en 2024"},
            {"agent": "content_creator_tause_pro", "task": "Escribe un blog post sobre productividad"},
            {"agent": "kumaway_assistant_kumaway", "task": "Responde consulta sobre tiempo de entrega"},
            {"agent": "tez_ecommerce_tez", "task": "Procesa pedido de cliente VIP"}
        ]
        
        start_time = time.time()
        
        for task_config in tasks:
            agent = self.agent_manager.get_agent(task_config["agent"])
            if agent:
                print(f"\n📋 Ejecutando: {task_config['task']}")
                print(f"🎯 Agente: {agent.config.name} (Tenant: {agent.config.tenant_id})")
                
                result = await agent.execute_task(task_config["task"])
                
                self.results["individual_agents"].append({
                    "agent": agent.config.name,
                    "tenant": agent.config.tenant_id,
                    "task": task_config["task"],
                    "response": result.response,
                    "tokens": result.metrics.tokens_used if result.metrics else 0,
                    "duration_ms": result.get_duration_ms(),
                    "success": result.is_successful()
                })
                
                print(f"✅ Resultado: {result.response}")
                print(f"📊 Tokens: {result.metrics.tokens_used if result.metrics else 0}")
        
        total_time = time.time() - start_time
        print(f"\n⏱️ Tiempo total agentes individuales: {total_time:.2f}s")
        
        return total_time
    
    async def demo_team_workflows(self):
        """Demo de workflows de equipos"""
        print("\n👥 === DEMO: WORKFLOWS DE EQUIPOS ===")
        
        workflows = [
            {
                "team": "research_team",
                "task": "Analiza el mercado colombiano de fintech",
                "type": "research"
            },
            {
                "team": "content_team", 
                "task": "Crea contenido para lanzamiento de producto",
                "type": "content"
            },
            {
                "team": "tez_team",
                "task": "Optimiza el proceso de checkout",
                "type": "ecommerce"
            }
        ]
        
        start_time = time.time()
        
        for workflow_config in workflows:
            # Encontrar equipo
            team = None
            for t in self.teams:
                if workflow_config["type"] in t.team_id.lower():
                    team = t
                    break
            
            if team:
                print(f"\n🔄 Ejecutando workflow: {workflow_config['task']}")
                print(f"👥 Equipo: {team.name} ({team.agent_count} agentes)")
                
                try:
                    result = await team.execute_workflow(workflow_config["task"])
                    
                    self.results["team_workflows"].append({
                        "team": team.name,
                        "task": workflow_config["task"],
                        "status": result["status"],
                        "execution_time_ms": result["execution_time_ms"],
                        "total_tokens": result["total_tokens_used"],
                        "steps": len(result["step_results"]),
                        "final_result": result["final_result"][:200] + "..." if len(result["final_result"]) > 200 else result["final_result"]
                    })
                    
                    print(f"✅ Status: {result['status']}")
                    print(f"📊 Tokens: {result['total_tokens_used']}")
                    print(f"🔗 Pasos: {len(result['step_results'])}")
                    print(f"📝 Resultado: {result['final_result'][:200]}...")
                    
                except Exception as e:
                    print(f"❌ Error en workflow: {str(e)}")
        
        total_time = time.time() - start_time
        print(f"\n⏱️ Tiempo total workflows: {total_time:.2f}s")
        
        return total_time
    
    async def demo_hybrid_orchestration(self):
        """Demo de orquestación híbrida (TauseStack + CrewAI concept)"""
        print("\n🔀 === DEMO: ORQUESTACIÓN HÍBRIDA ===")
        
        # Simular cómo tause.pro orquestaría agentes de TauseStack
        print("🎯 Caso de uso: Cliente de tause.pro solicita análisis completo")
        print("🔧 Orquestación: tause.pro decide qué agentes/equipos usar")
        
        start_time = time.time()
        
        # Paso 1: Investigación inicial (agente individual)
        print("\n1️⃣ Paso 1: Investigación inicial")
        research_agent = self.agent_manager.get_agent("research_pro_tause_pro")
        if research_agent:
            result1 = await research_agent.execute_task("Investiga el contexto del mercado colombiano")
            print(f"✅ Contexto obtenido: {result1.response}")
        
        # Paso 2: Análisis profundo (equipo completo)
        print("\n2️⃣ Paso 2: Análisis profundo con equipo")
        research_team = next((t for t in self.teams if "research" in t.team_id.lower()), None)
        if research_team:
            context = {"market_context": result1.response if 'result1' in locals() else "Mercado colombiano"}
            result2 = await research_team.execute_workflow(
                "Analiza oportunidades de negocio basado en contexto", 
                context
            )
            print(f"✅ Análisis completado: {result2['final_result'][:100]}...")
        
        # Paso 3: Contenido personalizado (agente especializado)
        print("\n3️⃣ Paso 3: Generación de contenido")
        content_agent = self.agent_manager.get_agent("content_creator_tause_pro")
        if content_agent:
            result3 = await content_agent.execute_task("Crea resumen ejecutivo del análisis")
            print(f"✅ Contenido generado: {result3.response}")
        
        # Registrar resultado híbrido
        self.results["hybrid_orchestration"].append({
            "use_case": "Análisis completo para cliente tause.pro",
            "orchestration_pattern": "Individual → Team → Individual",
            "total_agents_used": 1 + (research_team.agent_count if research_team else 0) + 1,
            "steps": 3,
            "success": True
        })
        
        total_time = time.time() - start_time
        print(f"\n⏱️ Tiempo total orquestación híbrida: {total_time:.2f}s")
        
        return total_time
    
    def generate_metrics_report(self):
        """Generar reporte de métricas"""
        print("\n📊 === REPORTE DE MÉTRICAS ===")
        
        # Métricas de agentes individuales
        individual_stats = self.results["individual_agents"]
        if individual_stats:
            total_tokens_individual = sum(r["tokens"] for r in individual_stats)
            avg_time_individual = sum(r["duration_ms"] for r in individual_stats) / len(individual_stats)
            success_rate_individual = sum(1 for r in individual_stats if r["success"]) / len(individual_stats) * 100
            
            print(f"\n🤖 Agentes Individuales:")
            print(f"  • Total tareas: {len(individual_stats)}")
            print(f"  • Tokens totales: {total_tokens_individual:,}")
            print(f"  • Tiempo promedio: {avg_time_individual:.0f}ms")
            print(f"  • Tasa de éxito: {success_rate_individual:.1f}%")
        
        # Métricas de equipos
        team_stats = self.results["team_workflows"]
        if team_stats:
            total_tokens_team = sum(r["total_tokens"] for r in team_stats)
            avg_time_team = sum(r["execution_time_ms"] for r in team_stats) / len(team_stats)
            total_steps = sum(r["steps"] for r in team_stats)
            
            print(f"\n👥 Equipos:")
            print(f"  • Total workflows: {len(team_stats)}")
            print(f"  • Tokens totales: {total_tokens_team:,}")
            print(f"  • Tiempo promedio: {avg_time_team:.0f}ms")
            print(f"  • Pasos totales: {total_steps}")
        
        # Métricas de orquestación híbrida
        hybrid_stats = self.results["hybrid_orchestration"]
        if hybrid_stats:
            total_agents_hybrid = sum(r["total_agents_used"] for r in hybrid_stats)
            
            print(f"\n🔀 Orquestación Híbrida:")
            print(f"  • Casos de uso: {len(hybrid_stats)}")
            print(f"  • Agentes orquestados: {total_agents_hybrid}")
            print(f"  • Patrones utilizados: {len(set(r['orchestration_pattern'] for r in hybrid_stats))}")
        
        # Recomendaciones
        print("\n💡 === RECOMENDACIONES ESTRATÉGICAS ===")
        print("✅ Agentes individuales: Ideal para tareas específicas y rápidas")
        print("✅ Equipos: Excelente para workflows complejos y coordinados")
        print("✅ Orquestación híbrida: Máxima flexibilidad para casos complejos")
        
        print("\n🎯 Estrategia recomendada:")
        print("1. TauseStack: Base sólida con agentes + equipos")
        print("2. tause.pro: Orquestación inteligente con CrewAI")
        print("3. Casos específicos: Equipos predefinidos optimizados")
    
    def save_results(self):
        """Guardar resultados completos"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"hybrid_strategy_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n💾 Resultados guardados en: {filename}")
    
    async def run_complete_demo(self):
        """Ejecutar demo completo"""
        print("🚀 === DEMO COMPLETO: ESTRATEGIA HÍBRIDA TAUSESTACK ===")
        print("📅 Fecha:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        await self.setup_individual_agents()
        await self.setup_teams()
        
        # Ejecutar demos
        time_individual = await self.demo_individual_agents()
        time_teams = await self.demo_team_workflows()
        time_hybrid = await self.demo_hybrid_orchestration()
        
        # Generar reporte
        self.generate_metrics_report()
        
        # Guardar resultados
        self.save_results()
        
        print(f"\n🎉 Demo completado exitosamente!")
        print(f"⏱️ Tiempo total: {time_individual + time_teams + time_hybrid:.2f}s")
        print(f"📊 Resultados: {len(self.results['individual_agents'])} agentes, {len(self.results['team_workflows'])} workflows, {len(self.results['hybrid_orchestration'])} orquestaciones")


async def main():
    """Función principal"""
    demo = HybridStrategyDemo()
    await demo.run_complete_demo()


if __name__ == "__main__":
    asyncio.run(main()) 