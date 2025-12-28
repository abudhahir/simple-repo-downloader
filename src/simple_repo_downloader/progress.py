from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console


class ProgressPrinter:
    """Progress printer that outputs to console and log file."""

    def __init__(self, log_file: Optional[Path] = None):
        self.console = Console()
        self.log_file = log_file
        self.start_time = datetime.now()

        # Create log directory if needed
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
