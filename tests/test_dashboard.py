# tests/test_dashboard.py
from simple_repo_downloader.dashboard import DownloadStatus, RepoStatus
from simple_repo_downloader.models import RepoInfo

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
        state="downloading",
        progress_pct=45,
        error=None
    )

    assert status.repo.name == "linux"
    assert status.state == "downloading"
    assert status.progress_pct == 45
    assert status.error is None
