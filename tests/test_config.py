# tests/test_config.py
import os
from simple_repo_downloader.config import Credentials

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
