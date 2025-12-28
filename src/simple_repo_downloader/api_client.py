from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import aiohttp

from .models import RepoInfo, RateLimitInfo


class APIError(Exception):
    """Exception raised when API request fails."""

    def __init__(
        self,
        message: str,
        status_code: int,
        platform: str,
        response_body: Optional[Dict] = None
    ):
        self.message = message
        self.status_code = status_code
        self.platform = platform
        self.response_body = response_body or {}
        super().__init__(self.message)

    def __str__(self):
        return f"{self.platform} API error ({self.status_code}): {self.message}"


class PlatformClient(ABC):
    """Abstract base class for platform API clients."""

    def __init__(self, token: Optional[str], session: aiohttp.ClientSession):
        self.token = token
        self.session = session

    @abstractmethod
    async def list_repositories(
        self,
        username: str,
        filters: Dict[str, bool]
    ) -> List[RepoInfo]:
        """Fetch all repos for a user/org with pagination."""
        pass

    @abstractmethod
    async def get_rate_limit(self) -> RateLimitInfo:
        """Get current rate limit status."""
        pass


class GitHubClient(PlatformClient):
    """GitHub API client."""

    BASE_URL = "https://api.github.com"

    def __init__(self, token: Optional[str], session: aiohttp.ClientSession):
        super().__init__(token, session)
        self.headers = {}
        if token:
            self.headers['Authorization'] = f'token {token}'

    async def list_repositories(
        self,
        username: str,
        filters: Dict[str, bool]
    ) -> List[RepoInfo]:
        """Fetch all repos for a GitHub user/org."""
        repos = []
        page = 1

        # Check if we're fetching authenticated user's repos (to include private)
        is_authenticated_user = False
        if self.token:
            async with self.session.get(f"{self.BASE_URL}/user", headers=self.headers) as user_response:
                if user_response.status == 200:
                    user_data = await user_response.json()
                    is_authenticated_user = user_data.get('login', '').lower() == username.lower()

        while True:
            # Use /user/repos for authenticated user to get private repos
            if is_authenticated_user:
                url = f"{self.BASE_URL}/user/repos"
                params = {'per_page': 100, 'page': page, 'affiliation': 'owner'}
            else:
                # Try user endpoint first, fall back to org
                url = f"{self.BASE_URL}/users/{username}/repos"
                params = {'per_page': 100, 'page': page}

            async with self.session.get(url, headers=self.headers, params=params) as response:
                if response.status == 404:
                    # Try org endpoint
                    url = f"{self.BASE_URL}/orgs/{username}/repos"
                    async with self.session.get(url, headers=self.headers, params=params) as org_response:
                        if org_response.status != 200:
                            error_body = await org_response.json() if org_response.content_type == 'application/json' else {}
                            error_msg = error_body.get('message', f'HTTP {org_response.status}')
                            raise APIError(
                                message=error_msg,
                                status_code=org_response.status,
                                platform='github',
                                response_body=error_body
                            )
                        data = await org_response.json()
                elif response.status != 200:
                    error_body = await response.json() if response.content_type == 'application/json' else {}
                    error_msg = error_body.get('message', f'HTTP {response.status}')
                    raise APIError(
                        message=error_msg,
                        status_code=response.status,
                        platform='github',
                        response_body=error_body
                    )
                else:
                    data = await response.json()

                if not data:
                    break

                for item in data:
                    # Apply filters
                    if filters.get('forks') == False and item['fork']:
                        continue
                    if filters.get('archived') == False and item['archived']:
                        continue

                    repo = RepoInfo(
                        platform='github',
                        username=item['owner']['login'],
                        name=item['name'],
                        clone_url=item['clone_url'],
                        is_fork=item['fork'],
                        is_private=item['private'],
                        is_archived=item['archived'],
                        size_kb=item['size'],
                        default_branch=item['default_branch']
                    )
                    repos.append(repo)

                # Check for pagination
                link_header = response.headers.get('Link', '')
                if 'rel="next"' not in link_header:
                    break

                page += 1

        return repos

    async def get_rate_limit(self) -> RateLimitInfo:
        """Get GitHub rate limit status."""
        url = f"{self.BASE_URL}/rate_limit"
        async with self.session.get(url, headers=self.headers) as response:
            data = await response.json()
            core = data['resources']['core']
            return RateLimitInfo(
                remaining=core['remaining'],
                limit=core['limit'],
                reset_timestamp=core['reset']
            )


class GitLabClient(PlatformClient):
    """GitLab API client."""

    def __init__(
        self,
        token: Optional[str],
        session: aiohttp.ClientSession,
        base_url: str = "https://gitlab.com"
    ):
        super().__init__(token, session)
        self.base_url = base_url
        self.headers = {}
        if token:
            self.headers['PRIVATE-TOKEN'] = token

    async def list_repositories(
        self,
        username: str,
        filters: Dict[str, bool]
    ) -> List[RepoInfo]:
        """Fetch all projects for a GitLab user/group."""
        repos = []
        page = 1

        while True:
            # Try user endpoint first, fall back to group
            url = f"{self.base_url}/api/v4/users/{username}/projects"
            params = {'per_page': 100, 'page': page}

            async with self.session.get(url, headers=self.headers, params=params) as response:
                if response.status == 404:
                    # Try group endpoint
                    url = f"{self.base_url}/api/v4/groups/{username}/projects"
                    async with self.session.get(url, headers=self.headers, params=params) as group_response:
                        if group_response.status != 200:
                            break
                        data = await group_response.json()
                        total_pages = int(group_response.headers.get('X-Total-Pages', '1'))
                elif response.status != 200:
                    break
                else:
                    data = await response.json()
                    total_pages = int(response.headers.get('X-Total-Pages', '1'))

                if not data:
                    break

                for item in data:
                    # Apply filters
                    is_fork = item.get('forked_from_project') is not None
                    if filters.get('forks') == False and is_fork:
                        continue
                    if filters.get('archived') == False and item.get('archived', False):
                        continue

                    repo = RepoInfo(
                        platform='gitlab',
                        username=item['namespace']['path'],
                        name=item['name'],
                        clone_url=item['http_url_to_repo'],
                        is_fork=is_fork,
                        is_private=item['visibility'] != 'public',
                        is_archived=item.get('archived', False),
                        size_kb=item.get('statistics', {}).get('repository_size', 0) // 1024,
                        default_branch=item.get('default_branch', 'main')
                    )
                    repos.append(repo)

                # Check if more pages
                if page >= total_pages:
                    break

                page += 1

        return repos

    async def get_rate_limit(self) -> RateLimitInfo:
        """Get GitLab rate limit status."""
        # GitLab doesn't have a dedicated rate limit endpoint
        # Return dummy data for now
        return RateLimitInfo(remaining=600, limit=600, reset_timestamp=0)
