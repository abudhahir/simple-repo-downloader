# Progress Output Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace TUI dashboard with scrollable progress output and file logging

**Architecture:** Remove Rich Live dashboard, create ProgressPrinter class that outputs to both console (with Rich markdown) and log file, maintain status tracking for final summary

**Tech Stack:** Rich (Console, Markdown), Python logging, asyncio

---

## Task 1: Create ProgressPrinter Class

**Files:**
- Create: `src/simple_repo_downloader/progress.py`
- Test: `tests/test_progress.py`

**Step 1: Write failing test for ProgressPrinter initialization**

Create `tests/test_progress.py`:

```python
from pathlib import Path
from simple_repo_downloader.progress import ProgressPrinter


def test_progress_printer_initialization(tmp_path):
    """Test ProgressPrinter initializes with log file path."""
    log_file = tmp_path / "test.log"
    printer = ProgressPrinter(log_file=log_file)

    assert printer.log_file == log_file
    assert printer.start_time is not None
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_progress.py::test_progress_printer_initialization -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'simple_repo_downloader.progress'"

**Step 3: Write minimal implementation**

Create `src/simple_repo_downloader/progress.py`:

```python
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console


class ProgressPrinter:
    """Progress printer that outputs to console and log file."""

    def __init__(self, log_file: Optional[Path] = None):
        self.console = Console()
        self.log_file = log_file
        self.start_time = datetime.now()

        # Create log directory if needed
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_progress.py::test_progress_printer_initialization -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_progress.py src/simple_repo_downloader/progress.py
git commit -m "feat: add ProgressPrinter class with log file support"
```

---

## Task 2: Add Print Start Method

**Files:**
- Modify: `src/simple_repo_downloader/progress.py`
- Modify: `tests/test_progress.py`

**Step 1: Write failing test for print_start**

Add to `tests/test_progress.py`:

```python
from simple_repo_downloader.models import RepoInfo


def test_print_start(tmp_path, capsys):
    """Test print_start displays repository count."""
    log_file = tmp_path / "test.log"
    printer = ProgressPrinter(log_file=log_file)

    repos = [
        RepoInfo(
            platform='github',
            username='test',
            name='repo1',
            clone_url='https://github.com/test/repo1.git',
            is_fork=False,
            is_private=True,
            is_archived=False,
            size_kb=100,
            default_branch='main'
        ),
        RepoInfo(
            platform='github',
            username='test',
            name='repo2',
            clone_url='https://github.com/test/repo2.git',
            is_fork=False,
            is_private=False,
            is_archived=False,
            size_kb=200,
            default_branch='main'
        ),
    ]

    printer.print_start(repos, max_parallel=5)

    captured = capsys.readouterr()
    assert "Found 2 repositories" in captured.out
    assert "1 private, 1 public" in captured.out
    assert "5 parallel workers" in captured.out

    # Check log file
    log_content = log_file.read_text()
    assert "Found 2 repositories" in log_content
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_progress.py::test_print_start -v
```

Expected: FAIL with "AttributeError: 'ProgressPrinter' object has no attribute 'print_start'"

**Step 3: Write minimal implementation**

Add to `src/simple_repo_downloader/progress.py`:

```python
from typing import List
from .models import RepoInfo


class ProgressPrinter:
    # ... existing code ...

    def print_start(self, repos: List[RepoInfo], max_parallel: int) -> None:
        """Print initial header with repository counts."""
        private_count = sum(1 for r in repos if r.is_private)
        public_count = len(repos) - private_count

        message = (
            f"Found {len(repos)} repositories "
            f"({private_count} private, {public_count} public)\n"
            f"Starting download with {max_parallel} parallel workers...\n"
        )

        self.console.print(message)
        self._log(message)

    def _log(self, message: str) -> None:
        """Write message to log file with timestamp."""
        if self.log_file:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.log_file, 'a') as f:
                f.write(f"{timestamp} | {message}\n")
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_progress.py::test_print_start -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_progress.py src/simple_repo_downloader/progress.py
git commit -m "feat: add print_start method with repo counts"
```

---

## Task 3: Add Print Repo Update Method

**Files:**
- Modify: `src/simple_repo_downloader/progress.py`
- Modify: `tests/test_progress.py`

**Step 1: Write failing test for print_repo_update**

Add to `tests/test_progress.py`:

```python
from simple_repo_downloader.models import StateEnum


