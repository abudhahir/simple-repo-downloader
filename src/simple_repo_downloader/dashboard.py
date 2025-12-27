# src/simple_repo_downloader/dashboard.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from .models import RepoInfo, DownloadIssue

@dataclass
class RepoStatus:
    """Status of a single repository download."""
    repo: RepoInfo
    state: str  # queued, downloading, completed, failed, paused, skipped
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

    @property
    def queued_count(self) -> int:
        return sum(1 for r in self.repos.values() if r.state == "queued")

    @property
    def downloading_count(self) -> int:
        return sum(1 for r in self.repos.values() if r.state == "downloading")

    @property
    def completed_count(self) -> int:
        return sum(1 for r in self.repos.values() if r.state == "completed")

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.repos.values() if r.state == "failed")

    def add_event(self, message: str):
        """Add event to log with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.events.append(f"[{timestamp}] {message}")
