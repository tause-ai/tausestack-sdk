"""
TauseStack MCP Adapter
Adaptador que integra el protocolo MCP con TauseStack multi-tenant
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime
import json
import uuid

from ..client import MCPClient, MCPClientFactory
from ..server import MCPServer
from ..models import (
    ClientCapabilities,
    ServerCapabilities,
    Implementation,
    Tool,
    ToolResult,
    Resource,
    ResourceContents,
    Prompt,
    GetPromptResult,
    CreateMessageParams,
    CreateMessageResult,
    LogLevel,
)
from ..transport import TransportFactory

# TauseStack imports
from tausestack.core.tenancy import TenantContext
from tausestack.core.isolation import IsolationManager
from tausestack.sdk.auth import AuthManager
from tausestack.sdk.database import DatabaseManager
from tausestack.sdk.storage import StorageManager

logger = logging.getLogger(__name__)

class TauseStackMCPAdapter:
    """
    Adaptador MCP para TauseStack
    
    Proporciona integración completa entre el protocolo MCP y TauseStack:
    - Aislamiento por tenant
    - Autenticación y autorización
    - Gestión de recursos multi-tenant
    - Tools dinámicos por tenant
    - Logging y monitoreo
    """
    
    def __init__(
        self,
        tenant_context: TenantContext,
        isolation_manager: IsolationManager,
        auth_manager: AuthManager,
        database_manager: DatabaseManager,
        storage_manager: StorageManager
    ):
        self.tenant_context = tenant_context
        self.isolation_manager = isolation_manager
        self.auth_manager = auth_manager
        self.database_manager = database_manager
        self.storage_manager = storage_manager
        
        # MCP Components
        self.mcp_server: Optional[MCPServer] = None
        self.mcp_clients: Dict[str, MCPClient] = {}
        
        # Tenant-specific registries
        self.tenant_tools: Dict[str, Dict[str, Tool]] = {}  # tenant_id -> tools
        self.tenant_resources: Dict[str, Dict[str, Resource]] = {}  # tenant_id -> resources
        self.tenant_prompts: Dict[str, Dict[str, Prompt]] = {}  # tenant_id -> prompts
        
        # Handlers
        self.tool_handlers: Dict[str, Callable] = {}
        self.resource_handlers: Dict[str, Callable] = {}
        self.prompt_handlers: Dict[str, Callable] = {}
        
        # AI Provider integration
        self.ai_providers: Dict[str, Any] = {}
        
        # Initialize default capabilities
        self.server_capabilities = ServerCapabilities(
            tools={"listChanged": True},
            resources={"subscribe": True, "listChanged": True},
            prompts={"listChanged": True},
            logging={}
        )
        
        self.client_capabilities = ClientCapabilities(
            sampling={},
            roots={"listChanged": True}
        )
    
    async def initialize_server(self, port: int = 8080) -> None:
        """Initialize MCP server."""
        try:
            server_info = Implementation(
                name="TauseStack MCP Server",
                version="1.0.0"
            )
            
            self.mcp_server = MCPServer(
                server_info=server_info,
                capabilities=self.server_capabilities
            )
            
            # Register default tools
            await self._register_default_tools()
            
            # Register default resources
            await self._register_default_resources()
            
            # Register default prompts
            await self._register_default_prompts()
            
            # Setup logging
            self.mcp_server.add_log_handler(self._handle_log_message)
            
            # Setup sampling
            self.mcp_server.register_sampling_handler(self._handle_sampling)
            
            # Add WebSocket transport
            from ..transport import WebSocketTransport
            websocket_transport = WebSocketTransport(f"ws://localhost:{port}/mcp")
            await self.mcp_server.add_transport("websocket", websocket_transport)
            
            # Start server
            await self.mcp_server.start()
            
            logger.info(f"TauseStack MCP server initialized on port {port}")
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP server: {e}")
            raise
    
    async def create_client(
        self,
        client_name: str,
        transport_type: str = "websocket",
        transport_config: Optional[Dict[str, Any]] = None
    ) -> MCPClient:
        """Create MCP client."""
        try:
            if transport_config is None:
                transport_config = {"uri": "ws://localhost:8080/mcp"}
            
            client = await MCPClientFactory.create_and_initialize_client(
                client_name=client_name,
                client_version="1.0.0",
                transport_type=transport_type,
                transport_config=transport_config,
                capabilities=self.client_capabilities
            )
            
            self.mcp_clients[client_name] = client
            
            logger.info(f"MCP client '{client_name}' created and initialized")
            
            return client
            
        except Exception as e:
            logger.error(f"Failed to create MCP client: {e}")
            raise
    
    async def _register_default_tools(self) -> None:
        """Register default TauseStack tools."""
        
        # Tenant management tools
        await self._register_tenant_tools()
        
        # Database tools
        await self._register_database_tools()
        
        # Storage tools
        await self._register_storage_tools()
        
        # Auth tools
        await self._register_auth_tools()
        
        # AI tools
        await self._register_ai_tools()
    
    async def _register_tenant_tools(self) -> None:
        """Register tenant management tools."""
        
        # Get tenant info
        self.mcp_server.register_tool(
            name="get_tenant_info",
            description="Get current tenant information",
            input_schema={
                "type": "object",
                "properties": {},
                "required": []
            },
            handler=self._handle_get_tenant_info
        )
        
        # List tenants (admin only)
        self.mcp_server.register_tool(
            name="list_tenants",
            description="List all tenants (admin only)",
            input_schema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 10},
                    "offset": {"type": "integer", "default": 0}
                },
                "required": []
            },
            handler=self._handle_list_tenants
        )
        
        # Create tenant (admin only)
        self.mcp_server.register_tool(
            name="create_tenant",
            description="Create a new tenant (admin only)",
            input_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "config": {"type": "object"}
                },
                "required": ["name"]
            },
            handler=self._handle_create_tenant
        )
    
    async def _register_database_tools(self) -> None:
        """Register database tools."""
        
        # Execute query
        self.mcp_server.register_tool(
            name="execute_query",
            description="Execute a database query",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "params": {"type": "object"}
                },
                "required": ["query"]
            },
            handler=self._handle_execute_query
        )
        
        # Get table schema
        self.mcp_server.register_tool(
            name="get_table_schema",
            description="Get table schema information",
            input_schema={
                "type": "object",
                "properties": {
                    "table_name": {"type": "string"}
                },
                "required": ["table_name"]
            },
            handler=self._handle_get_table_schema
        )
    
    async def _register_storage_tools(self) -> None:
        """Register storage tools."""
        
        # Upload file
        self.mcp_server.register_tool(
            name="upload_file",
            description="Upload a file to storage",
            input_schema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                    "content": {"type": "string"},
                    "content_type": {"type": "string"}
                },
                "required": ["file_path", "content"]
            },
            handler=self._handle_upload_file
        )
        
        # Download file
        self.mcp_server.register_tool(
            name="download_file",
            description="Download a file from storage",
            input_schema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"}
                },
                "required": ["file_path"]
            },
            handler=self._handle_download_file
        )
        
        # List files
        self.mcp_server.register_tool(
            name="list_files",
            description="List files in storage",
            input_schema={
                "type": "object",
                "properties": {
                    "prefix": {"type": "string"},
                    "limit": {"type": "integer", "default": 100}
                },
                "required": []
            },
            handler=self._handle_list_files
        )
    
    async def _register_auth_tools(self) -> None:
        """Register authentication tools."""
        
        # Get current user
        self.mcp_server.register_tool(
            name="get_current_user",
            description="Get current authenticated user",
            input_schema={
                "type": "object",
                "properties": {},
                "required": []
            },
            handler=self._handle_get_current_user
        )
        
        # Validate token
        self.mcp_server.register_tool(
            name="validate_token",
            description="Validate authentication token",
            input_schema={
                "type": "object",
                "properties": {
                    "token": {"type": "string"}
                },
                "required": ["token"]
            },
            handler=self._handle_validate_token
        )
    
    async def _register_ai_tools(self) -> None:
        """Register AI tools."""
        
        # Generate text
        self.mcp_server.register_tool(
            name="generate_text",
            description="Generate text using AI",
            input_schema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string"},
                    "provider": {"type": "string", "default": "openai"},
                    "model": {"type": "string"},
                    "max_tokens": {"type": "integer", "default": 1000},
                    "temperature": {"type": "number", "default": 0.7}
                },
                "required": ["prompt"]
            },
            handler=self._handle_generate_text
        )
        
        # Analyze text
        self.mcp_server.register_tool(
            name="analyze_text",
            description="Analyze text using AI",
            input_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "analysis_type": {"type": "string", "enum": ["sentiment", "entities", "summary"]},
                    "provider": {"type": "string", "default": "openai"}
                },
                "required": ["text", "analysis_type"]
            },
            handler=self._handle_analyze_text
        )
    
    async def _register_default_resources(self) -> None:
        """Register default resources."""
        
        # Tenant configuration
        self.mcp_server.register_resource(
            uri="tenant://config",
            name="Tenant Configuration",
            description="Current tenant configuration",
            mime_type="application/json",
            handler=self._handle_tenant_config_resource
        )
        
        # Database schema
        self.mcp_server.register_resource(
            uri="database://schema",
            name="Database Schema",
            description="Database schema information",
            mime_type="application/json",
            handler=self._handle_database_schema_resource
        )
        
        # Storage info
        self.mcp_server.register_resource(
            uri="storage://info",
            name="Storage Information",
            description="Storage usage and configuration",
            mime_type="application/json",
            handler=self._handle_storage_info_resource
        )
    
    async def _register_default_prompts(self) -> None:
        """Register default prompts."""
        
        # System prompt
        self.mcp_server.register_prompt(
            name="system_prompt",
            description="Generate system prompt for AI interactions",
            handler=self._handle_system_prompt
        )
        
        # Code generation prompt
        self.mcp_server.register_prompt(
            name="code_generation",
            description="Generate code based on requirements",
            arguments=[
                {"name": "language", "description": "Programming language", "required": True},
                {"name": "requirements", "description": "Code requirements", "required": True}
            ],
            handler=self._handle_code_generation_prompt
        )
    
    # --- Tool Handlers ---
    
    async def _handle_get_tenant_info(self, args: Dict[str, Any], progress_token: Optional[str] = None) -> ToolResult:
        """Handle get tenant info tool."""
        try:
            tenant_info = {
                "id": self.tenant_context.tenant_id,
                "name": self.tenant_context.tenant_name,
                "config": self.tenant_context.tenant_config,
                "created_at": self.tenant_context.created_at.isoformat() if self.tenant_context.created_at else None
            }
            
            return ToolResult(
                content=[{
                    "type": "text",
                    "text": json.dumps(tenant_info, indent=2)
                }]
            )
            
        except Exception as e:
            logger.error(f"Error getting tenant info: {e}")
            return ToolResult(
                content=[{"type": "text", "text": f"Error: {str(e)}"}],
                isError=True
            )
    
    async def _handle_list_tenants(self, args: Dict[str, Any], progress_token: Optional[str] = None) -> ToolResult:
        """Handle list tenants tool."""
        try:
            # Check admin permissions
            if not await self._check_admin_permissions():
                return ToolResult(
                    content=[{"type": "text", "text": "Error: Admin permissions required"}],
                    isError=True
                )
            
            # Get tenants from database
            query = "SELECT * FROM tenants LIMIT %s OFFSET %s"
            params = [args.get("limit", 10), args.get("offset", 0)]
            
            results = await self.database_manager.execute_query(query, params)
            
            return ToolResult(
                content=[{
                    "type": "text",
                    "text": json.dumps(results, indent=2, default=str)
                }]
            )
            
        except Exception as e:
            logger.error(f"Error listing tenants: {e}")
            return ToolResult(
                content=[{"type": "text", "text": f"Error: {str(e)}"}],
                isError=True
            )
    
    async def _handle_create_tenant(self, args: Dict[str, Any], progress_token: Optional[str] = None) -> ToolResult:
        """Handle create tenant tool."""
        try:
            # Check admin permissions
            if not await self._check_admin_permissions():
                return ToolResult(
                    content=[{"type": "text", "text": "Error: Admin permissions required"}],
                    isError=True
                )
            
            tenant_name = args["name"]
            tenant_config = args.get("config", {})
            
            # Create tenant
            tenant_id = str(uuid.uuid4())
            
            query = """
            INSERT INTO tenants (id, name, config, created_at)
            VALUES (%s, %s, %s, %s)
            """
            params = [tenant_id, tenant_name, json.dumps(tenant_config), datetime.now()]
            
            await self.database_manager.execute_query(query, params)
            
            result = {
                "id": tenant_id,
                "name": tenant_name,
                "config": tenant_config,
                "created_at": datetime.now().isoformat()
            }
            
            return ToolResult(
                content=[{
                    "type": "text",
                    "text": json.dumps(result, indent=2)
                }]
            )
            
        except Exception as e:
            logger.error(f"Error creating tenant: {e}")
            return ToolResult(
                content=[{"type": "text", "text": f"Error: {str(e)}"}],
                isError=True
            )
    
    async def _handle_execute_query(self, args: Dict[str, Any], progress_token: Optional[str] = None) -> ToolResult:
        """Handle execute query tool."""
        try:
            query = args["query"]
            params = args.get("params", {})
            
            # Execute query with tenant isolation
            results = await self.database_manager.execute_query(query, params)
            
            return ToolResult(
                content=[{
                    "type": "text",
                    "text": json.dumps(results, indent=2, default=str)
                }]
            )
            
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return ToolResult(
                content=[{"type": "text", "text": f"Error: {str(e)}"}],
                isError=True
            )
    
    async def _handle_get_table_schema(self, args: Dict[str, Any], progress_token: Optional[str] = None) -> ToolResult:
        """Handle get table schema tool."""
        try:
            table_name = args["table_name"]
            
            # Get table schema
            schema = await self.database_manager.get_table_schema(table_name)
            
            return ToolResult(
                content=[{
                    "type": "text",
                    "text": json.dumps(schema, indent=2)
                }]
            )
            
        except Exception as e:
            logger.error(f"Error getting table schema: {e}")
            return ToolResult(
                content=[{"type": "text", "text": f"Error: {str(e)}"}],
                isError=True
            )
    
    async def _handle_upload_file(self, args: Dict[str, Any], progress_token: Optional[str] = None) -> ToolResult:
        """Handle upload file tool."""
        try:
            file_path = args["file_path"]
            content = args["content"]
            content_type = args.get("content_type", "application/octet-stream")
            
            # Upload file with tenant isolation
            result = await self.storage_manager.upload_file(
                file_path, content.encode(), content_type
            )
            
            return ToolResult(
                content=[{
                    "type": "text",
                    "text": json.dumps(result, indent=2)
                }]
            )
            
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            return ToolResult(
                content=[{"type": "text", "text": f"Error: {str(e)}"}],
                isError=True
            )
    
    async def _handle_download_file(self, args: Dict[str, Any], progress_token: Optional[str] = None) -> ToolResult:
        """Handle download file tool."""
        try:
            file_path = args["file_path"]
            
            # Download file with tenant isolation
            content = await self.storage_manager.download_file(file_path)
            
            return ToolResult(
                content=[{
                    "type": "text",
                    "text": content.decode() if isinstance(content, bytes) else str(content)
                }]
            )
            
        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            return ToolResult(
                content=[{"type": "text", "text": f"Error: {str(e)}"}],
                isError=True
            )
    
    async def _handle_list_files(self, args: Dict[str, Any], progress_token: Optional[str] = None) -> ToolResult:
        """Handle list files tool."""
        try:
            prefix = args.get("prefix", "")
            limit = args.get("limit", 100)
            
            # List files with tenant isolation
            files = await self.storage_manager.list_files(prefix, limit)
            
            return ToolResult(
                content=[{
                    "type": "text",
                    "text": json.dumps(files, indent=2, default=str)
                }]
            )
            
        except Exception as e:
            logger.error(f"Error listing files: {e}")
            return ToolResult(
                content=[{"type": "text", "text": f"Error: {str(e)}"}],
                isError=True
            )
    
    async def _handle_get_current_user(self, args: Dict[str, Any], progress_token: Optional[str] = None) -> ToolResult:
        """Handle get current user tool."""
        try:
            # Get current user from auth context
            user_info = await self.auth_manager.get_current_user()
            
            return ToolResult(
                content=[{
                    "type": "text",
                    "text": json.dumps(user_info, indent=2, default=str)
                }]
            )
            
        except Exception as e:
            logger.error(f"Error getting current user: {e}")
            return ToolResult(
                content=[{"type": "text", "text": f"Error: {str(e)}"}],
                isError=True
            )
    
    async def _handle_validate_token(self, args: Dict[str, Any], progress_token: Optional[str] = None) -> ToolResult:
        """Handle validate token tool."""
        try:
            token = args["token"]
            
            # Validate token
            is_valid = await self.auth_manager.validate_token(token)
            
            result = {"valid": is_valid}
            
            return ToolResult(
                content=[{
                    "type": "text",
                    "text": json.dumps(result, indent=2)
                }]
            )
            
        except Exception as e:
            logger.error(f"Error validating token: {e}")
            return ToolResult(
                content=[{"type": "text", "text": f"Error: {str(e)}"}],
                isError=True
            )
    
    async def _handle_generate_text(self, args: Dict[str, Any], progress_token: Optional[str] = None) -> ToolResult:
        """Handle generate text tool."""
        try:
            prompt = args["prompt"]
            provider = args.get("provider", "openai")
            model = args.get("model")
            max_tokens = args.get("max_tokens", 1000)
            temperature = args.get("temperature", 0.7)
            
            # TODO: Integrate with AI providers
            # For now, return a placeholder
            result = {
                "text": f"Generated text for prompt: {prompt}",
                "provider": provider,
                "model": model,
                "tokens_used": 50
            }
            
            return ToolResult(
                content=[{
                    "type": "text",
                    "text": json.dumps(result, indent=2)
                }]
            )
            
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            return ToolResult(
                content=[{"type": "text", "text": f"Error: {str(e)}"}],
                isError=True
            )
    
    async def _handle_analyze_text(self, args: Dict[str, Any], progress_token: Optional[str] = None) -> ToolResult:
        """Handle analyze text tool."""
        try:
            text = args["text"]
            analysis_type = args["analysis_type"]
            provider = args.get("provider", "openai")
            
            # TODO: Integrate with AI providers
            # For now, return a placeholder
            result = {
                "analysis_type": analysis_type,
                "text": text,
                "result": f"Analysis result for {analysis_type}",
                "provider": provider
            }
            
            return ToolResult(
                content=[{
                    "type": "text",
                    "text": json.dumps(result, indent=2)
                }]
            )
            
        except Exception as e:
            logger.error(f"Error analyzing text: {e}")
            return ToolResult(
                content=[{"type": "text", "text": f"Error: {str(e)}"}],
                isError=True
            )
    
    # --- Resource Handlers ---
    
    async def _handle_tenant_config_resource(self, uri: str) -> ResourceContents:
        """Handle tenant config resource."""
        try:
            config = {
                "tenant_id": self.tenant_context.tenant_id,
                "tenant_name": self.tenant_context.tenant_name,
                "config": self.tenant_context.tenant_config
            }
            
            return ResourceContents(
                uri=uri,
                text=json.dumps(config, indent=2),
                mimeType="application/json"
            )
            
        except Exception as e:
            logger.error(f"Error getting tenant config resource: {e}")
            return ResourceContents(
                uri=uri,
                text=f"Error: {str(e)}",
                mimeType="text/plain"
            )
    
    async def _handle_database_schema_resource(self, uri: str) -> ResourceContents:
        """Handle database schema resource."""
        try:
            schema = await self.database_manager.get_schema()
            
            return ResourceContents(
                uri=uri,
                text=json.dumps(schema, indent=2),
                mimeType="application/json"
            )
            
        except Exception as e:
            logger.error(f"Error getting database schema resource: {e}")
            return ResourceContents(
                uri=uri,
                text=f"Error: {str(e)}",
                mimeType="text/plain"
            )
    
    async def _handle_storage_info_resource(self, uri: str) -> ResourceContents:
        """Handle storage info resource."""
        try:
            info = await self.storage_manager.get_storage_info()
            
            return ResourceContents(
                uri=uri,
                text=json.dumps(info, indent=2, default=str),
                mimeType="application/json"
            )
            
        except Exception as e:
            logger.error(f"Error getting storage info resource: {e}")
            return ResourceContents(
                uri=uri,
                text=f"Error: {str(e)}",
                mimeType="text/plain"
            )
    
    # --- Prompt Handlers ---
    
    async def _handle_system_prompt(self, args: Dict[str, str]) -> GetPromptResult:
        """Handle system prompt."""
        try:
            prompt_text = f"""
