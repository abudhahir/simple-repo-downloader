# tests/test_config.py
import os
import tempfile
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from simple_repo_downloader.config import (
    AppConfig,
    Credentials,
    DownloadConfig,
    Target,
    resolve_env_var,
)


# Test resolve_env_var function
def test_resolve_env_var_with_existing_var(monkeypatch):
    monkeypatch.setenv("TEST_VAR", "test_value")
    result = resolve_env_var("${TEST_VAR}")
    assert result == "test_value"


def test_resolve_env_var_with_missing_var():
    result = resolve_env_var("${NONEXISTENT_VAR}")
    assert result == "${NONEXISTENT_VAR}"


def test_resolve_env_var_with_multiple_vars(monkeypatch):
    monkeypatch.setenv("VAR1", "value1")
    monkeypatch.setenv("VAR2", "value2")
    result = resolve_env_var("${VAR1} and ${VAR2}")
    assert result == "value1 and value2"


def test_resolve_env_var_with_non_string():
    result = resolve_env_var(123)
    assert result == 123


# Test Credentials
def test_credentials_with_direct_tokens():
    creds = Credentials(
        github_token="ghp_test123",
        gitlab_token="glpat_test456"
    )
    assert creds.github_token == "ghp_test123"
    assert creds.gitlab_token == "glpat_test456"


def test_credentials_with_env_vars(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_from_env")
    monkeypatch.setenv("GITLAB_TOKEN", "glpat_from_env")

    creds = Credentials(
        github_token="${GITHUB_TOKEN}",
        gitlab_token="${GITLAB_TOKEN}"
    )
    assert creds.github_token == "ghp_from_env"
    assert creds.gitlab_token == "glpat_from_env"


def test_credentials_with_none_values():
    creds = Credentials()
    assert creds.github_token is None
    assert creds.gitlab_token is None


# Test DownloadConfig
def test_download_config_defaults():
    config = DownloadConfig()
    assert config.base_directory == Path('./repos')
    assert config.max_parallel == 5
    assert config.include_forks is True
    assert config.include_private is True


def test_download_config_custom_values():
    config = DownloadConfig(
        base_directory=Path('/custom/path'),
        max_parallel=10,
        include_forks=False,
        include_private=False
    )
    assert config.base_directory == Path('/custom/path')
    assert config.max_parallel == 10
    assert config.include_forks is False
    assert config.include_private is False


def test_download_config_max_parallel_validation():
    # Valid range (1-20)
    config = DownloadConfig(max_parallel=1)
    assert config.max_parallel == 1

    config = DownloadConfig(max_parallel=20)
    assert config.max_parallel == 20

    # Test invalid values
    with pytest.raises(ValidationError):
        DownloadConfig(max_parallel=0)

    with pytest.raises(ValidationError):
        DownloadConfig(max_parallel=21)


# Test Target
def test_target_github():
    target = Target(platform='github', username='torvalds')
    assert target.platform == 'github'
    assert target.username == 'torvalds'
    assert target.filters == {}


def test_target_gitlab():
    target = Target(platform='gitlab', username='gitlab-org')
    assert target.platform == 'gitlab'
    assert target.username == 'gitlab-org'
    assert target.filters == {}


def test_target_with_filters():
    target = Target(
        platform='github',
        username='testuser',
        filters={'forks': False, 'archived': False}
    )
    assert target.filters == {'forks': False, 'archived': False}


def test_target_invalid_platform():
    with pytest.raises(ValidationError):
        Target(platform='bitbucket', username='user')


# Test AppConfig
def test_app_config_complete():
    config = AppConfig(
        credentials=Credentials(github_token='ghp_test'),
        download=DownloadConfig(max_parallel=3),
        targets=[
            Target(platform='github', username='user1'),
            Target(platform='gitlab', username='user2')
        ]
    )
    assert config.credentials.github_token == 'ghp_test'
    assert config.download.max_parallel == 3
    assert len(config.targets) == 2
    assert config.targets[0].platform == 'github'
    assert config.targets[1].platform == 'gitlab'


def test_app_config_with_env_vars(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_env_token")

    config = AppConfig(
        credentials=Credentials(github_token='${GITHUB_TOKEN}'),
        download=DownloadConfig(),
        targets=[Target(platform='github', username='testuser')]
    )
    assert config.credentials.github_token == 'ghp_env_token'


def test_load_config_from_yaml():
    config_data = {
        'credentials': {
            'github_token': 'ghp_test',
            'gitlab_token': 'glpat_test'
        },
        'download': {
            'base_directory': './test_repos',
            'max_parallel': 10
        },
        'targets': [
            {
                'platform': 'github',
                'username': 'torvalds',
                'filters': {'forks': False}
            }
        ]
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        config_path = Path(f.name)

    try:
        config = AppConfig.from_yaml(config_path)
        assert config.credentials.github_token == 'ghp_test'
        assert config.download.max_parallel == 10
        assert len(config.targets) == 1
        assert config.targets[0].username == 'torvalds'
    finally:
        config_path.unlink()
