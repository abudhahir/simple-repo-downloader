# Multi-Credential Configuration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enable users to configure multiple named credential profiles per platform and group targets by platform to reduce configuration repetition.

**Architecture:** Extend Pydantic models to support named credential profiles and grouped target format. Add validation for credential references and platform matching. Implement normalization layer that converts both old and new formats to a common `ResolvedTarget` representation for the downloader.

**Tech Stack:** Python 3.10+, Pydantic 2.x, pytest, YAML

---

## Task 1: Add CredentialProfile Model

**Files:**
- Modify: `src/simple_repo_downloader/config.py`
- Create: `tests/test_credential_profile.py`

**Step 1: Write failing test for CredentialProfile basic creation**

```python
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
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_credential_profile.py::test_credential_profile_basic_creation -v`
Expected: FAIL with "cannot import name 'CredentialProfile'"

**Step 3: Add CredentialProfile model**

In `src/simple_repo_downloader/config.py`, add after the `resolve_env_var` function:

```python
class CredentialProfile(BaseModel):
    """Named credential profile for a platform."""
    platform: Literal['github', 'gitlab']
    username: str
    token: str

    @field_validator('token', mode='before')
    @classmethod
    def resolve_token_env_vars(cls, v: str) -> str:
        """Resolve environment variables in token."""
        if v is None:
            return v
        return resolve_env_var(v)
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_credential_profile.py::test_credential_profile_basic_creation -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_credential_profile.py src/simple_repo_downloader/config.py
git commit -m "feat: add CredentialProfile model"
```

---

## Task 2: Test CredentialProfile Environment Variable Resolution

**Files:**
- Modify: `tests/test_credential_profile.py`

**Step 1: Write failing test for env var resolution**

```python
# tests/test_credential_profile.py
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
```

**Step 2: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_credential_profile.py::test_credential_profile_resolves_env_vars -v`
Expected: PASS (implementation already done in Task 1)

**Step 3: Write test for validation - empty username**

```python
# tests/test_credential_profile.py
def test_credential_profile_empty_username_fails():
    """Test that empty username is rejected."""
    with pytest.raises(ValidationError):
        CredentialProfile(
            platform='github',
            username='',
            token='ghp_test123'
        )
```

**Step 4: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_credential_profile.py::test_credential_profile_empty_username_fails -v`
Expected: FAIL (Pydantic allows empty strings by default)

**Step 5: Add username validation**

In `src/simple_repo_downloader/config.py`, update CredentialProfile:

```python
class CredentialProfile(BaseModel):
    """Named credential profile for a platform."""
    platform: Literal['github', 'gitlab']
    username: str = Field(min_length=1)
    token: str = Field(min_length=1)

    @field_validator('token', mode='before')
    @classmethod
    def resolve_token_env_vars(cls, v: str) -> str:
        """Resolve environment variables in token."""
        if v is None:
            return v
        return resolve_env_var(v)
```

**Step 6: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_credential_profile.py::test_credential_profile_empty_username_fails -v`
Expected: PASS

**Step 7: Commit**

```bash
git add tests/test_credential_profile.py src/simple_repo_downloader/config.py
git commit -m "feat: add validation for CredentialProfile fields"
```

---

## Task 3: Update Credentials Model with Profiles

**Files:**
- Modify: `src/simple_repo_downloader/config.py`
- Modify: `tests/test_config.py`

**Step 1: Write failing test for Credentials with profiles**

Add to `tests/test_config.py`:

```python
def test_credentials_with_profiles():
    """Test credentials with named profiles."""
    creds = Credentials(
        profiles={
            'my-github': CredentialProfile(
                platform='github',
                username='testuser',
                token='ghp_test'
            ),
            'my-gitlab': CredentialProfile(
                platform='gitlab',
                username='gluser',
                token='glpat_test'
            )
        }
    )
    assert len(creds.profiles) == 2
    assert 'my-github' in creds.profiles
    assert creds.profiles['my-github'].platform == 'github'
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_config.py::test_credentials_with_profiles -v`
Expected: FAIL with "Credentials has no attribute 'profiles'"

**Step 3: Update Credentials model**

In `src/simple_repo_downloader/config.py`, update Credentials:

```python
class Credentials(BaseModel):
    """Authentication credentials for platforms."""
    # Legacy format (backward compatible)
    github_token: Optional[str] = None
    gitlab_token: Optional[str] = None

    # New named profiles
    profiles: Dict[str, CredentialProfile] = Field(default_factory=dict)

    @field_validator('github_token', 'gitlab_token', mode='before')
    @classmethod
    def resolve_env_vars(cls, v):
        if v is None:
            return v
        return resolve_env_var(v)
