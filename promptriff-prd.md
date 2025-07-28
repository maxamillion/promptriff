# Product Requirements Document: PromptRiff

## 1. Product Overview

### 1.1 Product Name
**PromptRiff**

### 1.2 Product Description
PromptRiff is a terminal-based user interface for interacting with multiple AI language models (Gemini, Claude, OpenAI) with integrated Model Context Protocol (MCP) tool support. The application enables prompt engineers to test and compare different prompts across various AI models while leveraging MCP tools, with a focus on efficient workflow and prompt version management.

### 1.3 Key Objectives
- Provide a unified terminal interface for multiple AI model providers
- Enable seamless integration with MCP tools
- Support prompt versioning and comparison
- Maintain conversation and prompt history
- Allow external text editor integration for prompt editing

## 2. Technical Architecture

### 2.1 Technology Stack
- **Language**: Python
- **Package Manager**: uv
- **TUI Framework**: Textual
- **MCP Integration**: mcp-client, Model Context Protocol Python SDK
- **Database**: SQLite
- **Build System**: Makefile

### 2.2 Supported AI Providers
- OpenAI (GPT models)
- Anthropic (Claude models)
- Google (Gemini models)

## 3. Functional Requirements

### 3.1 Configuration Management

#### 3.1.1 Configuration File
- Support for YAML/TOML configuration file
- Store API keys, endpoints, and model preferences
- Store MCP tool configurations
- Store default settings and preferences

#### 3.1.2 Environment Variable Overrides
- Support command-line environment variable overrides for all configuration values
- Priority: Environment variables > Configuration file > Defaults

#### 3.1.3 Configuration Schema
```yaml
# ~/.config/promptriff/config.yaml
models:
  openai:
    api_key: ${OPENAI_API_KEY}
    endpoint: https://api.openai.com/v1
    default_model: gpt-4
  claude:
    api_key: ${ANTHROPIC_API_KEY}
    endpoint: https://api.anthropic.com/v1
    default_model: claude-3-opus-20240229
  gemini:
    api_key: ${GOOGLE_API_KEY}
    endpoint: https://generativelanguage.googleapis.com/v1
    default_model: gemini-pro

mcp_tools:
  - name: tool_name
    path: /path/to/tool
    enabled: true
    config: {}

ui:
  theme: dark
  editor: $EDITOR
  diff_syntax_highlighting: true
```

### 3.2 User Interface Components

#### 3.2.1 Model Selection Menu
- Display list of configured model providers
- Show available models for each provider
- Allow selection of active model
- Display connection status

#### 3.2.2 MCP Tools Menu
- Display all configured MCP tools
- Toggle enable/disable state for each tool per prompt
- Show tool status and availability
- Display tool descriptions and capabilities

#### 3.2.3 Chat Interface
- Text input area for prompts
- Support for multi-line input
- Display streaming responses in real-time
- Show model and active tools indicators
- Conversation history scrollback

#### 3.2.4 Prompt Comparison View
- Side-by-side display of:
  - Current prompt vs. selected historical prompt
  - Current output vs. historical output
- Syntax highlighting for differences
- Navigation between different versions
- Diff statistics (additions, deletions, modifications)

#### 3.2.5 Prompt Library View
- List all historical prompts
- Search and filter capabilities
- Sort by date, model, or custom tags
- Quick preview of prompts and outputs

### 3.3 Core Features

#### 3.3.1 External Editor Integration
- Launch user's preferred text editor for prompt editing
- Support for $EDITOR environment variable
- Save edited prompt back to application
- Temporary file management

#### 3.3.2 Streaming Response Support
- Real-time display of AI model responses
- Progress indicators
- Ability to cancel ongoing requests
- Proper handling of partial responses

#### 3.3.3 Keyboard Shortcuts (Vi-style)
- Navigation: `h`, `j`, `k`, `l`
- Mode switching: `i` (insert), `ESC` (normal)
- Commands: `:w` (save), `:q` (quit), `:wq` (save and quit)
- Search: `/` (forward search), `?` (backward search)
- Copy/paste: `y` (yank), `p` (paste)
- Tab navigation: `gt` (next tab), `gT` (previous tab)

#### 3.3.4 Data Import/Export
- Export formats: JSON, Markdown
- Export options:
  - Individual conversations
  - Prompt templates
  - Full conversation history
- Import validation and conflict resolution

