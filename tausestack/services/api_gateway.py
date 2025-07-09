#!/usr/bin/env python3
"""
API Gateway - TauseStack v0.6.0
Gateway unificado para todos los servicios multi-tenant
"""

from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import httpx
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import os
from collections import defaultdict
import time
import logging

# Importar configuración centralizada
try:
    from tausestack.config.settings import settings
except ImportError:
    # Fallback para desarrollo
    class MockSettings:
        ANALYTICS_SERVICE_URL = "http://localhost:8001"
        COMMUNICATIONS_SERVICE_URL = "http://localhost:8002"
        BILLING_SERVICE_URL = "http://localhost:8003"
        MCP_SERVER_URL = "http://localhost:8000"
        AI_SERVICES_URL = "http://localhost:8005"
        API_GATEWAY_URL = "http://localhost:9001"
        CORS_ORIGINS = ["https://tausestack.dev", "http://localhost:3000", "http://localhost:9001"]
        CORS_CREDENTIALS = True
        RATE_LIMIT_PER_MINUTE = 100
    
    settings = MockSettings()

# Importar sistema de autenticación con Supabase
from tausestack.sdk.auth.main import require_user, get_current_user
from tausestack.sdk.auth.base import User

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de servicios usando configuración centralizada
SERVICES_CONFIG = {
    "analytics": {
        "url": settings.ANALYTICS_SERVICE_URL,
        "health_endpoint": "/health",
        "rate_limit": 1000,  # requests per hour per tenant
        "timeout": 30
    },
    "communications": {
        "url": settings.COMMUNICATIONS_SERVICE_URL, 
        "health_endpoint": "/health",
        "rate_limit": 500,
        "timeout": 30
    },
    "billing": {
        "url": settings.BILLING_SERVICE_URL,
        "health_endpoint": "/health", 
        "rate_limit": 200,
        "timeout": 30
    },
    "templates": {
        "url": "http://localhost:8004",
        "health_endpoint": "/health",
        "rate_limit": 100,
        "timeout": 30
    },
    "ai_services": {
        "url": settings.AI_SERVICES_URL,
        "health_endpoint": "/health",
        "rate_limit": 100,
        "timeout": 30
    },
    "builder_api": {
        "url": "http://localhost:8006",
        "health_endpoint": "/health",
        "rate_limit": 100,
        "timeout": 30
    },
    "team_api": {
        "url": "http://localhost:8007",
        "health_endpoint": "/health",
        "rate_limit": 100,
        "timeout": 30
    },
    "admin_api": {
        "url": "http://localhost:8008",  # Admin API en puerto propio
        "health_endpoint": "/health",
        "rate_limit": 100,
        "timeout": 30
    }
}

# Rate limiting storage
rate_limit_storage = defaultdict(lambda: defaultdict(list))

# Métricas globales
gateway_metrics = {
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "avg_response_time": 0,
    "services_health": {},
    "tenant_usage": defaultdict(int),
    "start_time": datetime.utcnow()
}

app = FastAPI(
    title="TauseStack API Gateway",
    description="Gateway unificado para servicios multi-tenant",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["tausestack.dev", "localhost", "127.0.0.1"]  # Hosts permitidos
)

class RateLimitExceeded(Exception):
    pass

class ServiceUnavailable(Exception):
    pass

def get_tenant_id(request: Request) -> str:
    """Extrae el tenant_id del request."""
    tenant_id = request.headers.get("X-Tenant-ID")
    if not tenant_id:
        # Fallback a query parameter
        tenant_id = request.query_params.get("tenant_id")
    if not tenant_id:
        tenant_id = "default"
    return tenant_id

def check_rate_limit(tenant_id: str, service: str) -> bool:
    """Verifica rate limiting por tenant y servicio."""
    if service not in SERVICES_CONFIG:
        return False
    
    # Deshabilitar rate limiting para health checks en desarrollo
    if os.getenv("ENVIRONMENT") == "development":
        return True
    
    limit = SERVICES_CONFIG[service]["rate_limit"]
    now = time.time()
    hour_ago = now - 3600
    
    # Limpiar requests antiguos
    rate_limit_storage[tenant_id][service] = [
        timestamp for timestamp in rate_limit_storage[tenant_id][service] 
        if timestamp > hour_ago
    ]
    
    # Verificar límite
    if len(rate_limit_storage[tenant_id][service]) >= limit:
        return False
    
    # Registrar request
    rate_limit_storage[tenant_id][service].append(now)
    return True

