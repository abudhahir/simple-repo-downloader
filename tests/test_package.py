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
