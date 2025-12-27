# Simple Repository Downloader - Design Document

**Date:** 2025-12-27
**Status:** Approved Design
**Version:** 1.0

## Overview

A simple, efficient tool for downloading all repositories from GitHub or GitLab users/organizations. Built as both a Python library and CLI tool with a real-time interactive dashboard.

## Project Goals

- Download all repositories for a given GitHub/GitLab username or organization
- Full git clones with complete history and all branches
- Efficient parallel downloads with configurable concurrency
- Support for both public and private repositories via personal access tokens
- Real-time dashboard showing download progress
- Interactive error resolution after bulk operations
- Flexible filtering (include/exclude forks, archived repos, etc.)
- Usable as both CLI tool and Python library

## Technology Stack

### Core Technologies
- **Language:** Python 3.10+
- **Async Framework:** `asyncio` for concurrent operations
- **HTTP Client:** `aiohttp` for GitHub/GitLab API calls
- **Git Operations:** `subprocess` calls to git CLI (reliable, widely available)
- **CLI Framework:** `click` for command-line interface
- **UI Framework:** `rich` for terminal dashboard and formatting
- **Configuration:** `pydantic` for validation and YAML parsing

### Key Dependencies
```
aiohttp>=3.9.0
click>=8.1.0
rich>=13.0.0
pydantic>=2.0.0
PyYAML>=6.0.0
gitpython>=3.1.0  # Optional, for git validation
```

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Layer                           │
│                    (click commands)                         │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    Configuration                            │
│              (Pydantic models, YAML)                        │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  Download Orchestrator                      │
│             (async queue, worker pool)                      │
└──────┬───────────────────┬──────────────────────┬───────────┘
       │                   │                      │
┌──────▼──────┐   ┌────────▼────────┐   ┌────────▼──────────┐
│   GitHub    │   │     GitLab      │   │    Dashboard      │
│   Client    │   │     Client      │   │   (Rich Live)     │
└─────────────┘   └─────────────────┘   └───────────────────┘
       │                   │                      │
┌──────▼───────────────────▼──────────────────────▼───────────┐
│                    Git Clone Workers                        │
│              (subprocess in thread pool)                    │
└─────────────────────────────────────────────────────────────┘
```

### Module Structure

```
simple_repo_downloader/
├── __init__.py           # Package exports
├── config.py             # Configuration models and parsing
├── api_client.py         # Base API client + implementations
├── downloader.py         # Core download engine
├── resolver.py           # Interactive error resolution
├── dashboard.py          # Rich UI components
├── cli.py                # Click command definitions
└── models.py             # Shared data models
```

## Detailed Component Design

### 1. Configuration System

**File Format (YAML):**

```yaml
credentials:
  github_token: ${GITHUB_TOKEN}  # Env var substitution
  gitlab_token: ${GITLAB_TOKEN}

download:
  base_directory: ./repos
  max_parallel: 5               # Concurrent downloads
  include_forks: true
  include_private: true

targets:
  - platform: github
    username: torvalds
    filters:
      forks: false
      archived: false

  - platform: gitlab
    username: gitlab-org
```

**Pydantic Models:**

```python
class Credentials(BaseModel):
    github_token: Optional[str] = None
    gitlab_token: Optional[str] = None

    @field_validator('*', mode='before')
    def resolve_env_vars(cls, v):
        # Resolve ${VAR_NAME} syntax
        pass

class DownloadConfig(BaseModel):
    base_directory: Path = Path('./repos')
    max_parallel: int = Field(default=5, ge=1, le=20)
    include_forks: bool = True
    include_private: bool = True

class Target(BaseModel):
    platform: Literal['github', 'gitlab']
    username: str
    filters: Dict[str, bool] = Field(default_factory=dict)

class AppConfig(BaseModel):
    credentials: Credentials
    download: DownloadConfig
    targets: List[Target]
```

**Configuration Priority:**
1. CLI arguments (highest priority)
2. Config file
3. Environment variables
4. Defaults (lowest priority)

### 2. API Client Architecture

**Base Class:**

```python
class PlatformClient(ABC):
    def __init__(self, token: Optional[str], session: aiohttp.ClientSession):
        self.token = token
        self.session = session

    @abstractmethod
    async def list_repositories(
        self,
        username: str,
        filters: Dict[str, bool]
    ) -> List[RepoInfo]:
        """Fetch all repos for a user/org with pagination."""
        pass

    @abstractmethod
    async def get_rate_limit(self) -> RateLimitInfo:
        """Get current rate limit status."""
        pass
