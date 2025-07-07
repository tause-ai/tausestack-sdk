#!/usr/bin/env python3
"""
TauseStack Agent API Service

API REST para gestionar agentes de IA multi-tenant.
Incluye CRUD de agentes, ejecución de tareas, y monitoreo.
"""

import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import aiofiles
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field

# Importar componentes de Agent Engine
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from tausestack.services.agent_engine.core.agent_role import AgentRole, AgentType, PresetRoles
from tausestack.services.agent_engine.core.agent_config import AgentConfig
from tausestack.services.agent_engine.core.agent_result import AgentResult
from tausestack.services.agent_engine.core.tausestack_agent import TauseStackAgent, TauseStackAgentManager


# ========================= MODELS =========================

class AgentStatusModel(BaseModel):
    agent_id: str
    name: str
    tenant_id: str
    role_name: str
    enabled: bool
    is_busy: bool
    tasks_completed: int
    tasks_failed: int
    total_tokens_used: int
    total_execution_time_ms: int
    memory_size: int
    last_activity: Optional[datetime]

class AgentCreateRequest(BaseModel):
    name: str
    tenant_id: str
    role_type: str  # "research", "writer", "customer_support", "ecommerce", "custom"
    custom_role: Optional[Dict[str, Any]] = None
    enabled: bool = True
    custom_instructions: Optional[str] = None
    allowed_tools: List[str] = Field(default_factory=list)

class AgentUpdateRequest(BaseModel):
    name: Optional[str] = None
    enabled: Optional[bool] = None
    custom_instructions: Optional[str] = None
    allowed_tools: Optional[List[str]] = None

class TaskExecutionRequest(BaseModel):
    task: str
    context: Dict[str, Any] = Field(default_factory=dict)
    priority: str = "normal"  # "low", "normal", "high"

class TaskExecutionResponse(BaseModel):
    task_id: str
    agent_id: str
    status: str  # "queued", "running", "completed", "failed"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: Optional[int] = None
    tokens_used: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

class AgentMemoryResponse(BaseModel):
    total_interactions: int
    memory_size_mb: float
    context_types: List[str]
    last_activity: Optional[datetime]
    task_statistics: Dict[str, int]


# ========================= SERVICE =========================

