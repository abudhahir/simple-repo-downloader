import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from click.testing import CliRunner

from simple_repo_downloader.cli import cli


def test_cli_help():
    """Test CLI help command."""
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert 'repo-dl' in result.output or 'download' in result.output


def test_cli_empty_repos_list():
    """Test that CLI handles empty repository list gracefully."""
    runner = CliRunner()

    # Mock the async function to return empty list
    async def mock_list_repositories(*args, **kwargs):
        return []

    with patch('simple_repo_downloader.cli.GitHubClient') as MockClient:
        mock_client = AsyncMock()
        mock_client.list_repositories = mock_list_repositories
        MockClient.return_value = mock_client

        # Test with headless mode
        result = runner.invoke(cli, [
            'download', 'github', 'testuser',
            '--token', 'fake_token',
            '--headless'
        ])

        # Should exit gracefully with message
        assert result.exit_code == 0
        assert 'Found 0 repositories' in result.output
        assert 'No repositories to download. Exiting.' in result.output

        # Test without headless mode (dashboard mode)
        result = runner.invoke(cli, [
            'download', 'github', 'testuser',
            '--token', 'fake_token'
        ])

        # Should exit gracefully with message (no dashboard should start)
        assert result.exit_code == 0
        assert 'Found 0 repositories' in result.output
        assert 'No repositories to download. Exiting.' in result.output


@pytest.mark.asyncio
async def test_cli_uses_progress_printer(tmp_path, monkeypatch):
    """Test CLI uses ProgressPrinter instead of Dashboard."""
    from simple_repo_downloader.cli import _download_from_args
    from simple_repo_downloader.models import RepoInfo
    from unittest.mock import AsyncMock, MagicMock, patch

    # Create a mock repository
    mock_repo = RepoInfo(
        platform='github',
        username='test',
        name='test-repo',
        clone_url='https://github.com/test/test-repo.git',
        is_fork=False,
        is_private=False,
        is_archived=False,
        size_kb=100,
        default_branch='main'
    )

    # Mock the API client
    mock_repos = [mock_repo]
    mock_client = AsyncMock()
    mock_client.list_repositories = AsyncMock(return_value=mock_repos)

    with patch('simple_repo_downloader.cli.aiohttp.ClientSession'):
        with patch('simple_repo_downloader.cli.GitHubClient', return_value=mock_client):
            with patch('simple_repo_downloader.cli.ProgressPrinter') as mock_printer:
                with patch('simple_repo_downloader.cli.DownloadEngine') as mock_engine:
                    mock_printer_instance = MagicMock()
                    mock_printer.return_value = mock_printer_instance

                    # Mock the engine
                    mock_engine_instance = AsyncMock()
                    mock_engine_instance.download_all = AsyncMock()
                    mock_engine.return_value = mock_engine_instance

                    # Run download
                    await _download_from_args(
                        platform='github',
                        username='test',
                        token='fake-token',
                        max_parallel=5,
                        output_dir=str(tmp_path),
                        no_forks=False,
                        headless=False,
                        verbose=False
                    )

                    # Verify ProgressPrinter was created
                    mock_printer.assert_called_once()


@pytest.mark.asyncio
async def test_cli_callback_behavior(tmp_path, monkeypatch):
    """Test CLI callback increments counter and calls printer for terminal states."""
    from simple_repo_downloader.cli import _download_from_args
    from simple_repo_downloader.models import RepoInfo
    from unittest.mock import AsyncMock, MagicMock, patch, call

    # Create mock repos
    mock_repos = [
        RepoInfo(
            platform='github',
            username='test',
            name='repo1',
            clone_url='https://github.com/test/repo1.git',
            is_fork=False,
            is_private=False,
            is_archived=False,
            size_kb=100,
            default_branch='main'
        )
    ]

    mock_client = AsyncMock()
    mock_client.list_repositories = AsyncMock(return_value=mock_repos)

    with patch('simple_repo_downloader.cli.aiohttp.ClientSession'):
        with patch('simple_repo_downloader.cli.GitHubClient', return_value=mock_client):
            with patch('simple_repo_downloader.cli.ProgressPrinter') as mock_printer_class:
                with patch('simple_repo_downloader.cli.DownloadEngine') as mock_engine_class:
                    # Setup mocks
                    mock_printer = MagicMock()
                    mock_printer_class.return_value = mock_printer

                    mock_engine = AsyncMock()
                    mock_engine_class.return_value = mock_engine

                    # Capture the callback
                    captured_callback = None
                    def capture_callback(config, status_callback=None):
                        nonlocal captured_callback
                        captured_callback = status_callback
                        return mock_engine
                    mock_engine_class.side_effect = capture_callback

                    # Mock download_all to return empty results
                    from simple_repo_downloader.downloader import DownloadResults
                    mock_engine.download_all = AsyncMock(return_value=DownloadResults(successful=[], issues=[]))

                    # Run download
                    await _download_from_args(
                        platform='github',
                        username='test',
                        token='fake-token',
                        max_parallel=5,
                        output_dir=str(tmp_path),
                        no_forks=False,
                        headless=False,
                        verbose=False
                    )

                    # Verify callback was created
                    assert captured_callback is not None

                    # Simulate callback for completed state
                    await captured_callback(mock_repos[0], "completed", 100, None)

                    # Verify print_repo_update was called
                    assert mock_printer.print_repo_update.called
                    call_args = mock_printer.print_repo_update.call_args
                    assert call_args.kwargs['current'] == 1
                    assert call_args.kwargs['total'] == 1
                    assert call_args.kwargs['state'].value == 'completed'
