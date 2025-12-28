# tests/test_resolve_targets.py
import os
from simple_repo_downloader.config import (
    AppConfig, Credentials, CredentialProfile,
    DownloadConfig, Target, TargetGroup
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


def test_resolve_targets_grouped_format():
    """Test resolving grouped format targets."""
    config = AppConfig(
        credentials=Credentials(
            profiles={
                'my-github': CredentialProfile(
                    platform='github',
                    username='test',
                    token='ghp_token123'
                )
            }
        ),
        download=DownloadConfig(),
        targets={
            'github': [
                TargetGroup(
                    credential='my-github',
                    usernames=['user1', 'user2', 'user3'],
                    filters={'forks': False}
                )
            ]
        }
    )

    resolved = config.resolve_targets()

    assert len(resolved) == 3
    assert resolved[0].platform == 'github'
    assert resolved[0].username == 'user1'
    assert resolved[0].token == 'ghp_token123'
    assert resolved[0].filters == {'forks': False}
    assert resolved[1].username == 'user2'
    assert resolved[2].username == 'user3'


def test_resolve_targets_multiple_groups_same_platform():
    """Test resolving multiple groups for same platform."""
    config = AppConfig(
        credentials=Credentials(
            profiles={
                'personal': CredentialProfile(
                    platform='github',
                    username='personal',
                    token='ghp_personal'
                ),
                'work': CredentialProfile(
                    platform='github',
                    username='work',
                    token='ghp_work'
                )
            }
        ),
        download=DownloadConfig(),
        targets={
            'github': [
                TargetGroup(
                    credential='personal',
                    usernames=['user1', 'user2']
                ),
                TargetGroup(
                    credential='work',
                    usernames=['company-org']
                )
            ]
        }
    )

    resolved = config.resolve_targets()

    assert len(resolved) == 3
    assert resolved[0].token == 'ghp_personal'
    assert resolved[1].token == 'ghp_personal'
    assert resolved[2].token == 'ghp_work'
