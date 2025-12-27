# src/simple_repo_downloader/dashboard.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from .models import RepoInfo, StateEnum
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.progress import Progress, BarColumn, TextColumn

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

    def add_event(self, message: str):
        """Add event to log with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.events.append(f"[{timestamp}] {message}")


class Dashboard:
    """Real-time terminal dashboard for download progress."""

    def __init__(self):
        self.console = Console()

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
                status_text = "⏸️  Paused"
            elif repo_status.state == StateEnum.SKIPPED:
                status_text = "⏭️  Skipped"
            else:  # QUEUED
                status_text = "⏳ Queued"

            # Progress bar
            if repo_status.state == StateEnum.DOWNLOADING:
                bar_width = int(repo_status.progress_pct / 100 * 10)
                progress_text = f"{'█' * bar_width}{'▌' if bar_width < 10 else ''}{'░' * (10 - bar_width)} {repo_status.progress_pct}%"
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
