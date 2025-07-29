# PromptRiff

> 🎸 Terminal-based AI prompt experimentation tool with MCP support

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

PromptRiff is a powerful terminal user interface for interacting with multiple AI language models (OpenAI, Claude, Gemini) with integrated Model Context Protocol (MCP) tool support. Test and compare prompts across different models, manage conversation history, and leverage MCP tools - all from your terminal.

## Features

- 🤖 **Multi-Model Support**: Seamlessly switch between OpenAI, Claude, and Gemini models
- 🛠️ **MCP Integration**: Full support for Model Context Protocol tools
- 📝 **External Editor**: Edit prompts in your favorite text editor
- 🔄 **Prompt Versioning**: Compare different versions of prompts and their outputs
- 💾 **Persistent History**: SQLite-backed conversation and prompt storage
- ⌨️ **Vi-style Keybindings**: Efficient navigation for power users
- 🎨 **Rich TUI**: Beautiful terminal interface built with Textual
- 📊 **Diff Visualization**: Side-by-side comparison with syntax highlighting

## Installation

### Using uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/promptriff.git
cd promptriff

# Install with uv
uv sync

# Run the application
make run
# Or directly with uv:
uv run promptriff
```

### Using pip

```bash
# Clone the repository
git clone https://github.com/yourusername/promptriff.git
cd promptriff

# Install in development mode
pip install -e .

# Run the application
promptriff
```

## Configuration

1. Copy the example configuration:
   ```bash
   cp examples/config.example.yaml ~/.config/promptriff/config.yaml
   ```

2. Edit the configuration file and add your API keys:
   ```yaml
   models:
     openai:
       api_key: ${OPENAI_API_KEY}  # or set directly
       default_model: gpt-4
     claude:
       api_key: ${ANTHROPIC_API_KEY}
       default_model: claude-3-opus-20240229
     gemini:
       api_key: ${GOOGLE_API_KEY}
       default_model: gemini-pro
   ```

3. Alternatively, set environment variables:
   ```bash
   export OPENAI_API_KEY="your-api-key"
   export ANTHROPIC_API_KEY="your-api-key"
   export GOOGLE_API_KEY="your-api-key"
   ```

## Usage

### Basic Commands

```bash
# Start PromptRiff
promptriff

# Use a specific config file
promptriff --config ~/my-config.yaml

# Run in development mode
promptriff --dev

# Enable debug logging
promptriff --debug
```

### Keyboard Shortcuts

| Key | Action | Description |
|-----|--------|-------------|
| `Ctrl+Q` | Quit | Exit the application |
| `Ctrl+S` | Save | Save current conversation |
| `Ctrl+N` | New Chat | Start a new chat |
| `Ctrl+D` | Dark Mode | Toggle dark/light theme |
| `Tab` | Next Tab | Navigate between tabs |
| `i` | Insert Mode | Enter text input mode |
| `Esc` | Normal Mode | Exit input mode |
| `/` | Search | Search in current view |
| `F1` | Help | Show help screen |

### Vi-style Navigation

- `h`, `j`, `k`, `l` - Navigate left, down, up, right
- `gg` - Go to top
- `G` - Go to bottom
- `Ctrl+F` - Page down
- `Ctrl+B` - Page up

## Development

### Setup Development Environment

```bash
# Install development dependencies
make install-dev

# Run tests
make test

# Run linters
make lint

# Format code
make format

# Run type checking
make type-check
```

### Project Structure

```
promptriff/
├── src/promptriff/
│   ├── config/         # Configuration management
│   ├── models/         # AI provider integrations
│   ├── mcp/           # MCP tool integration
│   ├── ui/            # Terminal UI components
│   ├── database/      # Data persistence
│   └── utils/         # Utility functions
├── tests/             # Test suite
├── docs/              # Documentation
└── examples/          # Example configurations
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Textual](https://github.com/Textualize/textual) - Amazing TUI framework
- MCP integration powered by [Model Context Protocol](https://modelcontextprotocol.io)
- Inspired by the need for better prompt engineering workflows
