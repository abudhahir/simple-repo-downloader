import asyncio
from datetime import datetime
from pathlib import Path

import aiohttp
import click

from .api_client import GitHubClient, GitLabClient
from .config import AppConfig, DownloadConfig
from .downloader import DownloadEngine
from .progress import ProgressPrinter


@click.group()
@click.version_option(version='0.1.0')
def cli():
    """Simple Repository Downloader - Download all repos from GitHub/GitLab users."""
    pass


@cli.command()
@click.argument('platform', type=click.Choice(['github', 'gitlab']))
@click.argument('username')
@click.option('--token', envvar='GITHUB_TOKEN', help='Authentication token')
@click.option('--max-parallel', default=5, type=click.IntRange(1, 20), help='Max concurrent downloads')
@click.option('--output-dir', type=click.Path(), default='./repos', help='Output directory')
@click.option('--no-forks', is_flag=True, help='Exclude forked repositories')
@click.option('--config', type=click.Path(exists=True), help='Config file path')
@click.option('--headless', is_flag=True, help='Run without interactive dashboard')
@click.option('--verbose', is_flag=True, help='Show verbose output')
def download(platform, username, token, max_parallel, output_dir, no_forks, config, headless, verbose):
    """Download repositories from a platform user/org."""

    if config:
        # Load from config file
        app_config = AppConfig.from_yaml(Path(config))
        asyncio.run(_download_from_config(app_config))
    else:
        # Use CLI arguments
        asyncio.run(_download_from_args(
            platform, username, token, max_parallel, output_dir, no_forks, headless, verbose
        ))


async def _download_from_args(
    platform: str,
    username: str,
    token: str | None,
    max_parallel: int,
    output_dir: str,
    no_forks: bool,
    headless: bool,
    verbose: bool
):
    """Execute download from CLI arguments."""
    # Create download config
    download_config = DownloadConfig(
        base_directory=Path(output_dir),
        max_parallel=max_parallel
    )

    # Create filters
    filters = {}
    if no_forks:
        filters['forks'] = False

    # Create appropriate client
    async with aiohttp.ClientSession() as session:
        if platform == 'github':
            client = GitHubClient(token=token, session=session)
        else:
            client = GitLabClient(token=token, session=session)

        # Fetch repositories
        click.echo(f"Fetching repositories for {username}...")
        repos = await client.list_repositories(username, filters)
        click.echo(f"Found {len(repos)} repositories")

        # Handle empty repository list
        if not repos:
            click.echo("No repositories to download. Exiting.")
            return

        # Create log file path
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        log_dir = Path.home() / ".simple-repo-downloader" / "logs"
        log_file = log_dir / f"download-{timestamp}.log"

        # Create progress printer
        printer = ProgressPrinter(log_file=log_file)
        printer.print_start(repos, max_parallel)

        # Create status tracker
        from .dashboard import DownloadStatus, RepoStatus
        from .models import StateEnum
        status = DownloadStatus()
        for repo in repos:
            repo_id = f"{repo.platform}/{repo.username}/{repo.name}"
            status.repos[repo_id] = RepoStatus(repo=repo, state=StateEnum.QUEUED)

        # Track current repo index
        repo_counter = [0]  # Use list for mutable counter in closure

        # Create callback
        async def status_callback(repo, state, progress, error=None):
            repo_id = f"{repo.platform}/{repo.username}/{repo.name}"
            if repo_id in status.repos:
                # Update status
                state_enum = getattr(StateEnum, state.upper(), StateEnum.QUEUED)
                status.repos[repo_id].state = state_enum
                status.repos[repo_id].progress_pct = progress

                # Print update for terminal states only
                if state_enum in [StateEnum.COMPLETED, StateEnum.FAILED, StateEnum.UPDATED,
                                 StateEnum.UP_TO_DATE, StateEnum.UNCOMMITTED_CHANGES, StateEnum.AHEAD]:
                    repo_counter[0] += 1
                    message = error if error else "Cloned successfully"
                    printer.print_repo_update(
                        current=repo_counter[0],
                        total=len(repos),
                        repo=repo,
                        state=state_enum,
                        message=message
                    )

        # Create engine with callback
        engine = DownloadEngine(download_config, status_callback=status_callback)

        # Run download
        await engine.download_all(repos, token=token)

        # Print summary
        printer.print_summary(status)

        if verbose:
            click.echo(f"\nLog saved to: {log_file}")


async def _download_from_config(app_config: AppConfig):
    """Execute download from configuration file."""
    async with aiohttp.ClientSession() as session:
        for target in app_config.targets:
            # Get appropriate token
            if target.platform == 'github':
                token = app_config.credentials.github_token
                client = GitHubClient(token=token, session=session)
            else:
                token = app_config.credentials.gitlab_token
                client = GitLabClient(token=token, session=session)

            click.echo(f"Fetching {target.platform} repositories for {target.username}...")
            repos = await client.list_repositories(target.username, target.filters)
            click.echo(f"Found {len(repos)} repositories")


            # Handle empty repository list
            if not repos:
                click.echo("No repositories to download. Skipping.")
                continue

            engine = DownloadEngine(app_config.download)
            results = await engine.download_all(repos, token=token)

            click.echo(f"✓ Downloaded: {len(results.successful)}, Issues: {len(results.issues)}")


def main():
    """Entry point for CLI."""
    cli()


if __name__ == '__main__':
    main()
