"""AI model provider integrations."""

from typing import Dict, Type

from .base import Message, ModelProvider, ModelResponse
from .claude import ClaudeProvider
from .gemini import GeminiProvider
from .openai import OpenAIProvider

# Provider registry
PROVIDERS: Dict[str, Type[ModelProvider]] = {
    "openai": OpenAIProvider,
    "claude": ClaudeProvider,
    "gemini": GeminiProvider,
}


def get_provider(provider_name: str, **kwargs) -> ModelProvider:
    """Get a model provider instance.
    
    Args:
        provider_name: Name of the provider (openai, claude, gemini)
        **kwargs: Provider configuration (api_key, endpoint, etc.)
        
    Returns:
        Initialized provider instance
        
    Raises:
        ValueError: If provider is not supported
    """
    provider_class = PROVIDERS.get(provider_name.lower())
    if not provider_class:
        raise ValueError(f"Unsupported provider: {provider_name}")
    
    return provider_class(**kwargs)


__all__ = [
    "ModelProvider",
    "Message",
    "ModelResponse",
    "OpenAIProvider",
    "ClaudeProvider", 
    "GeminiProvider",
    "get_provider",
    "PROVIDERS",
]