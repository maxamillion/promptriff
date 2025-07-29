"""Diff viewer component for prompt comparison."""

from typing import List, Optional, Tuple

from rich.console import Console
from rich.syntax import Syntax
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label, Static

import difflib


class DiffStats(Static):
    """Widget showing diff statistics."""
    
    def __init__(self, additions: int = 0, deletions: int = 0, **kwargs):
        """Initialize diff stats.
        
        Args:
            additions: Number of additions
            deletions: Number of deletions
            **kwargs: Additional widget arguments
        """
        super().__init__(**kwargs)
        self.additions = additions
        self.deletions = deletions
    
    def update_stats(self, additions: int, deletions: int) -> None:
        """Update diff statistics.
        
        Args:
            additions: Number of additions
            deletions: Number of deletions
        """
        self.additions = additions
        self.deletions = deletions
        self.update(self._format_stats())
    
    def _format_stats(self) -> str:
        """Format statistics for display."""
        return f"[green]+{self.additions}[/green] [red]-{self.deletions}[/red]"


class DiffViewer(Widget):
    """Side-by-side diff viewer widget."""
    
    left_content = reactive("")
    right_content = reactive("")
    
    def __init__(self, **kwargs):
        """Initialize diff viewer."""
        super().__init__(**kwargs)
        self.diff_lines: List[Tuple[str, str, str]] = []  # (type, left, right)
    
    def compose(self) -> ComposeResult:
        """Compose the diff viewer."""
        with Vertical(classes="diff-viewer"):
            # Header
            with Horizontal(classes="diff-header"):
                with Container(classes="diff-title"):
                    yield Label("Current", classes="diff-label-left")
                with Container(classes="diff-title"):
                    yield Label("Previous", classes="diff-label-right")
                yield DiffStats(id="diff-stats", classes="diff-stats")
            
            # Content
            with Horizontal(classes="diff-content"):
                # Left pane (current)
                with ScrollableContainer(classes="diff-pane diff-pane-left"):
                    yield Container(id="diff-left", classes="diff-text")
                
                # Right pane (previous)
                with ScrollableContainer(classes="diff-pane diff-pane-right"):
                    yield Container(id="diff-right", classes="diff-text")
    
    def set_content(self, left: str, right: str) -> None:
        """Set content for comparison.
        
        Args:
            left: Current/new content
            right: Previous/old content
        """
        self.left_content = left
        self.right_content = right
        self._compute_diff()
        self._render_diff()
    
    def _compute_diff(self) -> None:
        """Compute the diff between left and right content."""
        left_lines = self.left_content.splitlines(keepends=True)
        right_lines = self.right_content.splitlines(keepends=True)
        
        # Use difflib to compute diff
        differ = difflib.unified_diff(
            right_lines,
            left_lines,
            lineterm="",
            n=3
        )
        
        # Parse diff output
        self.diff_lines = []
        additions = 0
        deletions = 0
        
        # Use side-by-side diff
        matcher = difflib.SequenceMatcher(None, right_lines, left_lines)
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                # Lines are the same
                for i in range(i1, i2):
                    self.diff_lines.append(("equal", left_lines[j1 + i - i1], right_lines[i]))
            elif tag == "delete":
                # Lines deleted from right
                for i in range(i1, i2):
                    self.diff_lines.append(("delete", "", right_lines[i]))
                    deletions += 1
            elif tag == "insert":
                # Lines added to left
                for j in range(j1, j2):
                    self.diff_lines.append(("insert", left_lines[j], ""))
                    additions += 1
            elif tag == "replace":
                # Lines changed
                for i in range(i2 - i1):
                    if i < j2 - j1:
                        self.diff_lines.append(("change", left_lines[j1 + i], right_lines[i1 + i]))
                        additions += 1
                        deletions += 1
                    else:
                        self.diff_lines.append(("delete", "", right_lines[i1 + i]))
                        deletions += 1
                
                for j in range(j2 - j1 - (i2 - i1)):
                    self.diff_lines.append(("insert", left_lines[j1 + (i2 - i1) + j], ""))
                    additions += 1
        
        # Update stats
        stats = self.query_one("#diff-stats", DiffStats)
        stats.update_stats(additions, deletions)
    
    def _render_diff(self) -> None:
        """Render the diff in both panes."""
        left_container = self.query_one("#diff-left", Container)
        right_container = self.query_one("#diff-right", Container)
        
        # Clear existing content
        left_container.remove_children()
        right_container.remove_children()
        
        # Render each line
        for diff_type, left_line, right_line in self.diff_lines:
            # Left pane
            if left_line:
                if diff_type == "insert":
                    left_widget = Static(left_line.rstrip(), classes="diff-line diff-add")
                elif diff_type == "change":
                    left_widget = Static(left_line.rstrip(), classes="diff-line diff-change")
                else:
                    left_widget = Static(left_line.rstrip(), classes="diff-line")
                left_container.mount(left_widget)
            else:
                left_container.mount(Static("", classes="diff-line diff-empty"))
            
            # Right pane
            if right_line:
                if diff_type == "delete":
                    right_widget = Static(right_line.rstrip(), classes="diff-line diff-delete")
                elif diff_type == "change":
                    right_widget = Static(right_line.rstrip(), classes="diff-line diff-change")
                else:
                    right_widget = Static(right_line.rstrip(), classes="diff-line")
                right_container.mount(right_widget)
            else:
                right_container.mount(Static("", classes="diff-line diff-empty"))
    
    def clear(self) -> None:
        """Clear the diff viewer."""
        self.left_content = ""
        self.right_content = ""
        self.diff_lines = []
        
        left_container = self.query_one("#diff-left", Container)
        right_container = self.query_one("#diff-right", Container)
        left_container.remove_children()
        right_container.remove_children()
        
        stats = self.query_one("#diff-stats", DiffStats)
        stats.update_stats(0, 0)