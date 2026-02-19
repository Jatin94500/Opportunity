from __future__ import annotations

from datetime import datetime
import math
import time
from typing import Any

import requests

from .models import Mission, PerformanceMode, TelemetrySnapshot


class DaemonClient:
    def __init__(self, base_url: str = "http://127.0.0.1:7788") -> None:
        self.base_url = base_url.rstrip("/")
        self._session = requests.Session()
        self._timeout = 0.5

    def get_telemetry(self) -> TelemetrySnapshot:
        try:
            response = self._session.get(
                f"{self.base_url}/api/v1/telemetry",
                timeout=self._timeout,
            )
            response.raise_for_status()
            payload = response.json()
            return self._parse_telemetry(payload)
        except Exception:
            return self._mock_telemetry()

    def get_missions(self) -> list[Mission]:
        try:
            response = self._session.get(
                f"{self.base_url}/api/v1/missions",
                timeout=self._timeout,
            )
            response.raise_for_status()
            payload = response.json()
            return [self._parse_mission(item) for item in payload]
        except Exception:
            return self._mock_missions()

    def set_mode(self, mode: PerformanceMode) -> None:
        try:
            response = self._session.post(
                f"{self.base_url}/api/v1/mode",
                json={"mode": mode},
                timeout=self._timeout,
            )
            response.raise_for_status()
        except Exception:
            return

    def _parse_telemetry(self, data: dict[str, Any]) -> TelemetrySnapshot:
        timestamp = datetime.fromisoformat(
            str(data.get("timestamp", datetime.utcnow().isoformat())).replace("Z", "+00:00")
        )
        return TelemetrySnapshot(
            timestamp=timestamp,
            cpu_load_percent=float(data.get("cpu_load_percent", 0.0)),
            cpu_temp_c=float(data.get("cpu_temp_c", 0.0)),
            gpu_load_percent=float(data.get("gpu_load_percent", 0.0)),
            gpu_temp_c=float(data.get("gpu_temp_c", 0.0)),
            net_latency_ms=float(data.get("net_latency_ms", 0.0)),
            earnings_per_sec=float(data.get("earnings_per_sec", 0.0)),
            impact_score=float(data.get("impact_score", 0.0)),
            mode=str(data.get("mode", "balanced")),  # type: ignore[assignment]
        )

    def _parse_mission(self, data: dict[str, Any]) -> Mission:
        return Mission(
            id=str(data.get("id", "mission")),
            title=str(data.get("title", "Unknown Mission")),
            bounty_dig=float(data.get("bounty_dig", 0.0)),
            dataset_gb=float(data.get("dataset_gb", 0.0)),
            eta_minutes=int(data.get("eta_minutes", 0)),
            priority=int(data.get("priority", 1)),
            domain=str(data.get("domain", "general")),
        )

    def _mock_telemetry(self) -> TelemetrySnapshot:
        t = time.time()
        cpu = max(3.0, min(96.0, 34 + math.sin(t * 1.1) * 14))
        gpu = max(4.0, min(99.0, 58 + math.cos(t * 0.5) * 19))
        return TelemetrySnapshot(
            timestamp=datetime.utcnow(),
            cpu_load_percent=round(cpu, 2),
            cpu_temp_c=round(32 + cpu * 0.46, 2),
            gpu_load_percent=round(gpu, 2),
            gpu_temp_c=round(37 + gpu * 0.49, 2),
            net_latency_ms=round(17 + gpu * 0.1, 2),
            earnings_per_sec=round(max(0.001, (gpu / 100.0) * 0.08), 4),
            impact_score=round(25 + gpu * 0.72, 2),
            mode="balanced",
        )

    def _mock_missions(self) -> list[Mission]:
        return [
            Mission(
                id="med-pancreas-001",
                title="Pancreatic Cancer Detection",
                bounty_dig=500,
                dataset_gb=4.2,
                eta_minutes=12,
                priority=100,
                domain="medical",
            ),
            Mission(
                id="space-exoplanet-004",
                title="Exoplanet Atmosphere Analysis",
                bounty_dig=120,
                dataset_gb=2.1,
                eta_minutes=7,
                priority=55,
                domain="space",
            ),
            Mission(
                id="render-cyberpunk-2099",
                title="Render Cyberpunk 2099 Frame",
                bounty_dig=50,
                dataset_gb=1.4,
                eta_minutes=4,
                priority=20,
                domain="render",
            ),
        ]

