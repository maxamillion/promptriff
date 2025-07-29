"""Chat interface component."""

import asyncio
from typing import Any, Dict, List, Optional

from rich.syntax import Syntax
from textual import work
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, ScrollableContainer, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, Input, Label, LoadingIndicator, Static

from ..models import Message as ChatMessage, ModelProvider


class MessageBubble(Static):
    """A single message bubble in the chat."""
    
    def __init__(self, message: ChatMessage, **kwargs):
        """Initialize message bubble.
        
        Args:
            message: Chat message to display
            **kwargs: Additional widget arguments
        """
        super().__init__(**kwargs)
        self.message = message
        
        # Style based on role
        if message.role == "user":
            self.add_class("user-message")
        elif message.role == "assistant":
            self.add_class("assistant-message")
        else:
            self.add_class("system-message")
    
    def compose(self) -> ComposeResult:
        """Compose the message bubble."""
        # Add role label
        yield Label(f"{self.message.role.title()}:", classes="message-role")
        
        # Add message content
        if self.message.role == "assistant" and "```" in self.message.content:
            # Try to render code blocks with syntax highlighting
            parts = self.message.content.split("```")
            for i, part in enumerate(parts):
                if i % 2 == 0:
                    # Regular text
                    if part.strip():
                        yield Static(part.strip())
                else:
                    # Code block
                    lines = part.split("\n", 1)
                    lang = lines[0].strip() if lines[0].strip() else "text"
                    code = lines[1] if len(lines) > 1 else part
                    
                    try:
                        syntax = Syntax(code, lang, theme="monokai", line_numbers=True)
                        yield Static(syntax)
                    except Exception:
                        # Fallback to plain text
                        yield Static(f"```{part}```")
        else:
            yield Static(self.message.content)


class ChatInput(Widget):
    """Multi-line chat input widget."""
    
    class Submitted(Message):
        """Message sent when input is submitted."""
        
        def __init__(self, content: str):
            super().__init__()
            self.content = content
    
    def __init__(self, placeholder: str = "Type your message...", **kwargs):
        """Initialize chat input.
        
        Args:
            placeholder: Placeholder text
            **kwargs: Additional widget arguments
        """
        super().__init__(**kwargs)
        self.placeholder = placeholder
    
    def compose(self) -> ComposeResult:
        """Compose the chat input."""
        with Horizontal(classes="chat-input-container"):
            yield Input(
                placeholder=self.placeholder,
                id="chat-input",
                classes="chat-input-field"
            )
            yield Button("Send", variant="primary", id="send-button")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "send-button":
            self._submit()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        self._submit()
    
    def _submit(self) -> None:
        """Submit the current input."""
        input_widget = self.query_one("#chat-input", Input)
        content = input_widget.value.strip()
        
        if content:
            self.post_message(self.Submitted(content))
            input_widget.value = ""
            input_widget.focus()


class StreamingMessage(Static):
    """Widget for displaying streaming AI responses."""
    
    content = reactive("")
    
    def __init__(self, **kwargs):
        """Initialize streaming message."""
        super().__init__(**kwargs)
        self.add_class("assistant-message")
        self.add_class("streaming")
    
    def watch_content(self, content: str) -> None:
        """Update display when content changes."""
        self.update(content)
    
    def append_content(self, chunk: str) -> None:
        """Append content chunk."""
        self.content += chunk
    
    def finalize(self) -> ChatMessage:
        """Finalize the streaming message.
        
        Returns:
            Complete chat message
        """
        self.remove_class("streaming")
        return ChatMessage(role="assistant", content=self.content)


class ChatInterface(Widget):
    """Main chat interface widget."""
    
    class NewMessage(Message):
        """Message sent when a new chat message is submitted."""
        
        def __init__(self, content: str):
            super().__init__()
            self.content = content
    
    def __init__(self, **kwargs):
        """Initialize chat interface."""
        super().__init__(**kwargs)
        self.messages: List[ChatMessage] = []
        self.streaming_widget: Optional[StreamingMessage] = None
    
    def compose(self) -> ComposeResult:
        """Compose the chat interface."""
        with Vertical(id="chat-container"):
            # Message area
            with ScrollableContainer(id="message-area"):
                yield Container(id="message-list")
            
            # Input area
            yield ChatInput(id="chat-input-widget")
    
    def on_chat_input_submitted(self, event: ChatInput.Submitted) -> None:
        """Handle chat input submission."""
        # Add user message
        user_msg = ChatMessage(role="user", content=event.content)
        self.add_message(user_msg)
        
        # Post event for parent to handle
        self.post_message(self.NewMessage(event.content))
    
    def add_message(self, message: ChatMessage) -> None:
        """Add a message to the chat.
        
        Args:
            message: Message to add
        """
        self.messages.append(message)
        
        # Add to display
        message_list = self.query_one("#message-list", Container)
        message_list.mount(MessageBubble(message))
        
        # Scroll to bottom
        self.scroll_to_bottom()
    
    def start_streaming(self) -> StreamingMessage:
        """Start a streaming message.
        
        Returns:
            Streaming message widget
        """
        if self.streaming_widget:
            self.finalize_streaming()
        
        self.streaming_widget = StreamingMessage()
        message_list = self.query_one("#message-list", Container)
        message_list.mount(self.streaming_widget)
        
        self.scroll_to_bottom()
        return self.streaming_widget
    
    def finalize_streaming(self) -> Optional[ChatMessage]:
        """Finalize the current streaming message.
        
        Returns:
            Finalized message or None
        """
        if self.streaming_widget:
            message = self.streaming_widget.finalize()
            self.messages.append(message)
            self.streaming_widget = None
            return message
        return None
    
    def scroll_to_bottom(self) -> None:
        """Scroll message area to bottom."""
        message_area = self.query_one("#message-area", ScrollableContainer)
        message_area.scroll_end(animate=False)
    
    def clear_messages(self) -> None:
        """Clear all messages."""
        self.messages.clear()
        message_list = self.query_one("#message-list", Container)
        message_list.remove_children()
        
        if self.streaming_widget:
            self.streaming_widget = None