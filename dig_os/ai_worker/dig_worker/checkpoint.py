from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
import json
from pathlib import Path
from typing import Any

from .models import MissionState


class CheckpointStore:
    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def save(self, mission_id: str, state: MissionState, extra: dict[str, Any] | None = None) -> Path:
        mission_dir = self.root_dir / mission_id
        mission_dir.mkdir(parents=True, exist_ok=True)
        filename = mission_dir / f"epoch-{state.epoch:04d}.json"
        state_payload = asdict(state)
        for key in ("started_at", "last_updated"):
            value = state_payload.get(key)
            if isinstance(value, datetime):
                state_payload[key] = value.isoformat() + "Z"

        payload = {
            "mission_id": mission_id,
            "saved_at": datetime.utcnow().isoformat() + "Z",
            "state": state_payload,
            "extra": extra or {},
        }
        filename.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return filename

    def latest(self, mission_id: str) -> dict[str, Any] | None:
        mission_dir = self.root_dir / mission_id
        if not mission_dir.exists():
            return None
        files = sorted(mission_dir.glob("epoch-*.json"))
        if not files:
            return None
        return json.loads(files[-1].read_text(encoding="utf-8"))