```

**GitHub Implementation:**

- **API:** GitHub REST API v3
- **Endpoints:**
  - `/users/{username}/repos` - User repositories
  - `/orgs/{org}/repos` - Organization repositories
  - `/rate_limit` - Rate limit status
- **Pagination:** Link header, 100 items per page
- **Rate Limits:**
  - Authenticated: 5000 req/hour
  - Unauthenticated: 60 req/hour
- **Authentication:** `Authorization: token {PAT}`

**GitLab Implementation:**

- **API:** GitLab API v4
- **Endpoints:**
  - `/users/{username}/projects` - User projects
  - `/groups/{group}/projects` - Group projects
- **Pagination:** Page parameter + `X-Total-Pages` header
- **Rate Limits:** 300-600 req/minute (plan dependent)
- **Authentication:** `PRIVATE-TOKEN: {PAT}`
- **Configuration:** Support custom GitLab instances via base URL

**Repository Info Model:**

```python
@dataclass
class RepoInfo:
    platform: str          # 'github' or 'gitlab'
    username: str          # Owner username/org
    name: str              # Repository name
    clone_url: str         # HTTPS clone URL
    is_fork: bool
    is_private: bool
    is_archived: bool
    size_kb: int
    default_branch: str
```

### 3. Download Engine

**Core Architecture:**

```python
class DownloadEngine:
    def __init__(self, config: DownloadConfig):
        self.config = config
        self.semaphore = asyncio.Semaphore(config.max_parallel)
        self.download_queue: asyncio.Queue[RepoInfo] = asyncio.Queue()
        self.results: List[DownloadResult] = []
        self.issues: List[DownloadIssue] = []

    async def download_all(
        self,
        repos: List[RepoInfo],
        progress_callback: Optional[Callable] = None
    ) -> DownloadResults:
        """Main entry point for bulk download."""

        # Populate queue
        for repo in repos:
            await self.download_queue.put(repo)

        # Spawn workers
        workers = [
            asyncio.create_task(self._worker(i, progress_callback))
            for i in range(self.config.max_parallel)
        ]

        # Wait for completion
        await self.download_queue.join()

        # Cancel workers
        for worker in workers:
            worker.cancel()

        return DownloadResults(
            successful=self.results,
            issues=self.issues
        )
```

**Worker Pattern:**

```python
async def _worker(self, worker_id: int, callback: Optional[Callable]):
    while True:
        repo = await self.download_queue.get()

        try:
            async with self.semaphore:
                await self._clone_repo(repo, callback)
                self.results.append(DownloadResult(repo=repo, success=True))
        except Exception as e:
            self.issues.append(DownloadIssue(
                repo=repo,
                issue_type=self._classify_error(e),
                message=str(e)
            ))
        finally:
            self.download_queue.task_done()
```

**Git Clone Strategy:**

```python
async def _clone_repo(self, repo: RepoInfo, callback: Optional[Callable]):
    # Construct destination path: ./platform/username/repo-name
    dest = self.config.base_directory / repo.platform / repo.username / repo.name

    # Check for conflicts
    if dest.exists():
        if (dest / '.git').exists():
            raise ConflictError(f"Repository already exists: {dest}")
        else:
            raise FileError(f"Non-git directory exists: {dest}")

    # Create parent directories
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Inject token into URL for authentication
    clone_url = self._inject_token(repo.clone_url, repo.platform)

    # Execute git clone in thread pool (blocking subprocess)
    await asyncio.get_event_loop().run_in_executor(
        None,
        self._git_clone_subprocess,
        clone_url,
        dest,
        callback
    )

def _git_clone_subprocess(self, url: str, dest: Path, callback: Callable):
    """Execute git clone with progress tracking."""
    process = subprocess.Popen(
        ['git', 'clone', '--progress', url, str(dest)],
        stderr=subprocess.PIPE,
        universal_newlines=True
    )

    # Parse progress from stderr
    for line in process.stderr:
        if callback and 'Receiving objects' in line:
            # Extract percentage and call callback
            pct = self._parse_progress(line)
            callback(repo, pct)

    if process.wait() != 0:
        raise GitError(f"Git clone failed for {url}")
