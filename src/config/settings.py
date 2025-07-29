"""Configuration management with environment variable support."""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Union
import yaml
from pydantic import ValidationError, SecretStr
from dotenv import load_dotenv

from .schema import (
    Config, OpenAIConfig, ClaudeConfig, GeminiConfig,
    MCPToolConfig, UIConfig, DatabaseConfig
)


# Load .env file if it exists
load_dotenv()


class ConfigurationError(Exception):
    """Configuration related errors."""
    pass


class Settings:
    """Application settings manager with environment variable override support."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize settings.
        
        Args:
            config_path: Path to configuration file. If None, uses default location.
        """
        self.config_path = config_path or self._get_default_config_path()
        self._config: Optional[Config] = None
        self._env_prefix = "PROMPTRIFF_"
        
    @staticmethod
    def _get_default_config_path() -> Path:
        """Get default configuration file path."""
        config_dir = Path.home() / ".config" / "promptriff"
        return config_dir / "config.yaml"
    
    @staticmethod
    def _expand_path(path: str) -> str:
        """Expand user home directory and environment variables in path."""
        return os.path.expandvars(os.path.expanduser(path))
    
    def _load_yaml_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            return {}
            
        try:
            with open(self.config_path, 'r') as f:
                content = f.read()
                # Expand environment variables in YAML content
                expanded_content = os.path.expandvars(content)
                return yaml.safe_load(expanded_content) or {}
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Failed to parse config file: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load config file: {e}")
    
    def _apply_env_overrides(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides to configuration."""
        # Model provider API keys
        if "OPENAI_API_KEY" in os.environ:
            config_dict.setdefault("models", {}).setdefault("openai", {})
            config_dict["models"]["openai"]["api_key"] = os.environ["OPENAI_API_KEY"]
            
        if "ANTHROPIC_API_KEY" in os.environ:
            config_dict.setdefault("models", {}).setdefault("claude", {})
            config_dict["models"]["claude"]["api_key"] = os.environ["ANTHROPIC_API_KEY"]
            
        if "GOOGLE_API_KEY" in os.environ:
            config_dict.setdefault("models", {}).setdefault("gemini", {})
            config_dict["models"]["gemini"]["api_key"] = os.environ["GOOGLE_API_KEY"]
        
        # UI settings
        if "EDITOR" in os.environ:
            config_dict.setdefault("ui", {})["editor"] = os.environ["EDITOR"]
            
        # Apply PROMPTRIFF_ prefixed overrides
        for key, value in os.environ.items():
            if key.startswith(self._env_prefix):
                self._apply_env_var(key, value, config_dict)
                
        return config_dict
    
    def _apply_env_var(self, key: str, value: str, config_dict: Dict[str, Any]):
        """Apply a single environment variable to config dict."""
        # Remove prefix and convert to lowercase
        path = key[len(self._env_prefix):].lower().split('__')
        
        # Navigate to the correct position in config dict
        current = config_dict
        for part in path[:-1]:
            current = current.setdefault(part, {})
            
        # Set the value
        current[path[-1]] = self._parse_env_value(value)
    
    @staticmethod
    def _parse_env_value(value: str) -> Union[str, int, bool]:
        """Parse environment variable value to appropriate type."""
        # Try to parse as boolean
        if value.lower() in ('true', 'yes', '1'):
            return True
        elif value.lower() in ('false', 'no', '0'):
            return False
            
        # Try to parse as integer
        try:
            return int(value)
        except ValueError:
            pass
            
        # Return as string
        return value
    
    def _create_provider_config(self, provider: str, config: dict):
        """Create provider-specific configuration object."""
        if provider == "openai":
            return OpenAIConfig(**config)
        elif provider == "claude":
            return ClaudeConfig(**config)
        elif provider == "gemini":
            return GeminiConfig(**config)
        else:
            raise ConfigurationError(f"Unknown model provider: {provider}")
    
    def load(self) -> Config:
        """Load configuration from file and environment variables.
        
        Returns:
            Loaded configuration object.
            
        Raises:
            ConfigurationError: If configuration is invalid.
        """
        if self._config is not None:
            return self._config
            
        # Load from YAML file
        config_dict = self._load_yaml_config()
        
        # Apply environment variable overrides
        config_dict = self._apply_env_overrides(config_dict)
        
        # Process model provider configs
        if "models" in config_dict:
            for provider, provider_config in config_dict["models"].items():
                if isinstance(provider_config, dict):
                    config_dict["models"][provider] = self._create_provider_config(
                        provider, provider_config
                    )
        
        # Expand paths
        if "database" in config_dict and "path" in config_dict["database"]:
            config_dict["database"]["path"] = self._expand_path(
                config_dict["database"]["path"]
            )
            
        # Create configuration object
        try:
            self._config = Config(**config_dict)
            return self._config
        except ValidationError as e:
            raise ConfigurationError(f"Invalid configuration: {e}")
    
    def save_example(self, path: Optional[Path] = None):
        """Save an example configuration file.
        
        Args:
            path: Path to save example config. Defaults to examples/config.example.yaml
        """
        if path is None:
            path = Path("examples/config.example.yaml")
            
        example_config = {
            "models": {
                "openai": {
                    "api_key": "${OPENAI_API_KEY}",
                    "endpoint": "https://api.openai.com/v1",
                    "default_model": "gpt-4"
                },
                "claude": {
                    "api_key": "${ANTHROPIC_API_KEY}",
                    "endpoint": "https://api.anthropic.com/v1",
                    "default_model": "claude-3-opus-20240229"
                },
                "gemini": {
                    "api_key": "${GOOGLE_API_KEY}",
                    "endpoint": "https://generativelanguage.googleapis.com/v1",
                    "default_model": "gemini-pro"
                }
            },
            "mcp_tools": [
                {
                    "name": "example_tool",
                    "path": "/path/to/tool",
                    "enabled": True,
                    "config": {}
                }
            ],
            "ui": {
                "theme": "dark",
                "editor": "$EDITOR",
                "diff_syntax_highlighting": True
            },
            "database": {
                "path": "~/.local/share/promptriff/promptriff.db",
                "backup_on_startup": True
            }
        }
        
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            yaml.dump(example_config, f, default_flow_style=False, sort_keys=False)
    
    def get_model_config(self, provider: str) -> Optional[Any]:
        """Get configuration for a specific model provider.
        
        Args:
            provider: Provider name (openai, claude, gemini)
            
        Returns:
            Provider configuration or None if not configured.
        """
        config = self.load()
        return config.models.get(provider)
    
    def is_provider_configured(self, provider: str) -> bool:
        """Check if a provider is configured with an API key.
        
        Args:
            provider: Provider name
            
        Returns:
            True if provider is configured with API key.
        """
        provider_config = self.get_model_config(provider)
        if not provider_config:
            return False
            
        # Check if API key is set and not empty
        api_key = provider_config.api_key
        if isinstance(api_key, SecretStr):
            return bool(api_key.get_secret_value())
        return bool(api_key)
    
    def get_configured_providers(self) -> list[str]:
        """Get list of configured providers.
        
        Returns:
            List of provider names that have API keys configured.
        """
        config = self.load()
        providers = []
        
        for provider_name, provider_config in config.models.items():
            if self.is_provider_configured(provider_name):
                providers.append(provider_name)
                
        return providers


# Global settings instance
settings = Settings()