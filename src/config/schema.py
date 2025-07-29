"""Configuration schema definitions using Pydantic."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, SecretStr, HttpUrl


class ModelProviderConfig(BaseModel):
    """Configuration for an AI model provider."""
    
    api_key: SecretStr = Field(..., description="API key for the provider")
    endpoint: HttpUrl = Field(..., description="API endpoint URL")
    default_model: str = Field(..., description="Default model to use")
    timeout: int = Field(30, description="Request timeout in seconds")
    max_retries: int = Field(3, description="Maximum number of retries")
    

class OpenAIConfig(ModelProviderConfig):
    """OpenAI-specific configuration."""
    
    endpoint: HttpUrl = Field(
        default="https://api.openai.com/v1",
        description="OpenAI API endpoint"
    )
    default_model: str = Field(
        default="gpt-4",
        description="Default OpenAI model"
    )
    organization_id: Optional[str] = Field(
        None,
        description="OpenAI organization ID"
    )


class ClaudeConfig(ModelProviderConfig):
    """Anthropic Claude-specific configuration."""
    
    endpoint: HttpUrl = Field(
        default="https://api.anthropic.com/v1",
        description="Anthropic API endpoint"
    )
    default_model: str = Field(
        default="claude-3-opus-20240229",
        description="Default Claude model"
    )
    max_tokens_to_sample: int = Field(
        1000,
        description="Maximum tokens to generate"
    )


class GeminiConfig(ModelProviderConfig):
    """Google Gemini-specific configuration."""
    
    endpoint: HttpUrl = Field(
        default="https://generativelanguage.googleapis.com/v1",
        description="Google API endpoint"
    )
    default_model: str = Field(
        default="gemini-pro",
        description="Default Gemini model"
    )


class MCPToolConfig(BaseModel):
    """Configuration for an MCP tool."""
    
    name: str = Field(..., description="Tool name")
    path: str = Field(..., description="Path to tool executable")
    enabled: bool = Field(True, description="Whether tool is enabled by default")
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Tool-specific configuration"
    )


class UIConfig(BaseModel):
    """UI configuration settings."""
    
    theme: str = Field("dark", description="UI theme (dark/light)")
    editor: Optional[str] = Field(None, description="External editor command")
    diff_syntax_highlighting: bool = Field(
        True,
        description="Enable syntax highlighting in diff view"
    )
    max_conversation_display: int = Field(
        1000,
        description="Maximum messages to display in conversation"
    )
    keybindings_mode: str = Field(
        "vi",
        description="Keybinding mode (vi/emacs)"
    )


class DatabaseConfig(BaseModel):
    """Database configuration."""
    
    path: str = Field(
        "~/.local/share/promptriff/promptriff.db",
        description="Database file path"
    )
    backup_on_startup: bool = Field(
        True,
        description="Create backup on startup"
    )
    vacuum_interval_days: int = Field(
        7,
        description="Days between database vacuum operations"
    )


class Config(BaseModel):
    """Main configuration schema."""
    
    models: Dict[str, ModelProviderConfig] = Field(
        default_factory=dict,
        description="Model provider configurations"
    )
    mcp_tools: List[MCPToolConfig] = Field(
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
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            SecretStr: lambda v: v.get_secret_value() if v else None
        }