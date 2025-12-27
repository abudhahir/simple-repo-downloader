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

    def _inject_token(self, clone_url: str, platform: str, token: Optional[str]) -> str:
        """Inject authentication token into clone URL."""
        if not token:
            return clone_url

        # Convert https://github.com/user/repo.git
        # to https://TOKEN@github.com/user/repo.git
        if clone_url.startswith('https://'):
            parts = clone_url.replace('https://', '').split('/', 1)
            domain = parts[0]
            path = parts[1] if len(parts) > 1 else ''

            if platform == 'github':
                return f'https://{token}@{domain}/{path}'
            elif platform == 'gitlab':
                return f'https://oauth2:{token}@{domain}/{path}'

        return clone_url

    async def _clone_repo(
        self,
        repo: RepoInfo,
        callback: Optional[Callable],
        token: Optional[str] = None
    ) -> None:
        """Clone a repository to the configured location."""
        # Construct destination path
        dest = self.config.base_directory / repo.platform / repo.username / repo.name

        # Check for conflicts
        if dest.exists():
            if (dest / '.git').exists():
                raise FileExistsError(f"Repository already exists: {dest}")
            else:
                raise FileExistsError(f"Non-git directory exists: {dest}")

        # Create parent directories
        dest.parent.mkdir(parents=True, exist_ok=True)

        # Inject token into URL
        clone_url = self._inject_token(repo.clone_url, repo.platform, token)

        # Execute git clone in thread pool
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._git_clone_subprocess,
            clone_url,
            dest
        )

    def _git_clone_subprocess(self, url: str, dest: Path) -> None:
        """Execute git clone using subprocess."""
        result = subprocess.run(
            ['git', 'clone', '--progress', url, str(dest)],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(f"Git clone failed: {result.stderr}")