def test_print_repo_update(tmp_path, capsys):
    """Test print_repo_update displays progress line."""
    log_file = tmp_path / "test.log"
    printer = ProgressPrinter(log_file=log_file)

    repo = RepoInfo(
        platform='github',
        username='test',
        name='my-repo',
        clone_url='https://github.com/test/my-repo.git',
        is_fork=False,
        is_private=True,
        is_archived=False,
        size_kb=100,
        default_branch='main'
    )

    printer.print_repo_update(
        current=5,
        total=57,
        repo=repo,
        state=StateEnum.COMPLETED,
        message="Cloned successfully"
    )

    captured = capsys.readouterr()
    assert "[5/57]" in captured.out
    assert "PRIVATE" in captured.out
    assert "github/test/my-repo" in captured.out
    assert "Cloned successfully" in captured.out

    # Check log file
    log_content = log_file.read_text()
    assert "[5/57]" in log_content
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_progress.py::test_print_repo_update -v
```

Expected: FAIL with "AttributeError: 'ProgressPrinter' object has no attribute 'print_repo_update'"

**Step 3: Write minimal implementation**

Add to `src/simple_repo_downloader/progress.py`:

```python
from .models import StateEnum


class ProgressPrinter:
    # ... existing code ...

    def print_repo_update(
        self,
        current: int,
        total: int,
        repo: RepoInfo,
        state: StateEnum,
        message: str
    ) -> None:
        """Print single repo progress update."""
        # Status emoji mapping
        status_emoji = {
            StateEnum.COMPLETED: "✓",
            StateEnum.DOWNLOADING: "⏳",
            StateEnum.FAILED: "❌",
            StateEnum.UPDATED: "🔄",
            StateEnum.UP_TO_DATE: "✓",
            StateEnum.UNCOMMITTED_CHANGES: "⚠",
            StateEnum.AHEAD: "↑",
            StateEnum.QUEUED: "⏳",
            StateEnum.PAUSED: "⏸",
            StateEnum.SKIPPED: "⏭",
        }

        emoji = status_emoji.get(state, "•")
        visibility = "PRIVATE" if repo.is_private else "PUBLIC"
        repo_path = f"{repo.platform}/{repo.username}/{repo.name}"

        line = f"[{current}/{total}] {emoji} [{visibility}] {repo_path} - {message}"

        self.console.print(line)
        self._log(line)
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_progress.py::test_print_repo_update -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_progress.py src/simple_repo_downloader/progress.py
git commit -m "feat: add print_repo_update with progress tracking"
```

---

## Task 4: Add Print Summary Method with Rich Markdown

**Files:**
- Modify: `src/simple_repo_downloader/progress.py`
- Modify: `tests/test_progress.py`

**Step 1: Write failing test for print_summary**

Add to `tests/test_progress.py`:

```python
from simple_repo_downloader.dashboard import DownloadStatus, RepoStatus


