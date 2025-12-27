# Simple Repository Downloader Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Python tool for downloading all repositories from GitHub/GitLab users with parallel downloads, real-time dashboard, and interactive error resolution.

**Architecture:** Async Python using asyncio for concurrency, aiohttp for API calls, Rich for TUI, Click for CLI. Components: Config (Pydantic), API Clients (GitHub/GitLab), Download Engine (worker pool), Dashboard (Rich Live), Interactive Resolver.

**Tech Stack:** Python 3.10+, asyncio, aiohttp, click, rich, pydantic, PyYAML

---

## Phase 1: Core Models & Configuration

### Task 1: Create shared data models

**Files:**
- Create: `src/simple_repo_downloader/models.py`
- Test: `tests/test_models.py`

**Step 1: Write failing test for RepoInfo model**

```python
# tests/test_models.py
from simple_repo_downloader.models import RepoInfo

def test_repo_info_creation():
    repo = RepoInfo(
        platform="github",
        username="torvalds",
        name="linux",
        clone_url="https://github.com/torvalds/linux.git",
        is_fork=False,
        is_private=False,
        is_archived=False,
        size_kb=1024,
        default_branch="master"
    )
    assert repo.platform == "github"
    assert repo.username == "torvalds"
    assert repo.name == "linux"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py::test_repo_info_creation -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'simple_repo_downloader.models'"

**Step 3: Write minimal implementation**

```python
# src/simple_repo_downloader/models.py
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from datetime import datetime
from pathlib import Path


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
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class RateLimitInfo:
    """Rate limit information from API."""
    remaining: int
    limit: int
    reset_timestamp: int
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_models.py::test_repo_info_creation -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/simple_repo_downloader/models.py tests/test_models.py
git commit -m "feat: add core data models for repos and download results"
```

---

### Task 2: Create configuration models

**Files:**
- Create: `src/simple_repo_downloader/config.py`
- Test: `tests/test_config.py`

**Step 1: Write failing test for Credentials model**

```python
# tests/test_config.py
import os
from simple_repo_downloader.config import Credentials

def test_credentials_with_direct_tokens():
    creds = Credentials(
        github_token="ghp_test123",
        gitlab_token="glpat_test456"
    )
    assert creds.github_token == "ghp_test123"
    assert creds.gitlab_token == "glpat_test456"