```

Add import at top:
```python
from typing import Dict, List, Literal, Optional, Union
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_config.py::test_credentials_with_profiles -v`
Expected: PASS

**Step 5: Write test for mixed legacy and profiles**

```python
def test_credentials_mixed_legacy_and_profiles():
    """Test credentials can have both legacy tokens and profiles."""
    creds = Credentials(
        github_token='ghp_legacy',
        profiles={
            'work-github': CredentialProfile(
                platform='github',
                username='workuser',
                token='ghp_work'
            )
        }
    )
    assert creds.github_token == 'ghp_legacy'
    assert 'work-github' in creds.profiles
```

**Step 6: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_config.py::test_credentials_mixed_legacy_and_profiles -v`
Expected: PASS (already supported by implementation)

**Step 7: Commit**

```bash
git add tests/test_config.py src/simple_repo_downloader/config.py
git commit -m "feat: add profiles support to Credentials model"
```

---

## Task 4: Add TargetGroup Model

**Files:**
- Modify: `src/simple_repo_downloader/config.py`
- Create: `tests/test_target_group.py`

**Step 1: Write failing test for TargetGroup**

```python
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
```

**Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_target_group.py -v`
Expected: FAIL with "cannot import name 'TargetGroup'"

**Step 3: Add TargetGroup model**

In `src/simple_repo_downloader/config.py`, add after CredentialProfile:

```python
class TargetGroup(BaseModel):
    """Group of usernames sharing a credential."""
    credential: str = Field(min_length=1)
    usernames: List[str] = Field(min_length=1)
    filters: Dict[str, bool] = Field(default_factory=dict)

    @field_validator('usernames')
    @classmethod
    def validate_usernames(cls, v: List[str]) -> List[str]:
        """Validate usernames are non-empty after stripping."""
        if not all(u.strip() for u in v):
            raise ValueError("Usernames cannot be empty or whitespace")
        return v
```

**Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_target_group.py -v`
Expected: PASS

**Step 5: Write test for empty usernames validation**

```python
# tests/test_target_group.py
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
```

**Step 6: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_target_group.py -v`
Expected: PASS

**Step 7: Commit**

```bash
git add tests/test_target_group.py src/simple_repo_downloader/config.py
git commit -m "feat: add TargetGroup model with validation"
```

---

## Task 5: Update Target Model with Credential Reference

**Files:**
- Modify: `src/simple_repo_downloader/config.py`
- Modify: `tests/test_config.py`

**Step 1: Write test for Target with credential reference**

Add to `tests/test_config.py`:

```python
def test_target_with_credential_reference():
    """Test target can reference a credential profile."""
    target = Target(
        platform='github',
        username='testuser',
        credential='my-github'
    )
    assert target.credential == 'my-github'
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_config.py::test_target_with_credential_reference -v`
Expected: FAIL with "unexpected keyword argument 'credential'"

**Step 3: Update Target model**

In `src/simple_repo_downloader/config.py`, update Target:

```python
class Target(BaseModel):
    """A platform/username target to download from."""
    platform: Literal['github', 'gitlab']
    username: str
    credential: Optional[str] = None  # NEW: optional credential reference
    filters: Dict[str, bool] = Field(default_factory=dict)
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_config.py::test_target_with_credential_reference -v`
Expected: PASS

**Step 5: Verify backward compatibility**

Run: `.venv/bin/pytest tests/test_config.py::test_target_github tests/test_config.py::test_target_gitlab -v`
Expected: PASS (existing tests still work)

**Step 6: Commit**

```bash
git add tests/test_config.py src/simple_repo_downloader/config.py
git commit -m "feat: add credential reference to Target model"
```

---

## Task 6: Add ResolvedTarget Dataclass

**Files:**
- Modify: `src/simple_repo_downloader/config.py`
- Create: `tests/test_resolved_target.py`

**Step 1: Write test for ResolvedTarget**

```python
# tests/test_resolved_target.py
from simple_repo_downloader.config import ResolvedTarget


def test_resolved_target_creation():
    """Test creating a ResolvedTarget."""
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


