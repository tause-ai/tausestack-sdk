"""
MCP Server Implementation
Servidor completo para el protocolo MCP con soporte multi-tenant
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Callable, Set
from datetime import datetime
import uuid

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
    ServerCapabilities,
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
from .transport import MCPTransport, TransportManager

logger = logging.getLogger(__name__)

class MCPServerError(Exception):
    """Base exception for MCP server errors."""
    pass

class MCPServer:
    """
    MCP Server Implementation
    
    Implementa un servidor completo para el protocolo MCP con:
    - Soporte multi-tenant
    - Registro dinámico de tools, resources y prompts
    - Capabilities negotiation
    - Progress tracking
    - Logging
    """
    
    def __init__(
        self,
        server_info: Implementation,
        capabilities: Optional[ServerCapabilities] = None
    ):
        self.server_info = server_info
        self.capabilities = capabilities or ServerCapabilities()
        
        # Client connections
        self.clients: Dict[str, Dict[str, Any]] = {}  # client_id -> client_info
        self.transport_manager = TransportManager()
        
        # Tools registry
        self.tools: Dict[str, Tool] = {}
        self.tool_handlers: Dict[str, Callable] = {}
        
        # Resources registry
        self.resources: Dict[str, Resource] = {}
        self.resource_templates: Dict[str, ResourceTemplate] = {}
        self.resource_handlers: Dict[str, Callable] = {}
        
        # Prompts registry
        self.prompts: Dict[str, Prompt] = {}
        self.prompt_handlers: Dict[str, Callable] = {}
        
        # Sampling handler
        self.sampling_handler: Optional[Callable] = None
        
        # Logging
        self.log_level = LogLevel.INFO
        self.log_handlers: List[Callable] = []
        
        # Progress tracking
        self.progress_tokens: Dict[str, Dict[str, Any]] = {}
        
        # Subscriptions
        self.resource_subscriptions: Dict[str, Set[str]] = {}  # uri -> set of client_ids
        
        # Request handlers
        self.request_handlers = {
            MCPMethod.INITIALIZE: self._handle_initialize,
            MCPMethod.TOOLS_LIST: self._handle_tools_list,
            MCPMethod.TOOLS_CALL: self._handle_tools_call,
            MCPMethod.RESOURCES_LIST: self._handle_resources_list,
            MCPMethod.RESOURCES_READ: self._handle_resources_read,
            MCPMethod.RESOURCES_SUBSCRIBE: self._handle_resources_subscribe,
            MCPMethod.RESOURCES_UNSUBSCRIBE: self._handle_resources_unsubscribe,
            MCPMethod.PROMPTS_LIST: self._handle_prompts_list,
            MCPMethod.PROMPTS_GET: self._handle_prompts_get,
            MCPMethod.SAMPLING_CREATE_MESSAGE: self._handle_sampling_create_message,
            MCPMethod.LOGGING_SET_LEVEL: self._handle_logging_set_level,
        }
        
        # Notification handlers
        self.notification_handlers = {
            MCPMethod.INITIALIZED: self._handle_initialized,
            MCPMethod.NOTIFICATIONS_CANCELLED: self._handle_cancelled,
        }
    
    async def start(self) -> None:
        """Start the MCP server."""
        logger.info(f"Starting MCP server: {self.server_info.name}")
        
        # Initialize capabilities
        self._initialize_capabilities()
        
        logger.info("MCP server started successfully")
    
    async def stop(self) -> None:
        """Stop the MCP server."""
        logger.info("Stopping MCP server")
        
        # Disconnect all clients
        await self.transport_manager.close_all()
        self.clients.clear()
        
        logger.info("MCP server stopped")
    
    def _initialize_capabilities(self) -> None:
        """Initialize server capabilities."""
        # Tools capability
        if self.tools or self.tool_handlers:
            self.capabilities.tools = {"listChanged": True}
        
        # Resources capability
        if self.resources or self.resource_handlers:
            self.capabilities.resources = {
                "subscribe": True,
                "listChanged": True
            }
        
        # Prompts capability
        if self.prompts or self.prompt_handlers:
            self.capabilities.prompts = {"listChanged": True}
        
        # Logging capability
        self.capabilities.logging = {}
    
    async def add_transport(self, name: str, transport: MCPTransport) -> None:
        """Add a transport to the server."""
        # Setup message handlers
        transport.register_handler("request", self._handle_request)
        transport.register_handler("notification", self._handle_notification)
        
        await self.transport_manager.add_transport(name, transport)
        logger.info(f"Transport '{name}' added to MCP server")
    
    async def remove_transport(self, name: str) -> None:
        """Remove a transport from the server."""
        await self.transport_manager.remove_transport(name)
        logger.info(f"Transport '{name}' removed from MCP server")
    
    # --- Tool Management ---
    
    def register_tool(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        handler: Callable
    ) -> None:
        """Register a tool."""
        tool = Tool(
            name=name,
            description=description,
            inputSchema=ToolInputSchema(**input_schema)
        )
        
        self.tools[name] = tool
        self.tool_handlers[name] = handler
        
        logger.info(f"Tool '{name}' registered")
        
        # Notify clients about tools list change
        asyncio.create_task(self._notify_tools_list_changed())
    
    def unregister_tool(self, name: str) -> None:
        """Unregister a tool."""
        self.tools.pop(name, None)
        self.tool_handlers.pop(name, None)
        
        logger.info(f"Tool '{name}' unregistered")
        
        # Notify clients about tools list change
        asyncio.create_task(self._notify_tools_list_changed())
    
    # --- Resource Management ---
    
    def register_resource(
        self,
        uri: str,
        name: str,
        description: Optional[str] = None,
        mime_type: Optional[str] = None,
        handler: Optional[Callable] = None
    ) -> None:
        """Register a resource."""
        resource = Resource(
            uri=uri,
            name=name,
            description=description,
            mimeType=mime_type
        )
        
        self.resources[uri] = resource
        if handler:
            self.resource_handlers[uri] = handler
        
        logger.info(f"Resource '{uri}' registered")
        
        # Notify clients about resources list change
        asyncio.create_task(self._notify_resources_list_changed())
    
    def register_resource_template(
        self,
        uri_template: str,
        name: str,
        description: Optional[str] = None,
        mime_type: Optional[str] = None,
        handler: Optional[Callable] = None
    ) -> None:
        """Register a resource template."""
        template = ResourceTemplate(
            uriTemplate=uri_template,
            name=name,
            description=description,
            mimeType=mime_type
        )
        
        self.resource_templates[uri_template] = template
        if handler:
            self.resource_handlers[uri_template] = handler
        
        logger.info(f"Resource template '{uri_template}' registered")
        
        # Notify clients about resources list change
        asyncio.create_task(self._notify_resources_list_changed())
    
    def unregister_resource(self, uri: str) -> None:
        """Unregister a resource."""
        self.resources.pop(uri, None)
        self.resource_handlers.pop(uri, None)
        
        logger.info(f"Resource '{uri}' unregistered")
        
        # Notify clients about resources list change
        asyncio.create_task(self._notify_resources_list_changed())
    
    # --- Prompt Management ---
    
    def register_prompt(
        self,
        name: str,
        description: Optional[str] = None,
        arguments: Optional[List[PromptArgument]] = None,
        handler: Optional[Callable] = None
    ) -> None:
        """Register a prompt."""
        prompt = Prompt(
            name=name,
            description=description,
            arguments=arguments
        )
        
        self.prompts[name] = prompt
        if handler:
            self.prompt_handlers[name] = handler
        
        logger.info(f"Prompt '{name}' registered")
        
        # Notify clients about prompts list change
        asyncio.create_task(self._notify_prompts_list_changed())
    
    def unregister_prompt(self, name: str) -> None:
        """Unregister a prompt."""
        self.prompts.pop(name, None)
        self.prompt_handlers.pop(name, None)
        
        logger.info(f"Prompt '{name}' unregistered")
        
        # Notify clients about prompts list change
        asyncio.create_task(self._notify_prompts_list_changed())
    
    # --- Sampling Management ---
    
    def register_sampling_handler(self, handler: Callable) -> None:
        """Register a sampling handler."""
        self.sampling_handler = handler
        logger.info("Sampling handler registered")
    
    # --- Logging Management ---
    
    def add_log_handler(self, handler: Callable) -> None:
        """Add a log handler."""
        self.log_handlers.append(handler)
    
    def remove_log_handler(self, handler: Callable) -> None:
        """Remove a log handler."""
        if handler in self.log_handlers:
            self.log_handlers.remove(handler)
    
    async def log_message(self, level: LogLevel, data: Any, logger_name: Optional[str] = None) -> None:
        """Log a message."""
        if level.value >= self.log_level.value:
            params = LoggingMessageParams(
                level=level,
                data=data,
                logger=logger_name
            )
            
            # Call log handlers
            for handler in self.log_handlers:
                try:
                    await handler(params)
                except Exception as e:
                    logger.error(f"Error in log handler: {e}")
            
            # Send notification to clients
            await self._send_notification(
                MCPMethod.NOTIFICATIONS_MESSAGE,
                params.model_dump()
            )
    
    # --- Progress Management ---
    
    async def create_progress_token(self, client_id: str, total: Optional[int] = None) -> str:
        """Create a progress token."""
        token = str(uuid.uuid4())
        self.progress_tokens[token] = {
            "client_id": client_id,
            "progress": 0,
            "total": total,
            "created_at": datetime.now()
        }
        return token
    
    async def update_progress(self, token: str, progress: int, total: Optional[int] = None) -> None:
        """Update progress."""
        if token in self.progress_tokens:
            self.progress_tokens[token]["progress"] = progress
            if total is not None:
                self.progress_tokens[token]["total"] = total
            
            # Send progress notification
            params = ProgressParams(
                progressToken=token,
                progress=progress,
                total=total
            )
            
            await self._send_notification(
                MCPMethod.NOTIFICATIONS_PROGRESS,
                params.model_dump()
            )
    
    async def complete_progress(self, token: str) -> None:
        """Complete progress tracking."""
        if token in self.progress_tokens:
            progress_info = self.progress_tokens.pop(token)
            total = progress_info.get("total", 100)
            
            # Send final progress notification
            params = ProgressParams(
                progressToken=token,
                progress=total,
                total=total
            )
            
            await self._send_notification(
                MCPMethod.NOTIFICATIONS_PROGRESS,
                params.model_dump()
            )
    
    # --- Message Handlers ---
    
    async def _handle_request(self, request: JSONRPCRequest) -> None:
        """Handle incoming request."""
        method = request.method
        params = request.params or {}
        
        handler = self.request_handlers.get(method)
        if handler:
            try:
                result = await handler(request, params)
                response = MCPMessage.create_response(result, request.id)
                await self.transport_manager.broadcast_message(response)
                
            except Exception as e:
                logger.error(f"Error handling request {method}: {e}")
                error_response = MCPMessage.create_error_response(
                    MCPErrorCode.INTERNAL_ERROR,
                    f"Internal error: {str(e)}",
                    request.id
                )
                await self.transport_manager.broadcast_message(error_response)
        else:
            error_response = MCPMessage.create_error_response(
                MCPErrorCode.METHOD_NOT_FOUND,
                f"Method not found: {method}",
                request.id
            )
            await self.transport_manager.broadcast_message(error_response)
    
    async def _handle_notification(self, notification: JSONRPCNotification) -> None:
        """Handle incoming notification."""
        method = notification.method
        params = notification.params or {}
        
        handler = self.notification_handlers.get(method)
        if handler:
            try:
                await handler(notification, params)
            except Exception as e:
                logger.error(f"Error handling notification {method}: {e}")
        else:
            logger.warning(f"No handler for notification: {method}")
    
    # --- Request Handler Implementations ---
    
    async def _handle_initialize(self, request: JSONRPCRequest, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request."""
        try:
            init_params = InitializeParams(**params)
            
            # Store client info
            client_id = str(request.id)
            self.clients[client_id] = {
                "info": init_params.clientInfo,
                "capabilities": init_params.capabilities,
                "protocol_version": init_params.protocolVersion,
                "initialized": False
            }
            
            # Create initialize result
            result = InitializeResult(
                protocolVersion=ProtocolVersion(),
                capabilities=self.capabilities,
                serverInfo=self.server_info
            )
            
            logger.info(f"Client initialized: {init_params.clientInfo.name}")
            
            return result.model_dump()
            
        except Exception as e:
            logger.error(f"Error in initialize: {e}")
            raise MCPServerError(f"Initialize failed: {e}")
    
    async def _handle_tools_list(self, request: JSONRPCRequest, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/list request."""
        return {
            "tools": [tool.model_dump() for tool in self.tools.values()]
        }
    
    async def _handle_tools_call(self, request: JSONRPCRequest, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request."""
        try:
            call_params = CallToolParams(**params)
            
            if call_params.name not in self.tool_handlers:
                raise MCPServerError(f"Tool not found: {call_params.name}")
            
            handler = self.tool_handlers[call_params.name]
            
            # Extract progress token if present
            progress_token = None
            if "_meta" in params and "progressToken" in params["_meta"]:
                progress_token = params["_meta"]["progressToken"]
            
            # Call tool handler
            result = await handler(call_params.arguments or {}, progress_token)
            
            # Ensure result is a ToolResult
            if not isinstance(result, ToolResult):
                result = ToolResult(content=[{"type": "text", "text": str(result)}])
            
            return result.model_dump()
            
        except Exception as e:
            logger.error(f"Error calling tool: {e}")
            raise MCPServerError(f"Tool call failed: {e}")
    
    async def _handle_resources_list(self, request: JSONRPCRequest, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/list request."""
        resources = list(self.resources.values())
        resource_templates = list(self.resource_templates.values())
        
        return {
            "resources": [resource.model_dump() for resource in resources],
            "resourceTemplates": [template.model_dump() for template in resource_templates]
        }
    
    async def _handle_resources_read(self, request: JSONRPCRequest, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/read request."""
        try:
            read_params = ReadResourceParams(**params)
            uri = read_params.uri
            
            # Check if resource exists
            if uri not in self.resources and uri not in self.resource_handlers:
                raise MCPServerError(f"Resource not found: {uri}")
            
            # Call resource handler if exists
            if uri in self.resource_handlers:
                handler = self.resource_handlers[uri]
                content = await handler(uri)
                
                if isinstance(content, ResourceContents):
                    return {"contents": content.model_dump()}
                else:
                    # Convert to ResourceContents
                    contents = ResourceContents(
                        uri=uri,
                        text=str(content),
                        mimeType="text/plain"
                    )
                    return {"contents": contents.model_dump()}
            else:
                # Return basic resource info
                resource = self.resources[uri]
                contents = ResourceContents(
                    uri=uri,
                    text=f"Resource: {resource.name}",
                    mimeType=resource.mimeType or "text/plain"
                )
                return {"contents": contents.model_dump()}
                
        except Exception as e:
            logger.error(f"Error reading resource: {e}")
            raise MCPServerError(f"Resource read failed: {e}")
    
    async def _handle_resources_subscribe(self, request: JSONRPCRequest, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/subscribe request."""
        uri = params.get("uri")
        if not uri:
            raise MCPServerError("URI required for subscription")
        
        client_id = str(request.id)
        
        if uri not in self.resource_subscriptions:
            self.resource_subscriptions[uri] = set()
        
        self.resource_subscriptions[uri].add(client_id)
        
        logger.info(f"Client {client_id} subscribed to resource {uri}")
        
        return {}
    
    async def _handle_resources_unsubscribe(self, request: JSONRPCRequest, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/unsubscribe request."""
        uri = params.get("uri")
        if not uri:
            raise MCPServerError("URI required for unsubscription")
        
        client_id = str(request.id)
        
        if uri in self.resource_subscriptions:
            self.resource_subscriptions[uri].discard(client_id)
            
            # Clean up empty subscriptions
            if not self.resource_subscriptions[uri]:
                del self.resource_subscriptions[uri]
        
        logger.info(f"Client {client_id} unsubscribed from resource {uri}")
        
        return {}
    
    async def _handle_prompts_list(self, request: JSONRPCRequest, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle prompts/list request."""
        return {
            "prompts": [prompt.model_dump() for prompt in self.prompts.values()]
        }
    
    async def _handle_prompts_get(self, request: JSONRPCRequest, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle prompts/get request."""
        try:
            get_params = GetPromptParams(**params)
            
            if get_params.name not in self.prompt_handlers:
                raise MCPServerError(f"Prompt not found: {get_params.name}")
            
            handler = self.prompt_handlers[get_params.name]
            result = await handler(get_params.arguments or {})
            
            # Ensure result is a GetPromptResult
            if not isinstance(result, GetPromptResult):
                result = GetPromptResult(
                    messages=[{
                        "role": "user",
                        "content": {"type": "text", "text": str(result)}
                    }]
                )
            
            return result.model_dump()
            
        except Exception as e:
            logger.error(f"Error getting prompt: {e}")
            raise MCPServerError(f"Prompt get failed: {e}")
    
    async def _handle_sampling_create_message(self, request: JSONRPCRequest, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle sampling/createMessage request."""
        if not self.sampling_handler:
            raise MCPServerError("Sampling not supported")
        
        try:
            create_params = CreateMessageParams(**params)
            result = await self.sampling_handler(create_params)
            
            if not isinstance(result, CreateMessageResult):
                raise MCPServerError("Invalid sampling result")
            
            return result.model_dump()
            
        except Exception as e:
            logger.error(f"Error in sampling: {e}")
            raise MCPServerError(f"Sampling failed: {e}")
    
    async def _handle_logging_set_level(self, request: JSONRPCRequest, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle logging/setLevel request."""
        level = params.get("level")
        if not level:
            raise MCPServerError("Level required")
        
        try:
            self.log_level = LogLevel(level)
            logger.info(f"Log level set to: {level}")
            return {}
            
        except ValueError:
            raise MCPServerError(f"Invalid log level: {level}")
    
    # --- Notification Handler Implementations ---
    
    async def _handle_initialized(self, notification: JSONRPCNotification, params: Dict[str, Any]) -> None:
        """Handle initialized notification."""
        # Mark client as initialized
        # Note: We don't have a direct way to identify the client from notification
        # In a real implementation, you might need to track this differently
        logger.info("Client sent initialized notification")
    
    async def _handle_cancelled(self, notification: JSONRPCNotification, params: Dict[str, Any]) -> None:
        """Handle cancelled notification."""
        request_id = params.get("requestId")
        if request_id:
            logger.info(f"Request {request_id} was cancelled")
    
    # --- Notification Sending ---
    
    async def _send_notification(self, method: str, params: Optional[Dict[str, Any]] = None) -> None:
        """Send a notification to all clients."""
        notification = MCPMessage.create_notification(method, params)
        await self.transport_manager.broadcast_message(notification)
    
    async def _notify_tools_list_changed(self) -> None:
        """Notify clients that tools list changed."""
        await self._send_notification(MCPMethod.NOTIFICATIONS_TOOLS_LIST_CHANGED)
    
    async def _notify_resources_list_changed(self) -> None:
        """Notify clients that resources list changed."""
        await self._send_notification(MCPMethod.NOTIFICATIONS_RESOURCES_LIST_CHANGED)
    
    async def _notify_prompts_list_changed(self) -> None:
        """Notify clients that prompts list changed."""
        await self._send_notification(MCPMethod.NOTIFICATIONS_PROMPTS_LIST_CHANGED)
    
    async def notify_resource_updated(self, uri: str) -> None:
        """Notify subscribed clients that a resource was updated."""
        if uri in self.resource_subscriptions:
            params = {"uri": uri}
            await self._send_notification(
                MCPMethod.NOTIFICATIONS_RESOURCES_UPDATED,
                params
            )
    
    # --- Context Manager ---
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