def test_print_summary(tmp_path, capsys):
    """Test print_summary displays markdown table."""
    log_file = tmp_path / "test.log"
    printer = ProgressPrinter(log_file=log_file)

    # Create status with some repos
    status = DownloadStatus()

    repo1 = RepoInfo(
        platform='github',
        username='test',
        name='repo1',
        clone_url='https://github.com/test/repo1.git',
        is_fork=False,
        is_private=False,
        is_archived=False,
        size_kb=100,
        default_branch='main'
    )

    repo2 = RepoInfo(
        platform='github',
        username='test',
        name='repo2',
        clone_url='https://github.com/test/repo2.git',
        is_fork=False,
        is_private=True,
        is_archived=False,
        size_kb=200,
        default_branch='main'
    )

    status.repos['github/test/repo1'] = RepoStatus(
        repo=repo1,
        state=StateEnum.FAILED,
        error="Permission denied"
    )

    status.repos['github/test/repo2'] = RepoStatus(
        repo=repo2,
        state=StateEnum.UNCOMMITTED_CHANGES,
        error="Uncommitted changes, 2 commits behind"
    )

    printer.print_summary(status)

    captured = capsys.readouterr()
    assert "Download Summary" in captured.out
    assert "Failed: 1 repo" in captured.out or "Failed:** 1" in captured.out
    assert "repo1" in captured.out
    assert "Permission denied" in captured.out
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_progress.py::test_print_summary -v
```

Expected: FAIL with "AttributeError: 'ProgressPrinter' object has no attribute 'print_summary'"

**Step 3: Write minimal implementation**

Add to `src/simple_repo_downloader/progress.py`:

```python
from rich.markdown import Markdown
from .dashboard import DownloadStatus


class ProgressPrinter:
    # ... existing code ...

    def print_summary(self, status: DownloadStatus) -> None:
        """Print final summary with markdown table."""
        elapsed = datetime.now() - self.start_time
        elapsed_str = str(elapsed).split('.')[0]  # Remove microseconds

        # Count repos by state
        completed = sum(1 for r in status.repos.values() if r.state == StateEnum.COMPLETED)
        updated = sum(1 for r in status.repos.values() if r.state == StateEnum.UPDATED)
        up_to_date = sum(1 for r in status.repos.values() if r.state == StateEnum.UP_TO_DATE)
        uncommitted = sum(1 for r in status.repos.values() if r.state == StateEnum.UNCOMMITTED_CHANGES)
        ahead = sum(1 for r in status.repos.values() if r.state == StateEnum.AHEAD)
        failed = sum(1 for r in status.repos.values() if r.state == StateEnum.FAILED)

        # Build markdown summary
        md = f"""# Download Summary

## Results
- ✓ **Cloned**: {completed} repos
- 🔄 **Updated**: {updated} repos
- ✓ **Already up to date**: {up_to_date} repos
- ⚠️ **Uncommitted changes**: {uncommitted} repos
- ↑ **Ahead of remote**: {ahead} repos
- ❌ **Failed**: {failed} repos
"""

        # Add issues table if there are any
        issues = [
            (r.repo, r.state, r.error)
            for r in status.repos.values()
            if r.state in [StateEnum.FAILED, StateEnum.UNCOMMITTED_CHANGES, StateEnum.AHEAD]
        ]

        if issues:
            md += "\n## Issues Requiring Attention\n\n"
            md += "| Status | Visibility | Repository | Reason | Link |\n"
            md += "|--------|------------|------------|--------|------|\n"

            for repo, state, error in issues:
                status_emoji = {
                    StateEnum.FAILED: "❌",
                    StateEnum.UNCOMMITTED_CHANGES: "⚠️",
                    StateEnum.AHEAD: "↑"
                }[state]

                visibility = "PRIVATE" if repo.is_private else "PUBLIC"
                repo_path = f"{repo.platform}/{repo.username}/{repo.name}"

                # Convert clone_url to web URL
                web_url = repo.clone_url.replace('.git', '')
                platform_icon = "🐙" if repo.platform == "github" else "🦊"

                md += f"| {status_emoji} | {visibility} | `{repo_path}` | {error} | [{platform_icon}]({web_url}) |\n"

        md += f"\n---\n**Total:** {len(status.repos)} repositories processed | **Time:** {elapsed_str}\n"

        # Print to console with Rich markdown rendering
        self.console.print(Markdown(md))

        # Log plain text version
        self._log("\n" + md)
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_progress.py::test_print_summary -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_progress.py src/simple_repo_downloader/progress.py
git commit -m "feat: add print_summary with Rich markdown table"
```

---

## Task 5: Update CLI to Use ProgressPrinter

**Files:**
- Modify: `src/simple_repo_downloader/cli.py:139-183`
- Test: `tests/test_cli.py`

**Step 1: Write failing test for CLI with progress output**

Add to `tests/test_cli.py`:

```python
import pytest
from pathlib import Path