def test_resolved_target_without_token():
    """Test ResolvedTarget without token (public repos)."""
    resolved = ResolvedTarget(
        platform='github',
        username='testuser',
        token=None,
        filters={}
    )
    assert resolved.token is None
```

**Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_resolved_target.py -v`
Expected: FAIL with "cannot import name 'ResolvedTarget'"

**Step 3: Add ResolvedTarget dataclass**

In `src/simple_repo_downloader/config.py`, add imports at top:

```python
from dataclasses import dataclass
```

Add after TargetGroup model:

```python
@dataclass
class ResolvedTarget:
    """Normalized target with resolved credentials."""
    platform: str
    username: str
    token: Optional[str]
    filters: Dict[str, bool]
```

**Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_resolved_target.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_resolved_target.py src/simple_repo_downloader/config.py
git commit -m "feat: add ResolvedTarget dataclass for normalized targets"
```

---

## Task 7: Update AppConfig to Support Union of Target Formats

**Files:**
- Modify: `src/simple_repo_downloader/config.py`
- Modify: `tests/test_config.py`

**Step 1: Write test for AppConfig with grouped targets**

Add to `tests/test_config.py`:

```python
def test_app_config_with_grouped_targets():
    """Test AppConfig with new grouped targets format."""
    config = AppConfig(
        credentials=Credentials(
            profiles={
                'my-github': CredentialProfile(
                    platform='github',
                    username='test',
                    token='ghp_test'
                )
            }
        ),
        download=DownloadConfig(),
        targets={
            'github': [
                TargetGroup(
                    credential='my-github',
                    usernames=['user1', 'user2']
                )
            ]
        }
    )
    assert isinstance(config.targets, dict)
    assert 'github' in config.targets
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_config.py::test_app_config_with_grouped_targets -v`
Expected: FAIL with validation error (targets expects List[Target])

**Step 3: Update AppConfig model**

In `src/simple_repo_downloader/config.py`, update AppConfig:

```python
class AppConfig(BaseModel):
    """Complete application configuration."""
    credentials: Credentials
    download: DownloadConfig
    targets: Union[List[Target], Dict[str, List[TargetGroup]]]
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_config.py::test_app_config_with_grouped_targets -v`
Expected: PASS

**Step 5: Verify old format still works**

Run: `.venv/bin/pytest tests/test_config.py::test_app_config_complete -v`
Expected: PASS (existing test with List[Target] format)

**Step 6: Commit**

```bash
git add tests/test_config.py src/simple_repo_downloader/config.py
git commit -m "feat: support both flat and grouped target formats in AppConfig"
```

---

## Task 8: Add Credential Validation to AppConfig

**Files:**
- Modify: `src/simple_repo_downloader/config.py`
- Modify: `tests/test_config.py`

**Step 1: Write test for missing credential validation**

Add to `tests/test_config.py`:

```python
def test_app_config_validates_missing_credential():
    """Test AppConfig rejects reference to non-existent credential."""
    with pytest.raises(ValidationError, match="Credential 'missing' not found"):
        AppConfig(
            credentials=Credentials(profiles={}),
            download=DownloadConfig(),
            targets={
                'github': [
                    TargetGroup(
                        credential='missing',
                        usernames=['user1']
                    )
                ]
            }
        )


def test_app_config_validates_platform_mismatch():
    """Test AppConfig rejects credential with wrong platform."""
    with pytest.raises(ValidationError, match="platform"):
        AppConfig(
            credentials=Credentials(
                profiles={
                    'my-gitlab': CredentialProfile(
                        platform='gitlab',
                        username='test',
                        token='glpat_test'
                    )
                }
            ),
            download=DownloadConfig(),
            targets={
                'github': [  # GitHub target
                    TargetGroup(
                        credential='my-gitlab',  # But GitLab credential
                        usernames=['user1']
                    )
                ]
            }
        )
```

**Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_config.py::test_app_config_validates_missing_credential tests/test_config.py::test_app_config_validates_platform_mismatch -v`
Expected: FAIL (no validation yet)

**Step 3: Add validation to AppConfig**

In `src/simple_repo_downloader/config.py`, add to AppConfig:

