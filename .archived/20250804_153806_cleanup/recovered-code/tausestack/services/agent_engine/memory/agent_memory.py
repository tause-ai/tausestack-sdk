"""
Agent Memory - Memoria persistente para agentes multi-tenant
"""

import json
import aiofiles
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path


class AgentMemory:
    """
    Memoria persistente para agentes que usa storage multi-tenant
    """
    
    def __init__(
        self, 
        agent_id: str, 
        tenant_id: str, 
        storage_path: str = ".tausestack_storage"
    ):
        self.agent_id = agent_id
        self.tenant_id = tenant_id
        self.storage_path = Path(storage_path)
        
        # Crear directorio específico para el agente
        self.agent_memory_dir = self.storage_path / "agents" / tenant_id / agent_id
        self.agent_memory_dir.mkdir(parents=True, exist_ok=True)
        
        # Archivos de memoria
        self.interactions_file = self.agent_memory_dir / "interactions.json"
        self.context_file = self.agent_memory_dir / "context.json"
        self.summary_file = self.agent_memory_dir / "summary.json"
        
        # Memoria en caché
        self.interactions_cache: List[Dict[str, Any]] = []
        self.context_cache: Dict[str, Any] = {}
        self.summary_cache: Dict[str, Any] = {}
        
        # Cargar datos existentes
        self._load_memory()
    
    def _load_memory(self):
        """Cargar memoria desde archivos"""
        try:
            # Cargar interacciones
            if self.interactions_file.exists():
                with open(self.interactions_file, 'r') as f:
                    self.interactions_cache = json.load(f)
            
            # Cargar contexto
            if self.context_file.exists():
                with open(self.context_file, 'r') as f:
                    self.context_cache = json.load(f)
            
            # Cargar resumen
            if self.summary_file.exists():
                with open(self.summary_file, 'r') as f:
                    self.summary_cache = json.load(f)
                    
        except Exception as e:
            print(f"Error loading memory for agent {self.agent_id}: {e}")
    
    async def add_interaction(self, task: str, result: Any):
        """Agregar una nueva interacción"""
        interaction = {
            'timestamp': datetime.now().isoformat(),
            'task': task,
            'result': result,
            'metadata': {
                'tenant_id': self.tenant_id,
                'agent_id': self.agent_id
            }
        }
        
        self.interactions_cache.append(interaction)
        
        # Mantener solo las últimas 100 interacciones
        if len(self.interactions_cache) > 100:
            self.interactions_cache = self.interactions_cache[-100:]
        
        # Guardar en archivo
        await self._save_interactions()
        
        # Actualizar contexto relevante
        await self._update_context(task, result)
    
    async def get_relevant_context(self, task: str) -> str:
        """Obtener contexto relevante para una tarea"""
        # Buscar interacciones similares
        relevant_interactions = []
        
        for interaction in self.interactions_cache[-10:]:  # Últimas 10 interacciones
            if self._is_relevant(task, interaction['task']):
                relevant_interactions.append(interaction)
        
        if not relevant_interactions:
            return ""
        
        # Construir contexto
        context_parts = []
        for interaction in relevant_interactions:
            context_parts.append(
                f"Previous Task: {interaction['task']}\n"
                f"Result: {interaction['result']}\n"
                f"---"
            )
        
        return "\n".join(context_parts)
    
    def _is_relevant(self, current_task: str, previous_task: str) -> bool:
        """Determinar si una tarea anterior es relevante"""
        # Lógica simple de relevancia basada en palabras clave
        current_words = set(current_task.lower().split())
        previous_words = set(previous_task.lower().split())
        
        # Si comparten al menos 2 palabras, es relevante
        common_words = current_words.intersection(previous_words)
        return len(common_words) >= 2
    
    async def _update_context(self, task: str, result: Any):
        """Actualizar contexto basado en nueva interacción"""
        # Extraer información clave
        task_type = self._classify_task(task)
        
        if task_type not in self.context_cache:
            self.context_cache[task_type] = []
        
        self.context_cache[task_type].append({
            'task': task,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
        
        # Mantener solo los últimos 20 por tipo
        if len(self.context_cache[task_type]) > 20:
            self.context_cache[task_type] = self.context_cache[task_type][-20:]
        
        await self._save_context()
    
    def _classify_task(self, task: str) -> str:
        """Clasificar tipo de tarea"""
        task_lower = task.lower()
        
        if any(word in task_lower for word in ['write', 'create', 'generate', 'draft']):
            return 'writing'
        elif any(word in task_lower for word in ['analyze', 'research', 'study', 'investigate']):
            return 'analysis'
        elif any(word in task_lower for word in ['help', 'support', 'assist', 'solve']):
            return 'support'
        elif any(word in task_lower for word in ['product', 'order', 'payment', 'shop']):
            return 'ecommerce'
        else:
            return 'general'
    
    async def _save_interactions(self):
        """Guardar interacciones en archivo"""
        try:
            async with aiofiles.open(self.interactions_file, 'w') as f:
                await f.write(json.dumps(self.interactions_cache, indent=2))
        except Exception as e:
            print(f"Error saving interactions: {e}")
    
    async def _save_context(self):
        """Guardar contexto en archivo"""
        try:
            async with aiofiles.open(self.context_file, 'w') as f:
                await f.write(json.dumps(self.context_cache, indent=2))
        except Exception as e:
            print(f"Error saving context: {e}")
    
    async def _save_summary(self):
        """Guardar resumen en archivo"""
        try:
            async with aiofiles.open(self.summary_file, 'w') as f:
                await f.write(json.dumps(self.summary_cache, indent=2))
        except Exception as e:
            print(f"Error saving summary: {e}")
    
    async def get_size(self) -> int:
        """Obtener tamaño de la memoria"""
        return len(self.interactions_cache)
    
    async def get_last_activity(self) -> Optional[str]:
        """Obtener última actividad"""
        if self.interactions_cache:
            return self.interactions_cache[-1]['timestamp']
        return None
    
    async def clear(self):
        """Limpiar toda la memoria"""
        self.interactions_cache = []
        self.context_cache = {}
        self.summary_cache = {}
        
        # Eliminar archivos
        for file in [self.interactions_file, self.context_file, self.summary_file]:
            if file.exists():
                file.unlink()
    
    async def get_summary(self) -> Dict[str, Any]:
        """Obtener resumen de la memoria"""
        summary = {
            'agent_id': self.agent_id,
            'tenant_id': self.tenant_id,
            'total_interactions': len(self.interactions_cache),
            'context_types': list(self.context_cache.keys()),
            'last_activity': await self.get_last_activity(),
            'memory_size_mb': self._calculate_memory_size()
        }
        
        # Agregar estadísticas por tipo de tarea
        task_stats = {}
        for interaction in self.interactions_cache:
            task_type = self._classify_task(interaction['task'])
            if task_type not in task_stats:
                task_stats[task_type] = 0
            task_stats[task_type] += 1
        
        summary['task_statistics'] = task_stats
        return summary
    
    def _calculate_memory_size(self) -> float:
        """Calcular tamaño aproximado de la memoria en MB"""
        total_size = 0
        
        # Tamaño de interacciones
        interactions_str = json.dumps(self.interactions_cache)
        total_size += len(interactions_str.encode('utf-8'))
        
        # Tamaño de contexto
        context_str = json.dumps(self.context_cache)
        total_size += len(context_str.encode('utf-8'))
        
        # Convertir a MB
        return round(total_size / (1024 * 1024), 2) 