from datetime import datetime
from pathlib import Path
from typing import List, Optional

from rich.console import Console

from .models import RepoInfo


class ProgressPrinter:
    """Progress printer that outputs to console and log file."""

    def __init__(self, log_file: Optional[Path] = None):
        self.console = Console()
        self.log_file = log_file
        self.start_time = datetime.now()

        # Create log directory if needed
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def print_start(self, repos: List[RepoInfo], max_parallel: int) -> None:
        """Print initial header with repository counts."""
        private_count = sum(1 for r in repos if r.is_private)
        public_count = len(repos) - private_count

        message = (
            f"Found {len(repos)} repositories "
            f"({private_count} private, {public_count} public)\n"
            f"Starting download with {max_parallel} parallel workers...\n"
        )

        self.console.print(message)
        self._log(message)

    def _log(self, message: str) -> None:
        """Write message to log file with timestamp."""
        if self.log_file:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.log_file, 'a') as f:
                f.write(f"{timestamp} | {message}")
