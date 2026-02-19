from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Mission:
    id: str
    title: str
    bounty_dig: float
    dataset_gb: float
    eta_minutes: int
    priority: int
    domain: str

    @classmethod
    def from_api(cls, payload: dict[str, Any]) -> "Mission":
        return cls(
            id=str(payload.get("id", "mission-unknown")),
            title=str(payload.get("title", "Unknown mission")),
            bounty_dig=float(payload.get("bounty_dig", 0.0)),
            dataset_gb=float(payload.get("dataset_gb", 0.0)),
            eta_minutes=int(payload.get("eta_minutes", 5)),
            priority=int(payload.get("priority", 1)),
            domain=str(payload.get("domain", "general")),
        )

    @property
    def total_epochs(self) -> int:
        return min(30, max(6, self.eta_minutes))


@dataclass
class MissionState:
    mission_id: str
    epoch: int = 0
    total_epochs: int = 10
    accuracy: float = 0.10
    loss: float = 1.0
    started_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def completed(self) -> bool:
        return self.epoch >= self.total_epochs or self.accuracy >= 0.985
