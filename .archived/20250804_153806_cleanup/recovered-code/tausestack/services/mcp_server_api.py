"""
API para el servidor MCP Tause: gestión de memoria/contexto y tools para orquestación multiagente.
VERSIÓN 2.0: Multi-tenant con tools dinámicos y resources aislados.
"""
from fastapi import FastAPI, HTTPException, Header, Query, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Union
import os

app = FastAPI(title="MCP Tause Server v2.0", description="Servidor MCP multi-tenant para memoria y tools avanzada")

# --- Modelos ---

class AgentMemory(BaseModel):
    agent_id: str = Field(...)
    context: Dict[str, Any] = Field(default_factory=dict)
    tenant_id: Optional[str] = Field(default=None, description="Tenant ID for isolation")

class ToolRegistration(BaseModel):
    tool_id: str = Field(...)
    name: str
    description: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    tenant_id: Optional[str] = Field(default=None, description="Tenant ID for isolation")
    is_dynamic: bool = Field(default=False, description="Whether this tool is dynamically generated")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters schema")

class MCPResource(BaseModel):
    """Recurso MCP aislado por tenant."""
    resource_id: str = Field(...)
    name: str
    type: str = Field(description="Type of resource: file, database, api, etc.")
    uri: str = Field(description="Resource URI")
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tenant_id: Optional[str] = Field(default=None, description="Tenant ID for isolation")
    access_permissions: List[str] = Field(default_factory=list, description="Access permissions")

class TenantConfig(BaseModel):
    """Configuración específica de tenant para MCP."""
    tenant_id: str
    name: str
    mcp_config: Dict[str, Any] = Field(default_factory=dict)
    tool_limits: Dict[str, int] = Field(default_factory=dict)
    resource_limits: Dict[str, int] = Field(default_factory=dict)
    ai_providers: List[str] = Field(default_factory=list)

class DynamicToolRequest(BaseModel):
    """Request para crear tool dinámico."""
    name: str
    description: str
    parameters: Dict[str, Any]
    implementation: str = Field(description="Tool implementation code or endpoint")
    tenant_id: Optional[str] = None

# --- Multi-tenant storage ---
import json
from pathlib import Path

# Almacenamiento separado por tenant
TENANT_AGENT_MEMORIES: Dict[str, Dict[str, AgentMemory]] = {}
TENANT_TOOLS: Dict[str, Dict[str, ToolRegistration]] = {}
TENANT_RESOURCES: Dict[str, Dict[str, MCPResource]] = {}
TENANT_CONFIGS: Dict[str, TenantConfig] = {}

# Almacenamiento global (backward compatibility)
AGENT_MEMORIES: Dict[str, AgentMemory] = {}
TOOLS: Dict[str, ToolRegistration] = {}

# --- Helper functions ---

def get_tenant_id_from_request(
    tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
    tenant_query: Optional[str] = Query(None, alias="tenant_id")
) -> str:
    """Extraer tenant ID del header o query parameter."""
    effective_tenant = tenant_id or tenant_query or "default"
    return effective_tenant

def get_tenant_memories(tenant_id: str) -> Dict[str, AgentMemory]:
    """Obtener memorias del tenant específico."""
    if tenant_id not in TENANT_AGENT_MEMORIES:
        TENANT_AGENT_MEMORIES[tenant_id] = {}
    return TENANT_AGENT_MEMORIES[tenant_id]

def get_tenant_tools(tenant_id: str) -> Dict[str, ToolRegistration]:
    """Obtener tools del tenant específico."""
    if tenant_id not in TENANT_TOOLS:
        TENANT_TOOLS[tenant_id] = {}
    return TENANT_TOOLS[tenant_id]

def get_tenant_resources(tenant_id: str) -> Dict[str, MCPResource]:
    """Obtener resources del tenant específico."""
    if tenant_id not in TENANT_RESOURCES:
        TENANT_RESOURCES[tenant_id] = {}
    return TENANT_RESOURCES[tenant_id]

def is_multi_tenant_enabled() -> bool:
    """Verificar si el modo multi-tenant está habilitado."""
    return os.getenv("TAUSESTACK_MULTI_TENANT_MODE", "false").lower() == "true"

# --- Persistencia mejorada ---
DATA_PATH = Path(__file__).parent / "mcp_data.json"

