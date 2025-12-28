from pathlib import Path
import pytest
from simple_repo_downloader.progress import ProgressPrinter
from simple_repo_downloader.models import RepoInfo, StateEnum


def test_progress_printer_initialization(tmp_path):
    """Test ProgressPrinter initializes with log file path."""
    log_file = tmp_path / "test.log"
    printer = ProgressPrinter(log_file=log_file)

    assert printer.log_file == log_file
    assert printer.start_time is not None


def test_print_start(tmp_path, capsys):
    """Test print_start displays repository count."""
    log_file = tmp_path / "test.log"
    printer = ProgressPrinter(log_file=log_file)

    repos = [
        RepoInfo(
            platform='github',
            username='test',
            name='repo1',
            clone_url='https://github.com/test/repo1.git',
            is_fork=False,
            is_private=True,
            is_archived=False,
            size_kb=100,
            default_branch='main'
        ),
        RepoInfo(
            platform='github',
            username='test',
            name='repo2',
            clone_url='https://github.com/test/repo2.git',
            is_fork=False,
            is_private=False,
            is_archived=False,
            size_kb=200,
            default_branch='main'
        ),
    ]

    printer.print_start(repos, max_parallel=5)

    captured = capsys.readouterr()
    assert "Found 2 repositories" in captured.out
    assert "1 private, 1 public" in captured.out
    assert "5 parallel workers" in captured.out

    # Check log file
    log_content = log_file.read_text()
    assert "Found 2 repositories" in log_content
    # Verify timestamp format (YYYY-MM-DD HH:MM:SS)
    assert " | Found 2 repositories" in log_content
    import re
    assert re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \|", log_content), "Log should have timestamp format: YYYY-MM-DD HH:MM:SS |"


def test_print_repo_update(tmp_path, capsys):
    """Test print_repo_update displays progress line."""
    log_file = tmp_path / "test.log"
    printer = ProgressPrinter(log_file=log_file)

    repo = RepoInfo(
        platform='github',
        username='test',
        name='my-repo',
        clone_url='https://github.com/test/my-repo.git',
        is_fork=False,
        is_private=True,
        is_archived=False,
        size_kb=100,
        default_branch='main'
    )

    printer.print_repo_update(
        current=5,
        total=57,
        repo=repo,
        state=StateEnum.COMPLETED,
        message="Cloned successfully"
    )

    captured = capsys.readouterr()
    assert "[5/57]" in captured.out
    assert "✓" in captured.out  # Verify COMPLETED state emoji
    assert "PRIVATE" in captured.out
    assert "github/test/my-repo" in captured.out
    assert "Cloned successfully" in captured.out

    # Check log file
    log_content = log_file.read_text()
    assert "[5/57]" in log_content


@pytest.mark.parametrize("state,expected_emoji", [
    (StateEnum.COMPLETED, "✓"),
    (StateEnum.DOWNLOADING, "⏳"),
    (StateEnum.FAILED, "❌"),
    (StateEnum.UPDATED, "🔄"),
    (StateEnum.UP_TO_DATE, "✓"),
    (StateEnum.UNCOMMITTED_CHANGES, "⚠"),
    (StateEnum.AHEAD, "↑"),
    (StateEnum.QUEUED, "⏳"),
    (StateEnum.PAUSED, "⏸"),
    (StateEnum.SKIPPED, "⏭"),
])
def test_print_repo_update_all_states(tmp_path, capsys, state, expected_emoji):
    """Test print_repo_update displays correct emoji for each state."""
    log_file = tmp_path / "test.log"
    printer = ProgressPrinter(log_file=log_file)

    repo = RepoInfo(
        platform='github',
        username='test',
        name='test-repo',
        clone_url='https://github.com/test/test-repo.git',
        is_fork=False,
        is_private=False,
        is_archived=False,
        size_kb=100,
        default_branch='main'
    )

    printer.print_repo_update(
        current=1,
        total=10,
        repo=repo,
        state=state,
        message="Test message"
    )

    captured = capsys.readouterr()
    assert expected_emoji in captured.out
