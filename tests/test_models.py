"""Tests for AI model providers."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from promptriff.models import Message, get_provider
from promptriff.models.openai import OpenAIProvider
from promptriff.models.claude import ClaudeProvider
from promptriff.models.gemini import GeminiProvider


def test_get_provider():
    """Test provider factory function."""
    # Valid providers
    openai_provider = get_provider("openai", api_key="test-key")
    assert isinstance(openai_provider, OpenAIProvider)
    
    claude_provider = get_provider("claude", api_key="test-key")
    assert isinstance(claude_provider, ClaudeProvider)
    
    gemini_provider = get_provider("gemini", api_key="test-key")
    assert isinstance(gemini_provider, GeminiProvider)
    
    # Invalid provider
    with pytest.raises(ValueError, match="Unsupported provider"):
        get_provider("invalid", api_key="test-key")


@pytest.mark.asyncio
async def test_openai_provider_list_models():
    """Test OpenAI provider list models."""
    provider = OpenAIProvider(api_key="test-key")
    
    # Mock the client
    mock_response = MagicMock()
    mock_response.data = [
        MagicMock(id="gpt-3.5-turbo"),
        MagicMock(id="gpt-4"),
        MagicMock(id="text-davinci-003"),  # Should be filtered out
    ]
    
    provider.client.models.list = AsyncMock(return_value=mock_response)
    
    models = await provider.list_models()
    assert "gpt-3.5-turbo" in models
    assert "gpt-4" in models
    assert "text-davinci-003" not in models


@pytest.mark.asyncio
async def test_openai_chat_completion():
    """Test OpenAI chat completion."""
    provider = OpenAIProvider(api_key="test-key")
    
    messages = [
        Message(role="user", content="Hello")
    ]
    
    # Mock streaming response
    mock_chunk1 = MagicMock()
    mock_chunk1.choices = [MagicMock()]
    mock_chunk1.choices[0].delta.content = "Hi "
    mock_chunk1.choices[0].finish_reason = None
    mock_chunk1.id = "chunk1"
    
    mock_chunk2 = MagicMock()
    mock_chunk2.choices = [MagicMock()]
    mock_chunk2.choices[0].delta.content = "there!"
    mock_chunk2.choices[0].finish_reason = "stop"
    mock_chunk2.id = "chunk2"
    
    async def mock_stream():
        yield mock_chunk1
        yield mock_chunk2
    
    provider.client.chat.completions.create = AsyncMock(return_value=mock_stream())
    
    # Collect responses
    responses = []
    async for response in provider.chat_completion(messages, "gpt-4", stream=True):
        responses.append(response)
    
    assert len(responses) == 2
    assert responses[0].content == "Hi "
    assert responses[1].content == "there!"


@pytest.mark.asyncio
async def test_claude_provider_list_models():
    """Test Claude provider list models."""
    provider = ClaudeProvider(api_key="test-key")
    
    models = await provider.list_models()
    assert "claude-3-opus-20240229" in models
    assert "claude-3-haiku-20240307" in models


@pytest.mark.asyncio
async def test_gemini_provider_initialization():
    """Test Gemini provider initialization."""
    with patch("google.generativeai.configure") as mock_configure:
        provider = GeminiProvider(api_key="test-key")
        mock_configure.assert_called_once_with(api_key="test-key")


def test_message_model():
    """Test Message model."""
    msg = Message(
        role="user",
        content="Test message",
        metadata={"key": "value"}
    )
    
    assert msg.role == "user"
    assert msg.content == "Test message"
    assert msg.metadata == {"key": "value"}