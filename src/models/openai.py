"""OpenAI model provider implementation."""

import json
from typing import List, Dict, Any, Optional, AsyncIterator
from .base import (
    BaseModelProvider, ModelInfo, ChatMessage, ChatCompletionChunk,
    APIError, RateLimitError
)


class OpenAIProvider(BaseModelProvider):
    """OpenAI API provider implementation."""
    
    # Available models as of early 2024
    MODELS = {
        "gpt-4-turbo-preview": ModelInfo(
            id="gpt-4-turbo-preview",
            name="GPT-4 Turbo Preview",
            description="Most capable GPT-4 model with 128k context",
            context_window=128000,
            max_output_tokens=4096,
            supports_streaming=True,
            supports_functions=True
        ),
        "gpt-4": ModelInfo(
            id="gpt-4",
            name="GPT-4",
            description="Most capable model for complex tasks",
            context_window=8192,
            max_output_tokens=4096,
            supports_streaming=True,
            supports_functions=True
        ),
        "gpt-4-32k": ModelInfo(
            id="gpt-4-32k",
            name="GPT-4 32K",
            description="GPT-4 with extended context window",
            context_window=32768,
            max_output_tokens=4096,
            supports_streaming=True,
            supports_functions=True
        ),
        "gpt-3.5-turbo": ModelInfo(
            id="gpt-3.5-turbo",
            name="GPT-3.5 Turbo",
            description="Fast and efficient model",
            context_window=16384,
            max_output_tokens=4096,
            supports_streaming=True,
            supports_functions=True
        ),
        "gpt-3.5-turbo-16k": ModelInfo(
            id="gpt-3.5-turbo-16k",
            name="GPT-3.5 Turbo 16K",
            description="GPT-3.5 with extended context",
            context_window=16384,
            max_output_tokens=4096,
            supports_streaming=True,
            supports_functions=True
        )
    }
    
    def __init__(
        self,
        api_key: str,
        endpoint: str = "https://api.openai.com/v1",
        organization_id: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3
    ):
        """Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            endpoint: API endpoint URL
            organization_id: Optional organization ID
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        super().__init__(api_key, endpoint, timeout, max_retries)
        self.organization_id = organization_id
        
    def get_headers(self) -> Dict[str, str]:
        """Get headers for OpenAI API requests."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        if self.organization_id:
            headers["OpenAI-Organization"] = self.organization_id
        return headers
    
    async def list_models(self) -> List[ModelInfo]:
        """List available OpenAI models.
        
        Returns:
            List of available models.
        """
        # For now, return hardcoded list. Could fetch from API.
        return list(self.MODELS.values())
    
    async def complete(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = True,
        **kwargs
    ) -> AsyncIterator[ChatCompletionChunk]:
        """Generate a chat completion using OpenAI API.
        
        Args:
            messages: List of messages in the conversation
            model: Model to use for completion
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            **kwargs: Additional OpenAI-specific parameters
            
        Yields:
            Chat completion chunks.
        """
        # Prepare request data
        data = {
            "model": model,
            "messages": self._prepare_messages(messages),
            "temperature": temperature,
            "stream": stream
        }
        
        if max_tokens:
            data["max_tokens"] = max_tokens
            
        # Add any additional parameters
        for key in ["top_p", "n", "stop", "presence_penalty", "frequency_penalty",
                    "logit_bias", "user", "functions", "function_call"]:
            if key in kwargs:
                data[key] = kwargs[key]
        
        # Make the request
        async for chunk in self._stream_request(data):
            yield chunk
    
    async def _stream_request(
        self,
        data: Dict[str, Any]
    ) -> AsyncIterator[ChatCompletionChunk]:
        """Make a streaming request to OpenAI API.
        
        Args:
            data: Request data
            
        Yields:
            Chat completion chunks.
        """
        url = f"{self.endpoint}/chat/completions"
        
        async def _make_request():
            async with self.session.post(
                url,
                headers=self.get_headers(),
                json=data
            ) as response:
                if response.status == 429:
                    retry_after = response.headers.get("Retry-After")
                    retry_after = int(retry_after) if retry_after else None
                    raise RateLimitError(
                        "Rate limit exceeded",
                        retry_after=retry_after
                    )
                elif response.status >= 400:
                    error_text = await response.text()
                    raise APIError(
                        f"OpenAI API error: {error_text}",
                        status_code=response.status
                    )
                
                if data.get("stream"):
                    # Handle streaming response
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line.startswith("data: "):
                            line = line[6:]  # Remove "data: " prefix
                            
                            if line == "[DONE]":
                                break
                                
                            try:
                                chunk_data = json.loads(line)
                                delta = chunk_data["choices"][0]["delta"]
                                
                                if "content" in delta:
                                    yield ChatCompletionChunk(
                                        content=delta["content"],
                                        finish_reason=chunk_data["choices"][0].get("finish_reason"),
                                        metadata={
                                            "model": chunk_data.get("model"),
                                            "id": chunk_data.get("id")
                                        }
                                    )
                            except json.JSONDecodeError:
                                # Skip invalid JSON lines
                                continue
                else:
                    # Handle non-streaming response
                    response_data = await response.json()
                    content = response_data["choices"][0]["message"]["content"]
                    finish_reason = response_data["choices"][0]["finish_reason"]
                    
                    yield ChatCompletionChunk(
                        content=content,
                        finish_reason=finish_reason,
                        metadata={
                            "model": response_data.get("model"),
                            "id": response_data.get("id"),
                            "usage": response_data.get("usage")
                        }
                    )
        
        # Execute with retry logic
        async for chunk in self._retry_with_backoff(_make_request):
            yield chunk