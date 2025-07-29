"""Base class for AI model providers."""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional

from pydantic import BaseModel


class Message(BaseModel):
    """Message model for chat conversations."""
    
    role: str  # "user", "assistant", "system"
    content: str
    metadata: Optional[Dict[str, Any]] = None


class ModelResponse(BaseModel):
    """Response from an AI model."""
    
    content: str
    model: str
    provider: str
    metadata: Optional[Dict[str, Any]] = None
    usage: Optional[Dict[str, int]] = None


class ModelProvider(ABC):
    """Abstract base class for AI model providers."""
    
    def __init__(self, api_key: str, endpoint: Optional[str] = None, **kwargs):
        """Initialize the model provider.
        
        Args:
            api_key: API key for authentication
            endpoint: Optional custom API endpoint
            **kwargs: Additional provider-specific configuration
        """
        self.api_key = api_key
        self.endpoint = endpoint
        self.timeout = kwargs.get("timeout", 30)
        self.max_retries = kwargs.get("max_retries", 3)
    
    @abstractmethod
    async def list_models(self) -> List[str]:
        """List available models from the provider.
        
        Returns:
            List of model identifiers
        """
        pass
    
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Message],
        model: str,
        stream: bool = True,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> AsyncIterator[ModelResponse]:
        """Generate a chat completion.
        
        Args:
            messages: List of conversation messages
            model: Model identifier to use
            stream: Whether to stream the response
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            tools: Optional list of tools/functions available
            **kwargs: Additional provider-specific parameters
            
        Yields:
            Model response chunks if streaming, single response otherwise
        """
        pass
    
    @abstractmethod
    async def validate_api_key(self) -> bool:
        """Validate the API key.
        
        Returns:
            True if API key is valid, False otherwise
        """
        pass
    
    async def retry_with_backoff(self, func, *args, **kwargs):
        """Retry a function with exponential backoff.
        
        Args:
            func: Async function to retry
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
            
        Returns:
            Result from func
            
        Raises:
            Last exception if all retries fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    await asyncio.sleep(wait_time)
                    continue
                raise
        
        raise last_exception