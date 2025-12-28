# tests/test_resolved_target.py
import pytest
from dataclasses import FrozenInstanceError

from simple_repo_downloader.config import ResolvedTarget


def test_resolved_target_creation():
    """Test creating a ResolvedTarget with all fields."""
    resolved = ResolvedTarget(
        platform='github',
        username='testuser',
        token='ghp_test123',
        filters={'forks': False}
    )
    assert resolved.platform == 'github'
    assert resolved.username == 'testuser'
    assert resolved.token == 'ghp_test123'
    assert resolved.filters == {'forks': False}


def test_resolved_target_optional_token():
    """Test creating a ResolvedTarget with None token (public repos)."""
    resolved = ResolvedTarget(
        platform='gitlab',
        username='publicuser',
        token=None,
        filters={}
    )
    assert resolved.platform == 'gitlab'
    assert resolved.username == 'publicuser'
    assert resolved.token is None
    assert resolved.filters == {}


def test_resolved_target_empty_filters():
    """Test creating a ResolvedTarget with empty filters dict."""
    resolved = ResolvedTarget(
        platform='github',
        username='user',
        token='token123',
        filters={}
    )
    assert resolved.filters == {}


def test_resolved_target_is_immutable():
    """Test that ResolvedTarget is immutable (frozen)."""
    resolved = ResolvedTarget(
        platform='github',
        username='testuser',
        token='token123',
        filters={}
    )
    # Attempt to modify should raise FrozenInstanceError
    with pytest.raises(FrozenInstanceError):
        resolved.platform = 'gitlab'
