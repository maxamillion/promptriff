"""Main Textual application for PromptRiff."""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.containers import Container
from rich.text import Text


class PromptRiffApp(App):
    """Main PromptRiff application."""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    .main-container {
        height: 100%;
        padding: 1;
    }
    
    .placeholder {
        height: 100%;
        content-align: center middle;
        text-style: italic;
        color: $text-muted;
    }
    """
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
    ]
    
    def __init__(self, db, dev_mode: bool = False):
        """Initialize the app.
        
        Args:
            db: Database instance
            dev_mode: Whether running in development mode
        """
        super().__init__()
        self.db = db
        self.dev_mode = dev_mode
        self.title = "PromptRiff"
        self.sub_title = "Terminal AI Interface"
        
    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(show_clock=True)
        
        with Container(classes="main-container"):
            yield Static(
                Text(
                    "PromptRiff UI Coming Soon!\n\n"
                    "This is a placeholder for the full Textual interface.\n"
                    "Press 'q' or Ctrl+C to exit.",
                    style="dim"
                ),
                classes="placeholder"
            )
            
        yield Footer()
        
    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()