from datetime import datetime
from pathlib import Path
from simple_repo_downloader.models import (
    RepoInfo,
    DownloadResult,
    DownloadIssue,
    RateLimitInfo,
    IssueType,
)


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


def test_download_result_success():
    repo = RepoInfo(
        platform="github",
        username="test",
        name="repo",
        clone_url="https://github.com/test/repo.git",
        is_fork=False,
        is_private=False,
        is_archived=False,
        size_kb=512,
        default_branch="main"
    )
    result = DownloadResult(repo=repo, success=True)
    assert result.success is True
    assert result.error is None


def test_download_result_failure():
    repo = RepoInfo(
        platform="github",
        username="test",
        name="repo",
        clone_url="https://github.com/test/repo.git",
        is_fork=False,
        is_private=False,
        is_archived=False,
        size_kb=512,
        default_branch="main"
    )
    result = DownloadResult(repo=repo, success=False, error="Network error")
    assert result.success is False
    assert result.error == "Network error"


def test_download_issue_with_timestamp():
    repo = RepoInfo(
        platform="github",
        username="test",
        name="repo",
        clone_url="https://github.com/test/repo.git",
        is_fork=False,
        is_private=False,
        is_archived=False,
        size_kb=512,
        default_branch="main"
    )
    before = datetime.now()
    issue = DownloadIssue(
        repo=repo,
        issue_type=IssueType.CONFLICT,
        message="Repository already exists"
    )
    after = datetime.now()

    # Verify timestamp is automatically generated and is a datetime instance
    assert isinstance(issue.timestamp, datetime)
    assert before <= issue.timestamp <= after


def test_download_issue_with_existing_path():
    repo = RepoInfo(
        platform="github",
        username="test",
        name="repo",
        clone_url="https://github.com/test/repo.git",
        is_fork=False,
        is_private=False,
        is_archived=False,
        size_kb=512,
        default_branch="main"
    )
    path = Path("/path/to/repo")
    issue = DownloadIssue(
        repo=repo,
        issue_type=IssueType.FILE_CONFLICT,
        message="File conflict detected",
        existing_path=path
    )
    assert issue.existing_path == path


def test_rate_limit_info():
    rate_limit = RateLimitInfo(
        remaining=4500,
        limit=5000,
        reset_timestamp=1234567890
    )
    assert rate_limit.remaining == 4500
    assert rate_limit.limit == 5000
    assert rate_limit.reset_timestamp == 1234567890


def test_issue_type_enum():
    assert IssueType.CONFLICT.value == "conflict"
    assert IssueType.FILE_CONFLICT.value == "file_conflict"
    assert IssueType.NETWORK_ERROR.value == "network"
    assert IssueType.AUTH_ERROR.value == "auth"
    assert IssueType.GIT_ERROR.value == "git"
    assert IssueType.RATE_LIMIT.value == "rate_limit"
