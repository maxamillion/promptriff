"""Settings loading and management."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv

from .schema import Settings

# Load environment variables
load_dotenv()


def get_config_dir() -> Path:
    """Get the configuration directory path."""
    config_dir = Path(os.environ.get("PROMPTRIFF_CONFIG_DIR", "~/.config/promptriff"))
    return config_dir.expanduser()


def get_data_dir() -> Path:
    """Get the data directory path."""
    data_dir = Path(os.environ.get("PROMPTRIFF_DATA_DIR", "~/.local/share/promptriff"))
    return data_dir.expanduser()


def get_cache_dir() -> Path:
    """Get the cache directory path."""
    cache_dir = Path(os.environ.get("PROMPTRIFF_CACHE_DIR", "~/.cache/promptriff"))
    return cache_dir.expanduser()


def expand_env_vars(value: Any) -> Any:
    """Recursively expand environment variables in configuration values."""
    if isinstance(value, str):
        # Expand ${VAR} or $VAR patterns
        return os.path.expandvars(value)
    elif isinstance(value, dict):
        return {k: expand_env_vars(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [expand_env_vars(item) for item in value]
    return value


def load_settings(config_path: Optional[str] = None) -> Settings:
    """Load settings from configuration file and environment variables.
    
    Args:
        config_path: Optional path to configuration file
        
    Returns:
        Loaded settings object
    """
    # Determine config file path
    if config_path:
        config_file = Path(config_path)
    else:
        config_dir = get_config_dir()
        config_file = config_dir / "config.yaml"
        
        # Try alternative locations if primary doesn't exist
        if not config_file.exists():
            for alt_path in [
                config_dir / "config.yml",
                Path.home() / ".promptriff.yaml",
                Path.home() / ".promptriff.yml",
            ]:
                if alt_path.exists():
                    config_file = alt_path
                    break
    
    # Load configuration from file if it exists
    config_data: Dict[str, Any] = {}
    if config_file.exists():
        with open(config_file, "r") as f:
            raw_data = yaml.safe_load(f) or {}
            config_data = expand_env_vars(raw_data)
    
    # Apply environment variable overrides
    env_overrides = get_env_overrides()
    config_data = merge_configs(config_data, env_overrides)
    
    # Set default database path if not specified
    if "database" not in config_data:
        config_data["database"] = {}
    if "path" not in config_data["database"]:
        data_dir = get_data_dir()
        data_dir.mkdir(parents=True, exist_ok=True)
        config_data["database"]["path"] = str(data_dir / "promptriff.db")
    
    # Create and validate settings
    settings = Settings(**config_data)
    
    return settings


def get_env_overrides() -> Dict[str, Any]:
    """Get configuration overrides from environment variables."""
    overrides: Dict[str, Any] = {}
    
    # Model provider overrides
    for provider in ["openai", "claude", "gemini"]:
        prefix = f"PROMPTRIFF_{provider.upper()}_"
        
        api_key_var = f"{prefix}API_KEY"
        if api_key_var in os.environ:
            if "models" not in overrides:
                overrides["models"] = {}
            if provider not in overrides["models"]:
                overrides["models"][provider] = {}
            overrides["models"][provider]["api_key"] = os.environ[api_key_var]
        
        endpoint_var = f"{prefix}ENDPOINT"
        if endpoint_var in os.environ:
            if "models" not in overrides:
                overrides["models"] = {}
            if provider not in overrides["models"]:
                overrides["models"][provider] = {}
            overrides["models"][provider]["endpoint"] = os.environ[endpoint_var]
        
        model_var = f"{prefix}MODEL"
        if model_var in os.environ:
            if "models" not in overrides:
                overrides["models"] = {}
            if provider not in overrides["models"]:
                overrides["models"][provider] = {}
            overrides["models"][provider]["default_model"] = os.environ[model_var]
    
    # UI overrides
    if "PROMPTRIFF_THEME" in os.environ:
        if "ui" not in overrides:
            overrides["ui"] = {}
        overrides["ui"]["theme"] = os.environ["PROMPTRIFF_THEME"]
    
    if "EDITOR" in os.environ and "ui" not in overrides:
        if "ui" not in overrides:
            overrides["ui"] = {}
        overrides["ui"]["editor"] = os.environ["EDITOR"]
    
    # Debug mode
    if "PROMPTRIFF_DEBUG" in os.environ:
        overrides["debug"] = os.environ["PROMPTRIFF_DEBUG"].lower() in ("true", "1", "yes")
    
    return overrides


def merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge configuration dictionaries."""
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value
    
    return result


def save_settings(settings: Settings, config_path: Optional[str] = None) -> None:
    """Save settings to configuration file.
    
    Args:
        settings: Settings object to save
        config_path: Optional path to save configuration to
    """
    # Determine config file path
    if config_path:
        config_file = Path(config_path)
    else:
        config_dir = get_config_dir()
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "config.yaml"
    
    # Convert settings to dictionary
    config_data = settings.model_dump(exclude_defaults=False)
    
    # Save to file
    with open(config_file, "w") as f:
        yaml.safe_dump(config_data, f, default_flow_style=False, sort_keys=False)