```python
class AppConfig(BaseModel):
    """Complete application configuration."""
    credentials: Credentials
    download: DownloadConfig
    targets: Union[List[Target], Dict[str, List[TargetGroup]]]

    @field_validator('targets')
    @classmethod
    def validate_targets(cls, v: Union[List[Target], Dict[str, List[TargetGroup]]], info):
        """Validate targets format and credential references."""
        credentials = info.data.get('credentials')
        if credentials is None:
            return v

        if isinstance(v, list):
            # Flat format validation
            for target in v:
                if target.credential:
                    cls._validate_credential_ref(
                        target.credential,
                        target.platform,
                        credentials
                    )
        else:
            # Grouped format validation
            for platform, groups in v.items():
                if platform not in ('github', 'gitlab'):
                    raise ValueError(f"Invalid platform: {platform}")
                for group in groups:
                    cls._validate_credential_ref(
                        group.credential,
                        platform,
                        credentials
                    )
        return v

    @staticmethod
    def _validate_credential_ref(cred_name: str, platform: str, credentials: Credentials):
        """Validate credential reference exists and matches platform."""
        if cred_name not in credentials.profiles:
            raise ValueError(f"Credential '{cred_name}' not found in profiles")

        profile = credentials.profiles[cred_name]
        if profile.platform != platform:
            raise ValueError(
                f"Credential '{cred_name}' is for {profile.platform}, "
                f"but target uses {platform}"
            )
```

**Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_config.py::test_app_config_validates_missing_credential tests/test_config.py::test_app_config_validates_platform_mismatch -v`
Expected: PASS

**Step 5: Write test for flat format validation**

```python
def test_app_config_validates_flat_format_credential():
    """Test AppConfig validates credentials in flat format."""
    with pytest.raises(ValidationError, match="not found"):
        AppConfig(
            credentials=Credentials(profiles={}),
            download=DownloadConfig(),
            targets=[
                Target(
                    platform='github',
                    username='user1',
                    credential='missing'
                )
            ]
        )
```

**Step 6: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_config.py::test_app_config_validates_flat_format_credential -v`
Expected: PASS (validation already covers both formats)

**Step 7: Commit**

```bash
git add tests/test_config.py src/simple_repo_downloader/config.py
git commit -m "feat: add credential validation to AppConfig"
```

---

## Task 9: Implement resolve_targets() Method - Part 1 (Flat Format)

**Files:**
- Modify: `src/simple_repo_downloader/config.py`
- Create: `tests/test_resolve_targets.py`

**Step 1: Write test for resolving flat format**

```python
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
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_resolve_targets.py::test_resolve_targets_flat_format_with_profile -v`
Expected: FAIL with "AppConfig has no attribute 'resolve_targets'"

**Step 3: Add resolve_targets method (partial implementation)**

In `src/simple_repo_downloader/config.py`, add to AppConfig:

```python
    def resolve_targets(self) -> List[ResolvedTarget]:
        """Convert targets to normalized format with resolved credentials."""
        resolved = []

        if isinstance(self.targets, list):
            # Flat format
            for target in self.targets:
                token = self._resolve_token(target.platform, target.credential)
                resolved.append(ResolvedTarget(
                    platform=target.platform,
                    username=target.username,
                    token=token,
                    filters=target.filters
                ))
        else:
            # Grouped format - TODO in next task
            pass

        return resolved

    def _resolve_token(self, platform: str, credential: Optional[str]) -> Optional[str]:
        """Resolve token for a platform/credential combination."""
        # Priority 1: Explicit credential profile
        if credential:
            return self.credentials.profiles[credential].token

        # Priority 2: Legacy platform token
        if platform == 'github' and self.credentials.github_token:
            return self.credentials.github_token
        if platform == 'gitlab' and self.credentials.gitlab_token:
            return self.credentials.gitlab_token

        # Priority 3: Environment variables
        env_var = f"{platform.upper()}_TOKEN"
        return os.environ.get(env_var)
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_resolve_targets.py::test_resolve_targets_flat_format_with_profile -v`
Expected: PASS

**Step 5: Write test for legacy token fallback**

```python
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
```