```

**Progress Tracking:**

Git outputs progress to stderr in format:
```
Receiving objects: 75% (123/456), 2.5 MiB | 1.2 MiB/s
```

Parser extracts percentage and speed for dashboard updates.

### 4. Error Handling & Resolution

**Issue Classification:**

```python
class IssueType(Enum):
    CONFLICT = "conflict"           # Directory exists with git repo
    FILE_CONFLICT = "file_conflict" # Directory exists, not a git repo
    NETWORK_ERROR = "network"       # Connection/timeout issues
    AUTH_ERROR = "auth"             # Permission denied
    GIT_ERROR = "git"               # Git command failed
    RATE_LIMIT = "rate_limit"       # API rate limit hit
```

**Issue Model:**

```python
@dataclass
class DownloadIssue:
    repo: RepoInfo
    issue_type: IssueType
    message: str
    existing_path: Optional[Path] = None
    timestamp: datetime = field(default_factory=datetime.now)
```

**Interactive Resolver:**

```python
class InteractiveResolver:
    def __init__(self, issues: List[DownloadIssue]):
        self.issues = issues
        self.console = Console()

    async def resolve_all(self) -> List[DownloadResult]:
        """Walk through each issue and prompt for resolution."""
        results = []

        for i, issue in enumerate(self.issues, 1):
            self.console.print(f"\n[bold][{i}/{len(self.issues)}][/bold] {issue.repo.platform}/{issue.repo.username}/{issue.repo.name}")
            self.console.print(f"  Issue: {issue.issue_type.value}")
            self.console.print(f"  {issue.message}\n")

            action = self._prompt_action(issue)
            result = await self._execute_action(issue, action)
            results.append(result)

        return results

    def _prompt_action(self, issue: DownloadIssue) -> ResolutionAction:
        """Prompt user for resolution action based on issue type."""

        if issue.issue_type == IssueType.CONFLICT:
            choices = {
                'p': 'Pull latest changes',
                'r': 'Delete and re-clone',
                'c': f'Clone to timestamped copy ({issue.repo.name}-{date.today()})',
                's': 'Skip this repository',
                'a': 'Apply to all remaining conflicts'
            }
        elif issue.issue_type == IssueType.NETWORK_ERROR:
            choices = {
                'r': 'Retry download',
                's': 'Skip this repository',
                'a': 'Retry all network errors'
            }
        # ... more issue types

        return Prompt.ask("Choose action", choices=list(choices.keys()))
```

**Resolution Actions:**

- **Pull:** `git -C <path> pull --all`
- **Re-clone:** Delete directory, clone fresh
- **Copy:** Clone to `{name}-{timestamp}` directory
- **Skip:** Mark as resolved, no action
- **Retry:** Attempt download again

**Batch Actions:**

User can apply same action to all remaining issues of the same type:
- "Pull all conflicts"
- "Retry all network errors"
- "Skip all auth errors"

### 5. Dashboard & UI

**Dashboard Layout:**

```
╭─────────────────────────────────────────────────────────────────╮
│ Simple Repo Downloader | Elapsed: 00:05:23 | Rate Limit: 4,892 │
╰─────────────────────────────────────────────────────────────────╯

┌──────────────────────────────────────────────────────────────────┐
│ Platform │ User      │ Repository    │ Status      │ Progress   │
├──────────┼───────────┼───────────────┼─────────────┼────────────┤
│ github   │ torvalds  │ linux         │ 🔄 Cloning  │ ████▌ 45%  │
│ github   │ torvalds  │ subsurface    │ ✅ Done     │ ██████ 100%│
│ gitlab   │ gitlab-org│ gitlab-runner │ ⏳ Queued   │            │
│ github   │ microsoft │ vscode        │ ❌ Failed   │            │
└──────────┴───────────┴───────────────┴─────────────┴────────────┘

╭─────────────────────────────────────────────────────────────────╮
│ Summary: 1 downloading | 15 completed | 1 failed | 23 queued   │
│ Speed: 2.3 MB/s | ETA: ~8 minutes                              │
╰─────────────────────────────────────────────────────────────────╯

