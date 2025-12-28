# Quick Start Guide

Get started with Simple Repository Downloader in 5 minutes.

## 1. Installation (2 minutes)

```bash
# Clone the repository
git clone https://github.com/abudhahir/simple-repo-downloader.git
cd simple-repo-downloader

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install the package
pip install -e .

# Verify installation
repo-dl --help
```

## 2. Your First Download (1 minute)

Download all public repositories from a GitHub user:

```bash
repo-dl download github octocat
```

This will:
- Fetch all repositories from the `octocat` user
- Clone them to `./repos/github/octocat/`
- Show progress in real-time

**Output structure:**
```
repos/
└── github/
    └── octocat/
        ├── Hello-World/
        ├── Spoon-Knife/
        └── ... (other repos)
```

## 3. Add Authentication (1 minute)

For private repos and higher rate limits, create a GitHub Personal Access Token:

1. Go to https://github.com/settings/tokens
2. Click **"Generate new token (classic)"**
3. Select scope: `repo` (for private repos) or `public_repo` (public only)
4. Copy the token (starts with `ghp_`)

**Use the token:**

```bash
export GITHUB_TOKEN=ghp_your_token_here
repo-dl download github your-username
```

## 4. Download Faster (30 seconds)

Download multiple repos in parallel:

```bash
# Download 10 repos at once (default is 5)
repo-dl download github kubernetes --max-parallel 10
```

## 5. Common Use Cases (30 seconds)

**Exclude forks:**
```bash
repo-dl download github microsoft --no-forks
```

**Custom output directory:**
```bash
repo-dl download github torvalds --output-dir ~/backups
```

**Multiple users with config file:**

Create `config.yaml`:
```yaml
credentials:
  github_token: ${GITHUB_TOKEN}

download:
  base_directory: ./repos
  max_parallel: 5

targets:
  - platform: github
    username: kubernetes
    filters:
      forks: false

  - platform: github
    username: docker
    filters:
      forks: false
```

Run:
```bash
repo-dl download --config config.yaml
```

## 6. Download from GitLab

```bash
# Get GitLab token from https://gitlab.com/-/profile/personal_access_tokens
export GITLAB_TOKEN=glpat_your_token_here

repo-dl download gitlab gitlab-org
```

## What's Next?

- **[Full Documentation](README.md)** - Comprehensive guide with all features
- **[Installation Guide](INSTALL.md)** - Platform-specific installation help
- **[Python API](docs/API.md)** - Use as a library in your code
- **[CLI Examples](docs/examples/cli-usage.md)** - Advanced usage patterns

## Troubleshooting

**"Command not found: repo-dl"**
```bash
# Make sure you activated the virtual environment
source venv/bin/activate

# Or use Python module syntax
python -m simple_repo_downloader.cli download github octocat
```

**"API rate limit exceeded"**
```bash
# Use authentication for higher limits
export GITHUB_TOKEN=ghp_your_token
repo-dl download github username --token $GITHUB_TOKEN
```

**"Permission denied" or "Repository not found"**
```bash
# For private repos, you need authentication
export GITHUB_TOKEN=ghp_your_token_with_repo_scope
repo-dl download github your-username
```

## Quick Reference

| Command | Description |
|---------|-------------|
| `repo-dl download github USER` | Download all GitHub repos |
| `repo-dl download gitlab USER` | Download all GitLab repos |
| `repo-dl download --config FILE` | Use config file |
| `repo-dl --help` | Show all commands |
| `repo-dl download --help` | Show download options |

## Tips

1. **Start small** - Test with a user that has few repos first
2. **Use authentication** - Much better rate limits
3. **Check output directory** - Repos are organized by platform/username/repo-name
4. **Parallel downloads** - Adjust `--max-parallel` based on your bandwidth
5. **Config files** - Easier for multiple users or regular backups

---

**Ready to dive deeper?** Check out the [full documentation](README.md) for advanced features, filters, troubleshooting, and Python API usage.
