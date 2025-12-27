from unittest.mock import AsyncMock, patch

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