╭─ Recent Events ─────────────────────────────────────────────────╮
│ [12:34:56] Started cloning github/torvalds/linux               │
│ [12:34:52] Completed github/torvalds/subsurface                │
│ [12:34:48] Failed github/microsoft/vscode - Network timeout    │
╰─────────────────────────────────────────────────────────────────╯

╭─ Command Shell ─────────────────────────────────────────────────╮
│ > _                                                             │
╰─────────────────────────────────────────────────────────────────╯
```

**Implementation:**

```python
class Dashboard:
    def __init__(self):
        self.console = Console()
        self.layout = Layout()
        self.repo_table = Table()
        self.command_history = []

    async def run(self, engine: DownloadEngine):
        """Run live dashboard with command shell."""

        with Live(self.layout, console=self.console, refresh_per_second=4):
            # Start command listener in background
            asyncio.create_task(self._command_listener())

            # Monitor download progress
            while not engine.is_complete():
                self._update_display(engine.get_status())
                await asyncio.sleep(0.25)
```

**Command Shell:**

Interactive commands available during downloads:

```python
COMMANDS = {
    'pause <repo>': 'Pause specific repository download',
    'resume <repo>': 'Resume paused repository',
    'skip <repo>': 'Skip repository (add to skip list)',
    'set max-parallel <n>': 'Adjust concurrent downloads',
    'filter <type>:<value>': 'Filter table view',
    'clear-log': 'Clear event log panel',
    'status': 'Show detailed status',
    'help': 'Show available commands',
    'quit': 'Graceful shutdown'
}
```

**Shell Implementation:**

```python
async def _command_listener(self):
    """Listen for commands in non-blocking mode."""

    while True:
        # Non-blocking input using aioconsole
        try:
            cmd = await aioconsole.ainput()
            await self._execute_command(cmd)
        except EOFError:
            break

async def _execute_command(self, cmd: str):
    """Parse and execute command."""

    parts = cmd.strip().split()
    if not parts:
        return

    command = parts[0]
    args = parts[1:]

    if command == 'set' and args[0] == 'max-parallel':
        new_limit = int(args[1])
        self.engine.update_concurrency(new_limit)
        self._log_event(f"Concurrency set to {new_limit}")

    elif command == 'skip':
        repo_id = args[0]
        self.engine.skip_repo(repo_id)
        self._log_event(f"Skipped {repo_id}")

    # ... more commands
```

**Graceful Shutdown:**

`Ctrl+C` or `quit` command:
1. Stop accepting new downloads from queue
2. Wait for in-progress clones to complete (with timeout)
3. Save error list to `.repo-dl-session.json`
4. Display summary
5. Offer to resume later with `repo-dl resume --session .repo-dl-session.json`

### 6. CLI Interface

**Main Commands:**

```bash
# Download repositories
repo-dl download [OPTIONS] [PLATFORM USERNAME]...

# Examples:
repo-dl download github torvalds
repo-dl download github torvalds gitlab gitlab-org
repo-dl download --config myconfig.yaml
repo-dl download github torvalds --max-parallel 10 --no-forks --token ghp_xxx

# Resume interrupted session
repo-dl resume --session .repo-dl-session.json

# Resolve errors from previous run
repo-dl resolve --errors .repo-dl-errors.json

# Configuration management
repo-dl config init                      # Create template config
repo-dl config validate myconfig.yaml    # Validate config file
repo-dl config show                      # Show current effective config

# List available repositories (without downloading)
repo-dl list github torvalds --format table
```

**Global Options:**

```
--config PATH       Config file path
--verbose, -v       Verbose logging
--quiet, -q         Minimal output
--no-color          Disable color output
--version           Show version
--help              Show help
```

**Download Command Options:**

```
--token TEXT              Authentication token
--max-parallel INTEGER    Concurrent downloads (1-20)
--include-forks          Include forked repositories
--no-forks               Exclude forks
--include-archived       Include archived repositories
--output-dir PATH        Base output directory
--headless               No interactive dashboard
```

### 7. Library API

**Programmatic Usage:**

```python
import asyncio
from simple_repo_downloader import RepoDownloader, Config, Target

