from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass
class WorkerConfig:
    daemon_url: str = os.getenv("DIG_DAEMON_URL", "http://127.0.0.1:7788")
    checkpoints_dir: Path = Path(os.getenv("DIG_CHECKPOINT_DIR", "checkpoints"))
    poll_interval_seconds: float = float(os.getenv("DIG_POLL_SECONDS", "2.5"))
    mission_refresh_seconds: float = float(os.getenv("DIG_MISSION_REFRESH_SECONDS", "8.0"))
    preempt_delta_priority: int = int(os.getenv("DIG_PREEMPT_DELTA", "18"))
    verbose: bool = os.getenv("DIG_VERBOSE", "1") == "1"
