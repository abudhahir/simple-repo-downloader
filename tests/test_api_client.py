import pytest
import aiohttp
from aioresponses import aioresponses
from simple_repo_downloader.api_client import PlatformClient, GitHubClient, GitLabClient
from simple_repo_downloader.models import RepoInfo


def test_platform_client_is_abstract():
    """PlatformClient should be abstract and not instantiable."""
    with pytest.raises(TypeError):
        PlatformClient(token="test", session=None)


@pytest.mark.asyncio
async def test_github_list_repositories():
    """Test GitHub client fetches repositories correctly."""

    mock_response = [
        {
            'name': 'linux',
            'owner': {'login': 'torvalds'},
            'clone_url': 'https://github.com/torvalds/linux.git',
            'fork': False,
            'private': False,
            'archived': False,
            'size': 1024000,
            'default_branch': 'master'
        },
        {
            'name': 'subsurface',
            'owner': {'login': 'torvalds'},
            'clone_url': 'https://github.com/torvalds/subsurface.git',
            'fork': False,
            'private': False,
            'archived': False,
            'size': 50000,
            'default_branch': 'main'
        }
    ]

    with aioresponses() as m:
        m.get(
            'https://api.github.com/users/torvalds/repos?per_page=100&page=1',
            payload=mock_response,
            headers={'Link': ''}
        )

        async with aiohttp.ClientSession() as session:
            client = GitHubClient(token='ghp_test', session=session)
            repos = await client.list_repositories('torvalds', {})

            assert len(repos) == 2
            assert repos[0].name == 'linux'
            assert repos[0].username == 'torvalds'
            assert repos[0].platform == 'github'


@pytest.mark.asyncio
async def test_gitlab_list_repositories():
    """Test GitLab client fetches projects correctly."""

    mock_response = [
        {
            'name': 'gitlab-runner',
            'namespace': {'path': 'gitlab-org'},
            'http_url_to_repo': 'https://gitlab.com/gitlab-org/gitlab-runner.git',
            'forked_from_project': None,
            'visibility': 'public',
            'archived': False,
            'statistics': {'repository_size': 1024000},
            'default_branch': 'main'
        }
    ]

    with aioresponses() as m:
        m.get(
            'https://gitlab.com/api/v4/users/gitlab-org/projects?per_page=100&page=1',
            payload=mock_response,
            headers={'X-Total-Pages': '1'}
        )

        async with aiohttp.ClientSession() as session:
            client = GitLabClient(token='glpat_test', session=session)
            repos = await client.list_repositories('gitlab-org', {})

            assert len(repos) == 1
            assert repos[0].name == 'gitlab-runner'
            assert repos[0].platform == 'gitlab'