**Step 6: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_resolve_targets.py -v`
Expected: PASS

**Step 7: Commit**

```bash
git add tests/test_resolve_targets.py src/simple_repo_downloader/config.py
git commit -m "feat: implement resolve_targets for flat format"
```

---

## Task 10: Implement resolve_targets() Method - Part 2 (Grouped Format)

**Files:**
- Modify: `src/simple_repo_downloader/config.py`
- Modify: `tests/test_resolve_targets.py`

**Step 1: Write test for resolving grouped format**

Add to `tests/test_resolve_targets.py`:

```python
from simple_repo_downloader.config import TargetGroup


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
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_resolve_targets.py::test_resolve_targets_grouped_format -v`
Expected: FAIL (returns empty list, grouped format not implemented)

**Step 3: Implement grouped format resolution**

In `src/simple_repo_downloader/config.py`, update resolve_targets method:

```python
    def resolve_targets(self) -> List[ResolvedTarget]:
        """Convert targets to normalized format with resolved credentials."""
        resolved = []

        if isinstance(self.targets, list):
            # Flat format
            for target in self.targets:
                token = self._resolve_token(target.platform, target.credential)
                resolved.append(ResolvedTarget(
                    platform=target.platform,
                    username=target.username,
                    token=token,
                    filters=target.filters
                ))
        else:
            # Grouped format
            for platform, groups in self.targets.items():
                for group in groups:
                    token = self._resolve_token(platform, group.credential)
                    for username in group.usernames:
                        resolved.append(ResolvedTarget(
                            platform=platform,
                            username=username,
                            token=token,
                            filters=group.filters
                        ))

        return resolved
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_resolve_targets.py::test_resolve_targets_grouped_format -v`
Expected: PASS

**Step 5: Write test for multiple groups per platform**

```python
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
```

**Step 6: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_resolve_targets.py::test_resolve_targets_multiple_groups_same_platform -v`
Expected: PASS

**Step 7: Commit**

```bash
git add tests/test_resolve_targets.py src/simple_repo_downloader/config.py
git commit -m "feat: implement resolve_targets for grouped format"
```

---

## Task 11: Test Token Resolution Priority

**Files:**
- Modify: `tests/test_resolve_targets.py`

**Step 1: Write test for token priority**

```python
def test_token_resolution_priority():
    """Test token resolution follows correct priority."""
    os.environ['GITHUB_TOKEN'] = 'ghp_env'

    config = AppConfig(
        credentials=Credentials(
            github_token='ghp_legacy',
            profiles={
                'my-github': CredentialProfile(
                    platform='github',
                    username='test',
                    token='ghp_profile'
                )
            }
        ),
        download=DownloadConfig(),
        targets=[
            Target(platform='github', username='user1', credential='my-github'),
            Target(platform='github', username='user2'),
        ]
    )

    resolved = config.resolve_targets()

    # Profile takes priority when specified
    assert resolved[0].token == 'ghp_profile'
    # Legacy takes priority over env when no credential specified
    assert resolved[1].token == 'ghp_legacy'

    del os.environ['GITHUB_TOKEN']
```

**Step 2: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_resolve_targets.py::test_token_resolution_priority -v`
Expected: PASS

**Step 3: Write test for no token available**

```python
def test_token_resolution_no_token():
    """Test token resolution when no token available."""
    config = AppConfig(
        credentials=Credentials(),
        download=DownloadConfig(),
        targets=[
            Target(platform='github', username='user1')
        ]
    )

    resolved = config.resolve_targets()

    assert resolved[0].token is None
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_resolve_targets.py::test_token_resolution_no_token -v`
Expected: PASS

**Step 5: Run all resolve_targets tests**

Run: `.venv/bin/pytest tests/test_resolve_targets.py -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add tests/test_resolve_targets.py
git commit -m "test: add comprehensive token resolution priority tests"
```

---

## Task 12: Update YAML Load/Save for New Format

**Files:**
- Modify: `tests/test_config.py`

**Step 1: Write test for loading grouped format from YAML**

Add to `tests/test_config.py`:

```python
def test_load_grouped_format_from_yaml(tmp_path):
    """Test loading grouped target format from YAML."""
    yaml_content = """
credentials:
  profiles:
    my-github:
      platform: github
      username: testuser
      token: ghp_test123

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
"""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml_content)

    config = AppConfig.from_yaml(config_file)

    assert isinstance(config.targets, dict)
    assert 'github' in config.targets
    assert len(config.targets['github']) == 1
    assert config.targets['github'][0].credential == 'my-github'
    assert len(config.targets['github'][0].usernames) == 2
```

**Step 2: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_config.py::test_load_grouped_format_from_yaml -v`
Expected: PASS (Pydantic handles this automatically)

**Step 3: Write test for saving grouped format to YAML**

