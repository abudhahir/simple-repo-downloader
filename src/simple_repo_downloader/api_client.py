from abc import ABC, abstractmethod
from typing import Dict, List, Optional
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
