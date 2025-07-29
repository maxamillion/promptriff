"""Anthropic Claude model provider implementation."""

import json
from typing import List, Dict, Any, Optional, AsyncIterator
from .base import (
    BaseModelProvider, ModelInfo, ChatMessage, ChatCompletionChunk,
    APIError, RateLimitError
)


class ClaudeProvider(BaseModelProvider):
    """Anthropic Claude API provider implementation."""
    
    # Available models as of early 2024
    MODELS = {
        "claude-3-opus-20240229": ModelInfo(
            id="claude-3-opus-20240229",
            name="Claude 3 Opus",
            description="Most capable Claude model",
            context_window=200000,
            max_output_tokens=4096,
            supports_streaming=True,
            supports_functions=False
        ),
        "claude-3-sonnet-20240229": ModelInfo(
            id="claude-3-sonnet-20240229",
            name="Claude 3 Sonnet",
            description="Balanced performance and capability",
            context_window=200000,
            max_output_tokens=4096,
            supports_streaming=True,
            supports_functions=False
        ),
        "claude-3-haiku-20240307": ModelInfo(
            id="claude-3-haiku-20240307",
            name="Claude 3 Haiku",
            description="Fast and efficient model",
            context_window=200000,
            max_output_tokens=4096,
            supports_streaming=True,
            supports_functions=False
        ),
        "claude-2.1": ModelInfo(
            id="claude-2.1",
            name="Claude 2.1",
            description="Previous generation Claude",
            context_window=100000,
            max_output_tokens=4096,
            supports_streaming=True,
            supports_functions=False
        ),
        "claude-instant-1.2": ModelInfo(
            id="claude-instant-1.2",
            name="Claude Instant 1.2",
            description="Fast, affordable model",
            context_window=100000,
            max_output_tokens=4096,
            supports_streaming=True,
            supports_functions=False
        )
    }
    
    def __init__(
        self,
        api_key: str,
        endpoint: str = "https://api.anthropic.com/v1",
        max_tokens_to_sample: int = 1000,
        timeout: int = 30,
        max_retries: int = 3
    ):
        """Initialize Claude provider.
        
        Args:
            api_key: Anthropic API key
            endpoint: API endpoint URL
            max_tokens_to_sample: Default max tokens to generate
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        super().__init__(api_key, endpoint, timeout, max_retries)
        self.max_tokens_to_sample = max_tokens_to_sample
        
    def get_headers(self) -> Dict[str, str]:
        """Get headers for Anthropic API requests."""
        return {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
    
    async def list_models(self) -> List[ModelInfo]:
        """List available Claude models.
        
        Returns:
            List of available models.
        """
        # Return hardcoded list of models
        return list(self.MODELS.values())
    
    def _convert_messages_to_claude_format(
        self,
        messages: List[ChatMessage]
    ) -> tuple[Optional[str], List[Dict[str, str]]]:
        """Convert messages to Claude's expected format.
        
        Claude expects:
        - Optional system message
        - Alternating user/assistant messages
        
        Args:
            messages: List of chat messages
            
        Returns:
            Tuple of (system_message, messages)
        """
        system_message = None
        claude_messages = []
        
        for msg in messages:
            if msg.role == "system":
                # Claude only supports one system message at the beginning
                if system_message is None:
                    system_message = msg.content
            else:
                # Convert 'user' and 'assistant' messages
                claude_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # Ensure messages alternate between user and assistant
        # If first message is not from user, prepend a user message
        if claude_messages and claude_messages[0]["role"] != "user":
            claude_messages.insert(0, {
                "role": "user",
                "content": "Continue the conversation."
            })
            
        # If last message is from user, that's perfect for Claude
        # If last message is from assistant, append a user message
        if claude_messages and claude_messages[-1]["role"] == "assistant":
            claude_messages.append({
                "role": "user",
                "content": "Continue."
            })
            
        return system_message, claude_messages
    
    async def complete(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = True,
        **kwargs
    ) -> AsyncIterator[ChatCompletionChunk]:
        """Generate a chat completion using Claude API.
        
        Args:
            messages: List of messages in the conversation
            model: Model to use for completion
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            **kwargs: Additional Claude-specific parameters
            
        Yields:
            Chat completion chunks.
        """
        # Convert messages to Claude format
        system_msg, claude_messages = self._convert_messages_to_claude_format(messages)
        
        # Prepare request data
        data = {
            "model": model,
            "messages": claude_messages,
            "temperature": min(temperature, 1.0),  # Claude uses 0-1 range
            "max_tokens": max_tokens or self.max_tokens_to_sample,
            "stream": stream
        }
        
        if system_msg:
            data["system"] = system_msg
            
        # Add any additional parameters
        for key in ["top_p", "top_k", "stop_sequences", "metadata"]:
            if key in kwargs:
                data[key] = kwargs[key]
        
        # Make the request
        async for chunk in self._stream_request(data):
            yield chunk
    
    async def _stream_request(
        self,
        data: Dict[str, Any]
    ) -> AsyncIterator[ChatCompletionChunk]:
        """Make a streaming request to Claude API.
        
        Args:
            data: Request data
            
        Yields:
            Chat completion chunks.
        """
        url = f"{self.endpoint}/messages"
        
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
                        f"Claude API error: {error_text}",
                        status_code=response.status
                    )
                
                if data.get("stream"):
                    # Handle streaming response
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line.startswith("data: "):
                            line = line[6:]  # Remove "data: " prefix
                            
                            try:
                                event_data = json.loads(line)
                                
                                if event_data["type"] == "content_block_delta":
                                    # Text content update
                                    yield ChatCompletionChunk(
                                        content=event_data["delta"]["text"],
                                        finish_reason=None,
                                        metadata={
                                            "type": event_data["type"],
                                            "index": event_data["index"]
                                        }
                                    )
                                elif event_data["type"] == "message_stop":
                                    # Message complete
                                    yield ChatCompletionChunk(
                                        content="",
                                        finish_reason="stop",
                                        metadata={
                                            "type": event_data["type"],
                                            "stop_reason": event_data.get("stop_reason")
                                        }
                                    )
                                elif event_data["type"] == "message_start":
                                    # Message metadata
                                    message = event_data.get("message", {})
                                    yield ChatCompletionChunk(
                                        content="",
                                        finish_reason=None,
                                        metadata={
                                            "type": event_data["type"],
                                            "model": message.get("model"),
                                            "id": message.get("id"),
                                            "usage": message.get("usage")
                                        }
                                    )
                            except json.JSONDecodeError:
                                # Skip invalid JSON lines
                                continue
                else:
                    # Handle non-streaming response
                    response_data = await response.json()
                    
                    # Extract content from response
                    content = ""
                    for content_block in response_data.get("content", []):
                        if content_block["type"] == "text":
                            content += content_block["text"]
                    
                    yield ChatCompletionChunk(
                        content=content,
                        finish_reason=response_data.get("stop_reason", "stop"),
                        metadata={
                            "model": response_data.get("model"),
                            "id": response_data.get("id"),
                            "usage": response_data.get("usage"),
                            "stop_sequence": response_data.get("stop_sequence")
                        }
                    )
        
        # Execute with retry logic
        async for chunk in self._retry_with_backoff(_make_request):
            yield chunk