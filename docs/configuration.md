# Configuration Guide

## Configuration File

PromptRiff uses a YAML configuration file to manage settings. The default location is `~/.config/promptriff/config.yaml`.

### File Locations

PromptRiff looks for configuration in the following order:
1. Path specified with `--config` flag
2. `~/.config/promptriff/config.yaml`
3. `~/.config/promptriff/config.yml`
4. `~/.promptriff.yaml`
5. `~/.promptriff.yml`

### Directory Structure

```
~/.config/promptriff/     # Configuration files
~/.local/share/promptriff/  # Database and data files
~/.cache/promptriff/      # Cache files
```

## Configuration Options

### Models Configuration

Configure AI model providers and their settings:

```yaml
models:
  openai:
    api_key: ${OPENAI_API_KEY}  # Environment variable reference
    endpoint: https://api.openai.com/v1  # Optional custom endpoint
    default_model: gpt-4
    timeout: 30  # Request timeout in seconds
    max_retries: 3  # Maximum retry attempts

  claude:
    api_key: ${ANTHROPIC_API_KEY}
    endpoint: https://api.anthropic.com/v1
    default_model: claude-3-opus-20240229
    timeout: 30
    max_retries: 3

  gemini:
    api_key: ${GOOGLE_API_KEY}
    endpoint: https://generativelanguage.googleapis.com/v1
    default_model: gemini-pro
    timeout: 30
    max_retries: 3
```

#### Available Models

**OpenAI:**
- `gpt-4` - Most capable model
- `gpt-4-turbo-preview` - Faster GPT-4 variant
- `gpt-3.5-turbo` - Fast and cost-effective
- `gpt-3.5-turbo-16k` - Extended context window

**Claude:**
- `claude-3-opus-20240229` - Most capable
- `claude-3-sonnet-20240229` - Balanced performance
- `claude-3-haiku-20240307` - Fast and efficient
- `claude-2.1` - Previous generation
- `claude-instant-1.2` - Fastest option

**Gemini:**
- `gemini-pro` - General purpose
- `gemini-pro-vision` - Multimodal support
- `gemini-ultra` - Most advanced (when available)

### MCP Tools Configuration

Configure Model Context Protocol tools:

```yaml
mcp_tools:
  - name: filesystem
    path: /usr/local/bin/mcp-filesystem
    enabled: true
    config:
      allowed_directories:
        - ~/projects
        - /tmp
      max_file_size: 10485760  # 10MB

  - name: web_search
    path: /usr/local/bin/mcp-websearch
    enabled: true
    config:
      api_key: ${SEARCH_API_KEY}
      max_results: 10
      safe_search: true

  - name: calculator
    path: /usr/local/bin/mcp-calculator
    enabled: true
    config: {}
```

### UI Configuration

Customize the user interface:

```yaml
ui:
  theme: dark  # Options: dark, light
  editor: ${EDITOR}  # External editor command
  diff_syntax_highlighting: true  # Enable syntax highlighting in diffs
  max_response_lines: 1000  # Maximum lines to display per response
  autosave_interval: 60  # Auto-save interval in seconds
```

#### External Editor

The editor setting supports:
- Environment variable: `${EDITOR}`
- Specific commands: `vim`, `nvim`, `nano`, `emacs`, `code`, `subl`
- Custom commands with arguments: `code --wait`

### Database Configuration

Database settings:

```yaml
database:
  path: ~/.local/share/promptriff/promptriff.db  # Database file location
  backup_on_startup: true  # Create backup when starting
  vacuum_on_startup: false  # Optimize database on startup
```

### Debug Mode

Enable debug mode for troubleshooting:

```yaml
debug: true  # Enable debug logging
```

## Environment Variables

### Configuration Overrides

Environment variables can override configuration file settings:

```bash
# Model API keys
export PROMPTRIFF_OPENAI_API_KEY="sk-..."
export PROMPTRIFF_CLAUDE_API_KEY="sk-ant-..."
export PROMPTRIFF_GEMINI_API_KEY="..."

# Model endpoints (optional)
export PROMPTRIFF_OPENAI_ENDPOINT="https://custom.openai.com/v1"
export PROMPTRIFF_CLAUDE_ENDPOINT="https://custom.anthropic.com/v1"
export PROMPTRIFF_GEMINI_ENDPOINT="https://custom.google.com/v1"

# Default models
export PROMPTRIFF_OPENAI_MODEL="gpt-4"
export PROMPTRIFF_CLAUDE_MODEL="claude-3-opus-20240229"
export PROMPTRIFF_GEMINI_MODEL="gemini-pro"

# UI settings
export PROMPTRIFF_THEME="light"
export PROMPTRIFF_DEBUG="true"

# Directories
export PROMPTRIFF_CONFIG_DIR="~/custom/config"
export PROMPTRIFF_DATA_DIR="~/custom/data"
export PROMPTRIFF_CACHE_DIR="~/custom/cache"
```

### Priority Order

Configuration priority (highest to lowest):
1. Command-line flags
2. Environment variables
3. Configuration file
4. Default values

## Advanced Configuration

### Custom Themes

While PromptRiff currently supports dark/light themes, you can customize the appearance by modifying the CSS file at `src/promptriff/ui/styles.css`.

### Model Parameters

You can pass additional parameters to models through the API:

```python
# In your prompt metadata or tool configuration
{
  "temperature": 0.7,
  "max_tokens": 2000,
  "top_p": 0.9,
  "frequency_penalty": 0.0,
  "presence_penalty": 0.0
}
```

### Performance Tuning

#### Response Streaming
- Always enabled by default for better UX
- Disable for batch processing scenarios

#### Token Limits
```yaml
models:
  openai:
    default_model: gpt-4
    # Model-specific settings can be added
    model_config:
      gpt-4:
        max_tokens: 4000
      gpt-3.5-turbo:
        max_tokens: 2000
```

#### Database Performance
```yaml
database:
  vacuum_on_startup: true  # Enable for better performance
  # Additional SQLite pragmas can be configured
  pragmas:
    journal_mode: WAL
    synchronous: NORMAL
```

## Security Considerations

### API Key Storage

1. **Never commit API keys** to version control
2. Use environment variables for production
3. Set restrictive permissions on config files:
   ```bash
   chmod 600 ~/.config/promptriff/config.yaml
   ```

### MCP Tool Security

1. **Restrict tool access** to specific directories
2. **Validate tool paths** before enabling
3. **Review tool permissions** regularly
4. **Disable unused tools** to reduce attack surface

### Database Security

1. **Regular backups**: Enable `backup_on_startup`
2. **File permissions**: Ensure database file is protected
3. **Encryption**: Consider disk encryption for sensitive data

## Troubleshooting Configuration

### Viewing Active Configuration

Run with debug mode to see active configuration:
```bash
promptriff --debug
```

### Common Issues

**API Key Not Found:**
- Check environment variable names
- Verify YAML syntax in config file
- Ensure proper quoting of keys

**Tool Connection Failed:**
- Verify tool executable path
- Check file permissions
- Review tool-specific logs

**Database Errors:**
- Check file permissions
- Ensure directory exists
- Try database re-initialization

### Configuration Validation

PromptRiff validates configuration on startup and reports:
- Missing required fields
- Invalid API keys
- Inaccessible tool paths
- Permission issues