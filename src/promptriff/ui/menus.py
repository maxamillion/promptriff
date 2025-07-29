"""Menu components for model and tool selection."""

from typing import Any, Dict, List, Optional

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, Checkbox, Label, OptionList, Static
from textual.widgets.option_list import Option

from ..config import Settings
from ..models import PROVIDERS


class ModelSelector(Widget):
    """Widget for selecting AI models."""
    
    class ModelChanged(Message):
        """Message sent when model selection changes."""
        
        def __init__(self, provider: str, model: str):
            super().__init__()
            self.provider = provider
            self.model = model
    
    def __init__(self, settings: Settings, **kwargs):
        """Initialize model selector.
        
        Args:
            settings: Application settings
            **kwargs: Additional widget arguments
        """
        super().__init__(**kwargs)
        self.settings = settings
        self.current_provider: Optional[str] = None
        self.current_model: Optional[str] = None
        
        # Get first available provider
        for provider, config in settings.models.items():
            self.current_provider = provider
            self.current_model = config.default_model
            break
    
    def compose(self) -> ComposeResult:
        """Compose the model selector."""
        with Vertical(classes="model-selector"):
            yield Label("Model Selection", classes="section-title")
            
            # Provider selection
            yield Label("Provider:", classes="field-label")
            
            providers = list(self.settings.models.keys())
            yield OptionList(
                *[Option(p.title(), id=p) for p in providers],
                id="provider-list",
                classes="provider-list"
            )
            
            # Model selection
            yield Label("Model:", classes="field-label")
            yield OptionList(id="model-list", classes="model-list")
            
            # Status indicator
            yield Static("", id="model-status", classes="status-indicator")
    
    async def on_mount(self) -> None:
        """Handle widget mount."""
        # Select initial provider
        if self.current_provider:
            provider_list = self.query_one("#provider-list", OptionList)
            provider_list.highlighted = next(
                (i for i, opt in enumerate(provider_list._options)
                 if opt.id == self.current_provider),
                0
            )
            await self._update_models()
    
    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle option selection."""
        if event.option_list.id == "provider-list":
            self.current_provider = event.option.id
            self.app.call_later(self._update_models)
        elif event.option_list.id == "model-list":
            self.current_model = event.option.id
            if self.current_provider and self.current_model:
                self.post_message(
                    self.ModelChanged(self.current_provider, self.current_model)
                )
                self._update_status("Model selected")
    
    async def _update_models(self) -> None:
        """Update model list based on selected provider."""
        if not self.current_provider:
            return
        
        model_list = self.query_one("#model-list", OptionList)
        model_list.clear_options()
        
        # Get provider config
        provider_config = self.settings.models.get(self.current_provider)
        if not provider_config:
            return
        
        # Try to get available models
        try:
            from ..models import get_provider
            
            provider = get_provider(
                self.current_provider,
                api_key=provider_config.api_key,
                endpoint=provider_config.endpoint
            )
            
            models = await provider.list_models()
            
            # Add models to list
            for model in models:
                model_list.add_option(Option(model, id=model))
            
            # Select default model
            default_idx = next(
                (i for i, m in enumerate(models)
                 if m == provider_config.default_model),
                0
            )
            if models:
                model_list.highlighted = default_idx
                self.current_model = models[default_idx]
                
        except Exception as e:
            self._update_status(f"Error loading models: {str(e)}", error=True)
            # Add default model as fallback
            model_list.add_option(
                Option(provider_config.default_model, id=provider_config.default_model)
            )
    
    def _update_status(self, message: str, error: bool = False) -> None:
        """Update status indicator.
        
        Args:
            message: Status message
            error: Whether this is an error message
        """
        status = self.query_one("#model-status", Static)
        status.update(message)
        status.remove_class("error", "success")
        status.add_class("error" if error else "success")


class ToolSelector(Widget):
    """Widget for selecting MCP tools."""
    
    class ToolsChanged(Message):
        """Message sent when tool selection changes."""
        
        def __init__(self, enabled_tools: List[str]):
            super().__init__()
            self.enabled_tools = enabled_tools
    
    def __init__(self, tool_configs: List[Dict[str, Any]], **kwargs):
        """Initialize tool selector.
        
        Args:
            tool_configs: List of tool configurations
            **kwargs: Additional widget arguments
        """
        super().__init__(**kwargs)
        self.tool_configs = tool_configs
        self.enabled_tools: Dict[str, bool] = {
            tool["name"]: tool["enabled"] for tool in tool_configs
        }
    
    def compose(self) -> ComposeResult:
        """Compose the tool selector."""
        with Vertical(classes="tool-selector"):
            yield Label("MCP Tools", classes="section-title")
            
            # Tool list with checkboxes
            with Container(id="tool-list", classes="tool-list"):
                for tool in self.tool_configs:
                    with Container(classes="tool-item"):
                        yield Checkbox(
                            tool["name"],
                            value=tool["enabled"],
                            id=f"tool-{tool['name']}",
                            classes="tool-checkbox"
                        )
                        if "description" in tool.get("config", {}):
                            yield Label(
                                tool["config"]["description"],
                                classes="tool-description"
                            )
            
            # Select/deselect all buttons
            with Container(classes="tool-actions"):
                yield Button("Select All", id="select-all", variant="default")
                yield Button("Deselect All", id="deselect-all", variant="default")
    
    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle checkbox changes."""
        if event.checkbox.id and event.checkbox.id.startswith("tool-"):
            tool_name = event.checkbox.id[5:]  # Remove "tool-" prefix
            self.enabled_tools[tool_name] = event.value
            self._notify_changes()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "select-all":
            self._set_all_tools(True)
        elif event.button.id == "deselect-all":
            self._set_all_tools(False)
    
    def _set_all_tools(self, enabled: bool) -> None:
        """Set all tools to enabled/disabled state.
        
        Args:
            enabled: Whether to enable tools
        """
        for checkbox in self.query(Checkbox):
            if checkbox.id and checkbox.id.startswith("tool-"):
                checkbox.value = enabled
                tool_name = checkbox.id[5:]
                self.enabled_tools[tool_name] = enabled
        
        self._notify_changes()
    
    def _notify_changes(self) -> None:
        """Notify about tool selection changes."""
        enabled_list = [
            name for name, enabled in self.enabled_tools.items()
            if enabled
        ]
        self.post_message(self.ToolsChanged(enabled_list))
    
    def get_enabled_tools(self) -> List[str]:
        """Get list of enabled tools.
        
        Returns:
            List of enabled tool names
        """
        return [
            name for name, enabled in self.enabled_tools.items()
            if enabled
        ]