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


@pytest.mark.asyncio
async def test_download_with_status_callback():
    from simple_repo_downloader.downloader import DownloadEngine
    from simple_repo_downloader.config import DownloadConfig
    from simple_repo_downloader.models import RepoInfo
    from pathlib import Path
    import tempfile

    status_updates = []

    async def status_callback(repo, state, progress):
        status_updates.append((repo.name, state, progress))

    with tempfile.TemporaryDirectory() as tmpdir:
        config = DownloadConfig(base_directory=Path(tmpdir), max_parallel=1)
        engine = DownloadEngine(config, status_callback=status_callback)

        repos = [
            RepoInfo(
                platform="github",
                username="octocat",
                name="Hello-World",
                clone_url="https://github.com/octocat/Hello-World.git",
                is_fork=False,
                is_private=False,
                is_archived=False,
                size_kb=100,
                default_branch="master"
            )
        ]

        results = await engine.download_all(repos)

        # Should have received status updates
        assert len(status_updates) > 0
        # Should have downloading and completed states
        states = [update[1] for update in status_updates]
        assert "downloading" in states and "completed" in states
