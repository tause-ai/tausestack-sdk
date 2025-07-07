#!/usr/bin/env python3
"""
Analytics Service - Multi-Tenant API
TauseStack v0.5.0

Servicio de analytics con aislamiento completo por tenant.
Implementa:
- Métricas aisladas por tenant
- Dashboards personalizados
- Reportes en tiempo real
- Event tracking
- Agregaciones eficientes
- Cache distribuido
"""

from fastapi import FastAPI, HTTPException, Header, Query, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json
import os
import logging
from contextlib import asynccontextmanager

# Configuración de logging estructurado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("analytics-service")

# --- Modelos de datos ---

class EventType(str, Enum):
    """Tipos de eventos trackeable."""
    PAGE_VIEW = "page_view"
    USER_ACTION = "user_action"
    API_CALL = "api_call"
    ERROR = "error"
    CONVERSION = "conversion"
    CUSTOM = "custom"

class MetricType(str, Enum):
    """Tipos de métricas."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

class TimeRange(str, Enum):
    """Rangos de tiempo para consultas."""
    HOUR = "1h"
    DAY = "1d"
    WEEK = "1w"
    MONTH = "1m"
    QUARTER = "3m"
    YEAR = "1y"

class AnalyticsEvent(BaseModel):
    """Evento de analytics."""
    event_id: Optional[str] = None
    tenant_id: Optional[str] = None
    event_type: EventType
    timestamp: Optional[datetime] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class MetricDefinition(BaseModel):
    """Definición de métrica personalizada."""
    metric_id: str
    name: str
    description: Optional[str] = None
    metric_type: MetricType
    tenant_id: Optional[str] = None
    dimensions: List[str] = Field(default_factory=list)
    aggregations: List[str] = Field(default_factory=lambda: ["count", "sum"])
    retention_days: int = Field(default=90)

class DashboardConfig(BaseModel):
    """Configuración de dashboard por tenant."""
    dashboard_id: str
    name: str
    description: Optional[str] = None
    tenant_id: Optional[str] = None
    widgets: List[Dict[str, Any]] = Field(default_factory=list)
    layout: Dict[str, Any] = Field(default_factory=dict)
    refresh_interval: int = Field(default=300)  # segundos
    is_public: bool = Field(default=False)

class QueryRequest(BaseModel):
    """Request para consultas de analytics."""
    metric_ids: List[str]
    time_range: TimeRange
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    filters: Dict[str, Any] = Field(default_factory=dict)
    group_by: List[str] = Field(default_factory=list)
    aggregations: List[str] = Field(default_factory=lambda: ["count"])

class TenantAnalyticsConfig(BaseModel):
    """Configuración de analytics por tenant."""
    tenant_id: str
    name: str
    data_retention_days: int = Field(default=90)
    sampling_rate: float = Field(default=1.0, ge=0.0, le=1.0)
    custom_dimensions: List[str] = Field(default_factory=list)
    alert_thresholds: Dict[str, float] = Field(default_factory=dict)
    export_enabled: bool = Field(default=True)
    real_time_enabled: bool = Field(default=True)

# --- Storage multi-tenant simulado ---

class TenantAnalyticsStorage:
    """Storage de analytics aislado por tenant."""
    
    def __init__(self):
        # Simulación de storage distribuido
        self.tenant_events: Dict[str, List[Dict[str, Any]]] = {}
        self.tenant_metrics: Dict[str, Dict[str, MetricDefinition]] = {}
        self.tenant_dashboards: Dict[str, Dict[str, DashboardConfig]] = {}
        self.tenant_configs: Dict[str, TenantAnalyticsConfig] = {}
        self.tenant_aggregations: Dict[str, Dict[str, Any]] = {}
    
    def get_tenant_events(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Obtener eventos del tenant."""
        if tenant_id not in self.tenant_events:
            self.tenant_events[tenant_id] = []
        return self.tenant_events[tenant_id]
    
    def get_tenant_metrics(self, tenant_id: str) -> Dict[str, MetricDefinition]:
        """Obtener métricas del tenant."""
        if tenant_id not in self.tenant_metrics:
            self.tenant_metrics[tenant_id] = {}
        return self.tenant_metrics[tenant_id]
    
    def get_tenant_dashboards(self, tenant_id: str) -> Dict[str, DashboardConfig]:
        """Obtener dashboards del tenant."""
        if tenant_id not in self.tenant_dashboards:
            self.tenant_dashboards[tenant_id] = {}
        return self.tenant_dashboards[tenant_id]
    
    async def store_event(self, tenant_id: str, event: Dict[str, Any]) -> bool:
        """Almacenar evento de forma asíncrona."""
        events = self.get_tenant_events(tenant_id)
        events.append(event)
        
        # Simular límites de retención
        config = self.tenant_configs.get(tenant_id)
        if config and len(events) > 10000:  # Límite simulado
            # Mantener solo los eventos más recientes
            events[:] = events[-5000:]
        
        # Actualizar agregaciones en background
        await self._update_aggregations(tenant_id, event)
        return True
    
    async def _update_aggregations(self, tenant_id: str, event: Dict[str, Any]):
        """Actualizar agregaciones en tiempo real."""
        if tenant_id not in self.tenant_aggregations:
            self.tenant_aggregations[tenant_id] = {
                "hourly": {},
                "daily": {},
                "total_events": 0,
                "unique_users": set(),
                "event_types": {}
            }
        
        agg = self.tenant_aggregations[tenant_id]
        agg["total_events"] += 1
        
        # Trackear usuarios únicos
        if event.get("user_id"):
            agg["unique_users"].add(event["user_id"])
        
        # Contar por tipo de evento
        event_type = event.get("event_type", "unknown")
        agg["event_types"][event_type] = agg["event_types"].get(event_type, 0) + 1