@pytest.mark.asyncio
async def test_cli_uses_progress_printer(tmp_path, monkeypatch):
    """Test CLI uses ProgressPrinter instead of Dashboard."""
    from simple_repo_downloader.cli import _download_from_args
    from unittest.mock import AsyncMock, MagicMock, patch

    # Mock the API client
    mock_repos = []
    mock_client = AsyncMock()
    mock_client.list_repositories = AsyncMock(return_value=mock_repos)

    with patch('simple_repo_downloader.cli.aiohttp.ClientSession'):
        with patch('simple_repo_downloader.cli.GitHubClient', return_value=mock_client):
            with patch('simple_repo_downloader.cli.ProgressPrinter') as mock_printer:
                mock_printer_instance = MagicMock()
                mock_printer.return_value = mock_printer_instance

                # Run download
                await _download_from_args(
                    platform='github',
                    username='test',
                    token='fake-token',
                    max_parallel=5,
                    output_dir=str(tmp_path),
                    no_forks=False,
                    headless=False,
                    verbose=False
                )

                # Verify ProgressPrinter was created
                mock_printer.assert_called_once()
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_cli.py::test_cli_uses_progress_printer -v
```

Expected: FAIL (because CLI still uses Dashboard)

**Step 3: Update CLI implementation**

Modify `src/simple_repo_downloader/cli.py`:

```python
# Remove Dashboard import, add ProgressPrinter
from .progress import ProgressPrinter
from pathlib import Path as PathLib

