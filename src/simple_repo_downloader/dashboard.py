# src/simple_repo_downloader/dashboard.py
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from .models import RepoInfo, StateEnum
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live

@dataclass
class RepoStatus:
    """Status of a single repository download."""
    repo: RepoInfo
    state: StateEnum
    progress_pct: int = 0
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

@dataclass
class DownloadStatus:
    """Overall download status for dashboard."""
    repos: Dict[str, RepoStatus] = field(default_factory=dict)
    events: List[str] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)

    def _count_by_state(self, state: StateEnum) -> int:
        """Helper method to count repos by state."""
        return sum(1 for r in self.repos.values() if r.state == state)

    @property
    def queued_count(self) -> int:
        return self._count_by_state(StateEnum.QUEUED)

    @property
    def downloading_count(self) -> int:
        return self._count_by_state(StateEnum.DOWNLOADING)

    @property
    def completed_count(self) -> int:
        return self._count_by_state(StateEnum.COMPLETED)

    @property
    def failed_count(self) -> int:
        return self._count_by_state(StateEnum.FAILED)

    @property
    def paused_count(self) -> int:
        return self._count_by_state(StateEnum.PAUSED)

    @property
    def skipped_count(self) -> int:
        return self._count_by_state(StateEnum.SKIPPED)

    def add_event(self, message: str) -> None:
        """Add event to log with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.events.append(f"[{timestamp}] {message}")


class Dashboard:
    """Real-time terminal dashboard for download progress."""

    COMMANDS_HELP = """
