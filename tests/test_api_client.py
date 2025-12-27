import pytest
from simple_repo_downloader.api_client import PlatformClient
from simple_repo_downloader.models import RepoInfo


def test_platform_client_is_abstract():
    """PlatformClient should be abstract and not instantiable."""
    with pytest.raises(TypeError):
        PlatformClient(token="test", session=None)
