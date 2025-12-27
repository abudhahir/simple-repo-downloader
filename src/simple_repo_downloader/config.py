# src/simple_repo_downloader/config.py
import os
import re
from pathlib import Path
from typing import Dict, List, Literal, Optional

import yaml
from pydantic import BaseModel, Field, field_validator


def resolve_env_var(value: str) -> str:
    """Resolve ${VAR_NAME} syntax to environment variable value."""
    if not isinstance(value, str):
        return value

    pattern = r'\$\{([^}]+)\}'

    def replace_var(match):
        var_name = match.group(1)
        return os.environ.get(var_name, match.group(0))

    return re.sub(pattern, replace_var, value)


class Credentials(BaseModel):
    """Authentication credentials for platforms."""
    github_token: Optional[str] = None
    gitlab_token: Optional[str] = None

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
