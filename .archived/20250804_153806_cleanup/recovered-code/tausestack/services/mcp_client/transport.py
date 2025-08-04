"""
MCP Transport Layer Implementation
Implementa las capas de transporte para el protocolo MCP:
- STDIO (Standard Input/Output)
- SSE (Server-Sent Events)
- WebSocket
"""

import asyncio
import json
import sys
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Callable, Dict, Optional, Union
import websockets
from websockets.exceptions import ConnectionClosed
import aiohttp
from aiohttp import web
import logging

from .models import (
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCNotification,
    parse_mcp_message,
    serialize_mcp_message,
)

logger = logging.getLogger(__name__)

# --- Base Transport ---

class MCPTransport(ABC):
    """Base class for MCP transport implementations."""
    
    def __init__(self):
        self.message_handlers: Dict[str, Callable] = {}
        self.is_connected = False
        self._closed = False
    
    @abstractmethod
    async def connect(self) -> None:
        """Connect to the transport."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the transport."""
        pass
    
    @abstractmethod
    async def send_message(self, message: Union[JSONRPCRequest, JSONRPCResponse, JSONRPCNotification]) -> None:
        """Send a message through the transport."""
        pass
    
    @abstractmethod
    async def receive_messages(self) -> AsyncGenerator[Union[JSONRPCRequest, JSONRPCResponse, JSONRPCNotification], None]:
        """Receive messages from the transport."""
        pass
    
    def register_handler(self, method: str, handler: Callable) -> None:
        """Register a message handler."""
        self.message_handlers[method] = handler
    
    async def handle_message(self, message: Union[JSONRPCRequest, JSONRPCResponse, JSONRPCNotification]) -> None:
        """Handle an incoming message."""
        if isinstance(message, (JSONRPCRequest, JSONRPCNotification)):
            handler = self.message_handlers.get(message.method)
            if handler:
                try:
                    await handler(message)
                except Exception as e:
                    logger.error(f"Error handling message {message.method}: {e}")
            else:
                logger.warning(f"No handler for method: {message.method}")

# --- STDIO Transport ---

