# CLI Usage Examples

## Basic Usage

### Download all repos from a GitHub user

```bash
repo-dl download github torvalds
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

### Download using config file

```bash
repo-dl download --config myconfig.yaml
```

Example `config.yaml`:

```yaml
credentials:
  github_token: ${GITHUB_TOKEN}
  gitlab_token: ${GITLAB_TOKEN}

download:
  base_directory: ./repos
  max_parallel: 5

targets:
  - platform: github
    username: torvalds
    filters:
      forks: false
```

See [docs/examples/config-example.yaml](config-example.yaml) for a complete example.

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

Useful for automation and scripts. Disables the interactive dashboard and runs in simple output mode.

## Interactive Dashboard

By default, downloads run with an interactive dashboard showing:

- Real-time progress table with status and progress bars
- Summary statistics (queued/downloading/completed/failed/paused/skipped)
- Event log with timestamped download events
- Interactive command shell

### Dashboard Commands

During download, you can type commands in the shell at the bottom:

- `pause <repo>` - Pause a specific repository download
- `resume <repo>` - Resume a paused repository
- `skip <repo>` - Skip a repository (won't download)
- `status` - Show detailed status
- `clear-log` - Clear the event log panel
- `help` - Show available commands
- `quit` - Graceful shutdown (finish current downloads)

**Examples:**

```
> pause github/torvalds/linux
> skip github/microsoft/unwanted-repo
> resume github/torvalds/linux
> status
> quit
```

Repository names should be in the format: `platform/username/reponame`

## Complete Examples

### Example 1: Personal Backup

```bash
# Backup all your personal repos
export GITHUB_TOKEN=ghp_xxxxxxxxxxxx
repo-dl download github myusername \
  --output-dir ~/backups/github \
  --max-parallel 5
```

### Example 2: Organization Clone

```bash
# Clone all repos from your company's GitHub org (excluding forks)
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

- `GITHUB_TOKEN` - GitHub personal access token (used if `--token` not provided)
- `GITLAB_TOKEN` - GitLab personal access token
- Config files support environment variable substitution using `${VAR_NAME}` syntax

## Tips

1. **Start small**: Test with a user that has few repos first
2. **Use authentication**: Avoid rate limits by providing a token
3. **Use config files**: Easier to manage multiple targets and filters
4. **Monitor dashboard**: The interactive shell helps troubleshoot in real-time
5. **Use headless mode**: For automation and CI/CD pipelines

## Getting Help

```bash
# General help
repo-dl --help

# Command-specific help
repo-dl download --help
```
