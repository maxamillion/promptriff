# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

```bash
# Run the application
make run  # or: uv run python -m promptriff

# Development with hot reload
make dev  # or: uv run python -m promptriff --dev

# Run all tests
make test  # or: uv run pytest

# Run specific test file
uv run pytest tests/test_models.py

# Run tests in watch mode
make test-watch  # or: uv run pytest-watch

# Code quality checks (run all before committing)
make lint       # ruff check + mypy
make format     # black + ruff fix
make type-check # mypy src/

# Database operations
make db-init    # Initialize new database
make db-migrate # Run migrations
make db-backup  # Backup to backups/ directory
```

## Architecture Overview

### Core Design Patterns

1. **Model Provider Abstraction**: All LLM providers (OpenAI, Claude, Gemini) inherit from `ModelProvider` base class in `src/promptriff/models/base.py`. Each provider must implement:
   - `list_models()`: Return available models
   - `chat_completion()`: Streaming response generation
   - `validate_api_key()`: API key validation

2. **MCP Tool Integration**: Tools are external executables managed through the MCP protocol:
   - `MCPClient` handles stdio communication with tool processes
   - `ToolRegistry` manages tool lifecycle and provides LLM-formatted tool definitions
   - Tools are configured in YAML with path, enabled status, and tool-specific config

3. **Async Architecture**: The entire application uses async/await:
   - Textual UI runs in async context
   - All model API calls are async
   - Database operations use aiosqlite/async SQLAlchemy
   - MCP tool calls are async

4. **Configuration Hierarchy**:
   - Environment variables (e.g., `OPENAI_API_KEY`, `PROMPTRIFF_*`)
   - Config file (`~/.config/promptriff/config.yaml`)
   - Default values in Pydantic models

### Key Components

- **UI Layer** (`src/promptriff/ui/`):
  - `app.py`: Main Textual application and screen management
  - `chat.py`: Chat interface with message handling
  - `diff.py`: Diff viewer for comparing outputs
  - Vi-style keybindings implemented throughout

- **Database Layer** (`src/promptriff/database/`):
  - SQLAlchemy models: Conversation → Prompt → Response
  - Async session management with aiosqlite
  - Auto-migration support

- **MCP Integration** (`src/promptriff/mcp/`):
  - Manages external tool processes via stdio
  - Converts tool schemas to OpenAI function format
  - Handles tool discovery and lifecycle

## Development Guidelines

### Adding a New Model Provider

1. Create new file in `src/promptriff/models/` (e.g., `ollama.py`)
2. Inherit from `ModelProvider` base class
3. Implement required abstract methods
4. Add provider to `get_provider()` function in `models/__init__.py`
5. Update config schema if needed

### Working with MCP Tools

- Tools must be executable files that support MCP stdio protocol
- Tool paths in config can use `~` expansion
- Tools receive JSON-RPC messages via stdin, respond via stdout
- Each tool connection creates a separate process

### Database Schema Changes

1. Modify models in `src/promptriff/database/models.py`
2. Create migration script in `src/promptriff/database/migrations/`
3. Update `migrate()` function to apply changes
4. Test with fresh database using `make db-init`

### Testing Patterns

- Mock external API calls in provider tests
- Use `pytest.mark.asyncio` for async test functions
- Place fixtures in `tests/conftest.py`
- Mock MCP tool responses for integration tests

## Configuration Context

### API Key Management
```yaml
# Config supports environment variable expansion
models:
  openai:
    api_key: ${OPENAI_API_KEY}  # Reads from environment
    # Can also use PROMPTRIFF_OPENAI_API_KEY
```

### MCP Tool Configuration
```yaml
mcp_tools:
  - name: filesystem
    path: /usr/local/bin/mcp-filesystem  # Must be executable
    enabled: true
    config:  # Tool-specific configuration passed to tool
      allowed_directories: [~/projects]
```

## Common Workflows

### Running a Single Test
```bash
# Run specific test function
uv run pytest tests/test_models.py::test_openai_provider_list_models -v

# Run with debugging output
uv run pytest tests/test_models.py -s --log-cli-level=DEBUG
```

### Debugging MCP Tools
1. Check tool process is running: Look for subprocess in logs
2. Enable debug mode: `promptriff --debug`
3. Tool communication logged to stderr
4. Validate tool path exists and is executable

### UI Development
- Textual CSS in `src/promptriff/ui/styles.css`
- Use Textual dev tools: `textual run --dev src/promptriff/__main__.py`
- Keybindings defined in `MainScreen` class bindings