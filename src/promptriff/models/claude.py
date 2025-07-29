"""Anthropic Claude model provider implementation."""

import json
from typing import Any, AsyncIterator, Dict, List, Optional

import anthropic
from anthropic import AsyncAnthropic

from .base import Message, ModelProvider, ModelResponse


class ClaudeProvider(ModelProvider):
    """Anthropic Claude model provider."""
    
    def __init__(self, api_key: str, endpoint: Optional[str] = None, **kwargs):
        """Initialize Claude provider.
        
        Args:
            api_key: Anthropic API key
            endpoint: Optional custom API endpoint
            **kwargs: Additional configuration
        """
        super().__init__(api_key, endpoint, **kwargs)
        
        # Initialize client
        self.client = AsyncAnthropic(
            api_key=api_key,
            base_url=endpoint,
            timeout=self.timeout,
        )
    
    async def list_models(self) -> List[str]:
        """List available Claude models.
        
        Returns:
            List of model identifiers
        """
        # Claude doesn't have a list models endpoint, return known models
        return [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-2.1",
            "claude-2.0",
            "claude-instant-1.2",
        ]
    
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
        """Generate a chat completion using Claude.
        
        Args:
            messages: List of conversation messages
            model: Model identifier to use
            stream: Whether to stream the response
            temperature: Sampling temperature (0-1 for Claude)
            max_tokens: Maximum tokens to generate
            tools: Optional list of tools/functions available
            **kwargs: Additional parameters
            
        Yields:
            Model response chunks if streaming, single response otherwise
        """
        # Convert messages to Claude format
        # Extract system message if present
        system_message = None
        claude_messages = []
        
        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                claude_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # Ensure conversation starts with user message
        if claude_messages and claude_messages[0]["role"] != "user":
            claude_messages.insert(0, {"role": "user", "content": "Hello"})
        
        # Prepare request parameters
        params = {
            "model": model,
            "messages": claude_messages,
            "temperature": min(temperature, 1.0),  # Claude max is 1.0
            "max_tokens": max_tokens or 4096,  # Claude requires max_tokens
            "stream": stream,
        }
        
        if system_message:
            params["system"] = system_message
        
        if tools:
            # Convert tools to Claude format
            params["tools"] = [
                {
                    "name": tool["function"]["name"],
                    "description": tool["function"].get("description", ""),
                    "input_schema": tool["function"].get("parameters", {})
                }
                for tool in tools
            ]
        
        # Add any additional parameters
        for key, value in kwargs.items():
            if key not in params:
                params[key] = value
        
        try:
            # Make the API call
            response = await self.retry_with_backoff(
                self.client.messages.create,
                **params
            )
            
            if stream:
                # Stream response chunks
                async for event in response:
                    if event.type == "content_block_delta":
                        if hasattr(event.delta, "text"):
                            yield ModelResponse(
                                content=event.delta.text,
                                model=model,
                                provider="claude",
                                metadata={
                                    "event_type": event.type,
                                    "index": event.index,
                                }
                            )
                    elif event.type == "content_block_start":
                        if hasattr(event.content_block, "type") and event.content_block.type == "tool_use":
                            yield ModelResponse(
                                content=json.dumps({
                                    "tool_use": {
                                        "id": event.content_block.id,
                                        "name": event.content_block.name,
                                        "input": {}
                                    }
                                }),
                                model=model,
                                provider="claude",
                                metadata={"type": "tool_use_start"}
                            )
                    elif event.type == "message_stop":
                        # Final event with usage info
                        if hasattr(event, "message") and hasattr(event.message, "usage"):
                            yield ModelResponse(
                                content="",
                                model=model,
                                provider="claude",
                                metadata={"type": "message_complete"},
                                usage={
                                    "prompt_tokens": event.message.usage.input_tokens,
                                    "completion_tokens": event.message.usage.output_tokens,
                                    "total_tokens": event.message.usage.input_tokens + event.message.usage.output_tokens,
                                }
                            )
            else:
                # Return complete response
                content = ""
                if response.content:
                    for block in response.content:
                        if hasattr(block, "text"):
                            content += block.text
                
                yield ModelResponse(
                    content=content,
                    model=model,
                    provider="claude",
                    metadata={
                        "stop_reason": response.stop_reason,
                        "message_id": response.id,
                    },
                    usage={
                        "prompt_tokens": response.usage.input_tokens,
                        "completion_tokens": response.usage.output_tokens,
                        "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
                    } if response.usage else None
                )
                
        except anthropic.AuthenticationError:
            raise ValueError("Invalid Anthropic API key")
        except anthropic.RateLimitError:
            raise ValueError("Claude rate limit exceeded")
        except anthropic.APIError as e:
            raise ValueError(f"Claude API error: {str(e)}")
        except Exception as e:
            raise ValueError(f"Unexpected error: {str(e)}")
    
    async def validate_api_key(self) -> bool:
        """Validate the Anthropic API key.
        
        Returns:
            True if API key is valid, False otherwise
        """
        try:
            # Try a minimal API call to validate the key
            await self.client.messages.create(
                model="claude-3-haiku-20240307",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=1,
            )
            return True
        except anthropic.AuthenticationError:
            return False
        except Exception:
            # For other errors, assume key might be valid
            return True