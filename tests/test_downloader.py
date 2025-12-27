import pytest
from pathlib import Path
from simple_repo_downloader.downloader import DownloadEngine
from simple_repo_downloader.config import DownloadConfig


def test_download_engine_initialization():
    config = DownloadConfig(
        base_directory=Path('./test_repos'),
        max_parallel=3
    )
    engine = DownloadEngine(config)

    assert engine.config == config
    assert engine.semaphore._value == 3