def test_credentials_with_env_vars(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_from_env")
    monkeypatch.setenv("GITLAB_TOKEN", "glpat_from_env")

    creds = Credentials(
        github_token="${GITHUB_TOKEN}",
        gitlab_token="${GITLAB_TOKEN}"
    )
    assert creds.github_token == "ghp_from_env"
    assert creds.gitlab_token == "glpat_from_env"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py::test_credentials_with_direct_tokens -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# src/simple_repo_downloader/config.py
import os
import re
from pathlib import Path
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


def resolve_env_var(value: str) -> str:
    """Resolve ${VAR_NAME} syntax to environment variable value."""
    if not isinstance(value, str):
        return value

    pattern = r'\$\{([^}]+)\}'

    def replace_var(match):
        var_name = match.group(1)
        return os.environ.get(var_name, match.group(0))

    return re.sub(pattern, replace_var, value)


class Credentials(BaseModel):
    """Authentication credentials for platforms."""
    github_token: Optional[str] = None
    gitlab_token: Optional[str] = None

    @field_validator('github_token', 'gitlab_token', mode='before')
    @classmethod
    def resolve_env_vars(cls, v):
        if v is None:
            return v
        return resolve_env_var(v)


class DownloadConfig(BaseModel):
    """Configuration for download behavior."""
    base_directory: Path = Path('./repos')
    max_parallel: int = Field(default=5, ge=1, le=20)
    include_forks: bool = True
    include_private: bool = True


class Target(BaseModel):
    """A platform/username target to download from."""
    platform: Literal['github', 'gitlab']
    username: str
    filters: Dict[str, bool] = Field(default_factory=dict)


class AppConfig(BaseModel):
    """Complete application configuration."""
    credentials: Credentials
    download: DownloadConfig
    targets: List[Target]
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py -v`
Expected: PASS (both tests)

**Step 5: Commit**

```bash
git add src/simple_repo_downloader/config.py tests/test_config.py
git commit -m "feat: add configuration models with env var resolution"
```

---

### Task 3: Add YAML configuration loading

**Files:**
- Modify: `src/simple_repo_downloader/config.py`
- Test: `tests/test_config.py`

**Step 1: Write failing test for YAML loading**

```python
# tests/test_config.py (add to existing file)
import yaml
import tempfile
from pathlib import Path
from simple_repo_downloader.config import AppConfig

def test_load_config_from_yaml():
    config_data = {
        'credentials': {
            'github_token': 'ghp_test',
            'gitlab_token': 'glpat_test'
        },
        'download': {
            'base_directory': './test_repos',
            'max_parallel': 10
        },
        'targets': [
            {
                'platform': 'github',
                'username': 'torvalds',
                'filters': {'forks': False}
            }
        ]
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        config_path = Path(f.name)

    try:
        config = AppConfig.from_yaml(config_path)
        assert config.credentials.github_token == 'ghp_test'
        assert config.download.max_parallel == 10
        assert len(config.targets) == 1
        assert config.targets[0].username == 'torvalds'
    finally:
        config_path.unlink()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py::test_load_config_from_yaml -v`
Expected: FAIL with "AttributeError: 'AppConfig' has no attribute 'from_yaml'"

**Step 3: Write minimal implementation**

```python
# src/simple_repo_downloader/config.py (add to AppConfig class)
import yaml

class AppConfig(BaseModel):
    """Complete application configuration."""
    credentials: Credentials
    download: DownloadConfig
    targets: List[Target]

    @classmethod
    def from_yaml(cls, path: Path) -> "AppConfig":
        """Load configuration from YAML file."""
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        return cls(**data)

    def to_yaml(self, path: Path) -> None:
        """Save configuration to YAML file."""
        with open(path, 'w') as f:
            # Convert to dict, handle Path objects
            data = self.model_dump(mode='python')
            data['download']['base_directory'] = str(data['download']['base_directory'])
            yaml.dump(data, f, default_flow_style=False)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py::test_load_config_from_yaml -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/simple_repo_downloader/config.py tests/test_config.py
git commit -m "feat: add YAML config loading and saving"
```

---

## Phase 2: API Clients

### Task 4: Create base API client

**Files:**
- Create: `src/simple_repo_downloader/api_client.py`
- Test: `tests/test_api_client.py`

**Step 1: Write test for abstract base class structure**

```python
# tests/test_api_client.py
import pytest
from simple_repo_downloader.api_client import PlatformClient
from simple_repo_downloader.models import RepoInfo


def test_platform_client_is_abstract():
    """PlatformClient should be abstract and not instantiable."""
    with pytest.raises(TypeError):
        PlatformClient(token="test", session=None)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_api_client.py::test_platform_client_is_abstract -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# src/simple_repo_downloader/api_client.py
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import aiohttp

from .models import RepoInfo, RateLimitInfo


class PlatformClient(ABC):
    """Abstract base class for platform API clients."""

    def __init__(self, token: Optional[str], session: aiohttp.ClientSession):
        self.token = token
        self.session = session

    @abstractmethod
    async def list_repositories(
        self,
        username: str,
        filters: Dict[str, bool]
    ) -> List[RepoInfo]:
        """Fetch all repos for a user/org with pagination."""
        pass

    @abstractmethod
    async def get_rate_limit(self) -> RateLimitInfo:
        """Get current rate limit status."""
        pass
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_api_client.py::test_platform_client_is_abstract -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/simple_repo_downloader/api_client.py tests/test_api_client.py
git commit -m "feat: add abstract base class for platform API clients"
```

---

### Task 5: Implement GitHub API client

**Files:**
- Modify: `src/simple_repo_downloader/api_client.py`
- Test: `tests/test_api_client.py`

**Step 1: Write failing test for GitHub client**

```python
# tests/test_api_client.py (add to file)
import pytest
from aioresponses import aioresponses
from simple_repo_downloader.api_client import GitHubClient


@pytest.mark.asyncio
async def test_github_list_repositories():
    """Test GitHub client fetches repositories correctly."""

    mock_response = [
        {
            'name': 'linux',
            'owner': {'login': 'torvalds'},
            'clone_url': 'https://github.com/torvalds/linux.git',
            'fork': False,
            'private': False,
            'archived': False,
            'size': 1024000,
            'default_branch': 'master'
        },
        {
            'name': 'subsurface',
            'owner': {'login': 'torvalds'},
            'clone_url': 'https://github.com/torvalds/subsurface.git',
            'fork': False,
            'private': False,
            'archived': False,
            'size': 50000,
            'default_branch': 'main'
        }
    ]

    with aioresponses() as m:
        m.get(
            'https://api.github.com/users/torvalds/repos?per_page=100&page=1',
            payload=mock_response,
            headers={'Link': ''}
        )

        async with aiohttp.ClientSession() as session:
            client = GitHubClient(token='ghp_test', session=session)
            repos = await client.list_repositories('torvalds', {})

            assert len(repos) == 2
            assert repos[0].name == 'linux'
            assert repos[0].username == 'torvalds'
            assert repos[0].platform == 'github'
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_api_client.py::test_github_list_repositories -v`
Expected: FAIL with "ImportError: cannot import name 'GitHubClient'"

**Step 3: Write minimal implementation**

```python
# src/simple_repo_downloader/api_client.py (add to file)
from typing import Any, Dict, List, Optional
import aiohttp

from .models import RepoInfo, RateLimitInfo


class GitHubClient(PlatformClient):
    """GitHub API client."""

    BASE_URL = "https://api.github.com"

    def __init__(self, token: Optional[str], session: aiohttp.ClientSession):
        super().__init__(token, session)
        self.headers = {}
        if token:
            self.headers['Authorization'] = f'token {token}'

    async def list_repositories(
        self,
        username: str,
        filters: Dict[str, bool]
    ) -> List[RepoInfo]:
        """Fetch all repos for a GitHub user/org."""
        repos = []
        page = 1

        while True:
            # Try user endpoint first, fall back to org
            url = f"{self.BASE_URL}/users/{username}/repos"
            params = {'per_page': 100, 'page': page}

            async with self.session.get(url, headers=self.headers, params=params) as response:
                if response.status == 404:
                    # Try org endpoint
                    url = f"{self.BASE_URL}/orgs/{username}/repos"
                    async with self.session.get(url, headers=self.headers, params=params) as org_response:
                        if org_response.status != 200:
                            break
                        data = await org_response.json()
                elif response.status != 200:
                    break
                else:
                    data = await response.json()

                if not data:
                    break

                for item in data:
                    # Apply filters
                    if filters.get('forks') == False and item['fork']:
                        continue
                    if filters.get('archived') == False and item['archived']:
                        continue

                    repo = RepoInfo(
                        platform='github',
                        username=item['owner']['login'],
                        name=item['name'],
                        clone_url=item['clone_url'],
                        is_fork=item['fork'],
                        is_private=item['private'],
                        is_archived=item['archived'],
                        size_kb=item['size'],
                        default_branch=item['default_branch']
                    )
                    repos.append(repo)

                # Check for pagination
                link_header = response.headers.get('Link', '')
                if 'rel="next"' not in link_header:
                    break

                page += 1

        return repos

    async def get_rate_limit(self) -> RateLimitInfo:
        """Get GitHub rate limit status."""
        url = f"{self.BASE_URL}/rate_limit"
        async with self.session.get(url, headers=self.headers) as response:
            data = await response.json()
            core = data['resources']['core']
            return RateLimitInfo(
                remaining=core['remaining'],
                limit=core['limit'],
                reset_timestamp=core['reset']
            )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_api_client.py::test_github_list_repositories -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/simple_repo_downloader/api_client.py tests/test_api_client.py
git commit -m "feat: implement GitHub API client with pagination"
```

---

### Task 6: Implement GitLab API client

**Files:**
- Modify: `src/simple_repo_downloader/api_client.py`
- Test: `tests/test_api_client.py`

**Step 1: Write failing test for GitLab client**

```python
# tests/test_api_client.py (add to file)
@pytest.mark.asyncio
async def test_gitlab_list_repositories():
    """Test GitLab client fetches projects correctly."""

    mock_response = [
        {
            'name': 'gitlab-runner',
            'namespace': {'path': 'gitlab-org'},
            'http_url_to_repo': 'https://gitlab.com/gitlab-org/gitlab-runner.git',
            'forked_from_project': None,
            'visibility': 'public',
            'archived': False,
            'statistics': {'repository_size': 1024000},
            'default_branch': 'main'
        }
    ]

    with aioresponses() as m:
        m.get(
            'https://gitlab.com/api/v4/users/gitlab-org/projects?per_page=100&page=1',
            payload=mock_response,
            headers={'X-Total-Pages': '1'}
        )

        async with aiohttp.ClientSession() as session:
            client = GitLabClient(token='glpat_test', session=session)
            repos = await client.list_repositories('gitlab-org', {})

            assert len(repos) == 1
            assert repos[0].name == 'gitlab-runner'
            assert repos[0].platform == 'gitlab'
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_api_client.py::test_gitlab_list_repositories -v`
Expected: FAIL with "ImportError: cannot import name 'GitLabClient'"

**Step 3: Write minimal implementation**

```python
# src/simple_repo_downloader/api_client.py (add to file)

class GitLabClient(PlatformClient):
    """GitLab API client."""

    def __init__(
        self,
        token: Optional[str],
        session: aiohttp.ClientSession,
        base_url: str = "https://gitlab.com"
    ):
        super().__init__(token, session)
        self.base_url = base_url
        self.headers = {}
        if token:
            self.headers['PRIVATE-TOKEN'] = token

    async def list_repositories(
        self,
        username: str,
        filters: Dict[str, bool]
    ) -> List[RepoInfo]:
        """Fetch all projects for a GitLab user/group."""
        repos = []
        page = 1

        while True:
            # Try user endpoint first, fall back to group
            url = f"{self.base_url}/api/v4/users/{username}/projects"
            params = {'per_page': 100, 'page': page}

            async with self.session.get(url, headers=self.headers, params=params) as response:
                if response.status == 404:
                    # Try group endpoint
                    url = f"{self.base_url}/api/v4/groups/{username}/projects"
                    async with self.session.get(url, headers=self.headers, params=params) as group_response:
                        if group_response.status != 200:
                            break
                        data = await group_response.json()
                        total_pages = int(group_response.headers.get('X-Total-Pages', '1'))
                elif response.status != 200:
                    break
                else:
                    data = await response.json()
                    total_pages = int(response.headers.get('X-Total-Pages', '1'))

                if not data:
                    break

                for item in data:
                    # Apply filters
                    is_fork = item.get('forked_from_project') is not None
                    if filters.get('forks') == False and is_fork:
                        continue
                    if filters.get('archived') == False and item.get('archived', False):
                        continue

                    repo = RepoInfo(
                        platform='gitlab',
                        username=item['namespace']['path'],
                        name=item['name'],
                        clone_url=item['http_url_to_repo'],
                        is_fork=is_fork,
                        is_private=item['visibility'] != 'public',
                        is_archived=item.get('archived', False),
                        size_kb=item.get('statistics', {}).get('repository_size', 0) // 1024,
                        default_branch=item.get('default_branch', 'main')
                    )
                    repos.append(repo)

                # Check if more pages
                if page >= total_pages:
                    break

                page += 1

        return repos

    async def get_rate_limit(self) -> RateLimitInfo:
        """Get GitLab rate limit status."""
        # GitLab doesn't have a dedicated rate limit endpoint
        # Return dummy data for now
        return RateLimitInfo(remaining=600, limit=600, reset_timestamp=0)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_api_client.py::test_gitlab_list_repositories -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/simple_repo_downloader/api_client.py tests/test_api_client.py
git commit -m "feat: implement GitLab API client with pagination"
```

---

## Phase 3: Download Engine

### Task 7: Create download engine structure

**Files:**
- Create: `src/simple_repo_downloader/downloader.py`
- Test: `tests/test_downloader.py`

**Step 1: Write failing test for download engine initialization**

```python
# tests/test_downloader.py
import pytest
from pathlib import Path
from simple_repo_downloader.downloader import DownloadEngine
from simple_repo_downloader.config import DownloadConfig


def test_download_engine_initialization():
    config = DownloadConfig(
        base_directory=Path('./test_repos'),
        max_parallel=3
    )
    engine = DownloadEngine(config)

    assert engine.config == config
    assert engine.semaphore._value == 3
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_downloader.py::test_download_engine_initialization -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# src/simple_repo_downloader/downloader.py
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
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_downloader.py::test_download_engine_initialization -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/simple_repo_downloader/downloader.py tests/test_downloader.py
git commit -m "feat: add download engine structure"
```

---

### Task 8: Implement git clone functionality

**Files:**
- Modify: `src/simple_repo_downloader/downloader.py`
- Test: `tests/test_downloader.py`

**Step 1: Write failing test for clone functionality**

```python
# tests/test_downloader.py (add to file)
import tempfile
import shutil


@pytest.mark.asyncio
async def test_clone_repo_success(tmp_path):
    """Test successful repository clone."""
    config = DownloadConfig(base_directory=tmp_path, max_parallel=1)
    engine = DownloadEngine(config)

    # Use a small public repo for testing
    repo = RepoInfo(
        platform='github',
        username='test-user',
        name='test-repo',
        clone_url='https://github.com/octocat/Hello-World.git',
        is_fork=False,
        is_private=False,
        is_archived=False,
        size_kb=100,
        default_branch='master'
    )

    await engine._clone_repo(repo, None)

    expected_path = tmp_path / 'github' / 'test-user' / 'test-repo'
    assert expected_path.exists()
    assert (expected_path / '.git').exists()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_downloader.py::test_clone_repo_success -v`
Expected: FAIL with "AttributeError: '_clone_repo' not found"

**Step 3: Write minimal implementation**

```python
# src/simple_repo_downloader/downloader.py (add methods to DownloadEngine)

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
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_downloader.py::test_clone_repo_success -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/simple_repo_downloader/downloader.py tests/test_downloader.py
git commit -m "feat: implement git clone functionality"
```

---

### Task 9: Implement worker pool for parallel downloads

**Files:**
- Modify: `src/simple_repo_downloader/downloader.py`
- Test: `tests/test_downloader.py`

**Step 1: Write failing test for parallel downloads**

```python
# tests/test_downloader.py (add to file)
@pytest.mark.asyncio
async def test_download_all_with_multiple_repos(tmp_path):
    """Test downloading multiple repositories in parallel."""
    config = DownloadConfig(base_directory=tmp_path, max_parallel=2)
    engine = DownloadEngine(config)

    repos = [
        RepoInfo(
            platform='github',
            username='octocat',
            name='Hello-World',
            clone_url='https://github.com/octocat/Hello-World.git',
            is_fork=False,
            is_private=False,
            is_archived=False,
            size_kb=100,
            default_branch='master'
        ),
        RepoInfo(
            platform='github',
            username='octocat',
            name='Spoon-Knife',
            clone_url='https://github.com/octocat/Spoon-Knife.git',
            is_fork=False,
            is_private=False,
            is_archived=False,
            size_kb=50,
            default_branch='main'
        )
    ]

    result = await engine.download_all(repos)

    assert len(result.successful) == 2
    assert len(result.issues) == 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_downloader.py::test_download_all_with_multiple_repos -v`
Expected: FAIL with "AttributeError: 'download_all' not found"

**Step 3: Write minimal implementation**

```python
# src/simple_repo_downloader/downloader.py (add to DownloadEngine)
from dataclasses import dataclass


@dataclass
class DownloadResults:
    """Results from a batch download operation."""
    successful: List[DownloadResult]
    issues: List[DownloadIssue]


class DownloadEngine:
    # ... existing code ...

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

                try:
                    async with self.semaphore:
                        await self._clone_repo(repo, callback, token)
                        self.results.append(
                            DownloadResult(repo=repo, success=True)
                        )
                except FileExistsError as e:
                    self.issues.append(
                        DownloadIssue(
                            repo=repo,
                            issue_type=IssueType.CONFLICT,
                            message=str(e),
                            existing_path=self.config.base_directory / repo.platform / repo.username / repo.name
                        )
                    )
                except Exception as e:
                    issue_type = self._classify_error(e)
                    self.issues.append(
                        DownloadIssue(
                            repo=repo,
                            issue_type=issue_type,
                            message=str(e)
                        )
                    )
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
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_downloader.py::test_download_all_with_multiple_repos -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/simple_repo_downloader/downloader.py tests/test_downloader.py
git commit -m "feat: implement parallel download with worker pool"
```

---

## Phase 4: CLI Interface (Basic)

### Task 10: Create basic CLI structure

**Files:**
- Create: `src/simple_repo_downloader/cli.py`
- Test: `tests/test_cli.py`

**Step 1: Write failing test for CLI entry point**

```python
# tests/test_cli.py
from click.testing import CliRunner
from simple_repo_downloader.cli import cli


def test_cli_help():
    """Test CLI help command."""
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert 'repo-dl' in result.output or 'download' in result.output
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli.py::test_cli_help -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# src/simple_repo_downloader/cli.py
import asyncio
import sys
from pathlib import Path
from typing import Optional

import click
import aiohttp

from .config import AppConfig, DownloadConfig, Target, Credentials
from .api_client import GitHubClient, GitLabClient
from .downloader import DownloadEngine


@click.group()
@click.version_option(version='0.1.0')
def cli():
    """Simple Repository Downloader - Download all repos from GitHub/GitLab users."""
    pass


@cli.command()
@click.argument('platform', type=click.Choice(['github', 'gitlab']))
@click.argument('username')
@click.option('--token', envvar='GITHUB_TOKEN', help='Authentication token')
@click.option('--max-parallel', default=5, type=click.IntRange(1, 20), help='Max concurrent downloads')
@click.option('--output-dir', type=click.Path(), default='./repos', help='Output directory')
@click.option('--no-forks', is_flag=True, help='Exclude forked repositories')
@click.option('--config', type=click.Path(exists=True), help='Config file path')
def download(platform, username, token, max_parallel, output_dir, no_forks, config):
    """Download repositories from a platform user/org."""

    if config:
        # Load from config file
        app_config = AppConfig.from_yaml(Path(config))
        asyncio.run(_download_from_config(app_config))
    else:
        # Use CLI arguments
        asyncio.run(_download_from_args(
            platform, username, token, max_parallel, output_dir, no_forks
        ))


async def _download_from_args(
    platform: str,
    username: str,
    token: Optional[str],
    max_parallel: int,
    output_dir: str,
    no_forks: bool
):
    """Execute download from CLI arguments."""
    # Create download config
    download_config = DownloadConfig(
        base_directory=Path(output_dir),
        max_parallel=max_parallel
    )

    # Create filters
    filters = {}
    if no_forks:
        filters['forks'] = False

    # Create appropriate client
    async with aiohttp.ClientSession() as session:
        if platform == 'github':
            client = GitHubClient(token=token, session=session)
        else:
            client = GitLabClient(token=token, session=session)

        # Fetch repositories
        click.echo(f"Fetching repositories for {username}...")
        repos = await client.list_repositories(username, filters)
        click.echo(f"Found {len(repos)} repositories")

        # Download
        engine = DownloadEngine(download_config)
        click.echo(f"Downloading with {max_parallel} parallel workers...")
        results = await engine.download_all(repos, token=token)

        # Report results
        click.echo(f"\n✓ Successfully downloaded: {len(results.successful)}")
        if results.issues:
            click.echo(f"✗ Issues encountered: {len(results.issues)}")
            for issue in results.issues:
                click.echo(f"  - {issue.repo.name}: {issue.message}")


async def _download_from_config(app_config: AppConfig):
    """Execute download from configuration file."""
    async with aiohttp.ClientSession() as session:
        for target in app_config.targets:
            # Get appropriate token
            if target.platform == 'github':
                token = app_config.credentials.github_token
                client = GitHubClient(token=token, session=session)
            else:
                token = app_config.credentials.gitlab_token
                client = GitLabClient(token=token, session=session)

            click.echo(f"Fetching {target.platform} repositories for {target.username}...")
            repos = await client.list_repositories(target.username, target.filters)
            click.echo(f"Found {len(repos)} repositories")

            engine = DownloadEngine(app_config.download)
            results = await engine.download_all(repos, token=token)

            click.echo(f"✓ Downloaded: {len(results.successful)}, Issues: {len(results.issues)}")


def main():
    """Entry point for CLI."""
    cli()


if __name__ == '__main__':
    main()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli.py::test_cli_help -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/simple_repo_downloader/cli.py tests/test_cli.py
git commit -m "feat: add basic CLI with download command"
```

---

## Phase 5: Package Exports & Integration

### Task 11: Update package exports

**Files:**
- Modify: `src/simple_repo_downloader/__init__.py`

**Step 1: Write failing test for package imports**

```python
# tests/test_package.py
def test_package_exports():
    """Test that main classes are exported from package."""
    from simple_repo_downloader import (
        RepoInfo,
        DownloadEngine,
        DownloadConfig,
        AppConfig,
        GitHubClient,
        GitLabClient
    )

    assert RepoInfo is not None
    assert DownloadEngine is not None
    assert DownloadConfig is not None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_package.py::test_package_exports -v`
Expected: FAIL with "ImportError"

**Step 3: Write minimal implementation**

```python
# src/simple_repo_downloader/__init__.py
"""Simple Repository Downloader - A tool for downloading all repos from GitHub/GitLab users."""

__version__ = "0.1.0"

from .models import (
    RepoInfo,
    DownloadResult,
    DownloadIssue,
    IssueType,
    RateLimitInfo,
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

__all__ = [
    "__version__",
    # Models
    "RepoInfo",
    "DownloadResult",
    "DownloadIssue",
    "IssueType",
    "RateLimitInfo",
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
]
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_package.py::test_package_exports -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/simple_repo_downloader/__init__.py tests/test_package.py
git commit -m "feat: export main classes from package"
```

---

## Phase 6: Dashboard (Future Enhancement)

**Note:** The dashboard component using Rich is a complex feature that requires:
- Rich Live layout with multiple panels
- Command shell using aioconsole
- Real-time progress updates
- Interactive command processing

This should be implemented in a separate phase after core functionality is working and tested.

## Phase 7: Error Resolver (Future Enhancement)

**Note:** The interactive error resolver requires:
- Interactive prompts after bulk downloads
- Multiple resolution strategies (pull, re-clone, copy, skip)
- Batch operations
- Session persistence

This should be implemented after dashboard is complete.

---

## Testing Strategy

### Run All Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=simple_repo_downloader --cov-report=html

# Run specific module
pytest tests/test_downloader.py -v
```

### Integration Test

Create an end-to-end test:

```bash
# Test with a real small repository
repo-dl download github octocat --no-forks --max-parallel 2
```

---

## Success Criteria

- ✓ All unit tests pass
- ✓ Can download repos from GitHub
- ✓ Can download repos from GitLab
- ✓ Parallel downloads work correctly
- ✓ Config file loading works
- ✓ CLI commands work
- ✓ Proper error handling and reporting

---

## Next Steps After Core Implementation

1. **Add Dashboard** - Implement Rich-based real-time UI
2. **Add Interactive Resolver** - Implement error resolution workflow
3. **Add Resume Capability** - Session persistence and resume
4. **Add Progress Callbacks** - Detailed progress tracking
5. **Improve Error Handling** - Better error classification and recovery
6. **Add More Tests** - Integration tests, edge cases
7. **Documentation** - API docs, examples, tutorials
8. **CI/CD** - GitHub Actions for testing and releases
9. **PyPI Publishing** - Package and publish to PyPI

---

**Implementation Notes:**

- Each task is atomic and should take 2-5 minutes
- Always write test first (TDD)
- Commit after each passing test
- Run tests frequently
- Keep implementation minimal (YAGNI)
- Don't add features not in the design
- Focus on core functionality first
- Dashboard and advanced features come later
