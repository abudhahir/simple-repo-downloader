"""Simple Repository Downloader - A tool for downloading all repos from GitHub/GitLab users."""

__version__ = "0.1.0"

from .models import (
    RepoInfo,
    DownloadResult,
    DownloadIssue,
    IssueType,
    RateLimitInfo,
    StateEnum,
)
from .config import (
    AppConfig,
    DownloadConfig,
    Target,
    Credentials,
)
from .api_client import (
    PlatformClient,
    GitHubClient,
    GitLabClient,
)
from .downloader import (
    DownloadEngine,
    DownloadResults,
)
from .dashboard import (
    RepoStatus,
    DownloadStatus,
)

__all__ = [
    "__version__",
    # Models
    "RepoInfo",
    "DownloadResult",
    "DownloadIssue",
    "IssueType",
    "RateLimitInfo",
    "StateEnum",
    # Config
    "AppConfig",
    "DownloadConfig",
    "Target",
    "Credentials",
    # API Clients
    "PlatformClient",
    "GitHubClient",
    "GitLabClient",
    # Downloader
    "DownloadEngine",
    "DownloadResults",
    # Status Tracking
    "RepoStatus",
    "DownloadStatus",
]
