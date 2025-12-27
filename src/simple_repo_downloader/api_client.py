from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import aiohttp

from .models import RepoInfo, RateLimitInfo


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

        while True:
            # Try user endpoint first, fall back to org
            url = f"{self.BASE_URL}/users/{username}/repos"
            params = {'per_page': 100, 'page': page}

            async with self.session.get(url, headers=self.headers, params=params) as response:
                if response.status == 404:
                    # Try org endpoint
                    url = f"{self.BASE_URL}/orgs/{username}/repos"
                    async with self.session.get(url, headers=self.headers, params=params) as org_response:
                        if org_response.status != 200:
                            break
                        data = await org_response.json()
                elif response.status != 200:
                    break
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