```python
def test_save_grouped_format_to_yaml(tmp_path):
    """Test saving grouped format to YAML."""
    config = AppConfig(
        credentials=Credentials(
            profiles={
                'my-github': CredentialProfile(
                    platform='github',
                    username='test',
                    token='ghp_test'
                )
            }
        ),
        download=DownloadConfig(base_directory=Path('./repos')),
        targets={
            'github': [
                TargetGroup(
                    credential='my-github',
                    usernames=['user1', 'user2']
                )
            ]
        }
    )

    config_file = tmp_path / "config.yaml"
    config.to_yaml(config_file)

    # Reload and verify
    loaded = AppConfig.from_yaml(config_file)
    assert isinstance(loaded.targets, dict)
    assert 'github' in loaded.targets
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_config.py::test_save_grouped_format_to_yaml -v`
Expected: PASS (existing to_yaml handles this)

**Step 5: Write test for backward compatibility with old YAML**

```python
def test_load_legacy_yaml_still_works(tmp_path):
    """Test backward compatibility with old config format."""
    yaml_content = """
credentials:
  github_token: ghp_legacy

download:
  base_directory: ./repos

targets:
  - platform: github
    username: user1
    filters:
      forks: false
"""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml_content)

    config = AppConfig.from_yaml(config_file)

    assert isinstance(config.targets, list)
    assert len(config.targets) == 1
    assert config.credentials.github_token == 'ghp_legacy'
```

**Step 6: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_config.py::test_load_legacy_yaml_still_works -v`
Expected: PASS

**Step 7: Commit**

```bash
git add tests/test_config.py
git commit -m "test: verify YAML load/save works with new formats"
```

---

## Task 13: Run Full Test Suite and Fix Any Issues

**Files:**
- Various (as needed)

**Step 1: Run all existing tests**

Run: `.venv/bin/pytest -v`
Expected: All tests should PASS

**Step 2: If any tests fail, analyze and fix**

Common issues:
- Import errors → Add missing imports
- Validation errors → Check field validators
- Type errors → Check Union types

**Step 3: Run tests with coverage**

Run: `.venv/bin/pytest --cov=simple_repo_downloader --cov-report=term-missing -v`
Expected: Coverage should be similar or better than baseline (76%)

**Step 4: Commit any fixes**

```bash
git add <fixed-files>
git commit -m "fix: resolve issues found in full test suite"
```

---

## Task 14: Update CLI to Use resolve_targets()

**Files:**
- Modify: `src/simple_repo_downloader/cli.py`
- Modify: `tests/test_cli.py`

**Step 1: Review current CLI implementation**

Read: `src/simple_repo_downloader/cli.py` to understand current flow

**Step 2: Write test for CLI with config using profiles**

Add to `tests/test_cli.py`:

```python
def test_cli_with_config_profiles(tmp_path, mock_downloader):
    """Test CLI using config with credential profiles."""
    yaml_content = """
credentials:
  profiles:
    my-github:
      platform: github
      username: testuser
      token: ghp_profile_token

download:
  base_directory: ./repos

targets:
  github:
    - credential: my-github
      usernames:
        - user1
        - user2
"""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml_content)

    # CLI should resolve targets and pass them to downloader
    # Test implementation depends on current CLI structure
    # This test will guide the implementation
