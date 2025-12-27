import asyncio
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional

from .config import DownloadConfig
from .models import DownloadIssue, DownloadResult, RepoInfo, IssueType


@dataclass
class DownloadResults:
    """Results from a batch download operation."""
    successful: List[DownloadResult]
    issues: List[DownloadIssue]


class DownloadEngine:
    """Engine for parallel repository downloads."""

    def __init__(self, config: DownloadConfig, status_callback: Optional[Callable] = None):
        self.config = config
        self.semaphore = asyncio.Semaphore(config.max_parallel)
        self.download_queue: asyncio.Queue[RepoInfo] = asyncio.Queue()
        self.results: List[DownloadResult] = []
        self.issues: List[DownloadIssue] = []
        self.status_callback = status_callback

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

    async def _worker(
        self,
        worker_id: int,
        callback: Optional[Callable],
        token: Optional[str]
    ) -> None:
        """Worker coroutine for processing download queue."""
        while True:
            try:
                repo = await self.download_queue.get()

                # Notify status: starting download
                if self.status_callback:
                    await self.status_callback(repo, "downloading", 0)

                try:
                    async with self.semaphore:
                        await self._clone_repo(repo, callback, token)
                        self.results.append(
                            DownloadResult(repo=repo, success=True)
                        )
                        # Notify status: completed
                        if self.status_callback:
                            await self.status_callback(repo, "completed", 100)
                except FileExistsError as e:
                    self.issues.append(
                        DownloadIssue(
                            repo=repo,
                            issue_type=IssueType.CONFLICT,
                            message=str(e),
                            existing_path=self.config.base_directory / repo.platform / repo.username / repo.name
                        )
                    )
                    # Notify status: failed
                    if self.status_callback:
                        await self.status_callback(repo, "failed", 0)
                except Exception as e:
                    issue_type = self._classify_error(e)
                    self.issues.append(
                        DownloadIssue(
                            repo=repo,
                            issue_type=issue_type,
                            message=str(e)
                        )
                    )
                    # Notify status: failed
                    if self.status_callback:
                        await self.status_callback(repo, "failed", 0)
                finally:
                    self.download_queue.task_done()
            except asyncio.CancelledError:
                break

    def _classify_error(self, error: Exception) -> IssueType:
        """Classify an error into an IssueType."""
        error_str = str(error).lower()

        if 'permission denied' in error_str or 'unauthorized' in error_str:
            return IssueType.AUTH_ERROR
        elif 'network' in error_str or 'connection' in error_str:
            return IssueType.NETWORK_ERROR
        elif 'git' in error_str:
            return IssueType.GIT_ERROR
        else:
            return IssueType.GIT_ERROR

    async def download_all(
        self,
        repos: List[RepoInfo],
        progress_callback: Optional[Callable] = None,
        token: Optional[str] = None
    ) -> DownloadResults:
        """Download all repositories in parallel."""
        # Clear previous results
        self.results = []
        self.issues = []

        # Populate queue
        for repo in repos:
            await self.download_queue.put(repo)

        # Spawn workers
        workers = [
            asyncio.create_task(self._worker(i, progress_callback, token))
            for i in range(self.config.max_parallel)
        ]

        # Wait for all downloads to complete
        await self.download_queue.join()

        # Cancel workers
        for worker in workers:
            worker.cancel()

        # Wait for workers to finish
        await asyncio.gather(*workers, return_exceptions=True)

        return DownloadResults(
            successful=self.results,
            issues=self.issues
        )
