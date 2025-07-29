# Contributing to PromptRiff

Thank you for your interest in contributing to PromptRiff! This guide will help you get started.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct:
- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive criticism
- Respect differing viewpoints and experiences

## How to Contribute

### Reporting Issues

1. Check if the issue already exists
2. Use the issue template
3. Include:
   - Clear description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - System information (OS, Python version - must be 3.10+)
   - Relevant logs or error messages

### Suggesting Features

1. Check existing feature requests
2. Open a discussion first for major features
3. Explain the use case and benefits
4. Consider implementation complexity

### Submitting Code

#### Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/yourusername/promptriff.git
   cd promptriff
   ```

3. Set up development environment:
   ```bash
   uv sync --all-extras
   make install-dev
   ```

4. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

#### Development Workflow

1. Make your changes
2. Add tests for new functionality
3. Ensure all tests pass:
   ```bash
   make test
   ```

4. Check code quality:
   ```bash
   make lint
   make type-check
   ```

5. Format code:
   ```bash
   make format
   ```

6. Commit your changes:
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

#### Commit Message Guidelines

We follow the Conventional Commits specification:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `perf:` Performance improvements
- `test:` Test additions or fixes
- `chore:` Build process or auxiliary tool changes

Examples:
```
feat: add support for GPT-4 Vision model
fix: resolve connection timeout with Claude API
docs: update installation guide for Windows
refactor: simplify message streaming logic
```

#### Pull Request Process

1. Update documentation for any API changes
2. Add tests for new functionality
3. Update CHANGELOG.md if applicable
4. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

5. Create a Pull Request with:
   - Clear title and description
   - Link to related issues
   - Screenshots for UI changes
   - Test results

### Testing

#### Running Tests

```bash
# Run all tests
make test

# Run specific test file
uv run pytest tests/test_models.py

# Run with coverage
uv run pytest --cov

# Run in watch mode
make test-watch
```

#### Writing Tests

- Place tests in `tests/` directory
- Mirror source structure
- Use descriptive test names
- Test both success and failure cases
- Mock external API calls

Example test:
```python
@pytest.mark.asyncio
async def test_openai_provider_list_models():
    """Test that OpenAI provider can list models."""
    provider = OpenAIProvider(api_key="test-key")
    
    # Mock API response
    provider.client.models.list = AsyncMock(...)
    
    models = await provider.list_models()
    assert "gpt-4" in models
```

### Documentation

#### Documentation Standards

- Use clear, concise language
- Include code examples
- Keep it up-to-date with code changes
- Use proper markdown formatting
- Add screenshots for UI features

#### Building Documentation

```bash
# Install documentation dependencies
pip install mkdocs mkdocs-material

# Serve documentation locally
mkdocs serve

# Build documentation
mkdocs build
```

### Code Style

#### Python Style Guide

- Follow PEP 8
- Use type hints
- Maximum line length: 88 characters
- Use descriptive variable names
- Add docstrings to all public functions

#### Type Hints

```python
from typing import List, Optional, Dict, Any

async def process_messages(
    messages: List[Message],
    model: str,
    temperature: float = 0.7,
    tools: Optional[List[Dict[str, Any]]] = None
) -> AsyncIterator[Response]:
    """Process messages and return responses.
    
    Args:
        messages: List of conversation messages
        model: Model identifier to use
        temperature: Sampling temperature (0-2)
        tools: Optional MCP tools
        
    Yields:
        Response chunks if streaming
    """
    pass
```

### Security

#### Security Guidelines

- Never commit API keys or secrets
- Validate all user inputs
- Use parameterized queries
- Follow OWASP guidelines
- Report security issues privately

#### Handling Secrets

```python
# Good
api_key = os.environ.get("OPENAI_API_KEY")

# Bad
api_key = "sk-1234567890abcdef"
```

### Performance

#### Performance Considerations

- Use async/await for I/O operations
- Stream responses when possible
- Implement proper caching
- Profile before optimizing
- Consider memory usage

#### Profiling

```bash
# Profile the application
python -m cProfile -o profile.stats src/promptriff/__main__.py

# Analyze results
python -m pstats profile.stats
```

## Project Structure

```
promptriff/
├── src/promptriff/     # Source code
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

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create release PR
4. After merge, tag release:
   ```bash
   git tag -a v1.2.3 -m "Release version 1.2.3"
   git push origin v1.2.3
   ```

## Getting Help

- Check documentation first
- Search existing issues
- Ask in discussions
- Join our community chat

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project documentation

Thank you for contributing to PromptRiff! 🎸