# Storage global
analytics_storage = TenantAnalyticsStorage()

# --- Helpers multi-tenant ---

def get_tenant_id_from_request(
    tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
    tenant_query: Optional[str] = Query(None, alias="tenant_id")
) -> str:
    """Extraer tenant ID del request."""
    effective_tenant = tenant_id or tenant_query or "default"
    return effective_tenant

def is_multi_tenant_enabled() -> bool:
    """Verificar si el modo multi-tenant está habilitado."""
    return os.getenv("TAUSESTACK_MULTI_TENANT_MODE", "false").lower() == "true"

async def validate_tenant_access(tenant_id: str) -> bool:
    """Validar acceso del tenant (simulado)."""
    # En producción, esto consultaría un servicio de autenticación
    return tenant_id in ["default", "cliente_premium", "cliente_basico", "cliente_enterprise"]

# --- Lifespan management ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida del servicio."""
    logger.info("🚀 Analytics Service iniciando...")
    
    # Inicializar configuraciones por defecto
    await initialize_default_configs()
    
    # Inicializar cache distribuido (simulado)
    logger.info("📊 Cache distribuido inicializado")
    
    yield
    
    logger.info("🛑 Analytics Service cerrando...")

async def initialize_default_configs():
    """Inicializar configuraciones por defecto."""
    default_tenants = ["cliente_premium", "cliente_basico", "cliente_enterprise"]
    
    for tenant_id in default_tenants:
        if tenant_id not in analytics_storage.tenant_configs:
            config = TenantAnalyticsConfig(
                tenant_id=tenant_id,
                name=f"Analytics Config for {tenant_id}",
                data_retention_days=90 if tenant_id != "cliente_enterprise" else 365,
                sampling_rate=1.0 if tenant_id == "cliente_premium" else 0.8,
                real_time_enabled=True
            )
            analytics_storage.tenant_configs[tenant_id] = config

# --- FastAPI App ---

app = FastAPI(
    title="Analytics Service - Multi-Tenant",
    description="Servicio de analytics con aislamiento completo por tenant",
    version="0.6.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# --- Middleware ---

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # En producción, especificar hosts permitidos
)

# --- Endpoints de configuración ---

@app.post("/config/tenant", response_model=TenantAnalyticsConfig)
async def configure_tenant_analytics(
    config: TenantAnalyticsConfig,
    tenant_id: str = Depends(get_tenant_id_from_request)
):
    """Configurar analytics para un tenant."""
    if not await validate_tenant_access(tenant_id):
        raise HTTPException(status_code=403, detail="Acceso denegado al tenant")
    
    config.tenant_id = tenant_id
    analytics_storage.tenant_configs[tenant_id] = config
    
    logger.info(f"📊 Configuración actualizada para tenant {tenant_id}")
    return config

