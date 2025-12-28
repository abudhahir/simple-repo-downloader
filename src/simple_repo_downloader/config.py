# src/simple_repo_downloader/config.py
import os
import re
from pathlib import Path
from typing import Dict, List, Literal, Optional, Union

import yaml
from pydantic import BaseModel, Field, field_validator, ValidationInfo


def resolve_env_var(value: str) -> str:
    """Resolve ${VAR_NAME} syntax to environment variable value."""
    if not isinstance(value, str):
        return value

    pattern = r'\$\{([^}]+)\}'

    def replace_var(match):
        var_name = match.group(1)
        return os.environ.get(var_name, match.group(0))

    return re.sub(pattern, replace_var, value)


class CredentialProfile(BaseModel):
    """Named credential profile for a platform."""
    platform: Literal['github', 'gitlab']
    username: str = Field(min_length=1)
    token: str = Field(min_length=1)

    @field_validator('username', 'token')
    @classmethod
    def validate_non_whitespace(cls, v: str, info: ValidationInfo) -> str:
        """Validate that field is not empty or whitespace-only."""
        if not v.strip():
            raise ValueError(f"{info.field_name} cannot be empty or whitespace")
        return v

    @field_validator('token', mode='before')
    @classmethod
    def resolve_token_env_var(cls, v: str) -> str:
        """Resolve environment variables in token."""
        return resolve_env_var(v)


class TargetGroup(BaseModel):
    """Group of usernames sharing a credential."""
    credential: str = Field(min_length=1)
    usernames: List[str] = Field(min_length=1)
    filters: Dict[str, bool] = Field(default_factory=dict)

    @field_validator('credential', 'usernames')
    @classmethod
    def validate_non_whitespace(cls, v: Union[str, List[str]], info: ValidationInfo) -> Union[str, List[str]]:
        """Validate that credential and usernames are not empty or whitespace-only."""
        field_name = info.field_name

        if field_name == 'credential':
            if isinstance(v, str) and not v.strip():
                raise ValueError("Credential name cannot be empty or whitespace")
            return v
        else:  # usernames
            if isinstance(v, list) and not all(u.strip() for u in v):
                raise ValueError("Usernames cannot be empty or whitespace")
            return v


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


class DownloadConfig(BaseModel):
    """Configuration for download behavior."""
    base_directory: Path = Path('./repos')
    max_parallel: int = Field(default=5, ge=1, le=20)
    include_forks: bool = True
    include_private: bool = True


class Target(BaseModel):
    """A platform/username target to download from."""
    platform: Literal['github', 'gitlab']
    username: str
    filters: Dict[str, bool] = Field(default_factory=dict)


class AppConfig(BaseModel):
    """Complete application configuration."""
    credentials: Credentials
    download: DownloadConfig
    targets: List[Target]

    @classmethod
    def from_yaml(cls, path: Path) -> "AppConfig":
        """Load configuration from YAML file."""
        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in configuration file: {e}")

        return cls(**data)

    def to_yaml(self, path: Path) -> None:
        """Save configuration to YAML file."""
        try:
            with open(path, 'w') as f:
                # Convert to dict, handle Path objects
                data = self.model_dump(mode='python')
                data['download']['base_directory'] = str(data['download']['base_directory'])
                yaml.dump(data, f, default_flow_style=False)
        except (OSError, IOError) as e:
            raise IOError(f"Failed to write configuration file: {e}")
