# CLI Usage Examples

## Basic Usage

### Download all repos from a GitHub user

```bash
repo-dl download github torvalds
```

### Download from multiple platforms/users

```bash
repo-dl download github torvalds gitlab gitlab-org
```

### Download with authentication token

```bash
repo-dl download github myusername --token ghp_xxxxxxxxxxxx
```

Or use environment variable:

```bash
export GITHUB_TOKEN=ghp_xxxxxxxxxxxx
repo-dl download github myusername
```

## Using Configuration Files

### Create a template config

```bash
repo-dl config init
```

This creates a `config.yaml` template in the current directory.

### Download using config file

```bash
repo-dl download --config myconfig.yaml
```

### Validate config file

```bash
repo-dl config validate myconfig.yaml
```

### Show effective configuration

```bash
repo-dl config show
```

## Advanced Options

### Control concurrency

```bash
# Download 10 repos at once
repo-dl download github kubernetes --max-parallel 10
```

### Filter repositories

```bash
# Exclude forks
repo-dl download github myusername --no-forks

# Include forks
repo-dl download github myusername --include-forks

# Exclude archived repos (in config file)
```

### Specify output directory

```bash
repo-dl download github torvalds --output-dir ~/backups/linux
```

This will create: `~/backups/linux/github/torvalds/linux/`

### Headless mode (no interactive dashboard)

```bash
repo-dl download github myusername --headless
```

Useful for automation and scripts.

### Verbose output

```bash
repo-dl download github myusername --verbose
```

### Quiet mode

```bash
repo-dl download github myusername --quiet
```

## Session Management

### Resume interrupted download

If download is interrupted (Ctrl+C, network failure, etc.):

```bash
repo-dl resume --session .repo-dl-session.json
```

### Resolve errors from previous run

```bash
repo-dl resolve --errors .repo-dl-errors.json
```

## Listing Repositories

### Preview what would be downloaded

```bash
# Table format
repo-dl list github torvalds --format table

# JSON format
repo-dl list github torvalds --format json

# CSV format
repo-dl list github torvalds --format csv > repos.csv
```

## Interactive Command Shell

During download, you can use these commands in the shell at the bottom:

- `pause <repo>` - Pause a specific repository download
- `resume <repo>` - Resume a paused repository
- `skip <repo>` - Skip a repository (won't download)
- `set max-parallel <n>` - Adjust concurrent downloads on the fly
- `filter status:failed` - Filter table to show only failed repos
- `filter status:downloading` - Show only currently downloading repos
- `clear-log` - Clear the event log panel
- `status` - Show detailed status
- `help` - Show available commands
- `quit` - Graceful shutdown (finish current downloads)

### Examples:

```
> pause github/torvalds/linux
> set max-parallel 10
> filter status:failed
> skip github/microsoft/unwanted-repo
> quit
```

## Complete Examples

### Example 1: Personal Backup

```bash
# Backup all your personal repos
export GITHUB_TOKEN=ghp_xxxxxxxxxxxx
repo-dl download github myusername \
  --output-dir ~/backups/github \
  --max-parallel 5 \
  --include-forks
```

### Example 2: Organization Clone

```bash
# Clone all repos from your company's GitHub org
repo-dl download github mycompany \
  --token $GITHUB_TOKEN \
  --no-forks \
  --max-parallel 10 \
  --output-dir ~/work/repos
```

### Example 3: Multi-Platform Backup

Create `backup-config.yaml`:

```yaml
credentials:
  github_token: ${GITHUB_TOKEN}
  gitlab_token: ${GITLAB_TOKEN}

download:
  base_directory: ~/backups
  max_parallel: 8

targets:
  - platform: github
    username: myusername
  - platform: gitlab
    username: myusername
```

Run:

```bash
repo-dl download --config backup-config.yaml
```

### Example 4: Selective Download

```yaml
# selective-config.yaml
credentials:
  github_token: ${GITHUB_TOKEN}

download:
  base_directory: ./opensource
  max_parallel: 5

targets:
  - platform: github
    username: kubernetes
    filters:
      forks: false
      archived: false

  - platform: github
    username: docker
    filters:
      forks: false
      archived: false
```

```bash
repo-dl download --config selective-config.yaml
```

## Environment Variables

The tool respects these environment variables:

- `GITHUB_TOKEN` - GitHub personal access token
- `GITLAB_TOKEN` - GitLab personal access token
- `REPO_DL_CONFIG` - Default config file path
- `REPO_DL_BASE_DIR` - Default base directory for downloads

## Exit Codes

- `0` - Success
- `1` - General error
- `2` - Configuration error
- `3` - Authentication error
- `4` - Network error
- `130` - Interrupted by user (Ctrl+C)

## Tips

1. **Start small**: Test with a user that has few repos first
2. **Check rate limits**: Use `--verbose` to see rate limit status
3. **Save sessions**: Large downloads can be resumed if interrupted
4. **Use config files**: Easier to manage multiple targets
5. **Monitor dashboard**: The interactive shell helps troubleshoot in real-time
6. **Handle conflicts**: After bulk download, resolve conflicts interactively

## Getting Help

```bash
# General help
repo-dl --help

# Command-specific help
repo-dl download --help
repo-dl config --help
repo-dl resume --help
```