@app.get("/config/tenant", response_model=TenantAnalyticsConfig)
async def get_tenant_analytics_config(
    tenant_id: str = Depends(get_tenant_id_from_request)
):
    """Obtener configuración de analytics del tenant."""
    if not await validate_tenant_access(tenant_id):
        raise HTTPException(status_code=403, detail="Acceso denegado al tenant")
    
    config = analytics_storage.tenant_configs.get(tenant_id)
    if not config:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    
    return config

# --- Endpoints de tracking de eventos ---

@app.post("/events/track")
async def track_event(
    event: AnalyticsEvent,
    background_tasks: BackgroundTasks,
    tenant_id: str = Depends(get_tenant_id_from_request)
):
    """Trackear evento de analytics."""
    if not await validate_tenant_access(tenant_id):
        raise HTTPException(status_code=403, detail="Acceso denegado al tenant")
    
    # Asignar tenant y timestamp
    event.tenant_id = tenant_id
    if not event.timestamp:
        event.timestamp = datetime.utcnow()
    
    # Generar ID único
    if not event.event_id:
        event.event_id = f"{tenant_id}_{event.timestamp.isoformat()}_{hash(str(event.properties))}"
    
    # Verificar sampling rate
    config = analytics_storage.tenant_configs.get(tenant_id)
    if config and config.sampling_rate < 1.0:
        import random
        if random.random() > config.sampling_rate:
            return {"status": "sampled_out", "event_id": event.event_id}
    
    # Almacenar evento en background
    background_tasks.add_task(
        analytics_storage.store_event,
        tenant_id,
        event.dict()
    )
    
    logger.info(f"📈 Evento trackeado: {event.event_type} para tenant {tenant_id}")
    return {"status": "tracked", "event_id": event.event_id}

@app.post("/events/batch")
async def track_events_batch(
    events: List[AnalyticsEvent],
    background_tasks: BackgroundTasks,
    tenant_id: str = Depends(get_tenant_id_from_request)
):
    """Trackear múltiples eventos en batch."""
    if not await validate_tenant_access(tenant_id):
        raise HTTPException(status_code=403, detail="Acceso denegado al tenant")
    
    if len(events) > 1000:  # Límite de batch
        raise HTTPException(status_code=413, detail="Batch demasiado grande (máximo 1000 eventos)")
    
    processed_events = []
    
    for event in events:
        event.tenant_id = tenant_id
        if not event.timestamp:
            event.timestamp = datetime.utcnow()
        if not event.event_id:
            event.event_id = f"{tenant_id}_{event.timestamp.isoformat()}_{hash(str(event.properties))}"
        
        processed_events.append(event.dict())
    
    # Procesar batch en background
    background_tasks.add_task(
        process_events_batch,
        tenant_id,
        processed_events
    )
    
    logger.info(f"📊 Batch de {len(events)} eventos procesado para tenant {tenant_id}")
    return {"status": "batch_processed", "events_count": len(events)}

async def process_events_batch(tenant_id: str, events: List[Dict[str, Any]]):
    """Procesar batch de eventos de forma asíncrona."""
    for event in events:
        await analytics_storage.store_event(tenant_id, event)

# --- Endpoints de métricas ---

@app.post("/metrics/define", response_model=MetricDefinition)
async def define_metric(
    metric: MetricDefinition,
    tenant_id: str = Depends(get_tenant_id_from_request)
):
    """Definir métrica personalizada para el tenant."""
    if not await validate_tenant_access(tenant_id):
        raise HTTPException(status_code=403, detail="Acceso denegado al tenant")
    
    metric.tenant_id = tenant_id
    metrics = analytics_storage.get_tenant_metrics(tenant_id)
    metrics[metric.metric_id] = metric
    
    logger.info(f"📏 Métrica definida: {metric.name} para tenant {tenant_id}")
    return metric

