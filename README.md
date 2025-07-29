# PromptRiff

Open Source LLM Prompt Experimentation tool - A terminal-based UI for interacting with multiple AI language models (OpenAI, Claude, Gemini) with integrated MCP tool support.

## Features

- **Multi-Provider Support**: Seamlessly switch between OpenAI GPT, Anthropic Claude, and Google Gemini models
- **MCP Tool Integration**: Built-in support for Model Context Protocol tools
- **Prompt Version Management**: Track and compare different prompt versions
- **Vi-Style Navigation**: Familiar keybindings for efficient terminal use
- **External Editor Support**: Edit prompts in your favorite text editor
- **Conversation History**: Full SQLite-backed conversation persistence
- **Streaming Responses**: Real-time streaming from all providers
- **Diff Visualization**: Compare prompts and responses side-by-side

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/promptriff.git
cd promptriff

# Install with uv (recommended)
uv sync

# Or install with pip
pip install -e .
```

## Configuration

1. Copy the example configuration:
```bash
mkdir -p ~/.config/promptriff
cp examples/config.example.yaml ~/.config/promptriff/config.yaml
```

2. Set your API keys as environment variables:
```bash
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key" 
export GOOGLE_API_KEY="your-google-key"
```

Or add them directly to your config file.

## Usage

```bash
# Run the application
promptriff

# Or use the short alias
priff

# Run in development mode with debug output
promptriff --dev

# Use a custom config file
promptriff --config /path/to/config.yaml
```

## Development

```bash
# Install development dependencies
uv sync

# Run tests
make test

# Run linters
make lint

# Format code
make format

# Initialize database
make db-init

# Start development server
make dev
```

## Keyboard Shortcuts

PromptRiff uses vi-style keybindings:

- Navigation: `h`, `j`, `k`, `l`
- Insert mode: `i`
- Normal mode: `ESC`
- Save: `:w`
- Quit: `:q`
- Save and quit: `:wq`
- Search forward: `/`
- Search backward: `?`
- Copy: `y`
- Paste: `p`
- Next tab: `gt`
- Previous tab: `gT`

## License

MIT License - see LICENSE file for details.
