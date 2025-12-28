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
async def test_check_existing_repo_scenarios(tmp_path):
    """Test various git status scenarios for existing repos."""
    import subprocess
    from simple_repo_downloader.models import StateEnum

    config = DownloadConfig(base_directory=tmp_path, max_parallel=1)
    engine = DownloadEngine(config)

    # Scenario 1: Repo doesn't exist - should return (None, None)
    repo_new = RepoInfo(
        platform='github',
        username='test',
        name='new-repo',
        clone_url='https://github.com/test/new-repo.git',
        is_fork=False,
        is_private=False,
        is_archived=False,
        size_kb=100,
        default_branch='main'
    )
    state, message = await engine._check_existing_repo(repo_new)
    assert state is None
    assert message is None

    # Scenario 2: Directory exists but not a git repo - should return FAILED
    non_git_path = tmp_path / 'github' / 'test' / 'non-git'
    non_git_path.mkdir(parents=True)

    repo_non_git = RepoInfo(
        platform='github',
        username='test',
        name='non-git',
        clone_url='https://github.com/test/non-git.git',
        is_fork=False,
        is_private=False,
        is_archived=False,
        size_kb=100,
        default_branch='main'
    )
    state, message = await engine._check_existing_repo(repo_non_git)
    assert state == StateEnum.FAILED
    assert 'not a git repo' in message

    # Scenario 3: Valid git repo, up to date
    # Create a small test repo
    git_repo_path = tmp_path / 'github' / 'test' / 'existing-repo'
    git_repo_path.mkdir(parents=True)

    # Initialize git repo
    subprocess.run(['git', 'init'], cwd=git_repo_path, check=True, capture_output=True)
    subprocess.run(['git', 'config', 'user.email', 'test@test.com'], cwd=git_repo_path, check=True, capture_output=True)
    subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=git_repo_path, check=True, capture_output=True)

    # Create initial commit
    (git_repo_path / 'README.md').write_text('# Test Repo')
    subprocess.run(['git', 'add', '.'], cwd=git_repo_path, check=True, capture_output=True)
    subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=git_repo_path, check=True, capture_output=True)

    # Note: Without a remote, git fetch will fail, so this will likely return UP_TO_DATE or FAILED
    repo_existing = RepoInfo(
        platform='github',
        username='test',
        name='existing-repo',
        clone_url='https://github.com/test/existing-repo.git',
        is_fork=False,
        is_private=False,
        is_archived=False,
        size_kb=100,
        default_branch='main'
    )
    state, message = await engine._check_existing_repo(repo_existing)
    # Without upstream, should return UP_TO_DATE with "No upstream branch" message
    assert state == StateEnum.UP_TO_DATE
    assert 'upstream' in message.lower() or 'up to date' in message.lower()


@pytest.mark.asyncio
async def test_download_with_status_callback():
    from simple_repo_downloader.downloader import DownloadEngine
    from simple_repo_downloader.config import DownloadConfig
    from simple_repo_downloader.models import RepoInfo
    from pathlib import Path
    import tempfile

    status_updates = []

    async def status_callback(repo, state, progress, error):
        status_updates.append((repo.name, state, progress, error))

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

        # Verify download was successful
        assert len(results.successful) == 1
        assert len(results.issues) == 0

        # Should have received status updates
        assert len(status_updates) > 0
        # Should have downloading and completed states
        states = [update[1] for update in status_updates]
        assert "downloading" in states and "completed" in states
