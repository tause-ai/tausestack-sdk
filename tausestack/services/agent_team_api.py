#!/usr/bin/env python3
"""
TauseStack Agent Team API Service

API REST para gestionar equipos de agentes con workflows coordinados.
Complementa al Agent API individual con funcionalidad de equipos.
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

from tausestack.services.agent_engine.core.agent_team import AgentTeam, TeamType, PresetTeams
from tausestack.services.agent_engine.core.tausestack_agent import TauseStackAgent, TauseStackAgentManager


# ========================= MODELS =========================

class TeamStatusModel(BaseModel):
    team_id: str
    name: str
    team_type: str
    tenant_id: str
    is_busy: bool
    agent_count: int
    workflow_name: str
    current_execution: Optional[str]
    workflows_completed: int
    workflows_failed: int
    total_execution_time_ms: int
    total_tokens_used: int
    agents: List[Dict[str, str]]

class TeamCreateRequest(BaseModel):
    name: str
    tenant_id: str
    team_type: str  # "research", "content_creation", "customer_support", "ecommerce_optimization", "custom"
    agent_ids: List[str]  # IDs de agentes existentes
    description: Optional[str] = None

class TeamWorkflowRequest(BaseModel):
    task: str
    context: Dict[str, Any] = Field(default_factory=dict)
    priority: str = "normal"

class TeamExecutionResponse(BaseModel):
    execution_id: str
    team_id: str
    workflow_name: str
    status: str  # "running", "completed", "failed"
    start_time: datetime
    end_time: Optional[datetime] = None
    execution_time_ms: Optional[int] = None
    total_tokens_used: Optional[int] = None
    step_results: Optional[Dict[str, Any]] = None
    final_result: Optional[str] = None
    error: Optional[str] = None


# ========================= SERVICE =========================

class AgentTeamAPIService:
    def __init__(self):
        self.app = FastAPI(
            title="TauseStack Agent Team API",
            description="API para gestión de equipos de agentes con workflows",
            version="1.0.0"
        )
        
        self.security = HTTPBearer()
        
        # Integración con Agent Manager para acceder a agentes individuales
        self.agent_manager = TauseStackAgentManager(
            api_base_url="http://localhost:9001",
            storage_path=".tausestack_storage"
        )
        
        # Storage para equipos
        self.data_dir = Path(".tausestack_storage/teams")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.teams_file = self.data_dir / "team_configs.json"
        self.executions_file = self.data_dir / "team_executions.json"
        
        # Estado en memoria
        self.active_teams: Dict[str, AgentTeam] = {}
        self.execution_queue: List[TeamExecutionResponse] = []
        self.execution_history: List[TeamExecutionResponse] = []
        
        # Configurar eventos
        self.app.add_event_handler("startup", self._load_teams)
        
        # Configurar rutas
        self._setup_routes()
    
    async def _load_teams(self):
        """Cargar equipos guardados al iniciar"""
        try:
            if self.teams_file.exists():
                async with aiofiles.open(self.teams_file, 'r') as f:
                    content = await f.read()
                    teams_data = json.loads(content)
                    
                    for team_data in teams_data:
                        await self._recreate_team_from_data(team_data)
            
            # Cargar historial de ejecuciones
            if self.executions_file.exists():
                async with aiofiles.open(self.executions_file, 'r') as f:
                    content = await f.read()
                    executions_data = json.loads(content)
                    
                    for exec_data in executions_data:
                        exec_data['start_time'] = datetime.fromisoformat(exec_data['start_time'])
                        if exec_data.get('end_time'):
                            exec_data['end_time'] = datetime.fromisoformat(exec_data['end_time'])
                        self.execution_history.append(TeamExecutionResponse(**exec_data))
                        
        except Exception as e:
            print(f"Error loading teams: {e}")
    
    async def _recreate_team_from_data(self, team_data: Dict[str, Any]):
        """Recrear un equipo desde datos guardados"""
        try:
            # Obtener agentes desde el agent manager
            agents = []
            for agent_id in team_data.get('agent_ids', []):
                if agent_id in self.agent_manager.agents:
                    agents.append(self.agent_manager.agents[agent_id])
            
            if not agents:
                print(f"No agents found for team {team_data.get('team_id')}")
                return
            
            # Recrear equipo
            team = AgentTeam(
                team_id=team_data['team_id'],
                name=team_data['name'],
                tenant_id=team_data['tenant_id'],
                team_type=TeamType(team_data['team_type']),
                agents=agents,
                description=team_data.get('description', '')
            )
            
            # Restaurar estadísticas si existen
            if 'stats' in team_data:
                team.stats.update(team_data['stats'])
            
            self.active_teams[team.team_id] = team
            
        except Exception as e:
            print(f"Error recreating team {team_data.get('team_id', 'unknown')}: {e}")
    
    async def _save_teams(self):
        """Guardar configuraciones de equipos"""
        try:
            teams_data = []
            for team_id, team in self.active_teams.items():
                team_data = {
                    'team_id': team.team_id,
                    'name': team.name,
                    'tenant_id': team.tenant_id,
                    'team_type': team.team_type.value,
                    'description': team.description,
                    'agent_ids': list(team.agents.keys()),
                    'stats': team.stats,
                    'created_at': datetime.now().isoformat()
                }
                teams_data.append(team_data)
            
            async with aiofiles.open(self.teams_file, 'w') as f:
                await f.write(json.dumps(teams_data, indent=2))
                
        except Exception as e:
            print(f"Error saving teams: {e}")
    
    async def _save_executions(self):
        """Guardar historial de ejecuciones"""
        try:
            # Mantener solo las últimas 200 ejecuciones
            recent_history = self.execution_history[-200:]
            
            executions_data = []
            for execution in recent_history:
                exec_dict = execution.dict()
                exec_dict['start_time'] = exec_dict['start_time'].isoformat()
                if exec_dict.get('end_time'):
                    exec_dict['end_time'] = exec_dict['end_time'].isoformat()
                executions_data.append(exec_dict)
            
            async with aiofiles.open(self.executions_file, 'w') as f:
                await f.write(json.dumps(executions_data, indent=2))
                
        except Exception as e:
            print(f"Error saving executions: {e}")
    
    def _setup_routes(self):
        """Configurar todas las rutas del API"""
        
        @self.app.get("/teams", response_model=List[TeamStatusModel])
        async def list_teams():
            """Listar todos los equipos configurados"""
            teams_status = []
            
            for team_id, team in self.active_teams.items():
                status = team.get_status()
                team_status = TeamStatusModel(
                    team_id=status['team_id'],
                    name=status['name'],
                    team_type=status['team_type'],
                    tenant_id=status['tenant_id'],
                    is_busy=status['is_busy'],
                    agent_count=status['agent_count'],
                    workflow_name=status['workflow_name'],
                    current_execution=status['current_execution'],
                    workflows_completed=status['stats']['workflows_completed'],
                    workflows_failed=status['stats']['workflows_failed'],
                    total_execution_time_ms=status['stats']['total_execution_time_ms'],
                    total_tokens_used=status['stats']['total_tokens_used'],
                    agents=status['agents']
                )
                teams_status.append(team_status)
            
            return teams_status
        
        @self.app.post("/teams", response_model=TeamStatusModel)
        async def create_team(request: TeamCreateRequest):
            """Crear un nuevo equipo"""
            # Validar que existan los agentes
            agents = []
            for agent_id in request.agent_ids:
                if agent_id not in self.agent_manager.agents:
                    raise HTTPException(status_code=400, detail=f"Agent {agent_id} not found")
                agents.append(self.agent_manager.agents[agent_id])
            
            if not agents:
                raise HTTPException(status_code=400, detail="At least one agent is required")
            
            # Validar tipo de equipo
            try:
                team_type = TeamType(request.team_type)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid team type")
            
            # Crear equipo
            team_id = f"{request.name.lower().replace(' ', '-')}-{str(uuid.uuid4())[:8]}"
            
            team = AgentTeam(
                team_id=team_id,
                name=request.name,
                tenant_id=request.tenant_id,
                team_type=team_type,
                agents=agents,
                description=request.description or ""
            )
            
            # Registrar
            self.active_teams[team_id] = team
            await self._save_teams()
            
            # Retornar status
            status = team.get_status()
            return TeamStatusModel(
                team_id=status['team_id'],
                name=status['name'],
                team_type=status['team_type'],
                tenant_id=status['tenant_id'],
                is_busy=status['is_busy'],
                agent_count=status['agent_count'],
                workflow_name=status['workflow_name'],
                current_execution=status['current_execution'],
                workflows_completed=status['stats']['workflows_completed'],
                workflows_failed=status['stats']['workflows_failed'],
                total_execution_time_ms=status['stats']['total_execution_time_ms'],
                total_tokens_used=status['stats']['total_tokens_used'],
                agents=status['agents']
            )
        
        @self.app.get("/teams/{team_id}", response_model=TeamStatusModel)
        async def get_team(team_id: str):
            """Obtener información de un equipo específico"""
            if team_id not in self.active_teams:
                raise HTTPException(status_code=404, detail="Team not found")
            
            team = self.active_teams[team_id]
            status = team.get_status()
            
            return TeamStatusModel(
                team_id=status['team_id'],
                name=status['name'],
                team_type=status['team_type'],
                tenant_id=status['tenant_id'],
                is_busy=status['is_busy'],
                agent_count=status['agent_count'],
                workflow_name=status['workflow_name'],
                current_execution=status['current_execution'],
                workflows_completed=status['stats']['workflows_completed'],
                workflows_failed=status['stats']['workflows_failed'],
                total_execution_time_ms=status['stats']['total_execution_time_ms'],
                total_tokens_used=status['stats']['total_tokens_used'],
                agents=status['agents']
            )
        
        @self.app.delete("/teams/{team_id}")
        async def delete_team(team_id: str):
            """Eliminar un equipo"""
            if team_id not in self.active_teams:
                raise HTTPException(status_code=404, detail="Team not found")
            
            del self.active_teams[team_id]
            await self._save_teams()
            
            return {"message": f"Team {team_id} deleted successfully"}
        
        @self.app.post("/teams/{team_id}/execute", response_model=TeamExecutionResponse)
        async def execute_workflow(team_id: str, request: TeamWorkflowRequest, background_tasks: BackgroundTasks):
            """Ejecutar workflow de un equipo"""
            if team_id not in self.active_teams:
                raise HTTPException(status_code=404, detail="Team not found")
            
            team = self.active_teams[team_id]
            
            if team.is_busy:
                raise HTTPException(status_code=400, detail="Team is busy")
            
            # Crear respuesta de ejecución
            execution_id = str(uuid.uuid4())
            execution_response = TeamExecutionResponse(
                execution_id=execution_id,
                team_id=team_id,
                workflow_name=team.workflow.name,
                status="running",
                start_time=datetime.now()
            )
            
            self.execution_queue.append(execution_response)
            
            # Ejecutar en background
            background_tasks.add_task(
                self._execute_workflow_background,
                execution_response,
                team,
                request
            )
            
            return execution_response
        
        @self.app.get("/teams/preset/research")
        async def create_preset_research_team(tenant_id: str = "default"):
            """Crear un equipo de investigación predefinido"""
            team = await PresetTeams.create_research_team(tenant_id)
            self.active_teams[team.team_id] = team
            await self._save_teams()
            
            status = team.get_status()
            return TeamStatusModel(
                team_id=status['team_id'],
                name=status['name'],
                team_type=status['team_type'],
                tenant_id=status['tenant_id'],
                is_busy=status['is_busy'],
                agent_count=status['agent_count'],
                workflow_name=status['workflow_name'],
                current_execution=status['current_execution'],
                workflows_completed=status['stats']['workflows_completed'],
                workflows_failed=status['stats']['workflows_failed'],
                total_execution_time_ms=status['stats']['total_execution_time_ms'],
                total_tokens_used=status['stats']['total_tokens_used'],
                agents=status['agents']
            )
        
        @self.app.get("/teams/preset/content")
        async def create_preset_content_team(tenant_id: str = "default"):
            """Crear un equipo de contenido predefinido"""
            team = await PresetTeams.create_content_team(tenant_id)
            self.active_teams[team.team_id] = team
            await self._save_teams()
            
            status = team.get_status()
            return TeamStatusModel(
                team_id=status['team_id'],
                name=status['name'],
                team_type=status['team_type'],
                tenant_id=status['tenant_id'],
                is_busy=status['is_busy'],
                agent_count=status['agent_count'],
                workflow_name=status['workflow_name'],
                current_execution=status['current_execution'],
                workflows_completed=status['stats']['workflows_completed'],
                workflows_failed=status['stats']['workflows_failed'],
                total_execution_time_ms=status['stats']['total_execution_time_ms'],
                total_tokens_used=status['stats']['total_tokens_used'],
                agents=status['agents']
            )
        
        @self.app.get("/executions", response_model=List[TeamExecutionResponse])
        async def list_executions(limit: int = 50, team_id: Optional[str] = None):
            """Listar historial de ejecuciones de workflows"""
            executions = self.execution_history[-limit:]
            
            if team_id:
                executions = [e for e in executions if e.team_id == team_id]
            
            return executions
        
        @self.app.get("/executions/{execution_id}", response_model=TeamExecutionResponse)
        async def get_execution(execution_id: str):
            """Obtener información de una ejecución específica"""
            # Buscar en queue primero
            for execution in self.execution_queue:
                if execution.execution_id == execution_id:
                    return execution
            
            # Buscar en historial
            for execution in self.execution_history:
                if execution.execution_id == execution_id:
                    return execution
            
            raise HTTPException(status_code=404, detail="Execution not found")
    
    async def _execute_workflow_background(
        self,
        execution_response: TeamExecutionResponse,
        team: AgentTeam,
        request: TeamWorkflowRequest
    ):
        """Ejecutar workflow en background"""
        try:
            # Ejecutar workflow del equipo
            result = await team.execute_workflow(request.task, request.context)
            
            # Actualizar respuesta
            execution_response.status = result['status']
            execution_response.end_time = datetime.fromisoformat(result['end_time'])
            execution_response.execution_time_ms = result['execution_time_ms']
            execution_response.total_tokens_used = result['total_tokens_used']
            execution_response.step_results = result['step_results']
            execution_response.final_result = result['final_result']
            
            # Mover de queue a historial
            if execution_response in self.execution_queue:
                self.execution_queue.remove(execution_response)
            self.execution_history.append(execution_response)
            
            await self._save_executions()
            
        except Exception as e:
            execution_response.status = "failed"
            execution_response.error = str(e)
            execution_response.end_time = datetime.now()
            
            if execution_response in self.execution_queue:
                self.execution_queue.remove(execution_response)
            self.execution_history.append(execution_response)
            
            await self._save_executions()


# ========================= STARTUP =========================

def create_agent_team_api_app():
    """Factory function para crear la app"""
    service = AgentTeamAPIService()
    return service.app

# Instancia global para import directo
app = create_agent_team_api_app()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8007, log_level="info") 