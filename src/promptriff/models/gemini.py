"""Google Gemini model provider implementation."""

import json
from typing import Any, AsyncIterator, Dict, List, Optional

import google.generativeai as genai
from google.generativeai.types import HarmBlockThreshold, HarmCategory

from .base import Message, ModelProvider, ModelResponse


class GeminiProvider(ModelProvider):
    """Google Gemini model provider."""
    
    def __init__(self, api_key: str, endpoint: Optional[str] = None, **kwargs):
        """Initialize Gemini provider.
        
        Args:
            api_key: Google API key
            endpoint: Optional custom API endpoint (not typically used for Gemini)
            **kwargs: Additional configuration
        """
        super().__init__(api_key, endpoint, **kwargs)
        
        # Configure the API key
        genai.configure(api_key=api_key)
        
        # Safety settings - allow all content for prompt engineering
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
    
    async def list_models(self) -> List[str]:
        """List available Gemini models.
        
        Returns:
            List of model identifiers
        """
        try:
            # List models from the API
            models = []
            for model in genai.list_models():
                if "generateContent" in model.supported_generation_methods:
                    models.append(model.name.split("/")[-1])  # Extract model name
            return sorted(models)
        except Exception:
            # Return default models if listing fails
            return [
                "gemini-pro",
                "gemini-pro-vision",
                "gemini-ultra",
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
        """Generate a chat completion using Gemini.
        
        Args:
            messages: List of conversation messages
            model: Model identifier to use
            stream: Whether to stream the response
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            tools: Optional list of tools/functions available
            **kwargs: Additional parameters
            
        Yields:
            Model response chunks if streaming, single response otherwise
        """
        # Initialize the model
        generation_config = {
            "temperature": temperature,
            "top_p": kwargs.get("top_p", 0.95),
            "top_k": kwargs.get("top_k", 40),
        }
        
        if max_tokens:
            generation_config["max_output_tokens"] = max_tokens
        
        # Create model instance
        gemini_model = genai.GenerativeModel(
            model_name=model,
            generation_config=generation_config,
            safety_settings=self.safety_settings,
        )
        
        # Convert messages to Gemini format
        # Gemini uses a different conversation format
        gemini_messages = []
        
        for msg in messages:
            if msg.role == "system":
                # Add system message as a user message with context
                gemini_messages.append({
                    "role": "user",
                    "parts": [f"System: {msg.content}"]
                })
                gemini_messages.append({
                    "role": "model",
                    "parts": ["Understood. I'll follow these instructions."]
                })
            elif msg.role == "user":
                gemini_messages.append({
                    "role": "user",
                    "parts": [msg.content]
                })
            elif msg.role == "assistant":
                gemini_messages.append({
                    "role": "model",
                    "parts": [msg.content]
                })
        
        # Create chat session
        chat = gemini_model.start_chat(history=gemini_messages[:-1] if gemini_messages else [])
        
        try:
            # Get the last user message
            last_message = gemini_messages[-1]["parts"][0] if gemini_messages else "Hello"
            
            if stream:
                # Stream response chunks
                response = await self.retry_with_backoff(
                    chat.send_message_async,
                    last_message,
                    stream=True
                )
                
                async for chunk in response:
                    if chunk.text:
                        yield ModelResponse(
                            content=chunk.text,
                            model=model,
                            provider="gemini",
                            metadata={
                                "finish_reason": getattr(chunk, "finish_reason", None),
                            }
                        )
            else:
                # Get complete response
                response = await self.retry_with_backoff(
                    chat.send_message_async,
                    last_message
                )
                
                yield ModelResponse(
                    content=response.text,
                    model=model,
                    provider="gemini",
                    metadata={
                        "finish_reason": response.candidates[0].finish_reason.name if response.candidates else None,
                    },
                    usage={
                        "prompt_tokens": response.usage_metadata.prompt_token_count,
                        "completion_tokens": response.usage_metadata.candidates_token_count,
                        "total_tokens": response.usage_metadata.total_token_count,
                    } if hasattr(response, "usage_metadata") else None
                )
                
        except Exception as e:
            if "API_KEY_INVALID" in str(e):
                raise ValueError("Invalid Google API key")
            elif "RATE_LIMIT_EXCEEDED" in str(e):
                raise ValueError("Gemini rate limit exceeded")
            else:
                raise ValueError(f"Gemini API error: {str(e)}")
    
    async def validate_api_key(self) -> bool:
        """Validate the Google API key.
        
        Returns:
            True if API key is valid, False otherwise
        """
        try:
            # Try to list models as a validation check
            list(genai.list_models())
            return True
        except Exception as e:
            if "API_KEY_INVALID" in str(e):
                return False
            # For other errors, assume key might be valid
            return True