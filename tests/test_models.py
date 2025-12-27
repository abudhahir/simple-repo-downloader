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
