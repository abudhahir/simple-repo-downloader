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