class STDIOTransport(MCPTransport):
    """STDIO transport for MCP."""
    
    def __init__(self):
        super().__init__()
        self.stdin_reader: Optional[asyncio.StreamReader] = None
        self.stdout_writer: Optional[asyncio.StreamWriter] = None
    
    async def connect(self) -> None:
        """Connect to STDIO."""
        try:
            # Create async readers/writers for stdin/stdout
            self.stdin_reader = asyncio.StreamReader()
            protocol = asyncio.StreamReaderProtocol(self.stdin_reader)
            
            loop = asyncio.get_event_loop()
            await loop.connect_read_pipe(lambda: protocol, sys.stdin)
            
            transport, protocol = await loop.connect_write_pipe(
                asyncio.streams.FlowControlMixin, sys.stdout
            )
            self.stdout_writer = asyncio.StreamWriter(transport, protocol, self.stdin_reader, loop)
            
            self.is_connected = True
            logger.info("STDIO transport connected")
            
        except Exception as e:
            logger.error(f"Failed to connect STDIO transport: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from STDIO."""
        self._closed = True
        if self.stdout_writer:
            self.stdout_writer.close()
            await self.stdout_writer.wait_closed()
        self.is_connected = False
        logger.info("STDIO transport disconnected")
    
    async def send_message(self, message: Union[JSONRPCRequest, JSONRPCResponse, JSONRPCNotification]) -> None:
        """Send a message through STDIO."""
        if not self.is_connected or not self.stdout_writer:
            raise RuntimeError("STDIO transport not connected")
        
        try:
            message_str = serialize_mcp_message(message)
            self.stdout_writer.write(f"{message_str}\n".encode())
            await self.stdout_writer.drain()
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise
    
    async def receive_messages(self) -> AsyncGenerator[Union[JSONRPCRequest, JSONRPCResponse, JSONRPCNotification], None]:
        """Receive messages from STDIO."""
        if not self.is_connected or not self.stdin_reader:
            raise RuntimeError("STDIO transport not connected")
        
        try:
            while not self._closed:
                line = await self.stdin_reader.readline()
                if not line:
                    break
                
                try:
                    message_str = line.decode().strip()
                    if message_str:
                        message = parse_mcp_message(message_str)
                        yield message
                        
                except Exception as e:
                    logger.error(f"Failed to parse message: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error receiving messages: {e}")
            raise

# --- WebSocket Transport ---

class WebSocketTransport(MCPTransport):
    """WebSocket transport for MCP."""
    
    def __init__(self, uri: str):
        super().__init__()
        self.uri = uri
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
    
    async def connect(self) -> None:
        """Connect to WebSocket."""
        try:
            self.websocket = await websockets.connect(self.uri)
            self.is_connected = True
            logger.info(f"WebSocket transport connected to {self.uri}")
            
        except Exception as e:
            logger.error(f"Failed to connect WebSocket transport: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from WebSocket."""
        self._closed = True
        if self.websocket:
            await self.websocket.close()
        self.is_connected = False
        logger.info("WebSocket transport disconnected")
    
    async def send_message(self, message: Union[JSONRPCRequest, JSONRPCResponse, JSONRPCNotification]) -> None:
        """Send a message through WebSocket."""
        if not self.is_connected or not self.websocket:
            raise RuntimeError("WebSocket transport not connected")
        
        try:
            message_str = serialize_mcp_message(message)
            await self.websocket.send(message_str)
            
        except ConnectionClosed:
            logger.error("WebSocket connection closed")
            self.is_connected = False
            raise
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise
    
    async def receive_messages(self) -> AsyncGenerator[Union[JSONRPCRequest, JSONRPCResponse, JSONRPCNotification], None]:
        """Receive messages from WebSocket."""
        if not self.is_connected or not self.websocket:
            raise RuntimeError("WebSocket transport not connected")
        
        try:
            async for message_str in self.websocket:
                try:
                    message = parse_mcp_message(message_str)
                    yield message
                    
                except Exception as e:
                    logger.error(f"Failed to parse message: {e}")
                    continue
                    
        except ConnectionClosed:
            logger.info("WebSocket connection closed")
            self.is_connected = False
        except Exception as e:
            logger.error(f"Error receiving messages: {e}")
            raise

# --- SSE Transport ---

class SSETransport(MCPTransport):
    """Server-Sent Events transport for MCP."""
    
    def __init__(self, endpoint_url: str):
        super().__init__()
        self.endpoint_url = endpoint_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.response: Optional[aiohttp.ClientResponse] = None
    
    async def connect(self) -> None:
        """Connect to SSE endpoint."""
        try:
            self.session = aiohttp.ClientSession()
            self.response = await self.session.get(
                self.endpoint_url,
                headers={'Accept': 'text/event-stream'}
            )
            
            if self.response.status == 200:
                self.is_connected = True
                logger.info(f"SSE transport connected to {self.endpoint_url}")
            else:
                raise RuntimeError(f"SSE connection failed with status {self.response.status}")
                
        except Exception as e:
            logger.error(f"Failed to connect SSE transport: {e}")
            if self.session:
                await self.session.close()
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from SSE endpoint."""
        self._closed = True
        if self.response:
            self.response.close()
        if self.session:
            await self.session.close()
        self.is_connected = False
        logger.info("SSE transport disconnected")
    
    async def send_message(self, message: Union[JSONRPCRequest, JSONRPCResponse, JSONRPCNotification]) -> None:
        """Send a message through SSE (requires separate HTTP endpoint)."""
        if not self.is_connected or not self.session:
            raise RuntimeError("SSE transport not connected")
        
        try:
            # For SSE, we need to send via HTTP POST to a separate endpoint
            send_url = self.endpoint_url.replace('/events', '/send')
            message_data = serialize_mcp_message(message)
            
            async with self.session.post(
                send_url,
                json=json.loads(message_data),
                headers={'Content-Type': 'application/json'}
            ) as response:
                if response.status != 200:
                    raise RuntimeError(f"Failed to send message: {response.status}")
                    
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise
    
    async def receive_messages(self) -> AsyncGenerator[Union[JSONRPCRequest, JSONRPCResponse, JSONRPCNotification], None]:
        """Receive messages from SSE stream."""
        if not self.is_connected or not self.response:
            raise RuntimeError("SSE transport not connected")
        
        try:
            async for line in self.response.content:
                line_str = line.decode().strip()
                
                # Parse SSE format
                if line_str.startswith('data: '):
                    data = line_str[6:]  # Remove 'data: ' prefix
                    
                    if data == '[DONE]':
                        break
                    
                    try:
                        message = parse_mcp_message(data)
                        yield message
                        
                    except Exception as e:
                        logger.error(f"Failed to parse SSE message: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error receiving SSE messages: {e}")
            raise

# --- Transport Factory ---

class TransportFactory:
    """Factory for creating MCP transports."""
    
    @staticmethod
    def create_transport(transport_type: str, **kwargs) -> MCPTransport:
        """Create a transport instance."""
        if transport_type == "stdio":
            return STDIOTransport()
        elif transport_type == "websocket":
            uri = kwargs.get("uri")
            if not uri:
                raise ValueError("WebSocket transport requires 'uri' parameter")
            return WebSocketTransport(uri)
        elif transport_type == "sse":
            endpoint_url = kwargs.get("endpoint_url")
            if not endpoint_url:
                raise ValueError("SSE transport requires 'endpoint_url' parameter")
            return SSETransport(endpoint_url)
        else:
            raise ValueError(f"Unknown transport type: {transport_type}")

# --- Transport Manager ---

class TransportManager:
    """Manager for MCP transport connections."""
    
    def __init__(self):
        self.transports: Dict[str, MCPTransport] = {}
        self.active_tasks: Dict[str, asyncio.Task] = {}
    
    async def add_transport(self, name: str, transport: MCPTransport) -> None:
        """Add and connect a transport."""
        try:
            await transport.connect()
            self.transports[name] = transport
            
            # Start message handling task
            task = asyncio.create_task(self._handle_transport_messages(name, transport))
            self.active_tasks[name] = task
            
            logger.info(f"Transport '{name}' added and connected")
            
        except Exception as e:
            logger.error(f"Failed to add transport '{name}': {e}")
            raise
    
    async def remove_transport(self, name: str) -> None:
        """Remove and disconnect a transport."""
        if name in self.transports:
            # Cancel message handling task
            if name in self.active_tasks:
                self.active_tasks[name].cancel()
                try:
                    await self.active_tasks[name]
                except asyncio.CancelledError:
                    pass
                del self.active_tasks[name]
            
            # Disconnect transport
            await self.transports[name].disconnect()
            del self.transports[name]
            
            logger.info(f"Transport '{name}' removed")
    
    async def send_message(self, transport_name: str, message: Union[JSONRPCRequest, JSONRPCResponse, JSONRPCNotification]) -> None:
        """Send a message through a specific transport."""
        if transport_name not in self.transports:
            raise ValueError(f"Transport '{transport_name}' not found")
        
        await self.transports[transport_name].send_message(message)
    
    async def broadcast_message(self, message: Union[JSONRPCRequest, JSONRPCResponse, JSONRPCNotification]) -> None:
        """Broadcast a message to all connected transports."""
        for name, transport in self.transports.items():
            try:
                await transport.send_message(message)
            except Exception as e:
                logger.error(f"Failed to send message to transport '{name}': {e}")
    
    async def _handle_transport_messages(self, name: str, transport: MCPTransport) -> None:
        """Handle messages from a transport."""
        try:
            async for message in transport.receive_messages():
                await transport.handle_message(message)
                
        except asyncio.CancelledError:
            logger.info(f"Message handling cancelled for transport '{name}'")
        except Exception as e:
            logger.error(f"Error handling messages from transport '{name}': {e}")
    
    async def close_all(self) -> None:
        """Close all transports."""
        for name in list(self.transports.keys()):
            await self.remove_transport(name)
