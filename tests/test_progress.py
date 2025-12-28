from pathlib import Path
from simple_repo_downloader.progress import ProgressPrinter
from simple_repo_downloader.models import RepoInfo


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
