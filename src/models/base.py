"""Base AI model provider interface."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncIterator
from dataclasses import dataclass
import asyncio
from datetime import datetime
import aiohttp


@dataclass
class ModelInfo:
    """Information about an available model."""
    
    id: str
    name: str
    description: Optional[str] = None
    context_window: Optional[int] = None
    max_output_tokens: Optional[int] = None
    supports_streaming: bool = True
    supports_functions: bool = False
    

@dataclass
class ChatMessage:
    """A message in a chat conversation."""
    
    role: str  # "user", "assistant", "system"
    content: str
    metadata: Optional[Dict[str, Any]] = None
    

@dataclass
class ChatCompletionChunk:
    """A chunk of streaming chat completion."""
    
    content: str
    finish_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    

@dataclass
class ChatCompletion:
    """A complete chat response."""
    
    content: str
    finish_reason: Optional[str] = None
    model: str = ""
    usage: Optional[Dict[str, int]] = None
    metadata: Optional[Dict[str, Any]] = None


class RateLimitError(Exception):
    """Rate limit exceeded error."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


class APIError(Exception):
    """General API error."""
    
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class BaseModelProvider(ABC):
    """Abstract base class for AI model providers."""
    
    def __init__(
        self,
        api_key: str,
        endpoint: str,
        timeout: int = 30,
        max_retries: int = 3
    ):
        """Initialize the model provider.
        
        Args:
            api_key: API key for authentication
            endpoint: API endpoint URL
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.api_key = api_key
        self.endpoint = endpoint.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self._session: Optional[aiohttp.ClientSession] = None
        
    @property
    def session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    async def close(self):
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    @abstractmethod
    async def list_models(self) -> List[ModelInfo]:
        """List available models.
        
        Returns:
            List of available models.
        """
        pass
    
    @abstractmethod
    async def complete(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = True,
        **kwargs
    ) -> AsyncIterator[ChatCompletionChunk]:
        """Generate a chat completion.
        
        Args:
            messages: List of messages in the conversation
            model: Model to use for completion
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            **kwargs: Provider-specific parameters
            
        Yields:
            Chat completion chunks if streaming, single chunk if not.
        """
        pass
    
    async def complete_sync(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ChatCompletion:
        """Generate a non-streaming chat completion.
        
        Args:
            messages: List of messages in the conversation
            model: Model to use for completion
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific parameters
            
        Returns:
            Complete chat response.
        """
        chunks = []
        async for chunk in self.complete(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
            **kwargs
        ):
            chunks.append(chunk)
            
        if not chunks:
            raise APIError("No response received from model")
            
        # Combine chunks
        content = "".join(chunk.content for chunk in chunks)
        finish_reason = chunks[-1].finish_reason if chunks else None
        metadata = chunks[-1].metadata if chunks else {}
        
        return ChatCompletion(
            content=content,
            finish_reason=finish_reason,
            model=model,
            metadata=metadata
        )
    
    async def _retry_with_backoff(
        self,
        func,
        *args,
        **kwargs
    ):
        """Execute a function with exponential backoff retry.
        
        Args:
            func: Async function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
            
        Returns:
            Result of func
            
        Raises:
            Last exception if all retries fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except RateLimitError as e:
                last_exception = e
                # Use retry_after if provided, otherwise exponential backoff
                wait_time = e.retry_after or (2 ** attempt)
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(wait_time)
            except APIError as e:
                last_exception = e
                # Only retry on certain status codes
                if e.status_code and e.status_code >= 500:
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                else:
                    raise
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_exception = APIError(f"Network error: {str(e)}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    
        raise last_exception or APIError("All retry attempts failed")
    
    def _prepare_messages(self, messages: List[ChatMessage]) -> List[Dict[str, Any]]:
        """Prepare messages for API request.
        
        Args:
            messages: List of chat messages
            
        Returns:
            List of message dictionaries for API
        """
        return [
            {
                "role": msg.role,
                "content": msg.content,
                **(msg.metadata or {})
            }
            for msg in messages
        ]
    
    @abstractmethod
    def get_headers(self) -> Dict[str, str]:
        """Get headers for API requests.
        
        Returns:
            Dictionary of headers.
        """
        pass