# tests/test_integration_multi_credential.py
"""Integration tests for multi-credential configuration."""
import os
from pathlib import Path
import pytest
from simple_repo_downloader.config import AppConfig


def test_end_to_end_multi_credential_flow(tmp_path):
    """Test complete flow from config to resolved targets."""
    # Set up environment
    os.environ['GITHUB_PERSONAL'] = 'ghp_personal_token'

    # Create config
    yaml_content = """
credentials:
  github_token: ghp_legacy_token
  profiles:
    personal-github:
      platform: github
      username: personal
      token: ${GITHUB_PERSONAL}
    work-github:
      platform: github
      username: work
      token: ghp_work_token
    my-gitlab:
      platform: gitlab
      username: gitlab-user
      token: glpat_token

download:
  base_directory: ./repos
  max_parallel: 5

targets:
  github:
    - credential: personal-github
      usernames:
        - torvalds
        - kubernetes
      filters:
        forks: false
    - credential: work-github
      usernames:
        - company-org
  gitlab:
    - credential: my-gitlab
      usernames:
        - gitlab-org
"""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml_content)

    # Load config
    config = AppConfig.from_yaml(config_file)

    # Resolve targets
    resolved = config.resolve_targets()

    # Verify results
    assert len(resolved) == 4

    # Personal GitHub targets
    assert resolved[0].platform == 'github'
    assert resolved[0].username == 'torvalds'
    assert resolved[0].token == 'ghp_personal_token'
    assert resolved[0].filters == {'forks': False}

    assert resolved[1].platform == 'github'
    assert resolved[1].username == 'kubernetes'
    assert resolved[1].token == 'ghp_personal_token'

    # Work GitHub target
    assert resolved[2].platform == 'github'
    assert resolved[2].username == 'company-org'
    assert resolved[2].token == 'ghp_work_token'
    assert resolved[2].filters == {}

    # GitLab target
    assert resolved[3].platform == 'gitlab'
    assert resolved[3].username == 'gitlab-org'
    assert resolved[3].token == 'glpat_token'

    # Cleanup
    del os.environ['GITHUB_PERSONAL']


def test_backward_compatibility_integration(tmp_path):
    """Test that old config format still works end-to-end."""
    yaml_content = """
credentials:
  github_token: ghp_legacy_token

download:
  base_directory: ./repos

targets:
  - platform: github
    username: user1
  - platform: github
    username: user2
"""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml_content)

    config = AppConfig.from_yaml(config_file)
    resolved = config.resolve_targets()

    assert len(resolved) == 2
    assert all(r.token == 'ghp_legacy_token' for r in resolved)


def test_mixed_format_integration(tmp_path):
    """Test mixing legacy tokens with profiles."""
    yaml_content = """
credentials:
  github_token: ghp_legacy_token
  profiles:
    work-github:
      platform: github
      username: work
      token: ghp_work_token

download:
  base_directory: ./repos

targets:
  - platform: github
    username: user1
    # Uses legacy token
  - platform: github
    username: company-org
    credential: work-github
"""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml_content)

    config = AppConfig.from_yaml(config_file)
    resolved = config.resolve_targets()

    assert len(resolved) == 2
    # First target uses legacy token
    assert resolved[0].token == 'ghp_legacy_token'
    # Second target uses profile token
    assert resolved[1].token == 'ghp_work_token'


def test_env_var_fallback_integration(tmp_path):
    """Test environment variable fallback when no token configured."""
    os.environ['GITHUB_TOKEN'] = 'ghp_from_env'

    yaml_content = """
credentials: {}

download:
  base_directory: ./repos

targets:
  - platform: github
    username: user1
"""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml_content)

    config = AppConfig.from_yaml(config_file)
    resolved = config.resolve_targets()

    assert len(resolved) == 1
    assert resolved[0].token == 'ghp_from_env'

    del os.environ['GITHUB_TOKEN']


def test_token_priority_integration(tmp_path):
    """Test token resolution priority across all sources."""
    os.environ['GITHUB_TOKEN'] = 'ghp_env'

    yaml_content = """
credentials:
  github_token: ghp_legacy
  profiles:
    my-github:
      platform: github
      username: test
      token: ghp_profile

download:
  base_directory: ./repos

targets:
  - platform: github
    username: user1
    credential: my-github
  - platform: github
    username: user2
  - platform: github
    username: user3
"""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml_content)

    config = AppConfig.from_yaml(config_file)
    resolved = config.resolve_targets()

    assert len(resolved) == 3
    # Profile has highest priority
    assert resolved[0].token == 'ghp_profile'
    # Legacy token beats env var
    assert resolved[1].token == 'ghp_legacy'
    assert resolved[2].token == 'ghp_legacy'

    del os.environ['GITHUB_TOKEN']


def test_filters_preserved_in_resolution(tmp_path):
    """Test that filters are correctly preserved through resolution."""
    yaml_content = """
credentials:
  profiles:
    my-github:
      platform: github
      username: test
      token: ghp_token

download:
  base_directory: ./repos

targets:
  github:
    - credential: my-github
      usernames:
        - user1
        - user2
      filters:
        forks: false
        archived: false
    - credential: my-github
      usernames:
        - user3
      filters:
        forks: true
"""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml_content)

    config = AppConfig.from_yaml(config_file)
    resolved = config.resolve_targets()

    assert len(resolved) == 3
    # First group has forks: false
    assert resolved[0].filters == {'forks': False, 'archived': False}
    assert resolved[1].filters == {'forks': False, 'archived': False}
    # Second group has forks: true
    assert resolved[2].filters == {'forks': True}
