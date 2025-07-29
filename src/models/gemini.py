"""Google Gemini model provider implementation."""

import json
from typing import List, Dict, Any, Optional, AsyncIterator
from .base import (
    BaseModelProvider, ModelInfo, ChatMessage, ChatCompletionChunk,
    APIError, RateLimitError
)


class GeminiProvider(BaseModelProvider):
    """Google Gemini API provider implementation."""
    
    # Available models as of early 2024
    MODELS = {
        "gemini-pro": ModelInfo(
            id="gemini-pro",
            name="Gemini Pro",
            description="Versatile model for a wide range of tasks",
            context_window=30720,
            max_output_tokens=2048,
            supports_streaming=True,
            supports_functions=True
        ),
        "gemini-pro-vision": ModelInfo(
            id="gemini-pro-vision",
            name="Gemini Pro Vision",
            description="Multimodal model supporting text and images",
            context_window=12288,
            max_output_tokens=4096,
            supports_streaming=True,
            supports_functions=False
        )
    }
    
    def __init__(
        self,
        api_key: str,
        endpoint: str = "https://generativelanguage.googleapis.com/v1",
        timeout: int = 30,
        max_retries: int = 3
    ):
        """Initialize Gemini provider.
        
        Args:
            api_key: Google API key
            endpoint: API endpoint URL
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        super().__init__(api_key, endpoint, timeout, max_retries)
        
    def get_headers(self) -> Dict[str, str]:
        """Get headers for Gemini API requests."""
        return {
            "Content-Type": "application/json"
        }
    
    async def list_models(self) -> List[ModelInfo]:
        """List available Gemini models.
        
        Returns:
            List of available models.
        """
        # Return hardcoded list of models
        return list(self.MODELS.values())
    
    def _convert_messages_to_gemini_format(
        self,
        messages: List[ChatMessage]
    ) -> List[Dict[str, Any]]:
        """Convert messages to Gemini's expected format.
        
        Gemini expects a different format:
        - System messages become user messages with system context
        - Messages have 'parts' containing the content
        
        Args:
            messages: List of chat messages
            
        Returns:
            List of Gemini-formatted messages
        """
        gemini_messages = []
        system_context = []
        
        for msg in messages:
            if msg.role == "system":
                # Collect system messages to prepend to first user message
                system_context.append(msg.content)
            else:
                # Convert role names
                role = "user" if msg.role == "user" else "model"
                
                # If this is the first user message and we have system context,
                # prepend it
                content = msg.content
                if role == "user" and system_context and not gemini_messages:
                    context_str = "\n".join(system_context)
                    content = f"{context_str}\n\n{content}"
                    system_context = []  # Clear after using
                
                gemini_messages.append({
                    "role": role,
                    "parts": [{"text": content}]
                })
        
        # Gemini requires alternating user/model messages
        # Ensure the conversation starts with a user message
        if gemini_messages and gemini_messages[0]["role"] != "user":
            gemini_messages.insert(0, {
                "role": "user",
                "parts": [{"text": "Begin."}]
            })
            
        return gemini_messages
    
    async def complete(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = True,
        **kwargs
    ) -> AsyncIterator[ChatCompletionChunk]:
        """Generate a chat completion using Gemini API.
        
        Args:
            messages: List of messages in the conversation
            model: Model to use for completion
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            **kwargs: Additional Gemini-specific parameters
            
        Yields:
            Chat completion chunks.
        """
        # Convert messages to Gemini format
        gemini_messages = self._convert_messages_to_gemini_format(messages)
        
        # Prepare request data
        data = {
            "contents": gemini_messages,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens or 2048,
            }
        }
        
        # Add any additional generation config parameters
        for key in ["topP", "topK", "candidateCount", "stopSequences"]:
            if key in kwargs:
                data["generationConfig"][key] = kwargs[key]
                
        # Add safety settings if provided
        if "safetySettings" in kwargs:
            data["safetySettings"] = kwargs["safetySettings"]
        
        # Make the request
        async for chunk in self._stream_request(data, model, stream):
            yield chunk
    
    async def _stream_request(
        self,
        data: Dict[str, Any],
        model: str,
        stream: bool
    ) -> AsyncIterator[ChatCompletionChunk]:
        """Make a request to Gemini API.
        
        Args:
            data: Request data
            model: Model name
            stream: Whether to stream the response
            
        Yields:
            Chat completion chunks.
        """
        # Gemini uses different endpoints for streaming vs non-streaming
        if stream:
            endpoint = f"{self.endpoint}/models/{model}:streamGenerateContent"
        else:
            endpoint = f"{self.endpoint}/models/{model}:generateContent"
            
        # Add API key as query parameter
        url = f"{endpoint}?key={self.api_key}"
        
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
                        f"Gemini API error: {error_text}",
                        status_code=response.status
                    )
                
                if stream:
                    # Handle streaming response
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if not line:
                            continue
                            
                        try:
                            # Gemini streams JSON objects directly
                            chunk_data = json.loads(line)
                            
                            # Extract text from candidates
                            for candidate in chunk_data.get("candidates", []):
                                content = candidate.get("content", {})
                                for part in content.get("parts", []):
                                    if "text" in part:
                                        yield ChatCompletionChunk(
                                            content=part["text"],
                                            finish_reason=candidate.get("finishReason"),
                                            metadata={
                                                "index": candidate.get("index"),
                                                "safetyRatings": candidate.get("safetyRatings")
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
                    finish_reason = None
                    metadata = {}
                    
                    for candidate in response_data.get("candidates", []):
                        candidate_content = candidate.get("content", {})
                        for part in candidate_content.get("parts", []):
                            if "text" in part:
                                content += part["text"]
                        
                        finish_reason = candidate.get("finishReason", "stop")
                        metadata = {
                            "index": candidate.get("index"),
                            "safetyRatings": candidate.get("safetyRatings"),
                            "citationMetadata": candidate.get("citationMetadata")
                        }
                    
                    # Add prompt feedback if available
                    if "promptFeedback" in response_data:
                        metadata["promptFeedback"] = response_data["promptFeedback"]
                    
                    yield ChatCompletionChunk(
                        content=content,
                        finish_reason=finish_reason,
                        metadata=metadata
                    )
        
        # Execute with retry logic
        async for chunk in self._retry_with_backoff(_make_request):
            yield chunk