def save_data():
    """Guardar datos con soporte multi-tenant."""
    data = {
        "agent_memories": {k: v.dict() for k, v in AGENT_MEMORIES.items()},
        "tools": {k: v.dict() for k, v in TOOLS.items()},
        "tenant_agent_memories": {
            tenant: {k: v.dict() for k, v in memories.items()}
            for tenant, memories in TENANT_AGENT_MEMORIES.items()
        },
        "tenant_tools": {
            tenant: {k: v.dict() for k, v in tools.items()}
            for tenant, tools in TENANT_TOOLS.items()
        },
        "tenant_resources": {
            tenant: {k: v.dict() for k, v in resources.items()}
            for tenant, resources in TENANT_RESOURCES.items()
        },
        "tenant_configs": {k: v.dict() for k, v in TENANT_CONFIGS.items()},
    }
    with open(DATA_PATH, "w") as f:
        json.dump(data, f, indent=2)

def load_data():
    """Cargar datos con soporte multi-tenant."""
    if DATA_PATH.exists():
        with open(DATA_PATH) as f:
            data = json.load(f)
        
        # Cargar datos globales (backward compatibility)
        AGENT_MEMORIES.clear()
        TOOLS.clear()
        for k, v in data.get("agent_memories", {}).items():
            AGENT_MEMORIES[k] = AgentMemory(**v)
        for k, v in data.get("tools", {}).items():
            TOOLS[k] = ToolRegistration(**v)
        
        # Cargar datos multi-tenant
        TENANT_AGENT_MEMORIES.clear()
        TENANT_TOOLS.clear()
        TENANT_RESOURCES.clear()
        TENANT_CONFIGS.clear()
        
        for tenant, memories in data.get("tenant_agent_memories", {}).items():
            TENANT_AGENT_MEMORIES[tenant] = {
                k: AgentMemory(**v) for k, v in memories.items()
            }
        
        for tenant, tools in data.get("tenant_tools", {}).items():
            TENANT_TOOLS[tenant] = {
                k: ToolRegistration(**v) for k, v in tools.items()
            }
        
        for tenant, resources in data.get("tenant_resources", {}).items():
            TENANT_RESOURCES[tenant] = {
                k: MCPResource(**v) for k, v in resources.items()
            }
        
        for k, v in data.get("tenant_configs", {}).items():
            TENANT_CONFIGS[k] = TenantConfig(**v)

# Cargar datos al iniciar
load_data()

# --- Endpoints de configuración de tenants ---

@app.post("/tenants/configure", response_model=TenantConfig)
def configure_tenant(config: TenantConfig):
    """Configurar un tenant para MCP."""
    TENANT_CONFIGS[config.tenant_id] = config
    save_data()
    return config

@app.get("/tenants", response_model=List[TenantConfig])
def list_tenants():
    """Listar todos los tenants configurados."""
    return list(TENANT_CONFIGS.values())

@app.get("/tenants/{tenant_id}", response_model=TenantConfig)
def get_tenant_config(tenant_id: str):
    """Obtener configuración de un tenant."""
    config = TENANT_CONFIGS.get(tenant_id)
    if not config:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return config

# --- Endpoints de memoria (con soporte multi-tenant) ---

@app.get("/memory/all")
def get_all_memories(tenant_id: str = Depends(get_tenant_id_from_request)):
    """
    Expone todas las memorias de agentes en formato federable.
    Soporta aislamiento por tenant.
    """
    if is_multi_tenant_enabled():
        memories = get_tenant_memories(tenant_id)
        return {"memories": [mem.dict() for mem in memories.values()], "tenant_id": tenant_id}
    else:
        return {"memories": [mem.dict() for mem in AGENT_MEMORIES.values()]}

@app.post("/memory/register", response_model=AgentMemory)
def register_memory(mem: AgentMemory, tenant_id: str = Depends(get_tenant_id_from_request)):
    """Registrar memoria de agente con soporte multi-tenant."""
    if is_multi_tenant_enabled():
        mem.tenant_id = tenant_id
        memories = get_tenant_memories(tenant_id)
        memories[mem.agent_id] = mem
    else:
        AGENT_MEMORIES[mem.agent_id] = mem
    
    save_data()
    return mem

@app.get("/memory/{agent_id}", response_model=AgentMemory)
def get_memory(agent_id: str, tenant_id: str = Depends(get_tenant_id_from_request)):
    """Obtener memoria de agente con soporte multi-tenant."""
    if is_multi_tenant_enabled():
        memories = get_tenant_memories(tenant_id)
        mem = memories.get(agent_id)
    else:
        mem = AGENT_MEMORIES.get(agent_id)
    
    if not mem:
        raise HTTPException(status_code=404, detail="Agent memory not found")
    return mem

# --- Endpoints de tools (con soporte multi-tenant y dinámicos) ---

@app.post("/tools/register", response_model=ToolRegistration)
def register_tool(tool: ToolRegistration, tenant_id: str = Depends(get_tenant_id_from_request)):
    """Registrar tool con soporte multi-tenant."""
    if is_multi_tenant_enabled():
        tool.tenant_id = tenant_id
        tools = get_tenant_tools(tenant_id)
        tools[tool.tool_id] = tool
    else:
        TOOLS[tool.tool_id] = tool
    
    save_data()
    return tool

