"""MCP tool management and registry."""

import asyncio
from typing import Any, Dict, List, Optional

from ..config import MCPTool
from .client import MCPClient


class ToolRegistry:
    """Registry for managing MCP tools."""
    
    def __init__(self):
        """Initialize tool registry."""
        self.client = MCPClient()
        self.enabled_tools: Dict[str, MCPTool] = {}
        self.available_tools: Dict[str, Dict[str, Any]] = {}
    
    async def initialize(self, tool_configs: List[MCPTool]) -> None:
        """Initialize the registry with tool configurations.
        
        Args:
            tool_configs: List of MCP tool configurations
        """
        await self.client.start()
        
        # Connect to enabled tools
        for config in tool_configs:
            if config.enabled:
                success = await self.connect_tool(config)
                if success:
                    self.enabled_tools[config.name] = config
    
    async def shutdown(self) -> None:
        """Shutdown the tool registry."""
        await self.client.stop()
        self.enabled_tools.clear()
        self.available_tools.clear()
    
    async def connect_tool(self, tool_config: MCPTool) -> bool:
        """Connect to a specific tool.
        
        Args:
            tool_config: Tool configuration
            
        Returns:
            True if connection successful
        """
        config_dict = {
            "name": tool_config.name,
            "path": tool_config.path,
            "config": tool_config.config
        }
        
        success = await self.client.connect_tool(config_dict)
        if success:
            # Update available tools
            await self.refresh_available_tools()
        
        return success
    
    async def disconnect_tool(self, tool_name: str) -> None:
        """Disconnect from a tool.
        
        Args:
            tool_name: Name of the tool to disconnect
        """
        await self.client.disconnect_tool(tool_name)
        if tool_name in self.enabled_tools:
            del self.enabled_tools[tool_name]
        await self.refresh_available_tools()
    
    async def refresh_available_tools(self) -> None:
        """Refresh the list of available tools."""
        tools = await self.client.list_tools()
        self.available_tools = {tool["name"]: tool for tool in tools}
    
    async def enable_tool(self, tool_name: str) -> bool:
        """Enable a tool.
        
        Args:
            tool_name: Name of the tool to enable
            
        Returns:
            True if tool was enabled
        """
        if tool_name in self.enabled_tools:
            tool_config = self.enabled_tools[tool_name]
            tool_config.enabled = True
            return await self.connect_tool(tool_config)
        return False
    
    async def disable_tool(self, tool_name: str) -> None:
        """Disable a tool.
        
        Args:
            tool_name: Name of the tool to disable
        """
        if tool_name in self.enabled_tools:
            self.enabled_tools[tool_name].enabled = False
            await self.disconnect_tool(tool_name)
    
    def get_enabled_tools(self) -> List[str]:
        """Get list of enabled tool names.
        
        Returns:
            List of enabled tool names
        """
        return list(self.enabled_tools.keys())
    
    def get_available_tools(self) -> Dict[str, Dict[str, Any]]:
        """Get all available tools with their information.
        
        Returns:
            Dictionary of tool information by name
        """
        return self.available_tools.copy()
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> tuple[bool, Any]:
        """Call a tool.
        
        Args:
            tool_name: Full tool name (server.tool)
            arguments: Tool arguments
            
        Returns:
            Tuple of (success, result)
        """
        return await self.client.call_tool(tool_name, arguments)
    
    def format_tools_for_llm(self, selected_tools: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Format tools for LLM function calling.
        
        Args:
            selected_tools: Optional list of specific tools to include
            
        Returns:
            List of tool definitions in OpenAI function format
        """
        all_tools = self.client.format_tools_for_llm()
        
        if selected_tools:
            # Filter to only selected tools
            return [
                tool for tool in all_tools
                if tool["function"]["name"] in selected_tools
            ]
        
        return all_tools