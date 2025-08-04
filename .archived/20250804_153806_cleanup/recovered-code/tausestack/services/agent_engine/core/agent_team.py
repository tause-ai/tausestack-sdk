#!/usr/bin/env python3
"""
TauseStack Agent Teams

Gestión de equipos de agentes con workflows predefinidos.
Esto es el primer paso hacia la integración con CrewAI.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

from .agent_config import AgentConfig
from .agent_role import AgentRole, PresetRoles
from .agent_result import AgentResult
from .tausestack_agent import TauseStackAgent


class TeamType(str, Enum):
    """Tipos de equipos predefinidos"""
    RESEARCH = "research"
    CONTENT_CREATION = "content_creation"
    CUSTOMER_SUPPORT = "customer_support"
    ECOMMERCE_OPTIMIZATION = "ecommerce_optimization"
    CUSTOM = "custom"


class WorkflowStep:
    """Un paso en el workflow del equipo"""
    def __init__(
        self,
        step_id: str,
        agent_role: str,
        task_template: str,
        depends_on: List[str] = None,
        parallel: bool = False
    ):
        self.step_id = step_id
        self.agent_role = agent_role
        self.task_template = task_template
        self.depends_on = depends_on or []
        self.parallel = parallel


class TeamWorkflow:
    """Workflow completo para un equipo"""
    def __init__(self, workflow_id: str, name: str, description: str, steps: List[WorkflowStep]):
        self.workflow_id = workflow_id
        self.name = name
        self.description = description
        self.steps = steps
    
    def get_execution_order(self) -> List[List[str]]:
        """Obtiene el orden de ejecución considerando dependencias"""
        # Implementación simple de topological sort
        steps_dict = {step.step_id: step for step in self.steps}
        visited = set()
        execution_order = []
        
        def visit(step_id: str, current_level: List[str]):
            if step_id in visited:
                return
            
            step = steps_dict[step_id]
            
            # Verificar dependencias
            for dep in step.depends_on:
                if dep not in visited:
                    visit(dep, current_level)
            
            current_level.append(step_id)
            visited.add(step_id)
        
        # Agrupar por niveles
        remaining_steps = set(steps_dict.keys())
        while remaining_steps:
            level = []
            for step_id in list(remaining_steps):
                step = steps_dict[step_id]
                if all(dep in visited for dep in step.depends_on):
                    level.append(step_id)
                    remaining_steps.remove(step_id)
                    visited.add(step_id)
            
            if level:
                execution_order.append(level)
            else:
                # Romper ciclos si existen
                if remaining_steps:
                    execution_order.append([list(remaining_steps)[0]])
                    remaining_steps.remove(list(remaining_steps)[0])
        
        return execution_order


class AgentTeam:
    """Equipo de agentes con workflow coordinado"""
    
    def __init__(
        self,
        team_id: str,
        name: str,
        tenant_id: str,
        team_type: TeamType,
        agents: List[TauseStackAgent],
        workflow: Optional[TeamWorkflow] = None,
        description: str = ""
    ):
        self.team_id = team_id
        self.name = name
        self.tenant_id = tenant_id
        self.team_type = team_type
        self.agents = {agent.config.agent_id: agent for agent in agents}
        self.workflow = workflow or self._get_default_workflow()
        self.description = description
        
        # Estado del equipo
        self.is_busy = False
        self.current_execution = None
        self.execution_history = []
        
        # Métricas
        self.stats = {
            "workflows_completed": 0,
            "workflows_failed": 0,
            "total_execution_time_ms": 0,
            "total_tokens_used": 0,
            "average_workflow_time_ms": 0
        }
    
    def _get_default_workflow(self) -> TeamWorkflow:
        """Obtiene el workflow por defecto según el tipo de equipo"""
        if self.team_type == TeamType.RESEARCH:
            return self._create_research_workflow()
        elif self.team_type == TeamType.CONTENT_CREATION:
            return self._create_content_workflow()
        elif self.team_type == TeamType.CUSTOMER_SUPPORT:
            return self._create_support_workflow()
        elif self.team_type == TeamType.ECOMMERCE_OPTIMIZATION:
            return self._create_ecommerce_workflow()
        else:
            return self._create_basic_workflow()
    
    def _create_research_workflow(self) -> TeamWorkflow:
        """Workflow para equipo de investigación"""
        steps = [
            WorkflowStep(
                "research_phase",
                "research",
                "Investiga en profundidad sobre: {topic}. Recopila datos, estadísticas y fuentes confiables.",
                parallel=True
            ),
            WorkflowStep(
                "analysis_phase", 
                "research",
                "Analiza los datos recopilados y identifica patrones, tendencias y insights clave sobre: {topic}",
                depends_on=["research_phase"]
            ),
            WorkflowStep(
                "synthesis_phase",
                "writer", 
                "Sintetiza la investigación y análisis en un reporte ejecutivo sobre: {topic}",
                depends_on=["analysis_phase"]
            )
        ]
        
        return TeamWorkflow(
            "research_workflow",
            "Research Team Workflow",
            "Workflow completo de investigación, análisis y síntesis",
            steps
        )
    
    def _create_content_workflow(self) -> TeamWorkflow:
        """Workflow para equipo de creación de contenido"""
        steps = [
            WorkflowStep(
                "research_content",
                "research",
                "Investiga el tema y audiencia objetivo para: {content_brief}",
                parallel=True
            ),
            WorkflowStep(
                "create_draft",
                "writer",
                "Crea un borrador de contenido basado en: {content_brief}",
                depends_on=["research_content"]
            ),
            WorkflowStep(
                "optimize_seo",
                "writer", 
                "Optimiza el contenido para SEO y mejora la legibilidad",
                depends_on=["create_draft"]
            ),
            WorkflowStep(
                "review_content",
                "writer",
                "Revisa y perfecciona el contenido final",
                depends_on=["optimize_seo"]
            )
        ]
        
        return TeamWorkflow(
            "content_creation_workflow",
            "Content Creation Workflow", 
            "Workflow completo de creación de contenido optimizado",
            steps
        )
    
    def _create_support_workflow(self) -> TeamWorkflow:
        """Workflow para equipo de soporte"""
        steps = [
            WorkflowStep(
                "analyze_issue",
                "customer_support",
                "Analiza el problema del cliente: {customer_issue}",
                parallel=True
            ),
            WorkflowStep(
                "search_knowledge",
                "customer_support", 
                "Busca soluciones en la base de conocimiento para: {customer_issue}",
                parallel=True
            ),
            WorkflowStep(
                "provide_solution",
                "customer_support",
                "Proporciona una solución detallada y personalizada",
                depends_on=["analyze_issue", "search_knowledge"]
            ),
            WorkflowStep(
                "follow_up",
                "customer_support",
                "Programa seguimiento y verifica satisfacción del cliente",
                depends_on=["provide_solution"]
            )
        ]
        
        return TeamWorkflow(
            "support_workflow",
            "Customer Support Workflow",
            "Workflow completo de atención al cliente",
            steps
        )
    
    def _create_ecommerce_workflow(self) -> TeamWorkflow:
        """Workflow para equipo de ecommerce"""
        steps = [
            WorkflowStep(
                "analyze_order",
                "ecommerce",
                "Analiza el pedido y verifica disponibilidad: {order_details}",
                parallel=True
            ),
            WorkflowStep(
                "process_payment",
                "ecommerce",
                "Procesa el pago y verifica la transacción",
                depends_on=["analyze_order"]
            ),
            WorkflowStep(
                "update_inventory", 
                "ecommerce",
                "Actualiza el inventario y reserva productos",
                depends_on=["process_payment"]
            ),
            WorkflowStep(
                "notify_customer",
                "customer_support",
                "Notifica al cliente sobre el estado del pedido",
                depends_on=["update_inventory"]
            )
        ]
        
        return TeamWorkflow(
            "ecommerce_workflow",
            "E-commerce Order Workflow",
            "Workflow completo de procesamiento de pedidos",
            steps
        )
    
    def _create_basic_workflow(self) -> TeamWorkflow:
        """Workflow básico genérico"""
        steps = [
            WorkflowStep(
                "process_task",
                "research",  # Agente por defecto
                "Procesa la tarea: {task}",
                parallel=False
            )
        ]
        
        return TeamWorkflow(
            "basic_workflow",
            "Basic Workflow",
            "Workflow básico para tareas simples",
            steps
        )
    
    async def execute_workflow(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ejecuta el workflow completo del equipo"""
        if self.is_busy:
            raise ValueError("El equipo está ocupado ejecutando otro workflow")
        
        execution_id = str(uuid.uuid4())
        start_time = datetime.now()
        self.is_busy = True
        self.current_execution = execution_id
        
        try:
            context = context or {}
            context.update({
                "task": task,
                "topic": task,
                "content_brief": task,
                "customer_issue": task,
                "order_details": task
            })
            
            execution_order = self.workflow.get_execution_order()
            step_results = {}
            total_tokens = 0
            
            for level in execution_order:
                level_tasks = []
                
                for step_id in level:
                    step = next(s for s in self.workflow.steps if s.step_id == step_id)
                    
                    # Buscar agente apropiado
                    agent = self._find_agent_for_role(step.agent_role)
                    if not agent:
                        raise ValueError(f"No hay agente disponible para el rol: {step.agent_role}")
                    
                    # Preparar tarea con contexto
                    formatted_task = step.task_template.format(**context)
                    
                    # Agregar resultados de pasos anteriores al contexto
                    if step.depends_on:
                        previous_results = []
                        for dep in step.depends_on:
                            if dep in step_results:
                                previous_results.append(f"Resultado de {dep}: {step_results[dep]['response']}")
                        
                        if previous_results:
                            formatted_task += f"\n\nContexto de pasos anteriores:\n" + "\n".join(previous_results)
                    
                    # Crear tarea async
                    level_tasks.append(self._execute_step(agent, step_id, formatted_task, context))
                
                # Ejecutar nivel (en paralelo si hay múltiples pasos)
                level_results = await asyncio.gather(*level_tasks, return_exceptions=True)
                
                # Procesar resultados
                for i, result in enumerate(level_results):
                    step_id = level[i]
                    if isinstance(result, Exception):
                        raise result
                    
                    step_results[step_id] = result
                    if result.get('tokens_used'):
                        total_tokens += result['tokens_used']
            
            # Calcular métricas
            end_time = datetime.now()
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Actualizar estadísticas
            self.stats["workflows_completed"] += 1
            self.stats["total_execution_time_ms"] += execution_time_ms
            self.stats["total_tokens_used"] += total_tokens
            self.stats["average_workflow_time_ms"] = (
                self.stats["total_execution_time_ms"] // self.stats["workflows_completed"]
            )
            
            # Preparar resultado final
            execution_result = {
                "execution_id": execution_id,
                "workflow_name": self.workflow.name,
                "status": "completed",
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "execution_time_ms": execution_time_ms,
                "total_tokens_used": total_tokens,
                "step_results": step_results,
                "final_result": self._synthesize_results(step_results)
            }
            
            self.execution_history.append(execution_result)
            return execution_result
            
        except Exception as e:
            self.stats["workflows_failed"] += 1
            
            error_result = {
                "execution_id": execution_id,
                "workflow_name": self.workflow.name,
                "status": "failed",
                "error": str(e),
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat()
            }
            
            self.execution_history.append(error_result)
            raise e
            
        finally:
            self.is_busy = False
            self.current_execution = None
    
    async def _execute_step(self, agent: TauseStackAgent, step_id: str, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta un paso individual del workflow"""
        result = await agent.execute_task(task, context)
        
        return {
            "step_id": step_id,
            "agent_id": agent.config.agent_id,
            "status": "completed" if result.is_successful() else "failed",
            "response": result.response,
            "tokens_used": result.metrics.tokens_used if result.metrics else 0,
            "duration_ms": result.get_duration_ms(),
            "error": result.error_message if not result.is_successful() else None
        }
    
    def _find_agent_for_role(self, role_name: str) -> Optional[TauseStackAgent]:
        """Encuentra un agente apropiado para el rol especificado"""
        for agent in self.agents.values():
            # Mapear nombres de rol a tipos
            agent_role_type = agent.config.role.name.lower().replace(" ", "_")
            if role_name in agent_role_type or agent_role_type in role_name:
                return agent
        
        # Fallback: devolver el primer agente disponible
        return next(iter(self.agents.values())) if self.agents else None
    
    def _synthesize_results(self, step_results: Dict[str, Any]) -> str:
        """Sintetiza los resultados de todos los pasos"""
        if not step_results:
            return "No hay resultados disponibles"
        
        synthesis = f"Resultado del workflow '{self.workflow.name}':\n\n"
        
        for step_id, result in step_results.items():
            step = next(s for s in self.workflow.steps if s.step_id == step_id)
            synthesis += f"**{step_id.replace('_', ' ').title()}:**\n"
            synthesis += f"{result['response']}\n\n"
        
        return synthesis
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado actual del equipo"""
        return {
            "team_id": self.team_id,
            "name": self.name,
            "team_type": self.team_type.value,
            "tenant_id": self.tenant_id,
            "is_busy": self.is_busy,
            "agent_count": len(self.agents),
            "workflow_name": self.workflow.name,
            "current_execution": self.current_execution,
            "stats": self.stats,
            "agents": [
                {
                    "agent_id": agent.config.agent_id,
                    "name": agent.config.name,
                    "role": agent.config.role.name
                }
                for agent in self.agents.values()
            ]
        }


class PresetTeams:
    """Equipos predefinidos para casos de uso comunes"""
    
    @staticmethod
    async def create_research_team(tenant_id: str, api_base_url: str = "http://localhost:9001") -> AgentTeam:
        """Crea un equipo de investigación completo"""
        from .tausestack_agent import TauseStackAgent
        
        # Crear agentes especializados
        research_agent = TauseStackAgent(
            config=AgentConfig(
                agent_id=f"research-lead-{uuid.uuid4().hex[:8]}",
                tenant_id=tenant_id,
                name="Research Lead",
                role=PresetRoles.research_agent(),
                custom_instructions="Especializado en investigación exhaustiva y análisis de datos"
            ),
            api_base_url=api_base_url
        )
        
        analyst_agent = TauseStackAgent(
            config=AgentConfig(
                agent_id=f"data-analyst-{uuid.uuid4().hex[:8]}",
                tenant_id=tenant_id,
                name="Data Analyst", 
                role=PresetRoles.research_agent(),
                custom_instructions="Especializado en análisis estadístico y identificación de patrones"
            ),
            api_base_url=api_base_url
        )
        
        writer_agent = TauseStackAgent(
            config=AgentConfig(
                agent_id=f"report-writer-{uuid.uuid4().hex[:8]}",
                tenant_id=tenant_id,
                name="Report Writer",
                role=PresetRoles.writer_agent(),
                custom_instructions="Especializado en síntesis y redacción de reportes ejecutivos"
            ),
            api_base_url=api_base_url
        )
        
        return AgentTeam(
            team_id=f"research-team-{uuid.uuid4().hex[:8]}",
            name="Research Team",
            tenant_id=tenant_id,
            team_type=TeamType.RESEARCH,
            agents=[research_agent, analyst_agent, writer_agent],
            description="Equipo especializado en investigación, análisis y síntesis de información"
        )
    
    @staticmethod
    async def create_content_team(tenant_id: str, api_base_url: str = "http://localhost:9001") -> AgentTeam:
        """Crea un equipo de creación de contenido"""
        from .tausestack_agent import TauseStackAgent
        
        researcher = TauseStackAgent(
            config=AgentConfig(
                agent_id=f"content-researcher-{uuid.uuid4().hex[:8]}",
                tenant_id=tenant_id,
                name="Content Researcher",
                role=PresetRoles.research_agent(),
                custom_instructions="Investigación para creación de contenido y análisis de audiencia"
            ),
            api_base_url=api_base_url
        )
        
        writer = TauseStackAgent(
            config=AgentConfig(
                agent_id=f"content-writer-{uuid.uuid4().hex[:8]}",
                tenant_id=tenant_id,
                name="Content Writer",
                role=PresetRoles.writer_agent(),
                custom_instructions="Creación de contenido atractivo y optimizado para SEO"
            ),
            api_base_url=api_base_url
        )
        
        editor = TauseStackAgent(
            config=AgentConfig(
                agent_id=f"content-editor-{uuid.uuid4().hex[:8]}",
                tenant_id=tenant_id,
                name="Content Editor",
                role=PresetRoles.writer_agent(),
                custom_instructions="Edición, optimización y perfeccionamiento de contenido"
            ),
            api_base_url=api_base_url
        )
        
        return AgentTeam(
            team_id=f"content-team-{uuid.uuid4().hex[:8]}",
            name="Content Creation Team",
            tenant_id=tenant_id,
            team_type=TeamType.CONTENT_CREATION,
            agents=[researcher, writer, editor],
            description="Equipo especializado en creación de contenido de alta calidad"
        ) 