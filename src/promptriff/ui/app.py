"""Main application class for PromptRiff."""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    LoadingIndicator,
    Static,
    TabbedContent,
    TabPane,
)

from ..config import Settings
from ..database import Conversation, DatabaseManager, Prompt, Response
from ..mcp import ToolRegistry
from ..models import Message, get_provider
from .chat import ChatInterface
from .diff import DiffViewer
from .menus import ModelSelector, ToolSelector


class MainScreen(Screen):
    """Main application screen."""
    
    def __init__(self, app_instance: "PromptRiffApp"):
        """Initialize main screen.
        
        Args:
            app_instance: Parent application instance
        """
        super().__init__()
        self.app_instance = app_instance
        self.chat_interface: Optional[ChatInterface] = None
        self.model_selector: Optional[ModelSelector] = None
        self.tool_selector: Optional[ToolSelector] = None
        self.diff_viewer: Optional[DiffViewer] = None
        self.library_table: Optional[DataTable] = None
        
        # State
        self.current_conversation: Optional[Conversation] = None
        self.current_provider: Optional[str] = None
        self.current_model: Optional[str] = None
        self.enabled_tools: List[str] = []
    
    def compose(self) -> ComposeResult:
        """Compose the main screen layout."""
        yield Header()
        
        with Container(id="main-container"):
            with TabbedContent(initial="chat"):
                with TabPane("Chat", id="chat"):
                    self.chat_interface = ChatInterface()
                    yield self.chat_interface
                
                with TabPane("Models", id="models"):
                    self.model_selector = ModelSelector(self.app_instance.settings)
                    yield self.model_selector
                
                with TabPane("Tools", id="tools"):
                    tool_configs = [
                        {
                            "name": tool.name,
                            "enabled": tool.enabled,
                            "config": tool.config
                        }
                        for tool in self.app_instance.settings.mcp_tools
                    ]
                    self.tool_selector = ToolSelector(tool_configs)
                    yield self.tool_selector
                
                with TabPane("Library", id="library"):
                    with Vertical():
                        yield Label("Prompt Library", classes="section-title")
                        self.library_table = DataTable()
                        self.library_table.add_columns("Date", "Title", "Model", "Messages")
                        yield self.library_table
                
                with TabPane("Compare", id="compare"):
                    self.diff_viewer = DiffViewer()
                    yield self.diff_viewer
        
        yield Footer()
    
    async def on_mount(self) -> None:
        """Handle screen mount."""
        # Load conversation history
        await self._load_conversations()
        
        # Set initial model
        if self.model_selector:
            if self.model_selector.current_provider and self.model_selector.current_model:
                self.current_provider = self.model_selector.current_provider
                self.current_model = self.model_selector.current_model
    
    def on_model_selector_model_changed(self, event: ModelSelector.ModelChanged) -> None:
        """Handle model selection change."""
        self.current_provider = event.provider
        self.current_model = event.model
        self.app_instance.notify(f"Selected {event.provider}: {event.model}")
    
    def on_tool_selector_tools_changed(self, event: ToolSelector.ToolsChanged) -> None:
        """Handle tool selection change."""
        self.enabled_tools = event.enabled_tools
        self.app_instance.notify(f"Enabled {len(event.enabled_tools)} tools")
    
    def on_chat_interface_new_message(self, event: ChatInterface.NewMessage) -> None:
        """Handle new chat message."""
        self.process_message(event.content)
    
    @work(exclusive=True)
    async def process_message(self, content: str) -> None:
        """Process a new message from the user.
        
        Args:
            content: Message content
        """
        if not self.current_provider or not self.current_model:
            self.app_instance.notify("Please select a model first", severity="error")
            return
        
        try:
            # Create or get conversation
            if not self.current_conversation:
                await self._create_conversation()
            
            # Save user prompt
            prompt = await self._save_prompt(content)
            
            # Get provider
            provider_config = self.app_instance.settings.models[self.current_provider]
            provider = get_provider(
                self.current_provider,
                api_key=provider_config.api_key,
                endpoint=provider_config.endpoint
            )
            
            # Prepare messages
            messages = [
                Message(role="user", content=content)
            ]
            
            # Get tools if enabled
            tools = None
            if self.enabled_tools and self.app_instance.tool_registry:
                tools = self.app_instance.tool_registry.format_tools_for_llm(self.enabled_tools)
            
            # Start streaming
            if self.chat_interface:
                streaming_widget = self.chat_interface.start_streaming()
                
                # Stream response
                full_response = ""
                async for response in provider.chat_completion(
                    messages=messages,
                    model=self.current_model,
                    stream=True,
                    tools=tools
                ):
                    streaming_widget.append_content(response.content)
                    full_response += response.content
                
                # Finalize streaming
                self.chat_interface.finalize_streaming()
                
                # Save response
                await self._save_response(prompt.id, full_response)
        
        except Exception as e:
            self.app_instance.notify(f"Error: {str(e)}", severity="error")
    
    async def _create_conversation(self) -> None:
        """Create a new conversation."""
        if not self.app_instance.db_manager:
            return
        
        async with self.app_instance.db_manager.async_session() as session:
            self.current_conversation = Conversation(
                title=f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                model_provider=self.current_provider,
                model_name=self.current_model
            )
            session.add(self.current_conversation)
            await session.commit()
    
    async def _save_prompt(self, content: str) -> Prompt:
        """Save a user prompt.
        
        Args:
            content: Prompt content
            
        Returns:
            Saved prompt object
        """
        if not self.app_instance.db_manager or not self.current_conversation:
            raise ValueError("No active conversation")
        
        async with self.app_instance.db_manager.async_session() as session:
            prompt = Prompt(
                conversation_id=self.current_conversation.id,
                content=content,
                active_tools=self.enabled_tools,
                meta={}
            )
            session.add(prompt)
            await session.commit()
            return prompt
    
    async def _save_response(self, prompt_id: int, content: str) -> None:
        """Save an AI response.
        
        Args:
            prompt_id: Associated prompt ID
            content: Response content
        """
        if not self.app_instance.db_manager:
            return
        
        async with self.app_instance.db_manager.async_session() as session:
            response = Response(
                prompt_id=prompt_id,
                content=content,
                model_provider=self.current_provider,
                model_name=self.current_model,
                meta={}
            )
            session.add(response)
            await session.commit()
    
    async def _load_conversations(self) -> None:
        """Load conversation history into library."""
        if not self.app_instance.db_manager or not self.library_table:
            return
        
        try:
            async with self.app_instance.db_manager.async_session() as session:
                # Simple query for recent conversations
                from sqlalchemy import select
                
                result = await session.execute(
                    select(Conversation).order_by(Conversation.updated_at.desc()).limit(50)
                )
                conversations = result.scalars().all()
                
                # Populate table
                for conv in conversations:
                    self.library_table.add_row(
                        conv.created_at.strftime("%Y-%m-%d %H:%M"),
                        conv.title or "Untitled",
                        f"{conv.model_provider}/{conv.model_name}",
                        str(len(conv.prompts))
                    )
        except Exception as e:
            self.app_instance.notify(f"Failed to load conversations: {e}", severity="error")


