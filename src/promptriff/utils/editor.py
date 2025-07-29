"""External editor integration utilities."""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


def get_editor_command() -> Optional[str]:
    """Get the external editor command.
    
    Returns:
        Editor command or None if not configured
    """
    # Check in order: EDITOR env var, common editors
    editor = os.environ.get("EDITOR")
    if editor:
        return editor
    
    # Try common editors
    common_editors = ["vim", "nvim", "nano", "emacs", "code", "subl"]
    for cmd in common_editors:
        if subprocess.run(["which", cmd], capture_output=True).returncode == 0:
            return cmd
    
    return None


def edit_in_external_editor(
    initial_content: str = "",
    suffix: str = ".md",
    editor_cmd: Optional[str] = None
) -> Optional[str]:
    """Open external editor with content and return edited result.
    
    Args:
        initial_content: Initial content for the editor
        suffix: File suffix for syntax highlighting
        editor_cmd: Optional specific editor command
        
    Returns:
        Edited content or None if editing failed
    """
    editor = editor_cmd or get_editor_command()
    if not editor:
        raise ValueError("No editor configured. Set $EDITOR environment variable.")
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False) as tmp:
        tmp.write(initial_content)
        tmp_path = tmp.name
    
    try:
        # Get initial modification time
        initial_mtime = Path(tmp_path).stat().st_mtime
        
        # Open editor
        process = subprocess.run([editor, tmp_path])
        
        if process.returncode != 0:
            return None
        
        # Check if file was modified
        final_mtime = Path(tmp_path).stat().st_mtime
        if final_mtime == initial_mtime:
            # File wasn't modified
            return initial_content
        
        # Read edited content
        with open(tmp_path, "r") as f:
            return f.read()
            
    finally:
        # Clean up temporary file
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def edit_prompt_in_editor(prompt: str, editor_cmd: Optional[str] = None) -> Optional[str]:
    """Edit a prompt in external editor.
    
    Args:
        prompt: Initial prompt text
        editor_cmd: Optional specific editor command
        
    Returns:
        Edited prompt or None if editing failed
    """
    # Validate input
    if not isinstance(prompt, str):
        raise ValueError("Prompt must be a string")
    
    # Limit prompt size to prevent resource exhaustion
    max_prompt_size = 1024 * 1024  # 1MB
    if len(prompt) > max_prompt_size:
        raise ValueError(f"Prompt too large (max {max_prompt_size} bytes)")
    
    header = """# Edit your prompt below
# Lines starting with '#' will be removed
# Save and exit to submit, or exit without saving to cancel

"""
    
    full_content = header + prompt
    edited = edit_in_external_editor(full_content, suffix=".md", editor_cmd=editor_cmd)
    
    if edited is None:
        return None
    
    # Remove comment lines
    lines = edited.splitlines()
    content_lines = [line for line in lines if not line.strip().startswith("#")]
    
    return "\n".join(content_lines).strip()


def open_file_in_editor(file_path: Path, editor_cmd: Optional[str] = None) -> bool:
    """Open a file in external editor.
    
    Args:
        file_path: Path to file to open
        editor_cmd: Optional specific editor command
        
    Returns:
        True if editor opened successfully
    """
    editor = editor_cmd or get_editor_command()
    if not editor:
        return False
    
    try:
        subprocess.run([editor, str(file_path)])
        return True
    except Exception:
        return False