async def _download_from_args(
    platform: str,
    username: str,
    token: str | None,
    max_parallel: int,
    output_dir: str,
    no_forks: bool,
    headless: bool,  # Keep for backward compatibility but ignore
    verbose: bool
):
    """Execute download from CLI arguments."""
    from .api_client import APIError

    # Create download config
    download_config = DownloadConfig(
        base_directory=Path(output_dir),
        max_parallel=max_parallel
    )

    # ... existing API client and repo fetching code ...

    # Handle empty repository list
    if not repos:
        click.echo("No repositories to download. Exiting.")
        return

    # Create log file path
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_dir = PathLib.home() / ".simple-repo-downloader" / "logs"
    log_file = log_dir / f"download-{timestamp}.log"

    # Create progress printer
    printer = ProgressPrinter(log_file=log_file)
    printer.print_start(repos, max_parallel)

    # Create status tracker
    from .dashboard import DownloadStatus, RepoStatus
    from .models import StateEnum
    status = DownloadStatus()
    for repo in repos:
        repo_id = f"{repo.platform}/{repo.username}/{repo.name}"
        status.repos[repo_id] = RepoStatus(repo=repo, state=StateEnum.QUEUED)

    # Track current repo index
    repo_counter = {'current': 0}

    # Create callback
    async def status_callback(repo, state, progress, error):
        repo_id = f"{repo.platform}/{repo.username}/{repo.name}"
        if repo_id in status.repos:
            # Update status
            state_enum = getattr(StateEnum, state.upper(), StateEnum.QUEUED)
            status.repos[repo_id].state = state_enum
            status.repos[repo_id].progress_pct = progress
            if error:
                status.repos[repo_id].error = error

            # Print update for completed repos only
            if state_enum in [StateEnum.COMPLETED, StateEnum.FAILED, StateEnum.UPDATED,
                             StateEnum.UP_TO_DATE, StateEnum.UNCOMMITTED_CHANGES, StateEnum.AHEAD]:
                repo_counter['current'] += 1
                message = error if error else "Cloned successfully"
                printer.print_repo_update(
                    current=repo_counter['current'],
                    total=len(repos),
                    repo=repo,
                    state=state_enum,
                    message=message
                )

    # Create engine with callback
    engine = DownloadEngine(download_config, status_callback=status_callback)

    # Run download
    await engine.download_all(repos, token=token)

    # Print summary
    printer.print_summary(status)

    if verbose:
        click.echo(f"\nLog saved to: {log_file}")
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_cli.py::test_cli_uses_progress_printer -v
```

Expected: PASS

**Step 5: Run all tests to ensure nothing broke**

```bash
uv run pytest -v
```

Expected: All tests PASS

**Step 6: Commit**

```bash
git add src/simple_repo_downloader/cli.py tests/test_cli.py
git commit -m "feat: replace Dashboard with ProgressPrinter in CLI"
```

---

## Task 6: Remove --headless Flag

**Files:**
- Modify: `src/simple_repo_downloader/cli.py:28`
- Modify: `src/simple_repo_downloader/cli.py:30`

**Step 1: Remove headless flag from CLI**

Remove the `--headless` flag option and parameter from the download command in `src/simple_repo_downloader/cli.py`.

**Step 2: Update function signature**

Remove `headless` parameter from `_download_from_args` function (already ignored in Task 5).

**Step 3: Update documentation**

Update README.md and QUICKSTART.md to remove references to `--headless` flag.

**Step 4: Commit**

```bash
git add src/simple_repo_downloader/cli.py README.md QUICKSTART.md
git commit -m "refactor: remove --headless flag (progress output is default)"
```

---

## Task 7: Clean Up Dashboard Module

**Files:**
- Modify: `src/simple_repo_downloader/dashboard.py`
- Modify: `tests/test_dashboard.py`

**Step 1: Remove Dashboard class and TUI code**

Keep `DownloadStatus` and `RepoStatus` classes (still needed for tracking), but remove:
- `Dashboard` class
- All Rich Layout/Live code
- Interactive command methods

**Step 2: Update tests**

Remove tests for Dashboard TUI functionality, keep tests for DownloadStatus and RepoStatus.

**Step 3: Run tests**

```bash
uv run pytest tests/test_dashboard.py -v
```

Expected: Remaining tests PASS

**Step 4: Commit**

```bash
git add src/simple_repo_downloader/dashboard.py tests/test_dashboard.py
git commit -m "refactor: remove Dashboard TUI, keep status tracking"
```

---

## Task 8: Final Integration Test

**Files:**
- Test manually with real repository

**Step 1: Run with verbose flag**

```bash
uv run python -m simple_repo_downloader.cli download github <username> --verbose
```

**Step 2: Verify output**

- [ ] Progress lines show [N/total] format
- [ ] Private/public labels appear
- [ ] Status emojis display correctly
- [ ] Final summary renders as markdown table
- [ ] Issues table shows with clickable links
- [ ] Log file created in ~/.simple-repo-downloader/logs/

**Step 3: Check log file**

```bash
cat ~/.simple-repo-downloader/logs/download-*.log
```

Verify timestamps and all events logged.

**Step 4: Run full test suite**

```bash
uv run pytest -v
```

Expected: All tests PASS

**Step 5: Final commit**

```bash
git add -A
git commit -m "test: verify progress output with real repos"
```

---

## Completion Checklist

- [ ] All tests passing
- [ ] Progress output displays correctly
- [ ] Log file created and populated
- [ ] Markdown summary renders properly
- [ ] Platform icons (🐙/🦊) appear in links
- [ ] Private/public labels show
- [ ] --headless flag removed
- [ ] Documentation updated
- [ ] Clean git history with focused commits