@app.post("/tools/dynamic/create", response_model=ToolRegistration)
def create_dynamic_tool(
    request: DynamicToolRequest, 
    tenant_id: str = Depends(get_tenant_id_from_request)
):
    """Crear tool dinámico específico para el tenant."""
    tool_id = f"dynamic_{tenant_id}_{request.name}_{len(get_tenant_tools(tenant_id))}"
    
    tool = ToolRegistration(
        tool_id=tool_id,
        name=request.name,
        description=request.description,
        config={"implementation": request.implementation},
        tenant_id=tenant_id,
        is_dynamic=True,
        parameters=request.parameters
    )
    
    if is_multi_tenant_enabled():
        tools = get_tenant_tools(tenant_id)
        tools[tool_id] = tool
    else:
        TOOLS[tool_id] = tool
    
    save_data()
    return tool

@app.get("/tools", response_model=List[ToolRegistration])
def list_tools(
    tenant_id: str = Depends(get_tenant_id_from_request),
    include_dynamic: bool = Query(True, description="Include dynamic tools"),
    tool_type: Optional[str] = Query(None, description="Filter by tool type")
):
    """Listar tools con filtros y soporte multi-tenant."""
    if is_multi_tenant_enabled():
        tools = list(get_tenant_tools(tenant_id).values())
    else:
        tools = list(TOOLS.values())
    
    # Filtrar por tipo dinámico
    if not include_dynamic:
        tools = [t for t in tools if not t.is_dynamic]
    
    # Filtrar por tipo específico
    if tool_type:
        tools = [t for t in tools if t.config.get("type") == tool_type]
    
    return tools

@app.get("/tools/{tool_id}", response_model=ToolRegistration)
def get_tool(tool_id: str, tenant_id: str = Depends(get_tenant_id_from_request)):
    """Obtener tool específico con soporte multi-tenant."""
    if is_multi_tenant_enabled():
        tools = get_tenant_tools(tenant_id)
        tool = tools.get(tool_id)
    else:
        tool = TOOLS.get(tool_id)
    
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return tool

@app.delete("/tools/{tool_id}")
def delete_tool(tool_id: str, tenant_id: str = Depends(get_tenant_id_from_request)):
    """Eliminar tool con soporte multi-tenant."""
    if is_multi_tenant_enabled():
        tools = get_tenant_tools(tenant_id)
        if tool_id not in tools:
            raise HTTPException(status_code=404, detail="Tool not found")
        del tools[tool_id]
    else:
        if tool_id not in TOOLS:
            raise HTTPException(status_code=404, detail="Tool not found")
        del TOOLS[tool_id]
    
    save_data()
    return {"status": "deleted", "tool_id": tool_id}

# --- Endpoints de resources (NUEVO) ---

@app.post("/resources/register", response_model=MCPResource)
def register_resource(resource: MCPResource, tenant_id: str = Depends(get_tenant_id_from_request)):
    """Registrar resource aislado por tenant."""
    if is_multi_tenant_enabled():
        resource.tenant_id = tenant_id
        resources = get_tenant_resources(tenant_id)
        resources[resource.resource_id] = resource
    else:
        # En modo no multi-tenant, usar storage global (simplificado)
        if "global_resources" not in globals():
            global_resources = {}
        global_resources[resource.resource_id] = resource
    
    save_data()
    return resource

@app.get("/resources", response_model=List[MCPResource])
def list_resources(
    tenant_id: str = Depends(get_tenant_id_from_request),
    resource_type: Optional[str] = Query(None, description="Filter by resource type")
):
    """Listar resources aislados por tenant."""
    if is_multi_tenant_enabled():
        resources = list(get_tenant_resources(tenant_id).values())
    else:
        resources = []  # En modo no multi-tenant, simplificado
    
    # Filtrar por tipo
    if resource_type:
        resources = [r for r in resources if r.type == resource_type]
    
    return resources

@app.get("/resources/{resource_id}", response_model=MCPResource)
def get_resource(resource_id: str, tenant_id: str = Depends(get_tenant_id_from_request)):
    """Obtener resource específico aislado por tenant."""
    if is_multi_tenant_enabled():
        resources = get_tenant_resources(tenant_id)
        resource = resources.get(resource_id)
    else:
        resource = None  # Simplificado para modo no multi-tenant
    
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    return resource

@app.delete("/resources/{resource_id}")
def delete_resource(resource_id: str, tenant_id: str = Depends(get_tenant_id_from_request)):
    """Eliminar resource aislado por tenant."""
    if is_multi_tenant_enabled():
        resources = get_tenant_resources(tenant_id)
        if resource_id not in resources:
            raise HTTPException(status_code=404, detail="Resource not found")
        del resources[resource_id]
    else:
        raise HTTPException(status_code=400, detail="Resources not supported in non-multi-tenant mode")
    
    save_data()
    return {"status": "deleted", "resource_id": resource_id}

