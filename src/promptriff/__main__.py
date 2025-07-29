"""Entry point for PromptRiff application."""

import asyncio
import sys
from pathlib import Path

import click
from rich.console import Console

from .config import Settings, load_settings
from .ui.app import PromptRiffApp

console = Console()


@click.command()
@click.option("--config", "-c", type=click.Path(exists=True), help="Path to config file")
@click.option("--dev", is_flag=True, help="Run in development mode")
@click.option("--debug", is_flag=True, help="Enable debug logging")
@click.version_option()
def main(config: str | None, dev: bool, debug: bool) -> None:
    """PromptRiff - Terminal-based AI prompt experimentation tool."""
    try:
        # Load settings
        settings = load_settings(config_path=config)
        
        # Set debug mode
        if debug:
            settings.debug = True
        
        # Initialize and run the application
        app = PromptRiffApp(settings=settings, dev_mode=dev)
        asyncio.run(app.run_async())
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        if debug:
            console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    main()