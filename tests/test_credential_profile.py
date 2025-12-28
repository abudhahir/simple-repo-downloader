# tests/test_credential_profile.py
import os
import pytest
from pydantic import ValidationError
from simple_repo_downloader.config import CredentialProfile


def test_credential_profile_basic_creation():
    """Test creating a basic credential profile."""
    profile = CredentialProfile(
        platform='github',
        username='testuser',
        token='ghp_test123'
    )
    assert profile.platform == 'github'
    assert profile.username == 'testuser'
    assert profile.token == 'ghp_test123'


def test_credential_profile_resolves_env_vars():
    """Test credential profile resolves ${VAR} in token."""
    os.environ['TEST_TOKEN'] = 'ghp_from_env'
    profile = CredentialProfile(
        platform='github',
        username='testuser',
        token='${TEST_TOKEN}'
    )
    assert profile.token == 'ghp_from_env'
    del os.environ['TEST_TOKEN']


def test_credential_profile_invalid_platform():
    """Test invalid platform raises ValidationError."""
    with pytest.raises(ValidationError):
        CredentialProfile(
            platform='bitbucket',
            username='testuser',
            token='token123'
        )


def test_credential_profile_gitlab():
    """Test GitLab platform support."""
    profile = CredentialProfile(
        platform='gitlab',
        username='gitlabuser',
        token='glpat_test456'
    )
    assert profile.platform == 'gitlab'


def test_credential_profile_empty_username_fails():
    """Test that empty username is rejected."""
    with pytest.raises(ValidationError):
        CredentialProfile(
            platform='github',
            username='',
            token='ghp_test123'
        )


def test_credential_profile_empty_token_fails():
    """Test that empty token is rejected."""
    with pytest.raises(ValidationError):
        CredentialProfile(
            platform='github',
            username='testuser',
            token=''
        )


def test_credential_profile_whitespace_username_fails():
    """Test that whitespace-only username is rejected."""
    with pytest.raises(ValidationError, match="cannot be empty or whitespace"):
        CredentialProfile(
            platform='github',
            username='   ',
            token='ghp_test123'
        )


def test_credential_profile_whitespace_token_fails():
    """Test that whitespace-only token is rejected."""
    with pytest.raises(ValidationError, match="cannot be empty or whitespace"):
        CredentialProfile(
            platform='github',
            username='testuser',
            token='   '
        )
