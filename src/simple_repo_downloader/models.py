from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


@dataclass
class RepoInfo:
    """Information about a repository to be downloaded."""

    platform: str
    username: str
    name: str
    clone_url: str
    is_fork: bool
    is_private: bool
    is_archived: bool
    size_kb: int
    default_branch: str


class IssueType(Enum):
    """Types of download issues that can occur."""

    CONFLICT = "conflict"
    FILE_CONFLICT = "file_conflict"
    NETWORK_ERROR = "network"
    AUTH_ERROR = "auth"
    GIT_ERROR = "git"
    RATE_LIMIT = "rate_limit"


@dataclass
class DownloadResult:
    """Result of a repository download attempt."""

    repo: RepoInfo
    success: bool
    error: Optional[str] = None


@dataclass
class DownloadIssue:
    """An issue that occurred during download."""

    repo: RepoInfo
    issue_type: IssueType
    message: str
    existing_path: Optional[Path] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RateLimitInfo:
    """Rate limit information from API."""

    remaining: int
    limit: int
    reset_timestamp: int
