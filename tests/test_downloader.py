import pytest
from pathlib import Path
import tempfile
import shutil
from simple_repo_downloader.downloader import DownloadEngine
from simple_repo_downloader.config import DownloadConfig
from simple_repo_downloader.models import RepoInfo


def test_download_engine_initialization():
    config = DownloadConfig(
        base_directory=Path('./test_repos'),
        max_parallel=3
    )
    engine = DownloadEngine(config)

    assert engine.config == config
    assert engine.semaphore._value == 3


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
