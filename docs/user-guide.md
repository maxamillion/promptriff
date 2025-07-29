# PromptRiff User Guide

## Overview

PromptRiff is a terminal-based AI prompt experimentation tool that allows you to interact with multiple AI models (OpenAI, Claude, Gemini) while leveraging MCP tools for enhanced capabilities.

## Getting Started

### Starting PromptRiff

Launch PromptRiff from your terminal:
```bash
promptriff
```

You'll see the main interface with several tabs:
- **Chat**: Main conversation interface
- **Models**: Select and configure AI models
- **Tools**: Enable/disable MCP tools
- **Library**: Browse conversation history
- **Compare**: Compare different prompts and responses

### Navigating the Interface

PromptRiff uses vi-style keybindings for efficient navigation:

- `Tab` / `Shift+Tab`: Switch between tabs
- `h`, `j`, `k`, `l`: Navigate left, down, up, right
- `i`: Enter insert mode (for text input)
- `Esc`: Exit insert mode
- `/`: Search within current view
- `Ctrl+Q`: Quit the application

## Basic Chat Workflow

### 1. Select a Model

Navigate to the **Models** tab:
1. Use arrow keys or `j`/`k` to select a provider (OpenAI, Claude, Gemini)
2. Press `Enter` to confirm provider selection
3. Select a specific model from the list
4. The status indicator shows connection status

### 2. Enable MCP Tools (Optional)

Navigate to the **Tools** tab:
1. Check/uncheck tools you want to enable
2. Use `Space` to toggle individual tools
3. Use "Select All" or "Deselect All" buttons for bulk operations

### 3. Start Chatting

Return to the **Chat** tab:
1. Type your prompt in the input field
2. Press `Enter` to send (or click "Send")
3. Watch the AI response stream in real-time
4. Continue the conversation as needed

## Advanced Features

### External Editor Integration

Edit complex prompts in your preferred text editor:

1. Press `Ctrl+E` while in the chat interface
2. Your configured editor opens with the current prompt
3. Edit and save the file
4. The prompt updates automatically

Configure your editor in `~/.config/promptriff/config.yaml`:
```yaml
ui:
  editor: vim  # or code, nano, emacs, etc.
```

### Prompt Library

Browse and reuse previous conversations:

1. Navigate to the **Library** tab
2. View all saved conversations with metadata
3. Use arrow keys to select a conversation
4. Press `Enter` to load it (feature coming soon)

### Prompt Comparison

Compare different versions of prompts and their outputs:

1. Navigate to the **Compare** tab
2. Load two different prompts or responses
3. View side-by-side diff with:
   - Green highlights for additions
   - Red highlights for deletions
   - Statistics showing changes

### Keyboard Shortcuts Reference

| Shortcut | Action | Description |
|----------|--------|-------------|
| `Ctrl+Q` | Quit | Exit PromptRiff |
| `Ctrl+D` | Dark Mode | Toggle dark/light theme |
| `Ctrl+S` | Save | Export current conversation |
| `Ctrl+O` | Open | Import conversation |
| `Ctrl+N` | New Chat | Start fresh conversation |
| `Ctrl+E` | Edit | Open external editor |
| `F1` | Help | Show help screen |
| `Tab` | Next Tab | Navigate between tabs |
| `i` | Insert | Enter text input mode |
| `Esc` | Normal | Exit input mode |
| `/` | Search | Search in current view |

## Working with MCP Tools

### Understanding MCP Tools

MCP (Model Context Protocol) tools extend AI capabilities by providing:
- File system access
- Web search capabilities
- Calculation functions
- Custom integrations

### Using Tools in Conversations

When tools are enabled:
1. The AI can automatically use them to answer questions
2. Tool calls appear in the conversation
3. Results are integrated into responses

Example prompts that leverage tools:
- "Read the file at /path/to/file.txt and summarize it"
- "Search the web for recent news about AI"
- "Calculate the compound interest for $1000 at 5% over 10 years"

## Data Management

### Saving Conversations

Press `Ctrl+S` to export the current conversation:
- Exports to Markdown format by default
- Includes all messages and metadata
- Saves to current directory with timestamp

### Importing Conversations

Press `Ctrl+O` to import a previous conversation:
- Supports JSON and Markdown formats
- Preserves message history
- Allows continuing from where you left off

### Database Location

PromptRiff stores all data in a local SQLite database:
- Default location: `~/.local/share/promptriff/promptriff.db`
- Automatic backups on startup (configurable)
- Use `make db-backup` to create manual backups

## Tips and Tricks

### Efficient Prompt Writing

1. **Use the external editor** for long or complex prompts
2. **Save prompt templates** in the library for reuse
3. **Compare variations** to see what works best
4. **Enable relevant tools** before starting

### Performance Optimization

1. **Stream responses** for faster feedback
2. **Disable unused tools** to reduce overhead
3. **Clear old conversations** to keep the library manageable
4. **Use appropriate models** for the task complexity

### Troubleshooting Common Issues

**No response from AI:**
- Check your API key configuration
- Verify internet connection
- Ensure selected model is available

**Tools not working:**
- Verify tool installation and path
- Check tool permissions
- Review tool-specific configuration

**Slow performance:**
- Try a faster model (e.g., GPT-3.5-turbo, Claude Haiku)
- Disable syntax highlighting for large responses
- Clear conversation history if very long

## Advanced Configuration

See the [Configuration Guide](configuration.md) for detailed options:
- Custom themes
- Model parameters
- Tool configurations
- Performance tuning

## Getting Help

- Press `F1` within PromptRiff for quick help
- Check the [FAQ](faq.md) for common questions
- Report issues on [GitHub](https://github.com/yourusername/promptriff/issues)