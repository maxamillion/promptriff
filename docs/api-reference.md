# API Reference

## Core Modules

### promptriff.config

Configuration management for PromptRiff.

#### Classes

##### `Settings`
Main application settings using Pydantic.

```python
from promptriff.config import Settings

settings = Settings(
    models={
        "openai": {
            "api_key": "sk-...",
            "default_model": "gpt-4"
        }
    }
)
```

**Attributes:**
- `models: Dict[str, ModelConfig]` - AI model configurations
- `mcp_tools: List[MCPTool]` - MCP tool configurations
- `ui: UIConfig` - UI settings
- `database: DatabaseConfig` - Database settings
- `debug: bool` - Debug mode flag

##### `ModelConfig`
Configuration for an AI model provider.

**Attributes:**
- `api_key: str` - API key for the provider
- `endpoint: Optional[str]` - Custom API endpoint
- `default_model: str` - Default model to use
- `timeout: int` - Request timeout in seconds
- `max_retries: int` - Maximum retry attempts

#### Functions

##### `load_settings(config_path: Optional[str] = None) -> Settings`
Load settings from configuration file and environment variables.

**Parameters:**
- `config_path`: Optional path to configuration file

**Returns:**
- Loaded `Settings` object

### promptriff.models

AI model provider integrations.

#### Base Classes

##### `ModelProvider`
Abstract base class for AI model providers.

```python
from promptriff.models import ModelProvider, Message

class CustomProvider(ModelProvider):
    async def list_models(self) -> List[str]:
        return ["model-1", "model-2"]
    
    async def chat_completion(
        self,
        messages: List[Message],
        model: str,
        **kwargs
    ) -> AsyncIterator[ModelResponse]:
        # Implementation
        pass
```

**Methods:**
- `list_models() -> List[str]` - List available models
- `chat_completion(...)` - Generate chat completion
- `validate_api_key() -> bool` - Validate API key

##### `Message`
Message model for chat conversations.

**Attributes:**
- `role: str` - Message role ("user", "assistant", "system")
- `content: str` - Message content
- `metadata: Optional[Dict[str, Any]]` - Additional metadata

#### Provider Classes

##### `OpenAIProvider`
OpenAI model provider implementation.

```python
from promptriff.models import OpenAIProvider

provider = OpenAIProvider(
    api_key="sk-...",
    endpoint="https://api.openai.com/v1"
)

models = await provider.list_models()
```

##### `ClaudeProvider`
Anthropic Claude provider implementation.

##### `GeminiProvider`
Google Gemini provider implementation.

#### Functions

##### `get_provider(provider_name: str, **kwargs) -> ModelProvider`
Factory function to get a model provider instance.

**Parameters:**
- `provider_name`: Name of provider ("openai", "claude", "gemini")
- `**kwargs`: Provider configuration

### promptriff.database

Database models and operations.

#### Classes

##### `DatabaseManager`
Manages database connections and sessions.

```python
from promptriff.database import DatabaseManager

db = DatabaseManager("sqlite:///promptriff.db")
await db.create_tables()

async with db.async_session() as session:
    # Use session
    pass
```

**Methods:**
- `create_tables()` - Create all database tables
- `drop_tables()` - Drop all database tables
- `get_session() -> AsyncSession` - Get database session
- `close()` - Close database connections

##### `Conversation`
Conversation model representing a chat session.

**Attributes:**
- `id: int` - Primary key
- `created_at: datetime` - Creation timestamp
- `updated_at: datetime` - Last update timestamp
- `title: Optional[str]` - Conversation title
- `model_provider: str` - AI provider name
- `model_name: str` - Model identifier
- `prompts: List[Prompt]` - Related prompts

##### `Prompt`
Prompt model representing user input.

**Attributes:**
- `id: int` - Primary key
- `conversation_id: int` - Parent conversation ID
- `created_at: datetime` - Creation timestamp
- `content: str` - Prompt text
- `active_tools: Optional[Dict]` - Enabled MCP tools
- `metadata: Optional[Dict]` - Additional metadata
- `responses: List[Response]` - Related responses

##### `Response`
Response model representing AI output.

**Attributes:**
- `id: int` - Primary key
- `prompt_id: int` - Parent prompt ID
- `created_at: datetime` - Creation timestamp
- `content: str` - Response text
- `model_provider: str` - AI provider name
- `model_name: str` - Model identifier
- `metadata: Optional[Dict]` - Response metadata

### promptriff.mcp

Model Context Protocol integration.

#### Classes

##### `MCPClient`
Client for managing MCP tool connections.