@app.get("/metrics", response_model=List[MetricDefinition])
async def list_metrics(
    tenant_id: str = Depends(get_tenant_id_from_request)
):
    """Listar métricas del tenant."""
    if not await validate_tenant_access(tenant_id):
        raise HTTPException(status_code=403, detail="Acceso denegado al tenant")
    
    metrics = analytics_storage.get_tenant_metrics(tenant_id)
    return list(metrics.values())

@app.post("/metrics/query")
async def query_metrics(
    query: QueryRequest,
    tenant_id: str = Depends(get_tenant_id_from_request)
):
    """Consultar métricas con agregaciones."""
    if not await validate_tenant_access(tenant_id):
        raise HTTPException(status_code=403, detail="Acceso denegado al tenant")
    
    # Obtener eventos del tenant
    events = analytics_storage.get_tenant_events(tenant_id)
    
    # Filtrar por tiempo
    filtered_events = filter_events_by_time(events, query.time_range, query.start_time, query.end_time)
    
    # Aplicar filtros adicionales
    if query.filters:
        filtered_events = [e for e in filtered_events if matches_filters(e, query.filters)]
    
    # Calcular agregaciones
    results = calculate_aggregations(filtered_events, query.aggregations, query.group_by)
    
    logger.info(f"📊 Query ejecutada para tenant {tenant_id}: {len(filtered_events)} eventos")
    return {
        "tenant_id": tenant_id,
        "query": query.dict(),
        "events_count": len(filtered_events),
        "results": results,
        "timestamp": datetime.utcnow().isoformat()
    }

def filter_events_by_time(events: List[Dict], time_range: TimeRange, start_time: Optional[datetime], end_time: Optional[datetime]) -> List[Dict]:
    """Filtrar eventos por rango de tiempo."""
    now = datetime.utcnow()
    
    if start_time and end_time:
        start = start_time
        end = end_time
    else:
        # Calcular rango basado en time_range
        if time_range == TimeRange.HOUR:
            start = now - timedelta(hours=1)
        elif time_range == TimeRange.DAY:
            start = now - timedelta(days=1)
        elif time_range == TimeRange.WEEK:
            start = now - timedelta(weeks=1)
        elif time_range == TimeRange.MONTH:
            start = now - timedelta(days=30)
        elif time_range == TimeRange.QUARTER:
            start = now - timedelta(days=90)
        else:  # YEAR
            start = now - timedelta(days=365)
        end = now
    
    return [
        e for e in events 
        if start <= datetime.fromisoformat(e.get("timestamp", "1970-01-01T00:00:00")) <= end
    ]

def matches_filters(event: Dict, filters: Dict[str, Any]) -> bool:
    """Verificar si evento coincide con filtros."""
    for key, value in filters.items():
        if key in event:
            if isinstance(value, list):
                if event[key] not in value:
                    return False
            elif event[key] != value:
                return False
        elif key in event.get("properties", {}):
            if event["properties"][key] != value:
                return False
        else:
            return False
    return True

def calculate_aggregations(events: List[Dict], aggregations: List[str], group_by: List[str]) -> Dict[str, Any]:
    """Calcular agregaciones sobre eventos."""
    if not group_by:
        # Agregación simple
        result = {}
        for agg in aggregations:
            if agg == "count":
                result["count"] = len(events)
            elif agg == "unique_users":
                result["unique_users"] = len(set(e.get("user_id") for e in events if e.get("user_id")))
            elif agg == "unique_sessions":
                result["unique_sessions"] = len(set(e.get("session_id") for e in events if e.get("session_id")))
        return result
    else:
        # Agregación agrupada
        grouped = {}
        for event in events:
            group_key = tuple(str(event.get(field, "unknown")) for field in group_by)
            if group_key not in grouped:
                grouped[group_key] = []
            grouped[group_key].append(event)
        
        results = {}
        for group_key, group_events in grouped.items():
            group_name = "_".join(group_key)
            results[group_name] = {}
            for agg in aggregations:
                if agg == "count":
                    results[group_name]["count"] = len(group_events)
                elif agg == "unique_users":
                    results[group_name]["unique_users"] = len(set(e.get("user_id") for e in group_events if e.get("user_id")))
        
        return results