# --- Endpoints de estadísticas por tenant ---

@app.get("/tenants/{tenant_id}/stats")
def get_tenant_stats(tenant_id: str):
    """Obtener estadísticas de uso del tenant."""
    memories = get_tenant_memories(tenant_id)
    tools = get_tenant_tools(tenant_id)
    resources = get_tenant_resources(tenant_id)
    
    dynamic_tools = [t for t in tools.values() if t.is_dynamic]
    
    return {
        "tenant_id": tenant_id,
        "memories_count": len(memories),
        "tools_count": len(tools),
        "dynamic_tools_count": len(dynamic_tools),
        "resources_count": len(resources),
        "resource_types": list(set(r.type for r in resources.values())),
        "tool_types": list(set(t.config.get("type", "unknown") for t in tools.values()))
    }

# --- Federación con soporte multi-tenant ---

from fastapi import Body, Request
import httpx
from core.utils.auth import require_jwt, is_peer_allowed
import logging

@app.post("/federation/memory/pull")
@require_jwt
def pull_federated_memory(
    request: Request, 
    payload: dict = Body(...),
    tenant_id: str = Depends(get_tenant_id_from_request)
):
    """
    Sincroniza la memoria de agentes desde un MCP remoto con soporte multi-tenant.
    """
    url = payload.get("url")
    token = payload.get("token")
    remote_tenant = payload.get("tenant_id", tenant_id)
    
    if not url:
        raise HTTPException(status_code=400, detail="URL remota requerida")
    if not is_peer_allowed(url):
        raise HTTPException(status_code=403, detail="Peer remoto no permitido")
    
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    if is_multi_tenant_enabled():
        headers["X-Tenant-ID"] = remote_tenant
    
    try:
        resp = httpx.get(f"{url}/memory/all", headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        count = 0
        memories = get_tenant_memories(tenant_id) if is_multi_tenant_enabled() else AGENT_MEMORIES
        
        for mem in data.get("memories", []):
            agent_id = mem.get("agent_id")
            context = mem.get("context", {})
            if agent_id:
                memory_obj = AgentMemory(agent_id=agent_id, context=context, tenant_id=tenant_id)
                memories[agent_id] = memory_obj
                count += 1
        
        save_data()
        logging.info(f"Federación memoria desde {url} exitosa: {count} memorias importadas para tenant {tenant_id}")
        return {"status": "ok", "imported": count, "tenant_id": tenant_id}
    except Exception as e:
        logging.error(f"Federación memoria desde {url} fallida: {e}")
        raise HTTPException(status_code=502, detail=f"Error federando memoria: {e}")

@app.post("/federation/tools/pull")
@require_jwt
def pull_federated_tools(
    request: Request, 
    payload: dict = Body(...),
    tenant_id: str = Depends(get_tenant_id_from_request)
):
    """
    Sincroniza tools desde un MCP remoto con soporte multi-tenant.
    """
    url = payload.get("url")
    token = payload.get("token")
    remote_tenant = payload.get("tenant_id", tenant_id)
    
    if not url:
        raise HTTPException(status_code=400, detail="URL remota requerida")
    if not is_peer_allowed(url):
        raise HTTPException(status_code=403, detail="Peer remoto no permitido")
    
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    if is_multi_tenant_enabled():
        headers["X-Tenant-ID"] = remote_tenant
    
    try:
        resp = httpx.get(f"{url}/tools", headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        count = 0
        tools = get_tenant_tools(tenant_id) if is_multi_tenant_enabled() else TOOLS
        
        for tool in data:
            tool_id = tool.get("tool_id")
            if tool_id:
                tool_obj = ToolRegistration(**tool)
                tool_obj.tenant_id = tenant_id  # Reasignar al tenant local
                tools[tool_id] = tool_obj
                count += 1
        
        save_data()
        logging.info(f"Federación tools desde {url} exitosa: {count} tools importados para tenant {tenant_id}")
        return {"status": "ok", "imported": count, "tenant_id": tenant_id}
    except Exception as e:
        logging.error(f"Federación tools desde {url} fallida: {e}")
        raise HTTPException(status_code=502, detail=f"Error federando tools: {e}")

# --- Health check ---

@app.get("/health")
def health_check():
    """Health check con información del modo multi-tenant."""
    return {
        "status": "healthy",
        "multi_tenant_enabled": is_multi_tenant_enabled(),
        "tenants_count": len(TENANT_CONFIGS),
        "version": "2.0"
    }
