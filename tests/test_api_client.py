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

    user_response = {'login': 'different-user'}  # Not the same as torvalds
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
        # Mock /user endpoint (authenticated user check)
        m.get(
            'https://api.github.com/user',
            payload=user_response
        )
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
async def test_github_api_error_with_401():
    """Test GitHub client raises exception on 401 Unauthorized."""
    from simple_repo_downloader.api_client import APIError

    user_response = {'login': 'different-user'}
    error_response = {
        'message': 'Bad credentials',
        'documentation_url': 'https://docs.github.com/rest'
    }

    with aioresponses() as m:
        m.get(
            'https://api.github.com/user',
            payload=user_response
        )
        m.get(
            'https://api.github.com/users/testuser/repos?per_page=100&page=1',
            status=401,
            payload=error_response
        )

        async with aiohttp.ClientSession() as session:
            client = GitHubClient(token='invalid_token', session=session)

            with pytest.raises(APIError) as exc_info:
                await client.list_repositories('testuser', {})

            assert exc_info.value.status_code == 401
            assert 'Bad credentials' in str(exc_info.value)
            assert exc_info.value.platform == 'github'


@pytest.mark.asyncio
async def test_github_api_error_with_403():
    """Test GitHub client raises exception on 403 Forbidden (rate limit)."""
    from simple_repo_downloader.api_client import APIError

    user_response = {'login': 'different-user'}
    error_response = {
        'message': 'API rate limit exceeded',
        'documentation_url': 'https://docs.github.com/rest/overview/resources-in-the-rest-api#rate-limiting'
    }

    with aioresponses() as m:
        m.get(
            'https://api.github.com/user',
            payload=user_response
        )
        m.get(
            'https://api.github.com/users/testuser/repos?per_page=100&page=1',
            status=403,
            payload=error_response
        )

        async with aiohttp.ClientSession() as session:
            client = GitHubClient(token='ghp_test', session=session)

            with pytest.raises(APIError) as exc_info:
                await client.list_repositories('testuser', {})

            assert exc_info.value.status_code == 403
            assert 'rate limit' in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_github_authenticated_user_repos_includes_private():
    """Test GitHub client uses /user/repos when token is present to include private repos."""

    # Mock /user endpoint to identify authenticated user
    user_response = {'login': 'testuser'}

    # Mock response with both public and private repos
    repos_response = [
        {
            'name': 'public-repo',
            'owner': {'login': 'testuser'},
            'clone_url': 'https://github.com/testuser/public-repo.git',
            'fork': False,
            'private': False,
            'archived': False,
            'size': 1000,
            'default_branch': 'main'
        },
        {
            'name': 'private-repo',
            'owner': {'login': 'testuser'},
            'clone_url': 'https://github.com/testuser/private-repo.git',
            'fork': False,
            'private': True,
            'archived': False,
            'size': 2000,
            'default_branch': 'main'
        }
    ]

    with aioresponses() as m:
        # First call to /user to get authenticated username
        m.get(
            'https://api.github.com/user',
            payload=user_response
        )
        # Should use /user/repos for authenticated user
        m.get(
            'https://api.github.com/user/repos?per_page=100&page=1&affiliation=owner',
            payload=repos_response,
            headers={'Link': ''}
        )

        async with aiohttp.ClientSession() as session:
            client = GitHubClient(token='ghp_test', session=session)
            repos = await client.list_repositories('testuser', {})

            assert len(repos) == 2
            assert repos[0].name == 'public-repo'
            assert repos[0].is_private == False
            assert repos[1].name == 'private-repo'
            assert repos[1].is_private == True


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
