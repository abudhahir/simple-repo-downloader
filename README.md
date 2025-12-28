# Simple Repository Downloader

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-35%20passing-brightgreen.svg)]()
[![Coverage](https://img.shields.io/badge/coverage-72%25-green.svg)]()

A powerful, efficient tool for bulk downloading all repositories from GitHub or GitLab users and organizations. Built with Python, featuring parallel downloads, smart error handling, and both CLI and library interfaces.

## ✨ Features

- 🚀 **Parallel Downloads** - Download multiple repositories simultaneously with configurable concurrency (1-20 workers)
- 🌐 **Multi-Platform Support** - Works with both GitHub and GitLab (including self-hosted instances)
- 🔐 **Authentication** - Supports personal access tokens for private repositories and higher rate limits
- ⚙️ **Flexible Configuration** - Use CLI arguments, YAML config files, or Python API
- 🎯 **Smart Filtering** - Include/exclude forks, archived repos, and more
- 📊 **Organized Output** - Repositories saved in `./platform/username/repo-name` structure
- 🛡️ **Error Handling** - Robust error classification and recovery
- 📦 **Full Git Clones** - Complete repository history and all branches
- 🔄 **Environment Variables** - Support for `${VAR_NAME}` syntax in configuration
- 🧪 **Well Tested** - 35 tests with 72% code coverage

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
  - [CLI Usage](#cli-usage)
  - [Configuration File](#configuration-file)
  - [Multi-Credential Configuration](#multi-credential-configuration)
  - [Python API](#python-api)
- [Authentication](#authentication)
- [Advanced Usage](#advanced-usage)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Documentation](#documentation)
- [License](#license)

## 🚀 Installation

### Prerequisites

- **Python 3.10 or higher** - Check with `python --version`
- **Git** - Must be available in PATH, check with `git --version`

### Option 1: From Source (Recommended for now)

```bash
# Clone the repository
git clone https://github.com/abudhahir/simple-repo-downloader.git
cd simple-repo-downloader

# Create and activate virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install -e .

# Verify installation
repo-dl --help
```

### Option 2: Install with Development Dependencies

```bash
# Clone and navigate to directory
git clone https://github.com/abudhahir/simple-repo-downloader.git
cd simple-repo-downloader

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests to verify
pytest
```

### Option 3: From PyPI (Coming Soon)

```bash
pip install simple-repo-downloader
```

## ⚡ Quick Start

### 1. Download all public repos from a GitHub user

```bash
repo-dl download github torvalds
```

This will download all of Linus Torvalds' public repositories to `./repos/github/torvalds/`

### 2. Download with authentication (for private repos)

```bash
# Set your GitHub token - it's automatically detected!
export GITHUB_TOKEN=ghp_your_token_here

# Download your repos (token used automatically)
repo-dl download github your-username
```

### 3. Download from GitLab

```bash
# Set your GitLab token - it's automatically detected!
export GITLAB_TOKEN=glpat_your_token_here

# Download GitLab repos (token used automatically)
repo-dl download gitlab your-username
```

### 4. Control parallel downloads

```bash
# Download 10 repos at once (default is 5)
repo-dl download github kubernetes --max-parallel 10
```

### 5. Exclude forks

```bash
repo-dl download github microsoft --no-forks
```

## 📖 Usage

### CLI Usage

#### Basic Command Structure

```bash
repo-dl download <platform> <username> [OPTIONS]
```

**Platforms:** `github` | `gitlab`

#### Common Options

| Option | Description | Example |
|--------|-------------|---------|
| `--token TEXT` | Authentication token | `--token ghp_xxxxx` |
| `--max-parallel N` | Concurrent downloads (1-20) | `--max-parallel 10` |
| `--output-dir PATH` | Output directory | `--output-dir ~/repos` |
| `--no-forks` | Exclude forked repositories | `--no-forks` |
| `--config PATH` | Use config file | `--config myconfig.yaml` |

#### Examples

**Download from specific user:**
```bash
repo-dl download github octocat
```

**Download organization repos:**
```bash
repo-dl download github microsoft --token $GITHUB_TOKEN --max-parallel 8
```

**Custom output directory:**
```bash
repo-dl download gitlab gitlab-org --output-dir ~/backups
```

**Multiple options:**
```bash
repo-dl download github torvalds \
  --token $GITHUB_TOKEN \
  --max-parallel 10 \
  --no-forks \
  --output-dir ~/linux-repos
```

### Configuration File

Create a YAML configuration file for more complex setups:

**config.yaml:**
```yaml
credentials:
  github_token: ${GITHUB_TOKEN}
  gitlab_token: ${GITLAB_TOKEN}

download:
  base_directory: ./repos
  max_parallel: 5
  include_forks: true
  include_private: true

targets:
  # GitHub user - exclude forks
  - platform: github
    username: torvalds
    filters:
      forks: false
      archived: false

  # GitHub organization - include everything
  - platform: github
    username: microsoft
    filters:
      forks: true
      archived: true

  # GitLab user
  - platform: gitlab
    username: gitlab-org
```

**Run with config:**
```bash
repo-dl download --config config.yaml
```

**Generate template config:**
```bash
# Create a template config file
cat > config.yaml << 'EOF'
credentials:
  github_token: ${GITHUB_TOKEN}
  gitlab_token: ${GITLAB_TOKEN}

download:
  base_directory: ./repos
  max_parallel: 5

targets:
  - platform: github
    username: your-username
    filters:
      forks: false
EOF
```

### Multi-Credential Configuration

For advanced use cases involving multiple accounts (personal + work) or different tokens per platform, use **named credential profiles** with the **grouped targets format**.

#### Named Credential Profiles

Define reusable authentication profiles instead of single tokens per platform:

```yaml
credentials:
  profiles:
    # Personal GitHub account
    personal-github:
      platform: github
      username: your-personal-username
      token: ${GITHUB_PERSONAL_TOKEN}

    # Work GitHub account
    work-github:
      platform: github
      username: your-work-username
      token: ${GITHUB_WORK_TOKEN}

    # GitLab account
    my-gitlab:
      platform: gitlab
      username: your-gitlab-username
      token: ${GITLAB_TOKEN}
```

#### Grouped Targets Format

Group targets by platform and reference credential profiles:

```yaml
targets:
  github:
    # Personal projects - exclude forks
    - credential: personal-github
      usernames:
        - torvalds
        - kubernetes
        - docker
      filters:
        forks: false
        archived: false

    # Work organization - include everything
    - credential: work-github
      usernames:
        - your-company-org
        - company-team

  gitlab:
    # GitLab repos
    - credential: my-gitlab
      usernames:
        - gitlab-org
        - gitlab-com
```

**Benefits:**
- ✅ Multiple accounts per platform
- ✅ Organized credentials with clear names
- ✅ Less repetition in configuration
- ✅ Different tokens for different users/organizations

#### Complete Example

See [docs/examples/multi-credential-config.yaml](docs/examples/multi-credential-config.yaml) for a complete working example.

```yaml
credentials:
  profiles:
    personal-github:
      platform: github
      username: john-personal
      token: ${GITHUB_PERSONAL_TOKEN}

    work-github:
      platform: github
      username: john-work
      token: ${GITHUB_WORK_TOKEN}

download:
  base_directory: ./repos
  max_parallel: 10

targets:
  github:
    - credential: personal-github
      usernames: [torvalds, kubernetes]
      filters: {forks: false}

    - credential: work-github
      usernames: [company-org]
```

**Run with multi-credential config:**
```bash
# Set environment variables for your tokens
export GITHUB_PERSONAL_TOKEN=ghp_your_personal_token
export GITHUB_WORK_TOKEN=ghp_your_work_token

# Download with config
repo-dl download --config multi-cred-config.yaml
```

#### Token Resolution Priority

When resolving which token to use, the system follows this priority:

1. **Profile token** (if target specifies `credential: profile-name`)
2. **Legacy token** (`github_token` or `gitlab_token` in credentials)
3. **Environment variable** (`GITHUB_TOKEN` or `GITLAB_TOKEN`)

This allows you to mix old and new formats during migration.

#### Migration from Legacy Format

You can gradually migrate from the legacy format:

**Step 1 - Legacy format (still works):**
```yaml
credentials:
  github_token: ${GITHUB_TOKEN}

targets:
  - platform: github
    username: torvalds
```

**Step 2 - Add profiles while keeping legacy:**
```yaml
credentials:
  github_token: ${GITHUB_TOKEN}  # Keep for existing targets
  profiles:
    work-github:
      platform: github
      username: work
      token: ${GITHUB_WORK_TOKEN}

targets:
  - platform: github
    username: torvalds  # Uses legacy token

  - platform: github
    username: company-org
    credential: work-github  # Uses profile
```

**Step 3 - Full migration to grouped format:**
```yaml
credentials:
  profiles:
    personal-github:
      platform: github
      username: personal
      token: ${GITHUB_PERSONAL_TOKEN}

targets:
  github:
    - credential: personal-github
      usernames: [torvalds, kubernetes]
```

### Python API

Use as a library in your Python code:

```python
import asyncio
from simple_repo_downloader import (
    RepoDownloader,
    Config,
    Target,
    DownloadConfig,
    Credentials
)

async def download_repos():
    # Create configuration
    config = Config(
        credentials=Credentials(
            github_token='ghp_your_token'
        ),
        download=DownloadConfig(
            base_directory='./repos',
            max_parallel=5
        ),
        targets=[
            Target(
                platform='github',
                username='torvalds',
                filters={'forks': False}
            )
        ]
    )

    # Initialize downloader
    downloader = RepoDownloader(config)

    # Download all repos
    results = await downloader.download_all(
        targets=config.targets
    )

    # Print results
    print(f"✓ Downloaded: {len(results.successful)}")
    print(f"✗ Failed: {len(results.issues)}")

    # Handle errors
    for issue in results.issues:
        print(f"Issue: {issue.repo.name} - {issue.message}")

# Run
asyncio.run(download_repos())
```

**With progress callback:**
```python
def on_progress(repo, progress_pct):
    print(f"{repo.name}: {progress_pct}%")

results = await downloader.download_all(
    targets=config.targets,
    progress_callback=on_progress
)
```

## Progress Output

The download process shows real-time progress updates in your terminal:

- Repository status updates as they complete
- Progress tracking (e.g., "Repo 5/20")
- State indicators (Completed, Failed, Up-to-date, etc.)
- Final summary with counts of successful/failed downloads

**Example output:**

```bash
repo-dl download github kubernetes --max-parallel 10

# Shows progress as each repository completes:
[5/20] github/kubernetes/kubernetes: Completed - Cloned successfully
[6/20] github/kubernetes/test-infra: Completed - Cloned successfully
[7/20] github/kubernetes/website: Failed - Repository not found
...

# Final summary:
Download Summary:
  Total: 20
  Completed: 15
  Failed: 3
  Up-to-date: 2
```

## 🔐 Authentication

Authentication tokens enable downloading private repositories and provide higher API rate limits. The tool **automatically detects** tokens from environment variables based on the platform you're using.

### Token Auto-Detection

The tool automatically reads:
- `GITHUB_TOKEN` environment variable when downloading from GitHub
- `GITLAB_TOKEN` environment variable when downloading from GitLab

You don't need to specify `--token` if the environment variable is set!

**Token Priority:**
1. `--token` flag (if provided) - highest priority
2. Platform-specific environment variable (`GITHUB_TOKEN` or `GITLAB_TOKEN`)
3. No token (public repos only)

### GitHub Personal Access Token

1. Go to https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a name (e.g., "repo-downloader")
4. Select scopes:
   - ✅ `repo` (for private repos)
   - ✅ `public_repo` (for public repos only)
5. Click "Generate token"
6. Copy the token (starts with `ghp_`)

**Usage:**
```bash
# Option 1: Environment variable (recommended - auto-detected!)
export GITHUB_TOKEN=ghp_your_token_here
repo-dl download github your-username  # Token automatically used

# Option 2: Direct in command (overrides environment variable)
repo-dl download github your-username --token ghp_your_token_here

# Option 3: In config file
# config.yaml
credentials:
  github_token: ${GITHUB_TOKEN}
```

### GitLab Personal Access Token

1. Go to https://gitlab.com/-/profile/personal_access_tokens
2. Fill in token name and expiration
3. Select scopes:
   - ✅ `read_api`
   - ✅ `read_repository`
4. Click "Create personal access token"
5. Copy the token (starts with `glpat-`)

**Usage:**
```bash
# Option 1: Environment variable (recommended - auto-detected!)
export GITLAB_TOKEN=glpat_your_token_here
repo-dl download gitlab your-username  # Token automatically used

# Option 2: Direct in command (overrides environment variable)
repo-dl download gitlab your-username --token glpat_your_token_here

# Option 3: In config file
# config.yaml
credentials:
  gitlab_token: ${GITLAB_TOKEN}
```

**For self-hosted GitLab:**
```yaml
targets:
  - platform: gitlab
    base_url: https://gitlab.mycompany.com
    username: my-team
```

## 🎯 Advanced Usage

### Multiple Users/Organizations

```yaml
# config.yaml
targets:
  - platform: github
    username: kubernetes
    filters:
      forks: false

  - platform: github
    username: docker
    filters:
      forks: false

  - platform: gitlab
    username: gitlab-org
```

```bash
repo-dl download --config config.yaml
```

### Filter Options

Available in config file `filters`:

- `forks: false` - Exclude forked repositories
- `archived: false` - Exclude archived repositories
- Both can be combined

```yaml
targets:
  - platform: github
    username: torvalds
    filters:
      forks: false        # Exclude forks
      archived: false     # Exclude archived repos
```

### Custom Directory Structure

By default, repos are saved as `./repos/platform/username/repo-name`:

```
repos/
├── github/
│   ├── torvalds/
│   │   ├── linux/
│   │   └── subsurface/
│   └── microsoft/
│       └── vscode/
└── gitlab/
    └── gitlab-org/
        └── gitlab-runner/
```

**Change base directory:**
```bash
repo-dl download github torvalds --output-dir ~/my-repos
# Creates: ~/my-repos/github/torvalds/linux/
```

### Environment Variables

The config file supports environment variable substitution:

```yaml
credentials:
  github_token: ${GITHUB_TOKEN}
  gitlab_token: ${GITLAB_TOKEN}

download:
  base_directory: ${REPO_BASE_DIR}  # Falls back to ./repos
```

### Rate Limits

**GitHub:**
- Authenticated: 5,000 requests/hour
- Unauthenticated: 60 requests/hour

**GitLab:**
- Varies by plan: 300-600 requests/minute

**Tip:** Always use authentication for better rate limits.

## 🔧 Troubleshooting

### Common Issues

#### "Command not found: repo-dl"

**Solution:**
```bash
# Make sure you installed the package
pip install -e .

# Or use python -m
python -m simple_repo_downloader.cli download github octocat
```

#### "Permission denied (publickey)"

This is a git SSH error, not a downloader issue.

**Solution:**
```bash
# The tool uses HTTPS by default, so this shouldn't happen
# If you see this, check your git configuration:
git config --global --get url.ssh://git@github.com/.insteadof

# Remove SSH URL rewriting if present:
git config --global --unset url.ssh://git@github.com/.insteadof
```

#### "API rate limit exceeded"

**Solution:**
```bash
# Use authentication to get higher rate limits
export GITHUB_TOKEN=ghp_your_token
repo-dl download github username --token $GITHUB_TOKEN
```

#### "Repository already exists"

The tool won't overwrite existing repositories.

**Solutions:**
1. Delete the existing directory
2. Use a different output directory
3. Move the existing repos elsewhere

#### "Failed to clone: Repository not found"

**Causes:**
- Repository is private (need token)
- Repository was deleted
- User/organization doesn't exist

**Solution:**
```bash
# For private repos, use authentication
export GITHUB_TOKEN=ghp_your_token
repo-dl download github username
```

### Debug Mode

```bash
# Run with verbose output (coming soon)
repo-dl download github octocat --verbose

# Check logs
# Errors are displayed during download
```

### Getting Help

```bash
# General help
repo-dl --help

# Command-specific help
repo-dl download --help
```

## 🛠️ Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/abudhahir/simple-repo-downloader.git
cd simple-repo-downloader

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=simple_repo_downloader --cov-report=html

# Run specific test file
pytest tests/test_api_client.py -v

# Run specific test
pytest tests/test_models.py::test_repo_info_creation -v
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

### Project Structure

```
simple-repo-downloader/
├── src/simple_repo_downloader/
│   ├── __init__.py          # Package exports
│   ├── models.py            # Data models
│   ├── config.py            # Configuration
│   ├── api_client.py        # GitHub/GitLab clients
│   ├── downloader.py        # Download engine
│   └── cli.py               # CLI interface
├── tests/                   # Test suite
├── docs/                    # Documentation
│   ├── plans/              # Design documents
│   └── examples/           # Usage examples
├── pyproject.toml          # Project configuration
└── README.md               # This file
```

### Running from Source

```bash
# Without installation
python -m simple_repo_downloader.cli download github octocat

# Or use the installed command
repo-dl download github octocat
```

## 📚 Documentation

### Complete Documentation

- **[Installation Guide](INSTALL.md)** - Detailed installation instructions
- **[Quick Start Guide](QUICKSTART.md)** - Get started in 5 minutes
- **[Design Document](docs/plans/2025-12-27-repo-downloader-design.md)** - Architecture and implementation
- **[CLI Usage Guide](docs/examples/cli-usage.md)** - Comprehensive CLI examples
- **[Configuration Reference](docs/examples/config-example.yaml)** - Config file template
- **[API Reference](docs/API.md)** - Python API documentation

### Examples

See [docs/examples/](docs/examples/) for more examples:
- Basic usage
- Authentication setup
- Configuration files
- Python API usage
- Advanced filtering

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Add tests for new features
- Update documentation
- Use type hints
- Write descriptive commit messages

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [aiohttp](https://docs.aiohttp.org/) for async HTTP
- CLI powered by [Click](https://click.palletsprojects.com/)
- Configuration using [Pydantic](https://docs.pydantic.dev/)
- Interactive dashboard using [Rich](https://rich.readthedocs.io/)
- Designed following TDD principles

## 📊 Project Status

- ✅ Core functionality complete
- ✅ GitHub API client
- ✅ GitLab API client
- ✅ Parallel downloads
- ✅ CLI interface
- ✅ Configuration system
- ✅ Interactive dashboard
- 🚧 Resume capability (planned)
- 🚧 Interactive error resolver (planned)

## 🗺️ Roadmap

See [Design Document](docs/plans/2025-12-27-repo-downloader-design.md) for detailed roadmap.

**Upcoming features:**
- Real-time progress dashboard with Rich
- Interactive error resolution
- Resume interrupted downloads
- Incremental updates (pull existing repos)
- Web UI for monitoring
- Additional platforms (Bitbucket, Gitea)

---

**Made with ❤️ using Python and Test-Driven Development**