async def main():
    # Create configuration
    config = Config(
        credentials={'github_token': 'ghp_xxx'},
        download={'max_parallel': 5, 'base_directory': './repos'}
    )

    # Initialize downloader
    downloader = RepoDownloader(config)

    # Define targets
    targets = [
        Target(platform='github', username='torvalds', filters={'forks': False}),
        Target(platform='gitlab', username='gitlab-org')
    ]

    # Progress callback
    def on_progress(repo, progress_pct, speed_mbps):
        print(f"{repo.name}: {progress_pct}% @ {speed_mbps} MB/s")

    # Download all
    results = await downloader.download_all(
        targets=targets,
        progress_callback=on_progress,
        headless=False  # Show dashboard
    )

    # Handle results
    print(f"Successful: {len(results.successful)}")
    print(f"Failed: {len(results.issues)}")

    # Interactive resolution if needed
    if results.issues:
        from simple_repo_downloader import InteractiveResolver
        resolver = InteractiveResolver(results.issues)
        resolved = await resolver.resolve_all()

asyncio.run(main())
```

**Event Hooks:**

```python
# Register event handlers
downloader.on_repo_start = lambda repo: print(f"Starting {repo.name}")
downloader.on_repo_complete = lambda repo, result: print(f"Done {repo.name}")
downloader.on_error = lambda issue: print(f"Error: {issue.message}")
downloader.on_rate_limit = lambda platform, reset_time: print(f"Rate limited until {reset_time}")
```

**Advanced Usage:**

```python
# Direct API client usage
from simple_repo_downloader.api_client import GitHubClient

async with aiohttp.ClientSession() as session:
    client = GitHubClient(token='ghp_xxx', session=session)
    repos = await client.list_repositories('torvalds', filters={'forks': False})

    for repo in repos:
        print(f"{repo.name}: {repo.size_kb} KB")
```

## Directory Structure

**Output Organization:**

```
repos/                          # Base directory (configurable)
├── github/
│   ├── torvalds/
│   │   ├── linux/             # Full git clone
│   │   ├── subsurface/
│   │   └── test-tlb/
│   └── microsoft/
│       ├── vscode/
│       └── typescript/
└── gitlab/
    ├── gitlab-org/
    │   ├── gitlab-runner/
    │   └── gitlab-ce/
    └── some-user/
        └── project/
```

**Metadata Files:**

```
.repo-dl-session.json          # Current session state (for resume)
.repo-dl-errors.json           # Error list from last run
.repo-dl-config.yaml           # Default config (optional)
```

## Data Flow

### 1. Download Flow

```
User Input (CLI/Config)
    ↓
Parse & Validate Configuration
    ↓
Initialize API Clients (GitHub/GitLab)
    ↓
Fetch Repository Lists (with pagination)
    ↓
Apply Filters (forks, archived, etc.)
    ↓
Populate Download Queue
    ↓
Spawn Async Workers (max_parallel)
    ↓
Worker Loop:
    ├─ Acquire Semaphore
    ├─ Check for Conflicts
    ├─ Execute Git Clone (subprocess)
    ├─ Track Progress → Update Dashboard
    ├─ Release Semaphore
    └─ Mark Complete or Add to Issues
    ↓
All Downloads Complete
    ↓
Display Summary
    ↓
If Issues Exist → Interactive Resolution
```

### 2. Error Resolution Flow

```
Issues List
    ↓
For Each Issue:
    ├─ Display Issue Details
    ├─ Show Available Actions
    ├─ Prompt User
    ├─ Execute Selected Action
    │   ├─ Pull → git pull
    │   ├─ Re-clone → rm -rf + git clone
    │   ├─ Copy → git clone to new path
    │   ├─ Skip → no action
    │   └─ Batch → apply to all similar
    └─ Record Result
    ↓
All Issues Resolved
    ↓
