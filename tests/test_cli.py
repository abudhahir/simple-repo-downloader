from click.testing import CliRunner
from simple_repo_downloader.cli import cli


def test_cli_help():
    """Test CLI help command."""
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert 'repo-dl' in result.output or 'download' in result.output