class AgentAPIService:
    def __init__(self):
        self.app = FastAPI(
            title="TauseStack Agent API",
            description="API para gestión de agentes de IA multi-tenant",
            version="1.0.0"
        )
        
        self.security = HTTPBearer()
        self.agent_manager = TauseStackAgentManager(
            api_base_url="http://localhost:9001",
            storage_path=".tausestack_storage"
        )
        
        # Storage para agentes configurados
        self.data_dir = Path(".tausestack_storage/agents")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.agents_file = self.data_dir / "agent_configs.json"
        self.tasks_file = self.data_dir / "task_history.json"
        
        # Estado en memoria
        self.active_agents: Dict[str, TauseStackAgent] = {}
        self.task_queue: List[TaskExecutionResponse] = []
        self.task_history: List[TaskExecutionResponse] = []
        
        # Configurar eventos
        self.app.add_event_handler("startup", self._load_agents)
        
        # Configurar rutas
        self._setup_routes()
    
    async def _load_agents(self):
        """Cargar agentes guardados al iniciar"""
        try:
            if self.agents_file.exists():
                async with aiofiles.open(self.agents_file, 'r') as f:
                    content = await f.read()
                    agents_data = json.loads(content)
                    
                    for agent_data in agents_data:
                        await self._recreate_agent_from_data(agent_data)
            
            # Cargar historial de tareas
            if self.tasks_file.exists():
                async with aiofiles.open(self.tasks_file, 'r') as f:
                    content = await f.read()
                    tasks_data = json.loads(content)
                    
                    for task_data in tasks_data:
                        task_data['created_at'] = datetime.fromisoformat(task_data['created_at'])
                        if task_data.get('completed_at'):
                            task_data['completed_at'] = datetime.fromisoformat(task_data['completed_at'])
                        self.task_history.append(TaskExecutionResponse(**task_data))
                        
        except Exception as e:
            print(f"Error loading agents: {e}")
    
    async def _recreate_agent_from_data(self, agent_data: Dict[str, Any]):
        """Recrear un agente desde datos guardados"""
        try:
            # Recrear rol
            if agent_data.get('custom_role'):
                role = AgentRole(**agent_data['custom_role'])
            else:
                # Usar rol preset
                role_type = agent_data.get('role_type', 'research')
                if role_type == 'research':
                    role = PresetRoles.research_agent()
                elif role_type == 'writer':
                    role = PresetRoles.writer_agent()
                elif role_type == 'customer_support':
                    role = PresetRoles.customer_support_agent()
                elif role_type == 'ecommerce':
                    role = PresetRoles.ecommerce_agent()
                else:
                    role = PresetRoles.research_agent()  # Default
            
            # Recrear configuración
            config = AgentConfig(
                agent_id=agent_data['agent_id'],
                tenant_id=agent_data['tenant_id'],
                name=agent_data['name'],
                role=role,
                enabled=agent_data.get('enabled', True),
                custom_instructions=agent_data.get('custom_instructions'),
                allowed_tools=agent_data.get('allowed_tools', [])
            )
            
            # Crear agente
            agent = TauseStackAgent(
                config=config,
                api_base_url="http://localhost:9001",
                storage_path=".tausestack_storage"
            )
            
            self.active_agents[config.agent_id] = agent
            await self.agent_manager.add_agent(agent)
            
        except Exception as e:
            print(f"Error recreating agent {agent_data.get('agent_id', 'unknown')}: {e}")
    
    async def _save_agents(self):
        """Guardar configuraciones de agentes"""
        try:
            agents_data = []
            for agent_id, agent in self.active_agents.items():
                agent_data = {
                    'agent_id': agent.config.agent_id,
                    'tenant_id': agent.config.tenant_id,
                    'name': agent.config.name,
                    'role_type': agent.config.role.type.value if hasattr(agent.config.role, 'type') else 'custom',
                    'custom_role': agent.config.role.dict() if hasattr(agent.config.role, 'dict') else None,
                    'enabled': agent.config.enabled,
                    'custom_instructions': agent.config.custom_instructions,
                    'allowed_tools': agent.config.allowed_tools,
                    'created_at': datetime.now().isoformat()
                }
                agents_data.append(agent_data)
            
            async with aiofiles.open(self.agents_file, 'w') as f:
                await f.write(json.dumps(agents_data, indent=2))
                
        except Exception as e:
            print(f"Error saving agents: {e}")
    
    async def _save_task_history(self):
        """Guardar historial de tareas"""
        try:
            # Mantener solo las últimas 500 tareas
            recent_history = self.task_history[-500:]
            
            tasks_data = []
            for task in recent_history:
                task_dict = task.dict()
                task_dict['created_at'] = task_dict['created_at'].isoformat()
                if task_dict.get('completed_at'):
                    task_dict['completed_at'] = task_dict['completed_at'].isoformat()
                tasks_data.append(task_dict)
            
            async with aiofiles.open(self.tasks_file, 'w') as f:
                await f.write(json.dumps(tasks_data, indent=2))
                
        except Exception as e:
            print(f"Error saving task history: {e}")
    
    def _setup_routes(self):
        """Configurar todas las rutas del API"""
        
        @self.app.get("/agents", response_model=List[AgentStatusModel])
        async def list_agents():
            """Listar todos los agentes configurados"""
            agents_status = []
            
            for agent_id, agent in self.active_agents.items():
                status = await agent.get_status()
                agent_status = AgentStatusModel(
                    agent_id=agent.config.agent_id,
                    name=agent.config.name,
                    tenant_id=agent.config.tenant_id,
                    role_name=agent.config.role.name,
                    enabled=status['enabled'],
                    is_busy=status['is_busy'],
                    tasks_completed=status['stats']['tasks_completed'],
                    tasks_failed=status['stats']['tasks_failed'],
                    total_tokens_used=status['stats']['total_tokens_used'],
                    total_execution_time_ms=status['stats']['total_execution_time_ms'],
                    memory_size=status['memory_size'],
                    last_activity=status.get('last_activity')
                )
                agents_status.append(agent_status)
            
            return agents_status
        
        @self.app.post("/agents", response_model=AgentStatusModel)
        async def create_agent(request: AgentCreateRequest):
            """Crear un nuevo agente"""
            # Generar ID único
            agent_id = f"{request.name.lower().replace(' ', '-')}-{str(uuid.uuid4())[:8]}"
            
            # Crear rol
            if request.role_type == "custom" and request.custom_role:
                role = AgentRole(**request.custom_role)
            else:
                # Usar rol preset
                if request.role_type == "research":
                    role = PresetRoles.research_agent()
                elif request.role_type == "writer":
                    role = PresetRoles.writer_agent()
                elif request.role_type == "customer_support":
                    role = PresetRoles.customer_support_agent()
                elif request.role_type == "ecommerce":
                    role = PresetRoles.ecommerce_agent()
                else:
                    raise HTTPException(status_code=400, detail="Tipo de rol no válido")
            
            # Crear configuración
            config = AgentConfig(
                agent_id=agent_id,
                tenant_id=request.tenant_id,
                name=request.name,
                role=role,
                enabled=request.enabled,
                custom_instructions=request.custom_instructions,
                allowed_tools=request.allowed_tools
            )
            
            # Crear agente
            agent = TauseStackAgent(
                config=config,
                api_base_url="http://localhost:9001",
                storage_path=".tausestack_storage"
            )
            
            # Registrar
            self.active_agents[agent_id] = agent
            await self.agent_manager.add_agent(agent)
            await self._save_agents()
            
            # Retornar status
            status = await agent.get_status()
            return AgentStatusModel(
                agent_id=agent.config.agent_id,
                name=agent.config.name,
                tenant_id=agent.config.tenant_id,
                role_name=agent.config.role.name,
                enabled=status['enabled'],
                is_busy=status['is_busy'],
                tasks_completed=status['stats']['tasks_completed'],
                tasks_failed=status['stats']['tasks_failed'],
                total_tokens_used=status['stats']['total_tokens_used'],
                total_execution_time_ms=status['stats']['total_execution_time_ms'],
                memory_size=status['memory_size'],
                last_activity=status.get('last_activity')
            )
        
        @self.app.get("/agents/{agent_id}", response_model=AgentStatusModel)
        async def get_agent(agent_id: str):
            """Obtener información de un agente específico"""
            if agent_id not in self.active_agents:
                raise HTTPException(status_code=404, detail="Agente no encontrado")
            
            agent = self.active_agents[agent_id]
            status = await agent.get_status()
            
            return AgentStatusModel(
                agent_id=agent.config.agent_id,
                name=agent.config.name,
                tenant_id=agent.config.tenant_id,
                role_name=agent.config.role.name,
                enabled=status['enabled'],
                is_busy=status['is_busy'],
                tasks_completed=status['stats']['tasks_completed'],
                tasks_failed=status['stats']['tasks_failed'],
                total_tokens_used=status['stats']['total_tokens_used'],
                total_execution_time_ms=status['stats']['total_execution_time_ms'],
                memory_size=status['memory_size'],
                last_activity=status.get('last_activity')
            )
        
        @self.app.put("/agents/{agent_id}", response_model=AgentStatusModel)
        async def update_agent(agent_id: str, request: AgentUpdateRequest):
            """Actualizar configuración de un agente"""
            if agent_id not in self.active_agents:
                raise HTTPException(status_code=404, detail="Agente no encontrado")
            
            agent = self.active_agents[agent_id]
            
            # Actualizar configuración
            if request.name is not None:
                agent.config.name = request.name
            if request.enabled is not None:
                agent.config.enabled = request.enabled
            if request.custom_instructions is not None:
                agent.config.custom_instructions = request.custom_instructions
            if request.allowed_tools is not None:
                agent.config.allowed_tools = request.allowed_tools
            
            await self._save_agents()
            
            # Retornar status actualizado
            status = await agent.get_status()
            return AgentStatusModel(
                agent_id=agent.config.agent_id,
                name=agent.config.name,
                tenant_id=agent.config.tenant_id,
                role_name=agent.config.role.name,
                enabled=status['enabled'],
                is_busy=status['is_busy'],
                tasks_completed=status['stats']['tasks_completed'],
                tasks_failed=status['stats']['tasks_failed'],
                total_tokens_used=status['stats']['total_tokens_used'],
                total_execution_time_ms=status['stats']['total_execution_time_ms'],
                memory_size=status['memory_size'],
                last_activity=status.get('last_activity')
            )
        
        @self.app.delete("/agents/{agent_id}")
        async def delete_agent(agent_id: str):
            """Eliminar un agente"""
            if agent_id not in self.active_agents:
                raise HTTPException(status_code=404, detail="Agente no encontrado")
            
            # Remover del manager y memoria
            await self.agent_manager.remove_agent(agent_id)
            del self.active_agents[agent_id]
            await self._save_agents()
            
            return {"message": f"Agente {agent_id} eliminado exitosamente"}
        
        @self.app.post("/agents/{agent_id}/execute", response_model=TaskExecutionResponse)
        async def execute_task(agent_id: str, request: TaskExecutionRequest, background_tasks: BackgroundTasks):
            """Ejecutar una tarea en un agente específico"""
            if agent_id not in self.active_agents:
                raise HTTPException(status_code=404, detail="Agente no encontrado")
            
            agent = self.active_agents[agent_id]
            
            if not agent.config.enabled:
                raise HTTPException(status_code=400, detail="Agente deshabilitado")
            
            # Crear tarea
            task_id = str(uuid.uuid4())
            task_response = TaskExecutionResponse(
                task_id=task_id,
                agent_id=agent_id,
                status="queued",
                created_at=datetime.now()
            )
            
            self.task_queue.append(task_response)
            
            # Ejecutar en background
            background_tasks.add_task(self._execute_task_background, task_response, agent, request)
            
            return task_response
        
        @self.app.get("/agents/{agent_id}/memory", response_model=AgentMemoryResponse)
        async def get_agent_memory(agent_id: str):
            """Obtener información de memoria de un agente"""
            if agent_id not in self.active_agents:
                raise HTTPException(status_code=404, detail="Agente no encontrado")
            
            agent = self.active_agents[agent_id]
            memory_summary = await agent.get_memory_summary()
            
            return AgentMemoryResponse(**memory_summary)
        
        @self.app.get("/tasks", response_model=List[TaskExecutionResponse])
        async def list_tasks(limit: int = 50, agent_id: Optional[str] = None):
            """Listar historial de tareas"""
            tasks = self.task_history[-limit:]
            
            if agent_id:
                tasks = [t for t in tasks if t.agent_id == agent_id]
            
            return tasks
        
        @self.app.get("/tasks/{task_id}", response_model=TaskExecutionResponse)
        async def get_task(task_id: str):
            """Obtener información de una tarea específica"""
            # Buscar en queue primero
            for task in self.task_queue:
                if task.task_id == task_id:
                    return task
            
            # Buscar en historial
            for task in self.task_history:
                if task.task_id == task_id:
                    return task
            
            raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    async def _execute_task_background(self, task_response: TaskExecutionResponse, agent: TauseStackAgent, request: TaskExecutionRequest):
        """Ejecutar tarea en background"""
        try:
            # Actualizar status
            task_response.status = "running"
            
            # Ejecutar tarea
            result = await agent.execute_task(request.task, request.context)
            
            # Actualizar respuesta
            task_response.status = "completed" if result.is_successful() else "failed"
            task_response.completed_at = datetime.now()
            task_response.duration_ms = result.get_duration_ms()
            
            if result.is_successful():
                task_response.result = {
                    "response": result.response,
                    "confidence": getattr(result, 'confidence', None)
                }
                if result.metrics:
                    task_response.tokens_used = result.metrics.tokens_used
            else:
                task_response.error = result.error_message
            
            # Mover de queue a historial
            if task_response in self.task_queue:
                self.task_queue.remove(task_response)
            self.task_history.append(task_response)
            
            await self._save_task_history()
            
        except Exception as e:
            task_response.status = "failed"
            task_response.error = str(e)
            task_response.completed_at = datetime.now()
            
            if task_response in self.task_queue:
                self.task_queue.remove(task_response)
            self.task_history.append(task_response)
            
            await self._save_task_history()


# ========================= STARTUP =========================

if __name__ == "__main__":
    agent_service = AgentAPIService()
    uvicorn.run(
        agent_service.app,
        host="0.0.0.0",
        port=8003,
        log_level="info"
    ) 