async def forward_request(
    service: str, 
    path: str, 
    method: str, 
    headers: Dict[str, str], 
    body: Optional[bytes] = None,
    params: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Reenvía request al servicio correspondiente."""
    if service not in SERVICES_CONFIG:
        raise HTTPException(status_code=404, detail=f"Service {service} not found")
    
    service_config = SERVICES_CONFIG[service]
    url = f"{service_config['url']}{path}"
    timeout = service_config["timeout"]
    
    # Preparar headers
    forward_headers = {k: v for k, v in headers.items() if k.lower() not in ['host', 'content-length']}
    
    start_time = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            if method.upper() == "GET":
                response = await client.get(url, headers=forward_headers, params=params)
            elif method.upper() == "POST":
                response = await client.post(url, headers=forward_headers, content=body, params=params)
            elif method.upper() == "PUT":
                response = await client.put(url, headers=forward_headers, content=body, params=params)
            elif method.upper() == "DELETE":
                response = await client.delete(url, headers=forward_headers, params=params)
            elif method.upper() == "PATCH":
                response = await client.patch(url, headers=forward_headers, content=body, params=params)
            else:
                raise HTTPException(status_code=405, detail="Method not allowed")
            
            response_time = time.time() - start_time
            
            # Actualizar métricas
            gateway_metrics["total_requests"] += 1
            if response.status_code < 400:
                gateway_metrics["successful_requests"] += 1
            else:
                gateway_metrics["failed_requests"] += 1
            
            # Actualizar tiempo promedio de respuesta
            current_avg = gateway_metrics["avg_response_time"]
            total_requests = gateway_metrics["total_requests"]
            gateway_metrics["avg_response_time"] = (current_avg * (total_requests - 1) + response_time) / total_requests
            
            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content": response.content,
                "response_time": response_time
            }
            
    except httpx.TimeoutException:
        gateway_metrics["failed_requests"] += 1
        raise HTTPException(status_code=504, detail=f"Service {service} timeout")
    except httpx.ConnectError:
        gateway_metrics["failed_requests"] += 1
        raise HTTPException(status_code=503, detail=f"Service {service} unavailable")
    except Exception as e:
        gateway_metrics["failed_requests"] += 1
        logger.error(f"Error forwarding to {service}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal gateway error")

async def log_real_event(tenant_id: str, event_type: str, event_data: Dict[str, Any]):
    """Log eventos reales a analytics service"""
    try:
        if tenant_id == "tause.pro":  # Solo para datos reales
            async with httpx.AsyncClient(timeout=2.0) as client:
                event_payload = {
                    "event_type": event_type,
                    "timestamp": datetime.utcnow().isoformat(),
                    "properties": event_data,
                    "user_id": "system",
                    "session_id": "api_gateway"
                }
                
                await client.post(
                    "http://localhost:8001/events/track",
                    json=event_payload,
                    headers={"X-Tenant-ID": tenant_id}
                )
    except Exception as e:
        # No fallar si analytics no está disponible
        pass

@app.middleware("http")
async def gateway_middleware(request: Request, call_next):
    """Middleware principal del gateway."""
    start_time = time.time()
    
    # Extraer tenant_id
    tenant_id = get_tenant_id(request)
    
    # Actualizar métricas de tenant
    gateway_metrics["tenant_usage"][tenant_id] += 1
    
    response = await call_next(request)
    
    # Agregar headers de respuesta
    response.headers["X-Gateway-Version"] = "1.0.0"
    response.headers["X-Tenant-ID"] = tenant_id
    response.headers["X-Response-Time"] = str(time.time() - start_time)
    
    return response

@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    """Middleware para loggear requests reales"""
    start_time = datetime.utcnow()
    
    # Procesar request
    response = await call_next(request)
    
    # Calcular tiempo de respuesta
    end_time = datetime.utcnow()
    response_time = (end_time - start_time).total_seconds() * 1000  # en ms
    
    # Loggear evento real para tause.pro
    event_data = {
        "method": request.method,
        "path": str(request.url.path),
        "status_code": response.status_code,
        "response_time_ms": response_time,
        "user_agent": request.headers.get("user-agent", ""),
        "ip_address": request.client.host if request.client else "unknown"
    }
    
    # Registrar evento en analytics (async, no bloquear respuesta)
    asyncio.create_task(log_real_event("tause.pro", "api_call", event_data))
    
    return response

# === RUTAS DEL GATEWAY ===

@app.get("/api")
async def gateway_root():
    """Información del gateway con links al dashboard."""
    return {
        "service": "TauseStack API Gateway",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "services": list(SERVICES_CONFIG.keys()),
        "dashboard": "/",
        "documentation": "/docs"
    }

@app.get("/health")
async def gateway_health():
    """Health check del gateway y servicios. Siempre devuelve healthy para que ALB no falle."""
    services_health = {}
    healthy_services = 0
    
    # Verificar salud de cada servicio (solo servicios core)
    core_services = ["analytics", "communications", "billing", "templates", "ai_services", "builder_api", "team_api"]
    
    for service_name in core_services:
        if service_name in SERVICES_CONFIG:
            config = SERVICES_CONFIG[service_name]
            try:
                async with httpx.AsyncClient(timeout=3) as client:
                    response = await client.get(f"{config['url']}{config['health_endpoint']}")
                    if response.status_code == 200:
                        services_health[service_name] = {
                            "status": "healthy",
                            "response_time": response.elapsed.total_seconds() if response.elapsed else 0,
                            "last_check": datetime.utcnow().isoformat()
                        }
                        healthy_services += 1
                    else:
                        services_health[service_name] = {
                            "status": "unhealthy",
                            "status_code": response.status_code,
                            "last_check": datetime.utcnow().isoformat()
                        }
            except Exception as e:
                services_health[service_name] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "last_check": datetime.utcnow().isoformat()
                }
    
    gateway_metrics["services_health"] = services_health
    
    # Gateway siempre healthy si al menos está corriendo
    # No fallar el health check aunque algunos servicios estén down
    
    return {
        "gateway": {
            "status": "healthy",  # Siempre healthy para que ALB no falle
            "version": "1.0.0",
            "uptime": str(datetime.utcnow() - gateway_metrics["start_time"]),
            "total_requests": gateway_metrics["total_requests"],
            "success_rate": gateway_metrics["successful_requests"] / max(gateway_metrics["total_requests"], 1) * 100,
            "avg_response_time": gateway_metrics["avg_response_time"]
        },
        "services": services_health,
        "healthy_services": f"{healthy_services}/{len(core_services)}",
        "overall_status": "healthy" if healthy_services >= len(core_services) // 2 else "degraded"
    }

@app.get("/metrics")
async def gateway_metrics_endpoint(current_user: User = Depends(require_user(required_roles=["admin", "monitor"]))):
    """Métricas del gateway. Requiere rol admin o monitor."""
    return {
        "gateway_metrics": gateway_metrics,
        "tenant_usage": dict(gateway_metrics["tenant_usage"]),
        "rate_limits": {
            tenant: {service: len(requests) for service, requests in services.items()}
            for tenant, services in rate_limit_storage.items()
        }
    }

# === RUTAS DE SERVICIOS ===

@app.api_route("/analytics/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def analytics_proxy(path: str, request: Request):
    """Proxy para el servicio de Analytics."""
    tenant_id = get_tenant_id(request)
    
    # Verificar rate limiting
    if not check_rate_limit(tenant_id, "analytics"):
        raise HTTPException(status_code=429, detail="Rate limit exceeded for analytics service")
    
    # Leer body si existe
    body = await request.body() if request.method in ["POST", "PUT", "PATCH"] else None
    
    # Reenviar request
    result = await forward_request(
        "analytics", 
        f"/{path}", 
        request.method, 
        dict(request.headers),
        body,
        dict(request.query_params)
    )
    
    return Response(
        content=result["content"],
        status_code=result["status_code"],
        headers={k: v for k, v in result["headers"].items() if k.lower() not in ['content-length', 'transfer-encoding']}
    )

@app.api_route("/communications/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def communications_proxy(path: str, request: Request):
    """Proxy para el servicio de Communications."""
    tenant_id = get_tenant_id(request)
    
    if not check_rate_limit(tenant_id, "communications"):
        raise HTTPException(status_code=429, detail="Rate limit exceeded for communications service")
    
    body = await request.body() if request.method in ["POST", "PUT", "PATCH"] else None
    
    result = await forward_request(
        "communications", 
        f"/{path}", 
        request.method, 
        dict(request.headers),
        body,
        dict(request.query_params)
    )
    
    return Response(
        content=result["content"],
        status_code=result["status_code"],
        headers={k: v for k, v in result["headers"].items() if k.lower() not in ['content-length', 'transfer-encoding']}
    )

@app.api_route("/billing/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def billing_proxy(path: str, request: Request):
    """Proxy para el servicio de Billing."""
    tenant_id = get_tenant_id(request)
    
    if not check_rate_limit(tenant_id, "billing"):
        raise HTTPException(status_code=429, detail="Rate limit exceeded for billing service")
    
    body = await request.body() if request.method in ["POST", "PUT", "PATCH"] else None
    
    result = await forward_request(
        "billing", 
        f"/{path}", 
        request.method, 
        dict(request.headers),
        body,
        dict(request.query_params)
    )
    
    return Response(
        content=result["content"],
        status_code=result["status_code"],
        headers={k: v for k, v in result["headers"].items() if k.lower() not in ['content-length', 'transfer-encoding']}
    )

@app.api_route("/mcp/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def mcp_proxy(path: str, request: Request):
    """Proxy para el servidor MCP."""
    tenant_id = get_tenant_id(request)
    
    if not check_rate_limit(tenant_id, "mcp_server"):
        raise HTTPException(status_code=429, detail="Rate limit exceeded for MCP service")
    
    body = await request.body() if request.method in ["POST", "PUT", "PATCH"] else None
    
    result = await forward_request(
        "mcp_server", 
        f"/{path}", 
        request.method, 
        dict(request.headers),
        body,
        dict(request.query_params)
    )
    
    return Response(
        content=result["content"],
        status_code=result["status_code"],
        headers={k: v for k, v in result["headers"].items() if k.lower() not in ['content-length', 'transfer-encoding']}
    )

@app.api_route("/templates/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def templates_proxy(path: str, request: Request):
    """Proxy para Template Engine API."""
    tenant_id = get_tenant_id(request)
    
    # Rate limiting
    if not check_rate_limit(tenant_id, "templates"):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    # Actualizar métricas de tenant
    gateway_metrics["tenant_usage"][tenant_id] += 1
    
    # Preparar datos del request
    headers = dict(request.headers)
    body = await request.body() if request.method in ["POST", "PUT", "PATCH"] else None
    params = dict(request.query_params)
    
    # Agregar tenant_id a headers
    headers["X-Tenant-ID"] = tenant_id
    
    try:
        result = await forward_request("templates", f"/{path}", request.method, headers, body, params)
        
        return Response(
            content=result["content"],
            status_code=result["status_code"],
            headers={k: v for k, v in result["headers"].items() if k.lower() not in ['content-length', 'transfer-encoding']}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Templates proxy error: {str(e)}")
        raise HTTPException(status_code=500, detail="Templates service error")

@app.api_route("/ai/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_ai_service(request: Request, path: str):
    """Proxy para AI Service sin autenticación (para desarrollo)"""
    tenant_id = get_tenant_id(request)
    
    if not check_rate_limit(tenant_id, "ai_services"):
        raise HTTPException(status_code=429, detail="Rate limit exceeded for AI service")
    
    # Preparar datos del request
    body = await request.body() if request.method in ["POST", "PUT", "PATCH"] else None
    headers = dict(request.headers)
    params = dict(request.query_params)
    
    headers["X-Tenant-ID"] = tenant_id
    
    try:
        result = await forward_request(
            "ai_services", 
            f"/{path}", 
            request.method, 
            headers, 
            body, 
            params
        )
        
        return Response(
            content=result["content"],
            status_code=result["status_code"],
            headers={k: v for k, v in result["headers"].items() if k.lower() not in ['content-length', 'transfer-encoding']}
        )
        
    except Exception as e:
        logger.error(f"AI Service proxy error: {str(e)}")
        raise HTTPException(status_code=500, detail="AI Service error")

@app.api_route("/api/agents/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def api_agent_proxy(path: str, request: Request, current_user: User = Depends(require_user(required_roles=["admin"]))):
    """Proxy para /api/agents desde el frontend. Requiere rol admin."""
    tenant_id = get_tenant_id(request)
    
    # Rate limiting para agentes
    if not check_rate_limit(tenant_id, "agent_api"):
        raise HTTPException(status_code=429, detail="Rate limit exceeded for agent API")
    
    # Preparar datos del request
    body = await request.body() if request.method in ["POST", "PUT", "PATCH"] else None
    headers = dict(request.headers)
    params = dict(request.query_params)
    
    # Agregar información del usuario admin
    headers["X-Admin-User"] = current_user.id
    headers["X-Admin-Email"] = current_user.email
    headers["X-Tenant-ID"] = tenant_id
    
    try:
        result = await forward_request(
            "agent_api", 
            f"/{path}", 
            request.method, 
            headers, 
            body, 
            params
        )
        
        return Response(
            content=result["content"],
            status_code=result["status_code"],
            headers={k: v for k, v in result["headers"].items() if k.lower() not in ['content-length', 'transfer-encoding']}
        )
        
    except Exception as e:
        logger.error(f"Agent API proxy error: {str(e)}")
        raise HTTPException(status_code=500, detail="Agent API service error")

@app.api_route("/api/agents", methods=["GET", "POST"])
async def api_agents_root(request: Request, current_user: User = Depends(require_user(required_roles=["admin"]))):
    """Proxy para /api/agents sin path adicional. Requiere rol admin."""
    tenant_id = get_tenant_id(request)
    
    # Rate limiting para agentes
    if not check_rate_limit(tenant_id, "agent_api"):
        raise HTTPException(status_code=429, detail="Rate limit exceeded for agent API")
    
    # Preparar datos del request
    body = await request.body() if request.method in ["POST", "PUT", "PATCH"] else None
    headers = dict(request.headers)
    params = dict(request.query_params)
    
    # Agregar información del usuario admin
    headers["X-Admin-User"] = current_user.id
    headers["X-Admin-Email"] = current_user.email
    headers["X-Tenant-ID"] = tenant_id
    
    try:
        result = await forward_request(
            "agent_api", 
            "/agents", 
            request.method, 
            headers, 
            body, 
            params
        )
        
        return Response(
            content=result["content"],
            status_code=result["status_code"],
            headers={k: v for k, v in result["headers"].items() if k.lower() not in ['content-length', 'transfer-encoding']}
        )
        
    except Exception as e:
        logger.error(f"Agent API proxy error: {str(e)}")
        raise HTTPException(status_code=500, detail="Agent API service error")

# === RUTAS DE DESARROLLO (SIN AUTENTICACIÓN) ===

@app.api_route("/dev/agents/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def dev_agent_proxy(path: str, request: Request):
    """Proxy para agentes en modo desarrollo (SIN AUTENTICACIÓN)."""
    tenant_id = get_tenant_id(request)
    
    # Rate limiting para agentes
    if not check_rate_limit(tenant_id, "agent_api"):
        raise HTTPException(status_code=429, detail="Rate limit exceeded for agent API")
    
    # Preparar datos del request
    body = await request.body() if request.method in ["POST", "PUT", "PATCH"] else None
    headers = dict(request.headers)
    params = dict(request.query_params)
    
    # Agregar información de usuario mock para desarrollo
    headers["X-Admin-User"] = "dev-user"
    headers["X-Admin-Email"] = "dev@tausestack.dev"
    headers["X-Tenant-ID"] = tenant_id
    
    try:
        result = await forward_request(
            "agent_api", 
            f"/{path}", 
            request.method, 
            headers, 
            body, 
            params
        )
        
        return Response(
            content=result["content"],
            status_code=result["status_code"],
            headers={k: v for k, v in result["headers"].items() if k.lower() not in ['content-length', 'transfer-encoding']}
        )
        
    except Exception as e:
        logger.error(f"Dev Agent API proxy error: {str(e)}")
        raise HTTPException(status_code=500, detail="Agent API service error")

@app.api_route("/dev/agents", methods=["GET", "POST"])
async def dev_agents_root(request: Request):
    """Proxy para /dev/agents sin path adicional (SIN AUTENTICACIÓN)."""
    tenant_id = get_tenant_id(request)
    
    # Rate limiting para agentes
    if not check_rate_limit(tenant_id, "agent_api"):
        raise HTTPException(status_code=429, detail="Rate limit exceeded for agent API")
    
    # Preparar datos del request
    body = await request.body() if request.method in ["POST", "PUT", "PATCH"] else None
    headers = dict(request.headers)
    params = dict(request.query_params)
    
    # Agregar información de usuario mock para desarrollo
    headers["X-Admin-User"] = "dev-user"
    headers["X-Admin-Email"] = "dev@tausestack.dev"
    headers["X-Tenant-ID"] = tenant_id
    
    try:
        result = await forward_request(
            "agent_api", 
            "/agents", 
            request.method, 
            headers, 
            body, 
            params
        )
        
        return Response(
            content=result["content"],
            status_code=result["status_code"],
            headers={k: v for k, v in result["headers"].items() if k.lower() not in ['content-length', 'transfer-encoding']}
        )
        
    except Exception as e:
        logger.error(f"Dev Agent API proxy error: {str(e)}")
        raise HTTPException(status_code=500, detail="Agent API service error")

@app.api_route("/agents/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def agent_api_proxy(path: str, request: Request, current_user: User = Depends(require_user(required_roles=["admin"]))):
    """Proxy para el servicio de agentes. Requiere rol admin."""
    tenant_id = get_tenant_id(request)
    
    # Rate limiting para agentes
    if not check_rate_limit(tenant_id, "agent_api"):
        raise HTTPException(status_code=429, detail="Rate limit exceeded for agent API")
    
    # Preparar datos del request
    body = await request.body() if request.method in ["POST", "PUT", "PATCH"] else None
    headers = dict(request.headers)
    params = dict(request.query_params)
    
    # Agregar información del usuario admin
    headers["X-Admin-User"] = current_user.id
    headers["X-Admin-Email"] = current_user.email
    headers["X-Tenant-ID"] = tenant_id
    
    try:
        result = await forward_request(
            "agent_api", 
            f"/{path}", 
            request.method, 
            headers, 
            body, 
            params
        )
        
        return Response(
            content=result["content"],
            status_code=result["status_code"],
            headers={k: v for k, v in result["headers"].items() if k.lower() not in ['content-length', 'transfer-encoding']}
        )
        
    except Exception as e:
        logger.error(f"Agent API proxy error: {str(e)}")
        raise HTTPException(status_code=500, detail="Agent API service error")

# === RUTAS API ADMIN ===

@app.api_route("/api/admin/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def api_admin_proxy(path: str, request: Request, current_user: User = Depends(require_user(required_roles=["admin"]))):
    """Proxy para rutas de admin API a través de /api/admin/*. Requiere rol admin."""
    tenant_id = get_tenant_id(request)
    
    # Rate limiting para administración
    if not check_rate_limit(tenant_id, "admin_api"):
        raise HTTPException(status_code=429, detail="Rate limit exceeded for admin API")
    
    # Preparar datos del request
    body = await request.body() if request.method in ["POST", "PUT", "PATCH"] else None
    headers = dict(request.headers)
    params = dict(request.query_params)
    
    # Agregar información del usuario admin
    headers["X-Admin-User"] = current_user.id
    headers["X-Admin-Email"] = current_user.email
    headers["X-Tenant-ID"] = tenant_id
    
    try:
        result = await forward_request(
            "admin_api", 
            f"/admin/{path}", 
            request.method, 
            headers, 
            body, 
            params
        )
        
        return Response(
            content=result["content"],
            status_code=result["status_code"],
            headers={k: v for k, v in result["headers"].items() if k.lower() not in ['content-length', 'transfer-encoding']}
        )
        
    except Exception as e:
        logger.error(f"API Admin proxy error: {str(e)}")
        raise HTTPException(status_code=500, detail="Admin API service error")

@app.api_route("/api/admin/apis", methods=["GET", "POST"])
async def api_admin_apis_root(request: Request, current_user: User = Depends(require_user(required_roles=["admin"]))):
    """Proxy para /api/admin/apis sin path adicional. Requiere rol admin."""
    tenant_id = get_tenant_id(request)
    
    # Rate limiting para administración
    if not check_rate_limit(tenant_id, "admin_api"):
        raise HTTPException(status_code=429, detail="Rate limit exceeded for admin API")
    
    # Preparar datos del request
    body = await request.body() if request.method in ["POST", "PUT", "PATCH"] else None
    headers = dict(request.headers)
    params = dict(request.query_params)
    
    # Agregar información del usuario admin
    headers["X-Admin-User"] = current_user.id
    headers["X-Admin-Email"] = current_user.email
    headers["X-Tenant-ID"] = tenant_id
    
    try:
        result = await forward_request(
            "admin_api", 
            "/admin/apis", 
            request.method, 
            headers, 
            body, 
            params
        )
        
        return Response(
            content=result["content"],
            status_code=result["status_code"],
            headers={k: v for k, v in result["headers"].items() if k.lower() not in ['content-length', 'transfer-encoding']}
        )
        
    except Exception as e:
        logger.error(f"API Admin APIs proxy error: {str(e)}")
        raise HTTPException(status_code=500, detail="Admin API service error")

@app.api_route("/admin/apis/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def admin_api_proxy(path: str, request: Request, current_user: User = Depends(require_user(required_roles=["admin"]))):
    """Proxy para el servicio de administración de APIs. Requiere rol admin."""
    tenant_id = get_tenant_id(request)
    
    # Rate limiting para administración
    if not check_rate_limit(tenant_id, "admin_api"):
        raise HTTPException(status_code=429, detail="Rate limit exceeded for admin API")
    
    # Preparar datos del request
    body = await request.body() if request.method in ["POST", "PUT", "PATCH"] else None
    headers = dict(request.headers)
    params = dict(request.query_params)
    
    # Agregar información del usuario admin
    headers["X-Admin-User"] = current_user.id
    headers["X-Admin-Email"] = current_user.email
    
    try:
        result = await forward_request(
            "admin_api", 
            f"/admin/apis/{path}", 
            request.method, 
            headers, 
            body, 
            params
        )
        
        return Response(
            content=result["content"],
            status_code=result["status_code"],
            headers={k: v for k, v in result["headers"].items() if k.lower() not in ['content-length', 'transfer-encoding']}
        )
        
    except Exception as e:
        logger.error(f"Admin API proxy error: {str(e)}")
        raise HTTPException(status_code=500, detail="Admin API service error")

@app.api_route("/admin/dashboard/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def admin_dashboard_proxy(path: str, request: Request, current_user: User = Depends(require_user(required_roles=["admin"]))):
    """Proxy para el dashboard administrativo. Requiere rol admin."""
    tenant_id = get_tenant_id(request)
    
    # Rate limiting para administración
    if not check_rate_limit(tenant_id, "admin_api"):
        raise HTTPException(status_code=429, detail="Rate limit exceeded for admin API")
    
    # Preparar datos del request
    body = await request.body() if request.method in ["POST", "PUT", "PATCH"] else None
    headers = dict(request.headers)
    params = dict(request.query_params)
    
    # Agregar información del usuario admin
    headers["X-Admin-User"] = current_user.id
    headers["X-Admin-Email"] = current_user.email
    
    try:
        result = await forward_request(
            "admin_api", 
            f"/admin/dashboard/{path}", 
            request.method, 
            headers, 
            body, 
            params
        )
        
        return Response(
            content=result["content"],
            status_code=result["status_code"],
            headers={k: v for k, v in result["headers"].items() if k.lower() not in ['content-length', 'transfer-encoding']}
        )
        
    except Exception as e:
        logger.error(f"Admin Dashboard proxy error: {str(e)}")
        raise HTTPException(status_code=500, detail="Admin Dashboard service error")

@app.api_route("/teams/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def team_api_proxy(path: str, request: Request, current_user: User = Depends(require_user(required_roles=["admin"]))):
    """Proxy para el servicio de equipos de agentes. Requiere rol admin."""
    tenant_id = get_tenant_id(request)
    
    # Rate limiting para equipos
    if not check_rate_limit(tenant_id, "team_api"):
        raise HTTPException(status_code=429, detail="Rate limit exceeded for team API")
    
    # Preparar datos del request
    body = await request.body() if request.method in ["POST", "PUT", "PATCH"] else None
    headers = dict(request.headers)
    params = dict(request.query_params)
    
    # Agregar información del usuario admin
    headers["X-Admin-User"] = current_user.id
    headers["X-Admin-Email"] = current_user.email
    headers["X-Tenant-ID"] = tenant_id
    
    try:
        result = await forward_request(
            "team_api", 
            f"/{path}", 
            request.method, 
            headers, 
            body, 
            params
        )
        
        return Response(
            content=result["content"],
            status_code=result["status_code"],
            headers={k: v for k, v in result["headers"].items() if k.lower() not in ['content-length', 'transfer-encoding']}
        )
        
    except Exception as e:
        logger.error(f"Team API proxy error: {str(e)}")
        raise HTTPException(status_code=500, detail="Team API service error")

# === RUTAS DE ADMINISTRACIÓN ===

@app.get("/admin/tenants")
async def list_tenants(current_user: User = Depends(require_user(required_roles=["admin"]))):
    """Lista todos los tenants activos. Requiere rol admin."""
    return {
        "tenants": list(gateway_metrics["tenant_usage"].keys()),
        "total_tenants": len(gateway_metrics["tenant_usage"]),
        "usage_stats": dict(gateway_metrics["tenant_usage"])
    }

@app.get("/admin/tenants/{tenant_id}/stats")
async def tenant_stats(tenant_id: str, current_user: User = Depends(require_user(required_roles=["admin"]))):
    """Estadísticas de un tenant específico. Requiere rol admin."""
    if tenant_id not in gateway_metrics["tenant_usage"]:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return {
        "tenant_id": tenant_id,
        "total_requests": gateway_metrics["tenant_usage"][tenant_id],
        "rate_limits": {
            service: len(requests) 
            for service, requests in rate_limit_storage[tenant_id].items()
        },
        "services_used": list(rate_limit_storage[tenant_id].keys())
    }

@app.post("/admin/tenants/{tenant_id}/reset-limits")
async def reset_tenant_limits(tenant_id: str, current_user: User = Depends(require_user(required_roles=["admin"]))):
    """Resetea los límites de rate limiting de un tenant. Requiere rol admin."""
    if tenant_id in rate_limit_storage:
        rate_limit_storage[tenant_id].clear()
    
    return {
        "message": f"Rate limits reset for tenant {tenant_id}",
        "timestamp": datetime.utcnow().isoformat(),
        "reset_by": current_user.id
    }

# === BUILDER API v1 ENDPOINTS ===

@app.api_route("/v1/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def builder_api_v1_proxy(path: str, request: Request):
    """Proxy para Builder API v1 - Templates, Apps, Deploy, Tenants"""
    tenant_id = get_tenant_id(request)
    
    # Rate limiting para Builder API
    if not check_rate_limit(tenant_id, "builder_api"):
        raise HTTPException(status_code=429, detail="Rate limit exceeded for Builder API")
    
    # Actualizar métricas
    gateway_metrics["tenant_usage"][tenant_id] += 1
    
    # Preparar request
    headers = dict(request.headers)
    body = await request.body() if request.method in ["POST", "PUT", "PATCH"] else None
    params = dict(request.query_params)
    
    # Agregar tenant_id a headers para context
    headers["X-Tenant-ID"] = tenant_id
    
    try:
        # Builder API tiene rutas /v1/* y /health
        # /v1/templates/list -> /v1/templates/list
        # /v1/health -> /health (especial case)
        if path == "health":
            builder_path = "/health"
        else:
            builder_path = f"/v1/{path}"
        
        result = await forward_request("builder_api", builder_path, request.method, headers, body, params)
        
        return Response(
            content=result["content"],
            status_code=result["status_code"],
            headers={k: v for k, v in result["headers"].items() if k.lower() not in ['content-length', 'transfer-encoding']}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Builder API v1 proxy error: {str(e)}")
        raise HTTPException(status_code=500, detail="Builder API service error")

# === BUILDER API SPECIFIC ROUTES ===

@app.get("/v1/templates/list")
async def v1_templates_list(request: Request):
    """Endpoint directo para listar templates - sin autenticación para builders públicos"""
    return await builder_api_v1_proxy("templates/list", request)

@app.get("/v1/templates/{template_id}")
async def v1_template_detail(template_id: str, request: Request):
    """Endpoint directo para detalles de template"""
    return await builder_api_v1_proxy(f"templates/{template_id}", request)

@app.post("/v1/apps/create")
async def v1_create_app(request: Request):
    """Endpoint directo para crear apps - requiere autenticación en el Builder API"""
    return await builder_api_v1_proxy("apps/create", request)

@app.get("/v1/apps/{app_id}")
async def v1_get_app(app_id: str, request: Request):
    """Endpoint directo para estado de app"""
    return await builder_api_v1_proxy(f"apps/{app_id}", request)

@app.post("/v1/deploy/start")
async def v1_start_deploy(request: Request):
    """Endpoint directo para iniciar deployment"""
    return await builder_api_v1_proxy("deploy/start", request)

@app.get("/v1/deploy/{deployment_id}")
async def v1_get_deployment(deployment_id: str, request: Request):
    """Endpoint directo para estado de deployment"""
    return await builder_api_v1_proxy(f"deploy/{deployment_id}", request)

@app.post("/v1/tenants/create")
async def v1_create_tenant(request: Request):
    """Endpoint directo para crear tenant"""
    return await builder_api_v1_proxy("tenants/create", request)

@app.get("/v1/tenants/{tenant_id}")
async def v1_get_tenant(tenant_id: str, request: Request):
    """Endpoint directo para info de tenant"""
    return await builder_api_v1_proxy(f"tenants/{tenant_id}", request)

# === RUTAS ADMIN DUPLICADAS REMOVIDAS ===
# Las rutas admin apropiadas con autenticación están definidas arriba

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_gateway:app",
        host="0.0.0.0",
        port=9001,
        reload=True,
        log_level="info"
    ) 

# === FRONTEND ESTÁTICO (AL FINAL PARA NO CAPTURAR RUTAS API) ===

# Servir archivos estáticos del frontend en la raíz /
try:
    # En producción Docker, el frontend está en /app/frontend/
    frontend_build_path = "/app/frontend"
    if os.path.exists(frontend_build_path):
        app.mount("/", StaticFiles(directory=frontend_build_path, html=True), name="frontend")
        logger.info(f"Frontend estático montado en / desde: {frontend_build_path}")
    else:
        # Fallback para desarrollo local
        frontend_build_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "out")
        if os.path.exists(frontend_build_path):
            app.mount("/", StaticFiles(directory=frontend_build_path, html=True), name="frontend")
            logger.info(f"Frontend estático montado en / desde: {frontend_build_path}")
            logger.warning("Para desarrollo local, ejecuta: cd frontend && npm run build")
        else:
            logger.warning(f"Frontend build no encontrado en: {frontend_build_path}")
except Exception as e:
    logger.error(f"Error montando frontend estático: {e}")

# Sistema de autenticación ya importado arriba 