"""Configuration schema definitions using Pydantic."""

from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator


class ModelConfig(BaseModel):
    """Configuration for an AI model provider."""
    
    api_key: str = Field(description="API key for the provider")
    endpoint: Optional[str] = Field(None, description="Custom API endpoint")
    default_model: str = Field(description="Default model to use")
    timeout: int = Field(30, description="Request timeout in seconds")
    max_retries: int = Field(3, description="Maximum number of retries")
    
    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate API key is not empty."""
        if not v or v == "YOUR_API_KEY_HERE":
            raise ValueError("API key must be configured")
        return v


class MCPTool(BaseModel):
    """Configuration for an MCP tool."""
    
    name: str = Field(description="Tool name")
    path: str = Field(description="Path to tool executable or module")
    enabled: bool = Field(True, description="Whether tool is enabled")
    config: Dict[str, Any] = Field(default_factory=dict, description="Tool-specific configuration")
    
    @field_validator("path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        """Validate tool path exists."""
        path = Path(v).expanduser()
        if not path.exists():
            raise ValueError(f"Tool path does not exist: {v}")
        return str(path)


class UIConfig(BaseModel):
    """UI configuration settings."""
    
    theme: str = Field("dark", description="UI theme")
    editor: Optional[str] = Field(None, description="External editor command")
    diff_syntax_highlighting: bool = Field(True, description="Enable syntax highlighting in diffs")
    max_response_lines: int = Field(1000, description="Maximum lines to show in response")
    autosave_interval: int = Field(60, description="Autosave interval in seconds")


class DatabaseConfig(BaseModel):
    """Database configuration settings."""
    
    path: Optional[str] = Field(None, description="Database file path")
    backup_on_startup: bool = Field(True, description="Create backup on startup")
    vacuum_on_startup: bool = Field(False, description="Vacuum database on startup")


class Settings(BaseModel):
    """Main application settings."""
    
    models: Dict[str, ModelConfig] = Field(
        default_factory=dict,
        description="AI model provider configurations"
    )
    mcp_tools: list[MCPTool] = Field(
        default_factory=list,
        description="MCP tool configurations"
    )
    ui: UIConfig = Field(
        default_factory=UIConfig,
        description="UI settings"
    )
    database: DatabaseConfig = Field(
        default_factory=DatabaseConfig,
        description="Database settings"
    )
    debug: bool = Field(False, description="Enable debug mode")
    
    @field_validator("models")
    @classmethod
    def validate_models(cls, v: Dict[str, ModelConfig]) -> Dict[str, ModelConfig]:
        """Ensure at least one model is configured."""
        if not v:
            raise ValueError("At least one model provider must be configured")
        return v
    
    class Config:
        """Pydantic configuration."""
        
        validate_assignment = True
        use_enum_values = True