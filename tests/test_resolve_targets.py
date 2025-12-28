# tests/test_resolve_targets.py
import os
from simple_repo_downloader.config import (
    AppConfig, Credentials, CredentialProfile,
    DownloadConfig, Target
)


def test_resolve_targets_flat_format_with_profile():
    """Test resolving flat format targets with credential profiles."""
    config = AppConfig(
        credentials=Credentials(
            profiles={
                'my-github': CredentialProfile(
                    platform='github',
                    username='test',
                    token='ghp_profile_token'
                )
            }
        ),
        download=DownloadConfig(),
        targets=[
            Target(
                platform='github',
                username='user1',
                credential='my-github',
                filters={'forks': False}
            )
        ]
    )

    resolved = config.resolve_targets()

    assert len(resolved) == 1
    assert resolved[0].platform == 'github'
    assert resolved[0].username == 'user1'
    assert resolved[0].token == 'ghp_profile_token'
    assert resolved[0].filters == {'forks': False}


def test_resolve_targets_flat_format_legacy_token():
    """Test resolving flat format with legacy tokens."""
    config = AppConfig(
        credentials=Credentials(
            github_token='ghp_legacy_token'
        ),
        download=DownloadConfig(),
        targets=[
            Target(platform='github', username='user1')
        ]
    )

    resolved = config.resolve_targets()

    assert len(resolved) == 1
    assert resolved[0].token == 'ghp_legacy_token'


def test_resolve_targets_flat_format_env_var():
    """Test resolving flat format with env var fallback."""
    os.environ['GITHUB_TOKEN'] = 'ghp_from_env'

    config = AppConfig(
        credentials=Credentials(),
        download=DownloadConfig(),
        targets=[
            Target(platform='github', username='user1')
        ]
    )

    resolved = config.resolve_targets()

    assert len(resolved) == 1
    assert resolved[0].token == 'ghp_from_env'

    del os.environ['GITHUB_TOKEN']
