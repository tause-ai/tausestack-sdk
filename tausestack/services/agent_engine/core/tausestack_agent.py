"""
TauseStack Agent - Agente base que usa la infraestructura existente de TauseStack
"""

import uuid
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import httpx

from .agent_role import AgentRole
from .agent_config import AgentConfig
from .agent_result import AgentResult, AgentMetrics, TaskStatus
from ..memory.agent_memory import AgentMemory
from ..tools.agent_tools import AgentToolsManager


class TauseStackAgent:
    """
    Agente base que aprovecha la infraestructura existente de TauseStack:
    - AI Services (OpenAI, Claude)
    - Storage multi-tenant
    - Analytics 
    - Memory persistente
    """
    
    def __init__(
        self, 
        config: AgentConfig,
        api_base_url: str = "http://localhost:9001",
        storage_path: str = ".tausestack_storage"
    ):
        self.config = config
        self.api_base_url = api_base_url
        self.storage_path = storage_path
        
        # Inicializar componentes
        self.memory = AgentMemory(
            agent_id=config.agent_id,
            tenant_id=config.tenant_id,
            storage_path=storage_path
        )
        
        self.tools_manager = AgentToolsManager(
            allowed_tools=config.allowed_tools,
            restricted_tools=config.restricted_tools
        )
        
        # Estado del agente
        self.is_busy = False
        self.current_task_id: Optional[str] = None
        self.stats = {
            'tasks_completed': 0,
            'tasks_failed': 0,
            'total_tokens_used': 0,
            'total_execution_time_ms': 0
        }
    
    async def execute_task(self, task: str, context: Dict[str, Any] = None) -> AgentResult:
        """
        Ejecutar una tarea específica
        """
        if self.is_busy:
            raise Exception("Agent is currently busy with another task")
        
        task_id = str(uuid.uuid4())
        self.current_task_id = task_id
        self.is_busy = True
        
        # Crear resultado inicial
        result = AgentResult(
            task_id=task_id,
            agent_id=self.config.agent_id,
            tenant_id=self.config.tenant_id,
            status=TaskStatus.IN_PROGRESS,
            result=None
        )
        
        start_time = datetime.now()
        
        try:
            # Preparar contexto
            full_context = await self._prepare_context(task, context or {})
            
            # Ejecutar tarea con reintentos
            task_result = await self._execute_with_retry(task, full_context)
            
            # Guardar en memoria
            await self.memory.add_interaction(task, task_result)
            
            # Calcular métricas
            end_time = datetime.now()
            execution_time = int((end_time - start_time).total_seconds() * 1000)
            
            metrics = AgentMetrics(
                execution_time_ms=execution_time,
                tokens_used=task_result.get('tokens_used', 0),
                api_calls=1,
                model_used=self.config.get_model_config()['model']
            )
            
            # Actualizar resultado
            result.mark_completed(task_result, metrics)
            
            # Actualizar estadísticas
            self.stats['tasks_completed'] += 1
            self.stats['total_tokens_used'] += metrics.tokens_used
            self.stats['total_execution_time_ms'] += execution_time
            
            return result
            
        except Exception as e:
            result.mark_failed(str(e))
            self.stats['tasks_failed'] += 1
            return result
            
        finally:
            self.is_busy = False
            self.current_task_id = None
    
    async def _prepare_context(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Preparar contexto completo para la tarea"""
        
        # Obtener memoria relevante
        memory_context = await self.memory.get_relevant_context(task)
        
        # Combinar contextos
        full_context = {
            'task': task,
            'agent_instructions': self.config.get_effective_instructions(),
            'memory_context': memory_context,
            'user_context': context,
            'available_tools': self.tools_manager.get_available_tools(),
            'model_config': self.config.get_model_config()
        }
        
        return full_context
    
    async def _execute_with_retry(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar tarea con reintentos"""
        
        for attempt in range(self.config.retry_attempts):
            try:
                return await self._call_ai_service(task, context)
            except Exception as e:
                if attempt == self.config.retry_attempts - 1:
                    raise e
                
                # Esperar antes del siguiente intento
                await asyncio.sleep(2 ** attempt)
        
        raise Exception("Max retry attempts reached")
    
    async def _call_ai_service(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Llamar al AI Service de TauseStack"""
        
        model_config = context['model_config']
        
        # Construir prompt
        prompt = self._build_prompt(task, context)
        
        # Preparar payload
        payload = {
            'model': model_config['model'],
            'temperature': model_config['temperature'],
            'max_tokens': model_config['max_tokens'],
            'prompt': prompt,
            'tenant_id': self.config.tenant_id,
            'agent_id': self.config.agent_id
        }
        
        # Llamar al AI Service a través del API Gateway
        timeout = httpx.Timeout(self.config.timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout) as client:
            
            # Determinar endpoint según el modelo
            if model_config['model'].startswith('gpt'):
                endpoint = f"{self.api_base_url}/ai/openai/completion"
            elif model_config['model'].startswith('claude'):
                endpoint = f"{self.api_base_url}/ai/claude/completion"
            else:
                endpoint = f"{self.api_base_url}/ai/completion"
            
            response = await client.post(endpoint, json=payload)
            
            if response.status_code != 200:
                raise Exception(f"AI Service error: {response.status_code} - {response.text}")
            
            return response.json()
    
    def _build_prompt(self, task: str, context: Dict[str, Any]) -> str:
        """Construir prompt completo para el AI Service"""
        
        prompt_parts = [
            f"INSTRUCTIONS:\n{context['agent_instructions']}\n",
            f"TASK:\n{task}\n"
        ]
        
        # Agregar contexto de memoria si existe
        if context.get('memory_context'):
            prompt_parts.append(f"RELEVANT CONTEXT:\n{context['memory_context']}\n")
        
        # Agregar contexto del usuario
        if context.get('user_context'):
            prompt_parts.append(f"ADDITIONAL CONTEXT:\n{json.dumps(context['user_context'], indent=2)}\n")
        
        # Agregar herramientas disponibles
        if context.get('available_tools'):
            tools_list = "\n".join([f"- {tool}" for tool in context['available_tools']])
            prompt_parts.append(f"AVAILABLE TOOLS:\n{tools_list}\n")
        
        prompt_parts.append("RESPONSE:")
        
        return "\n".join(prompt_parts)
    
    async def get_status(self) -> Dict[str, Any]:
        """Obtener estado actual del agente"""
        return {
            'agent_id': self.config.agent_id,
            'name': self.config.name,
            'tenant_id': self.config.tenant_id,
            'role': self.config.role.name,
            'enabled': self.config.enabled,
            'is_busy': self.is_busy,
            'current_task_id': self.current_task_id,
            'stats': self.stats,
            'memory_size': await self.memory.get_size(),
            'last_activity': await self.memory.get_last_activity()
        }
    
    async def update_config(self, **kwargs):
        """Actualizar configuración del agente"""
        self.config.update_config(**kwargs)
        
        # Actualizar herramientas si cambiaron
        if 'allowed_tools' in kwargs or 'restricted_tools' in kwargs:
            self.tools_manager.update_tools(
                allowed_tools=self.config.allowed_tools,
                restricted_tools=self.config.restricted_tools
            )
    
    async def clear_memory(self):
        """Limpiar memoria del agente"""
        await self.memory.clear()
    
    async def get_memory_summary(self) -> Dict[str, Any]:
        """Obtener resumen de la memoria"""
        return await self.memory.get_summary()
    
    def get_config(self) -> AgentConfig:
        """Obtener configuración actual"""
        return self.config


class TauseStackAgentManager:
    """Gestor de agentes TauseStack"""
    
    def __init__(
        self, 
        api_base_url: str = "http://localhost:9001",
        storage_path: str = ".tausestack_storage"
    ):
        self.api_base_url = api_base_url
        self.storage_path = storage_path
        self.agents: Dict[str, TauseStackAgent] = {}
    
    def create_agent(self, config: AgentConfig) -> TauseStackAgent:
        """Crear nuevo agente"""
        agent = TauseStackAgent(
            config=config,
            api_base_url=self.api_base_url,
            storage_path=self.storage_path
        )
        
        self.agents[config.agent_id] = agent
        return agent
    
    def get_agent(self, agent_id: str) -> Optional[TauseStackAgent]:
        """Obtener agente por ID"""
        return self.agents.get(agent_id)
    
    def get_agents_by_tenant(self, tenant_id: str) -> List[TauseStackAgent]:
        """Obtener agentes por tenant"""
        return [
            agent for agent in self.agents.values() 
            if agent.config.tenant_id == tenant_id
        ]
    
    async def get_all_statuses(self) -> List[Dict[str, Any]]:
        """Obtener estado de todos los agentes"""
        statuses = []
        for agent in self.agents.values():
            status = await agent.get_status()
            statuses.append(status)
        return statuses
    
    async def execute_task(
        self, 
        agent_id: str, 
        task: str, 
        context: Dict[str, Any] = None
    ) -> AgentResult:
        """Ejecutar tarea en agente específico"""
        agent = self.get_agent(agent_id)
        if not agent:
            raise Exception(f"Agent {agent_id} not found")
        
        if not agent.config.enabled:
            raise Exception(f"Agent {agent_id} is disabled")
        
        return await agent.execute_task(task, context)
    
    def remove_agent(self, agent_id: str) -> bool:
        """Eliminar agente"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            return True
        return False 