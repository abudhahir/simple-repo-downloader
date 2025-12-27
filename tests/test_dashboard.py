# tests/test_dashboard.py
from simple_repo_downloader.dashboard import DownloadStatus, RepoStatus
from simple_repo_downloader.models import RepoInfo, StateEnum

def test_repo_status_creation():
    repo = RepoInfo(
        platform="github",
        username="torvalds",
        name="linux",
        clone_url="https://github.com/torvalds/linux.git",
        is_fork=False,
        is_private=False,
        is_archived=False,
        size_kb=2048000,
        default_branch="master"
    )

    status = RepoStatus(
        repo=repo,
        state=StateEnum.DOWNLOADING,
        progress_pct=45,
        error=None
    )

    assert status.repo.name == "linux"
    assert status.state == StateEnum.DOWNLOADING
    assert status.progress_pct == 45
    assert status.error is None


def test_download_status_counts():
    """Test all state count properties including paused and skipped."""
    repos = [
        RepoInfo(
            platform="github",
            username="user",
            name=f"repo{i}",
            clone_url=f"https://github.com/user/repo{i}.git",
            is_fork=False,
            is_private=False,
            is_archived=False,
            size_kb=1000,
            default_branch="main"
        )
        for i in range(6)
    ]

    status = DownloadStatus()
    status.repos["repo0"] = RepoStatus(repo=repos[0], state=StateEnum.QUEUED)
    status.repos["repo1"] = RepoStatus(repo=repos[1], state=StateEnum.DOWNLOADING)
    status.repos["repo2"] = RepoStatus(repo=repos[2], state=StateEnum.COMPLETED)
    status.repos["repo3"] = RepoStatus(repo=repos[3], state=StateEnum.FAILED)
    status.repos["repo4"] = RepoStatus(repo=repos[4], state=StateEnum.PAUSED)
    status.repos["repo5"] = RepoStatus(repo=repos[5], state=StateEnum.SKIPPED)

    assert status.queued_count == 1
    assert status.downloading_count == 1
    assert status.completed_count == 1
    assert status.failed_count == 1
    assert status.paused_count == 1
    assert status.skipped_count == 1


def test_download_status_add_event():
    status = DownloadStatus()
    status.add_event("Started download")

    assert len(status.events) == 1
    assert "Started download" in status.events[0]
    assert "]" in status.events[0]  # Has timestamp


def test_build_repo_table():
    from simple_repo_downloader.dashboard import Dashboard, DownloadStatus, RepoStatus
    from simple_repo_downloader.models import RepoInfo, StateEnum
    from rich.table import Table

    status = DownloadStatus()
    repo = RepoInfo(
        platform="github",
        username="torvalds",
        name="linux",
        clone_url="https://github.com/torvalds/linux.git",
        is_fork=False,
        is_private=False,
        is_archived=False,
        size_kb=2048000,
        default_branch="master"
    )
    status.repos["github/torvalds/linux"] = RepoStatus(
        repo=repo,
        state=StateEnum.DOWNLOADING,
        progress_pct=45
    )

    dashboard = Dashboard()
    table = dashboard._build_repo_table(status)

    assert isinstance(table, Table)
    assert table.row_count == 1


def test_build_summary_panel():
    from simple_repo_downloader.dashboard import Dashboard, DownloadStatus
    from rich.panel import Panel

    status = DownloadStatus()
    dashboard = Dashboard()
    panel = dashboard._build_summary_panel(status)

    assert isinstance(panel, Panel)


def test_build_event_log_panel():
    from simple_repo_downloader.dashboard import Dashboard, DownloadStatus
    from rich.panel import Panel

    status = DownloadStatus()
    status.add_event("Started cloning github/torvalds/linux")
    status.add_event("Completed github/torvalds/subsurface")

    dashboard = Dashboard()
    panel = dashboard._build_event_log_panel(status, max_events=10)

    assert isinstance(panel, Panel)


def test_parse_command():
    from simple_repo_downloader.dashboard import Dashboard

    dashboard = Dashboard()

    # Test pause command
    cmd, args = dashboard._parse_command("pause github/torvalds/linux")
    assert cmd == "pause"
    assert args == ["github/torvalds/linux"]

    # Test set command
    cmd, args = dashboard._parse_command("set max-parallel 10")
    assert cmd == "set"
    assert args == ["max-parallel", "10"]

    # Test help
    cmd, args = dashboard._parse_command("help")
    assert cmd == "help"
    assert args == []


import pytest

@pytest.mark.asyncio
async def test_execute_help_command():
    from simple_repo_downloader.dashboard import Dashboard, DownloadStatus

    status = DownloadStatus()
    dashboard = Dashboard()

    result = await dashboard._execute_command("help", [], status)

    assert result is not None
    assert "pause" in result.lower()
    assert "resume" in result.lower()


@pytest.mark.asyncio
async def test_execute_pause_command():
    from simple_repo_downloader.dashboard import Dashboard, DownloadStatus, RepoStatus
    from simple_repo_downloader.models import RepoInfo, StateEnum

    status = DownloadStatus()
    repo = RepoInfo(
        platform="github", username="user", name="repo",
        clone_url="url", is_fork=False, is_private=False,
        is_archived=False, size_kb=1024, default_branch="main"
    )
    status.repos["github/user/repo"] = RepoStatus(repo=repo, state=StateEnum.DOWNLOADING)

    dashboard = Dashboard()
    result = await dashboard._execute_command("pause", ["github/user/repo"], status)

    assert "Paused" in result
    assert status.repos["github/user/repo"].state == StateEnum.PAUSED
