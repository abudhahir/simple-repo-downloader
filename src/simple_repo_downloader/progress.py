from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.markdown import Markdown

from .models import RepoInfo, StateEnum
from .dashboard import DownloadStatus


class ProgressPrinter:
    """Progress printer that outputs to console and log file."""

    STATE_EMOJIS = {
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

    def __init__(self, log_file: Optional[Path] = None):
        self.console = Console()
        self.log_file = log_file
        self.start_time = datetime.now()

        # Create log directory if needed
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

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

    def print_repo_update(
        self,
        current: int,
        total: int,
        repo: RepoInfo,
        state: StateEnum,
        message: str
    ) -> None:
        """Print single repo progress update."""
        emoji = self.STATE_EMOJIS.get(state, "•")
        visibility = "PRIVATE" if repo.is_private else "PUBLIC"
        repo_path = f"{repo.platform}/{repo.username}/{repo.name}"

        line = f"[{current}/{total}] {emoji} [{visibility}] {repo_path} - {message}"

        self.console.print(line)
        self._log(line)

    def print_summary(self, status: DownloadStatus) -> None:
        """Print final summary with markdown table."""
        elapsed = datetime.now() - self.start_time
        # Better time formatting
        hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        elapsed_str = f"{hours}:{minutes:02d}:{seconds:02d}" if hours > 0 else f"{minutes}:{seconds:02d}"

        # Single pass through repos
        state_counts = Counter(r.state for r in status.repos.values())
        completed = state_counts[StateEnum.COMPLETED]
        updated = state_counts[StateEnum.UPDATED]
        up_to_date = state_counts[StateEnum.UP_TO_DATE]
        uncommitted = state_counts[StateEnum.UNCOMMITTED_CHANGES]
        ahead = state_counts[StateEnum.AHEAD]
        failed = state_counts[StateEnum.FAILED]

        # Add issues table if there are any
        issues = [
            (r.repo, r.state, r.error)
            for r in status.repos.values()
            if r.state in [StateEnum.FAILED, StateEnum.UNCOMMITTED_CHANGES, StateEnum.AHEAD]
        ]

        # Build issue table rows
        issue_rows = []
        if issues:
            for repo, state, error in issues:
                status_emoji = self.STATE_EMOJIS[state]
                visibility = "PRIVATE" if repo.is_private else "PUBLIC"
                repo_path = f"{repo.platform}/{repo.username}/{repo.name}"
                # Safe URL conversion
                web_url = repo.clone_url.removesuffix('.git') if repo.clone_url.endswith('.git') else repo.clone_url
                platform_icon = "🐙" if repo.platform == "github" else "🦊"

                issue_rows.append(
                    f"| {status_emoji} | {visibility} | `{repo_path}` | {error} | [{platform_icon}]({web_url}) |"
                )

        # Build complete markdown
        issue_table = ""
        if issue_rows:
            issue_table = (
                "\n## Issues Requiring Attention\n\n"
                "| Status | Visibility | Repository | Reason | Link |\n"
                "|--------|------------|------------|--------|------|\n"
                + "\n".join(issue_rows) + "\n"
            )

        md = f"""# Download Summary

## Results
- ✓ **Cloned**: {completed} repos
- 🔄 **Updated**: {updated} repos
- ✓ **Already up to date**: {up_to_date} repos
- ⚠️ **Uncommitted changes**: {uncommitted} repos
- ↑ **Ahead of remote**: {ahead} repos
- ❌ **Failed**: {failed} repos
{issue_table}
---
**Total:** {len(status.repos)} repositories processed | **Time:** {elapsed_str}
"""

        # Print to console with Rich markdown rendering
        self.console.print(Markdown(md))

        # Log plain text version
        self._log("\n" + md)

    def _log(self, message: str) -> None:
        """Write message to log file with timestamp."""
        if self.log_file:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.log_file, 'a') as f:
                f.write(f"{timestamp} | {message}")