```python
from promptriff.mcp import MCPClient

client = MCPClient()
await client.start()

success = await client.connect_tool({
    "name": "filesystem",
    "path": "/usr/bin/mcp-filesystem"
})

result = await client.call_tool("filesystem.read", {
    "path": "/tmp/file.txt"
})
```

**Methods:**
- `start()` - Start the MCP client
- `stop()` - Stop client and close connections
- `connect_tool(config) -> bool` - Connect to a tool
- `disconnect_tool(name)` - Disconnect from tool
- `list_tools() -> List[Dict]` - List available tools
- `call_tool(name, args) -> Tuple[bool, Any]` - Call a tool

##### `ToolRegistry`
Registry for managing MCP tools.

```python
from promptriff.mcp import ToolRegistry

registry = ToolRegistry()
await registry.initialize(tool_configs)

enabled = registry.get_enabled_tools()
tools_for_llm = registry.format_tools_for_llm()
```

**Methods:**
- `initialize(configs)` - Initialize with tool configs
- `connect_tool(config) -> bool` - Connect to a tool
- `enable_tool(name) -> bool` - Enable a tool
- `disable_tool(name)` - Disable a tool
- `get_enabled_tools() -> List[str]` - Get enabled tool names
- `format_tools_for_llm() -> List[Dict]` - Format for LLM use

### promptriff.utils

Utility functions and helpers.

#### Editor Utilities

##### `get_editor_command() -> Optional[str]`
Get the external editor command.

##### `edit_prompt_in_editor(prompt: str, editor_cmd: Optional[str] = None) -> Optional[str]`
Edit a prompt in external editor.

**Parameters:**
- `prompt`: Initial prompt text
- `editor_cmd`: Optional specific editor command

**Returns:**
- Edited prompt or None if cancelled

#### Export Utilities

##### `export_conversation_to_json(conversation, prompts, responses) -> Dict`
Export conversation to JSON format.

##### `export_conversation_to_markdown(conversation, prompts, responses) -> str`
Export conversation to Markdown format.

##### `save_export(content: str, filename: str, directory: Optional[Path] = None) -> Path`
Save exported content to file.

**Parameters:**
- `content`: Content to save
- `filename`: Target filename
- `directory`: Optional save directory

**Returns:**
- Path to saved file

## UI Components

### promptriff.ui.app

Main application and screen classes.

#### Classes

##### `PromptRiffApp`
Main Textual application class.

```python
from promptriff.ui.app import PromptRiffApp
from promptriff.config import Settings

settings = Settings(...)
app = PromptRiffApp(settings)
await app.run_async()
```

**Attributes:**
- `settings: Settings` - Application settings
- `db_manager: DatabaseManager` - Database manager
- `tool_registry: ToolRegistry` - MCP tool registry

**Key Bindings:**
- `Ctrl+Q` - Quit
- `Ctrl+D` - Toggle dark mode
- `Ctrl+S` - Save conversation
- `Ctrl+N` - New chat
- `Ctrl+E` - Edit in external editor
- `F1` - Help

### promptriff.ui.chat

Chat interface components.

#### Classes

##### `ChatInterface`
Main chat interface widget.

**Methods:**
- `add_message(message: Message)` - Add message to chat
- `start_streaming() -> StreamingMessage` - Start streaming response
- `finalize_streaming() -> Optional[Message]` - Finalize streaming
- `clear_messages()` - Clear all messages

### promptriff.ui.menus

Menu components for model and tool selection.

#### Classes

##### `ModelSelector`
Widget for selecting AI models.

**Events:**
- `ModelChanged(provider: str, model: str)` - Model selection changed

##### `ToolSelector`
Widget for selecting MCP tools.

**Events:**
- `ToolsChanged(enabled_tools: List[str])` - Tool selection changed

### promptriff.ui.diff

Diff viewer for prompt comparison.

#### Classes

##### `DiffViewer`
Side-by-side diff viewer widget.

**Methods:**
- `set_content(left: str, right: str)` - Set content to compare
- `clear()` - Clear the diff viewer

## Error Handling

All API methods may raise the following exceptions:

- `ValueError` - Invalid configuration or parameters
- `ConnectionError` - Network or API connection issues
- `TimeoutError` - Request timeout
- `AuthenticationError` - Invalid API credentials

Example error handling:

```python
try:
    provider = get_provider("openai", api_key="...")
    models = await provider.list_models()
except ValueError as e:
    print(f"Configuration error: {e}")
except ConnectionError as e:
    print(f"Connection error: {e}")
```