"""MCP (Model Context Protocol) client implementation."""

import asyncio
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPClient:
    """Client for managing MCP tool connections."""
    
    def __init__(self):
        """Initialize MCP client."""
        self.sessions: Dict[str, ClientSession] = {}
        self.tools: Dict[str, Dict[str, Any]] = {}
        self._running = False
    
    async def start(self) -> None:
        """Start the MCP client."""
        self._running = True
    
    async def stop(self) -> None:
        """Stop the MCP client and close all sessions."""
        self._running = False
        for session in self.sessions.values():
            if hasattr(session, 'close'):
                await session.close()
        self.sessions.clear()
        self.tools.clear()
    
    async def connect_tool(self, tool_config: Dict[str, Any]) -> bool:
        """Connect to an MCP tool.
        
        Args:
            tool_config: Tool configuration with name, path, and config
            
        Returns:
            True if connection successful, False otherwise
        """
        tool_name = tool_config["name"]
        tool_path = Path(tool_config["path"]).expanduser()
        
        if not tool_path.exists():
            return False
        
        try:
            # Create server parameters
            server_params = StdioServerParameters(
                command=str(tool_path),
                args=tool_config.get("args", []),
                env=tool_config.get("env", {})
            )
            
            # Connect to the tool
            async with stdio_client(server_params) as (read, write):
                session = ClientSession(read, write)
                await session.initialize()
                
                # Store session
                self.sessions[tool_name] = session
                
                # Get available tools from this server
                tools_response = await session.list_tools()
                for tool in tools_response.tools:
                    self.tools[f"{tool_name}.{tool.name}"] = {
                        "description": tool.description,
                        "input_schema": tool.inputSchema,
                        "server": tool_name,
                        "original_name": tool.name
                    }
                
                return True
                
        except Exception as e:
            print(f"Failed to connect to tool {tool_name}: {e}")
            return False
    
    async def disconnect_tool(self, tool_name: str) -> None:
        """Disconnect from an MCP tool.
        
        Args:
            tool_name: Name of the tool to disconnect
        """
        if tool_name in self.sessions:
            session = self.sessions.pop(tool_name)
            if hasattr(session, 'close'):
                await session.close()
            
            # Remove tools from this server
            tools_to_remove = [
                key for key in self.tools.keys()
                if key.startswith(f"{tool_name}.")
            ]
            for key in tools_to_remove:
                del self.tools[key]
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools.
        
        Returns:
            List of tool information
        """
        return [
            {
                "name": name,
                "description": info["description"],
                "input_schema": info["input_schema"],
                "server": info["server"]
            }
            for name, info in self.tools.items()
        ]
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Tuple[bool, Any]:
        """Call an MCP tool.
        
        Args:
            tool_name: Full tool name (server.tool)
            arguments: Tool arguments
            
        Returns:
            Tuple of (success, result)
        """
        if tool_name not in self.tools:
            return False, f"Tool not found: {tool_name}"
        
        tool_info = self.tools[tool_name]
        server_name = tool_info["server"]
        original_name = tool_info["original_name"]
        
        if server_name not in self.sessions:
            return False, f"Server not connected: {server_name}"
        
        try:
            session = self.sessions[server_name]
            result = await session.call_tool(original_name, arguments)
            
            # Extract content from result
            if hasattr(result, 'content'):
                if isinstance(result.content, list):
                    # Combine text content
                    text_parts = []
                    for item in result.content:
                        if hasattr(item, 'text'):
                            text_parts.append(item.text)
                    return True, "\n".join(text_parts)
                else:
                    return True, str(result.content)
            else:
                return True, str(result)
                
        except Exception as e:
            return False, f"Tool execution error: {str(e)}"
    
    def format_tools_for_llm(self) -> List[Dict[str, Any]]:
        """Format tools for LLM function calling.
        
        Returns:
            List of tool definitions in OpenAI function format
        """
        formatted_tools = []
        
        for name, info in self.tools.items():
            formatted_tools.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": info["description"],
                    "parameters": info["input_schema"] or {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            })
        
        return formatted_tools