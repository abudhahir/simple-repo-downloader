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
