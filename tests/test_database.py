"""Tests for database models and operations."""

import pytest
from sqlalchemy import select

from promptriff.database import Conversation, Prompt, PromptTemplate, Response


@pytest.mark.asyncio
async def test_create_conversation(db_session):
    """Test creating a conversation."""
    conversation = Conversation(
        title="Test Conversation",
        model_provider="openai",
        model_name="gpt-4"
    )
    
    db_session.add(conversation)
    await db_session.commit()
    
    # Verify
    result = await db_session.execute(
        select(Conversation).where(Conversation.id == conversation.id)
    )
    loaded = result.scalar_one()
    
    assert loaded.title == "Test Conversation"
    assert loaded.model_provider == "openai"
    assert loaded.model_name == "gpt-4"


@pytest.mark.asyncio
async def test_create_prompt_and_response(db_session):
    """Test creating prompts and responses."""
    # Create conversation
    conversation = Conversation(
        title="Test Chat",
        model_provider="claude",
        model_name="claude-3-opus-20240229"
    )
    db_session.add(conversation)
    await db_session.commit()
    
    # Create prompt
    prompt = Prompt(
        conversation_id=conversation.id,
        content="Hello, how are you?",
        active_tools=["tool1", "tool2"],
        meta={"temperature": 0.7}
    )
    db_session.add(prompt)
    await db_session.commit()
    
    # Create response
    response = Response(
        prompt_id=prompt.id,
        content="I'm doing well, thank you!",
        model_provider="claude",
        model_name="claude-3-opus-20240229",
        meta={"tokens": 10}
    )
    db_session.add(response)
    await db_session.commit()
    
    # Verify relationships
    await db_session.refresh(conversation)
    assert len(conversation.prompts) == 1
    assert conversation.prompts[0].content == "Hello, how are you?"
    
    await db_session.refresh(prompt)
    assert len(prompt.responses) == 1
    assert prompt.responses[0].content == "I'm doing well, thank you!"


@pytest.mark.asyncio
async def test_cascade_delete(db_session):
    """Test cascade deletion."""
    # Create conversation with prompt and response
    conversation = Conversation(
        title="Delete Test",
        model_provider="openai",
        model_name="gpt-4"
    )
    db_session.add(conversation)
    await db_session.commit()
    
    prompt = Prompt(
        conversation_id=conversation.id,
        content="Test prompt"
    )
    db_session.add(prompt)
    await db_session.commit()
    
    response = Response(
        prompt_id=prompt.id,
        content="Test response",
        model_provider="openai",
        model_name="gpt-4"
    )
    db_session.add(response)
    await db_session.commit()
    
    # Delete conversation
    await db_session.delete(conversation)
    await db_session.commit()
    
    # Verify cascade
    prompt_result = await db_session.execute(
        select(Prompt).where(Prompt.id == prompt.id)
    )
    assert prompt_result.scalar_one_or_none() is None
    
    response_result = await db_session.execute(
        select(Response).where(Response.id == response.id)
    )
    assert response_result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_prompt_template(db_session):
    """Test prompt template model."""
    template = PromptTemplate(
        name="Code Review",
        content="Please review this code:\n\n{code}",
        tags=["review", "code", "quality"]
    )
    
    db_session.add(template)
    await db_session.commit()
    
    # Verify
    result = await db_session.execute(
        select(PromptTemplate).where(PromptTemplate.name == "Code Review")
    )
    loaded = result.scalar_one()
    
    assert loaded.content == "Please review this code:\n\n{code}"
    assert loaded.tags == ["review", "code", "quality"]