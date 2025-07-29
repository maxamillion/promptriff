"""Tests for utility functions."""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from promptriff.database import Conversation, Prompt, Response
from promptriff.utils import (
    edit_prompt_in_editor,
    export_conversation_to_json,
    export_conversation_to_markdown,
    get_editor_command,
    import_conversation_from_json,
    save_export,
)


def test_get_editor_command(monkeypatch):
    """Test getting editor command."""
    # Test with EDITOR env var
    monkeypatch.setenv("EDITOR", "myeditor")
    assert get_editor_command() == "myeditor"
    
    # Test without EDITOR (would check common editors)
    monkeypatch.delenv("EDITOR", raising=False)
    with patch("subprocess.run") as mock_run:
        # Simulate vim being available
        mock_run.return_value.returncode = 0
        assert get_editor_command() == "vim"


def test_edit_prompt_in_editor():
    """Test editing prompt in external editor."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        
        with patch("tempfile.NamedTemporaryFile") as mock_tmp:
            # Setup mock temp file
            mock_file = mock_tmp.return_value.__enter__.return_value
            mock_file.name = "/tmp/test.md"
            
            # Simulate file being edited
            with patch("builtins.open", create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = "Edited content"
                
                with patch("pathlib.Path.stat") as mock_stat:
                    # Simulate file modification
                    mock_stat.side_effect = [
                        type('obj', (object,), {'st_mtime': 1.0}),
                        type('obj', (object,), {'st_mtime': 2.0})
                    ]
                    
                    result = edit_prompt_in_editor("Initial content", editor_cmd="vim")
                    assert result == "Edited content"


def test_export_conversation_to_json():
    """Test exporting conversation to JSON."""
    # Create test data
    conversation = Conversation(
        id=1,
        title="Test Chat",
        created_at=datetime(2024, 1, 1, 12, 0),
        updated_at=datetime(2024, 1, 1, 13, 0),
        model_provider="openai",
        model_name="gpt-4"
    )
    
    prompts = [
        Prompt(
            id=1,
            conversation_id=1,
            created_at=datetime(2024, 1, 1, 12, 0),
            content="Hello",
            active_tools=["tool1"],
            metadata={}
        )
    ]
    
    responses = {
        1: [
            Response(
                id=1,
                prompt_id=1,
                created_at=datetime(2024, 1, 1, 12, 1),
                content="Hi there!",
                model_provider="openai",
                model_name="gpt-4",
                metadata={}
            )
        ]
    }
    
    result = export_conversation_to_json(conversation, prompts, responses)
    
    assert result["conversation"]["title"] == "Test Chat"
    assert len(result["messages"]) == 1
    assert result["messages"][0]["content"] == "Hello"
    assert len(result["messages"][0]["responses"]) == 1
    assert result["messages"][0]["responses"][0]["content"] == "Hi there!"


def test_export_conversation_to_markdown():
    """Test exporting conversation to Markdown."""
    conversation = Conversation(
        title="Test Chat",
        created_at=datetime(2024, 1, 1, 12, 0),
        model_provider="claude",
        model_name="claude-3-opus-20240229"
    )
    
    prompts = [
        Prompt(
            id=1,
            content="What is Python?",
            active_tools=None
        )
    ]
    
    responses = {
        1: [
            Response(
                content="Python is a programming language.",
                model_provider="claude",
                model_name="claude-3-opus-20240229"
            )
        ]
    }
    
    result = export_conversation_to_markdown(conversation, prompts, responses)
    
    assert "# Test Chat" in result
    assert "## User" in result
    assert "What is Python?" in result
    assert "## Assistant" in result
    assert "Python is a programming language." in result


def test_save_export(temp_dir: Path):
    """Test saving exported content."""
    content = "Test export content"
    filename = "export.txt"
    
    saved_path = save_export(content, filename, temp_dir)
    
    assert saved_path.exists()
    assert saved_path.read_text() == content
    
    # Test with existing file (should add timestamp)
    saved_path2 = save_export(content, filename, temp_dir)
    assert saved_path2 != saved_path
    assert saved_path2.stem.startswith("export_")


def test_import_conversation_from_json():
    """Test importing conversation from JSON."""
    data = {
        "conversation": {
            "title": "Imported Chat",
            "model_provider": "openai",
            "model_name": "gpt-4"
        },
        "messages": [
            {
                "type": "prompt",
                "content": "Test prompt",
                "active_tools": ["tool1"],
                "responses": [
                    {
                        "content": "Test response",
                        "model_provider": "openai",
                        "model_name": "gpt-4"
                    }
                ]
            }
        ]
    }
    
    conv_data, prompts_data, responses_data = import_conversation_from_json(data)
    
    assert conv_data["title"] == "Imported Chat"
    assert len(prompts_data) == 1
    assert prompts_data[0]["content"] == "Test prompt"
    assert len(responses_data[0]) == 1
    assert responses_data[0][0]["content"] == "Test response"