You are an AI assistant integrated with TauseStack, a multi-tenant framework.

Current Context:
- Tenant ID: {self.tenant_context.tenant_id}
- Tenant Name: {self.tenant_context.tenant_name}
- Environment: {self.tenant_context.tenant_config.get('environment', 'development')}

You have access to the following capabilities:
- Database operations with tenant isolation
- File storage operations with tenant isolation
- Authentication and authorization
- AI text generation and analysis

Always respect tenant boundaries and security policies.
"""
            
            return GetPromptResult(
                description="System prompt for TauseStack AI interactions",
                messages=[{
                    "role": "system",
                    "content": {"type": "text", "text": prompt_text}
                }]
            )
            
        except Exception as e:
            logger.error(f"Error generating system prompt: {e}")
            return GetPromptResult(
                description="Error generating system prompt",
                messages=[{
                    "role": "system",
                    "content": {"type": "text", "text": f"Error: {str(e)}"}
                }]
            )
    
    async def _handle_code_generation_prompt(self, args: Dict[str, str]) -> GetPromptResult:
        """Handle code generation prompt."""
        try:
            language = args.get("language", "python")
            requirements = args.get("requirements", "")
            
            prompt_text = f"""
Generate {language} code based on the following requirements:

Requirements:
{requirements}

Guidelines:
- Follow best practices for {language}
- Include proper error handling
- Add comments for complex logic
- Consider tenant isolation if applicable
- Use TauseStack patterns when relevant

