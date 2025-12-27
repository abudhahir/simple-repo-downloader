# Simple Repository Downloader

A simple, efficient tool for downloading all repositories from GitHub or GitLab users/organizations.

## Features

- **Parallel Downloads** - Configurable concurrent cloning for maximum speed
- **Real-time Dashboard** - Live progress tracking with interactive TUI
- **Interactive Command Shell** - Control downloads on the fly
- **Smart Error Handling** - Collect and resolve issues interactively
- **Multi-platform** - Support for both GitHub and GitLab
- **Flexible Configuration** - CLI args, config files, or programmatic API
- **Resume Capability** - Pick up where you left off after interruption

## Installation

```bash
# From PyPI (when published)
pip install simple-repo-downloader

# From source
git clone https://github.com/yourusername/simple-repo-downloader
cd simple-repo-downloader
pip install -e .
```

## Quick Start

### Download all repos from a GitHub user

```bash
repo-dl download github torvalds
```

### Download with authentication

```bash
export GITHUB_TOKEN=ghp_xxxxxxxxxxxx
repo-dl download github myusername
```

### Using a configuration file

```bash
repo-dl download --config config.yaml
```

See [CLI Usage Guide](docs/examples/cli-usage.md) for more examples.

## Documentation

- **[Design Document](docs/plans/2025-12-27-repo-downloader-design.md)** - Complete architecture and implementation details
- **[CLI Usage Guide](docs/examples/cli-usage.md)** - Usage examples and recipes
- **[Configuration Example](docs/examples/config-example.yaml)** - Template config file

## Requirements

- Python 3.10 or higher
- Git (must be available in PATH)

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/yourusername/simple-repo-downloader
cd simple-repo-downloader

# Install in development mode with dev dependencies
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Roadmap

See the [Design Document](docs/plans/2025-12-27-repo-downloader-design.md) for planned features and implementation phases.
