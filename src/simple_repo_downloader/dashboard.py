# src/simple_repo_downloader/dashboard.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from .models import RepoInfo, StateEnum

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
