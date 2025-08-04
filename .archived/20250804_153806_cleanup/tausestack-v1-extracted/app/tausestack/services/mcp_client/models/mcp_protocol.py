"""
Model Context Protocol (MCP) Core Implementation
Implementación completa del protocolo MCP según especificación oficial
https://spec.modelcontextprotocol.io/specification/
"""

from typing import Any, Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field
from enum import Enum
import uuid
import json

# --- JSON-RPC 2.0 Base Types ---

class JSONRPCVersion(str, Enum):
    """JSON-RPC version."""
    V2_0 = "2.0"

class JSONRPCRequest(BaseModel):
    """JSON-RPC 2.0 Request."""
    jsonrpc: JSONRPCVersion = JSONRPCVersion.V2_0
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Optional[Union[str, int]] = None

class JSONRPCResponse(BaseModel):
    """JSON-RPC 2.0 Response."""
    jsonrpc: JSONRPCVersion = JSONRPCVersion.V2_0
    result: Optional[Any] = None
    error: Optional["JSONRPCError"] = None
    id: Optional[Union[str, int]] = None

class JSONRPCError(BaseModel):
    """JSON-RPC 2.0 Error."""
    code: int
    message: str
    data: Optional[Any] = None

class JSONRPCNotification(BaseModel):
    """JSON-RPC 2.0 Notification (no id field)."""
    jsonrpc: JSONRPCVersion = JSONRPCVersion.V2_0
    method: str
    params: Optional[Dict[str, Any]] = None

# --- MCP Error Codes ---

class MCPErrorCode(int, Enum):
    """MCP-specific error codes."""
    # JSON-RPC standard errors
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    
    # MCP-specific errors
    INVALID_PARAMS_MCP = -32000
    TIMEOUT = -32001
    CANCELLED = -32002
    RESOURCE_NOT_FOUND = -32003
    TOOL_NOT_FOUND = -32004
    PROMPT_NOT_FOUND = -32005

# --- MCP Capabilities ---

class ServerCapabilities(BaseModel):
    """Server capabilities."""
    tools: Optional[Dict[str, Any]] = None
    resources: Optional[Dict[str, Any]] = None
    prompts: Optional[Dict[str, Any]] = None
    logging: Optional[Dict[str, Any]] = None

class ClientCapabilities(BaseModel):
    """Client capabilities."""
    sampling: Optional[Dict[str, Any]] = None
    roots: Optional[Dict[str, Any]] = None
    elicitation: Optional[Dict[str, Any]] = None

# --- MCP Protocol Info ---

class ProtocolVersion(BaseModel):
    """Protocol version information."""
    version: str = "2025-03-26"

class Implementation(BaseModel):
    """Implementation information."""
    name: str
    version: str

# --- Initialize Messages ---

class InitializeParams(BaseModel):
    """Initialize request parameters."""
    protocolVersion: ProtocolVersion
    capabilities: ClientCapabilities
    clientInfo: Implementation

class InitializeResult(BaseModel):
    """Initialize response result."""
    protocolVersion: ProtocolVersion
    capabilities: ServerCapabilities
    serverInfo: Implementation

# --- Tool Types ---

class ToolInputSchema(BaseModel):
    """Tool input schema definition."""
    type: str = "object"
    properties: Dict[str, Any] = Field(default_factory=dict)
    required: Optional[List[str]] = None

class Tool(BaseModel):
    """Tool definition."""
    name: str
    description: Optional[str] = None
    inputSchema: ToolInputSchema

class CallToolParams(BaseModel):
    """Call tool parameters."""
    name: str
    arguments: Optional[Dict[str, Any]] = None

class ToolResult(BaseModel):
    """Tool execution result."""
    content: List[Dict[str, Any]]
    isError: Optional[bool] = None

# --- Resource Types ---

class Resource(BaseModel):
    """Resource definition."""
    uri: str
    name: str
    description: Optional[str] = None
    mimeType: Optional[str] = None

class ResourceTemplate(BaseModel):
    """Resource template for dynamic resources."""
    uriTemplate: str
    name: str
    description: Optional[str] = None
    mimeType: Optional[str] = None

class ReadResourceParams(BaseModel):
    """Read resource parameters."""
    uri: str

class ResourceContents(BaseModel):
    """Resource contents."""
    uri: str
    mimeType: Optional[str] = None
    text: Optional[str] = None
    blob: Optional[str] = None  # base64 encoded

# --- Prompt Types ---

class PromptArgument(BaseModel):
    """Prompt argument definition."""
    name: str
    description: Optional[str] = None
    required: Optional[bool] = None

class Prompt(BaseModel):
    """Prompt definition."""
    name: str
    description: Optional[str] = None
    arguments: Optional[List[PromptArgument]] = None

class GetPromptParams(BaseModel):
    """Get prompt parameters."""
    name: str
    arguments: Optional[Dict[str, str]] = None

class PromptMessage(BaseModel):
    """Prompt message."""
    role: Literal["user", "assistant", "system"]
    content: Dict[str, Any]

class GetPromptResult(BaseModel):
    """Get prompt result."""
    description: Optional[str] = None
    messages: List[PromptMessage]