```

**Step 3: Update CLI to use resolve_targets()**

In `src/simple_repo_downloader/cli.py`, find where config.targets is used and replace with config.resolve_targets().

The specific changes depend on the current CLI implementation. Look for:
- Where targets are iterated
- Where tokens are resolved
- Update to use ResolvedTarget instead of Target

**Step 4: Run CLI tests**

Run: `.venv/bin/pytest tests/test_cli.py -v`
Expected: PASS

**Step 5: Manual test with sample config**

Create test config and run:
```bash
.venv/bin/repo-dl download --config test-config.yaml
```

**Step 6: Commit**

```bash
git add src/simple_repo_downloader/cli.py tests/test_cli.py
git commit -m "feat: update CLI to use resolve_targets()"
```

---

## Task 15: Update Downloader to Accept ResolvedTarget

**Files:**
- Modify: `src/simple_repo_downloader/downloader.py`
- Modify: `tests/test_downloader.py`

**Step 1: Review current downloader implementation**

Read: `src/simple_repo_downloader/downloader.py` to understand current signature

**Step 2: Update downloader to accept List[ResolvedTarget]**

The downloader currently receives targets and resolves credentials internally.
Update to receive pre-resolved targets.

Changes needed:
- Update method signature to accept `List[ResolvedTarget]`
- Remove credential resolution logic (already done in config)
- Use `target.token` directly

**Step 3: Update downloader tests**

In `tests/test_downloader.py`, update tests to use ResolvedTarget instead of Target.

**Step 4: Run downloader tests**

Run: `.venv/bin/pytest tests/test_downloader.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/simple_repo_downloader/downloader.py tests/test_downloader.py
git commit -m "refactor: update downloader to accept ResolvedTarget"
```

---

## Task 16: Add Integration Test

**Files:**
- Create: `tests/test_integration_multi_credential.py`

**Step 1: Write end-to-end integration test**

```python
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
```

**Step 2: Run integration tests**

Run: `.venv/bin/pytest tests/test_integration_multi_credential.py -v`
Expected: PASS

**Step 3: Commit**

```bash
git add tests/test_integration_multi_credential.py
git commit -m "test: add end-to-end integration tests for multi-credential"
```

---

## Task 17: Update Documentation

**Files:**
- Modify: `README.md`
- Create: `docs/examples/multi-credential-config.yaml`

**Step 1: Create example config file**

```yaml
# docs/examples/multi-credential-config.yaml
# Example configuration with multiple credentials per platform

credentials:
  profiles:
    # Personal GitHub account
    personal-github:
      platform: github
      username: your-personal-username
      token: ${GITHUB_PERSONAL_TOKEN}

    # Work GitHub account
    work-github:
      platform: github
      username: your-work-username
      token: ${GITHUB_WORK_TOKEN}

    # Personal GitLab account
    personal-gitlab:
      platform: gitlab
      username: your-gitlab-username
      token: ${GITLAB_TOKEN}

download:
  base_directory: ./repos
  max_parallel: 10
  include_forks: true

targets:
  github:
    # Personal projects - exclude forks
    - credential: personal-github
      usernames:
        - torvalds
        - kubernetes
        - docker
      filters:
        forks: false
        archived: false

    # Work organization - include everything
    - credential: work-github
      usernames:
        - your-company-org
        - company-team

  gitlab:
    # Personal GitLab repos
    - credential: personal-gitlab
      usernames:
        - gitlab-org
        - gitlab-com
```

**Step 2: Update README.md**

Add new section "Multi-Credential Configuration" after the "Configuration File" section.

Content:
- Explain named credential profiles
- Show grouped targets format
- Provide migration examples from old to new format
- Document token resolution priority

**Step 3: Commit documentation**

```bash
git add README.md docs/examples/multi-credential-config.yaml
git commit -m "docs: add multi-credential configuration documentation"
```

---

## Task 18: Final Testing and Cleanup

**Files:**
- All

**Step 1: Run complete test suite**

Run: `.venv/bin/pytest -v`
Expected: All tests PASS

**Step 2: Run tests with coverage**

Run: `.venv/bin/pytest --cov=simple_repo_downloader --cov-report=html --cov-report=term`
Expected: Coverage >= 76% (baseline)

**Step 3: Run type checking**

Run: `.venv/bin/mypy src/`
Expected: No type errors

**Step 4: Run linting**

Run: `.venv/bin/ruff check src/ tests/`
Expected: No linting errors

**Step 5: Format code**

Run: `.venv/bin/black src/ tests/`

**Step 6: Final commit**

```bash
git add -A
git commit -m "chore: format code and ensure quality checks pass"
```

**Step 7: Review all commits**

Run: `git log --oneline`
Expected: Clean, logical commit history

---

## Summary

**Implementation complete!** The multi-credential configuration feature is now fully implemented with:

✅ Named credential profiles
✅ Grouped target format
✅ Full backward compatibility
✅ Comprehensive test coverage
✅ Token resolution priority
✅ Validation for credentials and platforms
✅ Documentation and examples

**Total tasks:** 18
**Estimated time:** 2-3 hours for experienced developer

**Next steps:**
1. Push feature branch
2. Create pull request
3. Code review
4. Merge to main

## Testing Checklist

Before merging, verify:
- [ ] All 62+ tests pass
- [ ] Coverage >= 76%
- [ ] mypy passes with no errors
- [ ] ruff/black formatting clean
- [ ] Manual testing with sample configs
- [ ] README examples work as documented
- [ ] Migration path from old to new format works
- [ ] Error messages are clear and helpful
