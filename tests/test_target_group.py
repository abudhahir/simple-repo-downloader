# tests/test_target_group.py
import pytest
from pydantic import ValidationError
from simple_repo_downloader.config import TargetGroup


def test_target_group_basic():
    """Test creating a basic target group."""
    group = TargetGroup(
        credential='my-github',
        usernames=['user1', 'user2', 'user3']
    )
    assert group.credential == 'my-github'
    assert len(group.usernames) == 3
    assert group.filters == {}


def test_target_group_with_filters():
    """Test target group with filters."""
    group = TargetGroup(
        credential='my-github',
        usernames=['user1'],
        filters={'forks': False, 'archived': False}
    )
    assert group.filters == {'forks': False, 'archived': False}


def test_target_group_empty_usernames_fails():
    """Test that empty usernames list is rejected."""
    with pytest.raises(ValidationError):
        TargetGroup(
            credential='my-github',
            usernames=[]
        )


def test_target_group_whitespace_username_fails():
    """Test that whitespace-only usernames are rejected."""
    with pytest.raises(ValidationError, match="Usernames cannot be empty"):
        TargetGroup(
            credential='my-github',
            usernames=['user1', '  ', 'user2']
        )


def test_target_group_whitespace_credential_fails():
    """Test that whitespace-only credential is rejected."""
    with pytest.raises(ValidationError, match="Credential name cannot be empty"):
        TargetGroup(
            credential='   ',
            usernames=['user1', 'user2']
        )
