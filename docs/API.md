# Python API Reference

This document provides a complete reference for using Simple Repository Downloader as a Python library.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Components](#core-components)
  - [Configuration Models](#configuration-models)
  - [Data Models](#data-models)
  - [API Clients](#api-clients)
  - [Download Engine](#download-engine)
  - [Dashboard](#dashboard)
- [Complete Examples](#complete-examples)
- [Error Handling](#error-handling)
- [Advanced Usage](#advanced-usage)

## Installation

```bash
pip install simple-repo-downloader  # From PyPI (coming soon)
# OR
pip install -e .  # From source
```

## Quick Start

```python
import asyncio
from simple_repo_downloader import (
    AppConfig,
    Credentials,
    DownloadConfig,
    Target,
    DownloadEngine,
    GitHubClient,
)
import aiohttp

async def main():
    # Create configuration
    config = AppConfig(
        credentials=Credentials(github_token='ghp_your_token'),
        download=DownloadConfig(
            base_directory='./repos',
            max_parallel=5
        ),
        targets=[
            Target(platform='github', username='octocat', filters={})
        ]
    )

    # List repositories
    async with aiohttp.ClientSession() as session:
        client = GitHubClient(config.credentials.github_token, session)
        repos = await client.list_repositories('octocat', {})
        print(f"Found {len(repos)} repositories")

        # Download all repos
        engine = DownloadEngine(config.download)
        results = await engine.download_all(repos, config.credentials.github_token)

        print(f"✓ Downloaded: {len(results.successful)}")
        print(f"✗ Failed: {len(results.issues)}")

asyncio.run(main())
```

## Core Components

### Configuration Models

All configuration models use [Pydantic](https://docs.pydantic.dev/) for validation and support environment variable substitution with `${VAR_NAME}` syntax.

#### `Credentials`

Stores authentication tokens for platforms.

**Fields:**
- `github_token: Optional[str]` - GitHub personal access token (supports `${GITHUB_TOKEN}`)
- `gitlab_token: Optional[str]` - GitLab personal access token (supports `${GITLAB_TOKEN}`)

**Example:**
```python
from simple_repo_downloader import Credentials

# Direct values
creds = Credentials(
    github_token='ghp_xxxxxxxxxxxx',
    gitlab_token='glpat_xxxxxxxxxxxx'
)

# Environment variables (resolved automatically)
creds = Credentials(
    github_token='${GITHUB_TOKEN}',  # Reads from os.environ
    gitlab_token='${GITLAB_TOKEN}'
)
```

#### `DownloadConfig`

Controls download behavior.

**Fields:**
- `base_directory: Path` - Base directory for downloads (default: `./repos`)
- `max_parallel: int` - Number of concurrent downloads (default: 5, range: 1-20)
- `include_forks: bool` - Whether to download forks (default: `True`)
- `include_private: bool` - Whether to download private repos (default: `True`)

**Example:**
```python
from pathlib import Path
from simple_repo_downloader import DownloadConfig

config = DownloadConfig(
    base_directory=Path('~/backups/repos').expanduser(),
    max_parallel=10,
    include_forks=False,
    include_private=True
)
```

**Validation:**
```python
# Raises ValidationError if max_parallel > 20
config = DownloadConfig(max_parallel=25)  # ❌ Error
```

#### `Target`

Defines a platform/username to download from.

**Fields:**
- `platform: Literal['github', 'gitlab']` - Platform name
- `username: str` - Username or organization name
- `filters: Dict[str, bool]` - Filter configuration (default: `{}`)

**Available Filters:**
- `forks: bool` - Include forks (`False` to exclude)
- `archived: bool` - Include archived repos (`False` to exclude)

**Example:**
```python
from simple_repo_downloader import Target

# GitHub user, exclude forks
target = Target(
    platform='github',
    username='torvalds',
    filters={'forks': False}
)

# GitLab org, exclude archived
target = Target(
    platform='gitlab',
    username='gitlab-org',
    filters={'archived': False}
)

# Multiple filters
target = Target(
    platform='github',
    username='kubernetes',
    filters={'forks': False, 'archived': False}
)
```

#### `AppConfig`

Complete application configuration combining credentials, download settings, and targets.

**Fields:**
- `credentials: Credentials` - Authentication credentials
- `download: DownloadConfig` - Download configuration
- `targets: List[Target]` - List of download targets

**Methods:**

##### `from_yaml(path: Path) -> AppConfig`

Load configuration from YAML file.

**Parameters:**
- `path: Path` - Path to YAML configuration file

**Returns:**
- `AppConfig` instance

**Raises:**
- `FileNotFoundError` - If config file doesn't exist
- `ValueError` - If YAML is invalid

**Example:**
```python
from pathlib import Path
from simple_repo_downloader import AppConfig

config = AppConfig.from_yaml(Path('config.yaml'))
```

##### `to_yaml(path: Path) -> None`

Save configuration to YAML file.

**Parameters:**
- `path: Path` - Destination path for YAML file

**Raises:**
- `IOError` - If file write fails

**Example:**
```python
config.to_yaml(Path('output.yaml'))
```

**Complete Example:**
```python
from simple_repo_downloader import AppConfig, Credentials, DownloadConfig, Target

config = AppConfig(
    credentials=Credentials(
        github_token='${GITHUB_TOKEN}',
        gitlab_token='${GITLAB_TOKEN}'
    ),
    download=DownloadConfig(
        base_directory='./repos',
        max_parallel=5
    ),
    targets=[
        Target(platform='github', username='kubernetes', filters={'forks': False}),
        Target(platform='gitlab', username='gitlab-org', filters={})
    ]
)

# Save to file
config.to_yaml(Path('my-config.yaml'))

# Load from file
loaded = AppConfig.from_yaml(Path('my-config.yaml'))
```

### Data Models

Immutable data classes representing repositories and results.

#### `RepoInfo`

Information about a repository (immutable).

**Fields:**
- `platform: str` - Platform name ('github' or 'gitlab')
- `username: str` - Repository owner username/org
- `name: str` - Repository name
- `clone_url: str` - HTTPS clone URL
- `is_fork: bool` - Whether repo is a fork
- `is_private: bool` - Whether repo is private
- `is_archived: bool` - Whether repo is archived
- `size_kb: int` - Repository size in kilobytes
- `default_branch: str` - Default branch name (e.g., 'main', 'master')

**Example:**
```python
from simple_repo_downloader import RepoInfo

repo = RepoInfo(
    platform='github',
    username='torvalds',
    name='linux',
    clone_url='https://github.com/torvalds/linux.git',
    is_fork=False,
    is_private=False,
    is_archived=False,
    size_kb=2048000,
    default_branch='master'
)

print(f"{repo.username}/{repo.name}")  # torvalds/linux
```

#### `IssueType`

Enum of possible download issue types.

**Values:**
- `CONFLICT` - Directory already exists
- `FILE_CONFLICT` - Non-git file/directory in the way
- `NETWORK_ERROR` - Network connectivity issue
- `AUTH_ERROR` - Authentication failure
- `GIT_ERROR` - Git clone failed
- `RATE_LIMIT` - API rate limit exceeded

**Example:**
```python
from simple_repo_downloader import IssueType

if issue.issue_type == IssueType.CONFLICT:
    print("Repository already downloaded")
elif issue.issue_type == IssueType.AUTH_ERROR:
    print("Authentication required")
```

#### `StateEnum`

Enum of repository download states.

**Values:**
- `QUEUED` - Repository waiting to be downloaded
- `DOWNLOADING` - Currently being downloaded
- `COMPLETED` - Successfully downloaded
- `FAILED` - Download failed
- `PAUSED` - Download paused by user
- `SKIPPED` - Download skipped by user

**Example:**
```python
from simple_repo_downloader import StateEnum, RepoStatus

if repo_status.state == StateEnum.DOWNLOADING:
    print(f"Progress: {repo_status.progress_pct}%")
elif repo_status.state == StateEnum.COMPLETED:
    print("Download complete")
elif repo_status.state == StateEnum.PAUSED:
    print("Download paused - use 'resume' command")
```

#### `DownloadResult`

Result of a single repository download (immutable).

**Fields:**
- `repo: RepoInfo` - Repository information
- `success: bool` - Whether download succeeded
- `error: Optional[str]` - Error message if failed (default: `None`)

**Example:**
```python
from simple_repo_downloader import DownloadResult, RepoInfo

result = DownloadResult(
    repo=repo_info,
    success=True,
    error=None
)

if result.success:
    print(f"✓ {result.repo.name}")
else:
    print(f"✗ {result.repo.name}: {result.error}")
```

#### `DownloadIssue`

Detailed information about a download issue.

**Fields:**
- `repo: RepoInfo` - Repository that had the issue
- `issue_type: IssueType` - Type of issue encountered
- `message: str` - Human-readable error message
- `existing_path: Optional[Path]` - Path to existing conflicting file/directory
- `timestamp: datetime` - When the issue occurred (auto-generated)

**Example:**
```python
from simple_repo_downloader import DownloadIssue, IssueType

for issue in results.issues:
    print(f"{issue.timestamp}: {issue.repo.name}")
    print(f"  Type: {issue.issue_type.value}")
    print(f"  Message: {issue.message}")
    if issue.existing_path:
        print(f"  Conflict at: {issue.existing_path}")
```

#### `RateLimitInfo`

API rate limit information (immutable).

**Fields:**
- `remaining: int` - Requests remaining in current window
- `limit: int` - Total requests allowed per window
- `reset_timestamp: int` - Unix timestamp when limit resets

**Example:**
```python
from datetime import datetime

rate_limit = await client.get_rate_limit()
reset_time = datetime.fromtimestamp(rate_limit.reset_timestamp)
print(f"Remaining: {rate_limit.remaining}/{rate_limit.limit}")
print(f"Resets at: {reset_time}")
```

### API Clients

Asynchronous clients for GitHub and GitLab APIs.

#### `PlatformClient` (Abstract Base Class)

Base class for all platform clients. Do not instantiate directly.

**Methods:**

##### `list_repositories(username: str, filters: Dict[str, bool]) -> List[RepoInfo]`

Fetch all repositories for a user/organization.

**Parameters:**
- `username: str` - Username or organization name
- `filters: Dict[str, bool]` - Filter configuration

**Returns:**
- `List[RepoInfo]` - List of repository information

##### `get_rate_limit() -> RateLimitInfo`

Get current API rate limit status.

**Returns:**
- `RateLimitInfo` - Rate limit information

#### `GitHubClient`

GitHub API client with automatic pagination.

**Constructor:**
```python
GitHubClient(token: Optional[str], session: aiohttp.ClientSession)
```

**Parameters:**
- `token: Optional[str]` - GitHub personal access token (optional but recommended)
- `session: aiohttp.ClientSession` - Async HTTP session

**Features:**
- Automatic pagination (100 repos per page)
- Fallback from user to org endpoint
- Rate limit handling
- Token authentication

**Example:**
```python
import aiohttp
from simple_repo_downloader import GitHubClient

async with aiohttp.ClientSession() as session:
    client = GitHubClient(token='ghp_your_token', session=session)

    # List all repos (handles pagination automatically)
    repos = await client.list_repositories('kubernetes', {})
    print(f"Found {len(repos)} repositories")

    # With filters
    repos = await client.list_repositories(
        'microsoft',
        filters={'forks': False, 'archived': False}
    )

    # Check rate limit
    rate_limit = await client.get_rate_limit()
    print(f"Remaining API calls: {rate_limit.remaining}")
```

#### `GitLabClient`

GitLab API client with automatic pagination.

**Constructor:**
```python
GitLabClient(token: Optional[str], session: aiohttp.ClientSession, base_url: str = "https://gitlab.com")
```

**Parameters:**
- `token: Optional[str]` - GitLab personal access token
- `session: aiohttp.ClientSession` - Async HTTP session
- `base_url: str` - Base URL for GitLab instance (default: `https://gitlab.com`)

**Features:**
- Self-hosted GitLab support
- Automatic pagination
- OAuth2 token authentication

**Example:**
```python
import aiohttp
from simple_repo_downloader import GitLabClient

async with aiohttp.ClientSession() as session:
    # GitLab.com
    client = GitLabClient(token='glpat_your_token', session=session)
    repos = await client.list_repositories('gitlab-org', {})

    # Self-hosted GitLab
    client = GitLabClient(
        token='glpat_your_token',
        session=session,
        base_url='https://gitlab.mycompany.com'
    )
    repos = await client.list_repositories('my-team', {})
```

### Download Engine

Manages parallel repository downloads.

#### `DownloadEngine`

Asynchronous download engine with worker pool.

**Constructor:**
```python
DownloadEngine(config: DownloadConfig)
```

**Parameters:**
- `config: DownloadConfig` - Download configuration

**Methods:**

##### `download_all(repos: List[RepoInfo], token: Optional[str] = None, callback: Optional[Callable] = None) -> DownloadResults`

Download all repositories in parallel.

**Parameters:**
- `repos: List[RepoInfo]` - Repositories to download
- `token: Optional[str]` - Authentication token (optional)
- `callback: Optional[Callable]` - Progress callback function (optional)

**Returns:**
- `DownloadResults` - Download results with successful and failed repos

**Example:**
```python
from simple_repo_downloader import DownloadEngine, DownloadConfig

config = DownloadConfig(max_parallel=10)
engine = DownloadEngine(config)

results = await engine.download_all(repos, token='ghp_token')

print(f"✓ Success: {len(results.successful)}")
print(f"✗ Issues: {len(results.issues)}")

# List successful downloads
for result in results.successful:
    print(f"  ✓ {result.repo.username}/{result.repo.name}")

# Handle issues
for issue in results.issues:
    print(f"  ✗ {issue.repo.name}: {issue.message}")
```

**With Progress Callback:**
```python
def on_progress(repo: RepoInfo, status: str):
    """Called when download status changes."""
    print(f"{repo.name}: {status}")

results = await engine.download_all(repos, callback=on_progress)
```

#### `DownloadResults`

Results from a batch download operation.

**Fields:**
- `successful: List[DownloadResult]` - Successfully downloaded repositories
- `issues: List[DownloadIssue]` - Download issues encountered

**Example:**
```python
from simple_repo_downloader import DownloadResults

results: DownloadResults = await engine.download_all(repos)

# Success rate
total = len(results.successful) + len(results.issues)
success_rate = len(results.successful) / total * 100
print(f"Success rate: {success_rate:.1f}%")

# Group issues by type
from collections import defaultdict
by_type = defaultdict(list)
for issue in results.issues:
    by_type[issue.issue_type].append(issue)

for issue_type, issues in by_type.items():
    print(f"{issue_type.value}: {len(issues)} repos")
```

### Dashboard

Real-time terminal dashboard for monitoring download progress.

#### `RepoStatus`

Status of a single repository download.

**Fields:**
- `repo: RepoInfo` - Repository information
- `state: StateEnum` - Current download state (QUEUED, DOWNLOADING, COMPLETED, FAILED, PAUSED, SKIPPED)
- `progress_pct: int` - Download progress percentage (0-100)
- `error: Optional[str]` - Error message if failed
- `started_at: Optional[datetime]` - When download started
- `completed_at: Optional[datetime]` - When download finished

**Example:**
```python
from simple_repo_downloader import RepoStatus, StateEnum
from datetime import datetime

status = RepoStatus(
    repo=repo_info,
    state=StateEnum.DOWNLOADING,
    progress_pct=45,
    started_at=datetime.now()
)
```

#### `DownloadStatus`

Overall download status tracking all repositories.

**Fields:**
- `repos: Dict[str, RepoStatus]` - Dictionary mapping repo ID to status
- `events: List[str]` - Event log with timestamps
- `start_time: datetime` - When downloads started

**Properties:**
- `queued_count: int` - Number of queued repositories
- `downloading_count: int` - Number of active downloads
- `completed_count: int` - Number of completed downloads
- `failed_count: int` - Number of failed downloads
- `paused_count: int` - Number of paused downloads
- `skipped_count: int` - Number of skipped downloads

**Methods:**

##### `add_event(message: str) -> None`

Add timestamped event to log.

**Parameters:**
- `message: str` - Event message

**Example:**
```python
from simple_repo_downloader import DownloadStatus

status = DownloadStatus()
status.add_event("Started downloading kubernetes/kubernetes")
status.add_event("Completed torvalds/linux")

# Access counts
print(f"Completed: {status.completed_count}")
print(f"Active: {status.downloading_count}")
```

#### `Dashboard`

Interactive terminal dashboard with real-time updates.

**Constructor:**
```python
Dashboard()
```

**Methods:**

##### `run_live(status: DownloadStatus, refresh_rate: float = 0.25) -> None`

Run live dashboard with automatic updates.

**Parameters:**
- `status: DownloadStatus` - Download status to display
- `refresh_rate: float` - Update interval in seconds (default: 0.25)

**Features:**
- Real-time progress table with emoji indicators
- Summary statistics panel
- Event log showing recent activities
- Command shell for interactive control
- Automatic refresh until all downloads complete

**Example:**
```python
import asyncio
from simple_repo_downloader import Dashboard, DownloadStatus, RepoStatus, StateEnum

async def download_with_dashboard():
    # Initialize status
    status = DownloadStatus()

    # Add repositories to track
    for repo in repos:
        repo_id = f"{repo.username}/{repo.name}"
        status.repos[repo_id] = RepoStatus(
            repo=repo,
            state=StateEnum.QUEUED
        )

    # Create dashboard
    dashboard = Dashboard()

    # Run dashboard in background
    dashboard_task = asyncio.create_task(
        dashboard.run_live(status, refresh_rate=0.5)
    )

    # Your download logic updates status.repos as needed
    # ...

    await dashboard_task

asyncio.run(download_with_dashboard())
```

##### `_execute_command(cmd: str, args: List[str], status: DownloadStatus) -> Optional[str]`

Execute dashboard command (internal use).

**Parameters:**
- `cmd: str` - Command name
- `args: List[str]` - Command arguments
- `status: DownloadStatus` - Current download status

**Returns:**
- `Optional[str]` - Response message or None

**Available Commands:**
- `pause <repo>` - Pause repository download
- `resume <repo>` - Resume paused download
- `skip <repo>` - Skip repository
- `status` - Show detailed status
- `clear-log` - Clear event log
- `help` - Show command help
- `quit` - Graceful shutdown

##### `_build_layout(status: DownloadStatus) -> Layout`

Build Rich layout for dashboard display (internal use).

**Parameters:**
- `status: DownloadStatus` - Current download status

**Returns:**
- `Layout` - Rich layout object

**Layout Structure:**
```
┌─────────────────────────────────────┐
│  Repository Downloads (Table)       │
│  - Platform | User | Repo | Status  │
│  - Progress bars for active         │
├─────────────────────────────────────┤
│  Statistics Panel                   │
│  - Counts by state                  │
│  - Elapsed time                     │
├─────────────────────────────────────┤
│  Recent Events (Log)                │
│  - Last 10 events with timestamps   │
├─────────────────────────────────────┤
│  Command Shell                      │
│  - Interactive command prompt       │
└─────────────────────────────────────┘
```

**Using with Status Callbacks:**
```python
import asyncio
from simple_repo_downloader import (
    GitHubClient,
    DownloadEngine,
    DownloadConfig,
    Dashboard,
    DownloadStatus,
    RepoStatus,
    StateEnum
)

async def download_with_interactive_dashboard():
    """Download with real-time dashboard."""
    # Setup
    status = DownloadStatus()
    dashboard = Dashboard()

    async with aiohttp.ClientSession() as session:
        client = GitHubClient(token='ghp_token', session=session)
        repos = await client.list_repositories('kubernetes', {})

        # Initialize status tracking
        for repo in repos:
            repo_id = f"{repo.username}/{repo.name}"
            status.repos[repo_id] = RepoStatus(
                repo=repo,
                state=StateEnum.QUEUED
            )

        # Define callback to update status
        def on_status_change(repo: RepoInfo, new_state: StateEnum, progress: int = 0):
            repo_id = f"{repo.username}/{repo.name}"
            status.repos[repo_id].state = new_state
            status.repos[repo_id].progress_pct = progress

            if new_state == StateEnum.DOWNLOADING:
                status.add_event(f"Started {repo.name}")
            elif new_state == StateEnum.COMPLETED:
                status.add_event(f"Completed {repo.name}")
            elif new_state == StateEnum.FAILED:
                status.add_event(f"Failed {repo.name}")

        # Start dashboard
        dashboard_task = asyncio.create_task(
            dashboard.run_live(status, refresh_rate=0.5)
        )

        # Download with status callback
        config = DownloadConfig(max_parallel=5)
        engine = DownloadEngine(config)
        results = await engine.download_all(
            repos,
            token='ghp_token',
            progress_callback=on_status_change
        )

        await dashboard_task

        return results

asyncio.run(download_with_interactive_dashboard())
```

## Complete Examples

### Example 1: Basic Download

Download all public repositories from a GitHub user.

```python
import asyncio
import aiohttp
from simple_repo_downloader import (
    GitHubClient,
    DownloadEngine,
    DownloadConfig,
)

async def download_github_user(username: str, token: str = None):
    """Download all repos from a GitHub user."""
    async with aiohttp.ClientSession() as session:
        # Create client
        client = GitHubClient(token, session)

        # Fetch repositories
        print(f"Fetching repositories for {username}...")
        repos = await client.list_repositories(username, {})
        print(f"Found {len(repos)} repositories")

        # Download
        config = DownloadConfig(max_parallel=5)
        engine = DownloadEngine(config)
        results = await engine.download_all(repos, token)

        # Report
        print(f"\n✓ Downloaded: {len(results.successful)}")
        print(f"✗ Issues: {len(results.issues)}")

        return results

# Run
asyncio.run(download_github_user('octocat'))
```

### Example 2: Multi-Platform Download

Download from both GitHub and GitLab.

```python
import asyncio
import aiohttp
from simple_repo_downloader import (
    GitHubClient,
    GitLabClient,
    DownloadEngine,
    DownloadConfig,
)

async def download_multi_platform():
    """Download from multiple platforms."""
    async with aiohttp.ClientSession() as session:
        # GitHub
        gh_client = GitHubClient(token='ghp_token', session=session)
        gh_repos = await gh_client.list_repositories('kubernetes', {})

        # GitLab
        gl_client = GitLabClient(token='glpat_token', session=session)
        gl_repos = await gl_client.list_repositories('gitlab-org', {})

        # Combine all repos
        all_repos = gh_repos + gl_repos
        print(f"Total repositories: {len(all_repos)}")

        # Download all
        config = DownloadConfig(max_parallel=10)
        engine = DownloadEngine(config)
        results = await engine.download_all(all_repos)

        return results

asyncio.run(download_multi_platform())
```

### Example 3: Using Configuration File

Load settings from YAML and download.

```python
import asyncio
import aiohttp
from pathlib import Path
from simple_repo_downloader import (
    AppConfig,
    GitHubClient,
    GitLabClient,
    DownloadEngine,
)

async def download_from_config(config_path: str):
    """Download using YAML configuration."""
    # Load config
    config = AppConfig.from_yaml(Path(config_path))

    async with aiohttp.ClientSession() as session:
        engine = DownloadEngine(config.download)
        all_results = []

        # Process each target
        for target in config.targets:
            print(f"\nProcessing {target.platform}/{target.username}...")

            # Select appropriate client
            if target.platform == 'github':
                client = GitHubClient(config.credentials.github_token, session)
            else:
                client = GitLabClient(config.credentials.gitlab_token, session)

            # Fetch and download
            repos = await client.list_repositories(target.username, target.filters)
            print(f"  Found {len(repos)} repositories")

            token = (config.credentials.github_token if target.platform == 'github'
                    else config.credentials.gitlab_token)
            results = await engine.download_all(repos, token)
            all_results.append(results)

            print(f"  ✓ Downloaded: {len(results.successful)}")
            print(f"  ✗ Issues: {len(results.issues)}")

        return all_results

asyncio.run(download_from_config('config.yaml'))
```

### Example 4: Progress Monitoring

Monitor download progress with callbacks.

```python
import asyncio
import aiohttp
from datetime import datetime
from simple_repo_downloader import (
    GitHubClient,
    DownloadEngine,
    DownloadConfig,
    RepoInfo,
)

class ProgressMonitor:
    """Track download progress."""

    def __init__(self, total: int):
        self.total = total
        self.completed = 0
        self.start_time = datetime.now()

    def on_complete(self, repo: RepoInfo, success: bool):
        """Called when a repo download completes."""
        self.completed += 1
        elapsed = (datetime.now() - self.start_time).total_seconds()
        rate = self.completed / elapsed if elapsed > 0 else 0
        remaining = self.total - self.completed
        eta = remaining / rate if rate > 0 else 0

        status = "✓" if success else "✗"
        print(f"{status} [{self.completed}/{self.total}] {repo.name} "
              f"(ETA: {eta:.0f}s)")

async def download_with_progress(username: str):
    """Download with progress monitoring."""
    async with aiohttp.ClientSession() as session:
        client = GitHubClient(token=None, session=session)
        repos = await client.list_repositories(username, {})

        monitor = ProgressMonitor(total=len(repos))

        config = DownloadConfig(max_parallel=5)
        engine = DownloadEngine(config)
        results = await engine.download_all(
            repos,
            callback=monitor.on_complete
        )

        return results

asyncio.run(download_with_progress('octocat'))
```

### Example 5: Error Handling and Retry

Handle errors and implement retry logic.

```python
import asyncio
import aiohttp
from simple_repo_downloader import (
    GitHubClient,
    DownloadEngine,
    DownloadConfig,
    IssueType,
)

async def download_with_retry(username: str, max_retries: int = 3):
    """Download with automatic retry for network errors."""
    async with aiohttp.ClientSession() as session:
        client = GitHubClient(token='ghp_token', session=session)

        # Initial download
        repos = await client.list_repositories(username, {})
        config = DownloadConfig(max_parallel=5)
        engine = DownloadEngine(config)
        results = await engine.download_all(repos, token='ghp_token')

        # Retry failed repos
        retry_count = 0
        while results.issues and retry_count < max_retries:
            # Filter network errors only
            network_errors = [
                issue for issue in results.issues
                if issue.issue_type == IssueType.NETWORK_ERROR
            ]

            if not network_errors:
                break

            retry_count += 1
            print(f"\nRetry attempt {retry_count}/{max_retries}")
            print(f"Retrying {len(network_errors)} failed repos...")

            # Retry
            retry_repos = [issue.repo for issue in network_errors]
            retry_results = await engine.download_all(retry_repos, token='ghp_token')

            # Combine results
            results.successful.extend(retry_results.successful)
            results.issues = [
                issue for issue in results.issues
                if issue.repo not in [r.repo for r in retry_results.successful]
            ]
            results.issues.extend(retry_results.issues)

        print(f"\nFinal results:")
        print(f"  ✓ Success: {len(results.successful)}")
        print(f"  ✗ Failed: {len(results.issues)}")

        return results

asyncio.run(download_with_retry('kubernetes'))
```

## Error Handling

### Common Exceptions

```python
from simple_repo_downloader import AppConfig
from pathlib import Path
import asyncio

# Configuration errors
try:
    config = AppConfig.from_yaml(Path('missing.yaml'))
except FileNotFoundError as e:
    print(f"Config not found: {e}")

try:
    config = AppConfig.from_yaml(Path('invalid.yaml'))
except ValueError as e:
    print(f"Invalid YAML: {e}")

# Validation errors
from pydantic import ValidationError
from simple_repo_downloader import DownloadConfig

try:
    config = DownloadConfig(max_parallel=100)  # Exceeds limit
except ValidationError as e:
    print(f"Validation failed: {e}")

# Network errors
from aiohttp import ClientError

async def safe_download():
    try:
        async with aiohttp.ClientSession() as session:
            client = GitHubClient(token='ghp_token', session=session)
            repos = await client.list_repositories('username', {})
    except ClientError as e:
        print(f"Network error: {e}")
    except asyncio.TimeoutError:
        print("Request timed out")

# Download issues (handled in DownloadResults)
results = await engine.download_all(repos)
for issue in results.issues:
    if issue.issue_type == IssueType.AUTH_ERROR:
        print("Authentication required")
    elif issue.issue_type == IssueType.RATE_LIMIT:
        print("Rate limit exceeded")
    elif issue.issue_type == IssueType.CONFLICT:
        print(f"Already exists: {issue.existing_path}")
```

## Advanced Usage

### Custom HTTP Session Configuration

```python
import aiohttp
from simple_repo_downloader import GitHubClient

# Custom session with timeout and headers
timeout = aiohttp.ClientTimeout(total=300, connect=60)
headers = {'User-Agent': 'My Custom Downloader'}

async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
    client = GitHubClient(token='ghp_token', session=session)
    repos = await client.list_repositories('username', {})
```

### Filtering Repositories Programmatically

```python
# Filter after fetching
repos = await client.list_repositories('username', {})

# Only repos larger than 10MB
large_repos = [r for r in repos if r.size_kb > 10240]

# Only non-archived, non-fork repos
active_repos = [
    r for r in repos
    if not r.is_archived and not r.is_fork
]

# Repos with specific naming pattern
import re
pattern_repos = [
    r for r in repos
    if re.match(r'^python-.*', r.name)
]

engine = DownloadEngine(config)
results = await engine.download_all(active_repos)
```

### Concurrent Multi-User Downloads

```python
async def download_multiple_users(users: list[str]):
    """Download from multiple users concurrently."""
    async with aiohttp.ClientSession() as session:
        client = GitHubClient(token='ghp_token', session=session)

        # Fetch all repos concurrently
        tasks = [
            client.list_repositories(user, {})
            for user in users
        ]
        all_repos_lists = await asyncio.gather(*tasks)

        # Flatten
        all_repos = [repo for repos in all_repos_lists for repo in repos]

        # Download all at once
        config = DownloadConfig(max_parallel=10)
        engine = DownloadEngine(config)
        results = await engine.download_all(all_repos, token='ghp_token')

        return results

users = ['torvalds', 'gvanrossum', 'dhh']
asyncio.run(download_multiple_users(users))
```

### Environment Variable Resolution

```python
import os
from simple_repo_downloader import Credentials

# Set environment variables
os.environ['GITHUB_TOKEN'] = 'ghp_real_token'
os.environ['GITLAB_TOKEN'] = 'glpat_real_token'

# Automatic resolution
creds = Credentials(
    github_token='${GITHUB_TOKEN}',
    gitlab_token='${GITLAB_TOKEN}'
)

# Values are resolved
print(creds.github_token)  # 'ghp_real_token'
```

### Type Hints and IDE Support

All public APIs have full type hints for IDE autocomplete and static type checking.

```python
from simple_repo_downloader import (
    RepoInfo,
    DownloadResults,
    IssueType,
)
from typing import List

def filter_repos(repos: List[RepoInfo]) -> List[RepoInfo]:
    """Filter function with type hints."""
    return [r for r in repos if not r.is_fork]

def analyze_results(results: DownloadResults) -> dict:
    """Analyze download results."""
    return {
        'total': len(results.successful) + len(results.issues),
        'success': len(results.successful),
        'failed': len(results.issues),
        'rate': len(results.successful) / (len(results.successful) + len(results.issues))
    }
```

## See Also

- [Quick Start Guide](../QUICKSTART.md) - Get started quickly
- [CLI Documentation](../README.md#usage) - Command-line interface
- [Configuration Examples](examples/config-example.yaml) - YAML config templates
- [Design Document](plans/2025-12-27-repo-downloader-design.md) - Architecture details

---

**Version:** 0.1.0
**Last Updated:** 2025-12-27
