# tests/test_dashboard_integration.py
import pytest
from simple_repo_downloader.dashboard import Dashboard, DownloadStatus, RepoStatus
from simple_repo_downloader.models import RepoInfo, StateEnum

NUM_TEST_REPOS = 3

@pytest.mark.asyncio
async def test_dashboard_basic_commands():
    """Test basic dashboard commands (status and pause)."""
    status = DownloadStatus()

    # Add test repos
    for i in range(NUM_TEST_REPOS):
        repo = RepoInfo(
            platform="github",
            username="user",
            name=f"repo{i}",
            clone_url=f"https://github.com/user/repo{i}.git",
            is_fork=False,
            is_private=False,
            is_archived=False,
            size_kb=1024,
            default_branch="main"
        )
        status.repos[f"github/user/repo{i}"] = RepoStatus(repo=repo, state=StateEnum.QUEUED)

    # Verify initial states
    for i in range(NUM_TEST_REPOS):
        assert status.repos[f"github/user/repo{i}"].state == StateEnum.QUEUED

    # Simulate download progress
    dashboard = Dashboard()

    # Test command execution
    result = await dashboard.execute_command("status", [], status)
    assert "Queued: 3" in result

    # Test pause
    result = await dashboard.execute_command("pause", ["github/user/repo0"], status)
    assert "Paused" in result
    assert status.repos["github/user/repo0"].state == StateEnum.PAUSED

    # Test events
    status.add_event("Test event")
    assert len(status.events) == 1
