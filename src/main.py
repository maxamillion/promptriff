"""Main entry point for PromptRiff application."""

import asyncio
import sys
from pathlib import Path
import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import settings, ConfigurationError
from src.database.models import Database


console = Console()


def print_banner():
    """Print application banner."""
    banner = Text.from_markup(
        "[bold cyan]PromptRiff[/bold cyan] - [dim]Terminal AI Interface with MCP Support[/dim]"
    )
    console.print(Panel(banner, expand=False, border_style="cyan"))


async def check_configuration():
    """Check if configuration is valid and providers are configured."""
    try:
        config = settings.load()
    except ConfigurationError as e:
        console.print(f"[red]Configuration error:[/red] {e}")
        console.print("\nPlease check your configuration file at:")
        console.print(f"  {settings.config_path}")
        console.print("\nYou can copy the example configuration from:")
        console.print("  examples/config.example.yaml")
        return False
    
    # Check if any providers are configured
    providers = settings.get_configured_providers()
    if not providers:
        console.print("[yellow]No AI providers configured![/yellow]")
        console.print("\nPlease set up at least one provider by adding API keys:")
        console.print("  - Set OPENAI_API_KEY for OpenAI")
        console.print("  - Set ANTHROPIC_API_KEY for Claude") 
        console.print("  - Set GOOGLE_API_KEY for Gemini")
        console.print("\nOr add them to your config file.")
        return False
    
    console.print(f"[green]Configured providers:[/green] {', '.join(providers)}")
    return True


async def initialize_database():
    """Initialize the database."""
    config = settings.load()
    db = Database(config.database.path)
    
    console.print("[dim]Initializing database...[/dim]")
    await db.initialize()
    
    # Create backup if configured
    if config.database.backup_on_startup:
        try:
            backup_path = await db.backup()
            console.print(f"[dim]Database backed up to: {backup_path}[/dim]")
        except Exception as e:
            console.print(f"[yellow]Warning: Failed to backup database: {e}[/yellow]")
    
    return db


async def run_app(dev_mode: bool = False):
    """Run the main application.
    
    Args:
        dev_mode: Whether to run in development mode
    """
    print_banner()
    
    # Check configuration
    if not await check_configuration():
        return
    
    # Initialize database
    try:
        db = await initialize_database()
    except Exception as e:
        console.print(f"[red]Failed to initialize database:[/red] {e}")
        return
    
    # Import and run the UI app
    try:
        from src.ui.app import PromptRiffApp
        
        console.print("\n[green]Starting PromptRiff...[/green]")
        console.print("[dim]Press Ctrl+C to exit[/dim]\n")
        
        app = PromptRiffApp(db=db, dev_mode=dev_mode)
        await app.run_async()
        
    except ImportError as e:
        console.print(f"[red]Failed to import UI components:[/red] {e}")
        console.print("\nThe UI components are not yet implemented.")
        console.print("This is a placeholder that shows the app structure.")
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down...[/yellow]")
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        if dev_mode:
            import traceback
            traceback.print_exc()


@click.command()
@click.option(
    '--dev',
    is_flag=True,
    help='Run in development mode with debug output'
)
@click.option(
    '--config',
    type=click.Path(exists=True, path_type=Path),
    help='Path to configuration file'
)
@click.version_option(version="0.1.0", prog_name="promptriff")
def main(dev: bool, config: Path):
    """PromptRiff - Terminal-based AI interface with MCP support.
    
    Test and compare prompts across multiple AI models (OpenAI, Claude, Gemini)
    with integrated MCP tool support.
    """
    if config:
        settings.config_path = config
        
    # Run the async main function
    asyncio.run(run_app(dev_mode=dev))


if __name__ == "__main__":
    main()