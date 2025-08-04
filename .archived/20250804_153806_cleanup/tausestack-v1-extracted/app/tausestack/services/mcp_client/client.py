"""
MCP Client Implementation
Cliente completo para el protocolo MCP con soporte para JSON-RPC 2.0
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union, Callable
import uuid
from datetime import datetime

from .models import (
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCNotification,
    MCPMethod,
    MCPErrorCode,
    MCPMessage,
    # Initialize
    InitializeParams,
    InitializeResult,
    ProtocolVersion,
    Implementation,
    ClientCapabilities,
    # Tools
    Tool,
    CallToolParams,
    ToolResult,
    # Resources
    Resource,
    ReadResourceParams,
    ResourceContents,
    # Prompts
    Prompt,
    GetPromptParams,
    GetPromptResult,
    # Sampling
    CreateMessageParams,
    CreateMessageResult,
    # Logging
    LogLevel,
    LoggingMessageParams,
    # Progress
    ProgressParams,
)
from .transport import MCPTransport, TransportFactory

logger = logging.getLogger(__name__)

class MCPClientError(Exception):
    """Base exception for MCP client errors."""
    pass

class MCPTimeoutError(MCPClientError):
    """Raised when a request times out."""
    pass

class MCPConnectionError(MCPClientError):
    """Raised when connection issues occur."""
    pass

class MCPClient:
    """
    MCP Client Implementation
    
    Implementa un cliente completo para el protocolo MCP con:
    - Negotiación de capabilities
    - Manejo de todos los tipos de mensajes MCP
    - Soporte para múltiples transportes
    - Manejo de errores y timeouts
    - Progress tracking
    """
    
    def __init__(
        self,
        client_info: Implementation,
        transport: MCPTransport,
        timeout: float = 30.0,
        capabilities: Optional[ClientCapabilities] = None
    ):
        self.client_info = client_info
        self.transport = transport
        self.timeout = timeout
        self.capabilities = capabilities or ClientCapabilities()
        
        # Connection state
        self.is_initialized = False
        self.server_info: Optional[Implementation] = None
        self.server_capabilities: Optional[Dict[str, Any]] = None
        self.protocol_version: Optional[ProtocolVersion] = None
        
        # Request tracking
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.request_handlers: Dict[str, Callable] = {}
        
        # Notification handlers
        self.notification_handlers: Dict[str, Callable] = {}
        
        # Progress tracking
        self.progress_handlers: Dict[Union[str, int], Callable] = {}
        
        # Setup transport handlers
        self._setup_transport_handlers()
    
    def _setup_transport_handlers(self) -> None:
        """Setup transport message handlers."""
        self.transport.register_handler("response", self._handle_response)
        self.transport.register_handler("notification", self._handle_notification)
        self.transport.register_handler("request", self._handle_request)
    
    async def connect(self) -> None:
        """Connect to the MCP server."""
        try:
            await self.transport.connect()
            logger.info("MCP client connected to transport")
            
            # Start message handling task
            self._message_task = asyncio.create_task(self._handle_messages())
            
        except Exception as e:
            logger.error(f"Failed to connect MCP client: {e}")
            raise MCPConnectionError(f"Connection failed: {e}")
    
    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        try:
            # Cancel pending requests
            for future in self.pending_requests.values():
                future.cancel()
            self.pending_requests.clear()
            
            # Cancel message handling task
            if hasattr(self, '_message_task'):
                self._message_task.cancel()
                try:
                    await self._message_task
                except asyncio.CancelledError:
                    pass
            
            await self.transport.disconnect()
            self.is_initialized = False
            logger.info("MCP client disconnected")
            
        except Exception as e:
            logger.error(f"Error disconnecting MCP client: {e}")
    
    async def initialize(self) -> InitializeResult:
        """Initialize the MCP session."""
        if self.is_initialized:
            raise MCPClientError("Client already initialized")
        
        params = InitializeParams(
            protocolVersion=ProtocolVersion(),
            capabilities=self.capabilities,
            clientInfo=self.client_info
        )
        
        try:
            result = await self.send_request(
                MCPMethod.INITIALIZE,
                params.model_dump()
            )
            
            # Parse initialize result
            init_result = InitializeResult(**result)
            
            # Store server info
            self.server_info = init_result.serverInfo
            self.server_capabilities = init_result.capabilities.model_dump()
            self.protocol_version = init_result.protocolVersion
            
            # Send initialized notification
            await self.send_notification(MCPMethod.INITIALIZED)
            
            self.is_initialized = True
            logger.info(f"MCP client initialized with server: {self.server_info.name}")
            
            return init_result
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP client: {e}")
            raise MCPClientError(f"Initialization failed: {e}")
    
    async def send_request(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> Any:
        """Send a JSON-RPC request and wait for response."""
        request_id = str(uuid.uuid4())
        request = MCPMessage.create_request(method, params, request_id)
        
        # Create future for response
        response_future = asyncio.Future()
        self.pending_requests[request_id] = response_future
        
        try:
            # Send request
            await self.transport.send_message(request)
            
            # Wait for response
            response = await asyncio.wait_for(
                response_future,
                timeout=timeout or self.timeout
            )
            
            # Check for errors
            if response.error:
                raise MCPClientError(f"Server error: {response.error.message}")
            
            return response.result
            
        except asyncio.TimeoutError:
            self.pending_requests.pop(request_id, None)
            raise MCPTimeoutError(f"Request {method} timed out")
        except Exception as e:
            self.pending_requests.pop(request_id, None)
            raise
    
    async def send_notification(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None
    ) -> None:
        """Send a JSON-RPC notification."""
        notification = MCPMessage.create_notification(method, params)
        await self.transport.send_message(notification)
    
    async def send_response(
        self,
        request_id: Union[str, int],
        result: Any
    ) -> None:
        """Send a JSON-RPC response."""
        response = MCPMessage.create_response(result, request_id)
        await self.transport.send_message(response)
    
    async def send_error_response(
        self,
        request_id: Union[str, int],
        error_code: int,
        error_message: str,
        error_data: Optional[Any] = None
    ) -> None:
        """Send a JSON-RPC error response."""
        response = MCPMessage.create_error_response(
            error_code, error_message, request_id, error_data
        )
        await self.transport.send_message(response)
    
    # --- Tool Methods ---
    
    async def list_tools(self) -> List[Tool]:
        """List available tools."""
        if not self.is_initialized:
            raise MCPClientError("Client not initialized")
        
        result = await self.send_request(MCPMethod.TOOLS_LIST)
        return [Tool(**tool) for tool in result.get("tools", [])]
    
    async def call_tool(
        self,
        name: str,
        arguments: Optional[Dict[str, Any]] = None,
        progress_token: Optional[Union[str, int]] = None
    ) -> ToolResult:
        """Call a tool."""
        if not self.is_initialized:
            raise MCPClientError("Client not initialized")
        
        params = CallToolParams(name=name, arguments=arguments).model_dump()
        if progress_token:
            params["_meta"] = {"progressToken": progress_token}
        
        result = await self.send_request(MCPMethod.TOOLS_CALL, params)
        return ToolResult(**result)
    
    # --- Resource Methods ---
    
    async def list_resources(self) -> List[Resource]:
        """List available resources."""
        if not self.is_initialized:
            raise MCPClientError("Client not initialized")
        
        result = await self.send_request(MCPMethod.RESOURCES_LIST)
        return [Resource(**resource) for resource in result.get("resources", [])]
    
    async def read_resource(self, uri: str) -> ResourceContents:
        """Read a resource."""
        if not self.is_initialized:
            raise MCPClientError("Client not initialized")
        
        params = ReadResourceParams(uri=uri).model_dump()
        result = await self.send_request(MCPMethod.RESOURCES_READ, params)
        return ResourceContents(**result["contents"])
    
    async def subscribe_resource(self, uri: str) -> None:
        """Subscribe to resource updates."""
        if not self.is_initialized:
            raise MCPClientError("Client not initialized")
        
        params = {"uri": uri}
        await self.send_request(MCPMethod.RESOURCES_SUBSCRIBE, params)
    
    async def unsubscribe_resource(self, uri: str) -> None:
        """Unsubscribe from resource updates."""
        if not self.is_initialized:
            raise MCPClientError("Client not initialized")
        
        params = {"uri": uri}
        await self.send_request(MCPMethod.RESOURCES_UNSUBSCRIBE, params)
    
    # --- Prompt Methods ---
    
    async def list_prompts(self) -> List[Prompt]:
        """List available prompts."""
        if not self.is_initialized:
            raise MCPClientError("Client not initialized")
        
        result = await self.send_request(MCPMethod.PROMPTS_LIST)
        return [Prompt(**prompt) for prompt in result.get("prompts", [])]
    
    async def get_prompt(
        self,
        name: str,
        arguments: Optional[Dict[str, str]] = None
    ) -> GetPromptResult:
        """Get a prompt."""
        if not self.is_initialized:
            raise MCPClientError("Client not initialized")
        
        params = GetPromptParams(name=name, arguments=arguments).model_dump()
        result = await self.send_request(MCPMethod.PROMPTS_GET, params)
        return GetPromptResult(**result)
    
    # --- Sampling Methods ---
    
    async def create_message(self, params: CreateMessageParams) -> CreateMessageResult:
        """Create a message (sampling)."""
        if not self.is_initialized:
            raise MCPClientError("Client not initialized")
        
        result = await self.send_request(
            MCPMethod.SAMPLING_CREATE_MESSAGE,
            params.model_dump()
        )
        return CreateMessageResult(**result)
    
    # --- Logging Methods ---
    
    async def set_logging_level(self, level: LogLevel) -> None:
        """Set logging level."""
        if not self.is_initialized:
            raise MCPClientError("Client not initialized")
        
        params = {"level": level.value}
        await self.send_request(MCPMethod.LOGGING_SET_LEVEL, params)
    
    # --- Handler Registration ---
    
    def register_request_handler(self, method: str, handler: Callable) -> None:
        """Register a request handler."""
        self.request_handlers[method] = handler
    
    def register_notification_handler(self, method: str, handler: Callable) -> None:
        """Register a notification handler."""
        self.notification_handlers[method] = handler
    
    def register_progress_handler(self, token: Union[str, int], handler: Callable) -> None:
        """Register a progress handler."""
        self.progress_handlers[token] = handler
    
    # --- Message Handling ---
    
    async def _handle_messages(self) -> None:
        """Handle incoming messages from transport."""
        try:
            async for message in self.transport.receive_messages():
                if isinstance(message, JSONRPCResponse):
                    await self._handle_response(message)
                elif isinstance(message, JSONRPCNotification):
                    await self._handle_notification(message)
                elif isinstance(message, JSONRPCRequest):
                    await self._handle_request(message)
                    
        except asyncio.CancelledError:
            logger.info("Message handling cancelled")
        except Exception as e:
            logger.error(f"Error handling messages: {e}")
    
    async def _handle_response(self, response: JSONRPCResponse) -> None:
        """Handle a JSON-RPC response."""
        if response.id in self.pending_requests:
            future = self.pending_requests.pop(response.id)
            if not future.cancelled():
                future.set_result(response)
        else:
            logger.warning(f"Received response for unknown request: {response.id}")
    
    async def _handle_notification(self, notification: JSONRPCNotification) -> None:
        """Handle a JSON-RPC notification."""
        method = notification.method
        params = notification.params or {}
        
        # Handle progress notifications
        if method == MCPMethod.NOTIFICATIONS_PROGRESS:
            progress_params = ProgressParams(**params)
            handler = self.progress_handlers.get(progress_params.progressToken)
            if handler:
                try:
                    await handler(progress_params)
                except Exception as e:
                    logger.error(f"Error in progress handler: {e}")
            return
        
        # Handle other notifications
        handler = self.notification_handlers.get(method)
        if handler:
            try:
                await handler(notification)
            except Exception as e:
                logger.error(f"Error in notification handler for {method}: {e}")
        else:
            logger.warning(f"No handler for notification: {method}")
    
    async def _handle_request(self, request: JSONRPCRequest) -> None:
        """Handle a JSON-RPC request."""
        method = request.method
        params = request.params or {}
        
        handler = self.request_handlers.get(method)
        if handler:
            try:
                result = await handler(request)
                await self.send_response(request.id, result)
            except Exception as e:
                logger.error(f"Error in request handler for {method}: {e}")
                await self.send_error_response(
                    request.id,
                    MCPErrorCode.INTERNAL_ERROR,
                    f"Handler error: {str(e)}"
                )
        else:
            logger.warning(f"No handler for request: {method}")
            await self.send_error_response(
                request.id,
                MCPErrorCode.METHOD_NOT_FOUND,
                f"Method not found: {method}"
            )
    
    # --- Utility Methods ---
    
    def is_server_capability_supported(self, capability: str) -> bool:
        """Check if server supports a capability."""
        if not self.server_capabilities:
            return False
        return capability in self.server_capabilities
    
    def get_server_capability(self, capability: str) -> Optional[Dict[str, Any]]:
        """Get server capability details."""
        if not self.server_capabilities:
            return None
        return self.server_capabilities.get(capability)
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

# --- MCP Client Factory ---

class MCPClientFactory:
    """Factory for creating MCP clients."""
    
    @staticmethod
    def create_client(
        client_name: str,
        client_version: str,
        transport_type: str,
        transport_config: Dict[str, Any],
        capabilities: Optional[ClientCapabilities] = None,
        timeout: float = 30.0
    ) -> MCPClient:
        """Create an MCP client."""
        
        # Create client info
        client_info = Implementation(name=client_name, version=client_version)
        
        # Create transport
        transport = TransportFactory.create_transport(transport_type, **transport_config)
        
        # Create client
        return MCPClient(
            client_info=client_info,
            transport=transport,
            timeout=timeout,
            capabilities=capabilities
        )
    
    @staticmethod
    async def create_and_initialize_client(
        client_name: str,
        client_version: str,
        transport_type: str,
        transport_config: Dict[str, Any],
        capabilities: Optional[ClientCapabilities] = None,
        timeout: float = 30.0
    ) -> MCPClient:
        """Create and initialize an MCP client."""
        
        client = MCPClientFactory.create_client(
            client_name, client_version, transport_type, 
            transport_config, capabilities, timeout
        )
        
        await client.connect()
        await client.initialize()
        
        return client