# --- Sampling Types ---

class SamplingMessage(BaseModel):
    """Sampling message."""
    role: Literal["user", "assistant", "system"]
    content: Dict[str, Any]

class CreateMessageParams(BaseModel):
    """Create message parameters for sampling."""
    messages: List[SamplingMessage]
    modelPreferences: Optional[Dict[str, Any]] = None
    systemPrompt: Optional[str] = None
    includeContext: Optional[Literal["none", "thisServer", "allServers"]] = None
    temperature: Optional[float] = None
    maxTokens: Optional[int] = None
    stopSequences: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class CreateMessageResult(BaseModel):
    """Create message result."""
    role: Literal["assistant"]
    content: Dict[str, Any]
    model: str
    stopReason: Optional[str] = None

# --- Logging Types ---

class LogLevel(str, Enum):
    """Log levels."""
    DEBUG = "debug"
    INFO = "info"
    NOTICE = "notice"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    ALERT = "alert"
    EMERGENCY = "emergency"

class LoggingMessageParams(BaseModel):
    """Logging message parameters."""
    level: LogLevel
    data: Any
    logger: Optional[str] = None

# --- Progress Types ---

class ProgressToken(BaseModel):
    """Progress token."""
    token: Union[str, int]

class ProgressParams(BaseModel):
    """Progress notification parameters."""
    progressToken: Union[str, int]
    progress: int
    total: Optional[int] = None

# --- MCP Message Types ---

class MCPMessage(BaseModel):
    """Base MCP message type."""
    
    @classmethod
    def create_request(cls, method: str, params: Optional[Dict[str, Any]] = None, 
                      request_id: Optional[Union[str, int]] = None) -> JSONRPCRequest:
        """Create a JSON-RPC request."""
        if request_id is None:
            request_id = str(uuid.uuid4())
        return JSONRPCRequest(method=method, params=params, id=request_id)
    
    @classmethod
    def create_response(cls, result: Any, request_id: Union[str, int]) -> JSONRPCResponse:
        """Create a JSON-RPC response."""
        return JSONRPCResponse(result=result, id=request_id)
    
    @classmethod
    def create_error_response(cls, error_code: int, error_message: str, 
                            request_id: Union[str, int], data: Optional[Any] = None) -> JSONRPCResponse:
        """Create a JSON-RPC error response."""
        error = JSONRPCError(code=error_code, message=error_message, data=data)
        return JSONRPCResponse(error=error, id=request_id)
    
    @classmethod
    def create_notification(cls, method: str, params: Optional[Dict[str, Any]] = None) -> JSONRPCNotification:
        """Create a JSON-RPC notification."""
        return JSONRPCNotification(method=method, params=params)

# --- MCP Method Names ---

class MCPMethod(str, Enum):
    """MCP method names."""
    # Lifecycle
    INITIALIZE = "initialize"
    INITIALIZED = "initialized"
    
    # Tools
    TOOLS_LIST = "tools/list"
    TOOLS_CALL = "tools/call"
    
    # Resources
    RESOURCES_LIST = "resources/list"
    RESOURCES_READ = "resources/read"
    RESOURCES_SUBSCRIBE = "resources/subscribe"
    RESOURCES_UNSUBSCRIBE = "resources/unsubscribe"
    
    # Prompts
    PROMPTS_LIST = "prompts/list"
    PROMPTS_GET = "prompts/get"
    
    # Sampling
    SAMPLING_CREATE_MESSAGE = "sampling/createMessage"
    
    # Logging
    LOGGING_SET_LEVEL = "logging/setLevel"
    
    # Notifications
    NOTIFICATIONS_CANCELLED = "notifications/cancelled"
    NOTIFICATIONS_PROGRESS = "notifications/progress"
    NOTIFICATIONS_MESSAGE = "notifications/message"
    NOTIFICATIONS_RESOURCES_LIST_CHANGED = "notifications/resources/list_changed"
    NOTIFICATIONS_RESOURCES_UPDATED = "notifications/resources/updated"
    NOTIFICATIONS_TOOLS_LIST_CHANGED = "notifications/tools/list_changed"
    NOTIFICATIONS_PROMPTS_LIST_CHANGED = "notifications/prompts/list_changed"

# --- Utility Functions ---

def parse_mcp_message(raw_message: str) -> Union[JSONRPCRequest, JSONRPCResponse, JSONRPCNotification]:
    """Parse a raw JSON-RPC message into the appropriate type."""
    try:
        data = json.loads(raw_message)
        
        # Check if it's a notification (no id field)
        if "id" not in data:
            return JSONRPCNotification(**data)
        
        # Check if it's a response (has result or error)
        if "result" in data or "error" in data:
            return JSONRPCResponse(**data)
        
        # Otherwise it's a request
        return JSONRPCRequest(**data)
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")
    except Exception as e:
        raise ValueError(f"Invalid MCP message format: {e}")

def serialize_mcp_message(message: Union[JSONRPCRequest, JSONRPCResponse, JSONRPCNotification]) -> str:
    """Serialize an MCP message to JSON string."""
    return message.model_dump_json(exclude_none=True)

# Update forward references
JSONRPCResponse.model_rebuild()