### 3.4 Data Persistence

#### 3.4.1 SQLite Database Schema
```sql
-- Conversations table
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    title TEXT,
    model_provider TEXT,
    model_name TEXT
);

-- Prompts table
CREATE TABLE prompts (
    id INTEGER PRIMARY KEY,
    conversation_id INTEGER,
    created_at TIMESTAMP,
    content TEXT,
    active_tools JSON,
    metadata JSON,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);

-- Responses table
CREATE TABLE responses (
    id INTEGER PRIMARY KEY,
    prompt_id INTEGER,
    created_at TIMESTAMP,
    content TEXT,
    model_provider TEXT,
    model_name TEXT,
    metadata JSON,
    FOREIGN KEY (prompt_id) REFERENCES prompts(id)
);

-- Prompt templates table
CREATE TABLE prompt_templates (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    content TEXT,
    tags JSON,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

## 4. Non-Functional Requirements

### 4.1 Performance
- Response time for UI interactions: < 100ms
- Support for conversations with 1000+ messages
- Efficient diff computation for large prompts
- Minimal memory footprint

### 4.2 Security
- Secure storage of API keys (never in plain text in database)
- Input sanitization for all user inputs
- Secure handling of temporary files for external editor
- No logging of sensitive data
- Rate limiting awareness for API calls
- Proper SSL/TLS certificate validation

### 4.3 Usability
- Intuitive vi-style navigation
- Clear error messages with actionable information
- Responsive UI during long-running operations
- Comprehensive help system (`:help` command)

### 4.4 Reliability
- Graceful handling of API failures
- Automatic retry with exponential backoff
- Data integrity checks for database operations
- Crash recovery for unsaved prompts

## 5. Development Requirements

### 5.1 Makefile Targets
```makefile
# Development
dev:          # Run development server with hot reload
test:         # Run all tests
test-watch:   # Run tests in watch mode
lint:         # Run all linters (ruff, mypy)
format:       # Format code with black/ruff
type-check:   # Run mypy type checking

# Build
build:        # Build application
install:      # Install dependencies with uv
clean:        # Clean build artifacts

# Database
db-init:      # Initialize database
db-migrate:   # Run database migrations
db-backup:    # Backup database

# Release
release:      # Build release version
package:      # Create distributable package
```

### 5.2 Project Structure
```
promptriff/
├── Makefile
├── pyproject.toml
├── README.md
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   └── schema.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── openai.py
│   │   ├── claude.py
│   │   └── gemini.py
│   ├── mcp/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   └── tools.py
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── app.py
│   │   ├── chat.py
│   │   ├── diff.py
│   │   └── menus.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── migrations/
│   └── utils/
│       ├── __init__.py
│       ├── editor.py
│       └── export.py
├── tests/
├── docs/
└── examples/
    └── config.example.yaml
```

## 6. Future Considerations

### 6.1 Potential Enhancements
- Plugin system for custom model providers
- Collaborative features (sharing prompts/templates)
- Advanced analytics and metrics
- Integration with version control systems
- Support for image/multimodal inputs
- Prompt chaining and workflows

### 6.2 Scalability Considerations
- Migration path from SQLite to PostgreSQL if needed
- Distributed MCP tool execution
- Cloud sync capabilities

## 7. Success Criteria

- Successfully connect to all three AI providers
- Execute MCP tools within conversations
- Maintain full conversation history
- Provide accurate diff visualization
- Support all defined keyboard shortcuts
- Pass all security best practices
- Achieve <100ms UI response time
- Support external editor workflow seamlessly

## 8. Constraints and Assumptions

### 8.1 Constraints
- Terminal-only interface (no GUI)
- Python ecosystem only
- Local SQLite database
- Requires API keys for model providers

### 8.2 Assumptions
- Users are familiar with terminal applications
- Users have valid API keys for at least one provider
- Users are comfortable with vi-style navigation
- Local file system access is available
- Python 3.9+ is installed

## 9. Branding and Identity

### 9.1 Name
**PromptRiff** - A play on "riff" in music, suggesting improvisation and iteration on prompts

### 9.2 Command Line Interface
- Primary command: `promptriff`
- Aliases: `priff`

### 9.3 Configuration Paths
- Config directory: `~/.config/promptriff/`
- Database location: `~/.local/share/promptriff/promptriff.db`
- Cache directory: `~/.cache/promptriff/`