"""OpenAI model provider implementation."""

import json
from typing import Any, AsyncIterator, Dict, List, Optional

import openai
from openai import AsyncOpenAI

from .base import Message, ModelProvider, ModelResponse


class OpenAIProvider(ModelProvider):
    """OpenAI model provider."""
    
    def __init__(self, api_key: str, endpoint: Optional[str] = None, **kwargs):
        """Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            endpoint: Optional custom API endpoint
            **kwargs: Additional configuration
        """
        super().__init__(api_key, endpoint, **kwargs)
        
        # Initialize client
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=endpoint,
            timeout=self.timeout,
        )
    
    async def list_models(self) -> List[str]:
        """List available OpenAI models.
        
        Returns:
            List of model identifiers
        """
        try:
            response = await self.client.models.list()
            # Filter for chat models
            chat_models = [
                model.id for model in response.data
                if any(prefix in model.id for prefix in ["gpt-3.5", "gpt-4"])
            ]
            return sorted(chat_models)
        except Exception as e:
            # Return default models if listing fails
            return [
                "gpt-3.5-turbo",
                "gpt-3.5-turbo-16k",
                "gpt-4",
                "gpt-4-turbo-preview",
                "gpt-4-vision-preview",
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
        """Generate a chat completion using OpenAI.
        
        Args:
            messages: List of conversation messages
            model: Model identifier to use
            stream: Whether to stream the response
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            tools: Optional list of tools/functions available
            **kwargs: Additional parameters
            
        Yields:
            Model response chunks if streaming, single response otherwise
        """
        # Convert messages to OpenAI format
        openai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        # Prepare request parameters
        params = {
            "model": model,
            "messages": openai_messages,
            "temperature": temperature,
            "stream": stream,
        }
        
        if max_tokens:
            params["max_tokens"] = max_tokens
        
        if tools:
            params["tools"] = tools
            params["tool_choice"] = kwargs.get("tool_choice", "auto")
        
        # Add any additional parameters
        for key, value in kwargs.items():
            if key not in params:
                params[key] = value
        
        try:
            # Make the API call
            response = await self.retry_with_backoff(
                self.client.chat.completions.create,
                **params
            )
            
            if stream:
                # Stream response chunks
                async for chunk in response:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield ModelResponse(
                            content=chunk.choices[0].delta.content,
                            model=model,
                            provider="openai",
                            metadata={
                                "finish_reason": chunk.choices[0].finish_reason,
                                "chunk_id": chunk.id,
                            }
                        )
                    
                    # Handle tool calls if present
                    if chunk.choices and chunk.choices[0].delta.tool_calls:
                        for tool_call in chunk.choices[0].delta.tool_calls:
                            yield ModelResponse(
                                content=json.dumps({
                                    "tool_call": {
                                        "id": tool_call.id,
                                        "type": tool_call.type,
                                        "function": {
                                            "name": tool_call.function.name,
                                            "arguments": tool_call.function.arguments,
                                        } if tool_call.function else None
                                    }
                                }),
                                model=model,
                                provider="openai",
                                metadata={"type": "tool_call"}
                            )
            else:
                # Return complete response
                choice = response.choices[0]
                yield ModelResponse(
                    content=choice.message.content or "",
                    model=model,
                    provider="openai",
                    metadata={
                        "finish_reason": choice.finish_reason,
                        "message_id": response.id,
                    },
                    usage={
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens,
                    } if response.usage else None
                )
                
        except openai.AuthenticationError:
            raise ValueError("Invalid OpenAI API key")
        except openai.RateLimitError:
            raise ValueError("OpenAI rate limit exceeded")
        except openai.APIError as e:
            raise ValueError(f"OpenAI API error: {str(e)}")
        except Exception as e:
            raise ValueError(f"Unexpected error: {str(e)}")
    
    async def validate_api_key(self) -> bool:
        """Validate the OpenAI API key.
        
        Returns:
            True if API key is valid, False otherwise
        """
        try:
            # Try to list models as a validation check
            await self.client.models.list()
            return True
        except openai.AuthenticationError:
            return False
        except Exception:
            # For other errors, assume key might be valid
            return True