from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal


PerformanceMode = Literal["gaming", "balanced", "sleep", "autopilot"]


@dataclass
class TelemetrySnapshot:
    timestamp: datetime
    cpu_load_percent: float
    cpu_temp_c: float
    gpu_load_percent: float
    gpu_temp_c: float
    net_latency_ms: float
    earnings_per_sec: float
    impact_score: float
    mode: PerformanceMode


@dataclass
class Mission:
    id: str
    title: str
    bounty_dig: float
    dataset_gb: float
    eta_minutes: int
    priority: int
    domain: str