class PromptRiffApp(App):
    """Main PromptRiff application."""
    
    CSS_PATH = Path(__file__).parent / "styles.css"
    
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+d", "toggle_dark", "Toggle Dark Mode"),
        Binding("ctrl+s", "save", "Save"),
        Binding("ctrl+o", "open", "Open"),
        Binding("ctrl+n", "new_chat", "New Chat"),
        Binding("ctrl+e", "edit_prompt", "Edit in Editor"),
        Binding("f1", "help", "Help"),
    ]
    
    def __init__(self, settings: Settings, dev_mode: bool = False):
        """Initialize the application.
        
        Args:
            settings: Application settings
            dev_mode: Whether to run in development mode
        """
        super().__init__()
        self.settings = settings
        self.dev_mode = dev_mode
        self.title = "PromptRiff"
        self.sub_title = "AI Prompt Experimentation Tool"
        
        # Set theme
        self.dark = settings.ui.theme == "dark"
        
        # Initialize managers
        self.db_manager: Optional[DatabaseManager] = None
        self.tool_registry: Optional[ToolRegistry] = None
    
    async def on_mount(self) -> None:
        """Handle application mount."""
        # Initialize database
        await self._init_database()
        
        # Initialize MCP tools
        await self._init_tools()
        
        # Push main screen
        self.push_screen(MainScreen(self))
    
    async def _init_database(self) -> None:
        """Initialize database connection."""
        try:
            db_path = self.settings.database.path
            self.db_manager = DatabaseManager(f"sqlite:///{db_path}")
            await self.db_manager.create_tables()
        except Exception as e:
            self.notify(f"Database initialization failed: {e}", severity="error")
    
    async def _init_tools(self) -> None:
        """Initialize MCP tool registry."""
        try:
            self.tool_registry = ToolRegistry()
            await self.tool_registry.initialize(self.settings.mcp_tools)
        except Exception as e:
            self.notify(f"Tool initialization failed: {e}", severity="error")
    
    def action_toggle_dark(self) -> None:
        """Toggle dark mode."""
        self.dark = not self.dark
        self.settings.ui.theme = "dark" if self.dark else "light"
    
    def action_save(self) -> None:
        """Save current conversation."""
        from ..utils import export_conversation_to_markdown, save_export
        
        screen = self.screen
        if isinstance(screen, MainScreen) and screen.current_conversation:
            try:
                # Export current conversation
                # Note: In a real implementation, we'd load full data from DB
                # For now, just notify
                self.notify("Export functionality will save conversation to file", severity="information")
            except Exception as e:
                self.notify(f"Save error: {str(e)}", severity="error")
        else:
            self.notify("No active conversation to save", severity="warning")
    
    def action_open(self) -> None:
        """Open a conversation."""
        self.notify("Open conversation dialog coming soon", severity="information")
    
    def action_new_chat(self) -> None:
        """Start a new chat."""
        screen = self.screen
        if isinstance(screen, MainScreen):
            if screen.chat_interface:
                screen.chat_interface.clear_messages()
            screen.current_conversation = None
            self.notify("Started new chat", severity="information")
    
    def action_edit_prompt(self) -> None:
        """Edit prompt in external editor."""
        from ..utils import edit_prompt_in_editor
        
        screen = self.screen
        if isinstance(screen, MainScreen) and screen.chat_interface:
            try:
                # Get current input value if any
                input_widget = screen.chat_interface.query_one("#chat-input", Input)
                current_text = input_widget.value
                
                # Open editor
                edited_text = edit_prompt_in_editor(
                    current_text,
                    editor_cmd=self.settings.ui.editor
                )
                
                if edited_text is not None:
                    # Update input with edited text
                    input_widget.value = edited_text
                    input_widget.focus()
                    self.notify("Prompt updated from editor", severity="information")
                else:
                    self.notify("Editor cancelled", severity="information")
                    
            except Exception as e:
                self.notify(f"Editor error: {str(e)}", severity="error")
    
    def action_help(self) -> None:
        """Show help."""
        help_text = """
PromptRiff Help

Keyboard Shortcuts:
- Ctrl+Q: Quit
- Ctrl+D: Toggle dark mode
- Ctrl+S: Save conversation
- Ctrl+O: Open conversation
- Ctrl+N: New chat
- Ctrl+E: Edit in external editor
- Tab: Switch between tabs
- F1: This help

Vi-style Navigation:
- h/j/k/l: Navigate
- /: Search
- i: Insert mode
- Esc: Normal mode
"""
        self.notify(help_text, severity="information", timeout=10)
    
    async def action_quit(self) -> None:
        """Quit the application."""
        # Cleanup
        if self.tool_registry:
            await self.tool_registry.shutdown()
        if self.db_manager:
            await self.db_manager.close()
        
        await super().action_quit()