Display Final Summary
```

## Error Handling Strategy

### API Errors

- **Rate Limiting:** Exponential backoff with jitter, respect `Retry-After` headers
- **Authentication:** Fail fast with clear error message, suggest token check
- **Network Errors:** Retry up to 3 times with increasing delays
- **Invalid Username:** Detect 404, fail immediately with helpful message

### Git Errors

- **Clone Failures:** Capture stderr, classify error type, add to issues list
- **Disk Space:** Check before cloning, fail gracefully if insufficient
- **Permission Errors:** Detect SSH vs HTTPS, suggest using HTTPS with token
- **Corrupted Repos:** Allow user to retry or skip

### Conflict Handling

- **Existing Repo:** Don't overwrite, add to conflict list for user decision
- **Existing Non-Repo:** Error clearly, offer to rename/move
- **Symbolic Links:** Error, don't follow symlinks automatically

## Testing Strategy

### Unit Tests

- Configuration parsing and validation
- API client response parsing
- Progress calculation logic
- Error classification
- Path construction

### Integration Tests

- GitHub API mocking (using responses/aioresponses)
- GitLab API mocking
- End-to-end download flow with mock git
- Rate limit handling
- Pagination edge cases

### Manual Testing

- Real GitHub/GitLab downloads
- Dashboard rendering in different terminals
- Command shell responsiveness
- Graceful shutdown
- Resume functionality

## Security Considerations

### Token Handling

- Never log tokens in plain text
- Redact tokens in error messages
- Support environment variables
- Use credential helpers if available
- Clear tokens from memory after use

### URL Injection

- Validate all URLs from API responses
- Prevent directory traversal in repository names
- Sanitize all user inputs

### Subprocess Security

- Use subprocess with argument lists (not shell=True)
- Validate all paths before passing to git
- Set appropriate timeouts

## Performance Optimization

### Parallelism

- Configurable concurrency (default: 5)
- Semaphore-based limiting
- Non-blocking I/O for API calls
- Thread pool for git subprocess calls

### Rate Limit Management

- Pre-check rate limits before batch operations
- Adaptive delays based on remaining quota
- Cache API responses where appropriate

### Memory Management

- Stream large repository lists
- Don't load all repos into memory at once
- Clean up completed items from dashboard table

## Future Enhancements (Out of Scope for v1)

- Incremental updates (pull existing repos instead of full re-clone)
- Compression/archival options
- Differential sync
- Web UI for monitoring
- Multi-platform support (Bitbucket, Gitea, etc.)
- Repository deduplication (identify forks)
- Bandwidth throttling
- Custom clone depth options
- Mirror mode (bare clones)

## Success Criteria

- Successfully download 100+ repositories without manual intervention
- Handle rate limits gracefully without failing
- Recover from network interruptions via resume
- Clear, actionable error messages
- Dashboard updates in real-time (<500ms lag)
- Memory usage stays under 500MB for 1000 repos
- All unit tests pass
- Works on Linux, macOS, Windows

## Timeline (No Specific Dates)

### Phase 1: Core Functionality
- Configuration system
- API clients (GitHub, GitLab)
- Basic download engine
- Simple progress output

### Phase 2: Advanced Features
- Rich dashboard
- Interactive command shell
- Error resolution system
- Resume capability

### Phase 3: Polish
- Library API
- Comprehensive tests
- Documentation
- Error message improvements

### Phase 4: Release
- PyPI package
- CLI installation (pipx)
- README and examples
- GitHub Actions for CI/CD

## Appendix

### Example Use Cases

**1. Backup All Personal Repos:**
```bash
repo-dl download github myusername --token $GITHUB_TOKEN --output-dir ~/backups
```

**2. Clone Organization Repos for Offline Work:**
```bash
repo-dl download github mycompany --no-forks --max-parallel 10
```

**3. Mirror Open Source Projects:**
```yaml
# config.yaml
targets:
  - platform: github
    username: kubernetes
  - platform: github
    username: docker
  - platform: gitlab
    username: gitlab-org
```

```bash
repo-dl download --config config.yaml
```

**4. Programmatic Backup Script:**
```python
import asyncio
from simple_repo_downloader import RepoDownloader, Config, Target

async def backup():
    config = Config.from_env()
    downloader = RepoDownloader(config)

    results = await downloader.download_all(
        targets=[Target(platform='github', username='myorg')],
        headless=True
    )

    if results.issues:
        # Send alert
        send_slack_alert(f"Backup failed for {len(results.issues)} repos")

asyncio.run(backup())
```

---

**End of Design Document**
