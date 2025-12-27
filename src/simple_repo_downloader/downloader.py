import asyncio
import subprocess
from pathlib import Path
from typing import Callable, List, Optional

from .config import DownloadConfig
from .models import DownloadIssue, DownloadResult, RepoInfo, IssueType


class DownloadEngine:
    """Engine for parallel repository downloads."""

    def __init__(self, config: DownloadConfig):
        self.config = config
        self.semaphore = asyncio.Semaphore(config.max_parallel)
        self.download_queue: asyncio.Queue[RepoInfo] = asyncio.Queue()
        self.results: List[DownloadResult] = []
        self.issues: List[DownloadIssue] = []