Available Commands:
  pause <repo>   - Pause specific repository download
  resume <repo>  - Resume paused repository
  skip <repo>    - Skip repository (won't download)
  clear-log      - Clear event log
  status         - Show detailed status
  help           - Show this help
  quit           - Graceful shutdown
"""

    def __init__(self) -> None:
        self.console = Console()

    def _parse_command(self, cmd_str: str) -> tuple[str, list[str]]:
        """Parse command string into command and arguments."""
        parts = cmd_str.strip().split()
        if not parts:
            return "", []
        return parts[0], parts[1:]

    async def _execute_command(self, cmd: str, args: list[str], status: DownloadStatus) -> Optional[str]:
        """Execute a dashboard command."""
        if cmd == "help":
            return self.COMMANDS_HELP

        elif cmd == "clear-log":
            status.events.clear()
            return "Event log cleared"

        elif cmd == "status":
            return (
                f"Queued: {status.queued_count}, "
                f"Downloading: {status.downloading_count}, "
                f"Completed: {status.completed_count}, "
                f"Failed: {status.failed_count}"
            )

        elif cmd == "pause":
            if not args:
                return "Error: pause requires repo ID"
            repo_id = args[0]
            if repo_id in status.repos:
                status.repos[repo_id].state = StateEnum.PAUSED
                return f"Paused {repo_id}"
            return f"Error: repo {repo_id} not found"

        elif cmd == "resume":
            if not args:
                return "Error: resume requires repo ID"
            repo_id = args[0]
            if repo_id in status.repos:
                if status.repos[repo_id].state == StateEnum.PAUSED:
                    status.repos[repo_id].state = StateEnum.QUEUED
                    return f"Resumed {repo_id}"
                return f"Error: {repo_id} is not paused"
            return f"Error: repo {repo_id} not found"

        elif cmd == "skip":
            if not args:
                return "Error: skip requires repo ID"
            repo_id = args[0]
            if repo_id in status.repos:
                status.repos[repo_id].state = StateEnum.SKIPPED
                return f"Skipped {repo_id}"
            return f"Error: repo {repo_id} not found"

        elif cmd == "quit":
            # Quit is not handled as a special signal here; inform the user how to exit.
            return "Quit command is not supported; use Ctrl+C to exit the dashboard."

        else:
            return f"Unknown command: {cmd}. Type 'help' for available commands."

    def _build_repo_table(self, status: DownloadStatus) -> Table:
        """Build Rich table of repository statuses."""
        table = Table(title="Repository Downloads", show_header=True, header_style="bold magenta")
        table.add_column("Platform", style="cyan", width=8)
        table.add_column("User", style="cyan", width=15)
        table.add_column("Repository", style="green", width=25)
        table.add_column("Status", width=12)
        table.add_column("Progress", width=15)

        for repo_id, repo_status in status.repos.items():
            # Status emoji
            if repo_status.state == StateEnum.DOWNLOADING:
                status_text = "🔄 Cloning"
            elif repo_status.state == StateEnum.COMPLETED:
                status_text = "✅ Done"
            elif repo_status.state == StateEnum.FAILED:
                status_text = "❌ Failed"
            elif repo_status.state == StateEnum.PAUSED:
                status_text = "⏸  Paused"
            elif repo_status.state == StateEnum.SKIPPED:
                status_text = "⏭  Skipped"
            else:  # QUEUED
                status_text = "⏳ Queued"

            # Progress bar
            if repo_status.state == StateEnum.DOWNLOADING:
                bar_fraction = repo_status.progress_pct / 100 * 10
                bar_width = int(bar_fraction)
                has_partial = (bar_fraction - bar_width) >= 0.5
                progress_text = f"{'█' * bar_width}{'▌' if has_partial else ''}{'░' * (10 - bar_width - (1 if has_partial else 0))} {repo_status.progress_pct}%"
            elif repo_status.state == StateEnum.COMPLETED:
                progress_text = "██████████ 100%"
            else:
                progress_text = ""

            table.add_row(
                repo_status.repo.platform,
                repo_status.repo.username,
                repo_status.repo.name,
                status_text,
                progress_text
            )

        return table

    def _build_summary_panel(self, status: DownloadStatus) -> Panel:
        """Build summary statistics panel."""
        elapsed = datetime.now() - status.start_time
        elapsed_str = str(elapsed).split('.')[0]  # Remove microseconds

        summary_text = (
            f"[bold]Summary:[/bold] "
            f"{status.downloading_count} downloading | "
            f"{status.completed_count} completed | "
            f"{status.failed_count} failed | "
            f"{status.queued_count} queued\n"
            f"[bold]Elapsed:[/bold] {elapsed_str}"
        )

        return Panel(summary_text, title="Statistics", border_style="blue")

    def _build_event_log_panel(self, status: DownloadStatus, max_events: int = 10) -> Panel:
        """Build event log panel with recent events."""
        recent_events = status.events[-max_events:] if len(status.events) > max_events else status.events

        if not recent_events:
            event_text = "[dim]No events yet[/dim]"
        else:
            event_text = "\n".join(recent_events)

        return Panel(event_text, title="Recent Events", border_style="yellow")

    def _build_layout(self, status: DownloadStatus) -> Layout:
        """Build complete dashboard layout."""
        layout = Layout()

        # Split into upper and lower sections
        layout.split_column(
            Layout(name="main", ratio=3),
            Layout(name="footer", size=5)
        )

        # Upper section: table and summary
        layout["main"].split_column(
            Layout(self._build_repo_table(status), name="table", ratio=2),
            Layout(self._build_summary_panel(status), name="summary", size=4)
        )

        # Footer: events and command prompt
        layout["footer"].split_column(
            Layout(self._build_event_log_panel(status), name="events", size=4),
            Layout(Panel("Type 'help' for commands", title="Command Shell"), name="shell", size=1)
        )

        return layout

    async def run_live(self, status: DownloadStatus, refresh_rate: float = 0.25):
        """Run live dashboard with updates."""
        refresh_per_sec = int(1 / refresh_rate) if refresh_rate > 0 else 4
        with Live(self._build_layout(status), console=self.console, refresh_per_second=refresh_per_sec) as live:
            while True:
                # Update display
                live.update(self._build_layout(status))

                # Check if all downloads complete
                if status.downloading_count == 0 and status.queued_count == 0:
                    break

                await asyncio.sleep(refresh_rate)
