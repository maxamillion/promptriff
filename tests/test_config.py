"""Tests for configuration management."""

import os
from pathlib import Path

import pytest
import yaml

from promptriff.config import Settings, load_settings, save_settings


def test_settings_schema():
    """Test Settings schema validation."""
    # Valid settings
    settings = Settings(
        models={
            "openai": {
                "api_key": "test-key",
                "default_model": "gpt-4"
            }
        }
    )
    assert settings.models["openai"].api_key == "test-key"
    assert settings.models["openai"].default_model == "gpt-4"
    
    # Invalid - no models
    with pytest.raises(ValueError, match="at least one model"):
        Settings(models={})
    
    # Invalid - empty API key
    with pytest.raises(ValueError, match="API key must be configured"):
        Settings(
            models={
                "openai": {
                    "api_key": "",
                    "default_model": "gpt-4"
                }
            }
        )


def test_load_settings_from_file(temp_dir: Path):
    """Test loading settings from YAML file."""
    # Create config file
    config_file = temp_dir / "config.yaml"
    config_data = {
        "models": {
            "openai": {
                "api_key": "test-key",
                "default_model": "gpt-4"
            }
        },
        "ui": {
            "theme": "light"
        }
    }
    
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)
    
    # Load settings
    settings = load_settings(str(config_file))
    
    assert settings.models["openai"].api_key == "test-key"
    assert settings.ui.theme == "light"


def test_load_settings_with_env_vars(temp_dir: Path, monkeypatch):
    """Test loading settings with environment variable expansion."""
    # Set environment variable
    monkeypatch.setenv("TEST_API_KEY", "env-api-key")
    
    # Create config file with env var reference
    config_file = temp_dir / "config.yaml"
    config_data = {
        "models": {
            "openai": {
                "api_key": "${TEST_API_KEY}",
                "default_model": "gpt-4"
            }
        }
    }
    
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)
    
    # Load settings
    settings = load_settings(str(config_file))
    
    assert settings.models["openai"].api_key == "env-api-key"


def test_env_var_overrides(monkeypatch):
    """Test environment variable overrides."""
    # Set environment variables
    monkeypatch.setenv("PROMPTRIFF_OPENAI_API_KEY", "override-key")
    monkeypatch.setenv("PROMPTRIFF_OPENAI_MODEL", "gpt-3.5-turbo")
    monkeypatch.setenv("PROMPTRIFF_THEME", "light")
    monkeypatch.setenv("PROMPTRIFF_DEBUG", "true")
    
    # Load settings without config file
    settings = load_settings("/nonexistent/config.yaml")
    
    assert settings.models["openai"].api_key == "override-key"
    assert settings.models["openai"].default_model == "gpt-3.5-turbo"
    assert settings.ui.theme == "light"
    assert settings.debug is True


def test_save_settings(temp_dir: Path):
    """Test saving settings to file."""
    settings = Settings(
        models={
            "openai": {
                "api_key": "test-key",
                "default_model": "gpt-4"
            }
        },
        ui={"theme": "dark"}
    )
    
    config_file = temp_dir / "saved_config.yaml"
    save_settings(settings, str(config_file))
    
    # Verify file was created
    assert config_file.exists()
    
    # Load and verify
    with open(config_file) as f:
        data = yaml.safe_load(f)
    
    assert data["models"]["openai"]["api_key"] == "test-key"
    assert data["ui"]["theme"] == "dark"