# --- Endpoints de dashboards ---

@app.post("/dashboards", response_model=DashboardConfig)
async def create_dashboard(
    dashboard: DashboardConfig,
    tenant_id: str = Depends(get_tenant_id_from_request)
):
    """Crear dashboard personalizado."""
    if not await validate_tenant_access(tenant_id):
        raise HTTPException(status_code=403, detail="Acceso denegado al tenant")
    
    dashboard.tenant_id = tenant_id
    dashboards = analytics_storage.get_tenant_dashboards(tenant_id)
    dashboards[dashboard.dashboard_id] = dashboard
    
    logger.info(f"📊 Dashboard creado: {dashboard.name} para tenant {tenant_id}")
    return dashboard

@app.get("/dashboards", response_model=List[DashboardConfig])
async def list_dashboards(
    tenant_id: str = Depends(get_tenant_id_from_request)
):
    """Listar dashboards del tenant."""
    if not await validate_tenant_access(tenant_id):
        raise HTTPException(status_code=403, detail="Acceso denegado al tenant")
    
    dashboards = analytics_storage.get_tenant_dashboards(tenant_id)
    return list(dashboards.values())

@app.get("/dashboards/{dashboard_id}", response_model=DashboardConfig)
async def get_dashboard(
    dashboard_id: str,
    tenant_id: str = Depends(get_tenant_id_from_request)
):
    """Obtener dashboard específico."""
    if not await validate_tenant_access(tenant_id):
        raise HTTPException(status_code=403, detail="Acceso denegado al tenant")
    
    dashboards = analytics_storage.get_tenant_dashboards(tenant_id)
    dashboard = dashboards.get(dashboard_id)
    
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard no encontrado")
    
    return dashboard

# --- Endpoints de estadísticas en tiempo real ---

@app.get("/realtime/stats")
async def get_realtime_stats(
    tenant_id: str = Depends(get_tenant_id_from_request)
):
    """Obtener estadísticas en tiempo real del tenant."""
    if not await validate_tenant_access(tenant_id):
        raise HTTPException(status_code=403, detail="Acceso denegado al tenant")
    
    aggregations = analytics_storage.tenant_aggregations.get(tenant_id, {})
    events = analytics_storage.get_tenant_events(tenant_id)
    
    # Calcular métricas en tiempo real
    now = datetime.utcnow()
    last_hour_events = [
        e for e in events
        if (now - datetime.fromisoformat(e.get("timestamp", "1970-01-01T00:00:00"))).total_seconds() < 3600
    ]
    
    return {
        "tenant_id": tenant_id,
        "timestamp": now.isoformat(),
        "total_events": aggregations.get("total_events", 0),
        "unique_users": len(aggregations.get("unique_users", set())),
        "event_types": aggregations.get("event_types", {}),
        "last_hour_events": len(last_hour_events),
        "events_per_minute": len(last_hour_events) / 60 if last_hour_events else 0
    }

# --- Health check ---

@app.get("/health")
async def health_check():
    """Health check del servicio."""
    return {
        "status": "healthy",
        "service": "analytics-mt",
        "version": "0.6.0",
        "timestamp": datetime.utcnow().isoformat(),
        "multi_tenant_enabled": is_multi_tenant_enabled(),
        "tenants_configured": len(analytics_storage.tenant_configs)
    }

# --- Endpoint de métricas para monitoreo ---

@app.get("/metrics/prometheus")
async def prometheus_metrics():
    """Métricas en formato Prometheus para monitoreo."""
    metrics = []
    
    for tenant_id, aggregations in analytics_storage.tenant_aggregations.items():
        total_events = aggregations.get("total_events", 0)
        unique_users = len(aggregations.get("unique_users", set()))
        
        metrics.append(f'analytics_total_events{{tenant="{tenant_id}"}} {total_events}')
        metrics.append(f'analytics_unique_users{{tenant="{tenant_id}"}} {unique_users}')
        
        for event_type, count in aggregations.get("event_types", {}).items():
            metrics.append(f'analytics_events_by_type{{tenant="{tenant_id}",type="{event_type}"}} {count}')
    
    return "\n".join(metrics)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    ) 