Please provide clean, production-ready code.
"""
            
            return GetPromptResult(
                description=f"Code generation prompt for {language}",
                messages=[{
                    "role": "user",
                    "content": {"type": "text", "text": prompt_text}
                }]
            )
            
        except Exception as e:
            logger.error(f"Error generating code generation prompt: {e}")
            return GetPromptResult(
                description="Error generating code generation prompt",
                messages=[{
                    "role": "user",
                    "content": {"type": "text", "text": f"Error: {str(e)}"}
                }]
            )
    
    # --- Sampling Handler ---
    
    async def _handle_sampling(self, params: CreateMessageParams) -> CreateMessageResult:
        """Handle sampling request."""
        try:
            # TODO: Integrate with AI providers for actual sampling
            # For now, return a placeholder response
            
            messages = params.messages
            last_message = messages[-1] if messages else None
            
            if last_message and last_message.content.get("type") == "text":
                user_text = last_message.content.get("text", "")
                response_text = f"Response to: {user_text}"
            else:
                response_text = "Hello! I'm your TauseStack AI assistant."
            
            return CreateMessageResult(
                role="assistant",
                content={"type": "text", "text": response_text},
                model="tausestack-ai-v1",
                stopReason="completed"
            )
            
        except Exception as e:
            logger.error(f"Error in sampling: {e}")
            raise
    
    # --- Log Handler ---
    
    async def _handle_log_message(self, log_params: Any) -> None:
        """Handle log message."""
        try:
            # Forward to TauseStack logging system
            logger.info(f"MCP Log: {log_params}")
            
        except Exception as e:
            logger.error(f"Error handling log message: {e}")
    
    # --- Utility Methods ---
    
    async def _check_admin_permissions(self) -> bool:
        """Check if current user has admin permissions."""
        try:
            user_info = await self.auth_manager.get_current_user()
            return user_info.get("role") == "admin"
        except:
            return False
    
    async def shutdown(self) -> None:
        """Shutdown the adapter."""
        try:
            # Close all clients
            for client in self.mcp_clients.values():
                await client.disconnect()
            
            # Stop server
            if self.mcp_server:
                await self.mcp_server.stop()
            
            logger.info("TauseStack MCP adapter shut down")
            
        except Exception as e:
            logger.error(f"Error shutting down adapter: {e}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize_server()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.shutdown()
