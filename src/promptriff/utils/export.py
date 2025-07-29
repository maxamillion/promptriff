"""Export utilities for conversations and prompts."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..database import Conversation, Prompt, Response


def export_conversation_to_json(
    conversation: Conversation,
    prompts: List[Prompt],
    responses: Dict[int, List[Response]]
) -> Dict[str, Any]:
    """Export a conversation to JSON format.
    
    Args:
        conversation: Conversation object
        prompts: List of prompts in the conversation
        responses: Dictionary mapping prompt IDs to responses
        
    Returns:
        JSON-serializable dictionary
    """
    return {
        "conversation": {
            "id": conversation.id,
            "title": conversation.title,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
            "model_provider": conversation.model_provider,
            "model_name": conversation.model_name,
        },
        "messages": [
            {
                "type": "prompt",
                "id": prompt.id,
                "created_at": prompt.created_at.isoformat(),
                "content": prompt.content,
                "active_tools": prompt.active_tools,
                "metadata": prompt.metadata,
                "responses": [
                    {
                        "id": resp.id,
                        "created_at": resp.created_at.isoformat(),
                        "content": resp.content,
                        "model_provider": resp.model_provider,
                        "model_name": resp.model_name,
                        "metadata": resp.metadata,
                    }
                    for resp in responses.get(prompt.id, [])
                ]
            }
            for prompt in prompts
        ]
    }


def export_conversation_to_markdown(
    conversation: Conversation,
    prompts: List[Prompt],
    responses: Dict[int, List[Response]]
) -> str:
    """Export a conversation to Markdown format.
    
    Args:
        conversation: Conversation object
        prompts: List of prompts in the conversation
        responses: Dictionary mapping prompt IDs to responses
        
    Returns:
        Markdown-formatted string
    """
    lines = []
    
    # Header
    lines.append(f"# {conversation.title or 'Untitled Conversation'}")
    lines.append("")
    lines.append(f"**Created:** {conversation.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Model:** {conversation.model_provider}/{conversation.model_name}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Messages
    for prompt in prompts:
        # User prompt
        lines.append("## User")
        lines.append("")
        
        if prompt.active_tools:
            lines.append(f"*Active tools: {', '.join(prompt.active_tools)}*")
            lines.append("")
        
        lines.append(prompt.content)
        lines.append("")
        
        # Responses
        for resp in responses.get(prompt.id, []):
            lines.append("## Assistant")
            lines.append("")
            lines.append(f"*Model: {resp.model_provider}/{resp.model_name}*")
            lines.append("")
            lines.append(resp.content)
            lines.append("")
        
        lines.append("---")
        lines.append("")
    
    return "\n".join(lines)


def export_prompts_to_json(prompts: List[Prompt]) -> List[Dict[str, Any]]:
    """Export prompts to JSON format.
    
    Args:
        prompts: List of prompts to export
        
    Returns:
        List of JSON-serializable dictionaries
    """
    return [
        {
            "id": prompt.id,
            "created_at": prompt.created_at.isoformat(),
            "content": prompt.content,
            "active_tools": prompt.active_tools,
            "metadata": prompt.metadata,
        }
        for prompt in prompts
    ]


def save_export(
    content: str,
    filename: str,
    directory: Optional[Path] = None
) -> Path:
    """Save exported content to a file.
    
    Args:
        content: Content to save
        filename: Filename to use
        directory: Optional directory to save in (defaults to current)
        
    Returns:
        Path to saved file
    """
    # Validate inputs
    if not isinstance(content, str):
        raise ValueError("Content must be a string")
    
    if not isinstance(filename, str) or not filename.strip():
        raise ValueError("Filename must be a non-empty string")
    
    # Sanitize filename to prevent path traversal
    filename = Path(filename).name  # Get just the filename, no path components
    
    if directory is None:
        directory = Path.cwd()
    else:
        directory = Path(directory).resolve()  # Resolve to absolute path
    
    # Ensure directory exists and is a directory
    if not directory.exists():
        raise ValueError(f"Directory does not exist: {directory}")
    if not directory.is_dir():
        raise ValueError(f"Not a directory: {directory}")
    
    filepath = directory / filename
    
    # Add timestamp if file exists
    if filepath.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = filepath.stem
        suffix = filepath.suffix
        filepath = directory / f"{stem}_{timestamp}{suffix}"
    
    with open(filepath, "w") as f:
        f.write(content)
    
    return filepath


def import_conversation_from_json(data: Dict[str, Any]) -> tuple[
    Dict[str, Any],
    List[Dict[str, Any]],
    Dict[int, List[Dict[str, Any]]]
]:
    """Import a conversation from JSON format.
    
    Args:
        data: JSON data to import
        
    Returns:
        Tuple of (conversation_data, prompts_data, responses_data)
    """
    conversation_data = data["conversation"]
    prompts_data = []
    responses_data = {}
    
    for message in data["messages"]:
        if message["type"] == "prompt":
            prompt_data = {
                "content": message["content"],
                "active_tools": message.get("active_tools"),
                "metadata": message.get("metadata"),
            }
            prompts_data.append(prompt_data)
            
            # Map responses
            responses = []
            for resp in message.get("responses", []):
                responses.append({
                    "content": resp["content"],
                    "model_provider": resp["model_provider"],
                    "model_name": resp["model_name"],
                    "metadata": resp.get("metadata"),
                })
            
            if responses:
                # Use prompt index as temporary ID
                responses_data[len(prompts_data) - 1] = responses
    
    return conversation_data, prompts_data, responses_data