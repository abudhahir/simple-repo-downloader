from pathlib import Path
from simple_repo_downloader.progress import ProgressPrinter


def test_progress_printer_initialization(tmp_path):
    """Test ProgressPrinter initializes with log file path."""
    log_file = tmp_path / "test.log"
    printer = ProgressPrinter(log_file=log_file)

    assert printer.log_file == log_file
    assert printer.start_time is not None
