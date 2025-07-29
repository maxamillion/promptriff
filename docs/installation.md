# Installation Guide

## Prerequisites

- Python 3.10 or higher
- `uv` package manager (recommended) or `pip`
- API keys for at least one AI provider (OpenAI, Claude, or Gemini)

## Installation Methods

### Using uv (Recommended)

1. Install uv if you haven't already:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/promptriff.git
   cd promptriff
   ```

3. Install dependencies:
   ```bash
   uv sync
   ```

4. Initialize the database:
   ```bash
   uv run make db-init
   ```

### Using pip

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/promptriff.git
   cd promptriff
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the package:
   ```bash
   pip install -e .
   ```

4. Initialize the database:
   ```bash
   python -m promptriff.database.init
   ```

## Configuration

1. Create the configuration directory:
   ```bash
   mkdir -p ~/.config/promptriff
   ```

2. Copy the example configuration:
   ```bash
   cp examples/config.example.yaml ~/.config/promptriff/config.yaml
   ```

3. Edit the configuration file and add your API keys:
   ```yaml
   models:
     openai:
       api_key: "your-openai-api-key"
       default_model: "gpt-4"
     claude:
       api_key: "your-anthropic-api-key"
       default_model: "claude-3-opus-20240229"
     gemini:
       api_key: "your-google-api-key"
       default_model: "gemini-pro"
   ```

### Using Environment Variables

Instead of adding API keys to the config file, you can use environment variables:

```bash
export OPENAI_API_KEY="your-openai-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
export GOOGLE_API_KEY="your-google-api-key"
```

Or create a `.env` file in the project directory:
```
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
GOOGLE_API_KEY=your-google-api-key
```

## MCP Tool Setup

To use MCP tools, you need to install and configure them:

1. Install an MCP tool (example):
   ```bash
   npm install -g @modelcontextprotocol/tool-filesystem
   ```

2. Add the tool to your configuration:
   ```yaml
   mcp_tools:
     - name: filesystem
       path: /usr/local/bin/mcp-filesystem
       enabled: true
       config:
         allowed_directories:
           - ~/projects
   ```

## Verification

Run PromptRiff to verify the installation:

```bash
uv run promptriff
# or if installed with pip:
promptriff
```

You should see the PromptRiff TUI interface. Press `Ctrl+Q` to quit.

## Troubleshooting

### Database Issues

If you encounter database errors, try reinitializing:
```bash
uv run make db-init
```

### API Key Errors

Ensure your API keys are correctly set. You can verify with:
```bash
echo $OPENAI_API_KEY  # Should show your key (or use the appropriate env var)
```

### MCP Tool Connection Errors

1. Verify the tool is installed and the path is correct
2. Check that the tool executable has proper permissions
3. Review the tool's documentation for specific configuration requirements

## Next Steps

- Read the [User Guide](user-guide.md) to learn how to use PromptRiff
- Configure your preferred [external editor](configuration.md#external-editor)
- Set up [MCP tools](mcp-tools.md) for enhanced functionality