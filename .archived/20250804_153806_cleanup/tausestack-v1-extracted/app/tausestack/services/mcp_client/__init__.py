"""
TauseStack MCP Client Package
Implementación completa del protocolo Model Context Protocol (MCP) para TauseStack
"""

from .models import (
    # JSON-RPC Base Types
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCError,
    JSONRPCNotification,
    JSONRPCVersion,
    
    # MCP Error Codes
    MCPErrorCode,
    
    # Capabilities
    ServerCapabilities,
    ClientCapabilities,
    
    # Protocol Info
    ProtocolVersion,
    Implementation,
    
    # Initialize
    InitializeParams,
    InitializeResult,
    
    # Tools
    Tool,
    ToolInputSchema,
    CallToolParams,
    ToolResult,
    
    # Resources
    Resource,
    ResourceTemplate,
    ReadResourceParams,
    ResourceContents,
    
    # Prompts
    Prompt,
    PromptArgument,
    GetPromptParams,
    PromptMessage,
    GetPromptResult,
    
    # Sampling
    SamplingMessage,
    CreateMessageParams,
    CreateMessageResult,
    
    # Logging
    LogLevel,
    LoggingMessageParams,
    
    # Progress
    ProgressToken,
    ProgressParams,
    
    # Base Message
    MCPMessage,
    MCPMethod,
    
    # Utilities
    parse_mcp_message,
    serialize_mcp_message,
)

from .transport import (
    MCPTransport,
    STDIOTransport,
    WebSocketTransport,
    SSETransport,
    TransportFactory,
    TransportManager,
)

from .client import (
    MCPClient,
    MCPClientFactory,
    MCPClientError,
    MCPTimeoutError,
    MCPConnectionError,
)

from .server import (
    MCPServer,
    MCPServerError,
)

# Commented out to avoid import errors when TauseStack core is not available
# from .adapters.tausestack_adapter import (
#     TauseStackMCPAdapter,
# )

__version__ = "1.0.0"

__all__ = [
    # Models
    "JSONRPCRequest",
    "JSONRPCResponse",
    "JSONRPCError",
    "JSONRPCNotification",
    "JSONRPCVersion",
    "MCPErrorCode",
    "ServerCapabilities",
    "ClientCapabilities",
    "ProtocolVersion",
    "Implementation",
    "InitializeParams",
    "InitializeResult",
    "Tool",
    "ToolInputSchema",
    "CallToolParams",
    "ToolResult",
    "Resource",
    "ResourceTemplate",
    "ReadResourceParams",
    "ResourceContents",
    "Prompt",
    "PromptArgument",
    "GetPromptParams",
    "PromptMessage",
    "GetPromptResult",
    "SamplingMessage",
    "CreateMessageParams",
    "CreateMessageResult",
    "LogLevel",
    "LoggingMessageParams",
    "ProgressToken",
    "ProgressParams",
    "MCPMessage",
    "MCPMethod",
    "parse_mcp_message",
    "serialize_mcp_message",
    
    # Transport
    "MCPTransport",
    "STDIOTransport",
    "WebSocketTransport",
    "SSETransport",
    "TransportFactory",
    "TransportManager",
    
    # Client
    "MCPClient",
    "MCPClientFactory",
    "MCPClientError",
    "MCPTimeoutError",
    "MCPConnectionError",
    
    # Server
    "MCPServer",
    "MCPServerError",
    
    # Adapters (commented out)
    # "TauseStackMCPAdapter",
]

# Convenience imports for common usage patterns
from .client import MCPClient as Client
from .server import MCPServer as Server
# from .adapters.tausestack_adapter import TauseStackMCPAdapter as Adapter

# Version info
VERSION_INFO = {
    "major": 1,
    "minor": 0,
    "patch": 0,
    "release": "stable"
}

def get_version() -> str:
    """Get the version string."""
    return __version__

def get_version_info() -> dict:
    """Get detailed version information."""
    return VERSION_INFO.copy()

# Protocol constants
PROTOCOL_VERSION = "2025-03-26"
SUPPORTED_TRANSPORTS = ["stdio", "websocket", "sse"]
SUPPORTED_CAPABILITIES = [
    "tools",
    "resources", 
    "prompts",
    "sampling",
    "logging"
]

def create_tausestack_adapter(
    tenant_context,
    isolation_manager,
    auth_manager,
    database_manager,
    storage_manager
):
    """
    Convenience function to create a TauseStack MCP adapter.
    
    NOTE: This function is commented out because it requires TauseStack core dependencies.
    To use this function, uncomment the TauseStackMCPAdapter import at the top of this file.
    
    Args:
        tenant_context: TenantContext instance
        isolation_manager: IsolationManager instance
        auth_manager: AuthManager instance
        database_manager: DatabaseManager instance
        storage_manager: StorageManager instance
    
    Returns:
        TauseStackMCPAdapter instance
    """
    raise ImportError(
        "TauseStackMCPAdapter is not available. "
        "Please ensure TauseStack core dependencies are installed and "
        "uncomment the import in services/mcp_client/__init__.py"
    )
    # return TauseStackMCPAdapter(
    #     tenant_context=tenant_context,
    #     isolation_manager=isolation_manager,
    #     auth_manager=auth_manager,
    #     database_manager=database_manager,
    #     storage_manager=storage_manager
    # )

async def create_mcp_client(
    client_name: str,
    transport_type: str = "websocket",
    transport_config: dict = None,
    client_version: str = "1.0.0",
    capabilities: ClientCapabilities = None,
    timeout: float = 30.0
) -> MCPClient:
    """
    Convenience function to create and initialize an MCP client.
    
    Args:
        client_name: Name of the client
        transport_type: Type of transport ("stdio", "websocket", "sse")
        transport_config: Transport configuration
        client_version: Client version
        capabilities: Client capabilities
        timeout: Request timeout
    
    Returns:
        Initialized MCPClient instance
    """
    if transport_config is None:
        transport_config = {}
    
    return await MCPClientFactory.create_and_initialize_client(
        client_name=client_name,
        client_version=client_version,
        transport_type=transport_type,
        transport_config=transport_config,
        capabilities=capabilities,
        timeout=timeout
    )

def create_mcp_server(
    server_name: str,
    server_version: str = "1.0.0",
    capabilities: ServerCapabilities = None
) -> MCPServer:
    """
    Convenience function to create an MCP server.
    
    Args:
        server_name: Name of the server
        server_version: Server version
        capabilities: Server capabilities
    
    Returns:
        MCPServer instance
    """
    server_info = Implementation(
        name=server_name,
        version=server_version
    )
    
    return MCPServer(
        server_info=server_info,
        capabilities=capabilities
    )

# Export convenience functions
__all__.extend([
    "Client",
    "Server", 
    # "Adapter",  # Commented out
    "get_version",
    "get_version_info",
    "create_tausestack_adapter",
    "create_mcp_client",
    "create_mcp_server",
    "PROTOCOL_VERSION",
    "SUPPORTED_TRANSPORTS",
    "SUPPORTED_CAPABILITIES",
    "VERSION_INFO",
])
