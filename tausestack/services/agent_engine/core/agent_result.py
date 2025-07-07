"""
Agent Result - Resultados y métricas de la ejecución de agentes
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    """Estados de las tareas"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentMetrics:
    """Métricas de ejecución del agente"""
    execution_time_ms: int
    tokens_used: int
    api_calls: int
    model_used: str
    cost_estimate: float = 0.0
    memory_used_mb: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'execution_time_ms': self.execution_time_ms,
            'tokens_used': self.tokens_used,
            'api_calls': self.api_calls,
            'model_used': self.model_used,
            'cost_estimate': self.cost_estimate,
            'memory_used_mb': self.memory_used_mb
        }


@dataclass
class AgentResult:
    """
    Resultado de la ejecución de un agente
    """
    task_id: str
    agent_id: str
    tenant_id: str
    status: TaskStatus
    result: Any
    error_message: Optional[str] = None
    metrics: Optional[AgentMetrics] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    intermediate_results: List[Any] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario para serialización"""
        return {
            'task_id': self.task_id,
            'agent_id': self.agent_id,
            'tenant_id': self.tenant_id,
            'status': self.status.value,
            'result': self.result,
            'error_message': self.error_message,
            'metrics': self.metrics.to_dict() if self.metrics else None,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'intermediate_results': self.intermediate_results,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentResult':
        """Crear desde diccionario"""
        metrics = None
        if data.get('metrics'):
            metrics = AgentMetrics(**data['metrics'])
        
        return cls(
            task_id=data['task_id'],
            agent_id=data['agent_id'],
            tenant_id=data['tenant_id'],
            status=TaskStatus(data['status']),
            result=data['result'],
            error_message=data.get('error_message'),
            metrics=metrics,
            created_at=datetime.fromisoformat(data['created_at']),
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None,
            intermediate_results=data.get('intermediate_results', []),
            metadata=data.get('metadata', {})
        )
    
    def mark_completed(self, result: Any, metrics: Optional[AgentMetrics] = None):
        """Marcar como completado"""
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.completed_at = datetime.now()
        if metrics:
            self.metrics = metrics
    
    def mark_failed(self, error_message: str):
        """Marcar como fallido"""
        self.status = TaskStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.now()
    
    def add_intermediate_result(self, result: Any):
        """Agregar resultado intermedio"""
        self.intermediate_results.append({
            'timestamp': datetime.now().isoformat(),
            'result': result
        })
    
    def get_duration_ms(self) -> Optional[int]:
        """Obtener duración en milisegundos"""
        if self.completed_at:
            return int((self.completed_at - self.created_at).total_seconds() * 1000)
        return None
    
    def is_successful(self) -> bool:
        """Verificar si la ejecución fue exitosa"""
        return self.status == TaskStatus.COMPLETED and self.error_message is None 